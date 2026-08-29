"""
User interface components for the Session Intake application.

This module contains all Gradio UI components, CSS styling, and event handlers
for the web application interface.
"""

import random
import time
from typing import Any

import gradio as gr

from src.config import (
    APPROACH_CHOICES,
    PRESSURE_CHOICES,
    REAL_SIGNAL_CHOICES,
    RESPONSE_CHOICES,
    WAITING_ROOM_SCRIPT,
)
from src.models import ChatMessage
from src.room_manager import add_room_message, remove_room_message, reset_room, room_snapshot
from src.telemetry import log_user_message, reset_user_telemetry
from src.persona_engine import (
    generate_table_chat,
    get_typing_config,
    make_paused_message,
    make_typing_message,
    select_matching_table,
    typing_duration,
)


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
    0% { opacity: 0; }
    8% { opacity: 1; }
    72% { opacity: 1; }
    100% { opacity: 0; }
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


def render_waiting_roster(active_players: int) -> str:
    """Render the waiting room roster."""
    from src.config import PERSONALITIES
    
    usernames = [p["username"] for p in PERSONALITIES]
    hidden_count = max(0, active_players - len(usernames) - 1)
    
    lines = ["**Waiting room**"]
    for username in usernames:
        lines.append(f"- {username}")
    
    if hidden_count > 0:
        lines.append(f"- … and {hidden_count} others")
    
    return "\n".join(lines)


def render_table_roster(matched_table: list[str], active_players: int) -> str:
    """Render the table roster with lobby players."""
    from src.config import PERSONALITIES
    
    all_usernames = [p["username"] for p in PERSONALITIES]
    lobby_usernames = [u for u in all_usernames if u not in matched_table]
    hidden_count = max(0, active_players - len(matched_table) - len(lobby_usernames) - 1)
    
    lines = ["**Your table**"]
    for username in matched_table:
        lines.append(f"- {username}")
    
    lines.append("")
    lines.append("**In lobby**")
    
    for username in lobby_usernames:
        lines.append(f"- {username}")
    
    if hidden_count > 0:
        lines.append(f"- … and {hidden_count} others")
    
    return "\n".join(lines)


def send_player_message(
    message: str,
    chat: list[dict],
    profile: dict[str, Any],
) -> tuple[list[dict], gr.components.base.Component]:
    """Handle user sending a message."""
    text = (message or "").strip()
    
    if not text:
        return room_snapshot(), gr.update()
    
    alias = profile.get("alias", "you") if profile else "you"
    
    print(f"[USER] {alias}: {text}", flush=True)
    log_user_message(alias, text)
    add_room_message(ChatMessage.user(text).to_dict())
    
    return room_snapshot(), gr.update(value="")


def stream_personality_message(
    username: str,
    text: str,
    current_output: callable,
) -> Any:
    """Stream a personality message with typing simulation."""
    config = get_typing_config(username)
    duration = typing_duration(username)
    phrase = random.choice(["typing", "drafting a message", "composing a reply"])
    
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
        
        time.sleep(random.uniform(config.get("pause_min", 1.0), config.get("pause_max", 3.0)))
        
        remove_room_message(paused_msg)
        
        resumed_phrase = random.choice(["typing", "rewriting", "tapping out a reply"])
        active_msg = make_typing_message(username, resumed_phrase)
        add_room_message(active_msg)
        yield current_output()
        
        time.sleep(max(0.5, duration - pre_pause))
    else:
        time.sleep(max(0.4, duration - pre_pause))
    
    remove_room_message(active_msg)
    add_room_message(ChatMessage.chat(username, text).to_dict())
    yield current_output()


