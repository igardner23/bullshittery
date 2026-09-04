from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect
import random
import time
import asyncio
import threading

from personalities import PERSONALITIES
from persona_engine import PersonaEngine
from telemetry import log_event
from src.game_phase import phase_manager, GamePhase
from src.narrative_director import narrative_director
from src.round_telemetry import round_telemetry
from src.games import create_game, VotingGame, TurnBasedGame, HiddenInfoGame

TEST_MODE = True
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Asyncio event loop for persona engine (runs in separate thread)
_event_loop = None
_loop_thread = None

def _get_event_loop():
    """Get or create the asyncio event loop for the persona engine."""
    global _event_loop, _loop_thread
    
    if _event_loop is None:
        _event_loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(target=_event_loop.run_forever, daemon=True)
        _loop_thread.start()
        print("[APP] Asyncio event loop started in background thread")
    
    return _event_loop

def run_async(coro):
    """Submit a coroutine to the persona engine's event loop and return a future."""
    loop = _get_event_loop()
    return asyncio.run_coroutine_threadsafe(coro, loop)

# Initialize engine with the task executor
engine = PersonaEngine(socketio, task_executor=run_async)
human_players = {}
trickle_started = False
dynamic_manager_started = False

# Track player sessions and active games
player_sessions = {}  # sid -> session_id
active_games = {}  # game_id -> game object


def _select_team_for_session(session):
    """Keep most familiar teammates while changing one face per match round."""
    available = [profile['name'] for profile in engine.active_profiles]
    if not session.team_players:
        return available[:3] or ['Nyx', 'Marcus_T', 'Sasha.K']

    retained = [name for name in session.team_players if name in available][:2]
    newcomers = [name for name in available if name not in session.team_players]
    return retained + newcomers[:max(0, 3 - len(retained))]


def _room_roster():
    """Return backwards-compatible names plus typed active-user metadata."""
    users = (
        [{'name': player['username'], 'kind': 'human'} for player in human_players.values()]
        + [{'name': profile['name'], 'kind': 'persona'} for profile in engine.active_profiles]
    )
    return {
        'players': [user['name'] for user in users],
        'users': users,
        'count': len(users),
    }


async def _send_private_persona_reply(sender_sid, sender_name, persona, text):
    """Generate a private persona reply away from the Socket.IO handler."""
    response = await asyncio.to_thread(
        engine._generate_ai_text,
        persona,
        sender_name,
    )
    if response and response != '...':
        socketio.emit('private_message', {
            'sender': persona['name'],
            'recipient': sender_name,
            'text': response,
        }, to=sender_sid)


def _complete_synthetic_actions(game, session, human_name, action, value):
    """Fill teammate actions for the single-human prototype table.

    These are deliberately deterministic placeholders. They make the game
    playable without spending an LLM request per synthetic teammate.
    """
    participants = [human_name] + [name for name in session.team_players if name != human_name]
    synthetic_names = participants[1:4]

    if isinstance(game, VotingGame):
        opposing_vote = 'no' if value == 'yes' else 'yes'
        for index, name in enumerate(synthetic_names):
            game.submit_vote(name, value if index != 1 else opposing_vote)
    elif isinstance(game, TurnBasedGame):
        for index, name in enumerate(synthetic_names):
            game.submit_action(name, 'risk' if index == session.match_round % 3 else 'safe')
    elif isinstance(game, HiddenInfoGame):
        for index, name in enumerate(synthetic_names):
            game.submit_guess(name, 'lighthouse' if index == 0 else 'harbor')


def _update_narrative_context(session, recent_event=''):
    """Apply the director's authored context to future persona messages."""
    engine.set_narrative_context(
        narrative_director.context_for(session, recent_event)
    )


def _finish_game_transition(session, result, recent_event):
    """Advance the session and publish its next playable state."""
    completed_round = (
        session.match_round
        if session.current_game and session.current_game.round_number == 3
        else None
    )
    phase_manager.advance_game(session.session_id, result)
    if completed_round is not None:
        round_telemetry.flush_round(session.session_id, completed_round)
    _update_narrative_context(session, recent_event)

    if session.current_game:
        active_games[session.current_game.game_id] = create_game(
            session.current_game.game_type,
            session.current_game.game_id,
            session.current_game.round_number,
        )

    socketio.emit('phase_update', phase_manager.get_phase_info(session.session_id))


