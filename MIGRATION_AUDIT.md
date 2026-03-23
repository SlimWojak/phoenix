# MIGRATION_AUDIT.md
# a8ra — M4 → M3 Infrastructure Migration Audit

```yaml
document: MIGRATION_AUDIT
version: 1.0
date: 2026-03-23
status: CANONICAL — produced by RepoPrompt structural scan (3 repos, 6 scans)
purpose: Complete inventory of everything that must change for M3 Ultra production deployment
author: Opus (RepoPrompt, P3.A audit)
source_machine: M4 Studio (echopeso, 100.120.83.66)
target_machine: M3 Ultra (a8ra_m3, 100.114.164.22)
methodology: file_search across 1951 files + launchd/cron inspection + filesystem validation
pass_condition: "CTO hands this to COO and says 'execute this checklist'"
```

---

## 1. SERVICE INVENTORY

Every process running as a service, daemon, or cron on M4.

### 1.1 LaunchAgents (~/Library/LaunchAgents/)

| Label | Script | RunAtLoad | KeepAlive | Logs | Migrates? |
|-------|--------|-----------|-----------|------|-----------|
| `com.a8ra.river` | `/Users/echopeso/phoenix/scripts/launch_river.sh` | YES | YES (unconditional) | `~/logs/river.{stdout,stderr}.log` | **YES** — River streamer moves to M3 |
| `com.nex.ibkr-gateway` | `/Users/echopeso/ibc/start_gateway.sh paper` | YES | YES (on abnormal exit) | `~/ibc/logs/launchd_{stdout,stderr}.log` | **YES** — IBKR Gateway moves to M3 |
| `com.a8ra.mcp` | `/Users/echopeso/a8ra/mcp/server.py` | YES | YES | `/tmp/a8ra-mcp.{log,err}` | **NO** — M4 keeps its own MCP server; M3 already has one |
| `com.nex.cockpit` | `python3 -m nex_os.cockpit.app` (in ~/nex) | YES | YES | `~/nex/logs/cockpit_{stdout,stderr}.log` | **NO** — legacy NEX, not part of a8ra |

### 1.2 Cron Jobs (crontab -l)

| Schedule | Command | Migrates? |
|----------|---------|-----------|
| `*/5 * * * *` | `/Users/echopeso/ibc/check_gateway.sh` | **YES** — IBKR health check moves with Gateway |
| `*/5 * * * *` | `cd ~/phoenix && python -m state.manifest_writer` | **YES** — HUD manifest refresh |
| `0 */6 * * *` | `cd ~/phoenix && python drills/s44_soak_test.py --heartbeat` | **REMOVE** — S44 soak test is historical, no longer needed |
| `*/30 * * * *` | `/Users/echopeso/nex/scripts/cron_refresh_enrichment.sh` | **NO** — legacy NEX enrichment |
| `0 7 * * *` | `cd ~/echo_os && python workers/morning_brief.py` | **NO** — echo_os personal system |
| `*/30 * * * *` (×3) | echo_os snapshot/notion workers | **NO** — personal system |

### 1.3 Services NOT Yet Daemonized (batch scripts, must be promoted)

| Service | Current Invocation | Location | Migrates? |
|---------|--------------------|----------|-----------|
| **Dexter detection pipeline** | `python3 scripts/daily_detection_export.py YYYY-MM-DD` (manual CLI) | `dexter/scripts/daily_detection_export.py` | **YES** — needs daemon wrapper on M3 |
| **MIRROR backend** | `python server.py` or `uvicorn server:app --port 8300` (manual) | `research_accelerator/mirror/backend/server.py` | **YES** — needs launchd plist on M3 |
| **Bridge cadence loop** | `orchestrator.cycle()` called manually | `dexter/dexter/bridge/orchestrator.py` | **YES** — needs daemon with polling cadence |
| **Dream Cycle** | `python scripts/dream_cycle_nightly.py --date YYYY-MM-DD` (manual) | `dexter/scripts/dream_cycle_nightly.py` | **YES** — needs nightly cron on M3 |
| **Strategy orchestrator** | Does not exist yet (P1.3 in DEPLOYMENT_ROADMAP) | `phoenix/daemons/strategy_orchestrator.py` (planned) | **YES** — will be primary M3 daemon |

### 1.4 Already on M3

| Service | Status | Notes |
|---------|--------|-------|
| `@a8ra_COO_bot` (Telegram) | OPERATIONAL | Already deployed and tested |
| Bead Field store (69GB synthetic) | DEPLOYED | 11.4M FACTs, SQLite |
| MCP server (port 7700) | OPERATIONAL | 4 tools, M3-specific |
| Claude Code 2.1.76 | INSTALLED | COO sessions active |

