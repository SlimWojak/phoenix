<file_map>
File: /Users/echopeso/phoenix/daemons/routing.py
Imports:
  - import hashlib
  - import logging
  - from collections.abc import Callable
  - from dataclasses import dataclass
  - from datetime import UTC, datetime
  - from enum import Enum
  - from pathlib import Path
  - from typing import Any, Protocol
  - import yaml
  - import time
  - from governance.halt import HaltManager
---
Classes:
  - IntentType
    Methods:
      - L54: def from_string(cls, value: str) -> IntentType:
  - Intent
    Methods:
      - L79: def __post_init__(self) -> None:
      - L84: def _compute_hash(self) -> str:
      - L88: def verify_immutable(self, current_yaml: str) -> bool:
    Properties:
      - intent_type
      - payload
      - timestamp
      - session_id
      - raw_yaml
      - source_path
      - content_hash
  - RouteResult
    Properties:
      - success
      - intent
      - worker_name
      - response_path
      - error
      - processing_time_ms
  - WorkerHandler
    Methods:
      - L118: def handle(self, intent: Intent) -> RouteResult:
  - IntentRouter
    Methods:
      - L136: def __init__(self) -> None:
      - L142: def register(self, intent_type: IntentType, handler: WorkerHandler) -> None:
      - L157: def register_function(
        self,
        intent_type: IntentType,
        func: Callable[[Intent], RouteResult],
    ) -> None:
      - L179: def is_priority(self, intent_type: IntentType) -> bool:
      - L187: def route(self, intent: Intent) -> RouteResult:
      - L245: def get_registered_types(self) -> list[IntentType]:
  - FunctionHandler
    Methods:
      - L171: def __init__(self, fn: Callable[[Intent], RouteResult]) -> None:
      - L174: def handle(self, intent: Intent) -> RouteResult:
  - StubHandler
    Methods:
      - L323: def __init__(self, name: str, resp_dir: Path) -> None:
      - L327: def handle(self, intent: Intent) -> RouteResult:
  - HaltHandler
    Methods:
      - L368: def handle(self, intent: Intent) -> RouteResult:

Functions:
  - L258: def parse_intent(path: Path) -> Intent | None:
  - L310: def create_stub_handler(
    intent_type: IntentType,
    response_dir: Path | None = None,
) -> WorkerHandler:
  - L360: def create_halt_handler() -> WorkerHandler:

Enums:
  - IntentType

Global vars:
  - logger
---


File: /Users/echopeso/phoenix/daemons/watcher.py
Imports:
  - import hashlib
  - import logging
  - import shutil
  - import threading
  - import time
  - from collections.abc import Callable
  - from dataclasses import dataclass, field
  - from datetime import UTC, datetime
  - from pathlib import Path
  - from typing import Any
  - from .routing import Intent, IntentRouter, IntentType, RouteResult, parse_intent
  - from datetime import timedelta
---
Classes:
  - WatcherConfig
    Properties:
      - incoming_dir
      - processed_dir
      - unprocessed_dir
      - poll_interval_ms
      - use_watchdog
      - max_retries
      - retry_delay_ms
      - intent_pattern
  - WatcherStats
    Methods:
      - L89: def to_dict(self) -> dict[str, Any]:
    Properties:
      - intents_processed
      - intents_failed
      - intents_quarantined
      - halt_intents
      - duplicates_skipped
      - start_time
      - last_activity
  - IntentWatcher
    Methods:
      - L120: def __init__(
        self,
        router: IntentRouter,
        config: WatcherConfig | None = None,
        on_intent_processed: Callable[[Intent, RouteResult], None] | None = None,
    ) -> None:
      - L153: def running(self) -> bool:
      - L158: def stats(self) -> WatcherStats:
      - L166: def start(self) -> None:
      - L187: def stop(self) -> None:
      - L197: def _recover_orphans(self) -> None:
      - L219: def _poll_loop(self) -> None:
      - L229: def _poll_once(self) -> None:
      - L243: def _process_intent_file(self, path: Path) -> None:
      - L339: def _quarantine(self, path: Path, reason: str) -> None:
      - L357: def _move_processed(self, path: Path) -> None:
      - L377: def cleanup_old_hashes(self, max_age_hours: int = 24) -> int:
      - L403: def process_single(self, path: Path) -> RouteResult | None:

Global vars:
  - logger
---


File: /Users/echopeso/phoenix/monitoring/alerts.py
Imports:
  - import hashlib
  - import json
  - import logging
  - import time
  - from collections import defaultdict, deque
  - from collections.abc import Callable
  - from dataclasses import dataclass, field
  - from datetime import UTC, datetime
  - from enum import Enum
