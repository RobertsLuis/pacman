"""Maze agents with pluggable navigation strategies."""

from __future__ import annotations

import random
from collections import deque
from typing import Deque, Dict, Iterable, List, Optional, Tuple

from .common import DIRECTIONS, PASSABLE_TILES, Position
from .environment import MazeEnvironment


class BaseAgent:
    """Base agent that keeps track of sensor memory and executes plans."""

    strategy_id = "base"
    strategy_label = "Base"

    def __init__(self, environment: MazeEnvironment, total_food: int):
        self.env = environment
        self.total_food = total_food
        self.direction = self.env.agent_direction

        self.memory: Dict[Position, str] = {}
        self.visited: set[Position] = set()
        self.plan: Deque[str] = deque()
        self.last_sensor: Optional[List[List[str]]] = None

    # --- Core loop -----------------------------------------------------
    def getSensor(self) -> List[List[str]]:
        """Return the 3x3 sensor snapshot and persist it in memory."""
        sensor = self.env.get_sensor_window()
        self.last_sensor = sensor
        self._update_memory(sensor)
        return sensor

    def setDirection(self, direction: str) -> None:
        """Rotate the agent to face the requested cardinal direction."""
        self.direction = direction
        self.env.set_direction(direction)

    def move(self) -> bool:
        """Advance one tile forward, syncing direction with the environment."""
        moved = self.env.move_forward()
        if not moved:
            return False
        self.direction = self.env.agent_direction
        return True

    def compute_plan(self) -> List[str]:  # pragma: no cover - abstract behaviour
        """Return a list of directions that should be executed next."""
        return []

    def step(self) -> bool:
        """Execute one perception-plan-action cycle and update memory."""
        self.getSensor()
        self.visited.add(self.env.agent_pos)

        if self.env.goal_reached():
            return False

        exit_known = (
            self.env.food_collected == self.total_food and self.env.exit in self.memory
        )
        if exit_known and self.plan:
            # NOTE: Discard outdated plans once the exit becomes the primary goal.
            if self._plan_destination() != self.env.exit:
                self.plan.clear()

        if not self.plan:
            new_plan = self.compute_plan()
            if new_plan:
                self.plan = deque(new_plan)

        if not self.plan:
            return False

        next_move = self.plan[0]
        if self.direction != next_move:
            self.setDirection(next_move)

        if self.move():
            self.plan.popleft()
            return True

        blocked = self.env.agent_pos.neighbor(self.direction)
        self.memory[blocked] = "X"
        self.plan.clear()
        return False

    # --- Memory helpers ------------------------------------------------
    def _update_memory(self, sensor: List[List[str]]) -> None:
        """Write the current sensor window into the agent's mental map."""
        center = self.env.agent_pos
        for dr, row_values in enumerate(sensor, start=-1):
            for dc, value in enumerate(row_values, start=-1):
                position = Position(center.row + dr, center.col + dc)
                if dr == 0 and dc == 0:
                    # NOTE: The agent stores the underlying tile at its own cell.
                    underlying = self.env.tile_at(center)
                    self.memory[position] = underlying
                else:
                    self.memory[position] = value

    def _memory_select_target(self) -> Optional[Position]:
        """Pick the next objective using only remembered information."""
        if self.env.food_collected < self.total_food:
            foods = [pos for pos, tile in self.memory.items() if tile == "o"]
            target = self._nearest_reachable(foods)
            if target:
                return target

        unchecked = [
            pos
            for pos, tile in self.memory.items()
            if tile in PASSABLE_TILES and pos not in self.visited
        ]
        target = self._nearest_reachable(unchecked)
        if target:
            return target

        if self.env.food_collected == self.total_food and self.env.exit in self.memory:
            return self.env.exit
        return None

    def _memory_plan(self) -> List[str]:
        """Plan a path to the best-known target using the mental map."""
        target = self._memory_select_target()
        if target is not None:
            return self._plan_path_with_memory(target)
        return []

    def _nearest_reachable(self, candidates: Iterable[Position]) -> Optional[Position]:
        """Return the candidate with the shortest memory-based route."""
        best_target: Optional[Position] = None
        best_path_length: Optional[int] = None
        for candidate in candidates:
            path = self._plan_path_with_memory(candidate)
            if not path:
                continue
            if best_path_length is None or len(path) < best_path_length:
                best_target = candidate
                best_path_length = len(path)
        return best_target

    def _plan_path_with_memory(self, target: Position) -> List[str]:
        """Run BFS on the remembered map to reach the desired target."""
        start = self.env.agent_pos
        if start == target:
            return []

        queue: Deque[Tuple[Position, List[str]]] = deque()
        queue.append((start, []))
        visited: set[Position] = {start}

        while queue:
            current, path = queue.popleft()
            for direction, (dr, dc) in DIRECTIONS.items():
                neighbor = Position(current.row + dr, current.col + dc)
                if neighbor in visited:
                    continue
                tile = self.memory.get(neighbor)
                if not self._memory_tile_passable(tile, neighbor, target):
                    continue
                new_path = path + [direction]
                if neighbor == target:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        return []

    # --- Grid-based helpers --------------------------------------------
    def _plan_path_on_grid(self, target: Position) -> List[str]:
        """Run BFS on the real grid, assuming omniscient knowledge."""
        start = self.env.agent_pos
        if start == target:
            return []

        queue: Deque[Tuple[Position, List[str]]] = deque()
        queue.append((start, []))
        visited: set[Position] = {start}

        while queue:
            current, path = queue.popleft()
            for direction, (dr, dc) in DIRECTIONS.items():
                neighbor = Position(current.row + dr, current.col + dc)
                if neighbor in visited:
                    continue
                if not self._grid_position_passable(neighbor, target):
                    continue
                new_path = path + [direction]
                if neighbor == target:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))
        return []

    def _can_traverse(self, position: Position) -> bool:
        """Return True when the real grid allows visiting the position."""
        if not (
            0 <= position.row < self.env.rows and 0 <= position.col < self.env.cols
        ):
            return False
        tile = self.env.grid[position.row][position.col]
        return tile != "X"

    def _plan_destination(self) -> Optional[Position]:
        """Project the final position if the current plan is executed fully."""
        current = self.env.agent_pos
        for direction in self.plan:
            vector = DIRECTIONS.get(direction)
            if vector is None:
                return None
            dr, dc = vector
            current = Position(current.row + dr, current.col + dc)
        return current

    # --- Hooks for subclasses ---------------------------------------------
    def _memory_tile_passable(
        self,
        tile: Optional[str],
        position: Position,
        target: Position,
    ) -> bool:
        if position == target:
            return True
        if tile is None:
            return False
        return tile in PASSABLE_TILES

    def _grid_position_passable(self, position: Position, target: Position) -> bool:
        if position == target:
            return True
        return self._can_traverse(position)

    # --- Reporting ------------------------------------------------------
    def report(self) -> str:
        """Return a human-readable summary of the current performance."""
        score = (self.env.food_collected * 10) - self.env.steps_taken
        return (
            f"Comidas coletadas: {self.env.food_collected}/{self.total_food}\n"
            f"Passos dados: {self.env.steps_taken}\n"
            f"Pontuacao final: {score}"
        )


