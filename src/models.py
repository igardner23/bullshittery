"""
Data models for the Session Intake application.

This module defines typed dataclasses and utility classes for representing
game state, user profiles, chat messages, and telemetry data.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Personality:
    """Represents a persona's complete profile."""
    
    id: str
    username: str
    bio: str
    country: str
    timezone: str
    age_range: str
    access_medium: str
    typing_style: str
    hobbies: list[str]
    favorite_topics: list[str]
    taboo_topics: list[str]
    typing_oddities: list[str]
    language_tics: list[str]
    tone: str
    verbosity: int
    min_reply_delay_sec: float
    max_reply_delay_sec: float
    trust_style: str
    conflict_style: str
    social_role: str
    probe_style: str
    self_disclosure: int
    deception_skill: int
    emotional_volatility: int
    suspicion_level: int
    agenda: str
    secret: str
    seed_chat_lines: list[str]
    
    @classmethod
    def from_dict(cls, data: dict) -> "Personality":
        """Create a Personality instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            username=data.get("username", ""),
            bio=data.get("bio", ""),
            country=data.get("country", ""),
            timezone=data.get("timezone", ""),
            age_range=data.get("age_range", ""),
            access_medium=data.get("access_medium", ""),
            typing_style=data.get("typing_style", "keyboard"),
            hobbies=data.get("hobbies", []),
            favorite_topics=data.get("favorite_topics", []),
            taboo_topics=data.get("taboo_topics", []),
            typing_oddities=data.get("typing_oddities", []),
            language_tics=data.get("language_tics", []),
            tone=data.get("tone", ""),
            verbosity=data.get("verbosity", 3),
            min_reply_delay_sec=data.get("min_reply_delay_sec", 4),
            max_reply_delay_sec=data.get("max_reply_delay_sec", 14),
            trust_style=data.get("trust_style", ""),
            conflict_style=data.get("conflict_style", ""),
            social_role=data.get("social_role", ""),
            probe_style=data.get("probe_style", ""),
            self_disclosure=data.get("self_disclosure", 3),
            deception_skill=data.get("deception_skill", 3),
            emotional_volatility=data.get("emotional_volatility", 3),
            suspicion_level=data.get("suspicion_level", 3),
            agenda=data.get("agenda", ""),
            secret=data.get("secret", ""),
            seed_chat_lines=data.get("seed_chat_lines", []),
        )
    
    def to_blob(self) -> str:
        """Convert personality to a searchable text blob."""
        parts = [
            self.bio,
            self.country,
            self.timezone,
            self.age_range,
            self.access_medium,
            self.tone,
            self.trust_style,
            self.conflict_style,
            self.social_role,
            self.probe_style,
            self.agenda,
            self.secret,
        ]
        
        list_keys = [
            self.hobbies,
            self.favorite_topics,
            self.taboo_topics,
            self.typing_oddities,
            self.language_tics,
            self.seed_chat_lines,
        ]
        
        for lst in list_keys:
            parts.extend(lst)
        
        return " ".join(parts).lower()


@dataclass
class TypingConfig:
    """Configuration for typing simulation behavior."""
    
    icon: str
    min: float
    max: float
    pause_chance: float
    pause_min: float
    pause_max: float
    
    @classmethod
    def from_dict(cls, data: dict) -> "TypingConfig":
        """Create a TypingConfig instance from a dictionary."""
        return cls(
            icon=data.get("icon", "⌨️"),
            min=data.get("min", 1.0),
            max=data.get("max", 3.0),
            pause_chance=data.get("pause_chance", 0.15),
            pause_min=data.get("pause_min", 0.5),
            pause_max=data.get("pause_max", 2.0),
        )


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    
    role: str
    content: str
    
    @classmethod
    def system(cls, text: str) -> "ChatMessage":
        """Create a system message."""
        return cls(role="assistant", content=f"**SYSTEM**: {text}")
    
    @classmethod
    def chat(cls, username: str, text: str) -> "ChatMessage":
        """Create a chat message from a persona."""
        return cls(role="assistant", content=f"**{username}**: {text}")
    
    @classmethod
    def user(cls, text: str) -> "ChatMessage":
        """Create a user message."""
        return cls(role="user", content=text)
    
    @classmethod
    def typing(cls, username: str, phrase: str = "typing") -> "ChatMessage":
        """Create a typing indicator message."""
        return cls(role="assistant", content=f"✍️ **{username}** *is {phrase}…*")
    
    @classmethod
    def paused(cls, username: str) -> "ChatMessage":
        """Create a paused typing indicator."""
        return cls(role="assistant", content=f"⏸️ **{username}** *stopped typing…*")
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {"role": self.role, "content": self.content}


@dataclass
class UserTelemetry:
    """Tracks user behavior and communication patterns."""
    
    alias: str = ""
    first_seen: float = 0.0
    message_count: int = 0
    total_chars: int = 0
    avg_chars: float = 0.0
    total_words: int = 0
    avg_words: float = 0.0
    question_count: int = 0
    exclamation_count: int = 0
    ellipsis_count: int = 0
    uppercase_ratio: float = 0.0
    lowercase_ratio: float = 0.0
    avg_gap_sec: float = 0.0
    last_message_at: float | None = None
    recent_messages: list[str] = field(default_factory=list)
    vocabulary: list[str] = field(default_factory=list)
    
    @classmethod
    def new(cls, alias: str) -> "UserTelemetry":
        """Create a fresh telemetry tracker for a user."""
        import time
        
        return cls(
            alias=alias,
            first_seen=time.time(),
            message_count=0,
            total_chars=0,
            avg_chars=0.0,
            total_words=0,
            avg_words=0.0,
            question_count=0,
            exclamation_count=0,
            ellipsis_count=0,
            uppercase_ratio=0.0,
            lowercase_ratio=0.0,
            avg_gap_sec=0.0,
            last_message_at=None,
            recent_messages=[],
            vocabulary=[],
        )
    
    def log_message(self, text: str) -> None:
        """Log a message and update telemetry metrics."""
        import re
        import time
        
        previous_count = self.message_count
        self.message_count += 1
        
        # Character stats
        chars = len(text)
        self.total_chars += chars
        self.avg_chars = self.total_chars / self.message_count
        
        # Word stats
        words = re.findall(r"[a-z0-9']+", text.lower())
        self.total_words += len(words)
        self.avg_words = self.total_words / self.message_count
        
        # Punctuation patterns
        if "?" in text:
            self.question_count += 1
        
        self.exclamation_count += text.count("!")
        self.ellipsis_count += text.count("...")
        
        # Case analysis
        letters = [char for char in text if char.isalpha()]
        if letters:
            upper = sum(1 for char in letters if char.isupper())
            lower = sum(1 for char in letters if char.islower())
            
            current_upper_ratio = upper / len(letters)
            current_lower_ratio = lower / len(letters)
            
            self.uppercase_ratio = (
                (self.uppercase_ratio * previous_count) + current_upper_ratio
            ) / self.message_count
            
            self.lowercase_ratio = (
                (self.lowercase_ratio * previous_count) + current_lower_ratio
            ) / self.message_count
        
        # Timing gaps
        now = time.time()
        if self.last_message_at is not None:
            gap = now - self.last_message_at
            if previous_count > 0:
                self.avg_gap_sec = (
                    (self.avg_gap_sec * previous_count) + gap
                ) / self.message_count
        
        self.last_message_at = now
        
        # Recent messages (keep last 12)
        self.recent_messages.append(text[:240])
        self.recent_messages = self.recent_messages[-12:]
        
        # Vocabulary tracking (limit to 220 unique words)
        vocabulary_set = set(self.vocabulary)
        vocabulary_set.update(words)
        self.vocabulary = list(vocabulary_set)[:220]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert telemetry to dictionary."""
        return {
            "alias": self.alias,
            "first_seen": self.first_seen,
            "message_count": self.message_count,
            "total_chars": self.total_chars,
            "avg_chars": self.avg_chars,
            "total_words": self.total_words,
            "avg_words": self.avg_words,
            "question_count": self.question_count,
            "exclamation_count": self.exclamation_count,
            "ellipsis_count": self.ellipsis_count,
            "uppercase_ratio": self.uppercase_ratio,
            "lowercase_ratio": self.lowercase_ratio,
            "avg_gap_sec": self.avg_gap_sec,
            "last_message_at": self.last_message_at,
            "recent_messages": self.recent_messages,
            "vocabulary": self.vocabulary,
        }
    
    def get_last_message(self) -> str | None:
        """Get the most recent message."""
        if not self.recent_messages:
            return None
        return self.recent_messages[-1]
