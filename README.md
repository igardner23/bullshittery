# Session Intake

A cooperative table psychology game built with Gradio for Hugging Face Spaces.

## Overview

This is a multiplayer psychology game where users interact with AI personas in a simulated chat environment. The group works together to convince a synthetic participant that its read on the room is wrong, while actually drawing out and profiling the human player.

## Features

- **Behavioral Calibration**: Users complete a short questionnaire that determines which AI personas will feel most familiar to them
- **Dynamic Persona Matching**: 10 unique personas with distinct personalities, typing styles, and social roles
- **AI-Powered Chat**: Uses Hugging Face's Inference API (when configured) to generate contextual responses
- **Typing Simulation**: Realistic typing indicators with pauses and hesitations based on persona characteristics
- **Telemetry Tracking**: Analyzes user communication patterns including vocabulary, punctuation, and timing

## Project Structure

```
/workspace
├── app.py              # Main entry point
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── src/               # Package directory
    ├── __init__.py           # Package exports
    ├── config.py             # Static data & configuration
    ├── models.py             # Data classes
    ├── room_manager.py       # Chat room state management
    ├── telemetry.py          # User behavior tracking
    ├── persona_engine.py     # AI integration & persona matching
    └── ui.py                 # Gradio UI components
```

## Installation

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

### Hugging Face Spaces

1. Create a new Space on Hugging Face
2. Select "Gradio" as the SDK
3. Upload all files from this repository
4. (Optional) Add `HF_TOKEN` and `HF_MODEL` secrets for AI-powered responses

## Configuration

### Environment Variables

- `HF_TOKEN`: Hugging Face API token for accessing inference models
- `HF_MODEL`: Model identifier (default: `meta-llama/Meta-Llama-3.1-8B-Instruct`)

Without these variables, the app uses fallback scripted responses.

## Personas

The game includes 10 distinct personas:

| Username | Tone | Social Role | Country |
|----------|------|-------------|---------|
| mariana.lx | muted | quiet observer | Portugal |
| dmac_1987 | theatrical | comic relief | Canada |
| juh_marttins | energetic | instigator | Brazil |
| k.sato78 | calm | advisor | Japan |
| TundeAde | sharp | challenger | Nigeria |
| lukas.bln | dreamy | odd poet | Germany |
| bex55 | friendly | friendly witness | Australia |
| sofi.cdmx | irritated | heckler | Mexico |
| kasia_waw | nostalgic | storyteller | Poland |
| minji_0212 | online | meta commenter | South Korea |

## License

MIT
