"""Maze environment responsible for agent interactions."""

from __future__ import annotations

from typing import Dict, List

from .common import DIRECTIONS, PASSABLE_TILES, Position


class MazeEnvironment:
    """Grid-based maze that exposes sensor data and movement helpers."""

    def __init__(self, grid: List[List[str]], sensor_size: int = 3):
        """Initialize the maze state from a rectangular matrix of tiles."""
        if not grid or not grid[0]:
            raise ValueError("Maze grid must be a non-empty rectangle.")

        if sensor_size % 2 == 0 or sensor_size < 3:
            raise ValueError("Sensor size must be an odd number >= 3.")

        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.sensor_size = sensor_size
        self.sensor_radius = sensor_size // 2

        self.entry = self._find_tile("E")
        self.exit = self._find_tile("S")
        self.agent_pos: Position = self.entry
        self.agent_direction = "N"

        self.steps_taken = 0
        self.food_total = sum(row.count("o") for row in grid)
        self.food_collected = 0

    @classmethod
    def from_file(cls, path: str, sensor_size: int = 3) -> "MazeEnvironment":
        """Build a maze environment by reading an ASCII map from disk."""
        with open(path, "r", encoding="ascii") as maze_file:
            lines = [line.rstrip("\n") for line in maze_file]
        grid = [list(line) for line in lines if line]
        return cls(grid, sensor_size)

    def _find_tile(self, tile: str) -> Position:
        """Locate the coordinates of a specific tile."""
        for r, row in enumerate(self.grid):
            for c, value in enumerate(row):
                if value == tile:
                    return Position(r, c)
        raise ValueError(f"Tile '{tile}' not found in maze.")

    def set_direction(self, direction: str) -> None:
        """Update the heading of the agent."""
        if direction not in DIRECTIONS:
            raise ValueError(f"Invalid direction '{direction}'.")
        self.agent_direction = direction

    def move_forward(self) -> bool:
        """Advance the agent if the target tile is traversable."""
        target = self.agent_pos.neighbor(self.agent_direction)
        if not self._inside(target) or self.grid[target.row][target.col] == "X":
            return False

        self.agent_pos = target
        self.steps_taken += 1

        current_tile = self.grid[target.row][target.col]
        if current_tile == "o":
            self.food_collected += 1
            self.grid[target.row][target.col] = "_"
        return True

    def goal_reached(self) -> bool:
        """Return True when all food is collected and the exit is reached."""
        on_exit = self.agent_pos == self.exit
        has_all_food = self.food_collected == self.food_total
        return on_exit and has_all_food

    def get_sensor_window(self) -> List[List[str]]:
        """Capture a perception window centered on the agent."""
        window: List[List[str]] = []
        radius = self.sensor_radius

        for dr in range(-radius, radius + 1):
            row_values: List[str] = []
            for dc in range(-radius, radius + 1):
                pos = Position(self.agent_pos.row + dr, self.agent_pos.col + dc)
                if self._inside(pos):
                    row_values.append(self.grid[pos.row][pos.col])
                else:
                    row_values.append("X")
            window.append(row_values)

        # NOTE: The center cell mirrors the agent direction instead of raw tile.
        center_idx = radius
        window[center_idx][center_idx] = self.agent_direction
        return window

    def get_directional_food_counts(self) -> Dict[str, int]:
        """Return how many food pellets exist along each cardinal direction."""
        counts = {direction: 0 for direction in DIRECTIONS}
        for direction, (dr, dc) in DIRECTIONS.items():
            current = self.agent_pos
            while True:
                current = Position(current.row + dr, current.col + dc)
                if not self._inside(current):
                    break
                tile = self.grid[current.row][current.col]
                if tile == "X":
                    break
                if tile == "o":
                    counts[direction] += 1
        return counts

    def tile_at(self, position: Position) -> str:
        """Return the tile stored at the requested coordinates."""
        if not self._inside(position):
            return "X"
        return self.grid[position.row][position.col]

    def render(self) -> str:
        """Render the maze grid as ASCII including the agent marker."""
        rows: List[str] = []
        for r in range(self.rows):
            chars: List[str] = []
            for c in range(self.cols):
                pos = Position(r, c)
                if pos == self.agent_pos:
                    chars.append(self.agent_direction)
                else:
                    chars.append(self.grid[r][c])
            rows.append("".join(chars))
        return "\n".join(rows)

    def _inside(self, position: Position) -> bool:
        """Check whether a position lies within the maze bounds."""
        return 0 <= position.row < self.rows and 0 <= position.col < self.cols


__all__ = ["MazeEnvironment"]
