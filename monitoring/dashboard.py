"""
Health Dashboard — Observable system health for Sovereign/CTO

VERSION: 1.0
SPRINT: S28.B

METRICS:
- halt latency (live, p99)
- River quality score
- chaos vector status (last run)
- worker heartbeat (per worker, last seen)
- bead emission rate

RENDER: Simple HTTP server with HTML template
"""

import json
import time
import threading
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# METRICS STORE
# =============================================================================

@dataclass
class HaltMetrics:
    """Halt latency metrics."""
    last_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    samples: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def record(self, latency_ms: float) -> None:
        self.last_latency_ms = latency_ms
        self.samples.append(latency_ms)
        if len(self.samples) > 1000:
            self.samples = self.samples[-1000:]
        
        sorted_samples = sorted(self.samples)
        self.p99_latency_ms = sorted_samples[int(len(sorted_samples) * 0.99)] if sorted_samples else 0
        self.max_latency_ms = max(self.samples) if self.samples else 0
        self.last_updated = datetime.now(timezone.utc)


@dataclass
class WorkerHeartbeat:
    """Worker heartbeat tracking."""
    worker_id: str
    last_seen: datetime
    status: str = "alive"
    task_count: int = 0


@dataclass
class ChaosStatus:
    """Chaos vector run status."""
    last_run: Optional[datetime] = None
    total_vectors: int = 0
    passed: int = 0
    failed: int = 0
    survival_rate: float = 0.0
    results: Dict[str, str] = field(default_factory=dict)


class MetricsStore:
    """
    Central store for dashboard metrics.
    Thread-safe updates.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Metrics
        self.halt_metrics = HaltMetrics()
        self.river_quality: float = 1.0
        self.workers: Dict[str, WorkerHeartbeat] = {}
        self.chaos_status = ChaosStatus()
        self.bead_emission_rate: float = 0.0
        self.bounds_violations: int = 0
        
        # Telemetry expansion metrics
        self.cascade_timing_histogram: List[float] = []
        self.signal_generation_rate: float = 0.0  # stub for CSO
    
    def record_halt_latency(self, latency_ms: float) -> None:
        with self._lock:
            self.halt_metrics.record(latency_ms)
    
    def record_cascade_timing(self, timing_ms: float) -> None:
        with self._lock:
            self.cascade_timing_histogram.append(timing_ms)
            if len(self.cascade_timing_histogram) > 1000:
                self.cascade_timing_histogram = self.cascade_timing_histogram[-1000:]
    
    def update_river_quality(self, quality: float) -> None:
        with self._lock:
            self.river_quality = quality
    
    def update_worker_heartbeat(self, worker_id: str, status: str = "alive", task_count: int = 0) -> None:
        with self._lock:
            self.workers[worker_id] = WorkerHeartbeat(
                worker_id=worker_id,
                last_seen=datetime.now(timezone.utc),
                status=status,
                task_count=task_count
            )
    
    def remove_worker(self, worker_id: str) -> None:
        with self._lock:
            self.workers.pop(worker_id, None)
    
    def update_chaos_status(
        self,
        total: int,
        passed: int,
        failed: int,
        results: Dict[str, str]
    ) -> None:
        with self._lock:
            self.chaos_status = ChaosStatus(
                last_run=datetime.now(timezone.utc),
                total_vectors=total,
                passed=passed,
                failed=failed,
                survival_rate=passed / total * 100 if total > 0 else 0,
                results=results
            )
    
    def increment_bounds_violation(self) -> None:
        with self._lock:
            self.bounds_violations += 1
    
    def update_bead_rate(self, rate: float) -> None:
        with self._lock:
            self.bead_emission_rate = rate
    
    def update_signal_rate(self, rate: float) -> None:
        with self._lock:
            self.signal_generation_rate = rate
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get thread-safe snapshot of all metrics."""
        with self._lock:
            now = datetime.now(timezone.utc)
            
            # Calculate worker staleness
            worker_list = []
            for w in self.workers.values():
                staleness = (now - w.last_seen).total_seconds()
                worker_list.append({
                    "id": w.worker_id,
                    "status": w.status,
                    "last_seen": w.last_seen.isoformat(),
                    "staleness_seconds": staleness,
                    "task_count": w.task_count,
                    "health": "healthy" if staleness < 30 else ("stale" if staleness < 60 else "dead")
                })
            
            return {
                "timestamp": now.isoformat(),
                "halt": {
                    "last_ms": self.halt_metrics.last_latency_ms,
                    "p99_ms": self.halt_metrics.p99_latency_ms,
                    "max_ms": self.halt_metrics.max_latency_ms,
                    "samples": len(self.halt_metrics.samples),
                    "slo_50ms": self.halt_metrics.p99_latency_ms < 50,
                },
                "river": {
                    "quality": self.river_quality,
                    "health": "healthy" if self.river_quality >= 0.8 else ("degraded" if self.river_quality >= 0.5 else "critical")
                },
                "workers": worker_list,
                "chaos": {
                    "last_run": self.chaos_status.last_run.isoformat() if self.chaos_status.last_run else None,
                    "total": self.chaos_status.total_vectors,
                    "passed": self.chaos_status.passed,
                    "failed": self.chaos_status.failed,
                    "survival_rate": self.chaos_status.survival_rate,
                    "results": self.chaos_status.results,
                },
                "cso": {
                    "bead_rate": self.bead_emission_rate,
                    "signal_rate": self.signal_generation_rate,
                },
                "bounds": {
                    "violations": self.bounds_violations,
                },
                "cascade": {
                    "samples": len(self.cascade_timing_histogram),
                    "avg_ms": sum(self.cascade_timing_histogram) / len(self.cascade_timing_histogram) if self.cascade_timing_histogram else 0,
                }
            }


