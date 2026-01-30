"""
Grid Expansion — S38 Track C
============================

Expand hypothesis grid into all variants.
Cartesian product of all dimensions.

INVARIANT: INV-HUNT-EXHAUSTIVE (compute ALL)
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any

from hunt.hypothesis import Hypothesis


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Variant:
    """A single parameter combination."""

    variant_id: str
    parameters: dict[str, Any]
    grid_position: int  # Position in grid order

    # NO: ranking, score, confidence, quality


@dataclass
class GridExpansion:
    """
    Expanded grid of variants.

    All combinations, no selection.
    """

    variants: list[Variant]
    total_variants: int
    order_declaration: str  # e.g., "cartesian_product, [dim1, dim2]"


# =============================================================================
# GRID EXPANDER
# =============================================================================


class GridExpander:
    """
    Expands hypothesis grid into all variants.

    Cartesian product of all dimensions.
    Order is deterministic: left-to-right by dimension order.

    INVARIANT: INV-HUNT-EXHAUSTIVE
    """

    def expand(self, hypothesis: Hypothesis) -> GridExpansion:
        """
        Expand hypothesis grid into all variants.

        Args:
            hypothesis: Hypothesis with grid to expand

        Returns:
            GridExpansion with ALL variants
        """
        grid = hypothesis.grid

        if not grid.dimensions:
            return GridExpansion(
                variants=[],
                total_variants=0,
                order_declaration="empty_grid",
            )

        # Get dimension names and values
        dim_names = [d.dimension for d in grid.dimensions]
        dim_values = [d.values for d in grid.dimensions]

        # Cartesian product
        combinations = list(itertools.product(*dim_values))

        # Create variants
        variants: list[Variant] = []
        for i, combo in enumerate(combinations):
            params = dict(zip(dim_names, combo))
            variant = Variant(
                variant_id=f"{hypothesis.hypothesis_id}_V{i:06d}",
                parameters=params,
                grid_position=i,
            )
            variants.append(variant)

        order_declaration = f"cartesian_product, {dim_names}"

        return GridExpansion(
            variants=variants,
            total_variants=len(variants),
            order_declaration=order_declaration,
        )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "Variant",
    "GridExpansion",
    "GridExpander",
]
