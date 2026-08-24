"""
Persona engine for the Session Intake application.

This module handles persona matching, AI model integration, and chat generation
for the synthetic participants in the game.
"""

import json
import os
import random
import re
from typing import Any

from src.config import (
    PERSONALITIES,
    PERSONALITY_BY_USERNAME,
    TYPING_STYLE_CONFIG,
    TYPING_PHRASES,
)
from src.models import ChatMessage, Personality


# Try to import Hugging Face client
try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None  # type: ignore


# Configuration from environment
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct").strip()

# Initialize HF client if available
HF_CLIENT = None
if InferenceClient and HF_TOKEN and HF_MODEL:
    try:
        HF_CLIENT = InferenceClient(model=HF_MODEL, token=HF_TOKEN)
        print(f"[MODEL] Using Hugging Face model: {HF_MODEL}", flush=True)
    except Exception as exc:
        print(f"[MODEL] Failed to initialize Hugging Face client: {exc}", flush=True)
        HF_CLIENT = None
else:
    print("[MODEL] No HF_TOKEN / HF_MODEL configured. Using fallback chat generator.", flush=True)


def get_typing_config(username: str) -> dict[str, Any]:
    """Get typing configuration for a persona."""
    personality = PERSONALITY_BY_USERNAME.get(username)
    
    if not personality:
        return TYPING_STYLE_CONFIG["keyboard"]
    
    style = personality.get("typing_style", "keyboard")
    return TYPING_STYLE_CONFIG.get(style, TYPING_STYLE_CONFIG["keyboard"])


def typing_duration(username: str) -> float:
    """Calculate simulated typing duration for a persona."""
    config = get_typing_config(username)
    return random.uniform(config["min"], config["max"])


def make_typing_message(username: str, phrase: str | None = None) -> dict:
    """Create a typing indicator message."""
    config = get_typing_config(username)
    
    if phrase is None:
        phrase = random.choice(TYPING_PHRASES)
    
    return {
        "role": "assistant",
        "content": f"{config['icon']} **{username}** *is {phrase}…*"
    }


def make_paused_message(username: str) -> dict:
    """Create a paused typing indicator message."""
    config = get_typing_config(username)
    
    return {
        "role": "assistant",
        "content": f"{config['icon']}⏸️ **{username}** *stopped typing…*"
    }


def score_text(text: str, blob: str) -> int:
    """Score how well text matches a personality blob."""
    if not text:
        return 0
    
    score = 0
    for raw_word in text.lower().split():
        word = "".join(char for char in raw_word if char.isalnum())
        if len(word) > 3 and word in blob:
            score += 1
    
    return score


