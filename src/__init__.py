"""
Session Intake - A cooperative table psychology game.

This package provides a Gradio-based web application where users interact
with AI personas in a simulated multiplayer environment.
"""

from src.config import (
    PERSONALITIES,
    PERSONALITY_BY_USERNAME,
    TYPING_STYLE_CONFIG,
    TYPING_PHRASES,
    WAITING_ROOM_SCRIPT,
    APPROACH_CHOICES,
    RESPONSE_CHOICES,
    REAL_SIGNAL_CHOICES,
    PRESSURE_CHOICES,
)
from src.models import Personality, TypingConfig, ChatMessage, UserTelemetry
from src.room_manager import RoomManager
from src.telemetry import TelemetryTracker
from src.persona_engine import PersonaEngine
from src.ui import create_ui

__version__ = "1.0.0"
__all__ = [
    "PERSONALITIES",
    "PERSONALITY_BY_USERNAME",
    "TYPING_STYLE_CONFIG",
    "TYPING_PHRASES",
    "WAITING_ROOM_SCRIPT",
    "APPROACH_CHOICES",
    "RESPONSE_CHOICES",
    "REAL_SIGNAL_CHOICES",
    "PRESSURE_CHOICES",
    "Personality",
    "TypingConfig",
    "ChatMessage",
    "UserTelemetry",
    "RoomManager",
    "TelemetryTracker",
    "PersonaEngine",
    "create_ui",
]