def enter_lobby(
    alias: str,
    self_description: str,
    approach: str,
    response_to_doubt: str,
    real_signal: str,
    pressure_style: str,
    social_goal: str,
):
    """Handle user entering the lobby and game flow."""
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
    
    reset_room([
        ChatMessage.system("Calibration accepted.").to_dict(),
        ChatMessage.system(f"You joined as {alias}.").to_dict(),
        ChatMessage.system("Entering waiting room...").to_dict(),
    ])
    
    def current_output(message_update: gr.Update | None = None):
        if message_update is None:
            message_update = gr.update(interactive=True, placeholder="Say something...")
        
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
    add_room_message(ChatMessage.system("You can talk while you wait.").to_dict())
    yield current_output()
    
    for index, item in enumerate(WAITING_ROOM_SCRIPT):
        time.sleep(random.uniform(2.2, 6.0))
        
        if random.random() < 0.18:
            time.sleep(random.uniform(4.0, 9.0))
        
        if index == 6:
            active_players = min(40, active_players + random.randint(1, 3))
            count = f"🟢 **{active_players} players online**"
            roster = render_waiting_roster(active_players)
        
        text = item["text"].replace("{alias}", alias)
        
        for output in stream_personality_message(item["username"], text, current_output):
            yield output
    
    time.sleep(2.0)
    add_room_message(ChatMessage.system("A table is opening.").to_dict())
    
    stage_banner = "<div class='stage waiting'>Match Found</div>"
    yield current_output()
    
    time.sleep(1.6)
    active_players = min(40, active_players + 1)
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
    
    add_room_message(ChatMessage.system(f"You have been seated at Table {table_id}.").to_dict())
    yield current_output()
    
    add_room_message(ChatMessage.system("Table participants are warming up.").to_dict())
    yield current_output()
    
    recent_chat = room_snapshot()
    table_messages = generate_table_chat(profile, matched_table, table_id, recent_chat)
    
    for table_message in table_messages:
        time.sleep(random.uniform(1.2, 3.0))
        
        for output in stream_personality_message(
            table_message["username"],
            table_message["text"],
            current_output,
        ):
            yield output
    
    time.sleep(1.4)
    add_room_message(ChatMessage.system("The table is listening.").to_dict())
    yield current_output()


def show_intake():
    """Transition from title screen to intake form."""
    return gr.update(visible=False), gr.update(visible=True)


def create_ui() -> gr.Blocks:
    """Create and configure the Gradio UI."""
    
    with gr.Blocks(
        title="Session Intake",
    ) as demo:
        profile = gr.State({})
        
        # Title Screen
        with gr.Column(visible=True) as title_screen:
            gr.Markdown("# Session Intake")
            gr.Markdown("""
            This is a cooperative table.
            
            The group works together to convince the synthetic participant that its read on the room is wrong.
            
            Before you join, complete a short behavioral calibration.
            
            Your answers determine which participants will feel most familiar to you.
            """)
            start_btn = gr.Button("Begin Calibration", variant="primary")
        
        # Intake Screen
        with gr.Column(visible=False) as intake_screen:
            gr.Markdown("## Behavioral Calibration")
            gr.Markdown("""
            Do not use your real name.
            
            The more specific you are, the better the table can be balanced around you.
            """)
            
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
        
        # Game Screen
        with gr.Column(visible=False, elem_id="game-screen") as game_screen:
            stage_banner = gr.HTML("", elem_id="stage-banner")
            count_md = gr.Markdown("🟢 -- players online", elem_id="active-count")
            flash_html = gr.HTML("")
            
            with gr.Row():
                with gr.Column(scale=3):
                    chat = gr.Chatbot(
                        label="Room",
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
                        send_btn = gr.Button("Send", variant="primary", scale=1, elem_id="send-btn")
                
                with gr.Column(scale=1):
                    roster_md = gr.Markdown("", elem_id="roster")
                    
                    with gr.Accordion("Stored profile", open=False):
                        profile_view = gr.JSON(label="Profile", elem_id="profile-json")
        
        # Event handlers
        start_btn.click(
            fn=show_intake,
            inputs=None,
            outputs=[title_screen, intake_screen],
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
            inputs=[message, chat, profile],
            outputs=[chat, message],
        )
        
        message.submit(
            fn=send_player_message,
            inputs=[message, chat, profile],
            outputs=[chat, message],
        )
    
    return demo
