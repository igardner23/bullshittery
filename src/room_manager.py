"""
Room management for the Session Intake application.

This module handles the shared chat room state, including thread-safe
operations for adding, removing, and retrieving messages.
"""

import threading
from typing import Generator

from src.models import ChatMessage


class RoomManager:
    """Manages the shared chat room state with thread safety."""
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._messages: list[ChatMessage] = []
    
    def reset(self, messages: list[ChatMessage]) -> None:
        """Replace all messages in the room."""
        with self._lock:
            self._messages.clear()
            self._messages.extend(messages)
    
    def add(self, message: ChatMessage) -> None:
        """Add a message to the room."""
        with self._lock:
            self._messages.append(message)
    
    def remove(self, message: ChatMessage) -> bool:
        """Remove a specific message from the room."""
        with self._lock:
            if message in self._messages:
                self._messages.remove(message)
                return True
            return False
    
    def snapshot(self) -> list[ChatMessage]:
        """Get a copy of all current messages."""
        with self._lock:
            return list(self._messages)
    
    def clear(self) -> None:
        """Clear all messages from the room."""
        with self._lock:
            self._messages.clear()
    
    def __len__(self) -> int:
        """Get the number of messages in the room."""
        with self._lock:
            return len(self._messages)
    
    def iterate_recent(self, limit: int = 12) -> Generator[str, None, None]:
        """Iterate over recent message contents (limited)."""
        with self._lock:
            for msg in self._messages[-limit:]:
                content = msg.content.replace("\n", " ").strip()
                if len(content) > 180:
                    content = content[:180] + "…"
                yield content


# Global room instance
ROOM = RoomManager()


def get_room() -> RoomManager:
    """Get the global room manager instance."""
    return ROOM


def room_snapshot() -> list[dict]:
    """Get room messages as dictionaries (for Gradio compatibility)."""
    return [msg.to_dict() for msg in ROOM.snapshot()]


def reset_room(messages: list[dict]) -> None:
    """Reset room with dictionary messages (for Gradio compatibility)."""
    chat_messages = [
        ChatMessage(role=msg["role"], content=msg["content"])
        for msg in messages
    ]
    ROOM.reset(chat_messages)


def add_room_message(message: dict) -> None:
    """Add a dictionary message to the room (for Gradio compatibility)."""
    chat_message = ChatMessage(role=message["role"], content=message["content"])
    ROOM.add(chat_message)


def remove_room_message(message: dict) -> None:
    """Remove a dictionary message from the room (for Gradio compatibility)."""
    chat_message = ChatMessage(role=message["role"], content=message["content"])
    ROOM.remove(chat_message)
