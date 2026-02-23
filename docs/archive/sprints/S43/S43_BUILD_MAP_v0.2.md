# ============================================================
# S43 BUILD MAP — QUICK WINS
# ============================================================

document: S43_BUILD_MAP
version: 0.2
date: 2026-01-31
status: GREENLIT
author: OPUS
approved_by: CTO
theme: "Developer velocity unlocked, foundation tightened"

# ============================================================
# PREAMBLE
# ============================================================

context: |
  S42 closed trust. S43-S52 is the path to WARBOAR v0.1.
  S43 is the momentum sprint — quick wins that pay immediate dividends.

  Every item here existed in CARPARK or was identified during S42.
  No new architecture. Just tightening, parallelizing, completing.

governing_principle: |
  "Quick wins first → momentum → confidence → velocity"
  "If it takes >4 hours, it's not S43 scope — ABORT and ESCALATE"
  "Boring = correct"

non_goals:
  - New features
  - New modules
  - New dependencies (zero new libs)
  - Anything requiring design phase
  - Anything clever

# ============================================================
# TRACK STRUCTURE
# ============================================================

tracks:
  A: PYTEST_PARALLELIZATION   # 7min → <3min test suite
  B: ALERT_BUNDLING           # CV-S42-04 completion
  C: CONFIG_CENTRALIZATION    # Scattered → unified schema
  D: NARRATOR_TEMPLATES       # Missing templates for research UX

estimated_duration: 2-3 days
effort_per_track: 2-4 hours each (hard cap)

scope_abort_rule: |
  Any track taking >4 hours = SCOPE ABORT
  Stop, escalate, document blocker
  Do not heroically extend

# ============================================================
# TRACK A: PYTEST_PARALLELIZATION
# ============================================================

