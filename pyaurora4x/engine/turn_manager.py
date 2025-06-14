"""Game turn management for PyAurora 4X."""

from dataclasses import dataclass


@dataclass
class GameTurnManager:
    """Manage the game turn counter and turn length."""

    turn_length: float = 5.0
    current_turn: int = 0

    def advance_turn(self) -> float:
        """Advance to the next turn and return the time delta."""
        self.current_turn += 1
        return self.turn_length

    def reset(self) -> None:
        """Reset the turn counter."""
        self.current_turn = 0
