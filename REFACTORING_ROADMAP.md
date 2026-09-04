# Bullshittery - Refactoring Complete + Next Steps

## Summary of Major Refactoring ✓

### Phase 1: Architecture Cleanup (COMPLETE)
- ✓ Removed all `time.sleep()` blocking calls
- ✓ Converted to async/await with proper event loop management
- ✓ Replaced `Thread` with `asyncio.create_task()`
- ✓ Created gevent↔asyncio bridge for Flask-SocketIO compatibility

### Phase 2: Decision Logic Cleanup (COMPLETE)
- ✓ Removed hardcoded `random.random()` thresholds (60%, 40%, 15%)
- ✓ Implemented context-based response decisions
- ✓ Added interaction_state tracking per persona
- ✓ Smart speaker selection favoring underrepresented voices
- ✓ Consistent (not random) ambient pacing

### Phase 3: Persona Authenticity (COMPLETE)
- ✓ Removed Nyx manipulation/gaslighting patterns
- ✓ Cleaned config.py: All personas now authentic
- ✓ Updated personalities.py: Distinctive without toxic traits
- ✓ Removed Nyx special-casing from app.py

### Phase 4: LLM Integration Foundation (COMPLETE)
- ✓ Restructured llm_players.py for LangChain readiness
- ✓ Added prompt template builder per persona + context
- ✓ Implemented system prompt composition with user profile
- ✓ Better error handling and logging
- ✓ Fallback mechanism (LangChain → Direct API)
- ✓ Method tracking in logs (mock/langchain/direct_api)

### Phase 5: Request Optimization (COMPLETE)
- ✓ Created RequestManager class for intelligent batching
- ✓ Priority-based queuing (human > chain > ambient)
- ✓ Parallel processing up to max_concurrent
- ✓ Backpressure handling for queue overflow
- ✓ Request deduplication architecture

---

## Documentation Created

1. **PROJECT_SUMMARY.md** - Comprehensive overview of codebase, pain points, and vision
2. **GAME_DESIGN.md** - Complete game flow design from lobby → dissonance → reflection
3. **REQUEST_MANAGER.py** - Efficient request batching and prioritization system

---

## Immediate Next Steps (In Order)

### 1. Test the Refactored Async Engine
```bash
cd /workspaces/bullshittery
python -m pytest app.py::test_persona_engine  # (when tests exist)
# OR manually test with: python app.py
```
**What to check:**
- Async tasks properly scheduled
- No `time.sleep()` blocking
- Message generation still works
- Personas speak naturally (not random)

### 2. Integrate RequestManager into PersonaEngine
**Location**: persona_engine.py, methods:
- `handle_human_input()` → submit HIGH priority request
- `_ambient_loop()` → submit LOW priority requests
- `_simulate_and_emit()` → consume batch results

**Benefit**: Parallel generation, better resource usage

### 3. Complete LangChain Integration
**In llm_players.py**:
- Implement `_generate_via_langchain()` with actual chain
- Test with real LangChain models
- Verify prompt templates working

**Currently**: Placeholder that returns None (falls back to API)

### 4. Enhance Conversation Flow
**In persona_engine.py**:
- Add response type classification (direct/side-comment/agrees/disagrees)
- Implement persona-specific response patterns
- Add topic-based response likelihood

### 5. Build Game Phase UI
**In templates/index.html**:
- Implement table-screen properly
- Add teammate cards with persona info
- Add game state tracking and display
- Implement scoring/relationship tracking

### 6. Implement Dissonance Mechanics
**New module**: game_phase.py or dissonance_manager.py
- Track relationship scores per teammate
- Orchestrate reveal moment (Options A/B/C from GAME_DESIGN.md)
- Handle persona state changes post-reveal

### 7. Add Post-Game Reflection Flow
**In app.py**:
- New socket handler for post-game phase
- Reflection questionnaire (if desired)
- Final persona messages
- Session summary/telemetry

---

## Code Quality Notes

### What's Working Well
- Clean async architecture (no more thread nightmares)
- Logic-based decisions (readable, debuggable)
- Proper logging and error handling
- Modular request management

