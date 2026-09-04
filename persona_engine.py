import asyncio
import time
from personalities import PERSONALITIES
from llm_players import generate_response
from config import TYPING_STYLES
from src.prompt_harness import NarrativeContext


class PersonaEngine:
    """Async persona management for realistic multi-player AI chat simulation.
    
    Handles AI character interactions, response generation, and conversation flow
    without blocking thread operations. All timing uses asyncio instead of sleep.
    
    Can be used in two modes:
    - With executor: Pass a task executor to submit coroutines from non-async context
    - Without executor: Used directly in async context (will use current event loop)
    """
    
    def __init__(self, socketio, task_executor=None):
        self.socketio = socketio
        self.task_executor = task_executor  # Optional: function to submit coroutines
        self.active_profiles = []
        self.chat_history = []
        self.is_running = False
        self.user_profile = {}
        self.ambient_task = None
        self.interaction_state = {}  # Track interaction patterns per profile
        self.narrative_context = NarrativeContext()
        print("[ENGINE] Persona engine initialized (async)")

    def set_narrative_context(self, context: NarrativeContext) -> None:
        """Update the authored narrative context used by future generations."""
        self.narrative_context = context

    def _schedule_coroutine(self, coro):
        """Schedule a coroutine to run. Works with or without executor."""
        if self.task_executor:
            self.task_executor(coro)
        else:
            # Assume we're in async context, use create_task directly
            try:
                return asyncio.create_task(coro)
            except RuntimeError:
                print("[ENGINE] Warning: No event loop available and no executor provided")
                return None

    def add_profile(self, profile):
        """Add an AI profile to the active chat."""
        self.active_profiles.append(profile)
        self.interaction_state[profile['name']] = {'last_spoke': 0, 'response_count': 0}
        print(f"[ENGINE] Added profile: {profile['name']} (Total: {len(self.active_profiles)})")

    def remove_profile(self, profile):
        """Remove an AI profile from the active chat."""
        if profile in self.active_profiles:
            self.active_profiles.remove(profile)
            self.interaction_state.pop(profile['name'], None)
            print(f"[ENGINE] Removed profile: {profile['name']} (Total: {len(self.active_profiles)})")

    def record_message(self, user, text, is_ai=False):
        """Record message in chat history (max 50 recent messages)."""
        self.chat_history.append({"user": user, "text": text, "is_ai": is_ai, "ts": time.time()})
        if len(self.chat_history) > 50:
            self.chat_history = self.chat_history[-50:]
        
        msg_type = "AI" if is_ai else "Human"
        print(f"[ENGINE] Recorded {msg_type} message from {user} (History: {len(self.chat_history)} msgs)")
        
        # Update interaction tracking
        if is_ai and user in self.interaction_state:
            self.interaction_state[user]['last_spoke'] = time.time()
            self.interaction_state[user]['response_count'] += 1

    def _generate_ai_text(self, speaker, context_user=None):
        """Generate AI text without emitting socket events (for pre-population)."""
        return generate_response(
            speaker,
            self.chat_history,
            context_user,
            self.user_profile,
            narrative_context=self.narrative_context,
        )

    def handle_human_input(self, human_name, text, profile):
        """Handle incoming human message. Schedules potential AI responses."""
        self.user_profile = profile
        self.record_message(human_name, text, is_ai=False)
        
        # Decide if AI should respond based on context, not random chance
        if self._should_respond_to_human():
            # Small delay to simulate reading/thinking (1.5-3.0 seconds is realistic)
            delay = self._calculate_response_delay()
            print(f"[ENGINE] Scheduling AI response in {delay:.1f}s...")
            self._schedule_coroutine(self._delayed_response(delay, human_name))
        else:
            print(f"[ENGINE] No AI response triggered (context check or no active profiles)")

    def _should_respond_to_human(self):
        """Decide if AI should respond based on context, not pure randomness.
        
        Logic:
        - Always respond if human directed message to specific AI
        - Respond if chat has been quiet for a while (encourage engagement)
        - Respond if active profiles exist
        """
        if not self.active_profiles:
            return False
        
        # Check if chat was recently active (if not, respond to encourage engagement)
        if len(self.chat_history) >= 2:
            last_msg_time = self.chat_history[-1]['ts']
            time_since_last = time.time() - last_msg_time
            # If it's been >3 seconds since last message, respond (realistic conversation)
            return time_since_last < 60  # Keep responding within a 60-second window
        
        return True

    def _calculate_response_delay(self):
        """Calculate realistic response delay based on persona typing speed and message length.
        
        Simulates human reading time (0.5-1.5s) + typing time.
        """
        # Small thinking delay (0.5-1.0s for reading)
        return 0.5

    async def _delayed_response(self, delay, trigger_user):
        """Wait, then trigger AI response."""
        await asyncio.sleep(delay)
        
        if not self.active_profiles:
            print(f"[ENGINE] No active profiles for delayed response")
            return
        
        speaker = self._pick_speaker(trigger_user)
        print(f"[ENGINE] Delayed response triggered. Speaker: {speaker['name']}")
        await self._simulate_and_emit(speaker, trigger_user)

    def _pick_speaker(self, trigger_user=None):
        """Select which AI persona should speak next based on interaction patterns.
        
        Replaces hardcoded randomness with logic-based selection:
        - Favor personas that haven't spoken recently
        - Consider interaction patterns (primary_engager vs observer)
        - Ensure variety in who speaks
        """
        if not self.active_profiles:
            return None
        
        # Sort by time since last spoke (prefer quieter voices)
        current_time = time.time()
        profiles_with_quiet_score = []
        
        for profile in self.active_profiles:
            state = self.interaction_state.get(profile['name'], {})
            time_since_spoke = current_time - state.get('last_spoke', 0)
            
            # Favor "primary_engager" types to be more active
            engagement_bonus = 2.0 if profile.get('interaction_pattern') == 'primary_engager' else 1.0
            quiet_score = time_since_spoke * engagement_bonus
            
            profiles_with_quiet_score.append((profile, quiet_score))
        
        # Pick the profile with highest quiet score (hasn't spoken in longest)
        speaker = max(profiles_with_quiet_score, key=lambda x: x[1])[0]
        print(f"[ENGINE] Speaker selected: {speaker['name']} (interaction: {speaker.get('interaction_pattern', 'unknown')})")
        return speaker

    async def _simulate_and_emit(self, speaker, context_user=None):
        """Generate response and emit to all clients with realistic typing simulation."""
        print(f"\n[TYPE] {speaker['name']} starting to type...")
        print(f"[TYPE] Context user: {context_user}")
        print(f"[TYPE] User profile available: {bool(self.user_profile)}")
        
        text = self._generate_ai_text(speaker, context_user)
        
        if not text or text == "...":
            print(f"[TYPE] No valid response generated, skipping")
            return

        style = TYPING_STYLES.get(speaker.get('style', 'lazy'), TYPING_STYLES['lazy'])
        typing_time = max(1.0, len(text) * style['ms_per_char'] / 1000.0)
        
        print(f"[TYPE] Generated text: '{text}'")
        print(f"[TYPE] Typing duration: {typing_time:.1f}s (Style: {speaker.get('style', 'lazy')})")

        self.socketio.emit('typing_start', {
            'user': speaker['name'],
            'style': speaker.get('style', 'lazy'),
        })
        await asyncio.sleep(typing_time)

        self.record_message(speaker['name'], text, is_ai=True)
        self.socketio.emit('chat_message', {'user': speaker['name'], 'text': text})
        self.socketio.emit('typing_stop', {'user': speaker['name']})
        
        print(f"[TYPE] {speaker['name']} finished typing and sent message\n")
        
        # Potential follow-up response (natural conversation flow)
        # Only if >1 other persona exists and message is substantive
        if len(self.active_profiles) > 1 and len(text) > 10:
            should_chain = self._should_trigger_chain_response()
            if should_chain:
                print(f"[TYPE] Natural follow-up triggered")
                await asyncio.sleep(0.8)  # Brief pause before follow-up
                await self._chain_response(speaker)

    def _should_trigger_chain_response(self):
        """Decide if another persona should chime in (natural conversation).
        
        Replace hardcoded 15% with context logic.
        """
        # Look at recent messages - if substantive discussion, maybe someone responds
        if len(self.chat_history) < 3:
            return False
        
        # Check if last few messages are from different people (active conversation)
        recent = self.chat_history[-3:]
        unique_speakers = len(set(m['user'] for m in recent))
        
        # Follow-up more likely if conversation is active (3+ different people talking)
        return unique_speakers >= 2

    async def _chain_response(self, first_speaker):
        """Natural follow-up response from another persona."""
        others = [p for p in self.active_profiles if p['name'] != first_speaker['name']]
        if others:
            # Pick based on who hasn't spoken, not random
            speaker = self._pick_speaker(first_speaker['name'])
            if speaker and speaker['name'] != first_speaker['name']:
                print(f"[CHAIN] Follow-up from {speaker['name']}")
                await self._simulate_and_emit(speaker)

    def start_ambient_loop(self, initial_user, profile):
        """Start the ambient chat loop (pre-game socializing).
        
        Note: This is sync but schedules async tasks. Caller must have asyncio loop ready.
        """
        if self.is_running:
            print("[AMBIENT] Loop already running, skipping")
            return
        
        self.is_running = True
        self.user_profile = profile
        
        print(f"\n[AMBIENT] Starting ambient loop for user: {initial_user}")
        print(f"[AMBIENT] User profile: {profile}\n")
        
        # Schedule the async sequence as a task
        self._schedule_coroutine(self._ambient_sequence(initial_user))

    async def _ambient_sequence(self, initial_user):
        """Orchestrate initial greeting + ambient loop concurrently."""
        # Initial greeting after 2 seconds
        await asyncio.sleep(2.0)
        print(f"[AMBIENT] Sending initial greeting to {initial_user}")
        speaker = self._pick_speaker(initial_user)
        if speaker:
            await self._simulate_and_emit(speaker, initial_user)
        
        # Then start ambient loop
        await self._ambient_loop()

    async def _ambient_loop(self):
        """Generate ambient chat while idle (realistic lobby socializing).
        
        Key change: Reduced frequency + intelligent speaker selection.
        Instead of ~134 req/sec, aim for 1 message every 10-15 seconds.
        """
        cycle = 0
        while self.is_running:
            cycle += 1
            
            if self.active_profiles:
                # More natural: not random, but based on engagement patterns
                should_speak = self._should_ambient_speak(cycle)
                
                if should_speak:
                    speaker = self._pick_speaker()
                    if speaker:
                        print(f"[AMBIENT] Cycle {cycle}: {speaker['name']} speaking")
                        await self._simulate_and_emit(speaker)
                else:
                    print(f"[AMBIENT] Cycle {cycle}: Silent (natural pausing)")
            else:
                print(f"[AMBIENT] Cycle {cycle}: No profiles to speak")
            
            # Realistic delay: 10-18 seconds between ambient messages (not 8-15 random)
            await asyncio.sleep(self._calculate_ambient_delay())

    def _should_ambient_speak(self, cycle):
        """Decide if someone should speak during ambient loop.
        
        Replace hardcoded 40% random with pattern-based logic.
        """
        # Roughly every other cycle, someone speaks (not pure random)
        # Can be influenced by engagement level if needed
        return cycle % 2 == 0

    def _calculate_ambient_delay(self):
        """Consistent ambient delay (more predictable than random)."""
        return 12  # 12 seconds between potential messages

    def stop_ambient_loop(self):
        """Stop the ambient chat loop."""
        if self.is_running:
            self.is_running = False
            if self.ambient_task:
                self.ambient_task.cancel()
            print("[AMBIENT] Ambient loop stopped")