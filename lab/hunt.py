"""
Hunt Engine — Hypothesis Testing Surface
========================================

NL hypothesis → HPG → variations → backtest → survivors

INVARIANTS:
- INV-HUNT-HPG-1: Hunt only accepts valid HPG JSON
- INV-HUNT-DET-1: Identical inputs → identical outputs
- INV-HUNT-CAP-1: Maximum 50 variations
- INV-HUNT-BEAD-1: Every Hunt emits exactly one HUNT bead
- INV-HUNT-SORT-1: Results sorted by variant_id before filtering

Operator experience:
1. Olya speaks hypothesis ("Test FVG entries after 8:30am London")
2. Claude classifies as DISPATCH:HUNT
3. Phoenix routes to Hunt worker
4. Hunt returns survivors + HUNT bead
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from .backtester import Backtester, BacktestResult, DataWindow
from .hpg_parser import HPG, HPGParser, Session, SignalType, StopModel, ValidationResult
from .variation_generator import VariationGenerator, VariationResult

# Import BeadStore for integration (optional dependency)
try:
    from memory.bead_store import BeadStore
except ImportError:
    BeadStore = None  # type: ignore[misc, assignment]

# =============================================================================
# RESULT TYPES
# =============================================================================


@dataclass
class Survivor:
    """Strategy variant that passed survival criteria."""

    variant_id: str
    params: dict[str, Any]
    sharpe: float
    win_rate: float
    max_drawdown: float
    profit_factor: float
    total_trades: int


@dataclass
class HuntResult:
    """Complete Hunt result."""

    hunt_id: str
    hypothesis_text: str
    hpg: HPG
    status: str  # COMPLETE, FAILED, TIMEOUT

    # Variation info
    variants_tested: int
    variation_metadata: dict[str, str]

    # Survivors
    survivors: list[Survivor]
    survivor_criteria_hash: str

    # Bead
    bead_id: str | None = None
    bead_hash: str | None = None

    # Timing
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    duration_ms: float = 0.0

    # Errors
    errors: list[str] = field(default_factory=list)

    def to_summary(self, max_tokens: int = 500) -> str:
        """Generate summary for Lens injection."""
        if self.status == "FAILED":
            return f"Hunt FAILED: {'; '.join(self.errors)}"

        best = self.survivors[0] if self.survivors else None
        best_info = (
            f"BEST: {best.variant_id} (Sharpe {best.sharpe:.2f})" if best else "None"
        )

        return f"""Hunt complete.
