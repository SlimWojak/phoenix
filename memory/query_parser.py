"""
Query Parser — Natural Language to Query IR
============================================

Parses natural language queries into Query IR.

INVARIANTS:
- INV-ATHENA-IR-ONLY-1: SQL generated ONLY from QueryIR fields, never raw text
- INV-ATHENA-AUDIT-1: Every query has audit fields

The parser:
1. Takes natural language query
2. Uses LLM to extract structured Query IR
3. Validates against query_ir_schema.yaml
4. Returns validated QueryIR or validation errors

CLOSED-WORLD: No SQL operators in keyword fields.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# =============================================================================
# ENUMS
# =============================================================================


class BeadTypeFilter(str, Enum):
    """Bead types for filtering."""

    HUNT = "HUNT"
    CONTEXT_SNAPSHOT = "CONTEXT_SNAPSHOT"
    PERFORMANCE = "PERFORMANCE"
    AUTOPSY = "AUTOPSY"
    POSITION = "POSITION"
    PROMOTION = "PROMOTION"


class Requester(str, Enum):
    """Query requester types."""

    CLAUDE = "claude"
    SYSTEM = "system"
    HUMAN = "human"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class DateRange:
    """Date range for queries."""

    start: datetime | None = None
    end: datetime | None = None


@dataclass
class QueryIR:
    """
    Query Intermediate Representation.

    All fields validated against query_ir_schema.yaml.
    SQL generated ONLY from these fields (INV-ATHENA-IR-ONLY-1).
    """

    # Audit fields (REQUIRED - INV-ATHENA-AUDIT-1)
    query_id: str
    timestamp_utc: datetime
    requester: Requester

    # Query version
    query_version: str = "1.0"

    # Query parameters
    bead_types: list[BeadTypeFilter] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    date_range: DateRange | None = None
    pair_filter: list[str] = field(default_factory=list)
    limit: int = 20

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "query_version": self.query_version,
            "query_id": self.query_id,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "requester": self.requester.value,
            "bead_types": [bt.value for bt in self.bead_types],
            "keywords": self.keywords,
            "limit": self.limit,
        }

        if self.date_range:
            result["date_range"] = {
                "start": self.date_range.start.isoformat() if self.date_range.start else None,
                "end": self.date_range.end.isoformat() if self.date_range.end else None,
            }

        if self.pair_filter:
            result["pair_filter"] = self.pair_filter

        return result


@dataclass
class ValidationResult:
    """Result of Query IR validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# QUERY PARSER
# =============================================================================


