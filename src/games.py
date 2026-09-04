"""
Placeholder game mechanics for A/B/C rounds
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import random


@dataclass
class GameResult:
    """Result of a completed game"""
    round_number: int
    game_type: str
    won: bool
    team_score: int
    opponent_score: int
    player_actions: Dict[str, Any]  # What the player did
    behavior_notes: Dict[str, Any]  # Observations for profiling


class VotingGame:
    """Game A: Voting/consensus mechanic - test cooperation and risk assessment"""

    def __init__(self, game_id: str, round_number: int = 1):
        self.game_id = game_id
        self.round_number = round_number
        self.votes = {}  # player_id -> vote
        self.proposal = "Should the team invest heavily in this opportunity?"
        self.state = "collecting_votes"  # collecting_votes, scored, complete

    def submit_vote(self, player_id: str, vote: str):
        """Record a player's vote (yes/no/abstain)"""
        if vote not in ["yes", "no", "abstain"]:
            return False
        self.votes[player_id] = vote
        return True

    def tally_votes(self) -> GameResult:
        """Score the voting round"""
        yes_count = sum(1 for v in self.votes.values() if v == "yes")
        no_count = sum(1 for v in self.votes.values() if v == "no")
        abstain_count = sum(1 for v in self.votes.values() if v == "abstain")

        # Team wins if consensus (all yes or all no, no abstains)
        team_won = abstain_count == 0 and (yes_count == 0 or no_count == 0)
        team_score = 10 if team_won else 5
        opponent_score = 10 if not team_won else 5

        # Behavior observations
        behavior = {
            "voting_pattern": {
                "yes": yes_count,
                "no": no_count,
                "abstain": abstain_count
            },
            "consensus_achieved": team_won,
            "decisive": abstain_count == 0
        }

        return GameResult(
            round_number=self.round_number,
            game_type="voting",
            won=team_won,
            team_score=team_score,
            opponent_score=opponent_score,
            player_actions=self.votes,
            behavior_notes=behavior
        )


class TurnBasedGame:
    """Game B: Turn-based cooperation - test timing, risk management, strategy"""

    def __init__(self, game_id: str, round_number: int = 2):
        self.game_id = game_id
        self.round_number = round_number
        self.turn_order = []  # List of player IDs in order
        self.current_turn_idx = 0
        self.actions = {}  # player_id -> action taken
        self.team_score = 0
        self.opponent_score = 0
        self.state = "collecting_actions"  # collecting_actions, scored, complete
        self.turn_count = 0
        self.max_turns = 4  # Each player gets one turn

    def set_turn_order(self, team_players: List[str], opponent_id: str):
        """Set who goes in what order"""
        all_players = team_players + [opponent_id]
        random.shuffle(all_players)
        self.turn_order = all_players

    def get_current_player(self) -> str:
        """Who's turn is it?"""
        if self.current_turn_idx < len(self.turn_order):
            return self.turn_order[self.current_turn_idx]
        return ""

    def submit_action(self, player_id: str, action: str) -> bool:
        """Player takes an action (safe or risk)"""
        if action not in ["safe", "risk"]:
            return False

        self.actions[player_id] = action
        self.current_turn_idx += 1

        # Simple scoring logic
        if action == "safe":
            self.team_score += 3
        elif action == "risk":
            # Risk is high-reward but team-dependent
            risk_success_rate = 0.6
            if random.random() < risk_success_rate:
                self.team_score += 7
            else:
                self.opponent_score += 5

        return True

    def complete_game(self) -> GameResult:
        """Score the turn-based round"""
        team_won = self.team_score >= self.opponent_score
        
        # Behavior: did they play safe or took risks?
        risk_count = sum(1 for a in self.actions.values() if a == "risk")
        behavior = {
            "actions_taken": self.actions,
            "risk_taking_rate": risk_count / len(self.actions) if self.actions else 0,
            "final_team_score": self.team_score,
            "final_opponent_score": self.opponent_score
        }

        return GameResult(
            round_number=self.round_number,
            game_type="turn_based",
            won=team_won,
            team_score=self.team_score,
            opponent_score=self.opponent_score,
            player_actions=self.actions,
            behavior_notes=behavior
        )


class HiddenInfoGame:
    """Game C: Hidden information puzzle - test communication, trust, information sharing"""

    def __init__(self, game_id: str, round_number: int = 3):
        self.game_id = game_id
        self.round_number = round_number
        self.puzzle_answer = "lighthouse"  # What they need to guess
        self.clues = [
            "I stand tall without feet",
            "Ships rely on me to stay safe",
            "I shine in the darkness"
        ]
        self.guesses = {}  # player_id -> guess
        self.state = "collecting_clues"  # collecting_clues, solving, complete
        self.correct_guess = None

    def get_clues(self) -> List[str]:
        """Return puzzle clues"""
        return self.clues

    def submit_guess(self, player_id: str, guess: str) -> bool:
        """Record a guess attempt"""
        self.guesses[player_id] = guess.lower().strip()
        return True

    def check_answers(self) -> GameResult:
        """Score based on correct guesses"""
        correct_count = sum(
            1 for guess in self.guesses.values()
            if guess == self.puzzle_answer
        )

        team_won = correct_count > 0
        team_score = 10 if team_won else 0
        opponent_score = 10 if not team_won else 0

        behavior = {
            "guesses": self.guesses,
            "correct_answers": correct_count,
            "correct_rate": correct_count / len(self.guesses) if self.guesses else 0,
            "communication_effectiveness": "high" if team_won else "low"
        }

        return GameResult(
            round_number=self.round_number,
            game_type="hidden_info",
            won=team_won,
            team_score=team_score,
            opponent_score=opponent_score,
            player_actions=self.guesses,
            behavior_notes=behavior
        )


def create_game(game_type: str, game_id: str, round_number: int):
    """Factory function to create the right game type"""
    if game_type == "voting":
        return VotingGame(game_id, round_number)
    elif game_type == "turn_based":
        return TurnBasedGame(game_id, round_number)
    elif game_type == "hidden_info":
        return HiddenInfoGame(game_id, round_number)
    else:
        raise ValueError(f"Unknown game type: {game_type}")