# =============================================================================
# HTTP HANDLER
# =============================================================================

class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for dashboard."""
    
    metrics_store: MetricsStore = None
    
    def log_message(self, format: str, *args) -> None:
        # Suppress default logging
        pass
    
    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/health":
            self._serve_dashboard()
        elif self.path == "/api/metrics":
            self._serve_metrics_json()
        elif self.path == "/api/alerts":
            self._serve_alerts_json()
        else:
            self.send_error(404)
    
    def _serve_dashboard(self) -> None:
        """Serve HTML dashboard."""
        html = self._render_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(html))
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _serve_metrics_json(self) -> None:
        """Serve metrics as JSON."""
        if self.metrics_store:
            data = json.dumps(self.metrics_store.get_snapshot(), indent=2)
        else:
            data = json.dumps({"error": "No metrics store"})
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data.encode())
    
    def _serve_alerts_json(self) -> None:
        """Serve recent alerts as JSON."""
        from .alerts import get_alert_manager
        
        manager = get_alert_manager()
        alerts = [a.to_dict() for a in manager.get_recent_alerts(20)]
        stats = manager.get_stats()
        
        data = json.dumps({"alerts": alerts, "stats": stats}, indent=2)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data.encode())
    
    def _render_html(self) -> str:
        """Render dashboard HTML."""
        metrics = self.metrics_store.get_snapshot() if self.metrics_store else {}
        
        # Get alerts
        try:
            from .alerts import get_alert_manager
            manager = get_alert_manager()
            alerts = manager.get_recent_alerts(10)
            alert_stats = manager.get_stats()
        except:
            alerts = []
            alert_stats = {}
        
        halt = metrics.get("halt", {})
        river = metrics.get("river", {})
        chaos = metrics.get("chaos", {})
        workers = metrics.get("workers", [])
        cso = metrics.get("cso", {})
        bounds = metrics.get("bounds", {})
        
        # Status colors
        def status_color(health: str) -> str:
            return {
                "healthy": "#22c55e",
                "degraded": "#f59e0b",
                "critical": "#ef4444",
                "stale": "#f59e0b",
                "dead": "#ef4444",
            }.get(health, "#6b7280")
        
        halt_health = "healthy" if halt.get("slo_50ms", True) else "critical"
        river_health = river.get("health", "unknown")
        
        # Workers HTML
        workers_html = ""
        for w in workers:
            color = status_color(w.get("health", "unknown"))
            workers_html += f"""
            <div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid #333;">
                <span style="color:{color};">{w['id']}</span>
                <span>{w['staleness_seconds']:.1f}s ago</span>
                <span style="color:{color};">{w['health']}</span>
            </div>
            """
        
        if not workers_html:
            workers_html = "<div style='padding:8px;color:#6b7280;'>No workers registered</div>"
        
        # Alerts HTML
        alerts_html = ""
        for a in alerts[-5:]:
            level_color = "#ef4444" if a.level.value == "critical" else "#f59e0b"
            alerts_html += f"""
            <div style="display:flex;gap:10px;padding:8px;border-bottom:1px solid #333;">
                <span style="color:{level_color};font-weight:bold;">[{a.level.value.upper()}]</span>
                <span>{a.message[:50]}...</span>
            </div>
            """
        
        if not alerts_html:
            alerts_html = "<div style='padding:8px;color:#6b7280;'>No recent alerts</div>"
        
        # Chaos results HTML
        chaos_results_html = ""
        for vid, result in chaos.get("results", {}).items():
            color = "#22c55e" if result in ("pass", "detected") else "#ef4444"
            chaos_results_html += f"<span style='color:{color};'>{vid}: {result}</span><br>"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Phoenix Health Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #111;
            color: #fff;
            padding: 20px;
        }}
        h1 {{ color: #f97316; margin-bottom: 20px; }}
        h2 {{ color: #9ca3af; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ 
            background: #1f1f1f; 
            border-radius: 8px; 
            padding: 20px;
            border: 1px solid #333;
        }}
        .metric {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        .sub {{ color: #6b7280; font-size: 14px; }}
        .status {{ 
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .healthy {{ background: #166534; color: #22c55e; }}
        .degraded {{ background: #854d0e; color: #f59e0b; }}
        .critical {{ background: #991b1b; color: #ef4444; }}
    </style>
</head>
<body>
    <h1>Phoenix Health Dashboard</h1>
    <p class="sub">Last updated: {metrics.get('timestamp', 'N/A')} | Auto-refresh: 5s</p>
    
    <div class="grid" style="margin-top: 20px;">
        <!-- Halt Latency -->
        <div class="card">
            <h2>Halt Latency</h2>
            <div class="metric" style="color:{status_color(halt_health)};">
                {halt.get('p99_ms', 0):.2f}ms
            </div>
            <span class="status {halt_health}">{halt_health.upper()}</span>
            <div class="sub" style="margin-top: 10px;">
                Last: {halt.get('last_ms', 0):.2f}ms | Max: {halt.get('max_ms', 0):.2f}ms | Samples: {halt.get('samples', 0)}
            </div>
            <div class="sub">SLO: &lt;50ms | Status: {'PASS' if halt.get('slo_50ms', True) else 'FAIL'}</div>
        </div>
        
        <!-- River Quality -->
        <div class="card">
            <h2>River Quality</h2>
            <div class="metric" style="color:{status_color(river_health)};">
                {river.get('quality', 0)*100:.1f}%
            </div>
            <span class="status {river_health}">{river_health.upper()}</span>
            <div class="sub" style="margin-top: 10px;">
                Threshold: &gt;80% healthy | &gt;50% degraded
            </div>
        </div>
        
        <!-- Chaos Status -->
        <div class="card">
            <h2>Chaos Vectors</h2>
            <div class="metric" style="color:{'#22c55e' if chaos.get('survival_rate', 0) >= 90 else '#ef4444'};">
                {chaos.get('survival_rate', 0):.0f}%
            </div>
            <div class="sub">
                Pass: {chaos.get('passed', 0)} | Fail: {chaos.get('failed', 0)} | Total: {chaos.get('total', 0)}
            </div>
            <div class="sub" style="margin-top: 10px;">
                Last run: {chaos.get('last_run', 'Never')[:19] if chaos.get('last_run') else 'Never'}
            </div>
            <div style="margin-top: 10px; font-size: 12px;">
                {chaos_results_html or "No results"}
            </div>
        </div>
        
        <!-- CSO / Beads -->
        <div class="card">
            <h2>CSO Status</h2>
            <div class="metric">{cso.get('bead_rate', 0):.2f}</div>
            <div class="sub">beads/min</div>
            <div class="sub" style="margin-top: 10px;">
                Signal rate: {cso.get('signal_rate', 0):.2f}/min
            </div>
            <div class="sub">
                Bounds violations: {bounds.get('violations', 0)}
            </div>
        </div>
        
        <!-- Workers -->
        <div class="card">
            <h2>Workers ({len(workers)})</h2>
            <div style="max-height: 200px; overflow-y: auto;">
                {workers_html}
            </div>
        </div>
        
        <!-- Alerts -->
        <div class="card">
            <h2>Recent Alerts ({alert_stats.get('total_alerts', 0)} total, {alert_stats.get('suppressed_count', 0)} suppressed)</h2>
            <div style="max-height: 200px; overflow-y: auto;">
                {alerts_html}
            </div>
        </div>
    </div>
    
    <div style="margin-top: 20px; color: #6b7280; font-size: 12px;">
        Phoenix Monitoring v1.0 | S28.B | <a href="/api/metrics" style="color:#f97316;">JSON API</a> | <a href="/api/alerts" style="color:#f97316;">Alerts API</a>
    </div>
</body>
</html>
"""


