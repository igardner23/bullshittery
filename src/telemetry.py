"""
User telemetry tracking for the Session Intake application.

This module provides thread-safe tracking of user communication patterns,
including message frequency, vocabulary, punctuation habits, and timing.
"""

import threading
from typing import Any

from src.models import UserTelemetry


class TelemetryTracker:
    """Thread-safe tracker for user communication telemetry."""
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._telemetry: UserTelemetry | None = None
    
    def reset(self, alias: str) -> None:
        """Reset telemetry tracking for a new user session."""
        with self._lock:
            self._telemetry = UserTelemetry.new(alias)
    
    def log_message(self, text: str) -> None:
        """Log a message and update all telemetry metrics."""
        with self._lock:
            if self._telemetry is None:
                raise RuntimeError("Telemetry not initialized. Call reset() first.")
            self._telemetry.log_message(text)
    
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
            return self._telemetry is not None


# Global telemetry instance
TELEMETRY = TelemetryTracker()


def get_telemetry() -> TelemetryTracker:
    """Get the global telemetry tracker instance."""
    return TELEMETRY


def reset_user_telemetry(alias: str) -> None:
    """Reset global telemetry for a new user."""
    TELEMETRY.reset(alias)


def log_user_message(alias: str, text: str) -> None:
    """Log a message to the global telemetry tracker."""
    TELEMETRY.log_message(text)


def get_telemetry_snapshot() -> dict[str, Any]:
    """Get snapshot from global telemetry tracker."""
    return TELEMETRY.get_snapshot()


def get_last_user_message() -> str | None:
    """Get last message from global telemetry tracker."""
    return TELEMETRY.get_last_message()
