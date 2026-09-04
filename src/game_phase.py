"""Session and match progression for the shared social game.

A session contains one three-round match. Each match round contains the same
    three game types, followed by a real return to the shared lobby. The team
    remains familiar but can change slightly between match rounds.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


PLACEHOLDER_LOBBY_TARGET = 3
MATCH_ROUNDS = 3
GAMES_PER_MATCH_ROUND = 3
GAME_TYPES = ("voting", "turn_based", "hidden_info")


class GamePhase(Enum):
    """High-level stages of the player's journey."""

    LOBBY = "lobby"  # Shared social room and intermission between match rounds
    GAME_1 = "game_1"  # Voting / consensus
    GAME_2 = "game_2"  # Turn-based cooperation
    GAME_3 = "game_3"  # Hidden information
    RESULTS = "results"  # Final reveal and reflection


@dataclass
class GameState:
    """State of one game inside a match round."""

    game_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    game_type: str = ""
    round_number: int = 0  # Game number within the current match round.
    current_turn: Optional[int] = None
    turn_order: List[str] = field(default_factory=list)
    votes: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    clues: List[str] = field(default_factory=list)
    puzzle_state: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


@dataclass
class PlayerProfile:
    """Behavioral observations collected across the match."""

    player_id: str
    session_id: str
    initial_messages: List[str] = field(default_factory=list)
    risk_profile: Optional[str] = None
    communication_style: Optional[str] = None
    decision_speed: Optional[str] = None
    cooperation_level: Optional[float] = None
    game_1_behavior: Optional[Dict[str, Any]] = None
    game_2_behavior: Optional[Dict[str, Any]] = None
    game_3_behavior: Optional[Dict[str, Any]] = None


