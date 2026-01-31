# OPUS_HYGIENE_PREFLIGHT.md

PURPOSE: Pre-build repo hygiene + preflight checks for Phoenix
TARGET: OPUS in Cursor
FORMAT: M2M (action-oriented, no prose)

---

## 1. CODE QUALITY ENFORCEMENT

RULES:
  max_lines_per_file: 300  # Forces decomposition
  mypy: --strict  # CI gate, no exceptions
  linter: ruff  # Pre-commit + CI
  no_print: true  # Logging only (structlog preferred)
  pre_commit: required

ENFORCEMENT:
  - CI blocks merge on ANY violation
  - Pre-commit hooks catch before push
  - These are laws, not suggestions

SETUP_COMMANDS:
  - pip install ruff mypy pre-commit structlog
  - pre-commit install
  - Create pyproject.toml with ruff + mypy config

---

## 2. .cursorrules

LOCATION: ~/echopeso/phoenix/.cursorrules

REQUIRED_CONTENT:
  - Project context (Phoenix constitutional trading)
  - DENSE M2M format preference
  - File size limit (300 lines)
  - Type hints required
  - No print() - use logging
  - Test file naming convention
  - Import ordering (stdlib, third-party, local)

ACTION: Create if missing, verify if exists

---

## 3. .env PREFLIGHT

CHECK:
  - .env exists in phoenix root
  - .env.example exists (template for others)
  - .gitignore excludes .env

KEYS_REQUIRED:
  ANTHROPIC_API_KEY: Claude API (for HIVE workers)
  OPENAI_API_KEY: GPT advisor (optional)
  GOOGLE_API_KEY: Gemini/Owl (optional)
  IBKR_*: Broker keys (S32, not now)
  TELEGRAM_BOT_TOKEN: Takopi bridge (S31)

ACTION:
  - Verify each key loads (python -c "import os; print(os.getenv('KEY'))")
  - Report missing keys (non-blocking for S30 except ANTHROPIC)
  - Fix now if critical

---

## 4. REPO HYGIENE

DIRECTORY_STRUCTURE:
  phoenix/
  ├── docs/              # Living docs (VISION, SPRINT_*, etc)
  ├── archive/           # OLD docs moved here (timestamped)
  ├── src/phoenix/       # All source code
  ├── tests/             # Mirror src structure
  ├── schemas/           # YAML schemas (beads, HPG, etc)
  ├── config/            # Runtime config (pairs.yaml, etc)
  ├── scripts/           # One-off scripts, utilities
  └── .github/           # CI workflows

BLOAT_PREVENTION:
  - Archive docs older than 2 sprints to archive/
  - No duplicate files (grep for similar names)
  - No orphan code (unused imports, dead functions)
  - Keep README.md current (not stale)

README_REQUIREMENTS:
  - Project purpose (1 para)
  - Current sprint + status
  - Quick start (3 commands max)
  - Link to docs/PRODUCT_VISION.md
  - Link to current sprint doc

---

## 5. PYPROJECT.TOML

LOCATION: ~/echopeso/phoenix/pyproject.toml

REQUIRED_SECTIONS:
  [project]:
    name, version, requires-python >= 3.11

  [tool.ruff]:
    line-length = 100
    select = ["E", "F", "I", "B", "UP"]

  [tool.mypy]:
    strict = true
    python_version = "3.11"

  [tool.pytest.ini_options]:
    testpaths = ["tests"]
    markers = ["invariant: constitutional compliance tests"]

---

## 6. PRE-COMMIT CONFIG

LOCATION: ~/echopeso/phoenix/.pre-commit-config.yaml

HOOKS:
  - ruff (lint + format)
  - mypy
  - check-yaml
  - end-of-file-fixer
  - trailing-whitespace
  - no-commit-to-branch (protect main)

---

## 7. PREFLIGHT CHECKLIST

RUN_BEFORE_S30:

□ .cursorrules exists and populated
□ .env loads ANTHROPIC_API_KEY
□ .env.example exists
□ .gitignore includes .env, __pycache__, .mypy_cache
□ pyproject.toml configured (ruff, mypy, pytest)
□ pre-commit install succeeds
□ ruff check . passes (or shows fixable issues)
□ mypy --strict src/ passes (empty is ok)
□ README.md is current
□ No orphan docs in root (move to docs/ or archive/)
□ Directory structure matches spec
□ Git status clean (no uncommitted changes)

---

## 8. ARCHIVE PROTOCOL

WHEN_TO_ARCHIVE:
  - Doc superseded by newer version
  - Sprint complete (move SPRINT_N.md to archive/)
  - Old reports (>2 sprints old)

NAMING:
  archive/2026-01-27_SPRINT_28_FINAL.md
  archive/2026-01-15_NEX_AUDIT_REPORT.md

NEVER_ARCHIVE:
  - PRODUCT_VISION.md (living doc)
  - Current sprint doc
  - CONSTITUTION_AS_CODE.md
  - Active schemas

---

## 9. OPUS ACTIONS

IMMEDIATE:
  1. cd ~/echopeso/phoenix
  2. Check directory structure, create missing dirs
  3. Check/create .cursorrules
  4. Check/create pyproject.toml
  5. Check/create .pre-commit-config.yaml
  6. Check .env, report missing keys
  7. Run: pre-commit install
  8. Run: ruff check . --fix
  9. Update README.md if stale
  10. Archive any orphan/old docs

REPORT_BACK:
  format: DENSE
  include:
    - created: [files]
    - fixed: [issues]
    - missing_keys: [env vars]
    - blockers: [if any]
    - status: READY | BLOCKED

---

## 10. SUCCESS CRITERIA

READY_TO_BUILD:
  - All preflight checks pass
  - Pre-commit hooks active
  - No ruff/mypy errors
  - README current
  - No repo spaghetti
  - Clean git status

BLOAT_SIGNALS (fix if found):
  - Files >300 lines
  - Duplicate code
  - Uncommitted changes
  - Stale docs in root
  - Missing type hints
  - print() statements
