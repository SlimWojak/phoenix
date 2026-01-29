"""
Hunt Output — S38 Track E
=========================

Hunt output is a TABLE. Not a ranking. Not a recommendation.
Every variant, every metric, no selection.

INVARIANTS:
  - INV-ATTR-NO-RANKING: Flat table
  - INV-NO-UNSOLICITED: No synthesis
  - INV-HUNT-GRID-ORDER-DECLARED: Order explicit
  - INV-OUTPUT-SHUFFLE: Shuffle opt-in
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from hunt.executor import HuntResult, VariantResult


# =============================================================================
# CONSTANTS
# =============================================================================

FORBIDDEN_OUTPUT_FIELDS = frozenset([
    "top_variants",
    "best_variant",
    "best_performers",
    "survivors",
    "recommendation",
    "ranking",
    "key_finding",
    "pattern_detected",
    "suggested_next",
    "winners",
    "promising",
    "highlighted",
])

FORBIDDEN_SECTIONS = frozenset([
    "Winners",
    "Survivors",
    "Top N",
    "Recommended",
    "Promising",
    "Key Insights",
    "Best Performers",
    "Highlighted",
])


# =============================================================================
# OUTPUT FORMATTER
# =============================================================================


class HuntOutputFormatter:
    """
    Formats hunt results.

    Flat table, no ranking, grid order declared.

    INVARIANTS:
      - INV-ATTR-NO-RANKING: Flat table
      - INV-NO-UNSOLICITED: No synthesis
      - INV-HUNT-GRID-ORDER-DECLARED: Order explicit
      - INV-OUTPUT-SHUFFLE: Shuffle opt-in
    """

    def format(
        self,
        result: HuntResult,
        shuffle: bool = False,
    ) -> dict[str, Any]:
        """
        Format hunt result for output.

        Args:
            result: HuntResult to format
            shuffle: Whether to shuffle rows (T2 opt-in)

        Returns:
            Formatted output dict
        """
        rows = list(result.rows)

        # Apply shuffle if requested (INV-OUTPUT-SHUFFLE)
        if shuffle:
            rng = secrets.SystemRandom()
            rng.shuffle(rows)

        # Build column list
        columns = self._get_columns(result)

        # Build table rows
        table_rows = [
            self._format_row(row) for row in rows
        ]

        output: dict[str, Any] = {
            "metadata": {
                "hypothesis_id": result.hypothesis_id,
                "executed_at": result.timestamp.isoformat(),
            },
            "summary": {
                "total_variants": result.total_variants,
                "variants_computed": result.variants_computed,
                "compute_time_seconds": result.compute_time_seconds,
                "status": result.status.value,
            },
            "table": {
                "columns": columns,
                "rows": table_rows,
                "sort_order": "GRID_ORDER",
                "grid_order_declaration": result.grid_order_declaration,
                "shuffle_applied": shuffle,
            },
            "provenance": {
                "query_string": result.provenance.query_string,
                "dataset_hash": result.provenance.dataset_hash,
                "governance_hash": result.provenance.governance_hash,
                "strategy_config_hash": result.provenance.strategy_config_hash,
            },
        }

        # Add abort metadata if present (INV-HUNT-PARTIAL-WATERMARK)
        if result.abort_metadata:
            output["abort_metadata"] = {
                "abort_notice": result.abort_metadata.abort_notice,
                "computed_region": {
                    "dimensions": result.abort_metadata.computed_region.dimensions,
                    "variants_computed": result.abort_metadata.computed_region.variants_computed,
                },
                "uncomputed_region": {
                    "dimensions": result.abort_metadata.uncomputed_region.dimensions,
                    "variants_remaining": result.abort_metadata.uncomputed_region.variants_remaining,
                },
                "completeness_mask": result.abort_metadata.completeness_mask,
            }

        return output

    def _get_columns(self, result: HuntResult) -> list[str]:
        """Get column names from result."""
        if not result.rows:
            return []

        first_row = result.rows[0]
        param_cols = list(first_row.parameters.keys())
        metric_cols = list(first_row.metrics.keys())
        return param_cols + metric_cols

    def _format_row(self, row: VariantResult) -> dict[str, Any]:
        """Format a single row."""
        formatted = dict(row.parameters)
        formatted.update(row.metrics)
        return formatted


# =============================================================================
# OUTPUT VALIDATOR
# =============================================================================


class OutputValidator:
    """
    Validates hunt output for forbidden content.

    Rejects ranking, synthesis, recommendations.
    """

    def validate(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate output for forbidden content.

        Args:
            output: Output to validate

        Returns:
            (valid, errors)
        """
        errors: list[str] = []

        # Check for forbidden fields
        def check_dict(d: dict[str, Any], path: str = "") -> None:
            for key, value in d.items():
                full_path = f"{path}.{key}" if path else key
                if key.lower() in FORBIDDEN_OUTPUT_FIELDS:
                    errors.append(f"Forbidden field '{key}' at {full_path}")
                if isinstance(value, dict):
                    check_dict(value, full_path)
                elif isinstance(value, str):
                    for section in FORBIDDEN_SECTIONS:
                        if section.lower() in value.lower():
                            errors.append(
                                f"Forbidden section '{section}' found in {full_path}"
                            )

        check_dict(output)

        return (len(errors) == 0, errors)

    def validate_no_sort_request(self, request: str) -> tuple[bool, str]:
        """
        Validate that no sort request is made.

        Args:
            request: Sort request string

        Returns:
            (valid, error)
        """
        request_lower = request.lower()

        forbidden_sorts = [
            "sort by sharpe",
            "sort by win_rate",
            "sort by performance",
            "sort by metric",
            "best first",
            "highest first",
            "top performers",
        ]

        for forbidden in forbidden_sorts:
            if forbidden in request_lower:
                return (
                    False,
                    f"Sort request '{request}' forbidden. "
                    "Output is in GRID_ORDER. Use shuffle opt-in if needed.",
                )

        return (True, "")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "HuntOutputFormatter",
    "OutputValidator",
    "FORBIDDEN_OUTPUT_FIELDS",
    "FORBIDDEN_SECTIONS",
]