def prepopulate_chat():
    """Generate initial ambient chat (no async calls, just message recording)."""
    print("\n[PREPOP] Starting pre-population of chat...")
    
    # Add first 10 personalities
    for profile_data in PERSONALITIES[:10]:
        engine.add_profile(profile_data)
        print(f"[PREPOP] Added {profile_data['name']}")
    
    # Generate ~8 messages over 40 seconds (realistic pacing, not spammy)
    messages_generated = 0
    start_time = time.time()
    
    while time.time() - start_time < 40 and messages_generated < 8:
        if engine.active_profiles:
            speaker = engine._pick_speaker()
            if speaker:
                # Generate response without context (no player yet)
                text = engine._generate_ai_text(speaker, None)
                
                if text and text != "...":
                    engine.record_message(speaker['name'], text, is_ai=True)
                    messages_generated += 1
                    print(f"[PREPOP] Generated message {messages_generated}/8 from {speaker['name']}: '{text}'")
        
        # Wait 4-6 seconds between messages (realistic)
        time.sleep(4.0 if TEST_MODE else random.uniform(4.0, 6.0))
    
    print(f"[PREPOP] Pre-population complete. Generated {messages_generated} messages")


@app.route('/')
def index():
    print("[APP] Root route accessed")
    return render_template('index.html')

@socketio.on('join_lobby')
def handle_join(data):
    global trickle_started, dynamic_manager_started

    if data.get('consent_given') is not True:
        emit('consent_required', {'message': 'Consent is required before entering the lobby.'})
        return
    
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
        'profile': profile,
        'consent_given': True
    }

    session = phase_manager.create_session(username)
    player_sessions[request.sid] = session.session_id
    round_telemetry.start_session(session.session_id, username)
    _update_narrative_context(session)
    emit('phase_update', phase_manager.get_phase_info(session.session_id))
    
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
    
    socketio.emit('player_update', _room_roster())
    emit('message', {'user': 'System', 'text': f'{username} entered the lobby.'}, broadcast=True)
    
    print(f"[JOIN] Sending {len(engine.chat_history[-20:])} recent messages to {username}")
    for msg in engine.chat_history[-20:]:
        emit('chat_message', {'user': msg['user'], 'text': msg['text']}, broadcast=True)
    
    if not trickle_started:
        trickle_started = True
        print(f"\n[TRICKLE] Starting additional AI population...")
        
        def trickle_remaining():
            # Add remaining 10 personalities
            for i, profile_data in enumerate(PERSONALITIES[10:20]):
                time.sleep(0.05 if TEST_MODE else random.uniform(0.3, 0.8))
                engine.add_profile(profile_data)
                socketio.emit('player_update', _room_roster())
                
                # Announce joins for a few select personalities (not everyone, not Nyx-biased)
                if random.random() < 0.2:  # Random 20% of them announce
                    socketio.emit('message', {'user': 'System', 'text': f"{profile_data['name']} joined."})
                
                if (i + 1) % 5 == 0:
                    print(f"[TRICKLE] Added {i + 1}/10 additional AI profiles")
            
            print(f"[TRICKLE] All 20 AI profiles added. Starting ambient loop and dynamic manager...")
            # Start the async ambient loop (this returns None, starts async task internally)
            engine.start_ambient_loop(username, profile)
            
            if not dynamic_manager_started:
                dynamic_manager_started = True
                socketio.start_background_task(dynamic_player_manager)
            
        socketio.start_background_task(trickle_remaining)


@socketio.on('request_table_transition')
def handle_table_transition(data):
    username = data.get('username')
    print(f"\n[TRANSITION] Triggering table transition for {username}")
    
    # Hardcoded teammates for Phase 1 testing
    teammates = ["Nyx", "Marcus_T", "Sasha.K"]
    opponent = "The Architect"
    
    print(f"[TRANSITION] Sending transition payload: teammates={teammates}, opponent={opponent}")
    
    socketio.emit('transition_to_table', {
        'teammates': teammates,
        'opponent': opponent
    }) # Or just to the user, but broadcast is fine for now


@socketio.on('participation')
def handle_participation(data=None):
    """Update lobby participation and open matching when the target is reached."""
    session_id = player_sessions.get(request.sid)
    session = phase_manager.record_participation(session_id, source='manual') if session_id else None
    if not session:
        return

    emit('participation_update', {
        'participation': session.participation_points,
        'participation_target': session.participation_target,
        'match_ready': session.match_ready,
    })
    if session.match_ready:
        emit('ready_to_match', {'message': 'Your lobby session is ready.'})


