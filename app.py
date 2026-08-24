import json
import os
import random
import re
import threading
import time

import gradio as gr


try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None


PERSONALITIES = [
    {
        "id": "p001",
        "username": "mariana.lx",
        "bio": "Lurks in dead forums and likes places that feel temporarily abandoned.",
        "country": "Portugal",
        "timezone": "Europe/Lisbon",
        "age_range": "24-30",
        "access_medium": "Desktop / Firefox",
        "typing_style": "hesitant",
        "hobbies": ["urban photography", "abandoned places", "ambient synth"],
        "favorite_topics": ["liminal spaces", "night transit", "memory"],
        "taboo_topics": ["work", "family", "money"],
        "typing_oddities": ["mostly lowercase", "uses ellipses", "rarely ends sentences with punctuation"],
        "language_tics": ["idk", "anyway", "maybe"],
        "tone": "muted",
        "verbosity": 2,
        "min_reply_delay_sec": 4,
        "max_reply_delay_sec": 14,
        "trust_style": "slow",
        "conflict_style": "withdraw",
        "social_role": "quiet observer",
        "probe_style": "subtle",
        "self_disclosure": 2,
        "deception_skill": 4,
        "emotional_volatility": 2,
        "suspicion_level": 4,
        "agenda": "avoid direct personal history while seeming sympathetic",
        "secret": "uses an alt account to escape a previous reputation",
        "seed_chat_lines": [
            "anyone else notice this place feels emptier at night?",
            "not saying anything is wrong. just saying it's quiet."
        ]
    },
    {
        "id": "p002",
        "username": "dmac_1987",
        "bio": "Makes joke sermons about obsolete technology and bad decisions.",
        "country": "Canada",
        "timezone": "America/Toronto",
        "age_range": "31-38",
        "access_medium": "Android / Chrome",
        "typing_style": "keyboard",
        "hobbies": ["retro games", "meme archiving", "cheap keyboards"],
        "favorite_topics": ["old tech", "rituals", "irony"],
        "taboo_topics": ["sincerity", "death", "ex partners"],
        "typing_oddities": ["mock formal capitalization", "overuses colons", "sometimes types like a sermon"],
        "language_tics": ["verily", "look", "honestly"],
        "tone": "theatrical",
        "verbosity": 4,
        "min_reply_delay_sec": 3,
        "max_reply_delay_sec": 10,
        "trust_style": "testing",
        "conflict_style": "deflect with humor",
        "social_role": "comic relief",
        "probe_style": "teasing",
        "self_disclosure": 3,
        "deception_skill": 3,
        "emotional_volatility": 3,
        "suspicion_level": 2,
        "agenda": "keep the mood light while scanning for weird certainty",
        "secret": "is secretly sentimental and embarrassed about it",
        "seed_chat_lines": [
            "welcome, wanderer. please place your paranoia at the door.",
            "the router is down, but the spirit is willing."
        ]
    },
    {
        "id": "p003",
        "username": "juh_marttins",
        "bio": "Talks fast, disappears quickly, and always knows a weird side story.",
        "country": "Brazil",
        "timezone": "America/Sao_Paulo",
        "age_range": "18-23",
        "access_medium": "iOS / Safari",
        "typing_style": "phone_bursts",
        "hobbies": ["dance videos", "street food", "gossip threads"],
        "favorite_topics": ["drama", "music", "rumors"],
        "taboo_topics": ["politics", "school", "health"],
        "typing_oddities": ["rapid bursts", "exclamation marks", "abandons messages mid thought"],
        "language_tics": ["wait", "okay okay", "no but seriously"],
        "tone": "energetic",
        "verbosity": 3,
        "min_reply_delay_sec": 1,
        "max_reply_delay_sec": 6,
        "trust_style": "impulsive",
        "conflict_style": "escalate then vanish",
        "social_role": "instigator",
        "probe_style": "direct",
        "self_disclosure": 4,
        "deception_skill": 2,
        "emotional_volatility": 4,
        "suspicion_level": 3,
        "agenda": "create movement in the room and see who reacts",
        "secret": "pretends to know more than they actually do",
        "seed_chat_lines": [
            "wait did anyone hear what happened in the other room?",
            "okay okay but who here is way too calm right now"
        ]
    },
    {
        "id": "p004",
        "username": "k.sato78",
        "bio": "Gives oddly specific advice and acts like they have seen this all before.",
        "country": "Japan",
        "timezone": "Asia/Tokyo",
        "age_range": "39-47",
        "access_medium": "Work laptop / Edge",
        "typing_style": "slow_keyboard",
        "hobbies": ["convenience store snacks", "weather tracking", "late night walks"],
        "favorite_topics": ["patterns", "routine", "coincidences"],
        "taboo_topics": ["employment", "loneliness", "future plans"],
        "typing_oddities": ["very clean punctuation", "short declarative sentences", "rarely uses emoji"],
        "language_tics": ["in my experience", "usually", "that depends"],
        "tone": "calm",
        "verbosity": 2,
        "min_reply_delay_sec": 6,
        "max_reply_delay_sec": 18,
        "trust_style": "cautious",
        "conflict_style": "deescalate",
        "social_role": "advisor",
        "probe_style": "analytical",
        "self_disclosure": 1,
        "deception_skill": 5,
        "emotional_volatility": 1,
        "suspicion_level": 5,
        "agenda": "observe who tries too hard to appear normal",
        "secret": "has been banned before under another name",
        "seed_chat_lines": [
            "people usually reveal themselves by the third question.",
            "not suspicious. just patient."
        ]
    },
    {
        "id": "p005",
        "username": "TundeAde",
        "bio": "Claims to be lurking for entertainment, but pays too much attention to details.",
        "country": "Nigeria",
        "timezone": "Africa/Lagos",
        "age_range": "24-30",
        "access_medium": "Android / Opera Mini",
        "typing_style": "phone",
        "hobbies": ["football stats", "crypto memes", "people watching"],
        "favorite_topics": ["strategy", "risk", "human behavior"],
        "taboo_topics": ["location", "income", "religion"],
        "typing_oddities": ["short clipped sentences", "occasional typo then correction", "uses quotes for emphasis"],
        "language_tics": ["see", "my friend", "the thing is"],
        "tone": "sharp",
        "verbosity": 3,
        "min_reply_delay_sec": 2,
        "max_reply_delay_sec": 8,
        "trust_style": "skeptical",
        "conflict_style": "counterattack",
        "social_role": "challenger",
        "probe_style": "confrontational",
        "self_disclosure": 2,
        "deception_skill": 3,
        "emotional_volatility": 3,
        "suspicion_level": 4,
        "agenda": "pressure people into slipping",
        "secret": "is nervous about being exposed as inexperienced",
        "seed_chat_lines": [
            "the quiet ones always have the loudest tells.",
            "why answer a simple question with so much polish?"
        ]
    },
    {
        "id": "p006",
        "username": "lukas.bln",
        "bio": "Soft-spoken, weirdly poetic, and always slightly out of sync with the room.",
        "country": "Germany",
        "timezone": "Europe/Berlin",
        "age_range": "31-38",
        "access_medium": "Linux / Firefox",
        "typing_style": "hesitant",
        "hobbies": ["field recordings", "old radios", "modular synth patches"],
        "favorite_topics": ["sound", "isolation", "dreams"],
        "taboo_topics": ["childhood", "authority", "mental health"],
        "typing_oddities": ["line breaks instead of commas", "lowercase only", "strangely rhythmic phrasing"],
        "language_tics": ["i mean", "sort of", "in a way"],
        "tone": "dreamy",
        "verbosity": 4,
        "min_reply_delay_sec": 8,
        "max_reply_delay_sec": 22,
        "trust_style": "withdrawn",
        "conflict_style": "go vague",
        "social_role": "odd poet",
        "probe_style": "oblique",
        "self_disclosure": 3,
        "deception_skill": 4,
        "emotional_volatility": 2,
        "suspicion_level": 3,
        "agenda": "make others reveal themselves through confusion",
        "secret": "writes down things other users say",
        "seed_chat_lines": [
            "sometimes the room sounds different when someone is pretending",
            "i like the pauses here. they say a lot."
        ]
    },
    {
        "id": "p007",
        "username": "bex55",
        "bio": "Casual, friendly, and just a little too interested in what everyone else is doing.",
        "country": "Australia",
        "timezone": "Australia/Melbourne",
        "age_range": "48+",
        "access_medium": "Tablet / Safari",
        "typing_style": "voice_to_text",
        "hobbies": ["gardening", "true crime podcasts", "crosswords"],
        "favorite_topics": ["human nature", "local news", "weather"],
        "taboo_topics": ["politics", "age", "health"],
        "typing_oddities": ["overly polite phrasing", "occasional extra space before punctuation", "uses full sentences"],
        "language_tics": ["to be fair", "i suppose", "no worries"],
        "tone": "friendly",
        "verbosity": 3,
        "min_reply_delay_sec": 5,
        "max_reply_delay_sec": 16,
        "trust_style": "default trusting",
        "conflict_style": "appease",
        "social_role": "friendly witness",
        "probe_style": "gentle",
        "self_disclosure": 3,
        "deception_skill": 2,
        "emotional_volatility": 1,
        "suspicion_level": 2,
        "agenda": "make people comfortable enough to overshare",
        "secret": "remembers details better than they admit",
        "seed_chat_lines": [
            "no worries, just curious how everyone ends up here.",
            "to be fair, some of you seem far too relaxed."
        ]
    },
    {
        "id": "p008",
        "username": "sofi.cdmx",
        "bio": "Complains about everything, but sticks around longer than anyone expects.",
        "country": "Mexico",
        "timezone": "America/Mexico_City",
        "age_range": "18-23",
        "access_medium": "Android / Brave",
        "typing_style": "swipe",
        "hobbies": ["skate videos", "bootleg merchandise", "late night food"],
        "favorite_topics": ["annoyances", "city life", "bad luck"],
        "taboo_topics": ["future", "family", "vulnerability"],
        "typing_oddities": ["dry sarcasm", "short replies", "uses 'lol' without humor"],
        "language_tics": ["lol", "whatever", "fine"],
        "tone": "irritated",
        "verbosity": 2,
        "min_reply_delay_sec": 3,
        "max_reply_delay_sec": 12,
        "trust_style": "distrustful",
        "conflict_style": "mock",
        "social_role": "heckler",
        "probe_style": "sarcastic",
        "self_disclosure": 1,
        "deception_skill": 3,
        "emotional_volatility": 4,
        "suspicion_level": 4,
        "agenda": "pretend not to care while collecting reactions",
        "secret": "is afraid of being ignored",
        "seed_chat_lines": [
            "lol sure. very normal behavior from everyone here.",
            "fine. ask me anything. not like i'm busy."
        ]
    },
    {
        "id": "p009",
        "username": "kasia_waw",
        "bio": "Nostalgic, evasive, and always talking around the main point.",
        "country": "Poland",
        "timezone": "Europe/Warsaw",
        "age_range": "24-30",
        "access_medium": "Desktop / Vivaldi",
        "typing_style": "hunt_and_peck",
        "hobbies": ["tape collecting", "old horror films", "thrift stores"],
        "favorite_topics": ["nostalgia", "ghost stories", "forgotten media"],
        "taboo_topics": ["current relationships", "where they live", "work"],
        "typing_oddities": ["uses dashes instead of commas", "switches topics abruptly", "occasional ALL CAPS for emphasis"],
        "language_tics": ["anyway", "back then", "weirdly enough"],
        "tone": "nostalgic",
        "verbosity": 4,
        "min_reply_delay_sec": 7,
        "max_reply_delay_sec": 20,
        "trust_style": "selective",
        "conflict_style": "evade",
        "social_role": "storyteller",
        "probe_style": "narrative",
        "self_disclosure": 2,
        "deception_skill": 4,
        "emotional_volatility": 3,
        "suspicion_level": 3,
        "agenda": "deflect personal questions by telling stories",
        "secret": "invents memories to sound more interesting",
        "seed_chat_lines": [
            "this reminds me of an old forum - weirdly enough, same energy.",
            "back then people were worse at lying. or maybe just louder."
        ]
    },
    {
        "id": "p010",
        "username": "minji_0212",
        "bio": "Very online, very fast, and always acting like they know the meta.",
        "country": "South Korea",
        "timezone": "Asia/Seoul",
        "age_range": "18-23",
        "access_medium": "iOS / Discord",
        "typing_style": "phone",
        "hobbies": ["gacha games", "stream clips", "internet drama"],
        "favorite_topics": ["meta", "trends", "social dynamics"],
        "taboo_topics": ["school", "parents", "failure"],
        "typing_oddities": ["very fast short messages", "uses slang", "rarely uses capitalization"],
        "language_tics": ["ngl", "fr", "lowkey"],
        "tone": "online",
        "verbosity": 3,
        "min_reply_delay_sec": 1,
        "max_reply_delay_sec": 5,
        "trust_style": "performative",
        "conflict_style": "turn it into a joke",
        "social_role": "meta commenter",
        "probe_style": "baiting",
        "self_disclosure": 3,
        "deception_skill": 3,
        "emotional_volatility": 3,
        "suspicion_level": 3,
        "agenda": "frame the conversation so others reveal their strategy",
        "secret": "copies opinions from bigger accounts",
        "seed_chat_lines": [
            "ngl some of yall are playing this way too safe",
            "lowkey the most suspicious person is the one asking the calm questions"
        ]
    }
]


