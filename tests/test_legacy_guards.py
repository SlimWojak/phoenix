"""
Tests for legacy deprecation guards and synthetic output isolation (S60 T3).

INVARIANTS:
  INV-LEGACY-FALLBACK-GATED: Legacy paths require explicit flag
  INV-SYNTHETIC-DATA-ISOLATION: Hunt/Validation outputs marked EXPLORATORY
"""

from __future__ import annotations

import importlib
import os
import sys
import warnings


class TestCFPBeadAdapterDeprecation:
    """INV-LEGACY-FALLBACK-GATED: cfp.bead_adapter warns without flag."""

    def test_import_without_flag_emits_warning(self) -> None:
        old_val = os.environ.pop("LEGACY_BACKEND", None)
        if "cfp.bead_adapter" in sys.modules:
            del sys.modules["cfp.bead_adapter"]
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                import cfp.bead_adapter  # noqa: F401

                deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
                assert len(deprecation_warnings) >= 1
                assert "DEPRECATED" in str(deprecation_warnings[0].message)
        finally:
            if old_val is not None:
                os.environ["LEGACY_BACKEND"] = old_val
            if "cfp.bead_adapter" in sys.modules:
                del sys.modules["cfp.bead_adapter"]

    def test_import_with_flag_no_warning(self) -> None:
        old_val = os.environ.get("LEGACY_BACKEND")
        os.environ["LEGACY_BACKEND"] = "true"
        if "cfp.bead_adapter" in sys.modules:
            del sys.modules["cfp.bead_adapter"]
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                importlib.import_module("cfp.bead_adapter")
                deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
                assert len(deprecation_warnings) == 0
        finally:
            if old_val is None:
                os.environ.pop("LEGACY_BACKEND", None)
            else:
                os.environ["LEGACY_BACKEND"] = old_val
            if "cfp.bead_adapter" in sys.modules:
                del sys.modules["cfp.bead_adapter"]


class TestHuntSyntheticIsolation:
    """INV-SYNTHETIC-DATA-ISOLATION: Hunt outputs self-identify as synthetic."""

    def test_hunt_result_has_synthetic_flag(self) -> None:
        from hunt.executor import HuntResult

        result = HuntResult(hypothesis_id="test-001")
        assert result.synthetic is True
        assert result.mode == "EXPLORATORY"
        assert result.do_not_use_for_decisions is True
        assert result.generator == "RNG_STUB"

    def test_hunt_result_synthetic_in_fields(self) -> None:
        from dataclasses import fields

        from hunt.executor import HuntResult

        field_names = {f.name for f in fields(HuntResult)}
        assert "synthetic" in field_names
        assert "mode" in field_names
        assert "do_not_use_for_decisions" in field_names

    def test_hunt_output_missing_synthetic_fails(self) -> None:
        """If someone removes synthetic fields from HuntResult, this catches it."""
        from dataclasses import fields

        from hunt.executor import HuntResult

        field_names = {f.name for f in fields(HuntResult)}
        required_synthetic_fields = {"synthetic", "generator", "mode", "do_not_use_for_decisions"}
        missing = required_synthetic_fields - field_names
        assert missing == set(), f"Missing synthetic isolation fields: {missing}"