class ExplorationAgent(BaseAgent):
    """Exploration baseline that uses only the agent's growing memory."""

    strategy_id = "exploration"
    strategy_label = "Exploração com memória"

    def compute_plan(self) -> List[str]:
        return self._memory_plan()


class ShortestPathAgent(BaseAgent):
    """Greedy planner that has full knowledge of the real maze grid."""

    strategy_id = "shortest_path"
    strategy_label = "Menor caminho conhecido"

    def compute_plan(self) -> List[str]:
        if self.env.food_collected < self.total_food:
            foods = self._foods_remaining()
            if foods:
                path = self._nearest_path_on_grid(foods)
                if path:
                    return path

        if self.env.food_collected == self.total_food:
            path = self._plan_path_on_grid(self.env.exit)
            if path:
                return path

        # NOTE: Fall back to the exploration logic when no grid path is found.
        return self._memory_plan()

    def _foods_remaining(self) -> List[Position]:
        foods: List[Position] = []
        for r, row in enumerate(self.env.grid):
            for c, value in enumerate(row):
                if value == "o":
                    foods.append(Position(r, c))
        return foods

    def _nearest_path_on_grid(self, candidates: Iterable[Position]) -> List[str]:
        best_path: List[str] = []
        for candidate in candidates:
            path = self._plan_path_on_grid(candidate)
            if not path:
                continue
            if not best_path or len(path) < len(best_path):
                best_path = path
        return best_path