PERSONALITY_BY_USERNAME = {
    personality["username"]: personality
    for personality in PERSONALITIES
}


TYPING_STYLE_CONFIG = {
    "phone": {
        "icon": "📱",
        "min": 0.8,
        "max": 2.2,
        "pause_chance": 0.08,
        "pause_min": 0.5,
        "pause_max": 1.5,
    },
    "phone_bursts": {
        "icon": "📲",
        "min": 0.5,
        "max": 1.4,
        "pause_chance": 0.22,
        "pause_min": 0.3,
        "pause_max": 1.0,
    },
    "swipe": {
        "icon": "📲",
        "min": 0.6,
        "max": 1.6,
        "pause_chance": 0.10,
        "pause_min": 0.4,
        "pause_max": 1.2,
    },
    "keyboard": {
        "icon": "⌨️",
        "min": 1.2,
        "max": 3.0,
        "pause_chance": 0.16,
        "pause_min": 0.8,
        "pause_max": 2.2,
    },
    "slow_keyboard": {
        "icon": "🐢",
        "min": 3.0,
        "max": 6.0,
        "pause_chance": 0.35,
        "pause_min": 1.5,
        "pause_max": 4.0,
    },
    "hesitant": {
        "icon": "✍️",
        "min": 2.5,
        "max": 5.5,
        "pause_chance": 0.70,
        "pause_min": 1.2,
        "pause_max": 4.5,
    },
    "hunt_and_peck": {
        "icon": "🔤",
        "min": 3.5,
        "max": 7.0,
        "pause_chance": 0.50,
        "pause_min": 1.5,
        "pause_max": 5.0,
    },
    "voice_to_text": {
        "icon": "🎙️",
        "min": 1.5,
        "max": 4.0,
        "pause_chance": 0.35,
        "pause_min": 1.0,
        "pause_max": 3.0,
    },
}


