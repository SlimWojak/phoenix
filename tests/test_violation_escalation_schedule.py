#!/usr/bin/env python3
"""
TEST: VIOLATION ESCALATION SCHEDULE
SPRINT: 26.TRACK_B
EXIT_GATE: 12h CTO escalation, 24h Sovereign escalation

PURPOSE:
  Prove violation tickets have correct escalation schedule.
  Dead-man's switch enforcement.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    ViolationTicket,
    ViolationSeverity,
    ViolationStatus,
)


# =============================================================================
# TESTS
# =============================================================================

def test_violation_ticket_structure():
    """ViolationTicket has required fields."""
    now = datetime.now(timezone.utc)
    
    ticket = ViolationTicket(
        ticket_id="TEST001",
        invariant_id="INV-HALT-1",
        timestamp=now,
        severity=ViolationSeverity.CRITICAL,
        evidence={'latency_ms': 75}
    )
    
    print("\nViolationTicket Structure:")
    print(f"  ticket_id: {ticket.ticket_id}")
    print(f"  invariant_id: {ticket.invariant_id}")
    print(f"  timestamp: {ticket.timestamp}")
    print(f"  severity: {ticket.severity.value}")
    print(f"  status: {ticket.status.value}")
    print(f"  evidence: {ticket.evidence}")
    
    assert ticket.ticket_id == "TEST001"
    assert ticket.invariant_id == "INV-HALT-1"
    assert ticket.severity == ViolationSeverity.CRITICAL
    assert ticket.status == ViolationStatus.OPEN


def test_escalation_schedule_12h_24h():
    """Escalation times set correctly: CTO at +12h, Sovereign at +24h."""
    now = datetime.now(timezone.utc)
    
    ticket = ViolationTicket(
        ticket_id="ESC001",
        invariant_id="INV-GOV-1",
        timestamp=now,
        severity=ViolationSeverity.VIOLATION
    )
    
    expected_cto = now + timedelta(hours=12)
    expected_sovereign = now + timedelta(hours=24)
    
    print("\nEscalation Schedule:")
    print(f"  ticket_created: {now}")
    print(f"  escalate_cto_at: {ticket.auto_escalate_cto_at}")
    print(f"  escalate_sovereign_at: {ticket.auto_escalate_sovereign_at}")
    
    # Allow 1 second tolerance for timing
    assert abs((ticket.auto_escalate_cto_at - expected_cto).total_seconds()) < 1
    assert abs((ticket.auto_escalate_sovereign_at - expected_sovereign).total_seconds()) < 1


def test_severity_levels():
    """All severity levels work correctly."""
    now = datetime.now(timezone.utc)
    
    severities = [
        ViolationSeverity.WARNING,
        ViolationSeverity.VIOLATION,
        ViolationSeverity.CRITICAL,
    ]
    
    print("\nSeverity Levels:")
    for severity in severities:
        ticket = ViolationTicket(
            ticket_id=f"SEV_{severity.value}",
            invariant_id="INV-TEST",
            timestamp=now,
            severity=severity
        )
        print(f"  {severity.value}: escalation set ✓")
        
        # All severities should have escalation times
        assert ticket.auto_escalate_cto_at is not None
        assert ticket.auto_escalate_sovereign_at is not None


def test_status_transitions():
    """ViolationStatus values are correct."""
    statuses = [
        ViolationStatus.OPEN,
        ViolationStatus.ACKED,
        ViolationStatus.RESOLVED,
        ViolationStatus.WAIVED,
    ]
    
    print("\nStatus Values:")
    for status in statuses:
        print(f"  {status.value}")
    
    # Verify expected values
    assert ViolationStatus.OPEN.value == "OPEN"
    assert ViolationStatus.ACKED.value == "ACKED"
    assert ViolationStatus.RESOLVED.value == "RESOLVED"
    assert ViolationStatus.WAIVED.value == "WAIVED"


def test_dead_mans_switch_timing():
    """Dead-man's switch: 12h CTO, then 24h Sovereign."""
    now = datetime.now(timezone.utc)
    
    ticket = ViolationTicket(
        ticket_id="DEAD001",
        invariant_id="INV-GOV-2",
        timestamp=now,
        severity=ViolationSeverity.VIOLATION
    )
    
    # CTO escalation should be before Sovereign
    assert ticket.auto_escalate_cto_at < ticket.auto_escalate_sovereign_at
    
    # Gap should be 12 hours
    gap = ticket.auto_escalate_sovereign_at - ticket.auto_escalate_cto_at
    assert gap == timedelta(hours=12)
    
    print("\nDead-Man's Switch:")
    print(f"  CTO at: +12h")
    print(f"  Sovereign at: +24h")
    print(f"  Gap: {gap}")


def test_evidence_preserved():
    """Evidence dict is preserved in ticket."""
    now = datetime.now(timezone.utc)
    
    evidence = {
        'measured_latency_ms': 75.5,
        'threshold_ms': 50.0,
        'module_id': 'test_module',
        'stack_trace': 'line 42...'
    }
    
    ticket = ViolationTicket(
        ticket_id="EVID001",
        invariant_id="INV-HALT-1",
        timestamp=now,
        severity=ViolationSeverity.CRITICAL,
        evidence=evidence
    )
    
    print("\nEvidence Preservation:")
    for k, v in ticket.evidence.items():
        print(f"  {k}: {v}")
    
    assert ticket.evidence == evidence
    assert ticket.evidence['measured_latency_ms'] == 75.5


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("VIOLATION ESCALATION SCHEDULE TEST")
    print("=" * 60)
    print("Dead-Man's Switch: 12h → CTO, 24h → Sovereign")
    
    try:
        test_violation_ticket_structure()
        test_escalation_schedule_12h_24h()
        test_severity_levels()
        test_status_transitions()
        test_dead_mans_switch_timing()
        test_evidence_preserved()
        
        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print("  - Ticket structure correct")
        print("  - 12h CTO escalation set")
        print("  - 24h Sovereign escalation set")
        print("  - Evidence preserved")
        print("=" * 60)
        
        sys.exit(0)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