class RandomWalkAgent(BaseAgent):
    """Random walk that avoids stepping back to the previous tile."""

    strategy_id = "random_walk"
    strategy_label = "Caminhada aleatória"

    _opposites = {"N": "S", "S": "N", "L": "O", "O": "L"}

    def __init__(self, environment: MazeEnvironment, total_food: int):
        super().__init__(environment, total_food)
        self.prev_direction: Optional[str] = None
        self._rng = random.Random()

    def compute_plan(self) -> List[str]:
        candidates: List[str] = []
        for direction in DIRECTIONS:
            neighbor = self.env.agent_pos.neighbor(direction)
            if self._can_traverse(neighbor):
                candidates.append(direction)

        if not candidates:
            return []

        if self.prev_direction and len(candidates) > 1:
            opposite = self._opposites[self.prev_direction]
            filtered = [d for d in candidates if d != opposite]
            if filtered:
                candidates = filtered

        choice = self._rng.choice(candidates)
        self.prev_direction = choice
        return [choice]


class SensorGreedyAgent(BaseAgent):
    """Agent that moves toward visible food greedily."""

    strategy_id = "sensor_greedy"
    strategy_label = "Sensor Greedy"

    def sense_and_decide(self) -> str:
        """Choose direction toward nearest visible food."""
        window = self.environment.get_sensor_window()
        sensor_size = self.environment.sensor_size
        center = sensor_size // 2

        best_direction = None
        min_distance = float("inf")

        # Search for food in the sensor window
        for row_idx, row in enumerate(window):
            for col_idx, cell in enumerate(row):
                if cell == "o":
                    # Calculate Manhattan distance from center
                    distance = abs(row_idx - center) + abs(col_idx - center)
                    if distance < min_distance:
                        min_distance = distance
                        # Determine direction toward this food
                        dr = row_idx - center
                        dc = col_idx - center

                        # Choose primary direction based on larger offset
                        if abs(dr) > abs(dc):
                            best_direction = "S" if dr > 0 else "N"
                        elif abs(dc) > abs(dr):
                            best_direction = "E" if dc > 0 else "W"
                        else:
                            # Equal distances, prefer horizontal movement
                            best_direction = "E" if dc > 0 else "W"

        if best_direction:
            return best_direction

        # No food visible, try moving in current direction
        return self.environment.agent_direction


class DeadEndAwareAgent(BaseAgent):
    """Exploration variant that avoids revisiting known dead ends."""

    strategy_id = "dead_end_aware"
    strategy_label = "Evita becos sem saída"

    def __init__(self, environment: MazeEnvironment, total_food: int):
        super().__init__(environment, total_food)
        self.dead_ends: set[Position] = set()

    def compute_plan(self) -> List[str]:
        """Mark discovered dead ends and plan using the filtered map."""
        self._mark_dead_ends()
        return self._memory_plan()

    def _mark_dead_ends(self) -> None:
        """Label visited cells that have no meaningful exits left."""
        for pos in list(self.visited):
            if pos in self.dead_ends:
                continue
            tile = self.memory.get(pos)
            if tile == "o":
                continue
            if pos in {self.env.entry, self.env.exit}:
                continue

            if any(
                pos.neighbor(direction) not in self.memory for direction in DIRECTIONS
            ):
                continue

            neighbors_passable = 0
            for direction in DIRECTIONS:
                neighbor = pos.neighbor(direction)
                tile_neighbor = self.memory.get(neighbor)
                if tile_neighbor in PASSABLE_TILES:
                    neighbors_passable += 1
            if neighbors_passable <= 1:
                self.dead_ends.add(pos)

    def _memory_tile_passable(
        self,
        tile: Optional[str],
        position: Position,
        target: Position,
    ) -> bool:
        if position in self.dead_ends and position != target:
            return False
        return super()._memory_tile_passable(tile, position, target)


