"""Shared types and constants for maze entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

DirectionVector = Tuple[int, int]

# Cardinal directions using Portuguese initials.
DIRECTIONS: Dict[str, DirectionVector] = {
    "N": (-1, 0),  # Norte
    "S": (1, 0),   # Sul
    "L": (0, 1),   # Leste
    "O": (0, -1),  # Oeste
}

PASSABLE_TILES = frozenset({"_", "E", "S", "o"})


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def neighbor(self, direction: str) -> "Position":
        dr, dc = DIRECTIONS[direction]
        return Position(self.row + dr, self.col + dc)