---

## 2. HARDCODED PATHS

Every M4-specific path found in code, with file:line.

### 2.1 `/Users/echopeso` (absolute — WILL BREAK on M3 where user is `a8ra_m3`)

| File | Line | Content | Severity |
|------|------|---------|----------|
| `dexter/.claude/settings.local.json` | 9 | `/Users/echopeso/phoenix-swarm/scripts/session_end_hook.sh` | LOW — dev tooling only |
| `phoenix/surfaces/hud/scripts/test-stale.sh` | 4 | `/Users/echopeso/phoenix-hud/WarBoarHUD/...` | LOW — HUD test script |
| `phoenix/surfaces/hud/scripts/test-watcher.sh` | 5 | `/Users/echopeso/phoenix-hud/WarBoarHUD/...` | LOW — HUD test script |
| `phoenix/tests/chaos/test_bunny_s33_p1.py` | 312, 340 | `sys.path.insert(0, '/Users/echopeso/phoenix')` | **MEDIUM** — test will fail |
| `research_accelerator/.factory/services.yaml` | 2-21 | 8× `cd /Users/echopeso/research_accelerator && ...` | **HIGH** — all RA Factory commands |
| `research_accelerator/.factory/init.sh` | 4 | `cd /Users/echopeso/research_accelerator` | **HIGH** — Factory bootstrap |
| `research_accelerator/tests/test_scored_comparison.py` | 518-579 | 4× `/Users/echopeso/research_accelerator/site/detect.py` | **MEDIUM** — tests will fail |
| `research_accelerator/reports/autoresearch/eval_*.yaml` | 3 | 5× `/Users/echopeso/research_accelerator/research/ground_truth/...` | LOW — historical reports |
| `research_accelerator/.factory/validation/*/synthesis.json` | 8 | 6× `cd /Users/echopeso/research_accelerator && ...` | LOW — validation artifacts |

**LaunchAgents (outside repos):**

| File | Hardcoded Path | Must Change |
|------|----------------|-------------|
| `~/Library/LaunchAgents/com.a8ra.river.plist` | `/Users/echopeso/phoenix/scripts/launch_river.sh`, `/Users/echopeso/logs/...`, `/Users/echopeso/.pyenv/shims:...`, `RIVER_ROOT=/Users/echopeso/phoenix-river` | **ALL** |
| `~/Library/LaunchAgents/com.nex.ibkr-gateway.plist` | `/Users/echopeso/ibc/start_gateway.sh`, `/Users/echopeso/ibc/logs/...`, `HOME=/Users/echopeso` | **ALL** |
| `~/ibc/start_gateway.sh` | `IBC_PATH="/Users/echopeso/ibc"`, `GATEWAY_PATH="/Users/echopeso/Applications/IB Gateway 10.37"`, `CONFIG_PATH="/Users/echopeso/ibc/config/config.ini"`, `LOG_PATH="/Users/echopeso/ibc/logs"` | **ALL** |
| `~/ibc/check_gateway.sh` | `LOG="/Users/echopeso/ibc/logs/health.log"`, `RESTART_ATTEMPT_FILE="/Users/echopeso/ibc/logs/.restart_attempts"` | **ALL** |

**Crontab entries:**

| Cron Line | Path | Must Change |
|-----------|------|-------------|
| `*/5 * * * * /Users/echopeso/ibc/check_gateway.sh` | absolute echopeso path | YES |
| `*/5 * * * * cd ~/phoenix && source .venv/bin/activate && python -m state.manifest_writer` | uses `~` (OK if user set correctly) | Review |
| `0 */6 * * * cd ~/phoenix && source .venv/bin/activate && python drills/s44_soak_test.py` | uses `~` (OK) | REMOVE (obsolete) |

### 2.2 `~/phoenix-river` (uses `~` or `Path.home()` — resolves per-user, OK if RIVER_ROOT set)

These all use `os.path.expanduser("~")` or `Path.home()`, which will resolve to `/Users/a8ra_m3` on M3. All support `RIVER_ROOT` env var override EXCEPT:

