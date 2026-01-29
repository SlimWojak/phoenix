"""
CFP API — File Seam Integration
===============================

S35 TRACK F DELIVERABLE
Created: 2026-01-29 (Day 6-7)

Integrates CFP with Phoenix file seam architecture.

INTEGRATION POINTS:
  - Intent: type=CFP_QUERY, payload=LensQuery
  - Response: CFPResult written to /responses/
  - Orientation: cfp_status in orientation.yaml
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from cfp.budget import BudgetExceededError
from cfp.executor import CFPExecutor, CFPResult
from cfp.linter import CausalBanLinter
from cfp.validation import LensQuery, LensQueryValidator

# =============================================================================
# CONSTANTS
# =============================================================================

PHOENIX_ROOT = Path(__file__).parent.parent
RESPONSES_PATH = PHOENIX_ROOT / "responses"
INTENTS_PATH = PHOENIX_ROOT / "intents" / "incoming"


# =============================================================================
# TYPES
# =============================================================================


class CFPStatus(Enum):
    """CFP health status for orientation."""

    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    ERROR = "ERROR"


@dataclass
class CFPIntentResult:
    """Result of handling a CFP intent."""

    success: bool
    status: CFPStatus
    result: CFPResult | None = None
    error: str | None = None
    response_path: Path | None = None


# =============================================================================
# CFP API
# =============================================================================


class CFPAPI:
    """
    CFP API for file seam integration.

    Handles CFP_QUERY intents from the file seam,
    executes queries, and writes responses.

    Usage:
        api = CFPAPI()
        result = api.handle_intent(intent_dict)
    """

    def __init__(
        self,
        responses_path: Path | None = None,
        executor: CFPExecutor | None = None,
    ) -> None:
        """
        Initialize API.

        Args:
            responses_path: Path to responses directory
            executor: CFPExecutor instance (optional)
        """
        self._responses_path = responses_path or RESPONSES_PATH
        self._executor = executor or CFPExecutor()
        self._validator = LensQueryValidator()
        self._linter = CausalBanLinter()

    def handle_intent(self, intent: dict[str, Any]) -> CFPIntentResult:
        """
        Handle a CFP_QUERY intent.

        Args:
            intent: Intent dict with type and payload

        Returns:
            CFPIntentResult with status and response path
        """
        # Validate intent type
        intent_type = intent.get("type", "")
        if intent_type != "CFP_QUERY":
            return CFPIntentResult(
                success=False,
                status=CFPStatus.ERROR,
                error=f"Invalid intent type: {intent_type}",
            )

        # Extract and validate payload
        payload = intent.get("payload", {})

        try:
            # Build query from payload
            query = LensQuery.from_dict(payload)

            # Lint the query
            lint_result = self._linter.lint_query(query.to_dict())
            if not lint_result.passed:
                return CFPIntentResult(
                    success=False,
                    status=CFPStatus.ERROR,
                    error=f"Causal language detected: {lint_result.error_message}",
                )

            # Execute query
            result = self._executor.execute(query)

            # Write response
            response_path = self._write_response(intent, result)

            return CFPIntentResult(
                success=True,
                status=CFPStatus.NOMINAL,
                result=result,
                response_path=response_path,
            )

        except BudgetExceededError as e:
            return CFPIntentResult(
                success=False,
                status=CFPStatus.BUDGET_EXCEEDED,
                error=e.result.suggestion,
            )

        except ValueError as e:
            return CFPIntentResult(
                success=False,
                status=CFPStatus.ERROR,
                error=str(e),
            )

        except Exception as e:
            return CFPIntentResult(
                success=False,
                status=CFPStatus.DEGRADED,
                error=f"Unexpected error: {e}",
            )

    def _write_response(
        self,
        intent: dict[str, Any],
        result: CFPResult,
    ) -> Path:
        """Write response to file seam."""
        # Generate response filename
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"cfp_response_{timestamp}.md"
        response_path = self._responses_path / filename

        # Create responses directory if needed
        self._responses_path.mkdir(parents=True, exist_ok=True)

        # Format response
        content = self._format_response(result)

        # Write response
        response_path.write_text(content)

        return response_path

    def _format_response(self, result: CFPResult) -> str:
        """Format CFPResult as markdown response."""
        lines = [
            "# CFP Query Result",
            "",
            f"**Status:** {result.result_type.value}",
            f"**Sample Size:** N={result.sample_size}",
            "",
            "## Metrics",
            "",
        ]

        for metric, value in result.data.items():
            if value is not None:
                lines.append(f"- **{metric}:** {value}")
            else:
                lines.append(f"- **{metric}:** N/A")

        if result.low_sample_size:
            lines.extend(
                [
                    "",
                    "## Warnings",
                    "",
                    f"- Low sample size (N={result.sample_size} < 30)",
                ]
            )

        if result.warnings:
            if "## Warnings" not in lines:
                lines.extend(["", "## Warnings", ""])
            for warning in result.warnings:
                lines.append(f"- {warning}")

        lines.extend(
            [
                "",
                "## Provenance",
                "",
                f"- **Dataset Hash:** `{result.provenance.dataset_hash[:16]}...`",
                f"- **Governance Hash:** `{result.provenance.governance_hash[:16]}...`",
                f"- **Computed At:** {result.provenance.computed_at.isoformat()}",
                "",
            ]
        )

        return "\n".join(lines)

    def get_status(self) -> dict[str, Any]:
        """
        Get CFP status for orientation.yaml.

        Returns:
            Status dict for inclusion in orientation
        """
        return {
            "cfp_status": CFPStatus.NOMINAL.value,
            "version": "0.5.0",
            "invariants_enforced": [
                "INV-ATTR-CAUSAL-BAN",
                "INV-ATTR-PROVENANCE",
                "INV-ATTR-CONFLICT-DISPLAY",
                "INV-CFP-BUDGET-ENFORCE",
                "INV-CFP-LOW-N-GATE",
            ],
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def handle_cfp_query(intent: dict[str, Any]) -> CFPIntentResult:
    """
    Handle a CFP_QUERY intent (dispatcher entry point).

    Args:
        intent: Intent dict with type and payload

    Returns:
        CFPIntentResult
    """
    api = CFPAPI()
    return api.handle_intent(intent)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "CFPAPI",
    "CFPIntentResult",
    "CFPStatus",
    "handle_cfp_query",
]