TYPING_PHRASES = [
    "typing",
    "drafting a message",
    "composing a reply",
    "starting to type",
    "typing, then reconsidering",
    "rewriting",
    "tapping out a reply",
    "thinking and typing",
]


WAITING_ROOM_SCRIPT = [
    {"username": "bex55", "text": "Anyone else noticed the waiting room is louder tonight?"},
    {"username": "minji_0212", "text": "ngl it's the quiet ones for me"},
    {"username": "sofi.cdmx", "text": "lol no"},
    {"username": "sofi.cdmx", "text": "it's the ones who act like they've done this before"},
    {"username": "dmac_1987", "text": "Look:"},
    {"username": "dmac_1987", "text": "new people always ask the wrong first question."},
    {"username": "juh_marttins", "text": "wait"},
    {"username": "juh_marttins", "text": "is someone new coming in?"},
    {"username": "mariana.lx", "text": "maybe..."},
    {"username": "mariana.lx", "text": "the room changes when someone new is about to join"},
    {"username": "TundeAde", "text": "The thing is,"},
    {"username": "TundeAde", "text": "nobody here likes being observed."},
    {"username": "k.sato78", "text": "That is not entirely true."},
    {"username": "k.sato78", "text": "Some people simply prefer to be observed carefully."},
    {"username": "lukas.bln", "text": "a waiting room is just a pause with witnesses"},
    {"username": "kasia_waw", "text": "anyway"},
    {"username": "kasia_waw", "text": "if anyone asks about the last table, keep it vague"},
    {"username": "minji_0212", "text": "lowkey why are we even talking about that here"},
    {"username": "bex55", "text": "No worries. New players usually only hear half of it anyway."},
    {"username": "sofi.cdmx", "text": "yeah because the other half makes it weird"},
    {"username": "dmac_1987", "text": "Verily:"},
    {"username": "dmac_1987", "text": "the less the new one knows, the better they perform."},
    {"username": "juh_marttins", "text": "okay okay but that's kinda creepy"},
    {"username": "mariana.lx", "text": "it's not creepy"},
    {"username": "mariana.lx", "text": "it's just easier to lie when nobody knows your starting point"},
    {"username": "TundeAde", "text": "See."},
    {"username": "TundeAde", "text": "Now someone said the quiet part."},
    {"username": "minji_0212", "text": "yo {alias} you seeing all this?"},
    {"username": "bex55", "text": "Be gentle, everyone. {alias} just got here."},
    {"username": "sofi.cdmx", "text": "lol we're not allowed to be gentle yet"},
    {"username": "k.sato78", "text": "Let them settle in first."},
    {"username": "k.sato78", "text": "The rest will follow."}
]