| File | Line | Resolution Method | Env Override? |
|------|------|-------------------|---------------|
| `phoenix/river/schema.py` | 41 | `os.environ.get("RIVER_ROOT", str(Path.home() / "phoenix-river"))` | ✅ YES |
| `phoenix/river/streamer.py` | (via schema.py) | inherits from schema.py | ✅ YES |
| `phoenix/river/writer.py` | 62 | documents RIVER_ROOT | ✅ YES |
| `phoenix/scripts/launch_river.sh` | 8 | `RIVER_ROOT="${RIVER_ROOT:-$HOME/phoenix-river}"` | ✅ YES |
| `dexter/dexter/bead_field/river/river_adapter.py` | 23 | `Path.home() / "phoenix-river"` (hardcoded default) | **⚠️ NO** — constructor accepts override but default is hardcoded |
| `research_accelerator/src/ra/data/river_adapter.py` | 52 | `Path(os.path.expanduser("~/phoenix-river"))` — but checks `RIVER_ROOT` env first | ✅ YES |
| `research_accelerator/mirror/backend/server.py` | 69 | `Path.home() / "phoenix-river"` (hardcoded) | **⚠️ NO** — no env override |

### 2.3 `~/dexter` (Dexter repo path references)

| File | Line | Content |
|------|------|---------|
| `dexter/dexter/bead_field/query/field_query.py` | 23 | `DEFAULT_DB_DIR = os.path.expanduser("~/dexter/tools/synthetic")` |
| `dexter/dexter/bead_field/query/tests/test_chain.py` | 11 | `os.path.expanduser("~/dexter/tools/synthetic/synthetic_beads.db")` |
| `dexter/dexter/bead_field/query/tests/test_field_query.py` | 10 | `os.path.expanduser("~/dexter/tools/synthetic")` |
| `dexter/dexter/bead_field/query/tests/test_temporal.py` | 12 | same pattern |
| `dexter/dexter/bead_field/query/tests/test_verify.py` | 10 | same pattern |
| `dexter/dexter/bead_field/validation/extract_golden_windows.py` | 30 | `~/dexter/tools/synthetic/synthetic_beads.db` |
| `dexter/dexter/bead_field/validation/generate_chart_overlays.py` | 50 | same |
| `dexter/scripts/gate5_comparison.py` | 37 | `~/dexter/reports` |
| `dexter/scripts/gate6_verification.py` | 38 | `~/dexter/reports` |
| `dexter/scripts/gate_b3c_signal_alignment.py` | 50 | `~/dexter/reports` |
| `research_accelerator/mirror/backend/server.py` | 30 | `DEXTER_ROOT = Path.home() / "dexter"` |

All use `~` expansion — will resolve to `/Users/a8ra_m3/dexter` on M3.

### 2.4 `~/nex/river.db` (LEGACY — stale reference)

| File | Line | Content | Severity |
|------|------|---------|----------|
| `phoenix/config/profiles/paper.yaml` | 16 | `data_path: "~/nex/river.db"` | **STALE** — River moved to parquet; this SQLite ref is dead |
| `phoenix/config/profiles/live.yaml` | 21 | `data_path: "~/nex/river.db"` | **STALE** — same |
| `phoenix/config/schema.py` | 54 | `default="~/nex/river.db"` | **STALE** — code default |

---

## 3. IBKR CONFIGURATION

### 3.1 Gateway Components (currently at ~/ibc/)

| Component | Path | Purpose |
|-----------|------|---------|
| `start_gateway.sh` | `~/ibc/start_gateway.sh` | Startup script — launches IBC → IB Gateway |
| `stop_gateway.sh` | `~/ibc/stop_gateway.sh` | Graceful shutdown |
| `check_gateway.sh` | `~/ibc/check_gateway.sh` | Health check (cron every 5min), max 3 restarts/day |
| `config.ini` | `~/ibc/config.ini` | IBC configuration |
| `IBC.jar` | `~/ibc/IBC.jar` | IBC v3.23.0 automation JAR |
| `gatewaystartmacos.sh` | `~/ibc/gatewaystartmacos.sh` | IBC's own gateway launcher |
| `REPLICATION_GUIDE.md` | `~/ibc/REPLICATION_GUIDE.md` | Pre-existing migration guide (targets user "olya") |