---
Classes:
  - Alert
    Methods:
      - L74: def to_dict(self) -> dict:
    Properties:
      - alert_class
      - level
      - message
      - timestamp
      - metadata
  - AlertThreshold
    Properties:
      - warn_threshold
      - critical_threshold
      - comparison
  - AlertManager
    Methods:
      - L145: def __init__(
        self,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
        thresholds: dict[AlertClass, AlertThreshold] | None = None,
        halt_callback: Callable[[str], None] | None = None,
        bead_callback: Callable[[dict], None] | None = None,
    ):
      - L175: def register_callback(self, callback: Callable[[Alert], None]) -> None:
      - L179: def check_threshold(
        self,
        alert_class: AlertClass,
        value: float,
        source_id: str = "default",
        metadata: dict | None = None,
    ) -> Alert | None:
      - L215: def emit(
        self,
        alert_class: AlertClass,
        level: AlertLevel,
        message: str,
        source_id: str = "default",
        metadata: dict | None = None,
    ) -> Alert | None:
      - L277: def _emit_violation_bead(self, alert: Alert) -> dict:
      - L309: def _compute_alert_hash(self, alert: Alert) -> str:
      - L320: def _check_auto_halt_escalation(self) -> None:
      - L343: def _trigger_auto_halt(self) -> None:
      - L380: def reset_auto_halt(self) -> None:
      - L385: def emit_halt_violation(self, latency_ms: float, source_id: str = "halt") -> Alert | None:
      - L391: def emit_quality_degraded(self, quality: float, source_id: str = "river") -> Alert | None:
      - L397: def emit_worker_death(self, worker_id: str, reason: str = "unknown") -> Alert | None:
      - L407: def emit_heartbeat_stale(self, worker_id: str, seconds_stale: float) -> Alert | None:
      - L416: def emit_bounds_violation(
        self, violation_type: str, value: float, threshold: float
    ) -> Alert | None:
      - L428: def get_recent_alerts(self, limit: int = 50) -> list[Alert]:
      - L432: def get_stats(self) -> dict:
      - L457: def get_beads(self) -> list[dict]:
      - L461: def is_auto_halted(self) -> bool:
      - L465: def clear_history(self) -> None:
    Properties:
      - DEFAULT_DEBOUNCE_SECONDS
      - AUTO_HALT_WINDOW_SECONDS
      - AUTO_HALT_THRESHOLD

Functions:
  - L480: def get_alert_manager() -> AlertManager:

Enums:
  - AlertLevel
  - AlertClass

Global vars:
  - logger
  - DEFAULT_THRESHOLDS
  - _alert_manager
---


File: /Users/echopeso/phoenix/monitoring/kill_manager.py
Imports:
  - import hashlib
  - import json
  - import uuid
  - from dataclasses import dataclass, field
  - from datetime import UTC, datetime
  - from typing import Any
---
Classes:
  - KillFlag
    Methods:
      - L39: def to_dict(self) -> dict[str, Any]:
    Properties:
      - strategy_id
      - active
      - reason
      - triggered_by
      - decay_metrics
      - timestamp
      - lifted_by
      - lifted_reason
      - bead_id
  - KillManager
    Methods:
      - L65: def __init__(self, bead_store: Any | None = None) -> None:
      - L75: def set_kill_flag(
        self,
        strategy_id: str,
        reason: str,
        triggered_by: str,
        decay_metrics: dict[str, Any] | None = None,
    ) -> KillFlag:
      - L140: def lift_kill_flag(
        self,
        strategy_id: str,
        lifted_by: str,
        lifted_reason: str,
    ) -> KillFlag | None:
      - L211: def get_kill_flag(self, strategy_id: str) -> KillFlag | None:
      - L261: def get_active_kills(self) -> list[KillFlag]:
      - L313: def is_killed(self, strategy_id: str) -> bool:
      - L326: def compute_hash(self) -> str:
---


File: /Users/echopeso/phoenix/notification/alert_taxonomy.py
Imports:
  - import time
  - from collections import defaultdict
  - from collections.abc import Callable
  - from dataclasses import dataclass, field
  - from datetime import UTC, datetime
  - from enum import Enum
---
Classes:
  - Alert
    Methods:
      - L100: def __post_init__(self):
    Properties:
      - severity
      - category
      - title
      - message
      - component
      - timestamp
      - metadata
      - dedup_key
  - DeduplicationWindow
    Methods:
      - L138: def should_send(self, window_seconds: float, max_count: int) -> bool:
      - L152: def record(self) -> None:
    Properties:
      - alerts
      - last_sent
  - AlertDeduplicator
    Methods:
      - L179: def __init__(self):
      - L184: def should_send(self, alert: Alert) -> bool:
      - L196: def record_sent(self, alert: Alert) -> None:
      - L202: def record_deduplicated(self, alert: Alert) -> None:
      - L207: def stats(self) -> dict:
    Properties:
      - WINDOW_SECONDS
      - MAX_IN_WINDOW
  - TelegramAlertFormatter
    Methods:
      - L266: def format_oneliner(self, alert: Alert) -> str:
      - L298: def format(self, alert: Alert, oneliner: bool = False) -> str:
      - L342: def format_batch(self, alerts: list[Alert]) -> str:
    Properties:
      - SEVERITY_EMOJI
      - SEVERITY_EMOJI_FULL
      - SEVERITY_HEADER
      - CATEGORY_EMOJI
  - AlertRouter
    Methods:
      - L399: def __init__(self):
      - L406: def add_handler(self, handler: Callable[[str, AlertSeverity], None]) -> None:
      - L410: def route(self, alert: Alert) -> bool:
      - L439: def stats(self) -> dict:
  - AlertBundler
    Methods:
      - L554: def __init__(self, window_seconds: int = 1800):
      - L573: def _should_bypass(self, alert: Alert) -> bool:
      - L577: def _get_bundle_key(self, alert: Alert) -> str:
      - L581: def _check_window_expired(self, bundle_key: str) -> bool:
      - L587: def submit(self, alert: Alert) -> Alert | None:
      - L630: def _create_multi_degraded(self, bundle_key: str) -> Alert:
      - L650: def flush(self) -> list[Alert]:
      - L666: def stats(self) -> dict:

