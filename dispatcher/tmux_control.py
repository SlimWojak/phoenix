"""
TMUX Control — Command & Control via tmux sessions.

SPRINT: 26.TRACK_D
VERSION: 1.0

Provides tmux session management for worker processes.
"""

import subprocess
import shlex
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path

from .types import SessionId, SessionInfo, CommandResult

logger = logging.getLogger(__name__)


# =============================================================================
# TMUX CONTROLLER
# =============================================================================

class TmuxController:
    """
    TMUX session management for Phoenix workers.
    
    Creates, monitors, and controls tmux sessions for worker processes.
    """
    
    def __init__(self, session_prefix: str = "phoenix"):
        self.session_prefix = session_prefix
        self._verify_tmux()
    
    def _verify_tmux(self) -> None:
        """Verify tmux is available."""
        try:
            result = subprocess.run(
                ["tmux", "-V"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("tmux not available")
            logger.debug(f"tmux version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError("tmux not installed")
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def create_session(
        self,
        name: str,
        command: Optional[str] = None,
        working_dir: Optional[str] = None
    ) -> SessionId:
        """
        Create a new tmux session.
        
        Args:
            name: Session name (prefixed with session_prefix)
            command: Initial command to run
            working_dir: Working directory for session
            
        Returns:
            SessionId of created session
        """
        session_name = f"{self.session_prefix}-{name}"
        
        # Build tmux command
        cmd = ["tmux", "new-session", "-d", "-s", session_name]
        
        if working_dir:
            cmd.extend(["-c", working_dir])
        
        if command:
            cmd.append(command)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # Check if session already exists
                if "duplicate session" in result.stderr:
                    logger.warning(f"Session {session_name} already exists")
                    return SessionId(session_name)
                raise RuntimeError(f"Failed to create session: {result.stderr}")
            
            logger.info(f"Created tmux session: {session_name}")
            return SessionId(session_name)
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("tmux session creation timed out")
    
    def kill_session(self, session_id: SessionId) -> bool:
        """
        Kill a tmux session.
        
        Args:
            session_id: Session to kill
            
        Returns:
            True if killed successfully
        """
        try:
            result = subprocess.run(
                ["tmux", "kill-session", "-t", str(session_id)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"Killed tmux session: {session_id}")
                return True
            else:
                # Session may not exist
                if "no server running" in result.stderr or "session not found" in result.stderr:
                    logger.warning(f"Session {session_id} not found")
                    return True  # Consider it killed
                logger.error(f"Failed to kill session: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout killing session: {session_id}")
            return False
    
    def session_exists(self, session_id: SessionId) -> bool:
        """Check if session exists."""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", str(session_id)],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    # =========================================================================
    # COMMAND EXECUTION
    # =========================================================================
    
    def send_command(
        self,
        session_id: SessionId,
        command: str,
        enter: bool = True
    ) -> CommandResult:
        """
        Send command to a tmux session.
        
        Args:
            session_id: Target session
            command: Command to send
            enter: Whether to send Enter key after command
            
        Returns:
            CommandResult
        """
        try:
            # Use send-keys to send the command
            cmd = ["tmux", "send-keys", "-t", str(session_id), command]
            if enter:
                cmd.append("Enter")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            success = result.returncode == 0
            
            return CommandResult(
                success=success,
                session_id=session_id,
                command=command,
                error=result.stderr if not success else None
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                session_id=session_id,
                command=command,
                error="Command send timed out"
            )
    
    def send_signal(
        self,
        session_id: SessionId,
        signal: str = "SIGTERM"
    ) -> bool:
        """
        Send signal to process in session.
        
        Args:
            session_id: Target session
            signal: Signal name (SIGTERM, SIGKILL, etc.)
            
        Returns:
            True if signal sent
        """
        # Send Ctrl-C first, then kill command
        cmd_result = self.send_command(
            session_id,
            f"kill -{signal} $$",
            enter=True
        )
        return cmd_result.success
    
    def send_interrupt(self, session_id: SessionId) -> bool:
        """Send Ctrl-C to session."""
        try:
            result = subprocess.run(
                ["tmux", "send-keys", "-t", str(session_id), "C-c"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    # =========================================================================
    # OUTPUT CAPTURE
    # =========================================================================
    
    def get_session_output(
        self,
        session_id: SessionId,
        lines: int = 100
    ) -> Optional[str]:
        """
        Get recent output from session.
        
        Args:
            session_id: Target session
            lines: Number of lines to capture
            
        Returns:
            Output string or None
        """
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", str(session_id), "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout
            return None
            
        except:
            return None
    
    # =========================================================================
    # LISTING
    # =========================================================================
    
    def list_sessions(self) -> List[SessionInfo]:
        """
        List all Phoenix-prefixed tmux sessions.
        
        Returns:
            List of SessionInfo
        """
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}|#{session_windows}|#{session_created}|#{session_attached}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                if "no server running" in result.stderr:
                    return []
                return []
            
            sessions = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 4:
                    name = parts[0]
                    # Filter to our prefix
                    if name.startswith(self.session_prefix):
                        sessions.append(SessionInfo(
                            session_id=SessionId(name),
                            session_name=name,
                            window_count=int(parts[1]) if parts[1].isdigit() else 1,
                            created_at=datetime.fromtimestamp(int(parts[2]), tz=timezone.utc) if parts[2].isdigit() else None,
                            attached=parts[3] == "1"
                        ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def cleanup_orphans(self) -> int:
        """
        Kill all Phoenix-prefixed sessions.
        
        Returns:
            Number of sessions killed
        """
        sessions = self.list_sessions()
        killed = 0
        
        for session in sessions:
            if self.kill_session(session.session_id):
                killed += 1
        
        return killed
    
    # =========================================================================
    # HALT MECHANISM
    # =========================================================================
    
    def broadcast_halt_signal(self, halt_command: str = "HALT") -> int:
        """
        Broadcast halt signal to all Phoenix sessions.
        
        Sends a special command that workers should recognize.
        
        Args:
            halt_command: Command string to send
            
        Returns:
            Number of sessions signaled
        """
        sessions = self.list_sessions()
        signaled = 0
        
        for session in sessions:
            result = self.send_command(session.session_id, halt_command)
            if result.success:
                signaled += 1
        
        logger.info(f"Broadcast halt to {signaled}/{len(sessions)} sessions")
        return signaled