@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in human_players:
        user_data = human_players.pop(request.sid)
        name = user_data['username']
        print(f"\n[LEAVE] Player disconnected: {name}")
        print(f"[LEAVE] Remaining humans: {len(human_players)}")
        
        log_event('human_leave', {'user': name, 'sid': request.sid})
        socketio.emit('player_update', _room_roster())
        socketio.emit('message', {'user': 'System', 'text': f'{name} left the lobby.'})

@socketio.on('chat_message')
def handle_message(msg):
    user_data = human_players.get(request.sid)
    if not user_data:
        print(f"[CHAT] Warning: Message from unknown session {request.sid}")
        return
    
    username = user_data['username']
    text = msg['text']
    
    print(f"[CHAT] Human message from {username}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
    
    socketio.emit('chat_message', {'user': username, 'text': text}, include_self=False)
    session_id = player_sessions.get(request.sid)
    if session_id:
        round_telemetry.record(session_id, 'chat_message', chat_length=len(text))
    session = phase_manager.record_participation(
        session_id,
        source='chat_message',
        metadata={'length': len(text)},
    ) if session_id else None
    if session:
        emit('participation_update', {
            'participation': session.participation_points,
            'participation_target': session.participation_target,
            'match_ready': session.match_ready,
            'objective': session.objective_state,
        })
        if session.match_ready:
            emit('ready_to_match', {'message': 'Your lobby session is ready.'})
    log_event('human_message', {'user': username, 'text': text})
    
    print(f"[CHAT] Handing off to persona engine for AI reactions...")
    engine.handle_human_input(username, text, user_data['profile'])


@socketio.on('private_message')
def handle_private_message(data):
    """Deliver a private message to another connected human player."""
    sender = human_players.get(request.sid)
    recipient_name = str(data.get('recipient', '')).strip()
    text = str(data.get('text', '')).strip()
    if not sender or not recipient_name or not text:
        emit('private_message_error', {'message': 'Choose a player and enter a message.'})
        return

    recipient_sid = next(
        (
            sid for sid, player in human_players.items()
            if player['username'] == recipient_name
        ),
        None,
    )
    if not recipient_sid:
        persona = next(
            (profile for profile in engine.active_profiles if profile['name'] == recipient_name),
            None,
        )
        if not persona:
            emit('private_message_error', {'message': 'That player is no longer connected.'})
            return
        emit('private_message', {
            'sender': sender['username'],
            'recipient': recipient_name,
            'text': text[:500],
        })
        run_async(_send_private_persona_reply(
            request.sid,
            sender['username'],
            persona,
            text[:500],
        ))
        return

    payload = {
        'sender': sender['username'],
        'recipient': recipient_name,
        'text': text[:500],
    }
    socketio.emit('private_message', payload, to=recipient_sid)
    emit('private_message', payload)
    log_event('private_message', {
        'sender': sender['username'],
        'recipient': recipient_name,
        'text': text[:500],
    })

def dynamic_player_manager():
    print(f"\n[DYNAMIC] Starting dynamic player manager...")
    
    available_profiles = PERSONALITIES[20:]
# Game Phase Handlers

@socketio.on('start_match')
def handle_start_match(data):
    """Player is matched and transitioning to game"""
    user_sid = request.sid
    username = human_players.get(user_sid, {}).get('username', 'Unknown')
    
    print(f"\n[MATCH] Starting match for {username}")
    
    session_id = player_sessions.get(user_sid)
    session = phase_manager.get_session(session_id) if session_id else None
    if not session or not session.match_ready or not human_players.get(user_sid, {}).get('consent_given'):
        emit('match_unavailable', {'message': 'More lobby participation is required before matching.'})
        return
    
    team_players = _select_team_for_session(session)
    opponent_id = "The Computer"
    
    # Match player
    phase_manager.match_player(session.session_id, team_players, opponent_id)
    _update_narrative_context(
        session,
        recent_event=f"Match round {session.match_round} is beginning with the current team.",
    )
    
    # Send phase update to client
    phase_info = phase_manager.get_phase_info(session.session_id)
    
    emit('phase_update', {
        'phase': 'game_1',
        'session_id': session.session_id,
        'game_type': 'voting',
        'round_number': 1,
        'team_players': team_players,
        'opponent_id': opponent_id,
        'team_score': 0,
        'prompt': 'Should we take the risk or play it safe?'
    })
    
    # Create the first game
    game = create_game('voting', session.current_game.game_id, 1)
    active_games[session.current_game.game_id] = game

@socketio.on('submit_game_action')
def handle_game_action(data):
    """Player submits an action in the current game"""
    user_sid = request.sid
    session_id = player_sessions.get(user_sid)
    
    if not session_id:
        print(f"[GAME] Warning: No session for user {user_sid}")
        return
    
    session = phase_manager.get_session(session_id)
    if not session or not session.current_game:
        print(f"[GAME] No active game for session {session_id}")
        return
    
    action = data.get('action')
    value = data.get('value')
    username = human_players.get(user_sid, {}).get('username', 'Unknown')
    
    print(f"[GAME] {username} submitted action: {action}={value}")
    round_telemetry.record(session_id, 'game_action', action=f'{action}:{value}')
    
    game = active_games.get(session.current_game.game_id)
    if not game:
        print(f"[GAME] Game {session.current_game.game_id} not found")
        return
    
    # Handle based on game type
    if isinstance(game, VotingGame):
        if action == 'vote':
            if not game.submit_vote(username, value):
                emit('game_error', {'message': 'Choose yes, no, or abstain.'})
                return
            _complete_synthetic_actions(game, session, username, action, value)
            if len(game.votes) >= 4:  # Team + opponent
                result = game.tally_votes()
                _finish_game_transition(
                    session,
                    {'behavior': result.behavior_notes, 'result': result.__dict__},
                    'The team completed a voting round.',
                )
                emit('game_result', {
                    'round': result.round_number,
                    'won': result.won,
                    'team_score': result.team_score
                }, broadcast=True)
    
    elif isinstance(game, TurnBasedGame):
        if action == 'turn_action':
            if not game.submit_action(username, value):
                emit('game_error', {'message': 'Choose safe or risk.'})
                return
            _complete_synthetic_actions(game, session, username, action, value)
            if len(game.actions) >= 4:  # All players acted
                result = game.complete_game()
                _finish_game_transition(
                    session,
                    {'behavior': result.behavior_notes, 'result': result.__dict__},
                    'The team completed a turn-based round.',
                )
                emit('game_result', {
                    'round': result.round_number,
                    'won': result.won,
                    'team_score': result.team_score
                }, broadcast=True)
    
    elif isinstance(game, HiddenInfoGame):
        if action == 'guess':
            if not value:
                emit('game_error', {'message': 'Enter a guess first.'})
                return
            game.submit_guess(username, value)
            _complete_synthetic_actions(game, session, username, action, value)
            if len(game.guesses) >= 4:  # All players guessed
                result = game.check_answers()
                _finish_game_transition(
                    session,
                    {'behavior': result.behavior_notes, 'result': result.__dict__},
                    'The team completed a hidden-information round.',
                )
                emit('game_result', {
                    'round': result.round_number,
                    'won': result.won,
                    'team_score': result.team_score
                }, broadcast=True)
    
def dynamic_player_manager():
    print(f"\n[DYNAMIC] Starting dynamic player manager...")
    
    available_profiles = PERSONALITIES[20:]
    cycle = 0
    while True:
        time.sleep(15)
        cycle += 1
        
        current_count = len(engine.active_profiles)
        print(f"\n[DYNAMIC] Cycle {cycle}: Current AI count: {current_count}")
        
        if current_count >= 39:
            print(f"[DYNAMIC] Max capacity reached (39), stopping dynamic management")
            break
        
        removable = [p for p in engine.active_profiles if p['name'] != 'Nyx']
        if removable:
            leaving = random.choice(removable)
            engine.remove_profile(leaving)
            print(f"[DYNAMIC] {leaving['name']} left the lobby")
            
            socketio.emit('player_update', _room_roster())
            socketio.emit('message', {'user': 'System', 'text': f"{leaving['name']} left."})
        
        for _ in range(2):
            if available_profiles and len(engine.active_profiles) < 39:
                new_profile = available_profiles.pop(0)
                engine.add_profile(new_profile)
                print(f"[DYNAMIC] {new_profile['name']} joined the lobby")
                
                socketio.emit('player_update', _room_roster())
                socketio.emit('message', {'user': 'System', 'text': f"{new_profile['name']} joined."})
                
                time.sleep(random.uniform(0.5, 1.5))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("STARTING SERVER")
    print(f"Host: 0.0.0.0:7860")
    print(f"Async mode: gevent")
    print(f"Total AI personalities: {len(PERSONALITIES)}")
    print(f"Pre-population: 60 seconds of idle chat")
    print(f"Initial load: 20 players")
    print(f"Dynamic management: 1 leaves, 2 join every 15s (max 39)")
    print("="*60 + "\n")
    
    # Model generation and time.sleep are synchronous; keep them off the gevent hub.
    threading.Thread(target=prepopulate_chat, name='prepopulate-chat', daemon=True).start()
    
    socketio.run(app, host='0.0.0.0', port=7860, debug=False)