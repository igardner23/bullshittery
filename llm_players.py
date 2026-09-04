import os
import time
import json
import random
from datetime import datetime
from typing import Optional, Dict, List

try:
    from langchain.chat_models.huggingface import ChatHuggingFace
    from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from langchain.memory import ConversationBufferMemory
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[LLM] Warning: LangChain not fully available, falling back to direct API calls")

from config import TEST_MODE, HF_TOKEN, HF_MODEL, TYPING_STYLES
from src.prompt_harness import NarrativeContext, build_system_prompt as build_narrative_prompt

# Mock responses for test mode
MOCK_RESPONSES = [
    "yeah makes sense",
    "lol true",
    "wait really?",
    "i was thinking the same thing",
    "bruh",
    "honestly same",
    "that's wild",
    "fr tho"
]

# LangChain chain cache (avoid recreating chains)
_chains_cache = {}


def log_to_file(log_entry: dict):
    """Log LLM interactions to file for debugging and telemetry."""
    if TEST_MODE:
        log_entry["test_mode"] = True
    try:
        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, indent=2, ensure_ascii=False) + "\n")
            f.write("-" * 60 + "\n")
    except Exception as e:
        print(f"[LOGGING ERROR] Failed to write to logs.txt: {e}")


def _build_system_prompt(
    player: Dict,
    context_user: Optional[str] = None,
    user_profile: Optional[Dict] = None,
    narrative_context: Optional[NarrativeContext] = None,
) -> str:
    """Build comprehensive system prompt for the LLM.
    
    Combines:
    - Base persona instruction
    - Typing style rules
    - Context about current interaction
    - Optional user profile info
    """
    style_rules = TYPING_STYLES.get(player.get('style', 'lazy'), TYPING_STYLES['lazy'])['prompt']
    system = build_narrative_prompt(player, narrative_context)
    
    system += f"\n\nTYPING STYLE:\n{style_rules}"
    
    if context_user:
        system += f"\n- You are currently responding directly to {context_user}"
    
    if user_profile and user_profile.get('q1'):
        earliest_memory = user_profile.get('q1', '')[:50]
        system += f"\n- About the user: Their earliest memory involves '{earliest_memory}...'"
    
    return system


def _get_or_create_chain(player_name: str) -> 'LLMChain':
    """Get or create a LangChain chain for a player.
    
    This caches chains to avoid repeated initialization overhead.
    """
    if not LANGCHAIN_AVAILABLE:
        return None
    
    if player_name not in _chains_cache:
        try:
            from langchain.llms import HuggingFaceLLM
            
            # Create a simple chat chain
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template("{system_prompt}"),
                HumanMessagePromptTemplate.from_template("{chat_history}\nRespond naturally:")
            ])
            
            # Note: This is simplified - actual LangChain integration may vary
            # based on available model implementations
            print(f"[LLM] Chain caching not fully implemented yet (TODO: full LangChain)")
        except Exception as e:
            print(f"[LLM] Could not create LangChain chain: {e}")
            return None
    
    return _chains_cache.get(player_name)


def _format_chat_context(chat_history: List[Dict], max_messages: int = 8) -> str:
    """Format chat history for the LLM context window."""
    recent = chat_history[-max_messages:] if chat_history else []
    
    formatted = []
    for msg in recent:
        user = msg.get('user', 'Unknown')
        text = msg.get('text', '')
        formatted.append(f"{user}: {text}")
    
    return "\n".join(formatted) if formatted else "(No prior chat history)"


def _parse_json_object(raw_content: str) -> Optional[Dict]:
    """Parse a JSON object, tolerating a model adding a code fence."""
    cleaned = raw_content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1].strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def generate_scene_batch(
    personas: List[Dict],
    chat_history: List[Dict],
    narrative_context: Optional[NarrativeContext] = None,
    max_messages: int = 4,
) -> Dict:
    """Generate a complete conversational beat with one provider request.

    The response contains messages and machine-readable signals so callers do
    not need a second classifier request. Test mode returns a deterministic
    fixture and never contacts the model provider.
    """
    context = narrative_context or NarrativeContext()
    allowed_names = [persona.get("name", "") for persona in personas]
    fallback = {
        "messages": [],
        "scene_event": "",
        "relationship_signals": [],
        "next_stage": context.stage.value,
    }

    if TEST_MODE:
        if allowed_names:
            fallback["messages"] = [{
                "speaker": allowed_names[0],
                "text": "the room is quieter between rounds, huh?",
                "intent": "observation",
            }]
        return fallback

    coordinator = {
        "name": "scene_coordinator",
        "persona": "Coordinate a brief fictional multiplayer chat scene.",
        "interaction_pattern": "social director",
    }
    system_prompt = build_narrative_prompt(coordinator, context) + """

Return only valid JSON with this exact shape:
{
  "messages": [{"speaker": "allowed name", "text": "short line", "intent": "reply|observation|challenge|repair"}],
  "scene_event": "one short description of what changed",
  "relationship_signals": ["trust|friction|curiosity|distance"],
  "next_stage": "lobby|team_bonding|intermission|escalation|dissonance|reflection"
}
Generate no more than the requested number of messages. Use only allowed names.
"""
    user_prompt = json.dumps({
        "allowed_names": allowed_names,
        "chat_history": _format_chat_context(chat_history, max_messages=12),
        "requested_messages": max_messages,
        "team_members": context.team_members,
        "recent_event": context.recent_event,
    })

    import requests

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max(180, max_messages * 90),
        "temperature": 0.75,
    }
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=12,
        )
        response.raise_for_status()
        raw_content = response.json()["choices"][0]["message"]["content"]
        parsed = _parse_json_object(raw_content)
        if not parsed:
            return fallback

        messages = []
        for message in parsed.get("messages", [])[:max_messages]:
            if not isinstance(message, dict):
                continue
            speaker = str(message.get("speaker", "")).strip()
            text = str(message.get("text", "")).strip()
            if speaker in allowed_names and text:
                messages.append({
                    "speaker": speaker,
                    "text": text[:240],
                    "intent": str(message.get("intent", "observation")),
                })
        return {
            "messages": messages,
            "scene_event": str(parsed.get("scene_event", ""))[:240],
            "relationship_signals": [
                str(signal) for signal in parsed.get("relationship_signals", [])[:4]
            ],
            "next_stage": str(parsed.get("next_stage", context.stage.value)),
        }
    except Exception as error:
        print(f"[LLM] Structured scene generation failed: {error}")
        return fallback


