"""
Active interrupt design test (S55 Track 5, part 2).

Design: halt_interrupt(pids) → SIGTERM, 2s grace → SIGKILL.
Status: DESIGNED AND TESTED, NOT wired into daemon loop.
Daemon wiring is a future sprint when execution daemon runs on M3.
"""

import signal
import subprocess
import sys
import time


def halt_interrupt(execution_pids: list[int], grace_seconds: float = 2.0) -> dict[int, str]:
    """
    Send SIGTERM to execution processes, escalate to SIGKILL after grace period.

    Returns dict of pid -> outcome ("terminated", "killed", "not_found").
    NOT wired into daemon loop — design + test only.
    """
    import os

    results: dict[int, str] = {}

    for pid in execution_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            results[pid] = "not_found"
            continue
        except PermissionError:
            results[pid] = "permission_denied"
            continue

    if not execution_pids:
        return results

    time.sleep(grace_seconds)

    for pid in execution_pids:
        if pid in results:
            continue
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
            results[pid] = "killed"
        except ProcessLookupError:
            results[pid] = "terminated"
        except PermissionError:
            results[pid] = "permission_denied"

    return results


def test_halt_interrupt_terminates_process() -> None:
    """halt_interrupt sends SIGTERM → process exits within grace period."""
    proc = subprocess.Popen(  # noqa: S603
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pid = proc.pid

    results = halt_interrupt([pid], grace_seconds=2.0)

    assert pid in results
    assert results[pid] in ("terminated", "killed")
    proc.wait(timeout=5)


def test_halt_interrupt_nonexistent_pid() -> None:
    """halt_interrupt handles nonexistent PID gracefully."""
    results = halt_interrupt([999999999])
    assert 999999999 in results
    assert results[999999999] == "not_found"


def test_halt_interrupt_empty_list() -> None:
    """halt_interrupt with empty list returns empty dict."""
    results = halt_interrupt([])
    assert results == {}
