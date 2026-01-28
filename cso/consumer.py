"""
CSO Consumer — CSE Validation and Routing
==========================================

S34: D2 MOCK_ORACLE_PIPELINE_VALIDATION

Consumes Canonical Signal Envelopes (CSE) from CSO or mock generator,
validates them, and routes to the approval workflow.

INVARIANTS:
- INV-D2-FORMAT-1: CSE must validate against cse_schema.yaml
- INV-D2-TRACEABLE-1: Evidence refs must be resolvable
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMA PATH
# =============================================================================

CSE_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "cse_schema.yaml"


# =============================================================================
# VALIDATION RESULT
# =============================================================================


@dataclass
class ValidationResult:
    """Result of CSE validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class ConsumeResult:
    """Result of consuming a CSE."""

    success: bool
    signal_id: str = ""
    validation: ValidationResult = field(default_factory=lambda: ValidationResult(False))
    routed_to: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "signal_id": self.signal_id,
            "validation": self.validation.to_dict(),
            "routed_to": self.routed_to,
            "error": self.error,
        }


# =============================================================================
# APPROVAL HANDLER PROTOCOL
# =============================================================================


class ApprovalHandler(Protocol):
    """Protocol for approval workflow handler."""

    def submit_for_approval(
        self,
        cse: dict[str, Any],
        evidence_bundle: dict[str, Any],
    ) -> bool:
        """Submit CSE for human approval."""
        ...


# =============================================================================
# CSE VALIDATOR
# =============================================================================