Functions:
  - L453: def create_halt_alert(component: str, reason: str) -> Alert:
  - L464: def create_circuit_open_alert(circuit_name: str, failure_count: int) -> Alert:
  - L476: def create_health_transition_alert(
    component: str,
    old_state: str,
    new_state: str,
) -> Alert:
  - L493: def create_ibkr_connection_alert(status: str, reason: str = "") -> Alert:
  - L505: def create_supervisor_alert(status: str, reason: str = "") -> Alert:
  - L517: def create_constitutional_violation_alert(
    violation_type: str,
    context: str,
    details: str,
) -> Alert:

Enums:
  - AlertSeverity
  - AlertCategory

Global vars:
  - HEALTH_STATE_SEVERITY
  - CIRCUIT_STATE_SEVERITY
  - UNBUNDLABLE_SEVERITIES
  - UNBUNDLABLE_CATEGORIES
---


File: /Users/echopeso/phoenix/orientation/generator.py
Imports:
  - import hashlib
  - import json
  - import os
  - import uuid
  - from dataclasses import dataclass, field
  - from datetime import UTC, datetime
  - from enum import Enum
  - from pathlib import Path
  - from typing import Any, Protocol
  - import yaml
---
Classes:
  - HaltManagerProvider
    Methods:
      - L72: def get_active_kill_flags_count(self) -> int:
  - PositionTrackerProvider
    Methods:
      - L80: def get_open_positions_count(self) -> int:
  - BeadStoreProvider
    Methods:
      - L88: def get_unresolved_drift_count(self) -> int:
      - L92: def get_last_human_action_bead_id(self) -> str | None:
  - HeartbeatProvider
    Methods:
      - L100: def get_status(self) -> str:
  - AlertStoreProvider
    Methods:
      - L108: def get_last_alert_id(self) -> str | None:
  - OrientationBead
    Methods:
      - L151: def __post_init__(self) -> None:
      - L156: def compute_hash(self) -> str:
      - L179: def verify_hash(self) -> bool:
      - L183: def to_dict(self) -> dict[str, Any]:
      - L200: def to_yaml_compact(self) -> str:
      - L211: def from_dict(cls, data: dict[str, Any]) -> OrientationBead:
    Properties:
      - bead_id
      - generated_at
      - execution_phase
      - mode
      - active_invariants_count
      - kill_flags_active
      - unresolved_drift_count
      - positions_open
      - heartbeat_status
      - last_human_action_bead_id
      - last_alert_id
      - bead_hash
  - OrientationGenerator
    Methods:
      - L247: def __init__(
        self,
        halt_provider: HaltManagerProvider | None = None,
        position_provider: PositionTrackerProvider | None = None,
        bead_provider: BeadStoreProvider | None = None,
        heartbeat_provider: HeartbeatProvider | None = None,
        alert_provider: AlertStoreProvider | None = None,
        state_dir: Path | None = None,
    ) -> None:
      - L277: def generate(self) -> OrientationBead:
      - L299: def generate_and_write(self) -> tuple[OrientationBead, Path]:
      - L310: def write_to_file(self, bead: OrientationBead) -> Path:
      - L328: def _get_execution_phase(self) -> ExecutionPhase:
      - L333: def _get_mode(self) -> ModeEnum:
      - L341: def _get_invariants_count(self) -> int:
      - L347: def _get_kill_flags_count(self) -> int:
      - L353: def _get_unresolved_drift_count(self) -> int:
      - L359: def _get_positions_count(self) -> int:
      - L365: def _get_heartbeat_status(self) -> HeartbeatStatusEnum:
      - L375: def _get_last_human_bead_id(self) -> str | None:
      - L381: def _get_last_alert_id(self) -> str | None:
    Properties:
      - DEFAULT_INVARIANT_COUNT

Enums:
  - ExecutionPhase
  - ModeEnum
  - HeartbeatStatusEnum
---


File: /Users/echopeso/phoenix/narrator/data_sources.py
Imports:
  - import time
  - from dataclasses import dataclass, field
  - from datetime import UTC, datetime
  - from pathlib import Path
  - from typing import Any
  - import yaml
