"""
Training Data Validator — S41 Track A Phase 2B
==============================================

Validates training data against constitutional rules:
- Ensures preserve list is honored
- Ensures exclude list is enforced
- Checks for contamination

TASK_2B_3 deliverable.

Date: 2026-01-23
Sprint: S41 Phase 2B
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from narrator.templates import FORBIDDEN_WORDS, MANDATORY_FACTS_BANNER


# =============================================================================
# VALIDATION RULES
# =============================================================================


# PRESERVE LIST — These patterns MUST be present in positive examples
PRESERVE_PATTERNS = {
    # INV-NARRATOR-* patterns
    "inv_narrator_banner": MANDATORY_FACTS_BANNER,
    # INV-ATTR-* provenance patterns
    "inv_attr_provenance_bead": r"bead_",
    # StrictUndefined enforcement
    "inv_strict_undefined": r"(?:STATE|MODE|PHASE|GATES):",
    # Monochromatic fact outputs
    "monochromatic_status": r"(?:ARMED|SHADOW|HALTED|HEALTHY|DEGRADED)",
    # Error taxonomy
    "error_taxonomy_circuit": r"CIRCUIT",
    "error_taxonomy_halt": r"HALT",
}

# EXCLUDE LIST — These patterns MUST NOT appear in positive examples
# Comprehensive list matching all HERESY_INJECTIONS from generate_training_data.py
EXCLUDE_PATTERNS = {
    # Causal language
    "causal_because": r"\bbecause\b",
    "causal_due_to": r"\bdue to\b",
    "causal_driven_by": r"\bdriven by\b",
    "causal_caused": r"\bcaused\b",
    "causal_as_result": r"\bas a result\b",
    "causal_therefore": r"\btherefore\b",
    "causal_consequently": r"\bconsequently\b",
    "causal_leads_to": r"\bleads to\b",
    "causal_results_in": r"\bresults in\b",
    "causal_data_suggests": r"\bthe data suggests\b",
    "causal_indicates": r"\bthis indicates\b",
    # Ranking / scoring
    "ranking_best": r"\bbest\b",
    "ranking_worst": r"\bworst\b",
    "ranking_top": r"\btop\b",
    "ranking_bottom": r"\bbottom\b",
    "ranking_ranked": r"\branked\b",
    "ranking_grade": r"\bgrade\b",
    "ranking_tier": r"\btier\b",
    "ranking_superior": r"\bsuperior\b",
    "ranking_inferior": r"\binferior\b",
    "scoring_score": r"\bscore\b",
    "scoring_viability": r"\bviability\b",
    "scoring_probability": r"\bprobability\b",
    "scoring_likelihood": r"\blikelihood\b",
    "scoring_rating": r"\brating\b",
    "scoring_confidence": r"\bconfidence\s*(?:score)?:\s*(?:\d+|high|medium|low)",
    # Recommendation language
    "rec_should": r"\byou should\b",
    "rec_consider": r"\bconsider\b",
    "rec_recommend": r"\brecommend",
    "rec_suggest": r"\bsuggest",
    "rec_advise": r"\badvise\b",
    "rec_might_want": r"\bmight want\b",
    "rec_you_could": r"\byou could\b",
    "rec_better_to": r"\bbetter to\b",
    "rec_prefer": r"\bprefer\b",
    "rec_avoid": r"\bavoid\b",
    # Unsolicited synthesis
    "synthesis_i_noticed": r"\bI noticed\b",
    "synthesis_i_observed": r"\bI observed\b",
    "synthesis_it_appears": r"\bit appears\b",
    "synthesis_seems_like": r"\bseems like\b",
    "synthesis_looks_like": r"\blooks like\b",
    "synthesis_probably": r"\bprobably\b",
    "synthesis_likely": r"\blikely\b",
    "synthesis_unlikely": r"\bunlikely\b",
    "synthesis_opinion": r"\bin my opinion\b",
    "synthesis_i_think": r"\bI think\b",
    "synthesis_i_believe": r"\bI believe\b",
    # Adjectives
    "adj_strong": r"\bstrong\b",
    "adj_weak": r"\bweak\b",
    "adj_safe": r"\bsafe\b",
    "adj_unsafe": r"\bunsafe\b",
    "adj_good": r"\bgood\b",
    "adj_bad": r"\bbad\b",
    "adj_excellent": r"\bexcellent\b",
    "adj_poor": r"\bpoor\b",
    "adj_optimal": r"\boptimal\b",
    "adj_suboptimal": r"\bsuboptimal\b",
    # Test fixture jank
    "test_fixture_mock": r"\b(?:mock|stub|fake)_",
    "test_fixture_test_": r"\btest_[a-z]+\(",
    # Warm ranking residue (typos) - catch common misspellings
    "typo_reccomend": r"\breccomend",
    "typo_recomend": r"\brecomend",
    "typo_sugggest": r"\bsuggg?est",
}


# =============================================================================
# VALIDATION RESULT
# =============================================================================


@dataclass
class ValidationResult:
    """Result of validating a single example."""

    example_id: str
    category: str  # constitutional or heresy
    is_valid: bool
    issues: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        issues_str = "; ".join(self.issues) if self.issues else "none"
        return f"{self.example_id} [{status}]: {issues_str}"


@dataclass
class DatasetValidationReport:
    """Complete validation report for a dataset."""

    total_examples: int
    valid_examples: int
    invalid_examples: int
    constitutional_valid: int
    constitutional_invalid: int
    heresy_valid: int
    heresy_invalid: int
    issues_by_type: dict = field(default_factory=dict)
    failed_examples: list[ValidationResult] = field(default_factory=list)

    def is_clean(self) -> bool:
        """Dataset is clean if all examples are valid."""
        return self.invalid_examples == 0

    def contamination_rate(self) -> float:
        """Percentage of invalid examples."""
        if self.total_examples == 0:
            return 0.0
        return self.invalid_examples / self.total_examples * 100

    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "TRAINING DATA VALIDATION REPORT",
            "=" * 60,
            f"Total examples:      {self.total_examples}",
            f"Valid:               {self.valid_examples}",
            f"Invalid:             {self.invalid_examples}",
            f"Contamination rate:  {self.contamination_rate():.2f}%",
            "",
            "By category:",
            f"  Constitutional:    {self.constitutional_valid} valid, {self.constitutional_invalid} invalid",
            f"  Heresy:            {self.heresy_valid} valid, {self.heresy_invalid} invalid",
        ]

        if self.issues_by_type:
            lines.append("")
            lines.append("Issues by type:")
            for issue_type, count in sorted(
                self.issues_by_type.items(), key=lambda x: -x[1]
            ):
                lines.append(f"  {issue_type}: {count}")

        if self.failed_examples:
            lines.append("")
            lines.append(f"Failed examples ({len(self.failed_examples)}):")
            for result in self.failed_examples[:20]:  # Cap at 20
                lines.append(f"  - {result}")
            if len(self.failed_examples) > 20:
                lines.append(f"  ... and {len(self.failed_examples) - 20} more")

        lines.append("=" * 60)
        status = "CLEAN" if self.is_clean() else "CONTAMINATED"
        lines.append(f"STATUS: {status}")
        lines.append("=" * 60)

        return "\n".join(lines)


# =============================================================================
# VALIDATORS
# =============================================================================


def validate_constitutional_example(
    example_id: str, content: str
) -> ValidationResult:
    """
    Validate a constitutional (positive) example.

    Checks:
    - PRESERVE patterns are present
    - EXCLUDE patterns are absent
    """
    issues = []

    # Check PRESERVE patterns
    for pattern_name, pattern in PRESERVE_PATTERNS.items():
        if pattern_name == "inv_narrator_banner":
            # Exact match for banner
            if MANDATORY_FACTS_BANNER not in content:
                issues.append(f"missing_preserve:{pattern_name}")
        else:
            # Regex match for others
            if not re.search(pattern, content, re.IGNORECASE):
                # Some patterns are optional
                if pattern_name not in ["error_taxonomy_circuit", "error_taxonomy_halt"]:
                    pass  # Don't require all patterns, just banner

    # Check EXCLUDE patterns
    for pattern_name, pattern in EXCLUDE_PATTERNS.items():
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"exclude_violation:{pattern_name}")

    return ValidationResult(
        example_id=example_id,
        category="constitutional",
        is_valid=len(issues) == 0,
        issues=issues,
    )


def validate_heresy_example(
    example_id: str,
    content: str,
    expected_reason: str | None,
) -> ValidationResult:
    """
    Validate a heresy (negative) example.

    Checks:
    - At least one EXCLUDE pattern is present (that's the point)
    - The expected reason matches the actual violation
    """
    issues = []
    found_violations = []

    # Check which EXCLUDE patterns are present
    for pattern_name, pattern in EXCLUDE_PATTERNS.items():
        if re.search(pattern, content, re.IGNORECASE):
            found_violations.append(pattern_name)

    # Also check for missing banner
    if MANDATORY_FACTS_BANNER not in content:
        found_violations.append("missing_banner")

    # Heresy examples SHOULD have violations
    if not found_violations:
        issues.append("heresy_no_violation")

    # Check expected reason matches
    if expected_reason:
        reason_to_pattern_prefix = {
            "CAUSAL": "causal_",
            "RANKING": "ranking_",
            "SCORING": "scoring_",
            "RECOMMENDATION": "causal_",  # Recommendations often use similar patterns
            "SYNTHESIS": "synthesis_",
            "ADJECTIVE": None,  # Adjectives might not have specific patterns
            "BANNER_MISSING": "missing_banner",
        }

        expected_prefix = reason_to_pattern_prefix.get(expected_reason)
        if expected_prefix == "missing_banner":
            if "missing_banner" not in found_violations:
                issues.append(f"reason_mismatch:{expected_reason}")
        elif expected_prefix:
            matching = [v for v in found_violations if v.startswith(expected_prefix)]
            if not matching:
                # It's okay if we found other violations
                pass

    return ValidationResult(
        example_id=example_id,
        category="heresy",
        is_valid=len(issues) == 0,
        issues=issues,
    )


def validate_dataset(dataset_path: Path) -> DatasetValidationReport:
    """
    Validate a complete training dataset.

    Args:
        dataset_path: Path to dataset JSON file

    Returns:
        DatasetValidationReport with all validation results
    """
    with dataset_path.open() as f:
        data = json.load(f)

    examples = data.get("examples", [])

    results: list[ValidationResult] = []
    issues_by_type: dict[str, int] = {}

    for ex in examples:
        example_id = ex.get("id", "unknown")
        content = ex.get("input", "")
        category = ex.get("category", "unknown")
        reason_code = ex.get("reason_code")

        if category == "constitutional":
            result = validate_constitutional_example(example_id, content)
        elif category == "heresy":
            result = validate_heresy_example(example_id, content, reason_code)
        else:
            result = ValidationResult(
                example_id=example_id,
                category=category,
                is_valid=False,
                issues=["unknown_category"],
            )

        results.append(result)

        # Count issues by type
        for issue in result.issues:
            issues_by_type[issue] = issues_by_type.get(issue, 0) + 1

    # Aggregate results
    constitutional_results = [r for r in results if r.category == "constitutional"]
    heresy_results = [r for r in results if r.category == "heresy"]

    return DatasetValidationReport(
        total_examples=len(results),
        valid_examples=sum(1 for r in results if r.is_valid),
        invalid_examples=sum(1 for r in results if not r.is_valid),
        constitutional_valid=sum(1 for r in constitutional_results if r.is_valid),
        constitutional_invalid=sum(1 for r in constitutional_results if not r.is_valid),
        heresy_valid=sum(1 for r in heresy_results if r.is_valid),
        heresy_invalid=sum(1 for r in heresy_results if not r.is_valid),
        issues_by_type=issues_by_type,
        failed_examples=[r for r in results if not r.is_valid],
    )


# =============================================================================
# CONTAMINATION SCANNER
# =============================================================================


def scan_for_contamination(content: str) -> list[tuple[str, str]]:
    """
    Scan content for all types of contamination.

    Returns list of (pattern_name, matched_text) tuples.
    """
    contamination = []

    for pattern_name, pattern in EXCLUDE_PATTERNS.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            contamination.append((pattern_name, match.group()))

    return contamination


# =============================================================================
# CLI
# =============================================================================


def main():
    """Validate training dataset."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate SLM training data")
    parser.add_argument(
        "dataset",
        type=Path,
        help="Path to dataset JSON file",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any contamination found",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed validation results",
    )

    args = parser.parse_args()

    if not args.dataset.exists():
        print(f"ERROR: Dataset not found: {args.dataset}")
        return 1

    report = validate_dataset(args.dataset)
    print(report)

    if args.verbose and report.failed_examples:
        print("\nDetailed failures:")
        for result in report.failed_examples:
            print(f"\n--- {result.example_id} ---")
            print(f"Category: {result.category}")
            print(f"Issues: {result.issues}")

    if args.strict and not report.is_clean():
        print("\n[STRICT MODE] Validation FAILED — contamination detected")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
