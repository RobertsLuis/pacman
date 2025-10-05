"""Ferramentas para criação de mapas ASCII do labirinto."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Iterable, List, Set, Tuple

try:
    from entities.common import PASSABLE_TILES, Position
except ModuleNotFoundError:  # pragma: no cover - executed apenas em modo script
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from entities.common import PASSABLE_TILES, Position  # type: ignore

DEFAULT_OUTPUT = Path("maps/generated_maze.txt")


def initialize_grid(rows: int, cols: int) -> Tuple[List[List[str]], Position, Position]:
    if rows < 5 or cols < 5:
        raise ValueError("O mapa precisa ter pelo menos 5 linhas e 5 colunas.")

    grid = [["X" for _ in range(cols)] for _ in range(rows)]
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            grid[r][c] = "_"

    entry = Position(1, 1)
    exit_pos = Position(rows - 2, cols - 2)
    grid[entry.row][entry.col] = "E"
    grid[exit_pos.row][exit_pos.col] = "S"
    return grid, entry, exit_pos


def _neighbors(position: Position) -> Iterable[Position]:
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        yield Position(position.row + dr, position.col + dc)


def _is_walkable(tile: str) -> bool:
    return tile in PASSABLE_TILES


def reachable_positions(grid: List[List[str]], start: Position) -> Set[Tuple[int, int]]:
    rows, cols = len(grid), len(grid[0])
    visited: Set[Tuple[int, int]] = set()
    queue: List[Position] = [start]

    while queue:
        current = queue.pop()
        key = (current.row, current.col)
        if key in visited:
            continue
        visited.add(key)

        for neighbor in _neighbors(current):
            if not (0 <= neighbor.row < rows and 0 <= neighbor.col < cols):
                continue
            tile = grid[neighbor.row][neighbor.col]
            if not _is_walkable(tile) and tile != "S":
                continue
            queue.append(neighbor)
    return visited


def validate_layout(grid: List[List[str]], entry: Position, exit_pos: Position) -> bool:
    reachable = reachable_positions(grid, entry)
    if (exit_pos.row, exit_pos.col) not in reachable:
        return False

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == "o" and (r, c) not in reachable:
                return False
    return True


def _build_random_map(
    rows: int,
    cols: int,
    wall_density: float,
    food_count: int,
    seed: int | None,
) -> List[str]:
    grid, entry, exit_pos = initialize_grid(rows, cols)
    rng = random.Random(seed)

    candidate_cells = [
        Position(r, c)
        for r in range(1, rows - 1)
        for c in range(1, cols - 1)
        if (r, c) not in {(entry.row, entry.col), (exit_pos.row, exit_pos.col)}
    ]
    rng.shuffle(candidate_cells)

    wall_target = int(wall_density * len(candidate_cells))
    walls_placed = 0
    for cell in candidate_cells:
        if walls_placed >= wall_target:
            break
        r, c = cell.row, cell.col
        if grid[r][c] != "_":
            continue
        grid[r][c] = "X"
        if validate_layout(grid, entry, exit_pos):
            walls_placed += 1
        else:
            grid[r][c] = "_"

    open_cells = [
        (r, c)
        for r in range(1, rows - 1)
        for c in range(1, cols - 1)
        if grid[r][c] == "_"
    ]
    rng.shuffle(open_cells)

    foods_to_place = min(food_count, len(open_cells))
    for index in range(foods_to_place):
        r, c = open_cells[index]
        grid[r][c] = "o"

    if not validate_layout(grid, entry, exit_pos):
        raise RuntimeError("Não foi possível gerar um mapa válido com os parâmetros informados.")

    return ["".join(row) for row in grid]


def generate_random_map(
    rows: int,
    cols: int,
    wall_density: float = 0.18,
    food_count: int = 6,
    seed: int | None = None,
    max_attempts: int = 12,
) -> List[str]:
    density = wall_density
    last_error: RuntimeError | None = None

    for attempt in range(max_attempts):
        attempt_seed = (seed + attempt) if seed is not None else None
        try:
            return _build_random_map(rows, cols, density, food_count, attempt_seed)
        except RuntimeError as exc:
            last_error = exc
            density = max(0.0, density * 0.85)

    raise RuntimeError(
        "Não foi possível gerar um mapa válido. Reduza --wall-density ou utilize --blank."
    ) from last_error


def write_map(lines: List[str], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


def estimate_wall_density(lines: List[str]) -> float:
    if not lines:
        return 0.0
    rows = len(lines)
    cols = len(lines[0]) if rows else 0
    if rows <= 2 or cols <= 2:
        return 0.0

    interior_total = (rows - 2) * (cols - 2)
    if interior_total <= 0:
        return 0.0

    walls = 0
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if lines[r][c] == "X":
                walls += 1
    return walls / interior_total


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera novos mapas ASCII para a simulação Pac-Man IA.",
    )
    parser.add_argument("--rows", type=int, default=15, help="Número de linhas (>=5).")
    parser.add_argument("--cols", type=int, default=15, help="Número de colunas (>=5).")
    parser.add_argument(
        "--wall-density",
        type=float,
        default=0.18,
        help="Proporção aproximada de paredes internas (0 a 0.6).",
    )
    parser.add_argument(
        "--food",
        type=int,
        default=6,
        help="Quantidade de comidas a distribuir.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semente para o gerador aleatório.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Arquivo de saída (padrão: maps/generated_maze.txt).",
    )
    parser.add_argument(
        "--blank",
        action="store_true",
        help="Gera apenas a grade básica sem paredes extras e comidas.",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> Path:
    import sys

    namespace = parse_args(argv or sys.argv[1:])
    if not (0 <= namespace.wall_density <= 0.6):
        raise ValueError("wall-density deve estar entre 0 e 0.6.")

    if namespace.blank:
        grid, _, _ = initialize_grid(namespace.rows, namespace.cols)
        lines = ["".join(row) for row in grid]
    else:
        lines = generate_random_map(
            rows=namespace.rows,
            cols=namespace.cols,
            wall_density=namespace.wall_density,
            food_count=namespace.food,
            seed=namespace.seed,
        )

    output_path = write_map(lines, namespace.output)
    if not namespace.blank:
        actual_density = estimate_wall_density(lines)
        if abs(actual_density - namespace.wall_density) > 0.02:
            print(
                "Aviso: densidade efetiva de paredes ajustada para "
                f"{actual_density:.2f} após múltiplas tentativas."
            )
    print(f"Mapa salvo em: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