---
Classes:
  - OrientationData
    Properties:
      - execution_phase
      - kill_flags
      - health_status
      - mode
      - last_updated
      - source_file
      - source_timestamp
  - AthenaData
    Properties:
      - recent_beads
      - claim_count
      - fact_count
      - conflict_count
      - last_bead_type
      - last_bead_id
      - source_file
      - source_timestamp
  - RiverData
    Methods:
      - L81: def is_stale(self) -> bool:
    Properties:
      - health_status
      - last_tick_time
      - staleness_seconds
      - ticks_processed
      - errors_count
      - source_file
      - source_timestamp
  - PytestData
    Methods:
      - L106: def all_passed(self) -> bool:
    Properties:
      - collected
      - passed
      - failed
      - errors
      - skipped
      - duration_seconds
      - last_run
      - source_file
      - source_timestamp
  - TradeData
    Properties:
      - open_positions
      - positions
      - last_trade_id
      - last_trade_time
      - daily_pnl
      - daily_pnl_pct
      - source_file
      - source_timestamp
  - CSOData
    Properties:
      - active_pairs
      - gates_per_pair
      - active_setups
      - last_scan_time
      - source_file
      - source_timestamp
  - HuntData
    Properties:
      - pending_hypotheses
      - hypotheses
      - last_hunt_id
      - last_hunt_result
      - last_hunt_time
      - source_file
      - source_timestamp
  - SupervisorData
    Properties:
      - state
      - ibkr_connected
      - heartbeat_ok
      - degradation_level
      - circuit_breakers_closed
      - circuit_breakers_total
      - source_file
      - source_timestamp
  - AlertData
    Properties:
      - severity
      - component
      - event
      - message
      - action_taken
      - timestamp
      - source_file
      - source_timestamp
  - DataSources
    Methods:
      - L220: def __init__(self, base_path: Path | None = None):
      - L226: def get_orientation(self) -> OrientationData:
      - L230: def get_athena(self) -> AthenaData:
      - L234: def get_river(self) -> RiverData:
      - L238: def get_tests(self) -> TestData:
      - L242: def get_trades(self) -> TradeData:
      - L246: def get_cso(self) -> CSOData:
      - L250: def get_hunt(self) -> HuntData:
      - L254: def get_supervisor(self) -> SupervisorData:
      - L258: def get_all(self) -> dict[str, Any]:
      - L279: def _cached_fetch(self, key: str, fetch_fn) -> Any:
      - L292: def clear_cache(self) -> None:
      - L301: def _fetch_orientation(self) -> OrientationData:
      - L321: def _fetch_athena(self) -> AthenaData:
      - L326: def _fetch_river(self) -> RiverData:
      - L335: def _fetch_tests(self) -> TestData:
      - L344: def _fetch_trades(self) -> TradeData:
      - L348: def _fetch_cso(self) -> CSOData:
      - L352: def _fetch_hunt(self) -> HuntData:
      - L356: def _fetch_supervisor(self) -> SupervisorData:

Global vars:
  - TestData
---


File: /Users/echopeso/phoenix/tools/hooks/scalar_ban_hook.py
Imports:
  - import re
  - from pathlib import Path
  - from .pre_commit_linter import (
    PreCommitLinter,
    LintRule,
    Violation,
    ViolationSeverity,
)
  - import sys
---
Classes:
  - ScalarBanHook
    Methods:
      - L200: def __init__(self, additional_rules: list[LintRule] | None = None):
      - L206: def check_file(self, filepath: Path) -> list[Violation]:
      - L210: def check_staged(self) -> list[Violation]:
      - L214: def check_directory(self, directory: Path) -> list[Violation]:
      - L218: def format_report(self, violations: list[Violation]) -> str:
      - L222: def run(self) -> int:

Functions:
  - L111: def is_in_comment_or_docstring(line: str, matched: str) -> bool:
  - L118: def is_test_mock_data(line: str, matched: str) -> bool:
  - L130: def get_constitutional_rules() -> list[LintRule]:
  - L250: def main() -> int:

Global vars:
  - SCALAR_PATTERNS
  - RANKING_PATTERNS
  - AVG_PATTERNS
  - CAUSAL_PATTERNS
  - GRADE_PATTERNS
  - VERDICT_PATTERNS
---


File: /Users/echopeso/phoenix/widget/surface_renderer.py
Imports:
  - import time
  - from dataclasses import dataclass
  - from datetime import UTC, datetime
  - from pathlib import Path
  - from typing import Any
  - import yaml
---
Classes:
  - RenderState
    Methods:
      - L57: def is_stale(self) -> bool:
      - L64: def to_menu_title(self) -> str:
      - L91: def to_detail_text(self) -> str:
      - L115: def _health_to_emoji(status: str | None) -> str:
      - L132: def _mode_to_emoji(mode: str | None) -> str:
    Properties:
      - source_available
      - heartbeat_status
      - positions_open
      - mode
      - kill_flags_active
      - generated_at
      - read_at
  - SurfaceRenderer
    Methods:
      - L168: def __init__(
        self,
        orientation_path: Path | None = None,
    ) -> None:
      - L185: def read_state(self) -> RenderState:
      - L237: def get_menu_title(self) -> str:
      - L246: def get_detail_text(self) -> str:
      - L255: def verify_no_derivation(self) -> bool:
      - L283: def verify_blank_on_missing(self) -> bool:
    Properties:
      - DEFAULT_ORIENTATION_PATH
---


File: /Users/echopeso/phoenix/state/manifest_writer.py
Imports:
  - import json
  - import os
  - import sys
  - import tempfile
  - from datetime import UTC
  - from datetime import datetime as dt
  - from pathlib import Path
  - from typing import Any
  - from governance.lease import LeaseManager
  - from governance.lease_types import LeaseState
  - from governance.lease import LeaseInterpreter, LeaseManager, LeaseStateMachine
  - import time