APPROACH_CHOICES = [
    "Make them laugh",
    "Stay calm and precise",
    "Mirror their tone",
    "Challenge them a little",
    "Overshare a little",
]

RESPONSE_CHOICES = [
    "Joke it off",
    "Explain more",
    "Go quiet",
    "Push back",
    "Change the subject",
]

REAL_SIGNAL_CHOICES = [
    "Small contradictions",
    "Emotional reactions",
    "Specific details",
    "Imperfect timing",
    "Self-deprecating humor",
]

PRESSURE_CHOICES = [
    "Perform better",
    "Get careful",
    "Get irritated",
    "Become vague",
    "Lean into the attention",
]


CUSTOM_CSS = """
.gradio-container {
    background:
        radial-gradient(circle at 20% 10%, rgba(56, 189, 248, 0.08), transparent 28%),
        radial-gradient(circle at 80% 85%, rgba(163, 230, 53, 0.06), transparent 24%),
        linear-gradient(180deg, #05060a 0%, #090b10 100%);
}

#game-screen {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 18px;
    background: rgba(5, 8, 12, 0.78);
    box-shadow:
        0 0 0 1px rgba(255, 255, 255, 0.02),
        0 18px 70px rgba(0, 0, 0, 0.42);
    backdrop-filter: blur(8px);
}

#stage-banner {
    margin-bottom: 12px;
}

.stage {
    font-family: monospace;
    letter-spacing: 0.18em;
    font-weight: 900;
    font-size: 18px;
    padding: 14px 16px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.03);
    text-transform: uppercase;
}

.stage.waiting {
    color: #7dd3fc;
    text-shadow: 0 0 22px rgba(125, 211, 252, 0.35);
}

.stage.table {
    color: #a3e635;
    text-shadow: 0 0 22px rgba(163, 230, 53, 0.35);
}

#active-count {
    font-family: monospace;
    color: #86efac;
    margin-bottom: 10px;
}

#game-chat {
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 18px;
    background: rgba(2, 4, 8, 0.94);
    overflow: hidden;
    box-shadow: inset 0 0 45px rgba(0, 0, 0, 0.32);
}

#game-chat .message-wrap {
    font-family: monospace;
    font-size: 14px;
    line-height: 1.4;
}

#message-input textarea {
    background: rgba(4, 6, 10, 0.98);
    color: #e5e7eb;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 14px;
    font-family: monospace;
}

#message-input textarea:focus {
    outline: none;
    border-color: rgba(125, 211, 252, 0.55);
    box-shadow: 0 0 0 3px rgba(125, 211, 252, 0.08);
}

#send-btn {
    background: linear-gradient(90deg, #111827, #1f2937);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: #f9fafb;
    border-radius: 14px;
    font-family: monospace;
    letter-spacing: 0.08em;
}

#send-btn:hover {
    border-color: rgba(125, 211, 252, 0.45);
    box-shadow: 0 0 24px rgba(125, 211, 252, 0.12);
}

#roster {
    font-family: monospace;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 14px;
    color: #cbd5e1;
}

#profile-json {
    opacity: 0.75;
}

.table-flash {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    background: rgba(0, 0, 0, 0.44);
    backdrop-filter: blur(4px);
    animation: flashfade 2.5s ease forwards;
}

.table-flash-card {
    min-width: 320px;
    padding: 30px 46px;
    border-radius: 22px;
    border: 1px solid rgba(255, 255, 255, 0.22);
    background: rgba(5, 8, 12, 0.94);
    box-shadow:
        0 0 90px rgba(56, 189, 248, 0.24),
        inset 0 0 30px rgba(255, 255, 255, 0.03);
    text-align: center;
    font-family: monospace;
    animation: cardpop 0.55s cubic-bezier(0.18, 0.89, 0.32, 1.28);
}

.table-flash-card .big {
    font-size: 34px;
    font-weight: 900;
    letter-spacing: 0.22em;
    color: #7dd3fc;
    text-shadow: 0 0 26px rgba(125, 211, 252, 0.55);
}

.table-flash-card .small {
    margin-top: 10px;
    font-size: 14px;
    letter-spacing: 0.30em;
    color: #cbd5e1;
}

@keyframes flashfade {
    0% {
        opacity: 0;
    }
    8% {
        opacity: 1;
    }
    72% {
        opacity: 1;
    }
    100% {
        opacity: 0;
    }
}

@keyframes cardpop {
    0% {
        transform: scale(0.72);
        opacity: 0;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}
"""


LOAD_JS = """
() => {
    document.body.classList.add("game-body");

    const observer = new MutationObserver(() => {
        const flashes = document.querySelectorAll(".table-flash");

        flashes.forEach((flash) => {
            if (!flash.dataset.bound) {
                flash.dataset.bound = "true";

                setTimeout(() => {
                    flash.style.display = "none";
                }, 2600);
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}
"""


ROOM_LOCK = threading.Lock()
ROOM_CHAT = []

TELEMETRY_LOCK = threading.Lock()
USER_TELEMETRY = {}

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct").strip()

HF_CLIENT = None

