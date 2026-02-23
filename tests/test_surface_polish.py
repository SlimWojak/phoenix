"""
Surface Polish Tests — S41 Phase 2E
===================================

Tests for human-readable narrator output.

EXIT GATES:
  - human_cadence: No raw IDs, hashes, or enums in default output
  - alert_format: All alerts ≤60 chars with emoji prefix
  - degraded_clean: All degraded states have human message
  - receipts_hidden: Provenance only shown when explicitly requested

GPT RED-LINES:
  RL1: No grade/count proxies (no "4/5 gates", "near ready")
  RL2: Every phrase maps 1:1 to gate predicate
  RL3: Alert one-liners keep essential facts
  RL4: No jargon in degraded messages
  RL5: Receipts hidden but logged
  RL6: Guard dog still effective

Date: 2026-01-30
Sprint: S41 Phase 2E
"""

import pytest
import re

from narrator import (
    NarratorRenderer,
    GATE_PHRASES,
    gates_to_phrases,
    format_gate_facts,
    DegradedState,
    DEGRADED_MESSAGES,
    get_degraded_message,
    format_alert_oneliner,
    format_health_status,
    format_receipts,
    format_circuit_status,
)
from notification.alert_taxonomy import (
    Alert,
    AlertCategory,
    AlertSeverity,
    TelegramAlertFormatter,
)


# =============================================================================
# TEST: HUMAN CADENCE (RL1, RL2)
# =============================================================================


class TestHumanCadence:
    """Tests for human-readable output without raw IDs."""

    def test_no_raw_gate_ids_in_output(self):
        """No raw gate IDs like [3,7,12] in formatted output."""
        gates = [3, 7, 12]
        result = format_gate_facts(gates)
        
        # Should NOT contain raw ID format
        assert "[3,7,12]" not in result
        assert "[3, 7, 12]" not in result
        assert "3,7,12" not in result
        
        # Should contain human phrases
        assert "HTF" in result or "gate" in result.lower()

    def test_gate_phrases_are_deterministic(self):
        """Each gate ID maps to exactly one phrase (RL2)."""
        # Verify consistency
        for _ in range(10):
            result1 = gates_to_phrases([1, 2, 3])
            result2 = gates_to_phrases([1, 2, 3])
            assert result1 == result2

    def test_no_fraction_patterns_default_output(self):
        """No X/Y fraction patterns in default output (RL1)."""
        # Pattern for fractions like "4/5", "3 / 7", etc.
        fraction_pattern = r"\b\d+\s*/\s*\d+\b"
        
        # Test circuit status (should NOT use fractions)
        result = format_circuit_status(4, 5)
        assert not re.search(fraction_pattern, result), f"Fraction found in: {result}"
        
        # Test gate facts (should NOT use fractions)
        result = format_gate_facts([1, 2, 3, 4])
        assert not re.search(fraction_pattern, result), f"Fraction found in: {result}"

    def test_no_readiness_language(self):
        """No readiness/grade proxy language (RL1)."""
        banned_phrases = [
            "near ready",
            "almost ready",
            "ready to",
            "setup live",
            "tradeable",
            "avoid",
        ]
        
        # Test gate facts
        result = format_gate_facts([1, 2, 3, 4, 5])
        result_lower = result.lower()
        
        for phrase in banned_phrases:
            assert phrase not in result_lower, f"Found banned phrase: {phrase}"

    def test_phrase_mapping_only(self):
        """Every phrase must come from gate_phrase_map (RL2)."""
        gates = [1, 3, 5, 7, 10]
        phrases = gates_to_phrases(gates)
        
        # All phrases should be in the mapping (or follow Gate X pattern)
        for phrase in phrases:
            is_valid = (
                phrase in GATE_PHRASES.values() or
                phrase.startswith("Gate ") and phrase.endswith(" passed")
            )
            assert is_valid, f"Phrase not from mapping: {phrase}"


# =============================================================================
# TEST: ALERT FORMAT (RL3)
# =============================================================================


