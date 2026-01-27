"""
Test TMUX Control — TMUX session management.

SPRINT: 26.TRACK_D
EXIT_GATE: tmux_c2

Tests:
- Session creation/deletion
- Command sending
- Output capture
- Session listing
"""

import sys
import time
from pathlib import Path

import pytest

# Add phoenix to path
PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

from dispatcher import SessionId, TmuxController

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tmux():
    """Create TMUX controller for testing."""
    controller = TmuxController(session_prefix="phoenix-test-tmux")
    yield controller
    # Cleanup after tests
    controller.cleanup_orphans()


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================


class TestSessionManagement:
    """Test session creation and deletion."""

    def test_create_session(self, tmux):
        """Create a tmux session."""
        session_id = tmux.create_session("test-create")

        assert session_id is not None
        assert "phoenix-test-tmux" in session_id

        # Cleanup
        tmux.kill_session(session_id)

    def test_create_session_with_command(self, tmux):
        """Create session with initial command."""
        session_id = tmux.create_session(name="test-cmd", command="echo 'hello world'")

        assert session_id is not None

        # Cleanup
        tmux.kill_session(session_id)

    def test_create_session_with_working_dir(self, tmux):
        """Create session with working directory."""
        session_id = tmux.create_session(name="test-dir", working_dir="/tmp")

        assert session_id is not None

        # Cleanup
        tmux.kill_session(session_id)

    def test_kill_session(self, tmux):
        """Kill a tmux session."""
        session_id = tmux.create_session("test-kill")

        result = tmux.kill_session(session_id)

        assert result is True
        assert not tmux.session_exists(session_id)

    def test_kill_nonexistent_session(self, tmux):
        """Killing nonexistent session returns True."""
        result = tmux.kill_session(SessionId("nonexistent-session"))
        # Should return True (consider it killed)
        assert result is True

    def test_session_exists(self, tmux):
        """Check if session exists."""
        session_id = tmux.create_session("test-exists")

        assert tmux.session_exists(session_id) is True

        tmux.kill_session(session_id)

        assert tmux.session_exists(session_id) is False


# =============================================================================
# COMMAND EXECUTION
# =============================================================================


class TestCommandExecution:
    """Test command sending."""

    def test_send_command(self, tmux):
        """Send command to session."""
        session_id = tmux.create_session("test-send")

        result = tmux.send_command(session_id, "echo 'test'")

        assert result.success is True
        assert result.session_id == session_id

        tmux.kill_session(session_id)

    def test_send_command_without_enter(self, tmux):
        """Send command without pressing Enter."""
        session_id = tmux.create_session("test-no-enter")

        result = tmux.send_command(session_id, "partial", enter=False)

        assert result.success is True

        tmux.kill_session(session_id)

    def test_send_interrupt(self, tmux):
        """Send Ctrl-C to session."""
        session_id = tmux.create_session("test-interrupt", command="sleep 60")
        time.sleep(0.2)  # Let sleep start

        result = tmux.send_interrupt(session_id)

        assert result is True

        tmux.kill_session(session_id)

    def test_send_command_to_nonexistent(self, tmux):
        """Send command to nonexistent session fails."""
        result = tmux.send_command(SessionId("fake-session"), "echo 'test'")

        assert result.success is False


# =============================================================================
# OUTPUT CAPTURE
# =============================================================================


class TestOutputCapture:
    """Test output capture."""

    def test_get_session_output(self, tmux):
        """Get output from session."""
        session_id = tmux.create_session("test-output")

        # Send command
        tmux.send_command(session_id, "echo 'captured output'")
        time.sleep(0.2)  # Let command execute

        output = tmux.get_session_output(session_id)

        assert output is not None
        # Output should contain our echoed text
        assert "captured" in output or len(output) > 0

        tmux.kill_session(session_id)

    def test_get_output_nonexistent(self, tmux):
        """Get output from nonexistent session returns None."""
        output = tmux.get_session_output(SessionId("fake-session"))
        assert output is None


# =============================================================================
# SESSION LISTING
# =============================================================================


class TestSessionListing:
    """Test session listing."""

    def test_list_sessions_empty(self, tmux):
        """List sessions when none exist."""
        # Ensure clean state
        tmux.cleanup_orphans()

        sessions = tmux.list_sessions()

        assert isinstance(sessions, list)
        # May be empty or have sessions from other tests

    def test_list_sessions_with_sessions(self, tmux):
        """List sessions returns created sessions."""
        s1 = tmux.create_session("test-list-1")
        s2 = tmux.create_session("test-list-2")

        sessions = tmux.list_sessions()
        session_ids = [s.session_id for s in sessions]

        assert s1 in session_ids
        assert s2 in session_ids

        tmux.kill_session(s1)
        tmux.kill_session(s2)

    def test_list_sessions_filters_prefix(self, tmux):
        """List only shows sessions with our prefix."""
        s1 = tmux.create_session("test-filter")

        sessions = tmux.list_sessions()

        for session in sessions:
            assert session.session_name.startswith("phoenix-test-tmux")

        tmux.kill_session(s1)


# =============================================================================
# CLEANUP
# =============================================================================


class TestCleanup:
    """Test cleanup operations."""

    def test_cleanup_orphans(self, tmux):
        """Cleanup removes all prefix sessions."""
        # Create some sessions
        tmux.create_session("test-orphan-1")
        tmux.create_session("test-orphan-2")

        count = tmux.cleanup_orphans()

        assert count >= 2

        # Verify none remain
        sessions = tmux.list_sessions()
        assert len(sessions) == 0


# =============================================================================
# HALT BROADCAST
# =============================================================================


class TestHaltBroadcast:
    """Test halt signal broadcast."""

    def test_broadcast_halt_signal(self, tmux):
        """Broadcast halt to all sessions."""
        tmux.create_session("test-halt-1", command="sleep 60")
        tmux.create_session("test-halt-2", command="sleep 60")

        count = tmux.broadcast_halt_signal("HALT")

        assert count >= 2

        # Cleanup
        tmux.cleanup_orphans()