# =============================================================================
# DASHBOARD SERVER
# =============================================================================

class HealthDashboard:
    """
    Health dashboard server.
    
    Usage:
        dashboard = HealthDashboard(port=8080)
        dashboard.start()  # Non-blocking
        
        # Update metrics
        dashboard.record_halt_latency(5.0)
        dashboard.update_river_quality(0.95)
        
        # Stop
        dashboard.stop()
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.metrics = MetricsStore()
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start dashboard server in background thread."""
        if self._server:
            return
        
        # Inject metrics store into handler
        DashboardHandler.metrics_store = self.metrics
        
        self._server = HTTPServer((self.host, self.port), DashboardHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        
        logger.info(f"Dashboard started at http://{self.host}:{self.port}")
    
    def stop(self) -> None:
        """Stop dashboard server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            self._thread = None
            logger.info("Dashboard stopped")
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    # Convenience methods to update metrics
    def record_halt_latency(self, latency_ms: float) -> None:
        self.metrics.record_halt_latency(latency_ms)
    
    def record_cascade_timing(self, timing_ms: float) -> None:
        self.metrics.record_cascade_timing(timing_ms)
    
    def update_river_quality(self, quality: float) -> None:
        self.metrics.update_river_quality(quality)
    
    def update_worker_heartbeat(self, worker_id: str, status: str = "alive", task_count: int = 0) -> None:
        self.metrics.update_worker_heartbeat(worker_id, status, task_count)
    
    def update_chaos_status(self, total: int, passed: int, failed: int, results: Dict[str, str]) -> None:
        self.metrics.update_chaos_status(total, passed, failed, results)
    
    def update_bead_rate(self, rate: float) -> None:
        self.metrics.update_bead_rate(rate)
    
    def increment_bounds_violation(self) -> None:
        self.metrics.increment_bounds_violation()


# =============================================================================
# CLI
# =============================================================================

def main():
    """Run dashboard from CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phoenix Health Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    dashboard = HealthDashboard(host=args.host, port=args.port)
    
    # Add some test data
    dashboard.record_halt_latency(5.0)
    dashboard.record_halt_latency(8.0)
    dashboard.record_halt_latency(3.0)
    dashboard.update_river_quality(0.92)
    dashboard.update_worker_heartbeat("worker-1", "alive", 10)
    dashboard.update_worker_heartbeat("worker-2", "alive", 5)
    dashboard.update_chaos_status(
        total=4,
        passed=3,
        failed=0,
        results={
            "V3-RIVER-001": "detected",
            "V3-RIVER-002": "pass",
            "V3-RIVER-003": "pass",
            "V3-CSO-001": "pass"
        }
    )
    
    print(f"Dashboard running at {dashboard.url}")
    print("Press Ctrl+C to stop")
    
    dashboard.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dashboard.stop()
        print("\nDashboard stopped")


if __name__ == "__main__":
    main()
