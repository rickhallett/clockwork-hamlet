#!/usr/bin/env python3
"""
Agent Coordination Module

Provides a Python API for agents to coordinate work via the shared SQLite database.
This module handles all database interactions with proper locking and error handling.

Usage:
    from agent_coordination import AgentCoordinator

    coord = AgentCoordinator()  # Auto-detects from .coordination.env
    coord.claim_track("track-a", "FEED-8", "Implementing CSV export")
    coord.update_status("working")
    coord.send_message("track-b", "info", "I'm modifying events.py")
    messages = coord.get_messages()
    coord.complete_track()
"""

import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class AgentInfo:
    """Information about a registered agent/track."""
    track: str
    worktree_path: str
    branch: str
    ticket_id: Optional[str]
    status: str
    current_task: Optional[str]
    started_at: Optional[datetime]
    updated_at: datetime
    agent_pid: Optional[int]


@dataclass
class Message:
    """A coordination message between agents."""
    id: int
    from_track: str
    to_track: Optional[str]
    message_type: str
    content: str
    acknowledged: bool
    created_at: datetime


class AgentCoordinator:
    """
    Coordinates multiple Claude Code agents working in parallel via SQLite.

    The database uses WAL mode for better concurrent access:
    - Multiple readers can work simultaneously
    - Writes are serialized but fast
    - No corruption from concurrent access
    """

    def __init__(self, db_path: Optional[str] = None, track_name: Optional[str] = None):
        """
        Initialize the coordinator.

        Args:
            db_path: Path to coordination database. If None, reads from .coordination.env
            track_name: This agent's track name. If None, reads from .coordination.env
        """
        # Try to load from environment/config file
        if db_path is None or track_name is None:
            config = self._load_config()
            db_path = db_path or config.get("COORDINATION_DB")
            track_name = track_name or config.get("TRACK_NAME")

        if not db_path:
            raise ValueError("No coordination database path specified")

        self.db_path = Path(db_path)
        self.track_name = track_name
        self._ensure_db_exists()

    def _load_config(self) -> dict:
        """Load configuration from .coordination.env file."""
        config = {}

        # Check current directory and parents for .coordination.env
        search_path = Path.cwd()
        for _ in range(5):  # Search up to 5 levels
            config_file = search_path / ".coordination.env"
            if config_file.exists():
                with open(config_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            config[key.strip()] = value.strip()
                break
            search_path = search_path.parent

        # Also check environment variables
        for key in ["COORDINATION_DB", "TRACK_NAME"]:
            if key in os.environ:
                config[key] = os.environ[key]

        return config

    def _ensure_db_exists(self):
        """Ensure the database exists and has the correct schema."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Coordination database not found: {self.db_path}")

    @contextmanager
    def _get_connection(self, timeout: float = 30.0):
        """Get a database connection with WAL mode and proper timeout."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=timeout,
            isolation_level=None  # Autocommit mode for better concurrency
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ==================== Track/Agent Management ====================

    def claim_track(self, track: Optional[str] = None, ticket_id: str = None,
                    task_description: str = None) -> bool:
        """
        Claim a track for this agent to work on.

        Args:
            track: Track name (defaults to self.track_name)
            ticket_id: The ticket being worked on (e.g., "FEED-8")
            task_description: Human-readable task description

        Returns:
            True if successfully claimed, False if already claimed by another
        """
        track = track or self.track_name
        if not track:
            raise ValueError("No track name specified")

        with self._get_connection() as conn:
            # Check if track exists and is not already being worked
            cursor = conn.execute(
                "SELECT status, agent_pid FROM agents WHERE track = ?",
                (track,)
            )
            row = cursor.fetchone()

            if row and row["status"] == "working":
                # Check if the PID is still alive
                pid = row["agent_pid"]
                if pid and self._is_pid_alive(pid):
                    return False  # Already claimed by live process

            # Claim the track
            conn.execute("""
                UPDATE agents SET
                    status = 'working',
                    ticket_id = ?,
                    current_task = ?,
                    started_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    agent_pid = ?
                WHERE track = ?
            """, (ticket_id, task_description, os.getpid(), track))

            return True

    def update_status(self, status: str, task_description: str = None):
        """
        Update this agent's status.

        Args:
            status: One of 'idle', 'working', 'blocked', 'review', 'done'
            task_description: Optional task description update
        """
        if not self.track_name:
            raise ValueError("No track name configured")

        with self._get_connection() as conn:
            if task_description:
                conn.execute("""
                    UPDATE agents SET
                        status = ?,
                        current_task = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE track = ?
                """, (status, task_description, self.track_name))
            else:
                conn.execute("""
                    UPDATE agents SET
                        status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE track = ?
                """, (status, self.track_name))

    def complete_track(self):
        """Mark this track as complete and release it."""
        self.update_status("done")

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE agents SET
                    agent_pid = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE track = ?
            """, (self.track_name,))

    def release_track(self):
        """Release this track without completing (e.g., for handoff)."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE agents SET
                    status = 'idle',
                    agent_pid = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE track = ?
            """, (self.track_name,))

    def get_all_agents(self) -> list[AgentInfo]:
        """Get information about all registered agents."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agents ORDER BY track")
            return [self._row_to_agent(row) for row in cursor.fetchall()]

    def get_active_agents(self) -> list[AgentInfo]:
        """Get all agents currently working."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM agents WHERE status = 'working' ORDER BY track"
            )
            return [self._row_to_agent(row) for row in cursor.fetchall()]

    # ==================== Messaging ====================

    def send_message(self, to_track: Optional[str], message_type: str, content: str):
        """
        Send a message to another agent or broadcast.

        Args:
            to_track: Target track name, or None for broadcast
            message_type: One of 'info', 'warning', 'blocker', 'question', 'done'
            content: Message content
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO messages (from_track, to_track, message_type, content)
                VALUES (?, ?, ?, ?)
            """, (self.track_name, to_track, message_type, content))

    def broadcast(self, message_type: str, content: str):
        """Send a message to all agents."""
        self.send_message(None, message_type, content)

    def get_messages(self, include_acknowledged: bool = False) -> list[Message]:
        """
        Get messages for this agent.

        Args:
            include_acknowledged: Whether to include already-acknowledged messages
        """
        with self._get_connection() as conn:
            if include_acknowledged:
                cursor = conn.execute("""
                    SELECT * FROM messages
                    WHERE to_track = ? OR to_track IS NULL
                    ORDER BY created_at DESC
                """, (self.track_name,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM messages
                    WHERE (to_track = ? OR to_track IS NULL) AND acknowledged = 0
                    ORDER BY created_at DESC
                """, (self.track_name,))

            return [self._row_to_message(row) for row in cursor.fetchall()]

    def acknowledge_message(self, message_id: int):
        """Mark a message as acknowledged."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE messages SET acknowledged = 1 WHERE id = ?",
                (message_id,)
            )

    def acknowledge_all_messages(self):
        """Mark all messages for this track as acknowledged."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE messages SET acknowledged = 1
                WHERE to_track = ? OR to_track IS NULL
            """, (self.track_name,))

    # ==================== File Locking ====================

    def lock_file(self, file_path: str, reason: str = None) -> bool:
        """
        Attempt to lock a file for exclusive modification.

        Args:
            file_path: Relative path to the file
            reason: Why the file is being locked

        Returns:
            True if lock acquired, False if already locked
        """
        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO file_locks (file_path, locked_by, reason)
                    VALUES (?, ?, ?)
                """, (file_path, self.track_name, reason))
                return True
            except sqlite3.IntegrityError:
                # Already locked
                return False

    def unlock_file(self, file_path: str):
        """Release a file lock."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM file_locks WHERE file_path = ? AND locked_by = ?",
                (file_path, self.track_name)
            )

    def get_file_lock(self, file_path: str) -> Optional[tuple[str, str]]:
        """
        Check if a file is locked.

        Returns:
            Tuple of (locked_by, reason) if locked, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT locked_by, reason FROM file_locks WHERE file_path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            if row:
                return (row["locked_by"], row["reason"])
            return None

    def get_all_locks(self) -> list[tuple[str, str, str]]:
        """Get all current file locks."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT file_path, locked_by, reason FROM file_locks")
            return [(row["file_path"], row["locked_by"], row["reason"])
                    for row in cursor.fetchall()]

    def release_all_my_locks(self):
        """Release all file locks held by this track."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM file_locks WHERE locked_by = ?",
                (self.track_name,)
            )

    # ==================== Utilities ====================

    def _is_pid_alive(self, pid: int) -> bool:
        """Check if a process is still running."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _row_to_agent(self, row) -> AgentInfo:
        """Convert a database row to AgentInfo."""
        return AgentInfo(
            track=row["track"],
            worktree_path=row["worktree_path"],
            branch=row["branch"],
            ticket_id=row["ticket_id"],
            status=row["status"],
            current_task=row["current_task"],
            started_at=self._parse_datetime(row["started_at"]),
            updated_at=self._parse_datetime(row["updated_at"]),
            agent_pid=row["agent_pid"]
        )

    def _row_to_message(self, row) -> Message:
        """Convert a database row to Message."""
        return Message(
            id=row["id"],
            from_track=row["from_track"],
            to_track=row["to_track"],
            message_type=row["message_type"],
            content=row["content"],
            acknowledged=bool(row["acknowledged"]),
            created_at=self._parse_datetime(row["created_at"])
        )

    def _parse_datetime(self, value) -> Optional[datetime]:
        """Parse a datetime string from SQLite."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None