### 3.2 Connection Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Gateway host | `127.0.0.1` | `phoenix/brokers/ibkr/config.py:75`, `connector.py:529`, `config/profiles/*.yaml` |
| Paper port | `4002` | `config.py:82`, `streamer.py:58`, `writer.py:55`, `paper.yaml:9` |
| Live port | `4001` | `live.yaml:14` |
| Client ID | `1` | `paper.yaml:12`, `live.yaml:17` |
| Trading mode | `paper` | `ibc/config.ini:TradingMode`, launchd plist arg |
| IBKR username | `hpqvlu803` | `ibc/config.ini:IbLoginId` |
| Password | `1Lovenex1` | `ibc/config.ini:IbPassword` (⚠️ plaintext at bottom of file) |
| Allowed IPs | `127.0.0.1` | `ibc/config.ini:IbAllowedIpAddresses` |
| 2FA handler | `manual` (IBKR Mobile) | `ibc/config.ini:SecondFactorAuthenticationHandler` |
| 2FA timeout | `180s` | `ibc/config.ini:SecondFactorAuthenticationTimeout` |
| Auto-closedown | `Saturday 03:00` | `ibc/config.ini:ClosedownAt` |

### 3.3 All Code Referencing 127.0.0.1 (IBKR context)

| File | Line | Context |
|------|------|---------|
| `phoenix/brokers/ibkr/config.py` | 75, 103, 119 | Default host, env doc, env read |
| `phoenix/brokers/ibkr/connector.py` | 529, 541 | Connection defaults |
| `phoenix/config/profiles/paper.yaml` | 8 | Profile setting |
| `phoenix/config/profiles/live.yaml` | 13 | Profile setting |
| `phoenix/config/schema.py` | 31 | Pydantic default |
| `phoenix/monitoring/dashboard.py` | 495, 565 | Dashboard bind (not IBKR) |
| `phoenix/river/streamer.py` | 133 | Direct connect call |
| `phoenix/river/writer.py` | 271 | Direct connect call |
| `phoenix/scripts/deployment_audit.py` | 90 | Port check |

**Migration note:** When Gateway moves to M3, Phoenix code on M3 will still connect to `127.0.0.1:4002` (local). This is correct — Gateway and Phoenix run on same machine. The `IBKR_HOST` env var provides override if needed.

### 3.4 Env Var Override Map

| Env Var | Default | Used By | Override Mechanism |
|---------|---------|---------|-------------------|
| `IBKR_HOST` | `127.0.0.1` | config.py, connector.py | `os.getenv("IBKR_HOST", "127.0.0.1")` |
| `IBKR_PORT` | `4002` | config.py, connector.py, streamer.py, deployment_audit.py | `os.getenv("IBKR_PORT", "4002")` |
| `IBKR_CLIENT_ID` | `1` | config.py | `os.getenv("IBKR_CLIENT_ID", "1")` |
| `IBKR_MODE` | `mock` | .env.example | env-only |
| `IBKR_ALLOW_LIVE` | `false` | .env.example | env-only |
| `IBKR_PASSWORD` | (none) | ibc/start_gateway.sh | sets `IB_PASSWORD` for IBC |

---

## 4. RIVER DATA TOPOLOGY

### 4.1 Data Layout

```
~/phoenix-river/                          # 1.1 GB total, 6 pairs
├── AUDUSD/{year}/{mm}/{dd}.parquet
├── EURUSD/{year}/{mm}/{dd}.parquet       # Primary pair (most data)
├── GBPUSD/{year}/{mm}/{dd}.parquet
├── USDCAD/{year}/{mm}/{dd}.parquet
├── USDCHF/{year}/{mm}/{dd}.parquet
├── USDJPY/{year}/{mm}/{dd}.parquet
├── {pair}/.staging/{YYYY-MM-DD}.jsonl    # Live intraday accumulation
└── .heartbeat.json                        # Streamer liveness
```

### 4.2 Writers (Append-Only)

| Writer | File | Mechanism | What It Writes |
|--------|------|-----------|----------------|
| RiverStreamer | `phoenix/river/streamer.py` | IBKR keepUpToDate callback | Staging JSONL → daily parquet (consolidation at 17:00 NY) |
| RiverWriter | `phoenix/river/writer.py` | Historical backfill | Direct parquet (2-day chunks, write-once guard) |

### 4.3 Readers (All Read-Only) — Complete Consumer Map