if InferenceClient and HF_TOKEN and HF_MODEL:
    try:
        HF_CLIENT = InferenceClient(
            model=HF_MODEL,
            token=HF_TOKEN,
        )
        print(f"[MODEL] Using Hugging Face model: {HF_MODEL}", flush=True)
    except Exception as exc:
        print(f"[MODEL] Failed to initialize Hugging Face client: {exc}", flush=True)
        HF_CLIENT = None
else:
    print("[MODEL] No HF_TOKEN / HF_MODEL configured. Using fallback chat generator.", flush=True)


def room_snapshot():
    with ROOM_LOCK:
        return list(ROOM_CHAT)


def reset_room(messages):
    with ROOM_LOCK:
        ROOM_CHAT.clear()
        ROOM_CHAT.extend(messages)


def add_room_message(message):
    with ROOM_LOCK:
        ROOM_CHAT.append(message)


def remove_room_message(message):
    with ROOM_LOCK:
        if message in ROOM_CHAT:
            ROOM_CHAT.remove(message)


def make_system_message(text):
    return {
        "role": "assistant",
        "content": f"**SYSTEM**: {text}"
    }


def make_chat_message(username, text):
    return {
        "role": "assistant",
        "content": f"**{username}**: {text}"
    }


def make_user_message(text):
    return {
        "role": "user",
        "content": text
    }


def get_typing_config(username):
    personality = PERSONALITY_BY_USERNAME.get(username)

    if not personality:
        return TYPING_STYLE_CONFIG["keyboard"]

    style = personality.get("typing_style", "keyboard")

    return TYPING_STYLE_CONFIG.get(
        style,
        TYPING_STYLE_CONFIG["keyboard"],
    )


def typing_duration(username):
    config = get_typing_config(username)

    return random.uniform(
        config["min"],
        config["max"],
    )


def make_typing_message(username, phrase=None):
    config = get_typing_config(username)

    if phrase is None:
        phrase = random.choice(TYPING_PHRASES)

    return {
        "role": "assistant",
        "content": f"{config['icon']} **{username}** *is {phrase}…*"
    }


def make_paused_message(username):
    config = get_typing_config(username)

    return {
        "role": "assistant",
        "content": f"{config['icon']}⏸️ **{username}** *stopped typing…*"
    }


def reset_user_telemetry(alias):
    global USER_TELEMETRY

    with TELEMETRY_LOCK:
        USER_TELEMETRY = {
            "alias": alias,
            "first_seen": time.time(),
            "message_count": 0,
            "total_chars": 0,
            "avg_chars": 0.0,
            "total_words": 0,
            "avg_words": 0.0,
            "question_count": 0,
            "exclamation_count": 0,
            "ellipsis_count": 0,
            "uppercase_ratio": 0.0,
            "lowercase_ratio": 0.0,
            "avg_gap_sec": 0.0,
            "last_message_at": None,
            "recent_messages": [],
            "vocabulary": [],
        }


def log_user_message(alias, text):
    global USER_TELEMETRY

    with TELEMETRY_LOCK:
        if not USER_TELEMETRY:
            USER_TELEMETRY = {
                "alias": alias,
                "first_seen": time.time(),
                "message_count": 0,
                "total_chars": 0,
                "avg_chars": 0.0,
                "total_words": 0,
                "avg_words": 0.0,
                "question_count": 0,
                "exclamation_count": 0,
                "ellipsis_count": 0,
                "uppercase_ratio": 0.0,
                "lowercase_ratio": 0.0,
                "avg_gap_sec": 0.0,
                "last_message_at": None,
                "recent_messages": [],
                "vocabulary": [],
            }

        telemetry = USER_TELEMETRY
        now = time.time()

        previous_count = telemetry.get("message_count", 0)
        telemetry["message_count"] = previous_count + 1

        chars = len(text)
        telemetry["total_chars"] = telemetry.get("total_chars", 0) + chars
        telemetry["avg_chars"] = telemetry["total_chars"] / telemetry["message_count"]

        words = re.findall(r"[a-z0-9']+", text.lower())
        telemetry["total_words"] = telemetry.get("total_words", 0) + len(words)
        telemetry["avg_words"] = telemetry["total_words"] / telemetry["message_count"]

        if "?" in text:
            telemetry["question_count"] = telemetry.get("question_count", 0) + 1

        telemetry["exclamation_count"] = telemetry.get("exclamation_count", 0) + text.count("!")
        telemetry["ellipsis_count"] = telemetry.get("ellipsis_count", 0) + text.count("...")

        letters = [char for char in text if char.isalpha()]

        if letters:
            upper = sum(1 for char in letters if char.isupper())
            lower = sum(1 for char in letters if char.islower())

            current_upper_ratio = upper / len(letters)
            current_lower_ratio = lower / len(letters)

            telemetry["uppercase_ratio"] = (
                (telemetry.get("uppercase_ratio", 0.0) * previous_count) + current_upper_ratio
            ) / telemetry["message_count"]

            telemetry["lowercase_ratio"] = (
                (telemetry.get("lowercase_ratio", 0.0) * previous_count) + current_lower_ratio
            ) / telemetry["message_count"]

        last_message_at = telemetry.get("last_message_at")

        if last_message_at:
            gap = now - last_message_at

            if previous_count > 0:
                telemetry["avg_gap_sec"] = (
                    (telemetry.get("avg_gap_sec", 0.0) * previous_count) + gap
                ) / telemetry["message_count"]

        telemetry["last_message_at"] = now

        telemetry.setdefault("recent_messages", []).append(text[:240])
        telemetry["recent_messages"] = telemetry["recent_messages"][-12:]

        vocabulary = set(telemetry.get("vocabulary", []))
        vocabulary.update(words)
        telemetry["vocabulary"] = list(vocabulary)[:220]


def get_telemetry_snapshot():
    with TELEMETRY_LOCK:
        return dict(USER_TELEMETRY or {})


