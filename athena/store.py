"""
Athena Store — S37 Track B
==========================

Typed storage engine for claims, facts, and conflicts.
Enforces type discipline. No writeback. No auto-surface.

INVARIANTS:
  - INV-ATTR-NO-WRITEBACK: Claims cannot mutate doctrine
  - INV-NO-AUTO-SURFACE: Claims retrieved ONLY via explicit query
  - INV-CLAIM-NO-EXECUTION: Claims cannot be predicates
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from athena.bead_types import (
    AthenaBeadType,
    BeadValidator,
    ClaimBead,
    ClaimContent,
    ClaimProvenance,
    ClaimSource,
    ClaimStatus,
    ConflictBead,
    ConflictDetails,
    ConflictReferences,
    ConflictResolution,
    ConflictStatus,
    ConflictType,
    FactBead,
    FactContent,
    FactProvenance,
    FactSource,
    FactStatus,
    ResolutionAction,
    SourceType,
    StatisticalParameters,
    StatisticalType,
    ValidationResult,
)
from athena.claim_linter import ClaimLanguageLinter
from athena.rate_limiter import AthenaRateLimiter, RateLimitResult


# =============================================================================
# CONSTANTS
# =============================================================================

ATHENA_ROOT = Path(__file__).parent
DEFAULT_DB_PATH = Path.home() / "phoenix" / "data" / "athena.db"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class AthenaStoreError(Exception):
    """Base exception for Athena store."""

    pass


class ValidationError(AthenaStoreError):
    """Bead validation failed."""

    pass


class RateLimitError(AthenaStoreError):
    """Rate limit exceeded."""

    pass


class ExecutionGuardError(AthenaStoreError):
    """Claim execution attempted."""

    pass


class AutoSurfaceError(AthenaStoreError):
    """Auto-surface attempted."""

    pass


# =============================================================================
# ATHENA STORE
# =============================================================================


class AthenaStore:
    """
    Typed storage engine for Athena beads.

    INVARIANTS:
      - INV-ATTR-NO-WRITEBACK: Claims cannot mutate doctrine
      - INV-NO-AUTO-SURFACE: Claims retrieved ONLY via explicit query
      - INV-CLAIM-NO-EXECUTION: Claims cannot be predicates

    Usage:
        store = AthenaStore()
        claim_id = store.store_claim(claim_bead)
        claims = store.get_claims_by_domain("ICT")
    """

    def __init__(
        self,
        db_path: Path | None = None,
        rate_limiter: AthenaRateLimiter | None = None,
    ) -> None:
        """
        Initialize store.

        Args:
            db_path: Path to SQLite database
            rate_limiter: Rate limiter instance
        """
        self._db_path = db_path or DEFAULT_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._validator = BeadValidator()
        self._linter = ClaimLanguageLinter()
        self._rate_limiter = rate_limiter or AthenaRateLimiter()

        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claim_beads (
                    bead_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    data JSON NOT NULL,
                    domain TEXT,
                    superseded_by TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS fact_beads (
                    bead_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    data JSON NOT NULL,
                    domain TEXT,
                    module TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS conflict_beads (
                    bead_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    data JSON NOT NULL,
                    domain TEXT,
                    claim_bead_id TEXT,
                    fact_bead_id TEXT,
                    status TEXT DEFAULT 'OPEN'
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_claim_domain
                ON claim_beads(domain)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fact_domain
                ON fact_beads(domain)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conflict_status
                ON conflict_beads(status)
            """)

            conn.commit()

    # =========================================================================
    # CLAIM OPERATIONS
    # =========================================================================

    def store_claim(self, claim: ClaimBead) -> str:
        """
        Store a claim bead.

        Validates:
        1. Claim structure
        2. Language linting
        3. Rate limit
        4. Execution guard

        Args:
            claim: ClaimBead to store

        Returns:
            bead_id

        Raises:
            ValidationError: If validation fails
            RateLimitError: If rate limit exceeded
        """
        # Validate claim
        validation = self._validator.validate_claim(claim)
        if not validation.valid:
            raise ValidationError(
                f"Claim validation failed: {validation.errors}"
            )

        # Lint claim language
        lint_result = self._linter.lint(claim.content.assertion)
        if not lint_result.valid:
            raise ValidationError(
                f"Claim language rejected: {lint_result.error_messages}"
            )

        # Check rate limit
        rate_result = self._rate_limiter.check_claim()
        if not rate_result.allowed:
            raise RateLimitError(rate_result.reason)

        # Store
        data = self._claim_to_dict(claim)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO claim_beads (bead_id, timestamp, data, domain, superseded_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    claim.bead_id,
                    claim.timestamp.isoformat(),
                    json.dumps(data),
                    claim.content.domain,
                    claim.status.superseded_by,
                ),
            )
            conn.commit()

        # Record for rate limiting
        self._rate_limiter.record_claim()

        return claim.bead_id

    def get_claim(self, bead_id: str) -> ClaimBead | None:
        """Get a claim by bead_id."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM claim_beads WHERE bead_id = ?",
                (bead_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._dict_to_claim(json.loads(row[0]))
        return None

    def get_claims_by_domain(self, domain: str) -> list[ClaimBead]:
        """
        Get claims by domain.

        NOTE: This is an EXPLICIT query. Not auto-surfacing.
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM claim_beads WHERE domain = ?",
                (domain,),
            )
            return [
                self._dict_to_claim(json.loads(row[0]))
                for row in cursor.fetchall()
            ]

    # =========================================================================
    # FACT OPERATIONS
    # =========================================================================

    def store_fact(self, fact: FactBead) -> str:
        """
        Store a fact bead.

        Validates:
        1. Fact structure (provenance required)
        2. Rate limit

        Args:
            fact: FactBead to store

        Returns:
            bead_id
        """
        # Validate fact
        validation = self._validator.validate_fact(fact)
        if not validation.valid:
            raise ValidationError(
                f"Fact validation failed: {validation.errors}"
            )

        # Check rate limit
        rate_result = self._rate_limiter.check_fact()
        if not rate_result.allowed:
            raise RateLimitError(rate_result.reason)

        # Store
        data = self._fact_to_dict(fact)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO fact_beads (bead_id, timestamp, data, domain, module)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fact.bead_id,
                    fact.timestamp.isoformat(),
                    json.dumps(data),
                    fact.content.domain,
                    fact.source.module,
                ),
            )
            conn.commit()

        self._rate_limiter.record_fact()

        return fact.bead_id

    def get_fact(self, bead_id: str) -> FactBead | None:
        """Get a fact by bead_id."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM fact_beads WHERE bead_id = ?",
                (bead_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._dict_to_fact(json.loads(row[0]))
        return None

    def get_facts_by_domain(self, domain: str) -> list[FactBead]:
        """Get facts by domain."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM fact_beads WHERE domain = ?",
                (domain,),
            )
            return [
                self._dict_to_fact(json.loads(row[0]))
                for row in cursor.fetchall()
            ]

    # =========================================================================
    # CONFLICT OPERATIONS
    # =========================================================================

    def store_conflict(self, conflict: ConflictBead) -> str:
        """
        Store a conflict bead.

        Validates:
        1. Conflict structure
        2. Rate limit (per domain)

        Args:
            conflict: ConflictBead to store

        Returns:
            bead_id
        """
        # Validate conflict
        validation = self._validator.validate_conflict(conflict)
        if not validation.valid:
            raise ValidationError(
                f"Conflict validation failed: {validation.errors}"
            )

        domain = conflict.conflict.domain

        # Check rate limit
        rate_result = self._rate_limiter.check_conflict(domain)
        if not rate_result.allowed:
            raise RateLimitError(rate_result.reason)

        # Store
        data = self._conflict_to_dict(conflict)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO conflict_beads
                (bead_id, timestamp, data, domain, claim_bead_id, fact_bead_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conflict.bead_id,
                    conflict.timestamp.isoformat(),
                    json.dumps(data),
                    domain,
                    conflict.references.claim_bead_id,
                    conflict.references.fact_bead_id,
                    conflict.resolution.status.value,
                ),
            )
            conn.commit()

        self._rate_limiter.record_conflict(domain)

        return conflict.bead_id

    def get_conflict(self, bead_id: str) -> ConflictBead | None:
        """Get a conflict by bead_id."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM conflict_beads WHERE bead_id = ?",
                (bead_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._dict_to_conflict(json.loads(row[0]))
        return None

    def get_open_conflicts(self) -> list[ConflictBead]:
        """
        Get all open conflicts.

        SHUFFLED by default (INV-CONFLICT-SHUFFLE).
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM conflict_beads WHERE status = 'OPEN'"
            )
            conflicts = [
                self._dict_to_conflict(json.loads(row[0]))
                for row in cursor.fetchall()
            ]

        # Shuffle results (INV-CONFLICT-SHUFFLE)
        rng = secrets.SystemRandom()
        rng.shuffle(conflicts)

        return conflicts

    # =========================================================================
    # EXECUTION GUARD (Critical)
    # =========================================================================

    def validate_no_claim_execution(
        self,
        predicate_refs: list[str],
        alert_refs: list[str],
        hunt_refs: list[str],
    ) -> None:
        """
        Validate that no claim is being used as executable.

        INV-CLAIM-NO-EXECUTION

        Args:
            predicate_refs: References in CSO predicates
            alert_refs: References in alert rules
            hunt_refs: References in hunt parameters

        Raises:
            ExecutionGuardError: If claim found in any refs
        """
        all_refs = predicate_refs + alert_refs + hunt_refs

        for ref in all_refs:
            if ref.startswith("CLAIM_"):
                raise ExecutionGuardError(
                    f"Claim '{ref}' cannot be used as executable. "
                    "INV-CLAIM-NO-EXECUTION violation."
                )

    # =========================================================================
    # AUTO-SURFACE GUARD
    # =========================================================================

    def validate_no_auto_surface(self, intent_type: str) -> None:
        """
        Validate that auto-surface is not attempted.

        INV-NO-AUTO-SURFACE

        Args:
            intent_type: The intent type being processed

        Raises:
            AutoSurfaceError: If auto-surface intent detected
        """
        forbidden_intents = [
            "AUTO_SURFACE_CLAIM",
            "PUSH_CLAIM_ON_CHART",
            "SURFACE_MATCHING_CLAIMS",
        ]

        if intent_type in forbidden_intents:
            raise AutoSurfaceError(
                f"Auto-surface intent '{intent_type}' forbidden. "
                "INV-NO-AUTO-SURFACE violation. "
                "Claims retrieved ONLY via explicit query."
            )

    # =========================================================================
    # SERIALIZATION HELPERS
    # =========================================================================

    def _claim_to_dict(self, claim: ClaimBead) -> dict[str, Any]:
        """Convert ClaimBead to dict."""
        return {
            "bead_id": claim.bead_id,
            "bead_type": claim.bead_type.value,
            "timestamp": claim.timestamp.isoformat(),
            "source": {
                "type": claim.source.type.value,
                "attribution": claim.source.attribution,
                "context": claim.source.context,
            },
            "content": {
                "assertion": claim.content.assertion,
                "domain": claim.content.domain,
            },
            "disclaimer": claim.disclaimer,
            "statistical_parameters": (
                {
                    "type": claim.statistical_parameters.type.value,
                    "value": claim.statistical_parameters.value,
                    "bounds_lower": claim.statistical_parameters.bounds_lower,
                    "bounds_upper": claim.statistical_parameters.bounds_upper,
                }
                if claim.statistical_parameters
                else None
            ),
            "status": {
                "verified": claim.status.verified,
                "superseded_by": claim.status.superseded_by,
            },
            "provenance": {
                "session_id": claim.provenance.session_id,
                "created_at": claim.provenance.created_at.isoformat(),
            },
        }

    def _dict_to_claim(self, data: dict[str, Any]) -> ClaimBead:
        """Convert dict to ClaimBead."""
        stat_params = data.get("statistical_parameters")
        return ClaimBead(
            bead_id=data["bead_id"],
            bead_type=AthenaBeadType(data["bead_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=ClaimSource(
                type=SourceType(data["source"]["type"]),
                attribution=data["source"]["attribution"],
                context=data["source"].get("context", ""),
            ),
            content=ClaimContent(
                assertion=data["content"]["assertion"],
                domain=data["content"]["domain"],
            ),
            disclaimer=data["disclaimer"],
            statistical_parameters=(
                StatisticalParameters(
                    type=StatisticalType(stat_params["type"]),
                    value=stat_params["value"],
                    bounds_lower=stat_params.get("bounds_lower"),
                    bounds_upper=stat_params.get("bounds_upper"),
                )
                if stat_params
                else None
            ),
            status=ClaimStatus(
                verified=data["status"]["verified"],
                superseded_by=data["status"].get("superseded_by"),
            ),
            provenance=ClaimProvenance(
                session_id=data["provenance"]["session_id"],
                created_at=datetime.fromisoformat(data["provenance"]["created_at"]),
            ),
        )

    def _fact_to_dict(self, fact: FactBead) -> dict[str, Any]:
        """Convert FactBead to dict."""
        return {
            "bead_id": fact.bead_id,
            "bead_type": fact.bead_type.value,
            "timestamp": fact.timestamp.isoformat(),
            "source": {
                "type": fact.source.type.value,
                "module": fact.source.module,
                "formula": fact.source.formula,
            },
            "content": {
                "statement": fact.content.statement,
                "value": fact.content.value,
                "domain": fact.content.domain,
            },
            "provenance": {
                "query_string": fact.provenance.query_string,
                "dataset_hash": fact.provenance.dataset_hash,
                "governance_hash": fact.provenance.governance_hash,
                "strategy_config_hash": fact.provenance.strategy_config_hash,
                "computed_at": fact.provenance.computed_at.isoformat(),
            },
            "status": {
                "valid_until": (
                    fact.status.valid_until.isoformat()
                    if fact.status.valid_until
                    else None
                ),
                "recomputed_from": fact.status.recomputed_from,
            },
        }

    def _dict_to_fact(self, data: dict[str, Any]) -> FactBead:
        """Convert dict to FactBead."""
        return FactBead(
            bead_id=data["bead_id"],
            bead_type=AthenaBeadType(data["bead_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=FactSource(
                type=SourceType(data["source"]["type"]),
                module=data["source"]["module"],
                formula=data["source"].get("formula", ""),
            ),
            content=FactContent(
                statement=data["content"]["statement"],
                value=data["content"]["value"],
                domain=data["content"]["domain"],
            ),
            provenance=FactProvenance(
                query_string=data["provenance"]["query_string"],
                dataset_hash=data["provenance"]["dataset_hash"],
                governance_hash=data["provenance"]["governance_hash"],
                strategy_config_hash=data["provenance"]["strategy_config_hash"],
                computed_at=datetime.fromisoformat(data["provenance"]["computed_at"]),
            ),
            status=FactStatus(
                valid_until=(
                    datetime.fromisoformat(data["status"]["valid_until"])
                    if data["status"].get("valid_until")
                    else None
                ),
                recomputed_from=data["status"].get("recomputed_from"),
            ),
        )

    def _conflict_to_dict(self, conflict: ConflictBead) -> dict[str, Any]:
        """Convert ConflictBead to dict."""
        return {
            "bead_id": conflict.bead_id,
            "bead_type": conflict.bead_type.value,
            "timestamp": conflict.timestamp.isoformat(),
            "references": {
                "claim_bead_id": conflict.references.claim_bead_id,
                "fact_bead_id": conflict.references.fact_bead_id,
                "supersession_chain": conflict.references.supersession_chain,
            },
            "conflict": {
                "description": conflict.conflict.description,
                "domain": conflict.conflict.domain,
                "conflict_type": conflict.conflict.conflict_type.value,
            },
            "resolution": {
                "status": conflict.resolution.status.value,
                "resolved_by": conflict.resolution.resolved_by,
                "resolution_action": (
                    conflict.resolution.resolution_action.value
                    if conflict.resolution.resolution_action
                    else None
                ),
                "resolved_at": (
                    conflict.resolution.resolved_at.isoformat()
                    if conflict.resolution.resolved_at
                    else None
                ),
            },
        }

    def _dict_to_conflict(self, data: dict[str, Any]) -> ConflictBead:
        """Convert dict to ConflictBead."""
        return ConflictBead(
            bead_id=data["bead_id"],
            bead_type=AthenaBeadType(data["bead_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            references=ConflictReferences(
                claim_bead_id=data["references"]["claim_bead_id"],
                fact_bead_id=data["references"]["fact_bead_id"],
                supersession_chain=data["references"].get("supersession_chain", []),
            ),
            conflict=ConflictDetails(
                description=data["conflict"]["description"],
                domain=data["conflict"]["domain"],
                conflict_type=ConflictType(data["conflict"]["conflict_type"]),
            ),
            resolution=ConflictResolution(
                status=ConflictStatus(data["resolution"]["status"]),
                resolved_by=data["resolution"].get("resolved_by"),
                resolution_action=(
                    ResolutionAction(data["resolution"]["resolution_action"])
                    if data["resolution"].get("resolution_action")
                    else None
                ),
                resolved_at=(
                    datetime.fromisoformat(data["resolution"]["resolved_at"])
                    if data["resolution"].get("resolved_at")
                    else None
                ),
            ),
        )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "AthenaStore",
    "AthenaStoreError",
    "ValidationError",
    "RateLimitError",
    "ExecutionGuardError",
    "AutoSurfaceError",
]