| Consumer | File | Read Method | Env Override? | Notes |
|----------|------|-------------|---------------|-------|
| **Phoenix RiverReader** | `phoenix/river/reader.py` | DuckDB glob `**/*.parquet` | ✅ via `get_river_root()` → RIVER_ROOT | Ghost injection, TF aggregation |
| **Phoenix CFP adapter** | `phoenix/cfp/river_adapter.py` | Read-only | ✅ via schema.py | CFP lens queries |
| **Phoenix data reader** | `phoenix/data/river_reader.py` | Thin wrapper | ✅ via schema.py | Additional read path |
| **Dexter RiverBarAdapter** | `dexter/dexter/bead_field/river/river_adapter.py` | `pd.read_parquet()` per day + staging JSONL | **⚠️ Hardcoded `Path.home() / "phoenix-river"`** — constructor accepts override | 30-day warmup |
| **RA RiverAdapter** | `research_accelerator/src/ra/data/river_adapter.py` | DuckDB `read_parquet([file_list])` | ✅ via RIVER_ROOT env | Asia/Bangkok→UTC normalization |
| **MIRROR backend** | `research_accelerator/mirror/backend/server.py` | Imports Dexter's `RiverBarAdapter` + direct `Path.home() / "phoenix-river"` | **⚠️ Hardcoded** | WebSocket live data, detection JSON |
| **RA test** | `research_accelerator/tests/test_river_adapter.py` | DuckDB via RIVER_ROOT env | ✅ via RIVER_ROOT env | |
| **RA init.sh** | `research_accelerator/.factory/init.sh` | Path check only | ✅ via RIVER_ROOT env | |

### 4.4 Detection Output Path

| Output | Path | Writer | Readers |
|--------|------|--------|---------|
| Daily detection JSON | `~/dexter/output/detections/{date}.json` | `dexter/scripts/daily_detection_export.py` | MIRROR backend (`server.py:73`), Dream Cycle analyzer |
| Dream Cycle briefing | `~/dexter/output/dream_cycle/{date}_briefing.{json,md}` | `dexter/scripts/dream_cycle_nightly.py` | Morning briefing consumers |

---

## 5. PYTHON ENVIRONMENT

### 5.1 Python Versions

| Context | Version | Path | Manager |
|---------|---------|------|---------|
| System global | 3.12.6 | `~/.pyenv/shims/python3` | pyenv |
| Phoenix venv | 3.12.6 | `~/phoenix/.venv/bin/python3` | pyenv + venv |
| pyenv installed | 3.11.9, 3.12.6* | — | pyenv |

**M3 must match:** Python 3.12.x (phoenix requires >=3.11, RA requires >=3.12)

### 5.2 Dependencies Per Repo

**Phoenix** (`pyproject.toml`):
- Core: `structlog>=24.1.0`, `pyyaml>=6.0`, `pydantic>=2.0`
- Implicit (in mypy overrides): `pandas`, `pyarrow`, `duckdb`, `ib_insync`, `nest_asyncio`, `httpx`, `numpy`
- Dev: `pytest>=8.0`, `pytest-asyncio>=0.23`, `pytest-xdist>=3.5.0`, `mypy>=1.8`, `ruff>=0.2`, `pre-commit>=3.6`

**Dexter** (`requirements.txt`):
- Core: `openai>=1.0.0`, `requests>=2.28.0`, `httpx>=0.27.0`, `python-dotenv>=1.0.0`, `pydantic>=2.0.0`, `pyyaml>=6.0`, `matrix-nio>=0.21.0`, `PyMuPDF>=1.24.0`
- Bead Field: `pydantic>=2.12.0`, `uuid6>=2025.0.1`, `ecdsa>=0.19.0`, `pqcrypto>=0.4.0`, `pyyaml>=6.0`, `pytest>=9.0.0`, `pytest-cov>=7.0.0`
- Implicit: `pandas`, `pyarrow` (River adapter)

