"""
Pre-Commit Linter — S40 Track C
===============================

Constitutional enforcement at commit time.
Catches heresy before it enters the codebase.

INVARIANTS:
  INV-HOOK-1: Blocks scalar_score in new code
  INV-HOOK-2: Blocks causal language
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


# =============================================================================
# ENUMS
# =============================================================================


class ViolationSeverity(str, Enum):
    """Severity levels for violations."""

    ERROR = "ERROR"  # Blocks commit
    WARNING = "WARNING"  # Logged but doesn't block
    INFO = "INFO"  # Informational only


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Violation:
    """A constitutional violation found in code."""

    rule_id: str
    file: Path
    line: int
    column: int
    message: str
    matched_text: str
    severity: ViolationSeverity = ViolationSeverity.ERROR
    context: str = ""  # Surrounding code for context

    def __str__(self) -> str:
        return (
            f"{self.severity.value}: {self.file}:{self.line}:{self.column} - "
            f"{self.rule_id}: {self.message} (matched: '{self.matched_text}')"
        )


@dataclass
class LintRule:
    """A linting rule definition."""

    id: str
    name: str
    patterns: list[re.Pattern]
    message: str
    severity: ViolationSeverity = ViolationSeverity.ERROR

    # Optional filter to exclude certain contexts
    exclude_filter: Callable[[str, str], bool] | None = None

    # File patterns to include/exclude
    include_files: list[str] = field(default_factory=lambda: ["*.py"])
    exclude_files: list[str] = field(default_factory=list)


# =============================================================================
# PRE-COMMIT LINTER
# =============================================================================


class PreCommitLinter:
    """
    Constitutional linter for pre-commit hooks.

    Scans code for patterns that violate the constitution:
    - Scalar scores
    - Hidden averages
    - Causal language
    - Grade reconstruction

    Usage:
        linter = PreCommitLinter(rules=[...])
        violations = linter.check_staged()
        if violations:
            print(linter.format_report(violations))
            sys.exit(1)

    INVARIANTS:
      INV-HOOK-1: Blocks scalar_score
      INV-HOOK-2: Blocks causal language
    """

    def __init__(self, rules: list[LintRule]):
        self.rules = rules

    def check_file(self, filepath: Path) -> list[Violation]:
        """
        Scan a single file for violations.

        Args:
            filepath: Path to file to scan

        Returns:
            List of violations found
        """
        violations = []

        if not filepath.exists():
            return violations

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            return violations

        lines = content.split("\n")

        for rule in self.rules:
            # Check file pattern matching
            if not self._file_matches_rule(filepath, rule):
                continue

            # Scan each line
            for line_num, line in enumerate(lines, start=1):
                for pattern in rule.patterns:
                    for match in pattern.finditer(line):
                        # Check exclude filter
                        if rule.exclude_filter:
                            if rule.exclude_filter(line, match.group()):
                                continue

                        # Get context (surrounding lines)
                        context = self._get_context(lines, line_num, 2)

                        violations.append(
                            Violation(
                                rule_id=rule.id,
                                file=filepath,
                                line=line_num,
                                column=match.start() + 1,
                                message=rule.message,
                                matched_text=match.group(),
                                severity=rule.severity,
                                context=context,
                            )
                        )

        return violations

    def check_files(self, files: list[Path]) -> list[Violation]:
        """
        Check multiple files for violations.

        Args:
            files: List of file paths

        Returns:
            All violations found
        """
        all_violations = []
        for filepath in files:
            all_violations.extend(self.check_file(filepath))
        return all_violations

    def check_staged(self) -> list[Violation]:
        """
        Check all staged files for violations.

        Uses git diff --cached to find staged files.

        Returns:
            All violations in staged files
        """
        staged_files = self._get_staged_files()
        return self.check_files(staged_files)

    def check_directory(self, directory: Path, recursive: bool = True) -> list[Violation]:
        """
        Check all Python files in directory.

        Args:
            directory: Directory to scan
            recursive: If True, scan subdirectories

        Returns:
            All violations found
        """
        if recursive:
            files = list(directory.rglob("*.py"))
        else:
            files = list(directory.glob("*.py"))

        return self.check_files(files)

    def format_report(self, violations: list[Violation]) -> str:
        """
        Format violations as human-readable report.

        Args:
            violations: List of violations

        Returns:
            Formatted report string
        """
        if not violations:
            return "✓ No constitutional violations found."

        lines = [
            "═" * 60,
            "CONSTITUTIONAL VIOLATIONS DETECTED",
            "═" * 60,
            "",
        ]

        # Group by file
        by_file: dict[Path, list[Violation]] = {}
        for v in violations:
            by_file.setdefault(v.file, []).append(v)

        for filepath, file_violations in by_file.items():
            lines.append(f"📄 {filepath}")
            lines.append("-" * 40)

            for v in sorted(file_violations, key=lambda x: x.line):
                lines.append(
                    f"  L{v.line}:{v.column} [{v.severity.value}] {v.rule_id}"
                )
                lines.append(f"    {v.message}")
                lines.append(f"    Matched: '{v.matched_text}'")
                if v.context:
                    lines.append(f"    Context:")
                    for ctx_line in v.context.split("\n"):
                        lines.append(f"      {ctx_line}")
                lines.append("")

        # Summary
        errors = sum(1 for v in violations if v.severity == ViolationSeverity.ERROR)
        warnings = sum(1 for v in violations if v.severity == ViolationSeverity.WARNING)

        lines.append("═" * 60)
        lines.append(f"SUMMARY: {errors} errors, {warnings} warnings")
        if errors > 0:
            lines.append("❌ COMMIT BLOCKED - Fix errors before committing")
        lines.append("═" * 60)

        return "\n".join(lines)

    def _file_matches_rule(self, filepath: Path, rule: LintRule) -> bool:
        """Check if file matches rule's include/exclude patterns."""
        filename = filepath.name
        filepath_str = str(filepath)

        # Check excludes first
        for pattern in rule.exclude_files:
            if pattern in filepath_str or filepath.match(pattern):
                return False

        # Check includes - use simple suffix matching for common patterns
        for pattern in rule.include_files:
            if pattern.startswith("*"):
                # Glob pattern like "*.py"
                suffix = pattern[1:]  # ".py"
                if filename.endswith(suffix):
                    return True
            elif filepath.match(pattern):
                return True

        return False

    def _get_context(self, lines: list[str], line_num: int, context_lines: int) -> str:
        """Get surrounding lines for context."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)

        context_parts = []
        for i in range(start, end):
            prefix = "→ " if i == line_num - 1 else "  "
            context_parts.append(f"{prefix}{i + 1}: {lines[i]}")

        return "\n".join(context_parts)

    def _get_staged_files(self) -> list[Path]:
        """Get list of staged files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = [
                Path(f.strip())
                for f in result.stdout.strip().split("\n")
                if f.strip() and f.endswith(".py")
            ]
            return files
        except subprocess.CalledProcessError:
            return []


# =============================================================================
# UTILITIES
# =============================================================================


def has_blocking_violations(violations: list[Violation]) -> bool:
    """Check if any violations block the commit."""
    return any(v.severity == ViolationSeverity.ERROR for v in violations)


def run_precommit_check(rules: list[LintRule]) -> int:
    """
    Run pre-commit check and return exit code.

    Returns:
        0 if no blocking violations, 1 otherwise
    """
    linter = PreCommitLinter(rules)
    violations = linter.check_staged()

    if violations:
        print(linter.format_report(violations))
        if has_blocking_violations(violations):
            return 1

    return 0