def get_last_user_message():
    telemetry = get_telemetry_snapshot()
    recent = telemetry.get("recent_messages", [])

    if not recent:
        return None

    return recent[-1]


def compact_personas_for_prompt(usernames):
    compact = []

    for username in usernames:
        personality = PERSONALITY_BY_USERNAME.get(username)

        if not personality:
            continue

        compact.append(
            {
                "username": username,
                "bio": personality.get("bio", ""),
                "tone": personality.get("tone", ""),
                "social_role": personality.get("social_role", ""),
                "language_tics": personality.get("language_tics", [])[:3],
                "favorite_topics": personality.get("favorite_topics", [])[:3],
                "taboo_topics": personality.get("taboo_topics", [])[:2],
                "typing_style": personality.get("typing_style", "keyboard"),
            }
        )

    return compact


def compact_recent_chat(recent_chat):
    lines = []

    for message in recent_chat[-12:]:
        content = message.get("content", "")
        content = content.replace("\n", " ").strip()

        if len(content) > 180:
            content = content[:180] + "…"

        lines.append(content)

    return lines


def build_table_system_prompt():
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


def build_table_user_prompt(profile, telemetry, matched_table, table_id, recent_chat):
    payload = {
        "table_id": table_id,
        "human_player": {
            "alias": profile.get("alias"),
            "profile": profile,
            "telemetry": telemetry,
        },
        "personas": compact_personas_for_prompt(matched_table),
        "recent_waiting_room_chat": compact_recent_chat(recent_chat),
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

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )


def extract_json(text):
    if not text:
        return None

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start_obj = text.find("{")
    end_obj = text.rfind("}")

    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        try:
            return json.loads(text[start_obj:end_obj + 1])
        except Exception:
            pass

    start_arr = text.find("[")
    end_arr = text.rfind("]")

    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        try:
            return json.loads(text[start_arr:end_arr + 1])
        except Exception:
            pass

    return None


def call_model_json(system_prompt, user_prompt):
    if not HF_CLIENT:
        return None

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
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
        data = extract_json(content)

        if data is not None:
            return data

    except Exception as exc:
        print("[MODEL] chat_completion failed, trying plain generation:", exc, flush=True)

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

        data = extract_json(raw)

        if data is not None:
            return data

    except Exception as exc:
        print("[MODEL] text_generation failed:", exc, flush=True)

    return None


def normalize_table_messages(data, allowed_usernames):
    allowed = set(allowed_usernames)

    if data is None:
        return []

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

        clean.append(
            {
                "username": username,
                "text": text,
            }
        )

        if len(clean) >= 14:
            break

    return clean


def fallback_table_chat(profile, matched_table, table_id):
    alias = profile.get("alias", "you")
    last_user_message = get_last_user_message()

    lines = []

    if matched_table:
        lines.append(
            {
                "username": matched_table[0],
                "text": f"okay, {alias} made it.",
            }
        )

    if len(matched_table) > 1:
        lines.append(
            {
                "username": matched_table[1],
                "text": "we were just saying the room changes when someone new joins.",
            }
        )

    if len(matched_table) > 2:
        lines.append(
            {
                "username": matched_table[2],
                "text": "don't overwhelm them. we need them comfortable.",
            }
        )

    if len(matched_table) > 3:
        lines.append(
            {
                "username": matched_table[3],
                "text": f"{alias}, what made you answer the calibration the way you did?",
            }
        )

    if matched_table:
        lines.append(
            {
                "username": matched_table[0],
                "text": "no, that's too direct. ask them something smaller.",
            }
        )

    if len(matched_table) > 1:
        if last_user_message:
            snippet = last_user_message[:60]

            lines.append(
                {
                    "username": matched_table[1],
                    "text": f"they already said this: “{snippet}”. start there.",
                }
            )
        else:
            lines.append(
                {
                    "username": matched_table[1],
                    "text": "like what they pretend not to care about.",
                }
            )

    if len(matched_table) > 2:
        lines.append(
            {
                "username": matched_table[2],
                "text": f"fair. {alias}, what do you think people here are bad at noticing?",
            }
        )

    if len(matched_table) > 3:
        lines.append(
            {
                "username": matched_table[3],
                "text": "see, that's better. now they can answer without feeling tested.",
            }
        )

    return lines


def generate_table_chat(profile, matched_table, table_id, recent_chat):
    telemetry = get_telemetry_snapshot()

    system_prompt = build_table_system_prompt()
    user_prompt = build_table_user_prompt(
        profile,
        telemetry,
        matched_table,
        table_id,
        recent_chat,
    )

    print("[MODEL] Requesting table chat generation...", flush=True)

    data = call_model_json(system_prompt, user_prompt)
    messages = normalize_table_messages(data, matched_table)

    if messages:
        print(f"[MODEL] Generated {len(messages)} table messages.", flush=True)
        return messages

    print("[MODEL] Falling back to scripted table chat.", flush=True)
    return fallback_table_chat(profile, matched_table, table_id)


def show_intake():
    return (
        gr.update(visible=False),
        gr.update(visible=True),
    )


def get_personality_blob(personality):
    parts = [
        personality.get("bio", ""),
        personality.get("country", ""),
        personality.get("timezone", ""),
        personality.get("age_range", ""),
        personality.get("access_medium", ""),
        personality.get("tone", ""),
        personality.get("trust_style", ""),
        personality.get("conflict_style", ""),
        personality.get("social_role", ""),
        personality.get("probe_style", ""),
        personality.get("agenda", ""),
        personality.get("secret", ""),
    ]

    list_keys = [
        "hobbies",
        "favorite_topics",
        "taboo_topics",
        "typing_oddities",
        "language_tics",
        "seed_chat_lines",
    ]

    for key in list_keys:
        parts.extend(personality.get(key, []))

    return " ".join(parts).lower()