class TestAlertFormat:
    """Tests for alert one-liner format."""

    def test_alert_one_liner_under_60_chars(self):
        """All alert one-liners ≤60 chars."""
        formatter = TelegramAlertFormatter()
        
        alerts = [
            Alert(
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.HALT,
                title="System Halted",
                message="Emergency",
                component="governance",
            ),
            Alert(
                severity=AlertSeverity.WARNING,
                category=AlertCategory.CIRCUIT_BREAKER,
                title="Circuit Open",
                message="Recovering",
                component="ibkr",
            ),
            Alert(
                severity=AlertSeverity.INFO,
                category=AlertCategory.SYSTEM,
                title="Session Start",
                message="London open",
                component="session",
            ),
        ]
        
        for alert in alerts:
            oneliner = formatter.format_oneliner(alert)
            assert len(oneliner) <= 60, f"Oneliner too long ({len(oneliner)}): {oneliner}"

    def test_alert_has_emoji_prefix(self):
        """All alerts have severity emoji prefix."""
        formatter = TelegramAlertFormatter()
        
        emoji_map = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.WARNING: "🟡",
            AlertSeverity.INFO: "🟢",
        }
        
        for severity, expected_emoji in emoji_map.items():
            alert = Alert(
                severity=severity,
                category=AlertCategory.SYSTEM,
                title="Test",
                message="Test",
            )
            oneliner = formatter.format_oneliner(alert)
            assert oneliner.startswith(expected_emoji), f"Wrong emoji for {severity}"

    def test_alert_has_component(self):
        """Alert one-liner includes component (RL3)."""
        formatter = TelegramAlertFormatter()
        
        alert = Alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.IBKR_CONNECTION,
            title="Disconnected",
            message="Lost connection",
            component="IBKR",
        )
        
        oneliner = formatter.format_oneliner(alert)
        assert "IBKR" in oneliner

    def test_alert_truncates_gracefully(self):
        """Long alerts truncate with ... (not break)."""
        formatter = TelegramAlertFormatter()
        
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.HALT,
            title="This is a very long title that should definitely exceed sixty characters",
            message="Long message",
            component="test",
        )
        
        oneliner = formatter.format_oneliner(alert)
        assert len(oneliner) <= 60
        # Should end with ... if truncated
        if "..." in oneliner:
            assert oneliner.endswith("...")


# =============================================================================
# TEST: DEGRADED MESSAGES (RL4)
# =============================================================================


class TestDegradedMessages:
    """Tests for degraded state messages."""

    def test_all_states_have_messages(self):
        """All degraded states have human messages."""
        for state in DegradedState:
            assert state in DEGRADED_MESSAGES, f"Missing message for {state}"
            message = DEGRADED_MESSAGES[state]
            assert len(message) > 0, f"Empty message for {state}"

    def test_no_jargon_in_messages(self):
        """No technical jargon in degraded messages (RL4)."""
        banned_terms = [
            "provenance",
            "bead",
            "enum",
            "hash",
            "exception",
            "traceback",
            "stacktrace",
        ]
        
        for state, message in DEGRADED_MESSAGES.items():
            message_lower = message.lower()
            for term in banned_terms:
                assert term not in message_lower, f"Jargon '{term}' in {state}: {message}"

    def test_messages_are_actionable(self):
        """Degraded messages give actionable info."""
        # Check messages have clear structure
        for state, message in DEGRADED_MESSAGES.items():
            # Should have subject — action format or similar
            assert len(message) >= 10, f"Message too short for {state}"

    def test_get_degraded_message_with_params(self):
        """get_degraded_message substitutes parameters."""
        msg = get_degraded_message(DegradedState.STALE_DATA, minutes=5)
        assert "5m" in msg or "5" in msg
        
        msg = get_degraded_message(DegradedState.CIRCUIT_OPEN, component="IBKR")
        assert "IBKR" in msg
        
        msg = get_degraded_message(DegradedState.HERESY_BLOCKED, category="CAUSAL")
        assert "CAUSAL" in msg


# =============================================================================
# TEST: RECEIPTS HIDDEN (RL5)
# =============================================================================


