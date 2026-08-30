from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect
import random
import time

from personalities import PERSONALITIES
from persona_engine import PersonaEngine
from telemetry import log_event

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

engine = PersonaEngine(socketio)
human_players = {}
trickle_started = False
dynamic_manager_started = False

@app.route('/')
def index():
    print("[APP] Root route accessed")
    return render_template('index.html')

@socketio.on('join_lobby')
def handle_join(data):
    global trickle_started, dynamic_manager_started
    
    username = data.get('username', '').strip() or f'Anon_{random.randint(100,999)}'
    profile = data.get('profile', {})
    
    print(f"\n{'='*60}")
    print(f"[JOIN] New player: {username}")
    print(f"[JOIN] Profile data: {profile}")
    print(f"[JOIN] Session ID: {request.sid}")
    print(f"[JOIN] Current human count: {len(human_players) + 1}")
    print(f"{'='*60}\n")
    
    human_players[request.sid] = {
        'username': username,
        'profile': profile
    }
    
    log_event('human_join', {
        'user': username, 
        'sid': request.sid,
        'goal': profile.get('goal'),
        'style': profile.get('style'),
        'q1': profile.get('q1'),
        'q2': profile.get('q2'),
        'q3': profile.get('q3'),
        'q4': profile.get('q4')
    })
    
    all_names = [p['username'] for p in human_players.values()] + [p['name'] for p in engine.active_profiles]
    emit('player_update', {'players': all_names, 'count': len(all_names)})
    emit('message', {'user': 'System', 'text': f'{username} entered the lobby.'}, )
    
    print(f"[JOIN] Sending {len(engine.chat_history[-20:])} recent messages to {username}")
    for msg in engine.chat_history[-20:]:
        emit('chat_message', {'user': msg['user'], 'text': msg['text']}, )
    
    if not trickle_started:
        trickle_started = True
        print(f"\n[TRICKLE] Starting initial AI population (20 players)...")
        
        def initial_trickle():
            # Add first 20 personalities
            for i, profile_data in enumerate(PERSONALITIES[:20]):
                time.sleep(random.uniform(0.3, 0.8))
                engine.add_profile(profile_data)
                names = [p['username'] for p in human_players.values()] + [p['name'] for p in engine.active_profiles]
                socketio.emit('player_update', {'players': names, 'count': len(names)}, )
                
                if profile_data['name'] == 'Nyx' or random.random() < 0.3:
                    socketio.emit('message', {'user': 'System', 'text': f"{profile_data['name']} joined."}, )
                
                if (i + 1) % 5 == 0:
                    print(f"[TRICKLE] Added {i + 1}/20 initial AI profiles")
            
            print(f"[TRICKLE] Initial 20 AI profiles added. Starting ambient loop and dynamic manager...")
            engine.start_ambient_loop(username, profile)
            
            # Start dynamic player management
            if not dynamic_manager_started:
                dynamic_manager_started = True
                socketio.start_background_task(dynamic_player_manager)
            
        socketio.start_background_task(initial_trickle)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in human_players:
        user_data = human_players.pop(request.sid)
        name = user_data['username']
        print(f"\n[LEAVE] Player disconnected: {name}")
        print(f"[LEAVE] Remaining humans: {len(human_players)}")
        
        log_event('human_leave', {'user': name, 'sid': request.sid})
        all_names = [p['username'] for p in human_players.values()] + [p['name'] for p in engine.active_profiles]
        emit('player_update', {'players': all_names, 'count': len(all_names)}, )
        emit('message', {'user': 'System', 'text': f'{name} left the lobby.'}, )


@socketio.on('chat_message')
def handle_message(msg):
    user_data = human_players.get(request.sid)
    if not user_data:
        print(f"[CHAT] Warning: Message from unknown session {request.sid}")
        return
    
    username = user_data['username']
    text = msg['text']
    
    print(f"[CHAT] Human message from {username}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
    
    # Broadcast to everyone EXCEPT the sender (they already rendered it optimistically)
    socketio.emit('chat_message', {'user': username, 'text': text}, include_self=False)
    log_event('human_message', {'user': username, 'text': text})
    
    print(f"[CHAT] Handing off to persona engine for AI reactions...")
    engine.handle_human_input(username, text, user_data['profile'])

def dynamic_player_manager():
    """Manages dynamic player flow: 1 leaves, 2 join every 15 seconds until 39 total."""
    print(f"\n[DYNAMIC] Starting dynamic player manager...")
    
    available_profiles = PERSONALITIES[20:]  # Profiles not yet added
    cycle = 0
    
    while True:
        time.sleep(15)
        cycle += 1
        
        current_count = len(engine.active_profiles)
        print(f"\n[DYNAMIC] Cycle {cycle}: Current AI count: {current_count}")
        
        if current_count >= 39:
            print(f"[DYNAMIC] Max capacity reached (39), stopping dynamic management")
            break
        
        # Remove 1 random player (not Nyx)
        removable = [p for p in engine.active_profiles if p['name'] != 'Nyx']
        if removable:
            leaving = random.choice(removable)
            engine.remove_profile(leaving)
            print(f"[DYNAMIC] {leaving['name']} left the lobby")
            
            names = [p['username'] for p in human_players.values()] + [p['name'] for p in engine.active_profiles]
            socketio.emit('player_update', {'players': names, 'count': len(names)}, )
            socketio.emit('message', {'user': 'System', 'text': f"{leaving['name']} left."}, )
        
        # Add 2 new players
        for _ in range(2):
            if available_profiles and len(engine.active_profiles) < 39:
                new_profile = available_profiles.pop(0)
                engine.add_profile(new_profile)
                print(f"[DYNAMIC] {new_profile['name']} joined the lobby")
                
                names = [p['username'] for p in human_players.values()] + [p['name'] for p in engine.active_profiles]
                socketio.emit('player_update', {'players': names, 'count': len(names)}, )
                socketio.emit('message', {'user': 'System', 'text': f"{new_profile['name']} joined."}, )
                
                time.sleep(random.uniform(0.5, 1.5))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("STARTING SERVER")
    print(f"Host: 0.0.0.0:7860")
    print(f"Async mode: gevent")
    print(f"Total AI personalities: {len(PERSONALITIES)}")
    print(f"Initial load: 20 players")
    print(f"Dynamic management: 1 leaves, 2 join every 15s (max 39)")
    print("="*60 + "\n")
    socketio.run(app, host='0.0.0.0', port=7860, debug=False)