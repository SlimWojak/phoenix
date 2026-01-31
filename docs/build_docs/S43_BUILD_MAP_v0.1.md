# ============================================================
# S43 BUILD MAP — QUICK WINS
# ============================================================

document: S43_BUILD_MAP
version: 0.1
date: 2026-01-31
status: BUILDABLE_SPEC
author: OPUS
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
  "If it takes >4 hours, it's not S43 scope"

non_goals:
  - New features
  - New modules
  - New invariants
  - Anything requiring design phase

# ============================================================
# TRACK STRUCTURE
# ============================================================

tracks:
  A: PYTEST_PARALLELIZATION   # 7min → <3min test suite
  B: ALERT_BUNDLING           # CV-S42-04 completion
  C: CONFIG_CENTRALIZATION    # Scattered → unified schema
  D: NARRATOR_TEMPLATES       # Missing templates for research UX

estimated_duration: 2-3 days
effort_per_track: 2-4 hours each

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
    - Group stateful tests with @pytest.mark.xdist_group
    - Verify no shared state pollution

  deliverables:
    - requirements.txt updated with pytest-xdist
    - pytest.ini or pyproject.toml with xdist config
    - tests/conftest.py with xdist group markers

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
      action: "Group stateful tests"
      markers:
        - "@pytest.mark.xdist_group('health')" for health_fsm tests
        - "@pytest.mark.xdist_group('ibkr')" for IBKR tests
        - "@pytest.mark.xdist_group('river')" for River tests

    step_5:
      action: "Run and verify"
      test: "time pytest tests/ -n auto"
      expect: "<3 minutes wall time"

  exit_gates:
    GATE_A1:
      criterion: "pytest runs parallel without failures"
      test: "pytest tests/ -n auto --tb=short"

    GATE_A2:
      criterion: "Test suite <3 minutes"
      test: "time pytest tests/ -n auto"

    GATE_A3:
      criterion: "No new test failures from parallelization"
      test: "compare pass count before/after"

  chaos_upside: |
    Run bunny vectors in parallel → discover race conditions
    we never saw sequentially. If it breaks, we learn.

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
    - 30-minute bundling window
    - Dedup by alert type
    - Single "MULTI_DEGRADED" alert for cascades
    - Test under chaos injection

  deliverables:
    - notification/alert_bundler.py (new or extend alert_taxonomy.py)
    - Tests for bundling behavior
    - CV-S42-04 fully validated

  implementation:
    step_1:
      action: "Review alert_taxonomy.py current state"
      file: "notification/alert_taxonomy.py"

    step_2:
      action: "Add bundling logic"
      logic: |
        - Track alerts by type + time window
        - If same type within 30min, increment count
        - Emit single bundled alert at window close or threshold

    step_3:
      action: "Add MULTI_DEGRADED alert type"
      content: |
        class AlertType(Enum):
            MULTI_DEGRADED = "multi_degraded"

    step_4:
      action: "Test under chaos"
      test: "drills/s42_failure_playbook.py::test_cv_s42_04"

  exit_gates:
    GATE_B1:
      criterion: "No alert storms (>10/min) in any failure mode"
      test: "chaos injection + alert count"

    GATE_B2:
      criterion: "CV-S42-04 fully PASS"
      test: "pytest drills/s42_failure_playbook.py -k cv_s42_04"

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
    - Create config/schema.yaml
    - Central validation on startup
    - Safe defaults documented

  deliverables:
    - config/schema.yaml (config schema)
    - config/loader.py (central loader)
    - config/defaults.yaml (safe defaults)
    - Tests for config validation

  implementation:
    step_1:
      action: "Inventory config sources"
      locations:
        - brokers/ibkr/config.py
        - governance/halt.py (thresholds)
        - narrator/renderer.py (template paths)
        - river/ (data paths)

    step_2:
      action: "Create schema"
      file: "config/schema.yaml"
      content: |
        schema_version: "1.0"
        sections:
          ibkr:
            required: [account_id, host, port]
            optional: [paper_mode, timeout_seconds]
          river:
            required: [data_path]
            optional: [refresh_interval_seconds]
          governance:
            required: [halt_timeout_ms]
            optional: [alert_cooldown_seconds]

    step_3:
      action: "Create loader"
      file: "config/loader.py"
      interface: |
        def load_config(path: str) -> Config:
            """Load and validate config against schema."""

    step_4:
      action: "Document defaults"
      file: "config/defaults.yaml"

  exit_gates:
    GATE_C1:
      criterion: "All config in central schema"
      test: "grep for scattered config patterns"

    GATE_C2:
      criterion: "Startup validates config"
      test: "Invalid config → clear error"

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

  deliverables:
    - narrator/templates/research_summary.jinja2
    - narrator/templates/hunt_result.jinja2
    - narrator/templates/weekly_review.jinja2
    - Tests for new templates

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

        ---
        *Facts only. You interpret.*

  exit_gates:
    GATE_D1:
      criterion: "All templates pass guard dog"
      test: "narrator/renderer.py validates all"

    GATE_D2:
      criterion: "INV-NARRATOR-* compliance"
      test: "No forbidden words in templates"

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
    - "Config has central schema"
    - "Research narrator templates exist"

definition_of_done: |
  Developer velocity unlocked:
    - Tests run fast
    - Alerts don't storm
    - Config is documented
    - Research UX has templates

  Foundation tightened for S44+.

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
    criterion: "config/schema.yaml exists and validates"
    test: "python -c 'from config.loader import load_config; load_config()'"

  GATE_S43_4:
    criterion: "3 new narrator templates pass guard"
    test: "narrator validation on templates/"

# ============================================================
# INVARIANT CHECK
# ============================================================

invariants_to_verify:
  - INV-NARRATOR-1: Templates remain facts-only
  - INV-ALERT-TAXONOMY-1: Alert types use defined categories
  - INV-HEALTH-1: Health FSM unaffected by parallel tests

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
    status: BUILDABLE_SPEC
    changes: |
      Initial draft from advisory team convergence.
      4 tracks identified from CARPARK + S42 findings.
      All tracks parallelizable.

# ============================================================
# END BUILD MAP v0.1
# ============================================================