class CSEValidator:
    """
    Validates CSE against schema.

    INV-D2-FORMAT-1: Both mock and production CSE validate here.
    """

    def __init__(self, schema_path: Path | None = None) -> None:
        """Load schema."""
        self._schema_path = schema_path or CSE_SCHEMA_PATH
        self._schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Load CSE schema from YAML."""
        if not self._schema_path.exists():
            logger.warning(f"Schema not found: {self._schema_path}")
            return {}

        with open(self._schema_path) as f:
            return yaml.safe_load(f)

    def validate(self, cse: dict[str, Any]) -> ValidationResult:
        """
        Validate CSE against schema.

        Args:
            cse: CSE dictionary

        Returns:
            ValidationResult with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Get field definitions
        cse_fields = self._schema.get("cse_fields", {})

        # Check required fields
        for field_name, field_def in cse_fields.items():
            if field_def.get("required", False):
                if field_name not in cse:
                    errors.append(f"Missing required field: {field_name}")

        if errors:
            return ValidationResult(valid=False, errors=errors)

        # Type validations
        # signal_id
        if not isinstance(cse.get("signal_id"), str):
            errors.append("signal_id must be a string")

        # timestamp
        if not isinstance(cse.get("timestamp"), str):
            errors.append("timestamp must be a string")

        # pair
        if not isinstance(cse.get("pair"), str):
            errors.append("pair must be a string")

        # source
        valid_sources = ["CSO", "HUNT_SURVIVOR", "MANUAL", "MOCK_5DRAWER"]
        if cse.get("source") not in valid_sources:
            errors.append(f"source must be one of {valid_sources}")

        # confidence
        confidence = cse.get("confidence")
        if not isinstance(confidence, (int, float)):
            errors.append("confidence must be numeric")
        elif not 0.0 <= confidence <= 1.0:
            errors.append(f"confidence must be 0-1, got {confidence}")

        # parameters
        params = cse.get("parameters", {})
        if not isinstance(params, dict):
            errors.append("parameters must be an object")
        else:
            # Check required params
            for param in ["entry", "stop", "target", "risk_percent"]:
                if param not in params:
                    errors.append(f"Missing parameter: {param}")
                elif not isinstance(params.get(param), (int, float)):
                    errors.append(f"Parameter {param} must be numeric")

            # Risk percent range
            risk = params.get("risk_percent", 0)
            if isinstance(risk, (int, float)):
                if not 0.5 <= risk <= 2.5:
                    errors.append(f"risk_percent must be 0.5-2.5, got {risk}")

            # Price validations
            entry = params.get("entry", 0)
            stop = params.get("stop", 0)
            target = params.get("target", 0)

            if entry == stop:
                errors.append("entry and stop cannot be equal")
            if entry == target:
                errors.append("entry and target cannot be equal")

            # Direction check
            if isinstance(entry, (int, float)) and isinstance(target, (int, float)):
                direction = "LONG" if entry < target else "SHORT"

                if isinstance(stop, (int, float)):
                    if direction == "LONG" and stop >= entry:
                        errors.append("LONG: stop must be below entry")
                    if direction == "SHORT" and stop <= entry:
                        errors.append("SHORT: stop must be above entry")

            # R:R warning
            all_numeric = (
                isinstance(entry, (int, float))
                and isinstance(stop, (int, float))
                and isinstance(target, (int, float))
            )
            if all_numeric:
                stop_dist = abs(entry - stop)
                target_dist = abs(target - entry)
                if stop_dist > 0:
                    rr = target_dist / stop_dist
                    if rr < 1.0:
                        warnings.append(f"Risk/reward {rr:.2f} is below 1:1")

        # evidence_hash
        evidence_hash = cse.get("evidence_hash")
        if not isinstance(evidence_hash, str):
            errors.append("evidence_hash must be a string")
        elif len(evidence_hash) != 64:
            warnings.append(f"evidence_hash should be 64 chars (SHA256), got {len(evidence_hash)}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


# =============================================================================
# EVIDENCE RESOLVER
# =============================================================================


class EvidenceResolver:
    """
    Resolves evidence references to source files.

    INV-D2-TRACEABLE-1: Refs must be resolvable.
    """

    def __init__(self, knowledge_dir: Path | None = None) -> None:
        """Initialize resolver."""
        self._knowledge_dir = knowledge_dir or (Path(__file__).parent / "knowledge")

    def resolve(self, cse: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Resolve evidence references in CSE.

        Args:
            cse: CSE dictionary

        Returns:
            (resolved, evidence_bundle)
        """
        evidence_bundle: dict[str, Any] = {
            "signal_id": cse.get("signal_id"),
            "source": cse.get("source"),
            "refs": [],
            "resolved": False,
        }

        # Check for mock metadata with gate refs
        mock_meta = cse.get("_mock_metadata", {})
        gate_ref = mock_meta.get("gate_ref", {})

        if gate_ref:
            gate_source = gate_ref.get("source", "")
            if gate_source == "conditions.yaml":
                # Verify file exists
                conditions_path = self._knowledge_dir / "conditions.yaml"
                if conditions_path.exists():
                    evidence_bundle["refs"].append(
                        {
                            "type": "5DRAWER_GATE",
                            "gate_id": gate_ref.get("gate_id"),
                            "source_file": str(conditions_path),
                            "resolved": True,
                        }
                    )
                    evidence_bundle["resolved"] = True
                else:
                    evidence_bundle["refs"].append(
                        {
                            "type": "5DRAWER_GATE",
                            "gate_id": gate_ref.get("gate_id"),
                            "error": f"Source file not found: {conditions_path}",
                            "resolved": False,
                        }
                    )

        # For production CSE (non-mock), evidence_hash links to reasoning
        if cse.get("source") != "MOCK_5DRAWER":
            evidence_bundle["evidence_hash"] = cse.get("evidence_hash")
            evidence_bundle["note"] = "Production evidence linked via hash"
            evidence_bundle["resolved"] = True

        return evidence_bundle.get("resolved", False), evidence_bundle


# =============================================================================
# CSO CONSUMER
# =============================================================================


class CSOConsumer:
    """
    Consumes and routes CSE signals.

    Pipeline:
    1. Validate CSE against schema
    2. Resolve evidence references
    3. Route to approval workflow
    """

    def __init__(
        self,
        validator: CSEValidator | None = None,
        resolver: EvidenceResolver | None = None,
        approval_handler: ApprovalHandler | None = None,
    ) -> None:
        """Initialize consumer."""
        self._validator = validator or CSEValidator()
        self._resolver = resolver or EvidenceResolver()
        self._approval_handler = approval_handler

    def consume(self, cse: dict[str, Any]) -> ConsumeResult:
        """
        Consume a CSE signal.

        Args:
            cse: CSE dictionary (from YAML or direct)

        Returns:
            ConsumeResult with validation and routing status
        """
        signal_id = cse.get("signal_id", "unknown")

        # Step 1: Validate (INV-D2-FORMAT-1)
        validation = self._validator.validate(cse)
        if not validation.valid:
            logger.warning(f"CSE {signal_id} validation failed: {validation.errors}")
            return ConsumeResult(
                success=False,
                signal_id=signal_id,
                validation=validation,
                error="Validation failed",
            )

        logger.info(f"CSE {signal_id} validated successfully")
        if validation.warnings:
            logger.warning(f"CSE {signal_id} warnings: {validation.warnings}")

        # Step 2: Resolve evidence (INV-D2-TRACEABLE-1)
        resolved, evidence_bundle = self._resolver.resolve(cse)
        if not resolved:
            logger.warning(f"CSE {signal_id} evidence not fully resolved")
            # Warning only, don't reject

        # Step 3: Route to approval
        if self._approval_handler:
            try:
                submitted = self._approval_handler.submit_for_approval(cse, evidence_bundle)
                if submitted:
                    return ConsumeResult(
                        success=True,
                        signal_id=signal_id,
                        validation=validation,
                        routed_to="approval_workflow",
                    )
                else:
                    return ConsumeResult(
                        success=False,
                        signal_id=signal_id,
                        validation=validation,
                        error="Approval handler rejected submission",
                    )
            except Exception as e:
                logger.error(f"Approval handler error: {e}")
                return ConsumeResult(
                    success=False,
                    signal_id=signal_id,
                    validation=validation,
                    error=str(e),
                )

        # No approval handler - just validate
        return ConsumeResult(
            success=True,
            signal_id=signal_id,
            validation=validation,
            routed_to="validated_only",
        )

    def consume_from_file(self, path: Path) -> ConsumeResult:
        """
        Consume CSE from YAML file.

        Args:
            path: Path to CSE YAML file

        Returns:
            ConsumeResult
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            # Handle intent wrapper
            if data.get("type") == "CSE":
                cse = data.get("payload", {})
            else:
                cse = data

            return self.consume(cse)

        except Exception as e:
            logger.error(f"Failed to consume {path}: {e}")
            return ConsumeResult(
                success=False,
                error=f"File read error: {e}",
            )


# =============================================================================
# D1 ROUTER INTEGRATION
# =============================================================================


def create_cse_route_handler(consumer: CSOConsumer):
    """
    Create a route handler for D1 watcher.

    Integrates CSO consumer with D1 routing table.
    """
    from daemons.routing import Intent, RouteResult

    class CSERouteHandler:
        def __init__(self, cso_consumer: CSOConsumer) -> None:
            self._consumer = cso_consumer

        def handle(self, intent: Intent) -> RouteResult:
            """Handle CSE intent from D1 watcher."""
            # Extract CSE from payload
            cse = intent.payload

            # Consume
            result = self._consumer.consume(cse)

            return RouteResult(
                success=result.success,
                intent=intent,
                worker_name="CSO_CONSUMER",
                error=result.error if not result.success else None,
            )

    return CSERouteHandler(consumer)
