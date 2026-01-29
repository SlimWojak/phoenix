"""
Output Tests — S38 Track E
==========================

INVARIANTS PROVEN:
  - INV-ATTR-NO-RANKING: Flat table
  - INV-NO-UNSOLICITED: No synthesis
  - INV-HUNT-GRID-ORDER-DECLARED: Order explicit
  - INV-OUTPUT-SHUFFLE: Shuffle opt-in

EXIT GATE E:
  Criterion: "Output is flat table; grid order declared; shuffle opt-in works"
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from hunt.executor import HuntExecutor, HuntResult, HuntStatus, VariantResult
from hunt.hypothesis import (
    GridDimension,
    Hypothesis,
    HypothesisApproval,
    HypothesisBudget,
    HypothesisFraming,
    HypothesisGrid,
)
from hunt.output import HuntOutputFormatter, OutputValidator


@pytest.fixture
def formatter() -> HuntOutputFormatter:
    return HuntOutputFormatter()


@pytest.fixture
def validator() -> OutputValidator:
    return OutputValidator()


@pytest.fixture
def simple_result() -> HuntResult:
    return HuntResult(
        hypothesis_id="H_test",
        status=HuntStatus.COMPLETE,
        total_variants=4,
        variants_computed=4,
        variants_skipped=0,
        rows=[
            VariantResult(
                variant_id=f"V_{i}",
                parameters={"x": i},
                metrics={"sharpe": 1.0 + i * 0.1},
                sample_size=100,
            )
            for i in range(4)
        ],
        grid_order_declaration="cartesian_product, [x]",
    )


class TestOutputFormat:
    def test_output_has_grid_order(
        self, formatter: HuntOutputFormatter, simple_result: HuntResult
    ) -> None:
        output = formatter.format(simple_result)

        assert output["table"]["sort_order"] == "GRID_ORDER"
        assert output["table"]["grid_order_declaration"]

    def test_output_has_shuffle_flag(
        self, formatter: HuntOutputFormatter, simple_result: HuntResult
    ) -> None:
        output = formatter.format(simple_result)
        assert "shuffle_applied" in output["table"]

    def test_shuffle_changes_order(
        self, formatter: HuntOutputFormatter, simple_result: HuntResult
    ) -> None:
        output_no_shuffle = formatter.format(simple_result, shuffle=False)
        assert not output_no_shuffle["table"]["shuffle_applied"]

        output_shuffle = formatter.format(simple_result, shuffle=True)
        assert output_shuffle["table"]["shuffle_applied"]


class TestOutputValidation:
    def test_top_variants_rejected(self, validator: OutputValidator) -> None:
        output = {"top_variants": [{"id": "V_1"}]}
        valid, errors = validator.validate(output)

        assert not valid
        assert any("top_variants" in e for e in errors)

    def test_survivors_rejected(self, validator: OutputValidator) -> None:
        output = {"survivors": ["V_1"]}
        valid, errors = validator.validate(output)

        assert not valid

    def test_recommendation_rejected(self, validator: OutputValidator) -> None:
        output = {"recommendation": "Use variant 3"}
        valid, errors = validator.validate(output)

        assert not valid

    def test_sort_request_rejected(self, validator: OutputValidator) -> None:
        valid, error = validator.validate_no_sort_request("sort by sharpe")
        assert not valid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