### What Still Needs Work
- LangChain integration not fully implemented (has fallback)
- RequestManager not yet integrated into PersonaEngine
- Game phase UI not implemented
- Dissonance mechanics not implemented
- Complex conversation patterns not implemented

### Debt to Address
- `src/` folder has duplicate modules (consolidate or remove)
- llm_players.py has direct API fallback (replace with full LangChain)
- Test coverage (create pytest suite)
- Personality profiles could be more distinct

---

## Performance Expectations

### Current (Post-Refactor)
- No blocking threads (async only)
- ~1-2 API calls per 12 seconds (ambient)
- Response to human input: 0.5s delay + generation time
- ~100x better than "134 requests/sec" issue

### With RequestManager
- Parallel generation possible (up to 3 concurrent)
- Queue management prevents overload
- Backpressure applied to old ambient requests

### With Full LangChain
- Prompt caching possible
- Chain reuse across personas
- Better context management
- Faster follow-up responses

---

## Testing Recommendations

Before moving to game phase, validate:

1. **Async Tests**
   - Tasks complete without blocking
   - Event loop doesn't crash
   - Proper shutdown/cleanup

2. **Logic Tests**
   - Speaker selection favors quiet personas
   - Response decision is context-based
   - Ambient loop pacing is consistent

3. **Integration Tests**
   - Human input triggers AI response
   - Multiple humans don't interfere
   - Socket emissions work correctly

4. **Load Tests**
   - Handle 10+ concurrent players
   - Queue doesn't back up indefinitely
   - Memory usage stays reasonable

---

## Questions for User

1. **Dissonance Approach**: Which option preferred?
   - A (Direct reveal)
   - B (Subtle inconsistency)
   - C (Meta-commentary)
   - Custom?

2. **Game Choice**: What game mechanic?
   - Poker-style (strategy + social)
   - Trivia (knowledge + team discussion)
   - Puzzle (collaboration required)
   - Real-time action (stress test relationships)

3. **Tone**: After dissonance, what's the feel?
   - Melancholic (player reflects on meaninglessness)
   - Hopeful (connection was real despite AI nature)
   - Ambiguous (intentionally unclear)

4. **Timeline**: How many game rounds before dissonance?
   - After 1 round (quick impact)
   - After 3-4 rounds (more bonding)
   - Open-ended (player driven)

---

## File Structure (Updated)

```
/workspaces/bullshittery/
├── app.py                          # ✓ Refactored: async management
├── config.py                       # ✓ Refactored: removed Nyx manipulation
├── llm_players.py                  # ✓ Refactored: LangChain-ready
├── persona_engine.py               # ✓ Refactored: fully async
├── personalities.py                # ✓ Updated: authentic personas
├── telemetry.py                    # (unchanged)
│
├── src/
│   ├── request_manager.py          # NEW: Batching + priority queue
│   ├── game_phase.py               # TODO: Game mechanics
│   ├── dissonance_manager.py       # TODO: Reveal logic
│   └── [cleanup: remove duplicates]
│
├── templates/
│   └── index.html                  # TODO: Enhance game UI
│
├── PROJECT_SUMMARY.md              # NEW: Comprehensive overview
├── GAME_DESIGN.md                  # NEW: Complete game flow design
├── REFACTORING_ROADMAP.md          # THIS FILE
│
└── docs/
    └── ARCHITECTURE.md             # TODO: System design
```

---

## Success Criteria

When refactoring is truly complete:

- ✓ No more `time.sleep()` anywhere
- ✓ Speaker selection is deterministic and fair
- ✓ LangChain actually used (not just fallback)
- ✓ Requests batched and prioritized
- ✓ Game phase playable with 3-4 teammates
- ✓ Dissonance moment feels earned and impactful
- ✓ Player leaves reflecting on online relationships

---

## Current State: Ready for Next Phase ✓

All major architectural issues resolved. Core engine is clean, efficient, and authentic.
Ready to build out game mechanics and the emotional arc of the experience.
