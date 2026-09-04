"""Buffered local telemetry for player interaction and game behavior.

Events stay in memory during a match round and are written as one aggregate
record when that round ends. The aggregate contains counts and choices, not
raw chat text.
"""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any, Dict


TELEMETRY_PATH = Path("round_telemetry.jsonl")


class RoundTelemetry:
    """Collect lightweight interaction data and flush it per match round."""

    def __init__(self, path: Path = TELEMETRY_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def start_session(self, session_id: str, player_id: str) -> None:
        """Start or reset the local buffer for a player session."""
        with self._lock:
            self._sessions[session_id] = {
                "player_id": player_id,
                "events": Counter(),
                "actions": Counter(),
                "chat_lengths": [],
            }

    def record(
        self,
        session_id: str,
        event: str,
        *,
        action: str = "",
        chat_length: int | None = None,
    ) -> None:
        """Record an interaction without writing to disk."""
        with self._lock:
            buffer = self._sessions.get(session_id)
            if not buffer:
                return
            buffer["events"][event] += 1
            if action:
                buffer["actions"][action] += 1
            if chat_length is not None:
                buffer["chat_lengths"].append(max(0, chat_length))

    def flush_round(self, session_id: str, match_round: int) -> Dict[str, Any] | None:
        """Write one aggregate round record and clear the in-memory buffer."""
        with self._lock:
            buffer = self._sessions.get(session_id)
            if not buffer:
                return None
            chat_lengths = buffer["chat_lengths"]
            record = {
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "player_id": buffer["player_id"],
                "match_round": match_round,
                "events": dict(buffer["events"]),
                "actions": dict(buffer["actions"]),
                "chat_message_count": len(chat_lengths),
                "chat_character_count": sum(chat_lengths),
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as telemetry_file:
                telemetry_file.write(json.dumps(record) + "\n")
            buffer["events"].clear()
            buffer["actions"].clear()
            buffer["chat_lengths"].clear()
            return record

    def discard_session(self, session_id: str) -> None:
        """Discard an unfinished session without flushing it."""
        with self._lock:
            self._sessions.pop(session_id, None)


round_telemetry = RoundTelemetry()
