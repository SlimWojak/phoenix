"""
Phoenix Hooks — S40 Track C
===========================

Pre-commit and runtime constitutional enforcement.
The physical wall of the constitution.

INVARIANTS ENFORCED:
  - INV-SCALAR-BAN: No scalar scores
  - INV-NO-AGGREGATE-SCALAR: No hidden averages
  - INV-NEUTRAL-ADJECTIVES: No causal language
  - INV-NO-GRADE-RECONSTRUCTION: No grades
"""

from .pre_commit_linter import (
    PreCommitLinter,
    LintRule,
    Violation,
    ViolationSeverity,
)
from .scalar_ban_hook import (
    ScalarBanHook,
    SCALAR_PATTERNS,
    AVG_PATTERNS,
    CAUSAL_PATTERNS,
    GRADE_PATTERNS,
)

__all__ = [
    "PreCommitLinter",
    "LintRule",
    "Violation",
    "ViolationSeverity",
    "ScalarBanHook",
    "SCALAR_PATTERNS",
    "AVG_PATTERNS",
    "CAUSAL_PATTERNS",
    "GRADE_PATTERNS",
]