# ==================== CLI Interface ====================

def main():
    """CLI interface for coordination commands."""
    import argparse

    parser = argparse.ArgumentParser(description="Agent coordination CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status command
    status_parser = subparsers.add_parser("status", help="Show all agents status")

    # claim command
    claim_parser = subparsers.add_parser("claim", help="Claim a track")
    claim_parser.add_argument("ticket", help="Ticket ID")
    claim_parser.add_argument("--task", help="Task description")

    # release command
    release_parser = subparsers.add_parser("release", help="Release current track")

    # message command
    msg_parser = subparsers.add_parser("msg", help="Send a message")
    msg_parser.add_argument("--to", help="Target track (omit for broadcast)")
    msg_parser.add_argument("--type", default="info",
                           choices=["info", "warning", "blocker", "question", "done"])
    msg_parser.add_argument("content", help="Message content")

    # inbox command
    inbox_parser = subparsers.add_parser("inbox", help="Check messages")
    inbox_parser.add_argument("--all", action="store_true", help="Include acknowledged")

    # locks command
    locks_parser = subparsers.add_parser("locks", help="Show file locks")

    args = parser.parse_args()

    try:
        coord = AgentCoordinator()
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        print("Make sure you're in a worktree with .coordination.env")
        return 1

    if args.command == "status":
        agents = coord.get_all_agents()
        if not agents:
            print("No agents registered")
        else:
            print(f"{'Track':<20} {'Status':<10} {'Ticket':<12} {'Task'}")
            print("-" * 70)
            for agent in agents:
                task = (agent.current_task or "")[:30]
                print(f"{agent.track:<20} {agent.status:<10} {agent.ticket_id or '':<12} {task}")

    elif args.command == "claim":
        if coord.claim_track(ticket_id=args.ticket, task_description=args.task):
            print(f"Claimed track for {args.ticket}")
        else:
            print("Track already claimed by another agent")
            return 1

    elif args.command == "release":
        coord.release_track()
        print("Track released")

    elif args.command == "msg":
        coord.send_message(args.to, args.type, args.content)
        print(f"Message sent ({args.type})")

    elif args.command == "inbox":
        messages = coord.get_messages(include_acknowledged=args.all)
        if not messages:
            print("No messages")
        else:
            for msg in messages:
                status = "" if msg.acknowledged else "[NEW] "
                print(f"{status}[{msg.message_type}] from {msg.from_track}: {msg.content}")

    elif args.command == "locks":
        locks = coord.get_all_locks()
        if not locks:
            print("No file locks")
        else:
            for path, owner, reason in locks:
                print(f"{path} - locked by {owner}" + (f" ({reason})" if reason else ""))

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
