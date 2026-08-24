"""
Session Intake - A cooperative table psychology game.

This is the main entry point for the Gradio application.
All logic has been refactored into the src package.
"""

from src.ui import create_ui, CUSTOM_CSS, LOAD_JS

# Create the UI
demo = create_ui()

# Enable queuing for streaming responses
demo.queue()

if __name__ == "__main__":
    demo.launch(
        theme="soft",
        css=CUSTOM_CSS,
        js=LOAD_JS,
    )
