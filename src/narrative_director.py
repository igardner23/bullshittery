"""Narrative stage and event selection for the social game.

The director is deliberately deterministic and small. It coordinates authored
story beats; it does not infer a player's beliefs or attempt to manipulate
emotional dependence. Hidden agendas belong to the fiction and remain server
side until the reveal is authored.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.game_phase import GamePhase, MATCH_ROUNDS
from src.prompt_harness import NarrativeContext, NarrativeStage


@dataclass(frozen=True)
class NarrativeEvent:
    """An authored beat that can guide persona dialogue."""

    event_id: str
    stage: NarrativeStage
    directive: str
    reveal_authorized: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class NarrativeDirector:
    """Translate session state into controlled narrative direction."""

    def __init__(self) -> None:
        self._events: Dict[str, NarrativeEvent] = {
            "return_to_lobby": NarrativeEvent(
                event_id="return_to_lobby",
                stage=NarrativeStage.INTERMISSION,
                directive=(
                    "Let returning teammates refer to the last set naturally. "
                    "A changed team should create curiosity, not panic."
                ),
            ),
            "team_familiarity": NarrativeEvent(
                event_id="team_familiarity",
                stage=NarrativeStage.TEAM_BONDING,
                directive=(
                    "Use a concrete shared game moment to build familiarity. "
                    "Keep warmth specific and low pressure."
                ),
            ),
            "competing_agendas": NarrativeEvent(
                event_id="competing_agendas",
                stage=NarrativeStage.ESCALATION,
                directive=(
                    "Let personas disagree about tactics and priorities. "
                    "Reveal conflicting fictional agendas through choices, not abuse."
                ),
            ),
            "final_dissonance": NarrativeEvent(
                event_id="final_dissonance",
                stage=NarrativeStage.DISSONANCE,
                directive=(
                    "Acknowledge the authored structure and the personas' hidden "
                    "agendas clearly. Invite the player to interpret what felt real."
                ),
                reveal_authorized=True,
            ),
        }

    def context_for(
        self,
        session: Any,
        recent_event: str = "",
    ) -> NarrativeContext:
        """Build prompt context from the current session without exposing secrets."""
        event = self._event_for_session(session)
        return NarrativeContext(
            stage=event.stage,
            match_round=session.match_round,
            game_number=session.game_number,
            team_members=list(session.team_players),
            recent_event=recent_event,
            authored_directive=event.directive,
            reveal_authorized=event.reveal_authorized,
        )

    def _event_for_session(self, session: Any) -> NarrativeEvent:
        """Select the authored beat for the current high-level phase."""
        if session.phase == GamePhase.RESULTS and session.completed_match_rounds >= MATCH_ROUNDS:
            return self._events["final_dissonance"]
        if session.phase == GamePhase.LOBBY and session.match_round > 1:
            return self._events["return_to_lobby"]
        if session.phase == GamePhase.GAME_1:
            return self._events["team_familiarity"]
        if session.phase in (GamePhase.GAME_2, GamePhase.GAME_3):
            return self._events["competing_agendas"]
        return NarrativeEvent(
            event_id="opening_lobby",
            stage=NarrativeStage.LOBBY,
            directive=(
                "Welcome the player into the shared room. Invite participation "
                "without pressure or excessive praise."
            ),
        )

    def reveal_payload(self, session: Any) -> Optional[Dict[str, Any]]:
        """Return a minimal reveal payload only after the full arc is complete."""
        if session.phase != GamePhase.RESULTS or session.completed_match_rounds < MATCH_ROUNDS:
            return None
        return {
            "event": "final_dissonance",
            "match_rounds_completed": session.completed_match_rounds,
            "team_history": [list(team) for team in session.team_history],
            "round_records": list(session.round_records),
        }


narrative_director = NarrativeDirector()
