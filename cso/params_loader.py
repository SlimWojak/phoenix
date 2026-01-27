"""
Params Loader — Calibratable Parameters
========================================

Loads and validates CSO parameters from config.
Emits CONFIG_CHANGE bead on parameter changes.

INVARIANT: INV-CSO-CAL-1
"Parameter recalibration triggers mandatory shadow period"
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class KillZone:
    """Kill zone timing."""

    start: str  # HH:MM
    end: str  # HH:MM


@dataclass
class CalibrationRules:
    """Rules for parameter calibration."""

    shadow_period_sessions: int
    bunny_required: bool
    auto_shadow_on_change: bool


@dataclass
class CSOParams:
    """CSO calibratable parameters."""

    version: str
    ready_min: float
    forming_min: float
    kill_zones: dict[str, KillZone]
    pair_weights: dict[str, float]
    calibration_rules: CalibrationRules
    params_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "ready_min": self.ready_min,
            "forming_min": self.forming_min,
            "kill_zones": {k: {"start": v.start, "end": v.end} for k, v in self.kill_zones.items()},
            "pair_weights": self.pair_weights,
            "calibration_rules": {
                "shadow_period_sessions": self.calibration_rules.shadow_period_sessions,
                "bunny_required": self.calibration_rules.bunny_required,
                "auto_shadow_on_change": self.calibration_rules.auto_shadow_on_change,
            },
            "params_hash": self.params_hash,
        }


@dataclass
class ValidationResult:
    """Result of params validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# PARAMS LOADER
# =============================================================================