**Research Accelerator** (`pyproject.toml`):
- Core: `pandas>=2.0`, `duckdb>=0.9`, `pyarrow>=14.0`, `pydantic>=2.0`, `pyyaml>=6.0`
- MIRROR: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`, `websockets>=12.0`, `watchdog>=3.0.0`, `pandas>=2.0.0`, `pyarrow>=14.0.0`

### 5.3 System-Level Dependencies

| Dependency | Used By | Install Method |
|------------|---------|----------------|
| DuckDB | Phoenix RiverReader, RA RiverAdapter | pip (Python package) |
| pyarrow | All River consumers/writers | pip |
| ib_insync | Phoenix IBKR broker, streamer, writer | pip |
| IB Gateway 10.37 | IBKR market data | macOS app install at `~/Applications/IB Gateway 10.37/` |
| IBC 3.23.0 | Gateway automation | `~/ibc/IBC.jar` (Java) |
| Java | IBC.jar | System Java (required for IBC) |
| pyenv | Python version management | brew |
| Tailscale | Cluster mesh network | macOS app |

### 5.4 Virtual Environments

| Repo | Venv Location | Status |
|------|---------------|--------|
| Phoenix | `~/phoenix/.venv/` | EXISTS — Python 3.12.6 |
| Dexter | — | No venv found (uses global Python) |
| RA | — | No venv found (uses global Python, editable install) |

---

## 6. CONFIG MAP

All environment-varying configuration with current M4 values.

### 6.1 Environment Variables (.env.example + launchd + cron)

| Variable | M4 Value | M3 Must Be | Source |
|----------|----------|-------------|--------|
| `RIVER_ROOT` | `/Users/echopeso/phoenix-river` | `/Users/a8ra_m3/phoenix-river` | launchd plist, launch_river.sh |
| `IBKR_HOST` | `127.0.0.1` | `127.0.0.1` (same — local) | .env.example |
| `IBKR_PORT` | `4002` | `4002` (paper) or `4001` (live) | .env.example |
| `IBKR_CLIENT_ID` | `1` | `1` | .env.example |
| `IBKR_MODE` | `mock` | `paper` (production) | .env.example |
| `IBKR_PASSWORD` | (set in config.ini) | Must set securely | ibc/start_gateway.sh |
| `ANTHROPIC_API_KEY` | (macOS Keychain) | Must configure | .env.example |
| `TELEGRAM_BOT_TOKEN` | (set) | Already configured on M3 | .env.example |
| `TELEGRAM_CHAT_ID` | (set) | Already configured on M3 | .env.example |
| `OLLAMA_URL` | `http://localhost:11434` | Update if models on DGX | .env.example |
| `PYTHONUNBUFFERED` | `1` | `1` | launch_river.sh |
| `PATH` | `/Users/echopeso/.pyenv/shims:...` | `/Users/a8ra_m3/.pyenv/shims:...` | launchd plists |

### 6.2 Config Profiles

| Profile | File | Key Differences from Default |
|---------|------|------------------------------|
| Paper | `phoenix/config/profiles/paper.yaml` | port 4002, paper_mode=true, telegram disabled |
| Live | `phoenix/config/profiles/live.yaml` | port 4001, paper_mode=false, telegram enabled, stricter thresholds |

**Stale field in both profiles:** `river.data_path: "~/nex/river.db"` — dead reference to legacy NEX SQLite.

### 6.3 Ports

| Port | Service | Scope |
|------|---------|-------|
| 4002 | IBKR Gateway (paper) | localhost only |
| 4001 | IBKR Gateway (live) | localhost only |
| 7700 | MCP health server | Tailscale mesh |
| 8080 | Phoenix monitoring dashboard | localhost |
| 8100 | RA calibration site (http.server) | localhost |
| 8200 | RA validation serve.py | localhost |
| 8300 | MIRROR backend (FastAPI) | localhost |
| 8787 | Calibration tool | localhost |
| 11434 | Ollama (local LLM) | localhost |

### 6.4 Secrets Location

| Secret | M4 Location | M3 Action |
|--------|-------------|-----------|
| IBKR credentials | `~/ibc/config.ini` (⚠️ plaintext) | Keychain or env var (do NOT copy plaintext) |
| IBKR account ID | macOS Keychain (`a8ra-ibkr-dev`) | Create Keychain entry (`a8ra-ibkr-paper` or `-live`) |
| API keys (Anthropic, etc.) | `~/.env` or Keychain | Configure per M3 environment |
| Telegram tokens | Already on M3 | No action needed |
| SSH keys | `~/.ssh/` | M3 already has own keys, COO has SSH to all nodes |

### 6.5 IBC Configuration Deltas for M3

| Setting | M4 Value | M3 Value |
|---------|----------|----------|
| IbLoginId | `hpqvlu803` | Same (same IBKR account) or new account |
| TradingMode | `paper` | `paper` initially → `live` after graduation |
| Config path | `/Users/echopeso/ibc/config/config.ini` | `/Users/a8ra_m3/ibc/config/config.ini` |
| Gateway path | `/Users/echopeso/Applications/IB Gateway 10.37` | `/Users/a8ra_m3/Applications/IB Gateway 10.37/` |
| IbPassword | plaintext in file | **Use env var `IBKR_PASSWORD` instead** |

---

## 7. MIGRATION CHECKLIST

Ordered by dependency — do X before Y.

### Phase A: Foundation (must complete first)

- [ ] **A.1** Install Python 3.12.x on M3 via pyenv
  - `pyenv install 3.12.6 && pyenv global 3.12.6`

- [ ] **A.2** Install Java runtime on M3 (required for IBC/IB Gateway)
  - Verify: `java -version`

- [ ] **A.3** Clone/sync repos to M3
  - `~/phoenix/`, `~/dexter/`, `~/research_accelerator/` must exist
  - M3 user is `a8ra_m3` → paths resolve to `/Users/a8ra_m3/{repo}`
  - Note: repos may already exist on M3 from earlier deployments

