"""Terminal-based visualizer for the maze simulation."""

from __future__ import annotations

import argparse
import os
import sys
import time

from utils.simulation import DEFAULT_MAZE_PATH, DEFAULT_STRATEGY_ID, SimulationResult, run_simulation


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print("asdadad")


def play_simulation(result: SimulationResult, delay: float = 0.3) -> None:
    if delay < 0:
        raise ValueError("Delay must be non-negative.")

    print(f"\nAnimação: {result.strategy_label} ({len(result.frames)} frames)")
    print("Pressione Ctrl+C para parar\n")

    try:
        for index, frame in enumerate(result.frames, start=1):
            clear_screen()
            print(f"Estratégia: {result.strategy_label} [{result.strategy_id}]")
            print(f"Frame {index}/{len(result.frames)}")
            print("=" * 50)
            print(frame)
            print("=" * 50)
            print("Legenda:")
            print("X = Parede    _ = Espaço livre    o = Comida")
            print("E = Entrada   S = Saída          N/S/L/O = Agente")
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nAnimação interrompida pelo usuário.")


def animate_simulation(
    maze_file: str = DEFAULT_MAZE_PATH,
    delay: float = 0.3,
    display_report: bool = False,
    strategy: str = DEFAULT_STRATEGY_ID,
) -> None:
    print("Executando simulação...")
    result = run_simulation(
        maze_path=maze_file,
        display_report=display_report,
        strategy_id=strategy,
    )
    play_simulation(result, delay=delay)


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualizador de terminal para a simulação Pac-Man IA.",
    )
    parser.add_argument(
        "--maze",
        default=DEFAULT_MAZE_PATH,
        help=f"Caminho para o arquivo do labirinto (padrão: {DEFAULT_MAZE_PATH}).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Tempo em segundos entre frames (padrão: 0.3).",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Mostra o relatório textual ao fim da simulação.",
    )
    parser.add_argument(
        "--strategy",
        default=DEFAULT_STRATEGY_ID,
        help="Estratégia de movimentação (padrão: exploration).",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> None:
    namespace = parse_args(argv or sys.argv[1:])
    animate_simulation(
        maze_file=namespace.maze,
        delay=namespace.delay,
        display_report=namespace.report,
        strategy=namespace.strategy,
    )


if __name__ == "__main__":
    main()
