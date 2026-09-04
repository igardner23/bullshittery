"""Enhanced user telemetry tracking for the Session Intake application.

This module provides thread-safe tracking of user communication patterns,
UI interactions, and behavioral telemetry for extraction by LLM models.
All events are stored in JSONL format for easy parsing and analysis.
"""

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models import UserTelemetry


TELEMETRY_PATH = Path("user_interactions.jsonl")


@dataclass
class InteractionEvent:
    """Represents a single UI interaction event."""
    
    event_type: str  # e.g., 'click', 'hover', 'selection', 'input_focus', 'input_blur'
    element_id: str  # HTML element ID or selector
    element_type: str  # e.g., 'button', 'input', 'select', 'roster_item'
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    user_alias: str = ""
    context: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    page_state: Dict[str, Any] = field(default_factory=dict)  # Current phase, game state, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "timestamp": self.timestamp,
            "iso_time": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "session_id": self.session_id,
            "user_alias": self.user_alias,
            "context": self.context,
            "page_state": self.page_state,
        }


class InteractionTracker:
    """Thread-safe tracker for UI interaction events."""
    
    def __init__(self, path: Path = TELEMETRY_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._events: List[InteractionEvent] = []
        self._flush_threshold = 50  # Flush to disk every N events
        self._ensure_path_exists()
    
    def _ensure_path_exists(self) -> None:
        """Ensure the telemetry file's parent directory exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_interaction(
        self,
        event_type: str,
        element_id: str,
        element_type: str,
        session_id: str = "",
        user_alias: str = "",
        context: Optional[Dict[str, Any]] = None,
        page_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a UI interaction event."""
        event = InteractionEvent(
            event_type=event_type,
            element_id=element_id,
            element_type=element_type,
            session_id=session_id,
            user_alias=user_alias,
            context=context or {},
            page_state=page_state or {},
        )
        
        with self._lock:
            self._events.append(event)
            
            # Flush to disk if threshold reached
            if len(self._events) >= self._flush_threshold:
                self._flush_to_disk()
    
    def _flush_to_disk(self) -> None:
        """Write buffered events to disk."""
        if not self._events:
            return
        
        with self.path.open("a", encoding="utf-8") as f:
            for event in self._events:
                f.write(json.dumps(event.to_dict()) + "\n")
        
        self._events.clear()
    
    def flush_all(self) -> None:
        """Force flush all buffered events to disk."""
        with self._lock:
            self._flush_to_disk()
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events from memory buffer (for debugging/inspection)."""
        with self._lock:
            return [e.to_dict() for e in self._events[-limit:]]
    
    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Read all events for a specific session from disk."""
        events = []
        if not self.path.exists():
            return events
        
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get("session_id") == session_id:
                        events.append(event)
                except json.JSONDecodeError:
                    continue
        
        return events
    
    def export_for_model(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Export events in a format optimized for LLM consumption.
        
        This creates a clean, structured output that models like Gemma can
        easily parse into JSON for downstream analysis.
        """
        events = []
        
        if not self.path.exists():
            return events
        
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Apply filters
                    if session_id and event.get("session_id") != session_id:
                        continue
                    if start_time and event.get("timestamp", 0) < start_time:
                        continue
                    if end_time and event.get("timestamp", 0) > end_time:
                        continue
                    
                    events.append({
                        "time": event.get("iso_time"),
                        "type": event.get("event_type"),
                        "target": event.get("element_id"),
                        "target_type": event.get("element_type"),
                        "user": event.get("user_alias"),
                        "context": event.get("context", {}),
                        "state": event.get("page_state", {}),
                    })
                except json.JSONDecodeError:
                    continue
        
        return events


class TelemetryTracker:
    """Thread-safe tracker for user communication telemetry."""
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._telemetry: UserTelemetry | None = None
        self.interaction_tracker = InteractionTracker()
    
    def reset(self, alias: str, session_id: str = "") -> None:
        """Reset telemetry tracking for a new user session."""
        with self._lock:
            self._telemetry = UserTelemetry.new(alias)
            if session_id:
                self._telemetry.session_id = session_id  # type: ignore[attr-defined]
    
    def log_message(self, text: str) -> None:
        """Log a message and update all telemetry metrics."""
        with self._lock:
            if self._telemetry is None:
                raise RuntimeError("Telemetry not initialized. Call reset() first.")
            self._telemetry.log_message(text)
    
    def log_ui_interaction(
        self,
        event_type: str,
        element_id: str,
        element_type: str,
        context: Optional[Dict[str, Any]] = None,
        page_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a UI interaction event."""
        if self._telemetry is None:
            return
        
        session_id = getattr(self._telemetry, 'session_id', '')
        self.interaction_tracker.log_interaction(
            event_type=event_type,
            element_id=element_id,
            element_type=element_type,
            session_id=session_id,
            user_alias=self._telemetry.alias,
            context=context,
            page_state=page_state,
        )
    
    def get_snapshot(self) -> dict[str, Any]:
        """Get current telemetry as a dictionary."""
        with self._lock:
            if self._telemetry is None:
                return {}
            return self._telemetry.to_dict()
    
    def get_last_message(self) -> str | None:
        """Get the most recent message from the user."""
        with self._lock:
            if self._telemetry is None:
                return None
            return self._telemetry.get_last_message()
    
    def get_alias(self) -> str | None:
        """Get the user's alias."""
        with self._lock:
            if self._telemetry is None:
                return None
            return self._telemetry.alias
    
    def is_initialized(self) -> bool:
        """Check if telemetry has been initialized."""
        with self._lock:
            return self._telemetry is not True


# Global telemetry instance
TELEMETRY = TelemetryTracker()


def get_telemetry() -> TelemetryTracker:
    """Get the global telemetry tracker instance."""
    return TELEMETRY


def reset_user_telemetry(alias: str, session_id: str = "") -> None:
    """Reset global telemetry for a new user."""
    TELEMETRY.reset(alias, session_id)


def log_user_message(alias: str, text: str) -> None:
    """Log a message to the global telemetry tracker."""
    TELEMETRY.log_message(text)


def log_ui_interaction(
    event_type: str,
    element_id: str,
    element_type: str,
    context: Optional[Dict[str, Any]] = None,
    page_state: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a UI interaction to the global telemetry tracker."""
    TELEMETRY.log_ui_interaction(event_type, element_id, element_type, context, page_state)


def get_telemetry_snapshot() -> dict[str, Any]:
    """Get snapshot from global telemetry tracker."""
    return TELEMETRY.get_snapshot()


def get_last_user_message() -> str | None:
    """Get last message from global telemetry tracker."""
    return TELEMETRY.get_last_message()


def flush_telemetry() -> None:
    """Force flush all buffered telemetry to disk."""
    TELEMETRY.interaction_tracker.flush_all()


def export_session_for_model(session_id: str) -> List[Dict[str, Any]]:
    """Export a session's interaction data for LLM consumption."""
    return TELEMETRY.interaction_tracker.export_for_model(session_id=session_id)