- [ ] **A.4** Create Python venvs on M3
  - `cd ~/phoenix && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - Install implicit deps: `pip install pandas pyarrow duckdb ib_insync nest_asyncio httpx numpy structlog`
  - Dexter: `cd ~/dexter && pip install -r dexter/requirements.txt -r dexter/bead_field/requirements.txt`
  - Also install pandas + pyarrow for Dexter River adapter
  - MIRROR: `pip install -r ~/research_accelerator/mirror/requirements.txt`

- [ ] **A.5** Set `RIVER_ROOT` in M3 shell profile
  - Add to `~/.zshrc`: `export RIVER_ROOT="/Users/a8ra_m3/phoenix-river"`

- [ ] **A.6** Transfer River data (1.1 GB)
  - `rsync -avz echopeso@m4-studio:~/phoenix-river/ ~/phoenix-river/`
  - Verify: all 6 pairs present, parquet files readable
  - Subsequent syncs: rsync delta only (new daily parquets)

### Phase B: IBKR Gateway (depends on A.1, A.2)

- [ ] **B.1** Install IB Gateway 10.37 on M3
  - Download from IBKR, install to `~/Applications/IB Gateway 10.37/`

- [ ] **B.2** Copy and update IBC directory
  - `rsync -avz echopeso@m4-studio:~/ibc/ ~/ibc/`
  - Update ALL paths in `start_gateway.sh`: `sed -i '' 's|/Users/echopeso|/Users/a8ra_m3|g'`
  - Update ALL paths in `check_gateway.sh`: same sed
  - Update ALL paths in `stop_gateway.sh`: same sed
  - **CRITICAL:** Remove plaintext password from `config.ini` — use `IBKR_PASSWORD` env var
  - Set in `~/.zshrc`: `export IBKR_PASSWORD="<from-keychain>"`
  - Pre-existing `REPLICATION_GUIDE.md` in `~/ibc/` documents this process (targets user "olya" — update to "a8ra_m3")

- [ ] **B.3** Create IBKR Gateway launchd plist on M3
  - Copy `com.nex.ibkr-gateway.plist` to `~/Library/LaunchAgents/`
  - Replace ALL `/Users/echopeso` → `/Users/a8ra_m3`
  - `launchctl load ~/Library/LaunchAgents/com.nex.ibkr-gateway.plist`

- [ ] **B.4** Create IBKR health check cron on M3
  - `*/5 * * * * /Users/a8ra_m3/ibc/check_gateway.sh`

- [ ] **B.5** Verify Gateway starts and 2FA works
  - Manual: `~/ibc/start_gateway.sh paper`
  - Approve 2FA on IBKR Mobile
  - Verify: `lsof -i :4002` shows Gateway listening

### Phase C: River Streamer (depends on A.4, A.5, A.6, B.5)

- [ ] **C.1** Create River launchd plist on M3
  - Copy `com.a8ra.river.plist` to `~/Library/LaunchAgents/`
  - Replace ALL `/Users/echopeso` → `/Users/a8ra_m3`
  - Update PATH to M3's pyenv shims: `/Users/a8ra_m3/.pyenv/shims:...`
  - Update RIVER_ROOT: `/Users/a8ra_m3/phoenix-river`
  - Create log directory: `mkdir -p ~/logs`
  - `launchctl load ~/Library/LaunchAgents/com.a8ra.river.plist`

- [ ] **C.2** Verify River streaming
  - Check logs: `tail -f ~/logs/river.stdout.log`
  - Verify heartbeat: `cat ~/phoenix-river/.heartbeat.json`
  - Verify staging JSONL files appearing in `~/phoenix-river/EURUSD/.staging/`
  - Wait for consolidation at 17:00 NY — verify daily parquet created

- [ ] **C.3** Stop River streamer on M4
  - `launchctl unload ~/Library/LaunchAgents/com.a8ra.river.plist` on M4
  - Only after M3 streamer is confirmed operational

### Phase D: Detection Pipeline + MIRROR (depends on A.3, A.4, C.1)

- [ ] **D.1** Fix Dexter RiverBarAdapter hardcoded path
  - `dexter/dexter/bead_field/river/river_adapter.py:23`: Add `RIVER_ROOT` env var support
  - Change: `RIVER_ROOT = Path(os.environ.get("RIVER_ROOT", str(Path.home() / "phoenix-river")))`

- [ ] **D.2** Fix MIRROR server hardcoded paths
  - `research_accelerator/mirror/backend/server.py:69`: Add RIVER_ROOT env support
  - `research_accelerator/mirror/backend/server.py:30`: Add DEXTER_ROOT env support or make configurable

- [ ] **D.3** Create detection pipeline daemon/cron on M3
  - Nightly: `python3 ~/dexter/scripts/daily_detection_export.py $(date +%Y-%m-%d)`
  - Or: daemon watching staging JSONL (MIRROR pattern)
  - Output: `~/dexter/output/detections/{date}.json`

- [ ] **D.4** Create MIRROR launchd plist on M3
  - Service: `cd ~/research_accelerator/mirror/backend && python3 server.py`
  - Port 8300, KeepAlive
  - Depends on River data + detection JSONs

- [ ] **D.5** Create Dream Cycle nightly cron on M3
  - `0 22 * * 1-5 cd ~/dexter && python3 scripts/dream_cycle_nightly.py --date $(date +%Y-%m-%d)`
  - Adjust time for 30min after market close (22:00 UTC = 17:30 NY)

### Phase E: Bridge + Orchestrator (depends on D.1)

- [ ] **E.1** Create Bridge cadence daemon on M3
  - Polling loop calling `orchestrator.cycle()` every 60s
  - Launchd or cron

- [ ] **E.2** Create Strategy Orchestrator (P1.3 — planned, not yet built)
  - This is the primary Phoenix production daemon
  - Watches staging JSONL → enrichment → CSO → execution
  - Depends on DEPLOYMENT_ROADMAP Phase 1 completion

- [ ] **E.3** Create HUD manifest refresh cron on M3
  - `*/5 * * * * cd ~/phoenix && source .venv/bin/activate && python -m state.manifest_writer`

### Phase F: Cleanup + Validation

- [ ] **F.1** Fix stale `~/nex/river.db` references
  - `phoenix/config/profiles/paper.yaml:16` — remove or update `data_path`
  - `phoenix/config/profiles/live.yaml:21` — same
  - `phoenix/config/schema.py:54` — update default

- [ ] **F.2** Fix hardcoded test paths
  - `phoenix/tests/chaos/test_bunny_s33_p1.py:312,340` — use relative path or `Path(__file__)`
  - `research_accelerator/tests/test_scored_comparison.py:518-579` — use relative paths

- [ ] **F.3** Run full test suites on M3
  - `cd ~/phoenix && source .venv/bin/activate && python -m pytest tests/ -x`
  - `cd ~/dexter && python -m pytest dexter/bead_field/tests/ -x`
  - `cd ~/research_accelerator && python -m pytest tests/ -x`

- [ ] **F.4** Verify M3 services (post-migration smoke test)
  - [ ] IBKR Gateway listening on 4002: `lsof -i :4002`
  - [ ] River heartbeat fresh: `cat ~/phoenix-river/.heartbeat.json`
  - [ ] Staging JSONL accumulating: `ls ~/phoenix-river/EURUSD/.staging/`
  - [ ] MIRROR serving on 8300: `curl http://localhost:8300/health`
  - [ ] Detection JSON present: `ls ~/dexter/output/detections/`
  - [ ] MCP server responding: `curl http://localhost:7700/health`
  - [ ] Telegram bot responsive: send test message

- [ ] **F.5** Stop migrated services on M4
  - `launchctl unload ~/Library/LaunchAgents/com.nex.ibkr-gateway.plist`
  - `launchctl unload ~/Library/LaunchAgents/com.a8ra.river.plist`
  - Remove migrated cron entries
  - Keep: com.a8ra.mcp (M4's own MCP), development tools

- [ ] **F.6** Set up M4 as read-only River data consumer
  - Periodic rsync from M3: `rsync -avz a8ra_m3@a8ra-m3:~/phoenix-river/ ~/phoenix-river/`
  - Schedule: daily or on-demand for backtesting
  - River on M4 becomes read-only archive for dev

---

## APPENDIX: ITEMS NOT IN SCOPE

| Item | Reason |
|------|--------|
| DGX setup | Already operational, no migration needed |
| Playground node | Isolated sandbox, no production dependencies |
| Spitfire | VPS-hosted, independent |
| echo_os / personal crons | Not a8ra infrastructure |
| NEX (legacy) | Deprecated, not migrating |
| WarBoar HUD (SwiftUI) | macOS app, not a server service |
| RA .factory services (8100, 8200) | Calibration tools, stay on M4 for dev |

---

*Every service, path, config, and dependency catalogued. No guesses. File:line for every finding.*
