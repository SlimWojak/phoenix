"""
Hooks Tests — S40 Track C
=========================

Tests for pre-commit and runtime constitutional enforcement.

INVARIANTS:
  - INV-HOOK-1: Pre-commit blocks scalar_score
  - INV-HOOK-2: Pre-commit blocks causal language
  - INV-HOOK-3: Runtime catches missing provenance
  - INV-HOOK-4: Runtime catches ranking fields
"""