---

Functions:
  - L58: def get_current_killzone(now: dt | None = None) -> dict[str, Any]:
  - L101: def _get_next_killzone(current_kz: str) -> tuple[str, int]:
  - L115: def _get_next_killzone_from_hour(hour: int) -> tuple[str, int]:
  - L125: def _format_duration(minutes: int) -> str:
  - L141: def read_yaml_simple(path: Path) -> dict[str, Any]:
  - L206: def _parse_value(value: str) -> Any:
  - L239: def map_health_to_hud(health_data: dict[str, Any]) -> dict[str, Any]:
  - L272: def get_comp_color(comp_name: str) -> str:
  - L319: def _get_lease_component_color() -> str:
  - L353: def _calculate_age_seconds(timestamp_str: str) -> int:
  - L378: def get_next_seq() -> int:
  - L398: def get_lease_state() -> dict[str, Any]:
  - L486: def build_manifest() -> dict[str, Any]:
  - L555: def write_manifest(manifest: dict[str, Any]) -> Path:
  - L586: def main() -> int:

Global vars:
  - STATE_DIR
  - MANIFEST_FILE
  - HEALTH_FILE
  - ORIENTATION_FILE
  - SEQ_FILE
  - SCHEMA_VERSION
  - KILLZONES
---


File: /Users/echopeso/phoenix/enrichment/layers/l2_reference_levels.py
Imports:
  - import numpy as np
  - import pandas as pd
---

Functions:
  - L51: def enrich(df: pd.DataFrame, symbol: str = None) -> pd.DataFrame:
  - L102: def _calculate_asia_range(df: pd.DataFrame, pip_mult: int) -> pd.DataFrame:
  - L144: def _calculate_pdh_pdl(df: pd.DataFrame, pip_mult: int) -> pd.DataFrame:
  - L184: def _calculate_weekly_levels(df: pd.DataFrame) -> pd.DataFrame:
  - L238: def _calculate_session_levels(df: pd.DataFrame, session: str, pip_mult: int) -> pd.DataFrame:
  - L275: def _add_stubbed_columns(df: pd.DataFrame) -> pd.DataFrame:
  - L321: def _validate_input(df: pd.DataFrame) -> None:
  - L419: def get_columns() -> list[str]:

Global vars:
  - PIP_MULTIPLIERS
  - DEFAULT_PIP_MULTIPLIER
  - MISSING_LEVEL
  - LAYER_2_COLUMNS
---


File: /Users/echopeso/phoenix/athena/store.py
Imports:
  - import json
  - import secrets
  - import sqlite3
  - from datetime import datetime
  - from pathlib import Path
  - from typing import Any
  - from athena.bead_types import (
    AthenaBeadType,
    BeadValidator,
    ClaimBead,
    ClaimContent,
    ClaimProvenance,
    ClaimSource,
    ClaimStatus,
    ConflictBead,
    ConflictDetails,
    ConflictReferences,
    ConflictResolution,
    ConflictStatus,
    ConflictType,
    FactBead,
    FactContent,
    FactProvenance,
    FactSource,
    FactStatus,
    ResolutionAction,
    SourceType,
    StatisticalParameters,
    StatisticalType,
)
  - from athena.claim_linter import ClaimLanguageLinter
  - from athena.rate_limiter import AthenaRateLimiter
---
Classes:
  - AthenaStore
    Methods:
      - L114: def __init__(
        self,
        db_path: Path | None = None,
        rate_limiter: AthenaRateLimiter | None = None,
    ) -> None:
      - L135: def _init_db(self) -> None:
      - L191: def store_claim(self, claim: ClaimBead) -> str:
      - L254: def get_claim(self, bead_id: str) -> ClaimBead | None:
      - L266: def get_claims_by_domain(self, domain: str) -> list[ClaimBead]:
      - L286: def store_fact(self, fact: FactBead) -> str:
      - L335: def get_fact(self, bead_id: str) -> FactBead | None:
      - L347: def get_facts_by_domain(self, domain: str) -> list[FactBead]:
      - L363: def store_conflict(self, conflict: ConflictBead) -> str:
      - L417: def get_conflict(self, bead_id: str) -> ConflictBead | None:
      - L429: def get_open_conflicts(self) -> list[ConflictBead]:
      - L454: def validate_no_claim_execution(
        self,
        predicate_refs: list[str],
        alert_refs: list[str],
        hunt_refs: list[str],
    ) -> None:
      - L486: def validate_no_auto_surface(self, intent_type: str) -> None:
      - L515: def _claim_to_dict(self, claim: ClaimBead) -> dict[str, Any]:
      - L551: def _dict_to_claim(self, data: dict[str, Any]) -> ClaimBead:
      - L588: def _fact_to_dict(self, fact: FactBead) -> dict[str, Any]:
      - L621: def _dict_to_fact(self, data: dict[str, Any]) -> FactBead:
      - L654: def _conflict_to_dict(self, conflict: ConflictBead) -> dict[str, Any]:
      - L686: def _dict_to_conflict(self, data: dict[str, Any]) -> ConflictBead:

