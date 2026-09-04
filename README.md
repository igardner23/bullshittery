# Bullshittery

Bullshittery is a prototype social game in which a human player enters a chat lobby populated by AI personas, forms a team, plays cooperative games, and encounters an authored reveal about the nature of the other participants.

This repository is both an implementation and a record of the design process. It began as code generated in response to prompts and pasted into the project, then became an exercise in identifying and correcting the architectural habits that generated code often hides: blocking sleeps in a real-time server, unexplained randomness, duplicated modules, incomplete framework integrations, and prototype mechanics presented as finished behavior.

## Start Here

- [Project Summary](PROJECT_SUMMARY.md): authoritative handoff, current implementation status, architecture, product intent, open questions, and continuation plan.
- [Game Design](GAME_DESIGN.md): intended lobby, game, dissonance, and reflection arc.
- [Refactoring Roadmap](REFACTORING_ROADMAP.md): historical priorities and proposed next steps.
- [Before and After](BEFORE_AFTER.md): examples of the original anti-patterns and their intended replacements.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:7860`. The application currently runs in mock generation mode, so a Hugging Face token is not required for the basic UI flow.

## Status

The Flask/Socket.IO lobby, persona engine scaffold, phase manager, prototype game classes, consent screen, and local telemetry are present. LangChain generation, request-manager integration, complete game UI, reveal mechanics, reflection, and automated tests remain unfinished. See the [current reality](PROJECT_SUMMARY.md#current-reality) section for the detailed status.

The central design question is: **what does it mean for an online connection to feel meaningful when the other participant is artificial?** The project uses a familiar game-lobby atmosphere to make that question accessible to both nostalgic players and people new to AI-mediated social interaction.