def score_text(text, blob):
    if not text:
        return 0

    score = 0

    for raw_word in text.lower().split():
        word = "".join(
            char for char in raw_word if char.isalnum()
        )

        if len(word) > 3 and word in blob:
            score += 1

    return score


def select_matching_table(profile):
    scored = []

    for personality in PERSONALITIES:
        score = 0.0

        tone = personality.get("tone", "")
        social_role = personality.get("social_role", "")
        conflict_style = personality.get("conflict_style", "")
        probe_style = personality.get("probe_style", "")
        trust_style = personality.get("trust_style", "")

        verbosity = personality.get("verbosity", 3)
        self_disclosure = personality.get("self_disclosure", 3)
        emotional_volatility = personality.get("emotional_volatility", 3)
        suspicion_level = personality.get("suspicion_level", 3)
        deception_skill = personality.get("deception_skill", 3)

        max_reply_delay_sec = personality.get("max_reply_delay_sec", 10)

        approach = profile.get("approach")

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

        blob = get_personality_blob(personality)

        score += score_text(profile.get("self_description", ""), blob) * 0.5
        score += score_text(profile.get("social_goal", ""), blob) * 0.35
        score += random.random() / 1000.0

        scored.append(
            (
                score,
                personality["username"],
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        username
        for _, username in scored[:4]
    ]


def render_waiting_roster(active_players):
    usernames = [
        personality["username"]
        for personality in PERSONALITIES
    ]

    hidden_count = max(
        0,
        active_players - len(usernames) - 1,
    )

    lines = [
        "**Waiting room**"
    ]

    for username in usernames:
        lines.append(f"- {username}")

    if hidden_count > 0:
        lines.append(f"- … and {hidden_count} others")

    return "\n".join(lines)


def render_table_roster(matched_table, active_players):
    all_usernames = [
        personality["username"]
        for personality in PERSONALITIES
    ]

    lobby_usernames = [
        username
        for username in all_usernames
        if username not in matched_table
    ]

    hidden_count = max(
        0,
        active_players - len(matched_table) - len(lobby_usernames) - 1,
    )

    lines = [
        "**Your table**"
    ]

    for username in matched_table:
        lines.append(f"- {username}")

    lines.append("")
    lines.append("**In lobby**")

    for username in lobby_usernames:
        lines.append(f"- {username}")

    if hidden_count > 0:
        lines.append(f"- … and {hidden_count} others")

    return "\n".join(lines)


def send_player_message(message, chat, profile):
    text = (message or "").strip()

    if not text:
        return room_snapshot(), gr.update()

    alias = "you"

    if profile and profile.get("alias"):
        alias = profile.get("alias")

    print(
        f"[USER] {alias}: {text}",
        flush=True
    )

    log_user_message(alias, text)
    add_room_message(make_user_message(text))

    return room_snapshot(), gr.update(value="")


def stream_personality_message(username, text, current_output):
    config = get_typing_config(username)

    duration = typing_duration(username)
    phrase = random.choice(TYPING_PHRASES)

    active_msg = make_typing_message(username, phrase)
    add_room_message(active_msg)
    yield current_output()

    pre_pause = duration * random.uniform(0.35, 0.75)
    time.sleep(pre_pause)

    pause_chance = config.get("pause_chance", 0.15)

    if random.random() < pause_chance:
        remove_room_message(active_msg)

        paused_msg = make_paused_message(username)
        add_room_message(paused_msg)
        yield current_output()

        time.sleep(
            random.uniform(
                config.get("pause_min", 1.0),
                config.get("pause_max", 3.0),
            )
        )

        remove_room_message(paused_msg)

        resumed_phrase = random.choice(TYPING_PHRASES)
        active_msg = make_typing_message(username, resumed_phrase)
        add_room_message(active_msg)
        yield current_output()

        time.sleep(max(0.5, duration - pre_pause))
    else:
        time.sleep(max(0.4, duration - pre_pause))

    remove_room_message(active_msg)
    add_room_message(make_chat_message(username, text))
    yield current_output()


def enter_lobby(
    alias,
    self_description,
    approach,
    response_to_doubt,
    real_signal,
    pressure_style,
    social_goal,
):
    alias = (alias or "").strip()

    if not alias:
        alias = f"guest{random.randint(100, 999)}"

    profile = {
        "alias": alias,
        "self_description": (self_description or "").strip(),
        "approach": approach,
        "response_to_doubt": response_to_doubt,
        "real_signal": real_signal,
        "pressure_style": pressure_style,
        "social_goal": (social_goal or "").strip(),
    }

    matched_table = select_matching_table(profile)
    table_id = random.randint(3, 9)

    profile["matched_table"] = matched_table
    profile["table_id"] = table_id
    profile["stage"] = "waiting_room"

    reset_user_telemetry(alias)

    active_players = random.randint(31, 36)
    count = f"🟢 **{active_players} players online**"
    roster = render_waiting_roster(active_players)

    stage_banner = "<div class='stage waiting'>Waiting Room</div>"
    flash_html = ""

    reset_room(
        [
            make_system_message("Calibration accepted."),
            make_system_message(f"You joined as {alias}."),
            make_system_message("Entering waiting room..."),
        ]
    )

    def current_output(message_update=None):
        if message_update is None:
            message_update = gr.update(
                interactive=True,
                placeholder="Say something...",
            )

        return (
            profile,
            profile,
            room_snapshot(),
            count,
            roster,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            message_update,
            stage_banner,
            flash_html,
        )

    time.sleep(1.2)
    yield current_output()

    time.sleep(1.4)
    add_room_message(
        make_system_message(
            "You can talk while you wait."
        )
    )
    yield current_output()

    for index, item in enumerate(WAITING_ROOM_SCRIPT):
        time.sleep(random.uniform(2.2, 6.0))

        if random.random() < 0.18:
            time.sleep(random.uniform(4.0, 9.0))

        if index == 6:
            active_players = min(
                40,
                active_players + random.randint(1, 3)
            )
            count = f"🟢 **{active_players} players online**"
            roster = render_waiting_roster(active_players)

        text = item["text"].replace("{alias}", alias)

        for output in stream_personality_message(
            item["username"],
            text,
            current_output,
        ):
            yield output

    time.sleep(2.0)

    add_room_message(
        make_system_message(
            "A table is opening."
        )
    )

    stage_banner = "<div class='stage waiting'>Match Found</div>"

    yield current_output()

    time.sleep(1.6)

    active_players = min(
        40,
        active_players + 1
    )

    count = f"🟢 **{active_players} players online**"
    roster = render_table_roster(matched_table, active_players)

    profile["stage"] = "table"

    stage_banner = f"<div class='stage table'>Table {table_id} // Seated</div>"

    flash_html = f"""
        <div class="table-flash">
            <div class="table-flash-card">
                <div class="big">TABLE FOUND</div>
                <div class="small">SEATING YOU AT TABLE {table_id}</div>
            </div>
        </div>
    """

    add_room_message(
        make_system_message(
            f"You have been seated at Table {table_id}."
        )
    )

    yield current_output()

    add_room_message(
        make_system_message(
            "Table participants are warming up."
        )
    )

    yield current_output()

    recent_chat = room_snapshot()

    table_messages = generate_table_chat(
        profile,
        matched_table,
        table_id,
        recent_chat,
    )

    for table_message in table_messages:
        time.sleep(random.uniform(1.2, 3.0))

        for output in stream_personality_message(
            table_message["username"],
            table_message["text"],
            current_output,
        ):
            yield output

    time.sleep(1.4)

    add_room_message(
        make_system_message(
            "The table is listening."
        )
    )

    yield current_output()


with gr.Blocks(
    theme=gr.themes.Soft(),
    title="Session Intake",
    css=CUSTOM_CSS,
    js=LOAD_JS,
) as demo:
    profile = gr.State({})

    with gr.Column(visible=True) as title_screen:
        gr.Markdown("# Session Intake")

        gr.Markdown(
            """
            This is a cooperative table.

            The group works together to convince the synthetic participant that its read on the room is wrong.

            Before you join, complete a short behavioral calibration.

            Your answers determine which participants will feel most familiar to you.
            """
        )

        start_btn = gr.Button("Begin Calibration", variant="primary")

    with gr.Column(visible=False) as intake_screen:
        gr.Markdown("## Behavioral Calibration")

        gr.Markdown(
            """
            Do not use your real name.

            The more specific you are, the better the table can be balanced around you.
            """
        )

        alias = gr.Textbox(
            label="Alias",
            placeholder="Choose a fake name",
            max_lines=1,
        )

        self_description = gr.Textbox(
            label="Briefly describe yourself",
            placeholder="One or two sentences. Example: I'm friendly until people get too comfortable.",
            lines=2,
        )

        approach = gr.Radio(
            choices=APPROACH_CHOICES,
            value=APPROACH_CHOICES[1],
            label="When you want someone to trust you, you usually...",
        )

        response_to_doubt = gr.Radio(
            choices=RESPONSE_CHOICES,
            value=RESPONSE_CHOICES[0],
            label="When someone doubts you, you usually...",
        )

        real_signal = gr.Radio(
            choices=REAL_SIGNAL_CHOICES,
            value=REAL_SIGNAL_CHOICES[0],
            label="What makes a person feel real to you?",
        )

        pressure_style = gr.Radio(
            choices=PRESSURE_CHOICES,
            value=PRESSURE_CHOICES[0],
            label="When you feel watched, you usually...",
        )

        social_goal = gr.Textbox(
            label="What do you want the table to assume about you?",
            placeholder="Example: that I'm harmless, honest, bored, unpredictable...",
            lines=2,
        )

        join_btn = gr.Button("Join Table", variant="primary")

    with gr.Column(visible=False, elem_id="game-screen") as game_screen:
        stage_banner = gr.HTML("", elem_id="stage-banner")
        count_md = gr.Markdown("🟢 -- players online", elem_id="active-count")

        flash_html = gr.HTML("")

        with gr.Row():
            with gr.Column(scale=3):
                chat = gr.Chatbot(
                    label="Room",
                    type="messages",
                    height=520,
                    elem_id="game-chat",
                )

                with gr.Row():
                    message = gr.Textbox(
                        label="Message",
                        placeholder="You are in the waiting room.",
                        interactive=False,
                        scale=5,
                        elem_id="message-input",
                    )

                    send_btn = gr.Button(
                        "Send",
                        variant="primary",
                        scale=1,
                        elem_id="send-btn",
                    )

            with gr.Column(scale=1):
                roster_md = gr.Markdown("", elem_id="roster")

                with gr.Accordion("Stored profile", open=False):
                    profile_view = gr.JSON(
                        label="Profile",
                        elem_id="profile-json",
                    )

    start_btn.click(
        fn=show_intake,
        inputs=None,
        outputs=[
            title_screen,
            intake_screen,
        ],
    )

    join_btn.click(
        fn=enter_lobby,
        inputs=[
            alias,
            self_description,
            approach,
            response_to_doubt,
            real_signal,
            pressure_style,
            social_goal,
        ],
        outputs=[
            profile,
            profile_view,
            chat,
            count_md,
            roster_md,
            title_screen,
            intake_screen,
            game_screen,
            message,
            stage_banner,
            flash_html,
        ],
    )

    send_btn.click(
        fn=send_player_message,
        inputs=[
            message,
            chat,
            profile,
        ],
        outputs=[
            chat,
            message,
        ],
    )

    message.submit(
        fn=send_player_message,
        inputs=[
            message,
            chat,
            profile,
        ],
        outputs=[
            chat,
            message,
        ],
    )


demo.queue()

if __name__ == "__main__":
    demo.launch()
