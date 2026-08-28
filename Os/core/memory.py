"""
V.E.R.O.N.I.C.A. Memory & Event Audit Store
Maintains short-term conversational context and a persistent event audit log.
"""

from __future__ import annotations
import time
import json
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path


class MemoryStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path.home() / ".veronica" / "memory.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.session_messages: List[Dict[str, str]] = []

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    event_type TEXT,
                    details TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    role TEXT,
                    content TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_message(self, role: str, content: str):
        """Adds a message to the active session and persistent log."""
        self.session_messages.append({"role": role, "content": content})
        if len(self.session_messages) > 30:
            self.session_messages.pop(0)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversation_logs (timestamp, role, content) VALUES (?, ?, ?)",
                (time.time(), role, content)
            )
            conn.commit()
        finally:
            conn.close()

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Logs a critical system or contingency event."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO event_logs (timestamp, event_type, details) VALUES (?, ?, ?)",
                (time.time(), event_type, json.dumps(details))
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Returns the most recent conversation messages."""
        return self.session_messages[-limit:]

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent event audit logs."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, event_type, details FROM event_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "timestamp": r[0],
                    "event_type": r[1],
                    "details": json.loads(r[2]) if r[2] else {}
                }
                for r in rows
            ]
        finally:
            conn.close()