Global vars:
  - ATHENA_ROOT
  - DEFAULT_DB_PATH
  - __all__
---


File: /Users/echopeso/phoenix/cfp/river_adapter.py
Imports:
  - import hashlib
  - from dataclasses import dataclass
  - from datetime import UTC, datetime
  - from pathlib import Path
  - from typing import TYPE_CHECKING, Any
  - import pandas as pd
  - from data.river_reader import RiverReader
  - import numpy as np
---
Classes:
  - AggregationResult
    Properties:
      - data
      - sample_size
      - dataset_hash
      - time_range
      - query_string
      - computed_at
  - RiverCFPAdapter
    Methods:
      - L70: def __init__(self, river_path: Path | None = None) -> None:
      - L79: def close(self) -> None:
      - L83: def __enter__(self) -> RiverCFPAdapter:
      - L86: def __exit__(self, *args: object) -> None:
      - L89: def is_available(self) -> bool:
      - L93: def get_total_rows(
        self,
        pair: str,
        timeframe: str = "1H",
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> int:
      - L128: def execute_aggregation(
        self,
        query_dict: dict[str, Any],
        pair: str = "EURUSD",
        timeframe: str = "1H",
    ) -> AggregationResult:
      - L201: def _apply_filters(
        self,
        df: pd.DataFrame,
        filter_spec: dict[str, Any],
    ) -> pd.DataFrame:
      - L211: def _compute_metrics(
        self,
        df: pd.DataFrame,
        metrics: list[str],
        group_by: list[str],
    ) -> dict[str, Any]:
      - L271: def _compute_dataframe_hash(self, df: pd.DataFrame) -> str:
      - L283: def _compute_hash(self, data: bytes) -> str:

Global vars:
  - PHOENIX_ROOT
  - __all__
---


File: /Users/echopeso/phoenix/validation/backtest.py
Imports:
  - import uuid
  - from dataclasses import dataclass, field
  - from datetime import UTC, datetime
  - from typing import Any
  - import secrets
---
Classes:
  - BacktestMetrics
    Properties:
      - sharpe
      - win_rate
      - profit_factor
      - max_drawdown
      - avg_trade
      - trade_count
  - BacktestSample
    Properties:
      - n_trades
      - n_days
  - BacktestProvenance
    Properties:
      - query_string
      - dataset_hash
      - governance_hash
      - strategy_config_hash
  - VisualMetadata
    Properties:
      - color_scale
      - highlight_threshold
      - emphasis_rules
  - BacktestParameters
    Properties:
      - strategy_config_hash
      - time_range_start
      - time_range_end
      - pairs
  - BacktestResult
    Methods:
      - L124: def __post_init__(self) -> None:
    Properties:
      - backtest_id
      - timestamp
      - disclaimer
      - parameters
      - metrics
      - sample
      - provenance
      - visual_metadata
  - BacktestWorker
    Methods:
      - L153: def run(
        self,
        strategy_config: dict[str, Any],
        time_range_start: datetime,
        time_range_end: datetime,
        pairs: list[str] | None = None,
    ) -> BacktestResult:
      - L193: def _compute_metrics(self, config: dict[str, Any]) -> BacktestMetrics:
      - L208: def _compute_sample(
        self,
        start: datetime,
        end: datetime,
    ) -> BacktestSample:
  - BacktestValidator
    Methods:
      - L229: def validate(self, result: BacktestResult) -> tuple[bool, list[str]]:
      - L247: def _to_dict(self, result: BacktestResult) -> dict[str, Any]:

Global vars:
  - MANDATORY_DISCLAIMER
  - FORBIDDEN_FIELDS
  - __all__
---


File: /Users/echopeso/phoenix/slm/train_slm.py
Imports:
  - import json
  - import time
  - from dataclasses import dataclass
  - from pathlib import Path
  - import mlx.core as mx
  - import mlx.nn as nn
  - import mlx.optimizers as optim
  - from mlx_lm import load, generate
  - from mlx_lm.tuner.trainer import TrainingArgs, train
  - from mlx_lm.tuner import linear_to_lora_layers, datasets
  - from mlx_lm.tuner.lora import LoRALinear
  - from mlx_lm.tuner.datasets import CacheDataset
  - from mlx_lm.tuner import linear_to_lora_layers
  - from transformers import AutoConfig
  - import argparse
  - import traceback
---
Classes:
  - SLMConfig
    Properties:
      - model_name
      - output_dir
      - train_data
      - val_data
      - lora_rank
      - lora_alpha
      - lora_dropout
      - lora_targets
      - batch_size
      - grad_accumulation
      - learning_rate
      - num_epochs
      - warmup_steps
      - max_seq_length
      - use_fp16
      - use_neural_engine
  - DatasetConfig
    Methods:
      - L220: def __init__(self, data_dir):

Functions:
  - L92: def check_hardware():
  - L117: def load_model(config: SLMConfig):
  - L129: def prepare_data(config: SLMConfig) -> tuple[Path, Path]:
  - L153: def run_training(config: SLMConfig):
  - L202: def count_params(params):
  - L282: def run_inference_test(config: SLMConfig, model_path: Path):
  - L389: def dry_run(config: SLMConfig):
  - L435: def main():

Global vars:
  - DEFAULT_CONFIG
---


File: /Users/echopeso/phoenix/surfaces/hud/WarBoarHUD/Services/ManifestWatcher.swift
Imports:
  - import Foundation
  - import Combine
---
Classes:
  - ManifestWatcher
    Methods:
      - L69: func startWatching(url: URL)
      - L94: func startWatchingPhoenix()
      - L128: func startWatchingMock()
      - L150: func stopWatching()
      - L169: func forceReload()
      - L176: private func setupDispatchSource(for url: URL) -> Bool
      - L208: private func setupFallbackPolling(for url: URL)
      - L216: private func setupStaleCheckTimer()
      - L223: private func updateStaleStatus()
      - L237: private func handleFileEvent(url: URL)
      - L252: private func loadManifest(from url: URL)
      - L277: private func handleParseError(_ error: Error, url: URL)
    Properties:
      - @Published private(set) var manifest: StateManifest?
      - @Published private(set) var isStale: Bool
      - @Published private(set) var manifestAgeSeconds: Int
      - @Published private(set) var watcherState: WatcherState
      - @Published private(set) var lastError: WatcherError?
      - let staleThreshold: TimeInterval
      - private let throttleInterval: TimeInterval
      - private let fallbackPollInterval: TimeInterval
      - private var fileDescriptor: Int32
      - private var dispatchSource: DispatchSourceFileSystemObject?
      - private var fallbackTimer: Timer?
      - private var staleCheckTimer: Timer?
      - private var lastUpdateTime: Date
      - private var watchedURL: URL?
      - private let fileQueue
  - WatcherError
    Properties:
      - var displayMessage: String

Enums:
  - WatcherState
  - WatcherError
---


File: /Users/echopeso/phoenix/tests/daemons/test_halt_priority.py
Imports:
  - import sys
  - import tempfile
  - import time
  - from pathlib import Path
  - import pytest
  - import yaml
  - from daemons.routing import IntentRouter, IntentType
  - from daemons.routing import Intent, IntentRouter, IntentType, RouteResult
  - from daemons.watcher import IntentWatcher, WatcherConfig
  - from daemons.routing import (
            Intent,
            IntentRouter,
            IntentType,
            RouteResult,
        )
  - import logging
  - from daemons.routing import create_halt_handler
  - from daemons.routing import IntentType, parse_intent
  - from governance.halt import HaltManager
---
Classes:
  - TestHaltPriority
    Methods:
      - L53: def test_halt_is_priority_type(self):
      - L63: def test_halt_processed_before_queued(self, temp_dirs):
      - L123: def test_halt_triggers_immediately(self, temp_dirs):
      - L174: def test_halt_logged_as_warning(self, temp_dirs, caplog):
  - OrderTracker
    Methods:
      - L79: def __init__(self, name: str):
      - L82: def handle(self, intent: Intent) -> RouteResult:
  - MockHaltHandler
    Methods:
      - L144: def handle(self, intent: Intent) -> RouteResult:
  - NoOpHaltHandler
    Methods:
      - L189: def handle(self, intent: Intent) -> RouteResult:
  - TestHaltHandler
    Methods:
      - L222: def test_create_halt_handler_exists(self):
      - L230: def test_halt_handler_calls_halt_manager(self, temp_dirs):

Functions:
  - L27: def temp_dirs():
---


File: /Users/echopeso/phoenix/drills/d3_verification.py
Imports:
  - import os
  - import sys
  - import time
  - from pathlib import Path
  - from orientation.generator import OrientationGenerator
  - from orientation.generator import OrientationBead
  - from datetime import UTC, datetime
  - from orientation.validator import OrientationValidator
  - import traceback
---
Classes:
  - D3Verification
    Methods:
      - L28: def __init__(self):
      - L31: def test_inv_d3_checksum_1_machine_verifiable(self) -> bool:
      - L78: def test_inv_d3_checksum_hash_integrity(self) -> bool:
      - L104: def test_inv_d3_cross_check_1_verifiable(self) -> bool:
      - L130: def test_inv_d3_no_derived_1_no_summaries(self) -> bool:
      - L157: def test_positive_verification_speed(self) -> bool:
      - L186: def test_gate_d3_1_generates_from_state(self) -> bool:
      - L222: def test_gate_d3_2_verification_success(self) -> bool:
      - L246: def test_file_seam_output(self) -> bool:
      - L275: def run_all(self):

Global vars:
  - PHOENIX_ROOT
---

</file_map>
<user_instructions>
<taskname="Phoenix Gap Inventory"/>
<task>Build an external-oracle prompt for `INTEGRITY_SWEEP.PHOENIX.WED`: audit non-capital-path `phoenix/` areas for implementation reality and risk. Classify each focus directory as `REAL|STUB|STALE|DEAD`; surface silent-fail patterns (swallowed errors, quiet defaults, missing-state assumptions); map cross-repo refs (`phoenix-swarm/`, `dexter/`, `oracle/`) as real vs aspirational; identify modules claiming integration without proving tests; perform `CONSTITUTION/` reality check. Output must be DENSE_M2M YAML only with keys: `directory_inventory`, `silent_fails`, `cross_refs`, `dead_code`, `summary`. Keep `governance/`, `execution/`, `cso/`, `river/` out of primary scope except interface checks.</task>

<architecture>`phoenix/` has a mixed state: production-like runtime modules (`daemons`, `monitoring`, `notification`) alongside declared/placeholder surfaces (`CONSTITUTION`, parts of `state`, HUD mock fallbacks, synthetic validation generators). Non-capital-path evidence spans watcher/routing seams, health/manifest projection, narrator data plumbing, hooks policy enforcement, and analytics/refinery modules (`athena`, `cfp`, `validation`, `hunt`, `enrichment`, `slm`).</architecture>

<selected_context>
phoenix/daemons/routing.py: `parse_intent()` returns `None` on parse failures; contains explicit `create_stub_handler()` writing stub markdown; `create_halt_handler()` triggers `governance.halt.HaltManager`.
phoenix/daemons/watcher.py: exactly-once hash guard + quarantine flow; multiple `except Exception` paths and silent duplicate cleanup (`pass`).
phoenix/monitoring/alerts.py: debounce, callback fanout, auto-halt escalation; callback failures logged but non-blocking.
phoenix/monitoring/kill_manager.py: kill flag bead writes wrapped in silent `except Exception: pass` in multiple paths.
phoenix/notification/alert_taxonomy.py: routing and bundling logic; handler exceptions swallowed with `pass`.
phoenix/orientation/generator.py: many fallback defaults (env/default counts/providers); writes `state/orientation.yaml`.
phoenix/narrator/data_sources.py: multiple placeholder fetchers (`Athena`, `River`, `Tests`) and broad fallback behavior.
phoenix/state/manifest_writer.py: explicit HUD stub sections + graceful fallbacks (`decay: GREEN`, defaulted sections).
phoenix/widget/surface_renderer.py: strict projection layer, blank-on-missing behavior.
phoenix/surfaces/hud/WarBoarHUD/Services/ManifestWatcher.swift: watches Phoenix manifest but falls back to `MockManifest.json` paths.
phoenix/enrichment/layers/l2_reference_levels.py: `_add_stubbed_columns()` explicitly inserts Phase-3 stub columns.
phoenix/cfp/river_adapter.py: multiple fallback empty/conservative returns; partial metric placeholders (`win_rate`, `pnl`, etc.).
phoenix/athena/store.py: typed store surface + strict invariant framing (claim/fact/conflict separation).
phoenix/hunt/queue.py: explicit forbidden priority operations raise `PriorityForbiddenError` (FIFO lock).
phoenix/validation/backtest.py: worker uses synthetic/randomized metric generation (non-real computation path).
phoenix/tools/hooks/scalar_ban_hook.py: constitutional lint rules + commit blocking flow.
phoenix/slm/train_slm.py: explicit TODO for LoRA adapter loading path in inference test.
phoenix/drills/d3_verification.py: D3 verification harness for orientation invariants.
phoenix/tests/daemons/test_halt_priority.py: proving test for HALT priority/watcher handling.

Discovered by direct reads (not in final selection due budget/format limits):
- `CONSTITUTION/README.md` marks directory as SKELETON (<5% populated), with missing referenced scripts.
- `CONSTITUTION/CONSTITUTION_MANIFEST.yaml` declares broad taxonomy/migration/validation scaffolding.
- `CONSTITUTION/modules/README.md` and `CONSTITUTION/wiring/README.md` are “to be created” templates.
- `CONSTITUTION/invariants/INV-GOV-HALT-BEFORE-ACTION.yaml` references execution files/tests that should be reality-checked.
- `config/profiles/live.yaml` is explicitly labeled PLACEHOLDER.
- `scripts/deployment_audit.py` and `scripts/validate_registry.py` provide deployment/registry checks; `validate_registry.py` explicitly treats `dexter/` refs as cross-repo skips.
</selected_context>

<relationships>
- `daemons/watcher.py` -> `daemons/routing.py` (`parse_intent`, route, HALT priority) -> handler outputs/quarantine.
- `monitoring/alerts.py` can escalate to halt callback; `monitoring/kill_manager.py` maintains kill-bead state used by broader health/state paths.
- `orientation/generator.py` emits orientation state consumed by `widget/surface_renderer.py` and narrator data loaders.
- `state/manifest_writer.py` projects health/orientation into HUD manifest; `ManifestWatcher.swift` consumes that manifest but can drop to mock fallback.
- `cfp/river_adapter.py` feeds `cfp` query execution with conservative fallback defaults; `validation/backtest.py` currently demonstrates synthetic output generation.
- `tools/hooks/scalar_ban_hook.py` enforces constitutional language/metric constraints pre-commit.
</relationships>

<ambiguities>
- `oracle/` repository is not loaded, so cross-repo target reality for oracle references cannot be directly verified.
- File-search in this workspace is noisy across loaded roots (`phoenix`, `phoenix-swarm`, `dexter`); use path-qualified evidence when classifying cross-repo links.
- Final selection is codemap-heavy due strict token cap and workspace tree overhead; use the discovered read notes above as implementation evidence anchors where source files were omitted.
</ambiguities>
</user_instructions>
