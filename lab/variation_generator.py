"""
Variation Generator — Systematic + Seeded Chaos Variations
==========================================================

Generates HPG variations for Hunt backtesting.

INVARIANTS:
- INV-HUNT-CAP-1: Maximum 50 variations
- INV-HUNT-DET-1: Seeded mutations are deterministic

Variation strategies:
1. Systematic: Grid over enums (session, stop_model)
2. Chaos: Seeded random mutations within bounds

BLOCKER FIX B1: Uses SEEDED_MUTATION_PLAN for deterministic chaos.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .hpg_parser import HPG, Session, StopModel

# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class VariationConfig:
    """Configuration for variation generation."""

    # Caps
    max_variations: int = 50  # INV-HUNT-CAP-1

    # Systematic variation
    vary_session: bool = True
    vary_stop_model: bool = True

    # Chaos variation
    chaos_enabled: bool = True
    chaos_mutations: int = 10  # Number of chaos variants

    # Risk variation bounds
    risk_min: float = 0.5
    risk_max: float = 2.0
    risk_step: float = 0.5

    # Generator version (for determinism)
    generator_version: str = "1.0"


# =============================================================================
# VARIATION RESULT
# =============================================================================


@dataclass
class VariationResult:
    """Result of variation generation."""

    variants: list[HPG]
    variant_ids: list[str]
    mutation_plan_hash: str
    generator_version: str
    capped: bool = False
    original_count: int = 0


# =============================================================================
# VARIATION GENERATOR
# =============================================================================


class VariationGenerator:
    """
    Generates HPG variations for Hunt backtesting.

    Two strategies:
    1. Systematic: Grid search over enum parameters
    2. Chaos: Seeded random mutations (deterministic)

    INVARIANT: INV-HUNT-CAP-1 — Maximum 50 variations
    INVARIANT: INV-HUNT-DET-1 — Seeded chaos is deterministic
    """

    def __init__(self, config: VariationConfig | None = None) -> None:
        """Initialize generator with config."""
        self.config = config or VariationConfig()

    def generate(self, base_hpg: HPG) -> VariationResult:
        """
        Generate variations from base HPG.

        Args:
            base_hpg: Base HPG to vary

        Returns:
            VariationResult with variants, IDs, and metadata
        """
        variants: list[HPG] = []
        variant_ids: list[str] = []

        # Always include base
        base_id = self._compute_variant_id(base_hpg, "base", 0)
        variants.append(base_hpg)
        variant_ids.append(base_id)

        # Systematic variations
        systematic = self._generate_systematic(base_hpg)
        for i, var in enumerate(systematic):
            var_id = self._compute_variant_id(var, "systematic", i)
            variants.append(var)
            variant_ids.append(var_id)

        # Chaos variations (seeded for determinism)
        if self.config.chaos_enabled:
            chaos = self._generate_chaos(base_hpg)
            for i, var in enumerate(chaos):
                var_id = self._compute_variant_id(var, "chaos", i)
                variants.append(var)
                variant_ids.append(var_id)

        # Track original count before cap
        original_count = len(variants)
        capped = False

        # Cap at max_variations (INV-HUNT-CAP-1)
        if len(variants) > self.config.max_variations:
            variants = variants[: self.config.max_variations]
            variant_ids = variant_ids[: self.config.max_variations]
            capped = True

        # Compute mutation plan hash for reproducibility
        plan_hash = self._compute_plan_hash(base_hpg, variant_ids)

        return VariationResult(
            variants=variants,
            variant_ids=variant_ids,
            mutation_plan_hash=plan_hash,
            generator_version=self.config.generator_version,
            capped=capped,
            original_count=original_count,
        )

    def _generate_systematic(self, base: HPG) -> list[HPG]:
        """Generate systematic grid variations."""
        variations: list[HPG] = []

        # Session variations
        if self.config.vary_session:
            for session in Session:
                if session != base.session:
                    var = self._clone_with_changes(base, session=session)
                    variations.append(var)

        # Stop model variations
        if self.config.vary_stop_model:
            for stop_model in StopModel:
                if stop_model != base.stop_model:
                    var = self._clone_with_changes(base, stop_model=stop_model)
                    variations.append(var)

        # Risk percent variations
        risk = self.config.risk_min
        while risk <= self.config.risk_max:
            if abs(risk - base.risk_percent) > 0.01:  # Avoid base duplicate
                var = self._clone_with_changes(base, risk_percent=risk)
                variations.append(var)
            risk += self.config.risk_step

        return variations

    def _generate_chaos(self, base: HPG) -> list[HPG]:
        """
        Generate seeded chaos variations.

        DETERMINISTIC: Same seed → same mutations.
        """
        variations: list[HPG] = []

        # Use base HPG's random_seed for chaos RNG
        rng = random.Random(base.random_seed)

        for i in range(self.config.chaos_mutations):
            # Deterministic mutation selection
            mutation_type = rng.choice(["session", "stop", "risk", "combo"])

            var = self._apply_mutation(base, mutation_type, rng, i)
            variations.append(var)

        return variations

    def _apply_mutation(
        self, base: HPG, mutation_type: str, rng: random.Random, step: int
    ) -> HPG:
        """Apply a single mutation (deterministic given RNG state)."""
        if mutation_type == "session":
            new_session = rng.choice(list(Session))
            return self._clone_with_changes(base, session=new_session)

        elif mutation_type == "stop":
            new_stop = rng.choice(list(StopModel))
            return self._clone_with_changes(base, stop_model=new_stop)

        elif mutation_type == "risk":
            new_risk = round(
                rng.uniform(self.config.risk_min, self.config.risk_max), 1
            )
            return self._clone_with_changes(base, risk_percent=new_risk)

        elif mutation_type == "combo":
            # Multiple mutations
            new_session = rng.choice(list(Session))
            new_stop = rng.choice(list(StopModel))
            return self._clone_with_changes(
                base, session=new_session, stop_model=new_stop
            )

        return base

    def _clone_with_changes(self, base: HPG, **changes: Any) -> HPG:
        """Clone HPG with specific changes."""
        data = base.to_dict()
        for key, value in changes.items():
            if isinstance(value, Enum):
                data[key] = value.value
            else:
                data[key] = value
        return HPG.from_dict(data)

    def _compute_variant_id(self, hpg: HPG, strategy: str, index: int) -> str:
        """
        Compute deterministic variant ID.

        Format: {strategy}_{index}_{hash8}
        """
        data = json.dumps(
            {"seed": hpg.random_seed, "strategy": strategy, "index": index},
            sort_keys=True,
        )
        hash8 = hashlib.sha256(data.encode()).hexdigest()[:8]
        return f"{strategy}_{index}_{hash8}"

    def _compute_plan_hash(self, base: HPG, variant_ids: list[str]) -> str:
        """Compute hash of the full mutation plan."""
        data = json.dumps(
            {
                "base_hash": base.compute_hash(),
                "variant_ids": variant_ids,
                "generator_version": self.config.generator_version,
            },
            sort_keys=True,
        )
        return hashlib.sha256(data.encode()).hexdigest()[:16]
