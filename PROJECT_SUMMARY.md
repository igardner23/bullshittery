# Bullshittery

> A social game about meeting a room full of apparently ordinary players, building a team, and eventually confronting what it means to form a connection with an artificial character.

This document is the project handoff and working brief. It explains the product idea, the history of the code, the current implementation, the intended experience, known contradictions, and the questions that need answers before the next major build step.

## Contents

- [What This Project Is](#what-this-project-is)
- [The Central Experience](#the-central-experience)
- [How the Project Got Here](#how-the-project-got-here)
- [Current Reality](#current-reality)
- [Repository Map](#repository-map)
- [Runtime Architecture](#runtime-architecture)
- [Player Flow](#player-flow)
- [Personas](#personas)
- [Games and Phase State](#games-and-phase-state)
- [LLM and Prompt Harness](#llm-and-prompt-harness)
- [Telemetry, Privacy, and Consent](#telemetry-privacy-and-consent)
- [Running the Project](#running-the-project)
- [Known Problems and Technical Debt](#known-problems-and-technical-debt)
- [Recommended Continuation](#recommended-continuation)
- [Questions Requiring Direction](#questions-requiring-direction)
- [Working Agreement for Future Changes](#working-agreement-for-future-changes)

## What This Project Is

Bullshittery is a browser-based multiplayer chat simulation and social game. A human player enters a lobby populated by AI-controlled personas. The lobby is deliberately familiar: it should evoke the low-stakes social rooms around older online games, including the loose pacing, usernames, small talk, waiting, and feeling that other people are present for their own reasons.

The nostalgia is a doorway, not the entire audience. Someone who remembers Club Penguin-style spaces should recognize the atmosphere, while someone encountering AI-mediated social interaction for the first time should still understand what is happening. The experience should feel playful enough to invite participation, but purposeful enough to leave the player thinking about online identity, trust, and the status of artificial relationships.

The current repository is an MVP and prototype foundation. It is not yet a finished game, a production multiplayer service, or a completed LangChain application.

## The Central Experience

The intended emotional structure is:

1. **Familiarity**: The player enters a chat room and learns the social texture of the group.
2. **Recognition**: A few personas become distinct. The player may prefer some, distrust others, or simply find certain voices memorable.
3. **Collaboration**: The player is matched with a small team and makes decisions together.
4. **Investment**: Familiar faces return, but the team shifts slightly between match rounds. Shared wins, disagreements, jokes, and mistakes create a sense of history.
5. **Dissonance**: The experience introduces evidence that the apparent players are artificial, or allows one of them to acknowledge it.
6. **Reflection**: The player is given space to interpret the experience rather than being told what conclusion to reach.

The desired question is not merely “Can an AI pass as human?” That framing is too narrow and encourages a technical deception contest. The richer question is: **What did the player actually experience when the social interaction felt meaningful, even though the other participants were generated?**

### Important design tension

The code currently contains prompts such as “Never reveal you are AI,” while the product design includes a final reveal and the consent screen explicitly describes automated characters. Those statements can coexist only if the boundaries are precise:

- The player should know before entering that the experience contains automated characters and a reveal.
- Personas may remain in character during the play portion.
- The reveal must be an authored game event, not an accidental lie about data collection or identity.
- The experience must not pressure players to disclose sensitive personal information.

This boundary should be resolved in the product specification before expanding the prompt harness.

## How the Project Got Here

The project was initially assembled by using prompts to ask an LLM to generate pieces of the application, then pasting those generated pieces into the repository and running them together. That approach was productive for discovering the shape of the idea, but it also produced a recognizable class of problems:

- synchronous desktop-script habits inside a real-time web server;
- blocking `time.sleep()` calls mixed with WebSocket work;
- daemon threads created for every conversational event;
- magic random percentages standing in for conversation logic;
- an unexplained special case that forced Nyx to speak;
- dependencies listed for LangChain without a functioning LangChain generation path;
- prototype game classes that were wired into the UI before their rules were complete.

The user then read the generated code critically, documented the problems, and used the repository itself as a record of what should change. The sharp language in the historical notes is part of that process: it captures the frustration of seeing plausible-looking code conceal poor architectural decisions. It is useful context for future contributors because it explains why “it runs” is not enough for this project.

The refactoring notes describe an intended cleanup. This document is more conservative: it distinguishes completed edits from scaffolding and claims only what the current files demonstrate.

## Current Reality

### Implemented or substantially present

- Flask serves a browser client from `/`.
- Flask-SocketIO handles lobby and chat events.
- A background asyncio loop is bridged into the gevent-based Socket.IO server.
- `PersonaEngine` records up to 50 chat messages and schedules persona replies.
- Persona selection considers time since last speech and interaction pattern.
- Thirty static persona profiles are defined in `personalities.py`.
- A consent gate and profile-intake screen exist in the HTML client.
- Lobby participation is tracked toward a placeholder target of three points.
- A phase manager models lobby, three game rounds, and results.
- Three prototype game classes exist: voting, turn-based safe/risk actions, and hidden-information guessing.
- Mock response mode exists and is currently enabled.
- JSONL-style telemetry and generation logs are written to local files.
- A standalone priority request manager exists for future integration.
- A provider-neutral narrative prompt harness exists in `src/prompt_harness.py`.
- The active server maps lobby, bonding, escalation, and results phases into that harness.
- A narrative director now owns those stage decisions in `src/narrative_director.py`.
- The browser UI is a fixed-height, state-driven client with game-specific controls.
- Prototype games fill synthetic teammate actions server-side, so a solo player can complete a round without extra model calls.
- `llm_players.py` exposes a structured scene-batch request that can return dialogue and narrative signals in one JSON response.

### Not complete despite earlier “complete” notes

- The LangChain generation function returns `None`; it is a placeholder.
- With `TEST_MODE=True`, no real model request is made at all.
- The request manager is not connected to `PersonaEngine`.
- The application still uses synchronous model generation and `time.sleep()` in some background paths, especially prepopulation and dynamic player management.
- Game actions are only partially wired. The browser currently emits turn actions, while voting and hidden-information rounds require different action names.
- Teammate and opponent identity are mocked in the match handler.
- Dissonance/reveal orchestration is not implemented.
- Relationship scoring, reflection, and post-game messaging are not implemented.
- There is no test suite in the repository.
- Top-level modules and `src/` contain overlapping or evolving architecture and need consolidation.

## Repository Map

### Application entry points

- `app.py`: Flask application, Socket.IO handlers, global runtime state, lobby population, match transition, and prototype game actions.
- `templates/index.html`: single-page browser UI and client-side Socket.IO behavior.

### Top-level domain modules

- `persona_engine.py`: orchestration for active personas, chat history, speaker selection, delayed responses, ambient conversation, and typing simulation.
- `llm_players.py`: mock generation, prompt construction, LangChain placeholder, direct Hugging Face fallback, retry behavior, and generation logging.
- `personalities.py`: the 30 static persona dictionaries.
- `config.py`: Hugging Face settings, test mode, telemetry path, typing styles, and an unused profile generator.
- `telemetry.py`: append-only event logging to `telemetry.jsonl`.

### `src/` modules

- `src/models.py`: typed dataclasses for richer personality data, chat messages, typing configuration, and user telemetry.
- `src/game_phase.py`: session lifecycle and phase transition state.
- `src/games.py`: prototype rules for the three game types.
- `src/request_manager.py`: priority queue and bounded parallel generation scaffold.
- `src/prompt_harness.py`: shared narrative stages and provider-neutral prompt construction.
- `src/narrative_director.py`: authored event selection, phase-to-stage mapping, and final reveal authorization.
- `src/telemetry.py`: thread-safe user communication telemetry scaffold.
- `src/persona_engine.py`, `src/config.py`, and `src/ui.py`: likely part of an alternate or earlier refactoring path; their ownership should be decided before more code is added.

### Documentation and generated artifacts

- `README.md`: quick project entry point.
- `PROJECT_SUMMARY.md`: this detailed handoff document.
- `GAME_DESIGN.md`: product flow and emotional design notes.
- `REFACTORING_ROADMAP.md`: historical implementation priorities.
- `REFACTORING_COMPLETE.md`: historical summary of claimed refactoring outcomes; compare it with code before relying on it.
- `BEFORE_AFTER.md`: examples of the original anti-patterns and intended replacements.
- `void_notes.md`: free-form product thinking about nostalgia, education, and audience.
- `logs.txt`: local generation logs; may contain prompt or response content.
- `telemetry.jsonl`: local event records; may contain user-entered data.

## Runtime Architecture

The current server combines two concurrency systems:

```text
Browser
  | Socket.IO events
  v
Flask-SocketIO / gevent hub
  |
  +-- lobby, chat, phase, and game handlers
  |
  +-- PersonaEngine
        |
        +-- run_async(coroutine)
              |
              v
        dedicated asyncio event-loop thread
              |
              +-- delayed persona responses
              +-- ambient lobby sequence
              +-- typing delays
```

This bridge is a transitional design. It can keep async persona timing from blocking the Socket.IO handler, but it does not automatically make synchronous model calls non-blocking. The next architecture should choose one concurrency model deliberately and put all slow I/O behind an explicit executor or async client.

### Chat response path

1. The browser emits `chat_message` with the message text.
2. `app.py` verifies the Socket.IO session exists.
3. The message is broadcast to other clients and recorded as a participation event.
4. `PersonaEngine.handle_human_input()` records the message in its own history.
5. `_should_respond_to_human()` decides whether the room is active enough to answer.
6. `_pick_speaker()` favors personas that have been quiet longest, with an engagement multiplier for primary engagers.
7. `_delayed_response()` waits asynchronously.
8. `_simulate_and_emit()` calls generation, emits `typing_start`, waits based on typing style, records the AI message, and emits `chat_message` and `typing_stop`.
9. A follow-up may occur if the recent history contains multiple speakers and the response is substantive.

### Ambient response path

After the first player joins, the application starts `PersonaEngine._ambient_sequence()`. It sends a greeting, then runs an ambient loop. The current loop checks every 12 seconds and speaks on every other cycle. This is deterministic pacing, not a model-based decision, and it is intentionally much quieter than the original request-spam behavior.

### Global-state warning

The current application stores `human_players`, `player_sessions`, `active_games`, and one global `PersonaEngine` at module scope. That means all connected humans share the same persona room and chat history, while phase sessions are per player. That may be correct for a shared lobby, but it is not yet a complete multiplayer isolation model. A future design must explicitly decide what is room-wide and what belongs to an individual session.

### Narrative context wiring

The active server keeps phase decisions out of `PersonaEngine` through two small boundaries in `app.py`:

- `_select_team_for_session()` preserves up to two previous teammates and selects a new available face for later match rounds.
- `_update_narrative_context()` maps phase state to a `NarrativeStage` and supplies the match round, game number, team, and recent event to the engine.

The active engine stores that context and passes it to `generate_response()`. The `NarrativeDirector` supplies the authored event behind that context: opening lobby, team familiarity, competing agendas, intermission, or final dissonance. It authorizes the final dissonance only after all three match rounds are complete. Hidden round records and team history remain server-side evidence for the reveal rather than a player-facing scorecard. The actual reveal UI and post-game reflection are still missing.

## Player Flow

### 1. Consent and intake

The browser first displays a consent gate. The user must check the consent box before proceeding. The intake step asks for:

- a display name;
- an earliest gaming memory;
- an ideal teammate description;
- what the player does when things go wrong;
- one other interesting fact.

The server receives these values as `profile`, but the current prompt builder only uses a shortened version of `q1`. The other answers are logged in the join event but are not yet used to shape the experience.

### 2. Lobby

The server prepopulates ten personas in a background thread and attempts to generate eight messages. When a player joins, the remaining personas are trickled in, then the ambient engine starts. The UI shows:

- team chat;
- a player count;
- a participation progress bar;
- a lobby message explaining that matching follows participation.

The current target is three participation points. Chat messages and an explicit `participation` event can supply points. This is a placeholder calibration objective, not a finished matchmaking system.

### 3. Match and game rounds

When the target is reached, the browser emits `start_match`. The server currently creates a prototype voting game but assigns placeholder teammates (`Alpha`, `Beta`, `Gamma`) and an opponent (`OpponentAI`). A separate transition handler still contains an older hardcoded team (`Nyx`, `Marcus_T`, `Sasha.K`) and broadcasts the transition. These two paths should be unified.

### 4. Results and reveal

The phase manager can advance through three rounds to `RESULTS`, but no reveal manager currently changes persona behavior or produces the intended dissonance. The emotional climax exists in the design documents, not in the running implementation.

## Personas

Each top-level persona currently contains:

- `name`: visible chat identity;
- `persona`: short behavioral instruction;
- `style`: typing/prompt style key;
- `interaction_pattern`: broad social role;
- `trust_building`: a qualitative trust tendency.

The cast includes engagers, mentors, observers, jokers, competitive players, newcomers, complainers, casual talkers, and welcoming social connectors. The first eleven names have more detailed design discussion in `GAME_DESIGN.md`; the remaining profiles extend the room's population.

Nyx is important to the history of the project. An earlier version gave Nyx a hidden manipulation objective and forced Nyx into the conversation. That was removed because it was not requested, made the system unfairly predictable, and confused “dramatic tension” with covert manipulation. Nyx is now simply a friendly, observant, high-trust persona with a primary-engager pattern. Future drama should come from authored game structure and interpersonal consequences, not from secretly targeting the player.

### Typing styles

`config.py` defines prompt and timing behavior for `fast`, `slow`, `gen_z`, `emoji`, `formal`, and `lazy`. These settings currently influence prompt text and simulated typing duration. They do not yet cover pauses, corrections, presence indicators, or message-specific cadence.

## Games and Phase State

`src/game_phase.py` defines the intended three-round sequence:

| Phase | Prototype | Intended social signal |
| --- | --- | --- |
| Lobby | Participation objective | Communication and initial self-presentation |
| Game 1 | Voting/consensus | Cooperation and risk assessment |
| Game 2 | Turn-based safe/risk actions | Timing, strategy, and willingness to take risks |
| Game 3 | Hidden-information puzzle | Trust, communication, and information sharing |
| Results | No full implementation yet | Reveal, interpretation, and reflection |

The game classes in `src/games.py` are deliberately small prototypes:

- `VotingGame` accepts `yes`, `no`, or `abstain` and rewards complete consensus.
- `TurnBasedGame` accepts `safe` or `risk`; risk uses a random success rate of `0.6` and scores immediately.
- `HiddenInfoGame` asks players to guess `lighthouse` from three clues.

These mechanics are useful for testing state transitions, but they are not yet balanced games. They also currently use randomness in scoring and turn order, which is acceptable as a prototype mechanic but should not be confused with the conversation-logic refactor.

### State model

- `SessionState` owns one player's phase, participation, current game, game history, changing team assignments, and opponent.
- `GameState` records the current game's type, round, turns, votes, actions, clues, and result.
- `PlayerProfile` is intended to accumulate behavioral observations across rounds.
- `GamePhaseManager.advance_game()` stores behavior and moves to the next round.

The current handlers pass `behavior_notes` into `advance_game()` rather than the full `GameResult`. That is enough for basic profiling, but it loses winner, score, and player-action fields in the session history. The phase manager now keeps internal round records, including team composition, for later reveal authoring; those records are not exposed as a truthful scorecard.

## LLM and Prompt Harness

### Current modes

1. `TEST_MODE=True` returns one of eight canned responses and writes a mock generation log. This is the default and makes local UI work possible without a token or quota.
2. When test mode is disabled, `llm_players.py` builds a system prompt and chat context, attempts a LangChain path, then falls back to a direct Hugging Face router request.
3. The LangChain imports and cache scaffolding exist, but `_generate_via_langchain()` currently returns `None`. The effective non-test path is therefore the direct API fallback.

### Prompt composition

The system prompt combines:

- persona instruction;
- typing style instruction;
- short-response and tone constraints;
- the current context user, if any;
- a truncated fragment of the player's earliest gaming memory.

The last eight chat messages are formatted as plain `username: text` lines. There is no typed conversation memory, response classification, topic extraction, safety filter, or explicit game-state context yet.

`src/prompt_harness.py` now provides the first layer of the intended templated system. It defines explicit stages for lobby, team bonding, intermission, escalation, dissonance, and reflection. Each stage supplies direction about the social texture of the response, while shared boundaries prohibit dependency-building, humiliation, coercion, isolation, and attempts to make the player doubt their own perception. The harness accepts the current match round, game number, team members, recent event, authored direction, and reveal authorization.

The harness is currently an available generation primitive, not a complete narrative director. `PersonaEngine` and `app.py` still need to populate it from live phase transitions and recent game events. Until that wiring exists, generation uses the default lobby stage.

### Intended “harness and muddle” direction

The original intent was not to make every response random. It was to create a stable context harness and then selectively disturb it:

- **Stable layer**: persona identity, current phase, recent conversation, player consent boundary, and game rules.
- **Interaction layer**: whether this is a direct answer, side comment, agreement, disagreement, joke, or non-verbal reaction.
- **Muddle layer**: controlled ambiguity, imperfect recall, conflicting social cues, or a carefully authored dissonance event.
- **Output layer**: short natural chat text with a structured internal classification before display.

The muddle layer must never be allowed to override game rules, consent, privacy constraints, or the authored reveal schedule.

### Attachment without coercion

The desired early warmth can be designed as specific, reciprocal-feeling conversation: remembering a game choice, welcoming a quiet player, celebrating a team moment, or giving a character a consistent sense of humor. That is different from love bombing. The system should not flood the player with affection, imply that the persona needs them, punish disengagement, or encourage the player to replace real relationships with the game. The dramatic force should come from the later contradiction between the social surface and the hidden agendas, not from making the player emotionally dependent on the software.

## Telemetry, Privacy, and Consent

There are two telemetry paths:

- top-level `telemetry.py` appends event objects to `telemetry.jsonl`;
- `src/telemetry.py` and `src/models.py` define a richer in-memory communication tracker.

The active app uses the top-level logger for joins, leaves, and chat messages. Generation logging in `llm_players.py` writes prompts/results metadata and responses to `logs.txt`. The client tells users that chat and game actions are used to adapt the session, but the implementation currently logs raw chat text. This needs an explicit retention and deletion policy before any public deployment.

Questions the product must answer:

- Is this intended for adults only, or can minors enter?
- Which intake answers are necessary, and can each one be skipped?
- Are raw messages used only during the live session, or retained for research?
- Can a player inspect, export, or delete their session data?
- Is the reveal also a research debrief, and does it require a separate consent step?
- What happens when a player asks a persona whether it is artificial before the reveal?

The design should favor data minimization. The game can learn communication patterns without retaining intimate free-text answers indefinitely.

## Running the Project

### Prerequisites

- Python 3.10 or newer is recommended because the code uses modern type syntax.
- Install dependencies from `requirements.txt`.
- A Hugging Face token is required only when test mode is disabled.

### Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:7860` in a browser.

### Configuration

The relevant environment variables are:

- `HF_TOKEN`: Hugging Face API token.
- `HF_MODEL`: model identifier; defaults to `Qwen/Qwen2.5-7B-Instruct`.
- `TEST_MODE`: intended to control mock mode, although `config.py` currently hardcodes `TEST_MODE=True` and comments out the environment-based expression.

For local UI work, keep test mode enabled. Before testing real inference, first repair configuration precedence, add request timeouts and cancellation behavior, and verify that logs do not expose information that should remain private.

## Known Problems and Technical Debt

### Concurrency

- `PersonaEngine` uses asyncio, but generation is synchronous.
- `prepopulate_chat()` runs synchronous generation and `time.sleep()` in a daemon thread.
- `dynamic_player_manager()` also uses `time.sleep()` in a Socket.IO background task.
- There is no shutdown path for the background asyncio loop or outstanding tasks.
- The request manager has an asyncio lock but is not integrated with the engine.

### Conversation quality

- Response eligibility is a time-window check, not a semantic decision.
- Speaker selection does not actually inspect message topic or direct mentions.
- Chain responses are still based on a simple recent-speaker count.
- Mock responses are not persona-specific and are selected randomly.
- User profile answers are only minimally incorporated.
- `generate_scene_batch()` provides a one-request JSON path, but the active ambient/persona loop still uses single-response generation and does not yet consume the batch signals.

### Game correctness

- Match teams are placeholders.
- `request_table_transition` and `start_match` represent competing transition paths.
- The client offers safe/risk actions even when the server expects voting or guessing.
- The server now supplies deterministic synthetic teammate actions for the single-human prototype, avoiding an infinite wait for four browser submissions.
- Game results are broadcast broadly even though sessions are player-specific.
- Results UI does not render stored game history.

### Architecture

- Top-level and `src/` modules overlap.
- `src/models.py` describes a richer schema than the active top-level personality dictionaries use.
- `src/telemetry.py` is not the active telemetry path.
- Configuration is duplicated conceptually across modules.
- There are no unit, integration, browser, load, or contract tests.

## Recommended Continuation

Work in this order so the product does not gain more surface area than it can explain:

### 1. Establish a truthful baseline

Add a small test suite around phase transitions, game scoring, speaker selection, and the chat protocol. Run the application in test mode and document the observed event sequence. Treat this as the behavioral contract.

### 2. Choose the ownership model

Decide whether `src/` becomes the canonical package or whether the top-level modules remain canonical. Move code once, update imports, and remove duplicate paths only after tests cover the behavior.

### 3. Fix session and room boundaries

Create explicit room/session objects. Keep shared lobby chat separate from private game state. Scope Socket.IO emissions to the correct room. Make disconnect cleanup and task cancellation part of the lifecycle.

### 4. Make generation schedulable

Integrate `RequestManager` or replace it with a clearer queue abstraction. Give human-directed responses priority, bound concurrency, coalesce stale ambient work, and move blocking model calls to a bounded executor or use an async HTTP client.

### 5. Implement a real prompt harness

Use structured prompt templates and typed output for response intent. Include phase and game context. Keep the stable layer separate from the optional muddle layer. Add prompt fixtures so changes can be reviewed without relying on live model output.

### 6. Make one game round fully playable

Finish voting end to end before expanding the other rounds: render the right controls, collect human and AI actions, score once, emit a private result, and advance the state. Then repeat for the other games.

### 7. Author the reveal

Choose one reveal strategy, define the exact trigger, write post-reveal persona behavior, and test impatient, silent, hostile, and highly suspicious players. The reveal should feel earned without relying on arbitrary hidden manipulation.

### 8. Add reflection and evaluation

Build a short, optional debrief. Measure participation, abandonment, recognition timing, perceived connection, and whether the player understood the consent/reveal boundary. Do not define success as tricking every player.

## Questions Requiring Direction

These are intentionally left as questions because they change both code and experience.

### Product and audience

- Is the primary audience nostalgic players, newcomers to AI social spaces, educators, researchers, or a mixture?
- Should the game feel like a playful chat room, an art project, a classroom exercise, or a psychological experiment?
- What age rating and moderation standard should govern the lobby?
- Is “Bullshittery” the final public title, an internal title, or a tone-setting placeholder?

### Reveal and tone

- Should the reveal be direct, a subtle inconsistency, meta-commentary, or a hybrid?
- Should the post-reveal feeling be melancholic, hopeful, ambiguous, funny, or unsettling?
- Does the player learn that the characters are AI before entry, during the reveal, or both?
- Should a player who asks directly receive an in-character answer, a truthful system answer, or a phase-dependent response?
- Does the player get to interpret the connection, or does the game present a stronger thesis?

### Game structure

- Is three rounds the right length, or is one excellent round better than three thin prototypes?
- Should the player choose the game, or should matchmaking create an unexpected sequence?
- Are the teammates always the same for continuity, or remixed to test attachment and comparison?
- What makes the opposing side interesting beyond being “the AI opponent”?
- How should teammate actions be generated and explained to the player?

### Social simulation

- Is the lobby genuinely shared by multiple human players, or primarily a solo experience surrounded by personas?
- How many active personas should a player be expected to remember?
- Should every persona have a stable memory across sessions?
- What counts as natural silence, and how should the system avoid both dead air and spam?
- Which forms of conflict are acceptable, and what should moderation do with abuse?

### Technical direction

- Should the server standardize on asyncio, gevent, or a separate generation service?
- Is LangChain a real architectural requirement, or would a small prompt/transport layer be easier to maintain?
- Which model quality, latency, and cost targets matter most?
- Is batching meaningful for this workload, or is per-response prioritization enough?
- What is the minimum concurrent-player target for the first public test?

### Data and evaluation

- What data is essential to the experience?
- How long should logs live?
- Which metrics indicate emotional impact without reducing the project to deception success?
- Will players be invited to provide qualitative feedback after the reveal?
- What result would make the project educationally useful even if the player never believes the personas are human?

## Working Agreement for Future Changes

When continuing this project:

1. Read this document and `GAME_DESIGN.md` before changing the player flow.
2. Confirm behavior against the active code, not only historical refactoring notes.
3. Prefer a small testable vertical slice over another broad scaffold.
4. Keep persona behavior distinct without giving any character secret permission to manipulate the player.
5. Treat randomness as a game mechanic that must have a reason, not as a substitute for decision logic.
6. Keep the consent boundary visible in the product and in the prompt design.
7. Record unresolved product decisions here as questions instead of silently baking them into code.
8. Do not claim a subsystem is complete until its active path is tested end to end.

The project is at a useful starting point: the premise is clear, the emotional arc is promising, and the prototype exposes the right pressure points. The next meaningful milestone is not “more personas” or “more model calls.” It is one coherent, testable experience from consent through lobby, one playable game, and an authored reflection that makes the central question land.
