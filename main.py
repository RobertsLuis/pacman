"""Menu principal para rodar e comparar estratégias da simulação."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, List

from utils.simulation import DEFAULT_MAZE_PATH, SimulationResult, run_simulations_for
from viewers.html import DEFAULT_OUTPUT as DEFAULT_HTML_OUTPUT
from viewers.html import save_animation_html
from viewers.terminal import play_simulation
from viewers.video import (
    DEFAULT_FRAMES_OUTPUT,
    DEFAULT_VIDEO_OUTPUT,
    create_video,
    save_frames_text,
)

MENU = {
    "1": "Executar estratégias e visualizar no terminal",
    "2": "Gerar HTML interativo para todas as estratégias",
    "3": "Gerar vídeo MP4 e frames para todas as estratégias",
    "0": "Sair",
}

RESULT_DIRS = {
    "html": DEFAULT_HTML_OUTPUT.parent,
    "videos": DEFAULT_VIDEO_OUTPUT.parent,
    "frames": DEFAULT_FRAMES_OUTPUT.parent,
}

MAPS_DIR = Path("maps")
DEFAULT_DELAY = 0.3
DEFAULT_FPS = 3

# ---------------------------------------------------------------------------
# Helpers


def prompt(prompt_text: str) -> str:
    try:
        return input(prompt_text)
    except EOFError:
        print()
        return ""


def list_available_maps() -> List[Path]:
    candidates = [
        path
        for path in MAPS_DIR.glob("*.txt")
        if path.is_file() and not path.name.startswith("_")
    ]
    if not candidates:
        raise FileNotFoundError(
            "Nenhum mapa encontrado em 'maps/'. Crie um com utils/map_builder.py."
        )
    return sorted(candidates)


def choose_map() -> Path:
    maps = list_available_maps()
    print("\nMapas disponíveis:")
    for index, map_path in enumerate(maps, start=1):
        print(f" {index}) {map_path.name}")

    while True:
        choice = prompt("Selecione o mapa [1]: ").strip()
        if not choice:
            return maps[0]
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(maps):
                return maps[idx - 1]
        print("Opção inválida. Informe um número da lista.")


def slugify(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "_")
    allowed = [c if c.isalnum() or c in {"-", "_"} else "_" for c in cleaned]
    slug = "".join(allowed).strip("_-")
    return slug or "run"


def prompt_run_name() -> str:
    value = prompt("Nome para identificar esta execução: ").strip()
    if not value:
        print("Nome vazio, usando 'run'.")
    return slugify(value or "run")


def ensure_dirs_exist() -> None:
    for directory in RESULT_DIRS.values():
        directory.mkdir(parents=True, exist_ok=True)


def prompt_sensor_size() -> int:
    """Prompt user for sensor window size."""
    while True:
        choice = prompt("Tamanho do sensor (3, 5, 7) [3]: ").strip()
        if not choice:
            return 3
        if choice in ["3", "5", "7"]:
            return int(choice)
        print("Tamanho inválido. Use 3, 5 ou 7.")


def run_all_strategies(
    maze_path: Path, sensor_size: int = 3
) -> Dict[str, SimulationResult]:
    print(f"\nExecutando estratégias com sensor {sensor_size}x{sensor_size}...")
    results = run_simulations_for(
        str(maze_path), display_report=False, sensor_size=sensor_size
    )
    print("Concluído.\n")
    return results


def order_results(results: Dict[str, SimulationResult]) -> List[SimulationResult]:
    return sorted(
        results.values(),
        key=lambda res: (-res.score, res.steps_taken, res.strategy_id),
    )


def render_scoreboard(results: Dict[str, SimulationResult]) -> str:
    rows = [
        "ID         | Estratégia                       | Score | Passos | Coleta | Objetivo"
    ]
    rows.append("-" * len(rows[0]))
    for res in order_results(results):
        goal = "Sim" if res.goal_reached else "Não"
        rows.append(
            f"{res.strategy_id:<10} | {res.strategy_label:<30} | "
            f"{res.score:>5} | {res.steps_taken:>6} | "
            f"{res.food_collected:>3}/{res.total_food:<3} | {goal}"
        )
    return "\n".join(rows)


def write_scoreboard(run_slug: str, results: Dict[str, SimulationResult]) -> Path:
    scoreboard_path = RESULT_DIRS["frames"] / f"{run_slug}_scoreboard.txt"
    scoreboard_path.write_text(render_scoreboard(results) + "\n", encoding="utf-8")
    return scoreboard_path


def prompt_strategy_choice(results: Dict[str, SimulationResult]) -> str | None:
    ordered = order_results(results)
    print("\nEstratégias disponíveis para animação:")
    for index, res in enumerate(ordered, start=1):
        status = "OK" if res.goal_reached else "Incompleto"
        print(
            f" {index}) {res.strategy_label} ({res.strategy_id}) - Score {res.score} [{status}]"
        )
    print(" 0) Voltar ao menu")

    while True:
        choice = prompt("Escolha a estratégia para animar [0]: ").strip()
        if not choice or choice == "0":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(ordered):
                return ordered[idx - 1].strategy_id
        print("Opção inválida. Digite um número válido.")


def build_output_name(run_slug: str, strategy_id: str, suffix: str) -> str:
    return f"{run_slug}_{strategy_id}{suffix}"


# ---------------------------------------------------------------------------
# Workflows


def run_terminal_workflow() -> None:
    ensure_dirs_exist()
    maze_path = choose_map()
    sensor_size = prompt_sensor_size()
    run_slug = prompt_run_name()

    results = run_all_strategies(maze_path, sensor_size)
    scoreboard_text = render_scoreboard(results)
    print("\nResumo das estratégias:\n")
    print(scoreboard_text)

    scoreboard_path = write_scoreboard(run_slug, results)
    print(f"\nQuadro salvo em: {scoreboard_path}")

    strategy_id = prompt_strategy_choice(results)
    if not strategy_id:
        return

    result = results[strategy_id]
    try:
        play_simulation(result, delay=DEFAULT_DELAY)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erro ao animar: {exc}")


def run_html_workflow() -> None:
    ensure_dirs_exist()
    maze_path = choose_map()
    run_slug = prompt_run_name()

    results = run_all_strategies(maze_path)
    for strategy_id, result in results.items():
        filename = build_output_name(run_slug, strategy_id, ".html")
        output_path = RESULT_DIRS["html"] / filename
        save_animation_html(
            maze_file=str(maze_path),
            output_file=output_path,
            strategy=strategy_id,
            result=result,
        )

    scoreboard_path = write_scoreboard(run_slug, results)
    print(f"Quadro comparativo salvo em: {scoreboard_path}")


def run_video_workflow() -> None:
    ensure_dirs_exist()
    maze_path = choose_map()
    run_slug = prompt_run_name()

    results = run_all_strategies(maze_path)
    for strategy_id, result in results.items():
        frames_name = build_output_name(run_slug, strategy_id, ".txt")
        video_name = build_output_name(run_slug, strategy_id, ".mp4")
        frames_path = RESULT_DIRS["frames"] / frames_name
        video_path = RESULT_DIRS["videos"] / video_name

        save_frames_text(
            maze_file=str(maze_path),
            output_file=frames_path,
            strategy=strategy_id,
            result=result,
        )

        try:
            create_video(
                maze_file=str(maze_path),
                output_file=video_path,
                fps=DEFAULT_FPS,
                scale=20,
                strategy=strategy_id,
                result=result,
            )
        except RuntimeError as exc:
            print(exc)
            print(
                "Dica: instale dependências opcionais com `pip install opencv-python numpy`."
            )

    scoreboard_path = write_scoreboard(run_slug, results)
    print(f"Quadro comparativo salvo em: {scoreboard_path}")


# ---------------------------------------------------------------------------
# Menu principal


def show_menu() -> None:
    print("\n=== Pac-Man IA ===")
    for key, label in MENU.items():
        print(f" {key}) {label}")


def main() -> None:
    while True:
        show_menu()
        choice = prompt("Escolha uma opção: ").strip()

        if choice == "1":
            run_terminal_workflow()
        elif choice == "2":
            run_html_workflow()
        elif choice == "3":
            run_video_workflow()
        elif choice in {"0", "", "q", "Q"}:
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaída solicitada pelo usuário.")
        sys.exit(0)
