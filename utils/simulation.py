"""Simulation orchestrator used by viewers and CLI entry-points."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

from entities import (
    BaseAgent,
    DeadEndAwareAgent,
    ExplorationAgent,
    HeuristicFrontierAgent,
    MazeEnvironment,
    RandomWalkAgent,
    SensorGreedyAgent,
    ShortestPathAgent,
)

DEFAULT_MAZE_PATH = "maps/maze.txt"
DEFAULT_STRATEGY_ID = "exploration"


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    label: str
    factory: Callable[[MazeEnvironment], BaseAgent]


STRATEGIES: Dict[str, StrategySpec] = {
    spec.strategy_id: spec
    for spec in (
        StrategySpec(
            strategy_id=ExplorationAgent.strategy_id,
            label=ExplorationAgent.strategy_label,
            factory=lambda env: ExplorationAgent(env, env.food_total),
        ),
        StrategySpec(
            strategy_id=RandomWalkAgent.strategy_id,
            label=RandomWalkAgent.strategy_label,
            factory=lambda env: RandomWalkAgent(env, env.food_total),
        ),
        StrategySpec(
            strategy_id=SensorGreedyAgent.strategy_id,
            label=SensorGreedyAgent.strategy_label,
            factory=lambda env: SensorGreedyAgent(env, env.food_total),
        ),
        StrategySpec(
            strategy_id=DeadEndAwareAgent.strategy_id,
            label=DeadEndAwareAgent.strategy_label,
            factory=lambda env: DeadEndAwareAgent(env, env.food_total),
        ),
        StrategySpec(
            strategy_id=HeuristicFrontierAgent.strategy_id,
            label=HeuristicFrontierAgent.strategy_label,
            factory=lambda env: HeuristicFrontierAgent(env, env.food_total),
        ),
        StrategySpec(
            strategy_id=ShortestPathAgent.strategy_id,
            label=ShortestPathAgent.strategy_label,
            factory=lambda env: ShortestPathAgent(env, env.food_total),
        ),
    )
}


@dataclass
class SimulationResult:
    frames: List[str]
    steps_taken: int
    food_collected: int
    total_food: int
    score: int
    goal_reached: bool
    final_render: str
    strategy_id: str
    strategy_label: str

    @property
    def summary(self) -> str:
        return (
            f"Estrategia: {self.strategy_label} ({self.strategy_id})\n"
            f"Comidas coletadas: {self.food_collected}/{self.total_food}\n"
            f"Passos dados: {self.steps_taken}\n"
            f"Pontuacao final: {self.score}"
        )


def get_strategy(strategy_id: str) -> StrategySpec:
    try:
        return STRATEGIES[strategy_id]
    except KeyError as exc:  # pragma: no cover - defensive
        available = ", ".join(sorted(STRATEGIES))
        raise ValueError(
            f"Estrategia desconhecida '{strategy_id}'. Disponiveis: {available}."
        ) from exc


def available_strategies() -> Iterable[StrategySpec]:
    return STRATEGIES.values()


def run_simulation(
    maze_path: str = DEFAULT_MAZE_PATH,
    max_steps: int = 500,
    display_report: bool = True,
    strategy_id: str = DEFAULT_STRATEGY_ID,
    sensor_size: int = 3,
    food_sensor_enabled: bool = True,
) -> SimulationResult:
    strategy = get_strategy(strategy_id)
    env = MazeEnvironment.from_file(
        maze_path,
        sensor_size=sensor_size,
        food_sensor_enabled=food_sensor_enabled,
    )
    agent = strategy.factory(env)

    frames: List[str] = [env.render()]
    for _ in range(max_steps):
        moved = agent.step()
        frames.append(env.render())
        if env.goal_reached():
            break
        if not moved and not agent.plan:
            break

    score = (env.food_collected * 10) - env.steps_taken
    result = SimulationResult(
        frames=frames,
        steps_taken=env.steps_taken,
        food_collected=env.food_collected,
        total_food=env.food_total,
        score=score,
        goal_reached=env.goal_reached(),
        final_render=env.render(),
        strategy_id=strategy.strategy_id,
        strategy_label=strategy.label,
    )

    if display_report:
        print(result.final_render)
        print()
        print(result.summary)
        print()
        print(
            "Utilize os visualizadores para gerar animações ou vídeos "
            "a partir de 'result.frames'."
        )

    return result


def run_simulations_for(
    maze_path: str,
    strategy_ids: Optional[Iterable[str]] = None,
    max_steps: int = 500,
    display_report: bool = True,
    sensor_size: int = 3,
    food_sensor_enabled: bool = True,
) -> Dict[str, SimulationResult]:
    ids = list(strategy_ids) if strategy_ids else list(STRATEGIES.keys())
    results: Dict[str, SimulationResult] = {}
    for strategy_id in ids:
        results[strategy_id] = run_simulation(
            maze_path=maze_path,
            max_steps=max_steps,
            display_report=display_report,
            strategy_id=strategy_id,
            sensor_size=sensor_size,
            food_sensor_enabled=food_sensor_enabled,
        )
    return results


__all__ = [
    "DEFAULT_MAZE_PATH",
    "DEFAULT_STRATEGY_ID",
    "SimulationResult",
    "StrategySpec",
    "available_strategies",
    "get_strategy",
    "run_simulation",
    "run_simulations_for",
]