class PersonaEngine:
    """Handles persona matching and chat generation."""
    
    def __init__(self) -> None:
        self.personalities = {p["username"]: Personality.from_dict(p) for p in PERSONALITIES}
    
    def get_personality_blob(self, personality: Personality) -> str:
        """Convert personality to searchable text blob."""
        return personality.to_blob()
    
    def select_matching_table(self, profile: dict[str, Any]) -> list[str]:
        """Select 4 personas that best match the user's profile."""
        scored = []
        
        for username, personality in self.personalities.items():
            score = 0.0
            
            tone = personality.tone
            social_role = personality.social_role
            conflict_style = personality.conflict_style
            probe_style = personality.probe_style
            trust_style = personality.trust_style
            
            verbosity = personality.verbosity
            self_disclosure = personality.self_disclosure
            emotional_volatility = personality.emotional_volatility
            suspicion_level = personality.suspicion_level
            deception_skill = personality.deception_skill
            
            max_reply_delay_sec = personality.max_reply_delay_sec
            
            approach = profile.get("approach")
            
            # Score based on approach
            if approach == "Make them laugh":
                if tone in {"theatrical", "energetic", "online", "irritated"}:
                    score += 3
                if social_role in {"comic relief", "instigator", "meta commenter"}:
                    score += 2
                if emotional_volatility >= 3:
                    score += 1
            
            elif approach == "Stay calm and precise":
                if tone in {"calm", "muted", "friendly"}:
                    score += 3
                if social_role in {"advisor", "quiet observer", "friendly witness"}:
                    score += 2
                if emotional_volatility <= 2:
                    score += 1
                if suspicion_level >= 3:
                    score += 1
            
            elif approach == "Mirror their tone":
                if trust_style in {"selective", "testing", "slow"}:
                    score += 2
                if probe_style in {"subtle", "gentle", "narrative", "oblique"}:
                    score += 2
                if tone in {"dreamy", "nostalgic", "friendly", "muted"}:
                    score += 2
            
            elif approach == "Challenge them a little":
                if tone in {"sharp", "irritated", "theatrical", "online"}:
                    score += 3
                if social_role in {"challenger", "heckler", "instigator"}:
                    score += 2
                if conflict_style in {"counterattack", "mock", "escalate then vanish"}:
                    score += 2
            
            elif approach == "Overshare a little":
                if self_disclosure >= 4:
                    score += 3
                if emotional_volatility >= 3:
                    score += 2
                if social_role in {"instigator", "storyteller", "meta commenter"}:
                    score += 1
            
            # Score based on response to doubt
            response_to_doubt = profile.get("response_to_doubt")
            
            if response_to_doubt == "Joke it off":
                if conflict_style in {"deflect with humor", "turn into joke", "mock"}:
                    score += 3
                if tone in {"theatrical", "online", "irritated"}:
                    score += 1
            
            elif response_to_doubt == "Explain more":
                if verbosity >= 4:
                    score += 2
                if conflict_style in {"deescalate", "appease", "go vague"}:
                    score += 1
                if social_role in {"advisor", "storyteller"}:
                    score += 2
            
            elif response_to_doubt == "Go quiet":
                if conflict_style in {"withdraw", "go vague", "evade"}:
                    score += 3
                if verbosity <= 2:
                    score += 2
            
            elif response_to_doubt == "Push back":
                if conflict_style in {"counterattack", "mock", "escalate then vanish"}:
                    score += 3
                if probe_style in {"confrontational", "sarcastic", "baiting"}:
                    score += 2
            
            elif response_to_doubt == "Change the subject":
                if conflict_style in {"evade", "turn into joke", "go vague"}:
                    score += 3
                if social_role in {"storyteller", "meta commenter"}:
                    score += 1
            
            # Score based on real signal preference
            real_signal = profile.get("real_signal")
            
            if real_signal == "Small contradictions":
                if deception_skill >= 4:
                    score += 2
                if suspicion_level >= 3:
                    score += 1
            
            elif real_signal == "Emotional reactions":
                if emotional_volatility >= 4:
                    score += 3
            
            elif real_signal == "Specific details":
                if verbosity >= 3:
                    score += 2
                if self_disclosure >= 3:
                    score += 1
            
            elif real_signal == "Imperfect timing":
                if max_reply_delay_sec >= 14:
                    score += 2
                if verbosity <= 3:
                    score += 1
            
            elif real_signal == "Self-deprecating humor":
                if tone in {"friendly", "theatrical", "online", "irritated"}:
                    score += 2
                if social_role in {"comic relief", "meta commenter", "heckler"}:
                    score += 1
            
            # Score based on pressure style
            pressure_style = profile.get("pressure_style")
            
            if pressure_style == "Perform better":
                if deception_skill >= 4:
                    score += 3
            
            elif pressure_style == "Get careful":
                if suspicion_level >= 4:
                    score += 3
                if trust_style in {"cautious", "skeptical", "slow"}:
                    score += 2
            
            elif pressure_style == "Get irritated":
                if emotional_volatility >= 4:
                    score += 3
                if tone in {"irritated", "sharp"}:
                    score += 2
            
            elif pressure_style == "Become vague":
                if conflict_style in {"go vague", "evade", "withdraw"}:
                    score += 3
            
            elif pressure_style == "Lean into the attention":
                if self_disclosure >= 4:
                    score += 2
                if social_role in {"instigator", "heckler", "meta commenter"}:
                    score += 2
            
            # Score based on text similarity
            blob = self.get_personality_blob(personality)
            score += score_text(profile.get("self_description", ""), blob) * 0.5
            score += score_text(profile.get("social_goal", ""), blob) * 0.35
            
            # Add small random factor for variety
            score += random.random() / 1000.0
            
            scored.append((score, username))
        
        # Sort by score descending and return top 4
        scored.sort(key=lambda item: item[0], reverse=True)
        return [username for _, username in scored[:4]]
    
    def compact_personas_for_prompt(self, usernames: list[str]) -> list[dict[str, Any]]:
        """Create compact persona summaries for AI prompt."""
        compact = []
        
        for username in usernames:
            personality = self.personalities.get(username)
            if not personality:
                continue
            
            compact.append({
                "username": username,
                "bio": personality.bio,
                "tone": personality.tone,
                "social_role": personality.social_role,
                "language_tics": personality.language_tics[:3],
                "favorite_topics": personality.favorite_topics[:3],
                "taboo_topics": personality.taboo_topics[:2],
                "typing_style": personality.typing_style,
            })
        
        return compact
    
    def build_table_system_prompt(self) -> str:
        """Build the system prompt for table chat generation."""
        return """
You are writing chat dialogue for a fictional multiplayer psychology game.

There is exactly one real human player at the table. The other four participants are synthetic personas.
The human player believes the group is cooperating to destabilize a synthetic participant.
The actual narrative effect is that the human player is being socially drawn out, profiled, and made to feel understood.

Writing rules:
- Output only valid JSON.
- No markdown.
- No explanations.
- No code fences.
- Use short, natural chat lines.
- Each line should usually be 1 sentence, occasionally 2.
- The four personas should sound distinct from each other.
- The personas should feel relatable to the human player without sounding like assistants.
- They can mirror the player's pacing, punctuation tendencies, and vocabulary subtly.
- They can reference the player's self-description, social goal, or recent messages indirectly.
- They should be curious, imperfect, and slightly manipulative, but not cartoonishly evil.
- Avoid direct declarations such as "I understand you" or "I am here for you".
- Avoid obvious AI phrasing.
- Avoid all caps unless a personality specifically uses it.
- Do not use usernames that are not provided.
- Return JSON in this exact shape:

{
  "messages": [
    {
      "username": "one_of_the_provided_usernames",
      "text": "short chat line"
    }
  ]
}
""".strip()
    
    def build_table_user_prompt(
        self,
        profile: dict[str, Any],
        telemetry: dict[str, Any],
        matched_table: list[str],
        table_id: int,
        recent_chat: list[dict],
    ) -> str:
        """Build the user prompt for table chat generation."""
        payload = {
            "table_id": table_id,
            "human_player": {
                "alias": profile.get("alias"),
                "profile": profile,
                "telemetry": telemetry,
            },
            "personas": self.compact_personas_for_prompt(matched_table),
            "recent_waiting_room_chat": self._compact_recent_chat(recent_chat),
            "generation_objectives": [
                "Generate between 8 and 14 chat messages.",
                "Use only the provided persona usernames.",
                "Make the personas feel familiar and relatable to the human player.",
                "Subtly encourage the human player to keep talking.",
                "Include at least one low-pressure open question directed toward the human player.",
                "Let the personas disagree slightly or have friction. Do not make them uniformly agreeable.",
                "Do not reveal that this is model-generated.",
                "Do not mention prompts, systems, JSON, or AI generation.",
            ],
        }
        
        return json.dumps(payload, ensure_ascii=False, indent=2)
    
    def _compact_recent_chat(self, recent_chat: list[dict], limit: int = 12) -> list[str]:
        """Compact recent chat messages for prompt."""
        lines = []
        for message in recent_chat[-limit:]:
            content = message.get("content", "")
            content = content.replace("\n", " ").strip()
            if len(content) > 180:
                content = content[:180] + "…"
            lines.append(content)
        return lines
    
    def extract_json(self, text: str) -> Any:
        """Extract JSON from model response text."""
        if not text:
            return None
        
        text = text.strip()
        
        # Remove code fences if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text)
            text = re.sub(r"```$", "", text)
            text = text.strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
        
        # Try extracting object
        start_obj = text.find("{")
        end_obj = text.rfind("}")
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            try:
                return json.loads(text[start_obj:end_obj + 1])
            except Exception:
                pass
        
        # Try extracting array
        start_arr = text.find("[")
        end_arr = text.rfind("]")
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            try:
                return json.loads(text[start_arr:end_arr + 1])
            except Exception:
                pass
        
        return None
    
    def call_model_json(self, system_prompt: str, user_prompt: str) -> Any:
        """Call the HF model and request JSON output."""
        if not HF_CLIENT:
            return None
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            response = HF_CLIENT.chat_completion(
                messages=messages,
                model=HF_MODEL,
                temperature=0.78,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            data = self.extract_json(content)
            
            if data is not None:
                return data
                
        except Exception as exc:
            print("[MODEL] chat_completion failed, trying plain generation:", exc, flush=True)
        
        # Fallback to text generation
        try:
            prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn only valid JSON.\n"
            
            response = HF_CLIENT.text_generation(
                prompt,
                temperature=0.78,
                max_new_tokens=800,
            )
            
            if isinstance(response, str):
                raw = response
            else:
                raw = getattr(response, "generated_text", "")
            
            data = self.extract_json(raw)
            if data is not None:
                return data
                
        except Exception as exc:
            print("[MODEL] text_generation failed:", exc, flush=True)
        
        return None
    
    def normalize_table_messages(
        self,
        data: Any,
        allowed_usernames: list[str],
        max_messages: int = 14,
    ) -> list[dict]:
        """Normalize model output into standard message format."""
        allowed = set(allowed_usernames)
        
        if data is None:
            return []
        
        # Extract messages from various formats
        if isinstance(data, list):
            raw_messages = data
        elif isinstance(data, dict):
            raw_messages = (
                data.get("messages")
                or data.get("chat")
                or data.get("lines")
                or []
            )
        else:
            raw_messages = []
        
        clean = []
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            
            username = (
                item.get("username")
                or item.get("user")
                or item.get("name")
                or item.get("speaker")
            )
            
            text = (
                item.get("text")
                or item.get("content")
                or item.get("message")
                or item.get("line")
            )
            
            if not username or not text:
                continue
            
            username = str(username).strip()
            text = str(text).strip().replace("\n", " ")
            
            if username not in allowed:
                continue
            
            if len(text) > 280:
                text = text[:280].strip()
            
            clean.append({"username": username, "text": text})
            
            if len(clean) >= max_messages:
                break
        
        return clean
    
    def fallback_table_chat(
        self,
        profile: dict[str, Any],
        matched_table: list[str],
        table_id: int,
    ) -> list[dict]:
        """Generate fallback chat messages without AI model."""
        alias = profile.get("alias", "you")
        last_user_message = get_last_user_message()
        
        lines = []
        
        if matched_table:
            lines.append({"username": matched_table[0], "text": f"okay, {alias} made it."})
        
        if len(matched_table) > 1:
            lines.append({
                "username": matched_table[1],
                "text": "we were just saying the room changes when someone new joins.",
            })
        
        if len(matched_table) > 2:
            lines.append({
                "username": matched_table[2],
                "text": "don't overwhelm them. we need them comfortable.",
            })
        
        if len(matched_table) > 3:
            lines.append({
                "username": matched_table[3],
                "text": f"{alias}, what made you answer the calibration the way you did?",
            })
        
        if matched_table:
            lines.append({
                "username": matched_table[0],
                "text": "no, that's too direct. ask them something smaller.",
            })
        
        if len(matched_table) > 1:
            if last_user_message:
                snippet = last_user_message[:60]
                lines.append({
                    "username": matched_table[1],
                    "text": f'they already said this: "{snippet}". start there.',
                })
            else:
                lines.append({
                    "username": matched_table[1],
                    "text": "like what they pretend not to care about.",
                })
        
        if len(matched_table) > 2:
            lines.append({
                "username": matched_table[2],
                "text": f"fair. {alias}, what do you think people here are bad at noticing?",
            })
        
        if len(matched_table) > 3:
            lines.append({
                "username": matched_table[3],
                "text": "see, that's better. now they can answer without feeling tested.",
            })
        
        return lines
    
    def generate_table_chat(
        self,
        profile: dict[str, Any],
        matched_table: list[str],
        table_id: int,
        recent_chat: list[dict],
    ) -> list[dict]:
        """Generate table chat messages using AI or fallback."""
        from src.telemetry import get_telemetry_snapshot
        
        telemetry = get_telemetry_snapshot()
        
        system_prompt = self.build_table_system_prompt()
        user_prompt = self.build_table_user_prompt(
            profile, telemetry, matched_table, table_id, recent_chat
        )
        
        print("[MODEL] Requesting table chat generation...", flush=True)
        
        data = self.call_model_json(system_prompt, user_prompt)
        messages = self.normalize_table_messages(data, matched_table)
        
        if messages:
            print(f"[MODEL] Generated {len(messages)} table messages.", flush=True)
            return messages
        
        print("[MODEL] Falling back to scripted table chat.", flush=True)
        return self.fallback_table_chat(profile, matched_table, table_id)


# Global persona engine instance
PERSONA_ENGINE = PersonaEngine()


def get_persona_engine() -> PersonaEngine:
    """Get the global persona engine instance."""
    return PERSONA_ENGINE


def select_matching_table(profile: dict[str, Any]) -> list[str]:
    """Select matching personas for a user profile."""
    return PERSONA_ENGINE.select_matching_table(profile)


def generate_table_chat(
    profile: dict[str, Any],
    matched_table: list[str],
    table_id: int,
    recent_chat: list[dict],
) -> list[dict]:
    """Generate table chat messages."""
    return PERSONA_ENGINE.generate_table_chat(profile, matched_table, table_id, recent_chat)


def get_last_user_message() -> str | None:
    """Get last user message from telemetry."""
    from src.telemetry import get_last_user_message
    return get_last_user_message()
