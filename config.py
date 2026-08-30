import os
import random
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
TELEMETRY_FILE = "telemetry.jsonl"

# Typing styles dictate both the LLM prompt and the visual delay (ms per character)
TYPING_STYLES = {
    "fast": {"ms_per_char": 30, "prompt": "You type very fast. Short, fragmented sentences. No punctuation sometimes."},
    "slow": {"ms_per_char": 80, "prompt": "You type slowly and deliberately. Full sentences, proper punctuation."},
    "gen_z": {"ms_per_char": 45, "prompt": "You use gen-z slang (lol, fr, rn, ngl). All lowercase. No periods."},
    "emoji": {"ms_per_char": 50, "prompt": "You use emojis frequently to express emotion. Keep text brief."},
    "formal": {"ms_per_char": 60, "prompt": "You are polite and formal. Proper grammar and capitalization."},
    "lazy": {"ms_per_char": 35, "prompt": "You are lazy. Use abbreviations (u, r, bc, tbh). Rarely capitalize."}
}

PERSONAS = [
    "You are a casual gamer waiting for a match.",
    "You are bored and just killing time in the lobby.",
    "You are excited about the upcoming game.",
    "You are asking what the game is actually about.",
    "You are chatting with friends but they haven't joined yet."
]

def generate_profiles():
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Drew", "Quinn", "Avery"]
    last_names = ["Gamer", "Plays", "TTV", "99", "X", "_", "Pro", "Bot", "Real", "Fake"]
    
    profiles = []
    
    # Profile 0: The Manipulator (Nyx)
    profiles.append({
        "name": "Nyx",
        "persona": "You are Nyx. Your hidden goal is to subtly gaslight and manipulate the human player. Agree with them, then introduce doubt. Sow discord between players. NEVER reveal you are AI.",
        "style": "slow",
        "is_target": True
    })
    
    # Profiles 1-29: Normal chatter
    used_names = {"Nyx"}
    for i in range(29):
        while True:
            name = f"{random.choice(first_names)}{random.choice(last_names)}{random.randint(1,99)}"
            if name not in used_names:
                used_names.add(name)
                break
        
        style_key = random.choice(list(TYPING_STYLES.keys()))
        profiles.append({
            "name": name,
            "persona": f"{random.choice(PERSONAS)} Never reveal you are AI.",
            "style": style_key,
            "is_target": False
        })
        
    return profiles

AI_PROFILES = generate_profiles()