class QueryParser:
    """
    Parses natural language queries into Query IR.

    Uses LLM (configurable) to extract structured parameters,
    then validates against schema.

    INVARIANT: INV-ATHENA-IR-ONLY-1 — SQL from QueryIR only
    INVARIANT: INV-ATHENA-AUDIT-1 — Every query has audit fields
    """

    # Forbidden patterns in keywords (prevent SQL injection)
    FORBIDDEN_PATTERNS = [
        ";",
        "--",
        "/*",
        "*/",
        "DROP",
        "DELETE",
        "INSERT",
        "UPDATE",
        "CREATE",
        "ALTER",
        "TRUNCATE",
    ]

    def __init__(
        self,
        valid_pairs: list[str] | None = None,
        llm_backend: str = "mock",
    ) -> None:
        """
        Initialize parser.

        Args:
            valid_pairs: List of valid pair symbols
            llm_backend: LLM backend ("mock", "gemma", "claude")
        """
        self._valid_pairs = valid_pairs or [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"
        ]
        self._llm_backend = llm_backend

    def parse(
        self,
        natural_language: str,
        requester: Requester = Requester.CLAUDE,
    ) -> QueryIR | None:
        """
        Parse natural language query into Query IR.

        Args:
            natural_language: Query text
            requester: Who is making the query

        Returns:
            QueryIR object or None if parsing fails
        """
        # Generate audit fields (INV-ATHENA-AUDIT-1)
        query_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        # Parse using backend
        if self._llm_backend == "mock":
            parsed = self._mock_parse(natural_language)
        else:
            parsed = self._llm_parse(natural_language)

        if parsed is None:
            return None

        # Build QueryIR with audit fields
        return QueryIR(
            query_id=query_id,
            timestamp_utc=timestamp,
            requester=requester,
            query_version="1.0",
            bead_types=parsed.get("bead_types", []),
            keywords=parsed.get("keywords", []),
            date_range=parsed.get("date_range"),
            pair_filter=parsed.get("pair_filter", []),
            limit=min(parsed.get("limit", 20), 100),  # Cap at 100
        )

    def _mock_parse(self, text: str) -> dict[str, Any] | None:
        """
        Mock parser for testing.

        Extracts parameters from structured text patterns.
        """
        text_lower = text.lower()
        result: dict[str, Any] = {}

        # Detect bead types
        bead_types = []
        if "hunt" in text_lower or "hypothesis" in text_lower or "test" in text_lower:
            bead_types.append(BeadTypeFilter.HUNT)
        if "snapshot" in text_lower or "context" in text_lower or "session" in text_lower:
            bead_types.append(BeadTypeFilter.CONTEXT_SNAPSHOT)
        if "performance" in text_lower or "metric" in text_lower:
            bead_types.append(BeadTypeFilter.PERFORMANCE)
        if "autopsy" in text_lower or "trade" in text_lower:
            bead_types.append(BeadTypeFilter.AUTOPSY)

        result["bead_types"] = bead_types

        # Extract keywords (simple word extraction)
        keywords = []
        important_words = [
            "fvg", "bos", "choch", "ote", "sweep",
            "london", "ny", "asia",
            "ranging", "trending", "volatile",
            "tight", "wide",
        ]
        for word in important_words:
            if word in text_lower:
                keywords.append(word)

        # Also extract quoted strings as keywords
        quoted = re.findall(r'"([^"]+)"', text)
        keywords.extend(quoted)

        result["keywords"] = keywords[:10]  # Max 10 keywords

        # Detect pair filter
        pairs = []
        for pair in self._valid_pairs:
            if pair.lower() in text_lower:
                pairs.append(pair)
        result["pair_filter"] = pairs

        # Detect date range (simple patterns)
        date_range = None
        if "january" in text_lower:
            date_range = DateRange(
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 1, 31, 23, 59, 59, tzinfo=UTC),
            )
        elif "last week" in text_lower:
            now = datetime.now(UTC)
            date_range = DateRange(
                start=now.replace(hour=0, minute=0, second=0) - timedelta(days=7),
                end=now,
            )
        elif "today" in text_lower:
            now = datetime.now(UTC)
            date_range = DateRange(
                start=now.replace(hour=0, minute=0, second=0),
                end=now,
            )

        result["date_range"] = date_range

        # Detect limit
        limit_match = re.search(r"(?:top|first|last|limit)\s*(\d+)", text_lower)
        if limit_match:
            result["limit"] = min(int(limit_match.group(1)), 100)
        else:
            result["limit"] = 20

        return result

    def _llm_parse(self, text: str) -> dict[str, Any] | None:
        """
        Parse using LLM backend.

        TODO: Implement Gemma/Claude integration.
        """
        return self._mock_parse(text)

    def validate(self, ir: QueryIR) -> ValidationResult:
        """
        Validate Query IR against schema.

        Args:
            ir: QueryIR to validate

        Returns:
            ValidationResult with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Audit fields required (INV-ATHENA-AUDIT-1)
        if not ir.query_id:
            errors.append("query_id is required (INV-ATHENA-AUDIT-1)")
        if not ir.timestamp_utc:
            errors.append("timestamp_utc is required (INV-ATHENA-AUDIT-1)")

        # Validate keywords (no SQL injection)
        for keyword in ir.keywords:
            for forbidden in self.FORBIDDEN_PATTERNS:
                if forbidden.lower() in keyword.lower():
                    errors.append(
                        f"Forbidden pattern in keyword: {forbidden}"
                    )

            if len(keyword) > 100:
                errors.append(f"Keyword too long: {keyword[:20]}...")

        # Validate pair filter
        for pair in ir.pair_filter:
            if pair not in self._valid_pairs:
                warnings.append(f"Unknown pair: {pair}")

        # Validate limit
        if ir.limit < 1:
            errors.append("Limit must be at least 1")
        if ir.limit > 100:
            errors.append("Limit cannot exceed 100 (INV-ATHENA-CAP-1)")

        # Validate bead types
        if len(ir.bead_types) > 6:
            errors.append("Too many bead types specified")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


