import random
import time
from threading import Thread
from personalities import PERSONALITIES
from llm_players import generate_response
from config import TYPING_STYLES

class PersonaEngine:
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_profiles = []
        self.chat_history = []
        self.is_running = False
        self.user_profile = {}
        print("[ENGINE] Persona engine initialized")

    def add_profile(self, profile):
        self.active_profiles.append(profile)
        print(f"[ENGINE] Added profile: {profile['name']} (Total: {len(self.active_profiles)})")

    def remove_profile(self, profile):
        if profile in self.active_profiles:
            self.active_profiles.remove(profile)
            print(f"[ENGINE] Removed profile: {profile['name']} (Total: {len(self.active_profiles)})")

    def record_message(self, user, text, is_ai=False):
        self.chat_history.append({"user": user, "text": text, "is_ai": is_ai, "ts": time.time()})
        if len(self.chat_history) > 50:
            self.chat_history = self.chat_history[-50:]
        
        msg_type = "AI" if is_ai else "Human"
        print(f"[ENGINE] Recorded {msg_type} message from {user} (History: {len(self.chat_history)} msgs)")

    def handle_human_input(self, human_name, text, profile):
        self.user_profile = profile
        self.record_message(human_name, text, is_ai=False)
        
        if random.random() < 0.6 and self.active_profiles:
            delay = random.uniform(1.5, 4.0)
            print(f"[ENGINE] Scheduling AI response in {delay:.1f}s...")
            Thread(target=self._delayed_response, args=(delay, human_name), daemon=True).start()
        else:
            print(f"[ENGINE] No AI response triggered (random chance or no active profiles)")

    def _delayed_response(self, delay, trigger_user):
        time.sleep(delay)
        if not self.active_profiles:
            print(f"[ENGINE] No active profiles for delayed response")
            return
        speaker = self._pick_speaker(trigger_user)
        print(f"[ENGINE] Delayed response triggered. Speaker: {speaker['name']}")
        self._simulate_and_emit(speaker, trigger_user)

    def _pick_speaker(self, trigger_user=None):
        nyx = next((p for p in self.active_profiles if p['name'] == 'Nyx'), None)
        if nyx and random.random() < 0.4:
            print(f"[ENGINE] Nyx selected to speak (40% chance)")
            return nyx
        speaker = random.choice(self.active_profiles)
        print(f"[ENGINE] Random speaker selected: {speaker['name']}")
        return speaker

    def _simulate_and_emit(self, speaker, context_user=None):
        print(f"\n[TYPE] {speaker['name']} starting to type...")
        print(f"[TYPE] Context user: {context_user}")
        print(f"[TYPE] User profile available: {bool(self.user_profile)}")
        
        text = generate_response(speaker, self.chat_history, context_user, self.user_profile)
        
        if not text or text == "...":
            print(f"[TYPE] No valid response generated, skipping")
            return

        style = TYPING_STYLES.get(speaker['style'], TYPING_STYLES['lazy'])
        typing_time = max(1.0, len(text) * style['ms_per_char'] / 1000.0)
        
        print(f"[TYPE] Generated text: '{text}'")
        print(f"[TYPE] Typing duration: {typing_time:.1f}s (Style: {speaker['style']})")

        self.socketio.emit('typing_start', {'user': speaker['name']}, )
        time.sleep(typing_time)

        self.record_message(speaker['name'], text, is_ai=True)
        self.socketio.emit('chat_message', {'user': speaker['name'], 'text': text}, )
        self.socketio.emit('typing_stop', {'user': speaker['name']}, )
        
        print(f"[TYPE] {speaker['name']} finished typing and sent message\n")

        if random.random() < 0.15 and len(self.active_profiles) > 1:
            print(f"[TYPE] 15% chance triggered - scheduling chain response")
            Thread(target=self._chain_response, args=(speaker,), daemon=True).start()

    def _chain_response(self, first_speaker):
        time.sleep(random.uniform(2.0, 5.0))
        others = [p for p in self.active_profiles if p['name'] != first_speaker['name']]
        if others:
            speaker = random.choice(others)
            print(f"[CHAIN] Chain response from {speaker['name']}")
            self._simulate_and_emit(speaker)

    def start_ambient_loop(self, initial_user, profile):
        if self.is_running:
            print("[AMBIENT] Loop already running, skipping")
            return
        self.is_running = True
        self.user_profile = profile
        
        print(f"\n[AMBIENT] Starting ambient loop for user: {initial_user}")
        print(f"[AMBIENT] User profile: {profile}\n")
        
        Thread(target=self._initial_greeting, args=(initial_user,), daemon=True).start()
        Thread(target=self._ambient_loop, daemon=True).start()

    def _initial_greeting(self, initial_user):
        time.sleep(2.0)
        print(f"[AMBIENT] Sending initial greeting to {initial_user}")
        speaker = self._pick_speaker(initial_user)
        self._simulate_and_emit(speaker, initial_user)

    def _ambient_loop(self):
        cycle = 0
        while self.is_running:
            cycle += 1
            if self.active_profiles and random.random() < 0.4:
                speaker = random.choice(self.active_profiles)
                print(f"[AMBIENT] Cycle {cycle}: {speaker['name']} speaking")
                self._simulate_and_emit(speaker)
            else:
                print(f"[AMBIENT] Cycle {cycle}: Silent (40% chance or no profiles)")
            time.sleep(random.uniform(8.0, 15.0))