class ParamsLoader:
    """
    Loads and validates CSO parameters.

    INVARIANT: INV-CSO-CAL-1
    Parameter changes trigger CONFIG_CHANGE bead + shadow mode.
    """

    DEFAULT_PATH = Path(__file__).parent.parent / "config" / "cso_params.yaml"

    def __init__(
        self,
        config_path: Path | None = None,
        bead_store: Any | None = None,
    ) -> None:
        """
        Initialize params loader.

        Args:
            config_path: Path to cso_params.yaml
            bead_store: BeadStore for CONFIG_CHANGE beads
        """
        self._config_path = config_path or self.DEFAULT_PATH
        self._bead_store = bead_store
        self._current_params: CSOParams | None = None
        self._current_hash: str = ""

    def load(self) -> CSOParams:
        """
        Load parameters from config file.

        Returns:
            CSOParams object
        """
        if not self._config_path.exists():
            return self._default_params()

        with open(self._config_path) as f:
            data = yaml.safe_load(f)

        params = self._parse_params(data)
        params.params_hash = self._compute_hash(data)

        self._current_params = params
        self._current_hash = params.params_hash

        return params

    def reload(self) -> tuple[CSOParams, bool]:
        """
        Reload parameters, detect changes.

        Returns:
            (params, changed) tuple
        """
        old_hash = self._current_hash
        old_params = self._current_params

        params = self.load()
        changed = params.params_hash != old_hash

        if changed and old_params:
            self._on_change(old_params, params)

        return params, changed

    def validate(self, params: dict) -> ValidationResult:
        """
        Validate parameters against schema.

        Args:
            params: Raw params dict

        Returns:
            ValidationResult
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Required fields
        if "thresholds" not in params:
            errors.append("Missing 'thresholds' section")
        else:
            thresholds = params["thresholds"]
            if "ready_min" not in thresholds:
                errors.append("Missing thresholds.ready_min")
            if "forming_min" not in thresholds:
                errors.append("Missing thresholds.forming_min")

            # Validate ranges
            ready = thresholds.get("ready_min", 0)
            forming = thresholds.get("forming_min", 0)

            if not 0.0 <= ready <= 1.0:
                errors.append("ready_min must be 0.0-1.0")
            if not 0.0 <= forming <= 1.0:
                errors.append("forming_min must be 0.0-1.0")
            if forming >= ready:
                warnings.append("forming_min should be less than ready_min")

        # Kill zones
        if "kill_zones" in params:
            for zone_name, zone in params["kill_zones"].items():
                if "start" not in zone or "end" not in zone:
                    errors.append(f"Kill zone '{zone_name}' missing start/end")

        # Pair weights
        if "pair_weights" in params:
            for pair, weight in params["pair_weights"].items():
                if not 0.0 <= weight <= 2.0:
                    warnings.append(f"Pair weight for {pair} outside normal range")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _parse_params(self, data: dict) -> CSOParams:
        """Parse YAML data into CSOParams."""
        thresholds = data.get("thresholds", {})
        kill_zones_raw = data.get("kill_zones", {})
        pair_weights = data.get("pair_weights", {})
        cal_rules = data.get("calibration_rules", {})

        kill_zones = {
            name: KillZone(start=zone.get("start", "00:00"), end=zone.get("end", "23:59"))
            for name, zone in kill_zones_raw.items()
        }

        calibration_rules = CalibrationRules(
            shadow_period_sessions=cal_rules.get("shadow_period_sessions", 5),
            bunny_required=cal_rules.get("bunny_required", True),
            auto_shadow_on_change=cal_rules.get("auto_shadow_on_change", True),
        )

        return CSOParams(
            version=data.get("version", "1.0"),
            ready_min=thresholds.get("ready_min", 0.8),
            forming_min=thresholds.get("forming_min", 0.5),
            kill_zones=kill_zones,
            pair_weights=pair_weights,
            calibration_rules=calibration_rules,
        )

    def _default_params(self) -> CSOParams:
        """Return default parameters."""
        return CSOParams(
            version="1.0",
            ready_min=0.8,
            forming_min=0.5,
            kill_zones={
                "london": KillZone(start="07:00", end="11:00"),
                "new_york": KillZone(start="12:00", end="16:00"),
                "asia": KillZone(start="00:00", end="04:00"),
            },
            pair_weights={
                "EURUSD": 1.0,
                "GBPUSD": 1.0,
                "USDJPY": 0.9,
                "AUDUSD": 0.8,
                "USDCAD": 0.8,
                "NZDUSD": 0.7,
            },
            calibration_rules=CalibrationRules(
                shadow_period_sessions=5,
                bunny_required=True,
                auto_shadow_on_change=True,
            ),
        )

    def _compute_hash(self, data: dict) -> str:
        """Compute hash of params."""
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def _on_change(self, old: CSOParams, new: CSOParams) -> None:
        """
        Handle parameter change.

        INVARIANT: INV-CSO-CAL-1
        Emits CONFIG_CHANGE bead, triggers shadow mode.
        """
        if self._bead_store is None:
            return

        # Compute diff
        changed_keys = []
        old_dict = old.to_dict()
        new_dict = new.to_dict()

        for key in set(old_dict.keys()) | set(new_dict.keys()):
            if old_dict.get(key) != new_dict.get(key):
                changed_keys.append(key)

        # Emit CONFIG_CHANGE bead
        bead_content = {
            "config_file": "cso_params.yaml",
            "param_diff": {
                "changed_keys": changed_keys,
                "old_values": {k: old_dict.get(k) for k in changed_keys},
                "new_values": {k: new_dict.get(k) for k in changed_keys},
            },
            "old_hash": old.params_hash,
            "new_hash": new.params_hash,
            "operator": "system",
            "trigger": "MANUAL",
        }

        bead_dict = {
            "bead_id": f"CONFIG-{uuid.uuid4().hex[:8]}",
            "bead_type": "CONFIG_CHANGE",
            "prev_bead_id": None,
            "bead_hash": hashlib.sha256(
                json.dumps(bead_content, sort_keys=True).encode()
            ).hexdigest()[:16],
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "signer": "system",
            "version": "1.0",
            "content": bead_content,
        }

        try:
            self._bead_store.write_dict(bead_dict)
        except Exception:  # noqa: S110
            pass  # Non-blocking