track_a:
  name: PYTEST_PARALLELIZATION
  priority: P0
  owner: OPUS
  carpark_ref: CARPARK.md:PYTEST_PARALLELIZATION

  why: |
    7+ minute test suite kills iteration velocity.
    12-worker capability exists (NEX pattern).
    Mac Studio has 12+ cores available.

  scope:
    - Install pytest-xdist
    - Configure -n auto (or -n logical)
    - Group ALL stateful tests with @pytest.mark.xdist_group
    - Verify no shared state pollution

  # CTO ADDENDUM v0.2
  addendum:
    - Mark ALL stateful tests (health/ibkr/river) with xdist_group
    - Expect failures = signal, not regression (truth surfaces)
    - If races surface, isolate with group markers, don't disable parallel

  deliverables:
    - requirements.txt updated with pytest-xdist
    - pytest.ini or pyproject.toml with xdist config
    - tests/conftest.py with xdist group markers for ALL stateful tests

  implementation:
    step_1:
      action: "pip install pytest-xdist"
      verify: "pytest --version shows xdist"

    step_2:
      action: "Add to requirements.txt"
      content: "pytest-xdist>=3.5.0"

    step_3:
      action: "Configure parallel execution"
      file: "pytest.ini or pyproject.toml"
      config: |
        [pytest]
        addopts = -n auto --dist loadgroup

    step_4:
      action: "Group ALL stateful tests"
      markers:
        health:
          pattern: "**/test_*health*.py, **/test_*fsm*.py"
          marker: "@pytest.mark.xdist_group('health')"
        ibkr:
          pattern: "**/test_*ibkr*.py, **/test_*broker*.py, **/test_*connector*.py"
          marker: "@pytest.mark.xdist_group('ibkr')"
        river:
          pattern: "**/test_*river*.py, **/test_*data*.py"
          marker: "@pytest.mark.xdist_group('river')"
        narrator:
          pattern: "**/test_narrator*.py"
          marker: "@pytest.mark.xdist_group('narrator')"

    step_5:
      action: "Run and verify"
      test: "time pytest tests/ -n auto"
      expect: "<3 minutes wall time"

    step_6:
      action: "Handle race failures"
      protocol: |
        If parallel run surfaces failures:
        1. Record failure (it's signal, not regression)
        2. Identify shared state
        3. Add xdist_group marker to isolate
        4. Do NOT disable parallel
        5. Document in TECH_DEBT.md if unresolved

  exit_gates:
    GATE_A1:
      criterion: "pytest runs parallel without failures"
      test: "pytest tests/ -n auto --tb=short"

    GATE_A2:
      criterion: "Test suite <3 minutes"
      test: "time pytest tests/ -n auto"

    GATE_A3:
      criterion: "No new test failures from parallelization (or races documented)"
      test: "compare pass count before/after, document any race discoveries"

  chaos_upside: |
    Run bunny vectors in parallel → discover race conditions
    we never saw sequentially. If it breaks, we learn. That's the win.

# ============================================================
# TRACK B: ALERT_BUNDLING
# ============================================================

track_b:
  name: ALERT_BUNDLING
  priority: P1
  owner: OPUS
  ref: CV-S42-04 (multi_degrade_cascade)

  why: |
    CV-S42-04 flagged as MEDIUM complexity.
    Alert storms during multi-failure scenarios.
    Need deduped bundle, not 17 Telegram pings.

  scope:
    - Configurable bundling window (default 30min)
    - Dedup by alert type
    - Single "MULTI_DEGRADED" alert for cascades
    - CRITICAL/HALT bypass bundling (unbundlable)
    - Test under chaos injection

  # CTO ADDENDUM v0.2
  addendum:
    - CRITICAL and HALT alerts BYPASS bundling (unbundlable types)
    - 30min window → make configurable via config schema
    - Test: >5 alerts in window → single MULTI_DEGRADED

  deliverables:
    - notification/alert_bundler.py (new or extend alert_taxonomy.py)
    - Tests for bundling behavior
    - CV-S42-04 fully validated

  implementation:
    step_1:
      action: "Review alert_taxonomy.py current state"
      file: "notification/alert_taxonomy.py"

    step_2:
      action: "Define unbundlable types"
      content: |
        UNBUNDLABLE_TYPES = {
            AlertSeverity.CRITICAL,
            AlertType.HALT,
            AlertType.EMERGENCY,
        }
        # These ALWAYS emit immediately, never bundled

    step_3:
      action: "Add bundling logic"
      logic: |
        class AlertBundler:
            def __init__(self, window_seconds: int = 1800):  # 30min default, configurable
                self.window = window_seconds
                self.pending: dict[AlertType, list[Alert]] = {}

            def submit(self, alert: Alert) -> Optional[Alert]:
                if alert.severity in UNBUNDLABLE_TYPES or alert.type in UNBUNDLABLE_TYPES:
                    return alert  # Emit immediately

                # Bundle logic...
                if len(self.pending.get(alert.type, [])) >= 5:
                    return self._emit_multi_degraded()

    step_4:
      action: "Add MULTI_DEGRADED alert type"
      content: |
        class AlertType(Enum):
            MULTI_DEGRADED = "multi_degraded"

    step_5:
      action: "Wire bundler window to config schema"
      config_key: "notification.bundle_window_seconds"
      default: 1800

    step_6:
      action: "Test under chaos"
      tests:
        - ">5 same-type alerts → single MULTI_DEGRADED"
        - "CRITICAL alert → immediate emit"
        - "HALT alert → immediate emit"
        - "drills/s42_failure_playbook.py::test_cv_s42_04"

  exit_gates:
    GATE_B1:
      criterion: "No alert storms (>10/min) in any failure mode"
      test: "chaos injection + alert count"

    GATE_B2:
      criterion: "CV-S42-04 fully PASS"
      test: "pytest drills/s42_failure_playbook.py -k cv_s42_04"

    GATE_B3:
      criterion: "CRITICAL/HALT bypass bundling"
      test: "unit test for unbundlable types"

# ============================================================
# TRACK C: CONFIG_CENTRALIZATION
# ============================================================

track_c:
  name: CONFIG_CENTRALIZATION
  priority: P2
  owner: OPUS

  why: |
    Config scattered across modules.
    "Works on my box" drift risk.
    S49 DMG packaging needs central config.

  scope:
    - Inventory all config sources
    - Create config/schema.py (Pydantic model)
    - Central validation on startup
    - Safe defaults documented
    - ZERO new dependencies

  # CTO ADDENDUM v0.2
  addendum:
    - Consider Pydantic model for schema (config/schema.py) — already in deps
    - Zero new deps — if it needs new lib, ABORT track
    - Virgin VM concept: config must work on clean machine

  deliverables:
    - config/schema.py (Pydantic config model)
    - config/loader.py (central loader)
    - config/defaults.yaml (safe defaults)
    - Tests for config validation

  implementation:
    step_1:
      action: "Verify Pydantic available"
      test: "python -c 'from pydantic import BaseModel'"
      abort_if: "ImportError → use dataclass fallback, no new dep"

    step_2:
      action: "Inventory config sources"
      locations:
        - brokers/ibkr/config.py
        - governance/halt.py (thresholds)
        - narrator/renderer.py (template paths)
        - river/ (data paths)
        - notification/ (bundle_window_seconds)

    step_3:
      action: "Create Pydantic schema"
      file: "config/schema.py"
      content: |
        from pydantic import BaseModel, Field
        from typing import Optional

        class IBKRConfig(BaseModel):
            account_id: str
            host: str = "127.0.0.1"
            port: int = 7497
            paper_mode: bool = True
            timeout_seconds: int = 30

        class RiverConfig(BaseModel):
            data_path: str
            refresh_interval_seconds: int = 60

        class GovernanceConfig(BaseModel):
            halt_timeout_ms: int = 50
            alert_cooldown_seconds: int = 60

        class NotificationConfig(BaseModel):
            bundle_window_seconds: int = 1800  # 30min

        class PhoenixConfig(BaseModel):
            ibkr: IBKRConfig
            river: RiverConfig
            governance: GovernanceConfig
            notification: NotificationConfig = Field(default_factory=NotificationConfig)

    step_4:
      action: "Create loader"
      file: "config/loader.py"
      interface: |
        def load_config(path: str = "config/phoenix.yaml") -> PhoenixConfig:
            """Load and validate config. Raises ValidationError on invalid."""

    step_5:
      action: "Document defaults"
      file: "config/defaults.yaml"

    step_6:
      action: "Virgin VM test"
      test: |
        # Conceptually: fresh clone, no .env, no secrets
        # Config loads with defaults, clear error if required field missing

  exit_gates:
    GATE_C1:
      criterion: "All config in central schema"
      test: "grep for scattered config patterns → 0 outside config/"

    GATE_C2:
      criterion: "Startup validates config"
      test: "Invalid config → clear ValidationError"

    GATE_C3:
      criterion: "Zero new dependencies"
      test: "diff requirements.txt shows only pytest-xdist added"

# ============================================================
# TRACK D: NARRATOR_TEMPLATES
# ============================================================

track_d:
  name: NARRATOR_TEMPLATES
  priority: P3
  owner: OPUS
  ref: S45 Research UX prep

  why: |
    Research UX (S45) needs templates for:
    - Hunt results
    - CFP summaries
    - Weekly reviews
    Current templates: alert, briefing, health, trade

  scope:
    - Add research_summary.jinja2
    - Add hunt_result.jinja2
    - Add weekly_review.jinja2
    - Ensure INV-NARRATOR-* compliance
    - Add INV-NARRATOR-FACTS-ONLY linter check

  # CTO ADDENDUM v0.2
  addendum:
    - Add INV-NARRATOR-FACTS-ONLY linter check (pre-commit or test)
    - Regex for forbidden interpretation words
    - Optional: {{ receipts_link }} in templates for forensic access

  forbidden_words:
    # INV-NARRATOR-FACTS-ONLY enforcement
    patterns:
      - "edge concentrates"
      - "best"
      - "strongest"
      - "weakest"
      - "recommend"
      - "should"
      - "suggests"
      - "indicates"
      - "likely"
      - "probably"
    enforcement: |
      # In tests/test_narrator_templates.py or pre-commit hook
      FORBIDDEN_PATTERNS = [r'\bedge concentrates\b', r'\bbest\b', r'\bstrongest\b', ...]
      for template in glob('narrator/templates/*.jinja2'):
          content = open(template).read()
          for pattern in FORBIDDEN_PATTERNS:
              assert not re.search(pattern, content, re.IGNORECASE), f"Forbidden: {pattern}"

  deliverables:
    - narrator/templates/research_summary.jinja2
    - narrator/templates/hunt_result.jinja2
    - narrator/templates/weekly_review.jinja2
    - tests/test_narrator_templates.py (forbidden words linter)

  implementation:
    step_1:
      action: "Review existing templates"
      files:
        - narrator/templates/alert.jinja2
        - narrator/templates/briefing.jinja2
        - narrator/templates/health.jinja2
        - narrator/templates/trade.jinja2

    step_2:
      action: "Create research_summary.jinja2"
      content: |
        {# MANDATORY_FACTS_BANNER #}
        {% include 'facts_banner.jinja2' %}

        ## Research Summary

        Query: {{ query }}
        Dataset: {{ dataset_hash }}
        Rows: {{ row_count }}

        {% for row in results %}
        - {{ row }}
        {% endfor %}

        {% if receipts_link %}
        📎 [Receipts]({{ receipts_link }})
        {% endif %}

        ---
        *Facts only. You interpret.*

    step_3:
      action: "Create hunt_result.jinja2"
      content: |
        {# MANDATORY_FACTS_BANNER #}
        {% include 'facts_banner.jinja2' %}

        ## Hunt Result: {{ hypothesis_id }}

        Variants computed: {{ variant_count }}

        {% for variant in variants %}
        | {{ variant.params }} | {{ variant.result }} |
        {% endfor %}

        {% if receipts_link %}
        📎 [Receipts]({{ receipts_link }})
        {% endif %}

        ---
        *All variants shown. No selection. You interpret.*

    step_4:
      action: "Create weekly_review.jinja2"
      content: |
        {# MANDATORY_FACTS_BANNER #}
        {% include 'facts_banner.jinja2' %}

        ## Weekly Review: {{ week_start }} → {{ week_end }}

        Trades: {{ trade_count }}
        Gates passed: {{ gates_summary }}

        {% if receipts_link %}
        📎 [Receipts]({{ receipts_link }})
        {% endif %}

        ---
        *Facts only. You interpret.*

    step_5:
      action: "Create forbidden words linter"
      file: "tests/test_narrator_templates.py"
      content: |
        import re
        from pathlib import Path
        import pytest

        FORBIDDEN_PATTERNS = [
            r'\bedge concentrates\b',
            r'\bbest\b',
            r'\bstrongest\b',
            r'\bweakest\b',
            r'\brecommend\b',
            r'\bshould\b',
            r'\bsuggests?\b',
            r'\bindicates?\b',
            r'\blikely\b',
            r'\bprobably\b',
        ]

        @pytest.mark.parametrize('template', Path('narrator/templates').glob('*.jinja2'))
        def test_no_forbidden_words(template):
            content = template.read_text()
            for pattern in FORBIDDEN_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                assert not match, f"INV-NARRATOR-FACTS-ONLY violation in {template}: '{match.group()}'"

  exit_gates:
    GATE_D1:
      criterion: "All templates pass guard dog"
      test: "narrator/renderer.py validates all"

    GATE_D2:
      criterion: "INV-NARRATOR-FACTS-ONLY compliance"
      test: "pytest tests/test_narrator_templates.py"

    GATE_D3:
      criterion: "Forbidden words linter catches violations"
      test: "Inject forbidden word → test fails"

# ============================================================
# DEPENDENCIES
# ============================================================

dependency_graph:
  A (PYTEST): → independent, start immediately
  B (ALERT):  → independent, start immediately
  C (CONFIG): → independent, start immediately
  D (NARRATOR): → independent, start immediately

parallel_execution: |
  All 4 tracks can run in parallel.
  No dependencies between tracks.
  Start all immediately.

# ============================================================
# SUCCESS CRITERIA
# ============================================================

sprint_success:
  S43_COMPLETE_WHEN:
    - "pytest runs in <3 minutes (parallelized)"
    - "CV-S42-04 fully passes (alert bundling)"
    - "Config has central schema (Pydantic)"
    - "Research narrator templates exist"
    - "All xfails reviewed before close"

definition_of_done: |
  Developer velocity unlocked:
    - Tests run fast
    - Alerts don't storm
    - Config is documented
    - Research UX has templates

  Foundation tightened for S44+.
  Nothing clever shipped.

# ============================================================
# EXIT GATES (SPRINT-LEVEL)
# ============================================================

exit_gates:
  GATE_S43_1:
    criterion: "pytest -n auto completes <3min"
    test: "time pytest tests/ -n auto"

  GATE_S43_2:
    criterion: "CV-S42-04 PASS"
    test: "chaos injection, single bundled alert"

  GATE_S43_3:
    criterion: "config/schema.py exists and validates"
    test: "python -c 'from config.loader import load_config; load_config()'"

  GATE_S43_4:
    criterion: "3 new narrator templates pass guard + forbidden words linter"
    test: "pytest tests/test_narrator_templates.py"

  GATE_S43_5:
    criterion: "All xfails reviewed before close"
    test: "grep xfail tests/ → each has documented reason"
    rationale: "No hidden rot ships to S44"

# ============================================================
# INVARIANT CHECK
# ============================================================

invariants_to_verify:
  - INV-NARRATOR-1: Templates remain facts-only
  - INV-NARRATOR-FACTS-ONLY: Forbidden words linter enforces
  - INV-ALERT-TAXONOMY-1: Alert types use defined categories
  - INV-HEALTH-1: Health FSM unaffected by parallel tests

# ============================================================
# TRAPS TO GUARD
# ============================================================

traps:
  config_creep:
    description: "Adding 'just one more' config option"
    guard: "If config grows beyond inventory, STOP"

  new_deps:
    description: "Importing shiny new library"
    guard: "Zero new deps. Pydantic already in deps. If anything else needed, ABORT."

  heroic_extension:
    description: "Track taking >4 hours, push through anyway"
    guard: "HARD CAP. >4 hours = scope abort, escalate, document blocker."

  race_panic:
    description: "Parallel tests surface races, disable parallel"
    guard: "Races = signal. Isolate with markers, don't disable parallel."

# ============================================================
# POST-S43 UNLOCK
# ============================================================

unlocks:
  S44_LIVE_VALIDATION:
    - Fast test feedback (<3min)
    - Stable alert behavior
    - Config reproducibility

  S45_RESEARCH_UX:
    - Templates ready for research output
    - CFP summaries renderable

# ============================================================
# VERSION HISTORY
# ============================================================

versions:
  v0.1:
    date: 2026-01-31
    author: OPUS
    status: DRAFT
    changes: |
      Initial draft from advisory team convergence.
      4 tracks identified from CARPARK + S42 findings.
      All tracks parallelizable.

  v0.2:
    date: 2026-01-31
    author: OPUS
    approved_by: CTO
    status: GREENLIT
    changes: |
      CTO addendum woven in:
      - Track A: ALL stateful tests marked, races = signal not regression
      - Track B: CRITICAL/HALT bypass bundling, configurable window
      - Track C: Pydantic schema, zero new deps, virgin VM concept
      - Track D: INV-NARRATOR-FACTS-ONLY linter, forbidden words, receipts_link
      - Sprint: GATE_S43_5 (xfail review), >4h scope abort rule
      - Added TRAPS section for guardrails

# ============================================================
# END BUILD MAP v0.2
# ============================================================