class HeuristicFrontierAgent(BaseAgent):
    """Select unexplored frontiers that promise more unknown neighbors."""

    strategy_id = "frontier_heuristic"
    strategy_label = "Fronteiras heurísticas"

    def __init__(self, environment: MazeEnvironment, total_food: int):
        super().__init__(environment, total_food)
        self.dead_ends: set[Position] = set()

    def compute_plan(self) -> List[str]:
        """Track dead ends before searching for the next frontier target."""
        self._mark_dead_ends()
        target = self._select_target()
        if target is None:
            return []
        path = self._plan_path_with_memory(target)
        if path:
            return path
        return []

    def _select_target(self) -> Optional[Position]:
        """Choose a frontier or food target based on heuristic ranking."""
        if self.env.food_collected < self.total_food:
            foods = [pos for pos, tile in self.memory.items() if tile == "o"]
            foods = sorted(foods, key=lambda pos: self._heuristic(pos))
            for pos in foods:
                if self._plan_path_with_memory(pos):
                    return pos

        frontiers = [
            pos
            for pos, tile in self.memory.items()
            if tile in PASSABLE_TILES
            and pos not in self.visited
            and pos not in self.dead_ends
        ]
        frontiers = [pos for pos in frontiers if self._count_unknown_neighbors(pos) > 0]
        if not frontiers:
            if (
                self.env.exit in self.memory
                and self.env.food_collected == self.total_food
            ):
                return self.env.exit
            return None

        frontiers.sort(key=self._frontier_score)
        for pos in frontiers:
            if self._plan_path_with_memory(pos):
                return pos
        return None

    def _frontier_score(self, position: Position) -> Tuple[int, int]:
        """Return ordering tuple prioritizing frontiers with more unknowns."""
        unknown_neighbors = self._count_unknown_neighbors(position)
        manhattan = abs(position.row - self.env.agent_pos.row) + abs(
            position.col - self.env.agent_pos.col
        )
        return (-unknown_neighbors, manhattan)

    def _heuristic(self, position: Position) -> int:
        return abs(position.row - self.env.agent_pos.row) + abs(
            position.col - self.env.agent_pos.col
        )

    def _count_unknown_neighbors(self, position: Position) -> int:
        """Count how many adjacent tiles have not been sensed yet."""
        return sum(
            1
            for direction in DIRECTIONS
            if position.neighbor(direction) not in self.memory
        )

    def _mark_dead_ends(self) -> None:
        """Reuse the dead-end detection logic to prune future targets."""
        for pos in list(self.visited):
            if pos in self.dead_ends:
                continue
            tile = self.memory.get(pos)
            if tile == "o":
                continue
            if pos in {self.env.entry, self.env.exit}:
                continue

            if any(
                pos.neighbor(direction) not in self.memory for direction in DIRECTIONS
            ):
                continue

            neighbors_passable = 0
            for direction in DIRECTIONS:
                neighbor = pos.neighbor(direction)
                tile_neighbor = self.memory.get(neighbor)
                if tile_neighbor in PASSABLE_TILES:
                    neighbors_passable += 1
            if neighbors_passable <= 1:
                self.dead_ends.add(pos)

    def _memory_tile_passable(
        self,
        tile: Optional[str],
        position: Position,
        target: Position,
    ) -> bool:
        if position in self.dead_ends and position != target:
            return False
        return super()._memory_tile_passable(tile, position, target)


# Backwards compatibility alias -------------------------------------------------
Agent = ExplorationAgent

__all__ = [
    "Agent",
    "BaseAgent",
    "DeadEndAwareAgent",
    "ExplorationAgent",
    "HeuristicFrontierAgent",
    "RandomWalkAgent",
    "SensorGreedyAgent",
    "ShortestPathAgent",
]