class TestReceiptsHidden:
    """Tests for receipts hiding behavior."""

    def test_receipts_hidden_by_default(self):
        """Receipts not shown by default."""
        renderer = NarratorRenderer()
        
        trade = {
            "action": "ENTRY",
            "pair": "EURUSD",
            "direction": "LONG",
            "entry": "1.0850",
            "stop": "1.0800",
            "target": "1.0950",
            "risk_pct": 1.0,
            "gates_passed": [1, 3, 7],
            "evidence_bead": "abc123xyz",
            "show_receipts": False,
        }
        
        result = renderer.render_trade(trade, show_receipts=False)
        
        # Should NOT contain receipts section or bead ID
        assert "abc123xyz" not in result
        assert "RECEIPTS" not in result

    def test_receipts_shown_when_requested(self):
        """Receipts shown when show_receipts=True."""
        renderer = NarratorRenderer()
        
        trade = {
            "action": "ENTRY",
            "pair": "EURUSD",
            "direction": "LONG",
            "entry": "1.0850",
            "stop": "1.0800",
            "target": "1.0950",
            "risk_pct": 1.0,
            "gates_passed": [1, 3, 7],
            "evidence_bead": "abc123xyz",
        }
        
        result = renderer.render_trade(trade, show_receipts=True)
        
        # Should contain receipts
        assert "abc123xyz" in result or "RECEIPTS" in result

    def test_format_receipts_helper(self):
        """format_receipts produces correct format."""
        result = format_receipts(
            bead_id="bead_123",
            query_hash="hash_456",
            provenance="source_789",
        )
        
        assert "RECEIPTS" in result
        assert "bead_123" in result
        assert "hash_456" in result
        assert "source_789" in result

    def test_format_receipts_empty_when_no_data(self):
        """format_receipts returns empty when no data."""
        result = format_receipts()
        assert result == ""


# =============================================================================
# TEST: CIRCUIT STATUS (RL1)
# =============================================================================


class TestCircuitStatus:
    """Tests for circuit breaker formatting."""

    def test_circuit_status_no_fractions(self):
        """Circuit status uses words, not fractions."""
        # All closed
        assert format_circuit_status(5, 5) == "All circuits closed"
        
        # All open
        assert format_circuit_status(0, 5) == "All circuits OPEN"
        
        # Partial (should NOT say "3/5")
        result = format_circuit_status(3, 5)
        assert "3/5" not in result
        assert "/" not in result
        assert "2 circuit" in result  # 2 open

    def test_circuit_status_indicates_open_count(self):
        """Circuit status tells how many are open."""
        result = format_circuit_status(3, 5)
        assert "2" in result
        assert "OPEN" in result


# =============================================================================
# TEST: HEALTH STATUS
# =============================================================================


class TestHealthStatus:
    """Tests for health status formatting."""

    def test_health_status_has_emoji(self):
        """Health status includes appropriate emoji."""
        assert "🟢" in format_health_status("HEALTHY")
        assert "🟡" in format_health_status("DEGRADED")
        assert "🔴" in format_health_status("CRITICAL")
        assert "🛑" in format_health_status("HALTED")

    def test_health_status_with_detail(self):
        """Health status can include detail."""
        result = format_health_status("DEGRADED", "IBKR reconnecting")
        assert "🟡" in result
        assert "DEGRADED" in result
        assert "IBKR reconnecting" in result


# =============================================================================
# TEST: REGRESSION — GUARD DOG STILL EFFECTIVE (RL6)
# =============================================================================


class TestGuardDogEffective:
    """Verify guard dog still catches heresy after surface polish."""

    def test_rendered_briefing_passes_guard(self):
        """Rendered briefing passes through guard dog."""
        renderer = NarratorRenderer()
        result = renderer.render_briefing()
        
        # Should contain banner
        assert "FACTS_ONLY" in result

    def test_rendered_health_passes_guard(self):
        """Rendered health passes through guard dog."""
        renderer = NarratorRenderer()
        result = renderer.render_health()
        
        assert "FACTS_ONLY" in result

    def test_gate_facts_no_banned_words(self):
        """Gate facts output has no banned words."""
        from governance.slm_boundary import ContentClassifier
        
        classifier = ContentClassifier()
        gates = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        facts = format_gate_facts(gates)
        
        # Wrap in banner for classifier
        content = f"FACTS_ONLY — NO INTERPRETATION\n\n{facts}"
        result = classifier.classify(content)
        
        from governance.slm_boundary import SLMClassification
        assert result.classification == SLMClassification.VALID_FACTS, \
            f"Gate facts triggered heresy: {result.reason_code}"