SURVIVORS: {len(self.survivors)}/{self.variants_tested}
{best_info}
BEAD: {self.bead_id}"""


# =============================================================================
# HUNT ENGINE
# =============================================================================


class HuntEngine:
    """
    Hunt Engine — hypothesis testing pipeline.

    Pipeline:
    1. Parse NL → HPG (via HPGParser)
    2. Validate HPG (schema check)
    3. Generate variations (systematic + chaos)
    4. Backtest each variant
    5. Filter survivors (threshold criteria)
    6. Emit HUNT bead

    INVARIANT: INV-HUNT-BEAD-1 — Every Hunt emits exactly one HUNT bead
    """

    def __init__(
        self,
        parser: HPGParser | None = None,
        generator: VariationGenerator | None = None,
        backtester: Backtester | None = None,
        bead_store: object | None = None,
    ) -> None:
        """Initialize Hunt engine with components."""
        self._parser = parser or HPGParser()
        self._generator = generator or VariationGenerator()
        self._backtester = backtester or Backtester()
        self._bead_store = bead_store
        self._survivor_criteria = self._load_survivor_criteria()

    def _load_survivor_criteria(self) -> dict:
        """Load survivor criteria from config."""
        criteria_path = Path(__file__).parent.parent / "config" / "survivor_criteria.yaml"
        if criteria_path.exists():
            with open(criteria_path) as f:
                config = yaml.safe_load(f)
                return config.get("thresholds", {})
        # Defaults
        return {
            "sharpe_min": {"value": 1.0},
            "win_rate_min": {"value": 0.45},
            "max_drawdown_max": {"value": 0.15},
            "min_trades": {"value": 10},
            "profit_factor_min": {"value": 1.2},
        }

    def _compute_criteria_hash(self) -> str:
        """Compute hash of survivor criteria."""
        data = json.dumps(self._survivor_criteria, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def run(
        self,
        hypothesis_text: str,
        session_id: str,
        data_window: DataWindow | None = None,
    ) -> HuntResult:
        """
        Run Hunt pipeline.

        Args:
            hypothesis_text: Natural language hypothesis
            session_id: Session identifier
            data_window: Time range for backtest (default: 90 days)

        Returns:
            HuntResult with survivors and bead
        """
        import time

        start_time = time.perf_counter()
        hunt_id = str(uuid.uuid4())
        data_window = data_window or DataWindow.default()

        # 1. Parse NL → HPG
        hpg = self._parse_to_hpg(hypothesis_text)
        if hpg is None:
            return self._fail_result(
                hunt_id, hypothesis_text, ["Failed to parse hypothesis to HPG"]
            )

        # 2. Validate HPG
        validation = self._validate_hpg(hpg)
        if not validation.valid:
            return self._fail_result(hunt_id, hypothesis_text, validation.errors, hpg)

        # 3. Generate variations
        variation_result = self._generate_variations(hpg)

        # 4. Backtest all variants
        backtest_results = self._backtest_variants(variation_result, data_window)

        # 5. Filter survivors
        survivors = self._filter_survivors(backtest_results)

        # 6. Create result
        duration_ms = (time.perf_counter() - start_time) * 1000

        result = HuntResult(
            hunt_id=hunt_id,
            hypothesis_text=hypothesis_text,
            hpg=hpg,
            status="COMPLETE",
            variants_tested=len(variation_result.variants),
            variation_metadata={
                "generator_version": variation_result.generator_version,
                "mutation_plan_hash": variation_result.mutation_plan_hash,
            },
            survivors=survivors,
            survivor_criteria_hash=self._compute_criteria_hash(),
            started_at=datetime.now(UTC) - timedelta(milliseconds=duration_ms),
            completed_at=datetime.now(UTC),
            duration_ms=duration_ms,
        )

        # 7. Emit HUNT bead (INV-HUNT-BEAD-1)
        bead_id, bead_hash = self._emit_bead(result, data_window)
        result.bead_id = bead_id
        result.bead_hash = bead_hash

        return result

    def _parse_to_hpg(self, text: str) -> HPG | None:
        """Parse natural language to HPG."""
        return self._parser.parse(text)

    def _validate_hpg(self, hpg: HPG) -> ValidationResult:
        """Validate HPG against schema."""
        return self._parser.validate(hpg)

    def _generate_variations(self, hpg: HPG) -> VariationResult:
        """Generate HPG variations."""
        return self._generator.generate(hpg)

    def _backtest_variants(
        self, variation_result: VariationResult, data_window: DataWindow
    ) -> list[BacktestResult]:
        """Backtest all variants."""
        variants = list(zip(variation_result.variants, variation_result.variant_ids, strict=True))
        return self._backtester.run_batch(variants, data_window)

    def _filter_survivors(self, results: list[BacktestResult]) -> list[Survivor]:
        """
        Filter backtest results by survivor criteria.

        ALL thresholds must pass (logic: ALL).
        """
        survivors = []

        sharpe_min = self._survivor_criteria.get("sharpe_min", {}).get("value", 1.0)
        win_rate_min = self._survivor_criteria.get("win_rate_min", {}).get("value", 0.45)
        max_dd_max = self._survivor_criteria.get("max_drawdown_max", {}).get("value", 0.15)
        min_trades = self._survivor_criteria.get("min_trades", {}).get("value", 10)
        pf_min = self._survivor_criteria.get("profit_factor_min", {}).get("value", 1.2)

        for result in results:
            # Check ALL criteria
            if (
                result.sharpe >= sharpe_min
                and result.win_rate >= win_rate_min
                and result.max_drawdown <= max_dd_max
                and result.total_trades >= min_trades
                and result.profit_factor >= pf_min
            ):
                survivors.append(
                    Survivor(
                        variant_id=result.variant_id,
                        params=result.to_dict(),
                        sharpe=result.sharpe,
                        win_rate=result.win_rate,
                        max_drawdown=result.max_drawdown,
                        profit_factor=result.profit_factor,
                        total_trades=result.total_trades,
                    )
                )

        # Sort by Sharpe (best first)
        survivors.sort(key=lambda s: s.sharpe, reverse=True)
        return survivors

    def _emit_bead(
        self, result: HuntResult, data_window: DataWindow
    ) -> tuple[str, str]:
        """
        Emit HUNT bead.

        INVARIANT: INV-HUNT-BEAD-1 — Every Hunt emits exactly one HUNT bead
        """
        bead_id = f"HUNT-{result.hunt_id[:8]}"

        # Build bead content
        bead_content = {
            "bead_id": bead_id,
            "bead_type": "HUNT",
            "prev_bead_id": None,  # TODO: Chain to previous
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "signer": "system",
            "version": "1.0",
            "hpg_version": result.hpg.hpg_version,
            "hypothesis_text": result.hypothesis_text,
            "hpg_json": result.hpg.to_dict(),
            "data_window": {
                "start": data_window.start.isoformat(),
                "end": data_window.end.isoformat(),
            },
            "variants_tested": result.variants_tested,
            "survivors": [
                {
                    "variant_id": s.variant_id,
                    "params": s.params,
                    "sharpe": s.sharpe,
                    "win_rate": s.win_rate,
                    "max_drawdown": s.max_drawdown,
                }
                for s in result.survivors
            ],
            "random_seed": result.hpg.random_seed,
            "variation_metadata": result.variation_metadata,
            "survivor_criteria_hash": result.survivor_criteria_hash,
        }

        # Compute bead hash
        bead_hash = hashlib.sha256(
            json.dumps(bead_content, sort_keys=True).encode()
        ).hexdigest()[:16]
        bead_content["bead_hash"] = bead_hash

        # Store bead (if BeadStore available)
        if self._bead_store is not None:
            try:
                self._bead_store.write_dict(bead_content)
            except Exception:  # noqa: S110
                pass  # Non-blocking bead emission

        return bead_id, bead_hash

    def _fail_result(
        self,
        hunt_id: str,
        hypothesis_text: str,
        errors: list[str],
        hpg: HPG | None = None,
    ) -> HuntResult:
        """Create failed hunt result."""
        return HuntResult(
            hunt_id=hunt_id,
            hypothesis_text=hypothesis_text,
            hpg=hpg or HPG(
                hpg_version="1.0",
                signal_type=SignalType.FVG,
                pair="EURUSD",
                session=Session.ANY,
                stop_model=StopModel.NORMAL,
                risk_percent=1.0,
                random_seed=0,
            ),
            status="FAILED",
            variants_tested=0,
            variation_metadata={},
            survivors=[],
            survivor_criteria_hash="",
            errors=errors,
        )