def generate_response(
    player: Dict,
    chat_history: List[Dict],
    context_user: Optional[str] = None,
    user_profile: Optional[Dict] = None,
    max_retries: int = 3,
    narrative_context: Optional[NarrativeContext] = None
) -> str:
    """Generate an AI response using LangChain chains (with fallback to direct API).
    
    Args:
        player: Character profile dict
        chat_history: List of prior messages
        context_user: If provided, personalize response to this user
        user_profile: Optional user profile for personalization
        max_retries: Number of API retry attempts
    
    Returns:
        Generated response text
    """
    
    # --- TEST MODE BYPASS ---
    if TEST_MODE:
        print(f"[TEST MODE] Mocking response for {player['name']}")
        time.sleep(0.1)
        mock_text = random.choice(MOCK_RESPONSES)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "player": player['name'],
            "test_mode": True,
            "parsed_message": mock_text,
            "method": "mock"
        }
        log_to_file(log_entry)
        return mock_text
    # ------------------------
    
    print(f"\n[LLM] Generating response for {player['name']} (LangChain mode)")
    
    system_prompt = _build_system_prompt(
        player,
        context_user,
        user_profile,
        narrative_context,
    )
    chat_context = _format_chat_context(chat_history)
    
    # Try LangChain chain first if available
    if LANGCHAIN_AVAILABLE:
        try:
            response = _generate_via_langchain(player, system_prompt, chat_context)
            if response:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "player": player['name'],
                    "context_user": context_user,
                    "method": "langchain",
                    "parsed_message": response
                }
                log_to_file(log_entry)
                return response
        except Exception as e:
            print(f"[LLM] LangChain generation failed: {e}, falling back to direct API")
    
    # Fallback to direct API call
    return _generate_via_api(player, system_prompt, chat_history, chat_context, max_retries)


def _generate_via_langchain(player: Dict, system_prompt: str, chat_context: str) -> Optional[str]:
    """Generate response using LangChain (not fully implemented yet).
    
    This is a placeholder for full LangChain integration.
    """
    print(f"[LLM] LangChain integration in progress...")
    # TODO: Implement full LangChain chain here
    return None


def _generate_via_api(
    player: Dict,
    system_prompt: str,
    chat_history: List[Dict],
    chat_context: str,
    max_retries: int
) -> str:
    """Generate response via direct HuggingFace API call.
    
    Fallback when LangChain is not available or fails.
    """
    import requests
    
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    HEADERS = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Chat so far:\n{chat_context}\n\nRespond naturally and briefly:"}
    ]
    
    payload = {
        "model": HF_MODEL,
        "messages": messages,
        "max_tokens": 80,
        "temperature": 0.8,  # Slightly higher for variety
    }
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "player": player['name'],
        "method": "direct_api",
        "raw_response": None,
        "parsed_message": None,
        "error": None
    }
    
    for attempt in range(max_retries):
        try:
            print(f"[LLM] Calling HF API (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=12)
            response.raise_for_status()
            
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()
            log_entry["raw_response"] = raw_content
            
            # Clean up markdown formatting if present
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1].strip()
            
            text = raw_content.strip()
            
            # Ensure response is short enough
            if len(text) > 200:
                text = text[:200].rsplit(' ', 1)[0] + "..."
            
            log_entry["parsed_message"] = text
            print(f"[LLM] Generated: '{text}'")
            log_to_file(log_entry)
            return text or "..."
            
        except requests.exceptions.Timeout:
            print(f"[LLM] Request timed out (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(1)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                print(f"[LLM] Rate limited, backing off...")
                time.sleep(3)
            else:
                print(f"[LLM] HTTP Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        except Exception as e:
            log_entry["error"] = str(e)
            print(f"[LLM] Unexpected error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    log_to_file(log_entry)
    return "..."  # Fallback empty response