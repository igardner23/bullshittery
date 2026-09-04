# UI Interaction Telemetry Implementation

## Overview
Added comprehensive user interaction tracking to capture UI events client-side and store them server-side in JSONL format for LLM model consumption (e.g., Gemma).

## What Was Changed

### 1. Enhanced `src/telemetry.py`
**Added:**
- `InteractionEvent` dataclass - Structured event representation with:
  - `event_type`: click, selection, form_submit, message_send, etc.
  - `element_id`: HTML element identifier
  - `element_type`: button, input, form, roster_item, etc.
  - `timestamp` & `iso_time`: Precise timing
  - `session_id`: User session correlation
  - `user_alias`: Username
  - `context`: Event-specific metadata
  - `page_state`: Current application state (phase, game number, etc.)

- `InteractionTracker` class - Thread-safe event management:
  - Buffered writing (flushes every 50 events)
  - JSONL output to `user_interactions.jsonl`
  - Session-based filtering
  - LLM-optimized export format via `export_for_model()`

- Helper functions:
  - `log_ui_interaction()` - Log individual events
  - `flush_telemetry()` - Force flush buffered events
  - `export_session_for_model(session_id)` - Export clean JSON for LLMs

**Modified:**
- `UserTelemetry` now includes `session_id` field
- `TelemetryTracker` integrates `InteractionTracker` instance

### 2. Updated `src/models.py`
**Added:**
- `session_id: str = ""` field to `UserTelemetry` dataclass
- Updated `UserTelemetry.new()` to accept `session_id` parameter

### 3. Enhanced `templates/index.html`
**Client-side telemetry emitters added:**

```javascript
// Roster selection tracking
socket.emit('ui_interaction', {
    event_type: 'selection',
    element_id: 'roster-' + name,
    element_type: 'roster_item',
    context: { selected_user: name, purpose: 'private_message' }
});

// Profile submission
socket.emit('ui_interaction', {
    event_type: 'form_submit',
    element_id: 'enter-button',
    element_type: 'button',
    context: { step: 'profile_complete', username: state.username }
});

// Chat messages
socket.emit('ui_interaction', {
    event_type: 'message_send',
    element_id: 'chat-form',
    element_type: 'form',
    context: { message_length: text.length, phase: state.phase }
});

// Private messages
socket.emit('ui_interaction', {
    event_type: 'private_message_send',
    element_id: 'private-form',
    element_type: 'form',
    context: { recipient, message_length: text.length }
});

// Game action buttons
function trackActionClick(actionType, value, elementId) {
    socket.emit('ui_interaction', {
        event_type: 'click',
        element_id: elementId || ('action-' + actionType),
        element_type: 'button',
        context: { action: actionType, value, phase: state.phase, game_number: state.gameNumber }
    });
}
```

### 4. Updated `app.py`
**Server-side handlers:**

```python
# Import new telemetry functions
from src.telemetry import log_ui_interaction, flush_telemetry

# New Socket.IO handler for client events
@socketio.on('ui_interaction')
def handle_ui_interaction(data):
    """Handle UI interaction events from the client."""
    # Extracts event data, enriches with server-side phase info
    # Logs to JSONL file
```

**Enhanced existing handlers:**
- `handle_join()` - Initializes telemetry with session ID
- `handle_message()` - Logs chat sends with message preview
- `handle_private_message()` - Logs private message metadata
- `handle_game_action()` - Logs game button clicks with context

## Data Flow

```
User clicks button in browser
    ↓
JavaScript emits socket event 'ui_interaction'
    ↓
Server receives via @socketio.on('ui_interaction')
    ↓
Enriched with server-side phase/game state
    ↓
Passed to log_ui_interaction()
    ↓
Buffered in InteractionTracker._events list
    ↓
Auto-flushed at 50 events or on disconnect
    ↓
Written to user_interactions.jsonl as JSON lines
```

## Example JSONL Output

```json
{"event_type": "selection", "element_id": "roster-Nyx", "element_type": "roster_item", "timestamp": 1788548438.7469375, "iso_time": "2026-09-04T19:00:38.746938+00:00", "session_id": "sess_abc123", "user_alias": "PlayerOne", "context": {"selected_user": "Nyx"}, "page_state": {"phase": "lobby", "match_round": 1}}
{"event_type": "click", "element_id": "action-vote", "element_type": "button", "timestamp": 1788548445.123456, "iso_time": "2026-09-04T19:00:45.123456+00:00", "session_id": "sess_abc123", "user_alias": "PlayerOne", "context": {"action": "vote", "value": "yes", "game_type": "voting"}, "page_state": {"phase": "game", "game_number": 1, "match_round": 1}}
```

## LLM-Ready Export Format

```python
from src.telemetry import export_session_for_model

events = export_session_for_model('sess_abc123')
# Returns clean, filtered list optimized for prompt injection:
[
  {
    "time": "2026-09-04T19:00:38.746938+00:00",
    "type": "selection",
    "target": "roster-Nyx",
    "target_type": "roster_item",
    "user": "PlayerOne",
    "context": {"selected_user": "Nyx"},
    "state": {"phase": "lobby", "match_round": 1}
  }
]
```

## Usage Examples

### For Behavioral Analysis
```python
from src.telemetry import export_session_for_model

# Get all interactions for a session
events = export_session_for_model(session_id)

# Feed to Gemma/other LLM for analysis
prompt = f"""
Analyze this user's interaction pattern:
{json.dumps(events, indent=2)}

What does their behavior suggest about their play style?
"""
```

### For Real-time Adaptation
```python
# In persona engine or narrative director
from src.telemetry import get_telemetry

tracker = get_telemetry()
recent = tracker.interaction_tracker.get_recent_events(limit=10)

# Adjust persona responses based on user engagement patterns
if len([e for e in recent if e.event_type == 'message_send']) > 5:
    # User is highly engaged, increase response frequency
    pass
```

## Files Modified
1. `src/telemetry.py` - Core telemetry implementation (+230 lines)
2. `src/models.py` - Added session_id to UserTelemetry (+3 lines)
3. `templates/index.html` - Client-side event emitters (+60 lines)
4. `app.py` - Server-side handlers and integration (+50 lines)

## Testing
```bash
# Test imports
python -c "from src.telemetry import InteractionTracker; print('OK')"

# Test logging
python -c "
from src.telemetry import log_ui_interaction, flush_telemetry
log_ui_interaction('click', 'test-btn', 'button')
flush_telemetry()
print('Logged')
"

# View raw data
cat user_interactions.jsonl

# Test export
python -c "
from src.telemetry import export_session_for_model
import json
events = export_session_for_model('test_session')
print(json.dumps(events, indent=2))
"
```

## Next Steps (Not Implemented)
1. **LangChain Integration** - Create LangChain tool/loader for telemetry data
2. **JSON Schema Validation** - Add pydantic models for strict typing
3. **Aggregation Endpoints** - REST API for querying telemetry by time range, event type, etc.
4. **Real-time Dashboards** - WebSocket stream for live monitoring
5. **Privacy Controls** - Opt-out mechanisms, data retention policies
6. **Compression** - Rotate/compress old JSONL files

## Known Limitations
- No automatic session cleanup (manual intervention needed for long-running servers)
- No built-in analytics (export first, then analyze externally)
- Events not linked to specific LLM generations (would need correlation IDs)
- No hover/scroll tracking yet (only explicit interactions)