@dataclass
class SessionState:
    """State for one player across the full three-round match.

    ``match_round`` identifies the larger social arc. ``game_number``
    identifies the current game within that arc. Returning to ``LOBBY`` after
    game three is intentional: familiar faces remain visible, while the team
    can shift slightly before the next set begins.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str = ""
    phase: GamePhase = GamePhase.LOBBY
    match_round: int = 1
    game_number: int = 0
    completed_match_rounds: int = 0
    lobby_duration_seconds: int = 0
    participation_points: int = 0
    participation_target: int = PLACEHOLDER_LOBBY_TARGET
    match_ready: bool = False
    participation_events: List[Dict[str, Any]] = field(default_factory=list)
    objective_state: Dict[str, Any] = field(default_factory=lambda: {
        "name": "lobby_participation",
        "status": "collecting",
        "intermission": False,
    })
    player_profile: Optional[PlayerProfile] = None
    current_game: Optional[GameState] = None
    game_history: List[GameState] = field(default_factory=list)
    round_records: List[Dict[str, Any]] = field(default_factory=list)
    team_players: List[str] = field(default_factory=list)
    team_history: List[List[str]] = field(default_factory=list)
    opponent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    matched_at: Optional[datetime] = None


class GamePhaseManager:
    """Create sessions and enforce match/lobby transitions."""

    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}

    def create_session(self, player_id: str) -> SessionState:
        """Create a new player session in the first lobby."""
        session = SessionState(player_id=player_id)
        session.player_profile = PlayerProfile(
            player_id=player_id,
            session_id=session.session_id,
        )
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve an active session."""
        return self.sessions.get(session_id)

    def record_participation(
        self,
        session_id: str,
        points: int = 1,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SessionState]:
        """Record a signal toward the current lobby objective."""
        session = self.get_session(session_id)
        if not session or session.phase != GamePhase.LOBBY:
            return session

        awarded_points = max(points, 0)
        session.participation_events.append({
            "source": source,
            "points": awarded_points,
            "metadata": metadata or {},
            "recorded_at": datetime.now().isoformat(),
        })
        session.participation_points = min(
            session.participation_target,
            session.participation_points + awarded_points,
        )
        session.match_ready = session.participation_points >= session.participation_target
        session.objective_state["status"] = (
            "ready" if session.match_ready else "collecting"
        )
        return session

    def match_player(
        self,
        session_id: str,
        team_players: List[str],
        opponent_id: str,
    ) -> Optional[SessionState]:
        """Start the next three-game set after a lobby intermission.

        The caller supplies the team for each match round. Most members should
        usually return, but a small change keeps the social room alive and
        creates room for new agendas to emerge.
        """
        session = self.get_session(session_id)
        if not session or session.phase != GamePhase.LOBBY:
            return session
        if not 1 <= session.match_round <= MATCH_ROUNDS:
            return session

        session.phase = GamePhase.GAME_1
        session.game_number = 1
        if team_players:
            session.team_players = list(team_players)
        if session.team_players != (session.team_history[-1] if session.team_history else []):
            session.team_history.append(list(session.team_players))
        session.opponent_id = opponent_id or session.opponent_id
        session.matched_at = datetime.now()
        session.objective_state["intermission"] = False
        session.current_game = GameState(
            game_type=GAME_TYPES[0],
            round_number=1,
            started_at=datetime.now(),
        )
        return session

    def advance_game(
        self,
        session_id: str,
        game_result: Dict[str, Any],
    ) -> Optional[SessionState]:
        """Store a result and move to the next game or shared lobby."""
        session = self.get_session(session_id)
        if not session or not session.current_game:
            return session

        current_game = session.current_game
        current_game.result = game_result
        current_game.ended_at = datetime.now()
        session.game_history.append(current_game)

        if session.player_profile:
            behavior = game_result.get("behavior", {})
            if current_game.round_number == 1:
                session.player_profile.game_1_behavior = behavior
            elif current_game.round_number == 2:
                session.player_profile.game_2_behavior = behavior
            elif current_game.round_number == 3:
                session.player_profile.game_3_behavior = behavior

        if session.phase == GamePhase.GAME_1:
            session.phase = GamePhase.GAME_2
            session.game_number = 2
            session.current_game = GameState(
                game_type=GAME_TYPES[1],
                round_number=2,
                started_at=datetime.now(),
            )
        elif session.phase == GamePhase.GAME_2:
            session.phase = GamePhase.GAME_3
            session.game_number = 3
            session.current_game = GameState(
                game_type=GAME_TYPES[2],
                round_number=3,
                started_at=datetime.now(),
            )
        elif session.phase == GamePhase.GAME_3:
            self._complete_match_round(session)

        return session

    def _complete_match_round(self, session: SessionState) -> None:
        """Record an interim round or finish the full match."""
        completed_games = session.game_history[-GAMES_PER_MATCH_ROUND:]
        # Keep this internal. It is evidence for the eventual reveal, not a
        # truthful performance score promised to the player.
        session.round_records.append({
            "match_round": session.match_round,
            "games": [
                {
                    "round": game.round_number,
                    "game_type": game.game_type,
                    "result": game.result,
                }
                for game in completed_games
            ],
            "team_players": list(session.team_players),
            "opponent_id": session.opponent_id,
        })
        session.completed_match_rounds = session.match_round
        session.current_game = None
        session.game_number = 0

        if session.match_round >= MATCH_ROUNDS:
            session.phase = GamePhase.RESULTS
            return

        # Return to the shared social room with familiar faces and a changed team.
        session.match_round += 1
        session.phase = GamePhase.LOBBY
        session.participation_points = 0
        session.match_ready = False
        session.objective_state = {
            "name": "lobby_participation",
            "status": "collecting",
            "match_round": session.match_round,
            "intermission": True,
            "familiar_team": list(session.team_players),
            "team_history": [list(team) for team in session.team_history],
        }

    def get_phase_info(self, session_id: str) -> Dict[str, Any]:
        """Return serializable phase state for the browser."""
        session = self.get_session(session_id)
        if not session:
            return {"phase": "unknown"}

        info: Dict[str, Any] = {
            "phase": session.phase.value,
            "session_id": session.session_id,
            "player_id": session.player_id,
            "participation": session.participation_points,
            "participation_target": session.participation_target,
            "match_ready": session.match_ready,
            "objective": session.objective_state,
            "match_round": session.match_round,
            "game_number": session.game_number,
            "completed_match_rounds": session.completed_match_rounds,
            "team_players": session.team_players,
            "opponent_id": session.opponent_id,
        }

        if session.current_game:
            info.update({
                "game_type": session.current_game.game_type,
                "round_number": session.current_game.round_number,
                "game_id": session.current_game.game_id,
            })

        if session.phase == GamePhase.RESULTS:
            info["game_history"] = [
                {
                    "round": game.round_number,
                    "game_type": game.game_type,
                    "result": game.result,
                }
                for game in session.game_history
            ]

        return info


phase_manager = GamePhaseManager()
