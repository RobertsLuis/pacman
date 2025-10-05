"""Video generator for the maze simulation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

from utils.simulation import (
    DEFAULT_MAZE_PATH,
    DEFAULT_STRATEGY_ID,
    SimulationResult,
    run_simulation,
)

DEFAULT_VIDEO_OUTPUT = Path("results/videos/maze_simulation.mp4")
DEFAULT_FRAMES_OUTPUT = Path("results/frames/frames.txt")


def _require_video_dependencies() -> Tuple["cv2", "np"]:  # type: ignore[name-defined]
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise RuntimeError(
            "As dependências 'opencv-python' e 'numpy' são necessárias para gerar vídeo."
        ) from exc
    return cv2, np


def ascii_to_image(frame: str, scale: int = 20):
    cv2, np = _require_video_dependencies()

    palette = {
        "X": (40, 40, 40),
        "_": (230, 230, 230),
        "o": (0, 200, 0),
        "E": (255, 120, 0),
        "S": (220, 0, 0),
        "N": (0, 200, 255),
        "L": (0, 200, 255),
        "O": (0, 200, 255),
    }

    rows = [row for row in frame.splitlines() if row]
    height = len(rows) * scale
    width = len(rows[0]) * scale if rows else 0

    img = np.zeros((height, width, 3), dtype=np.uint8)

    for i, line in enumerate(rows):
        for j, char in enumerate(line):
            color = palette.get(char, (200, 200, 200))
            y_start = i * scale
            y_end = y_start + scale
            x_start = j * scale
            x_end = x_start + scale
            img[y_start:y_end, x_start:x_end] = color

    return img


def create_video(
    maze_file: str = DEFAULT_MAZE_PATH,
    output_file: str | Path = DEFAULT_VIDEO_OUTPUT,
    fps: int = 3,
    scale: int = 20,
    strategy: str = DEFAULT_STRATEGY_ID,
    result: SimulationResult | None = None,
) -> Path:
    cv2, _ = _require_video_dependencies()

    if result is None:
        print("Executando simulação...")
        result = run_simulation(
            maze_path=maze_file,
            display_report=False,
            strategy_id=strategy,
        )

    print(f"Convertendo {len(result.frames)} frames para imagens...")
    images = [ascii_to_image(frame, scale=scale) for frame in result.frames]

    if not images:
        raise RuntimeError("Nenhum frame foi gerado pela simulação.")

    height, width, _ = images[0].shape
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    print("Criando vídeo...")
    for index, img in enumerate(images, start=1):
        writer.write(img)
        if index % 10 == 0 or index == len(images):
            print(f"Processando frame {index}/{len(images)}")

    writer.release()
    print(f"Vídeo salvo em: {output_path}")
    return output_path


def save_frames_text(
    maze_file: str = DEFAULT_MAZE_PATH,
    output_file: str | Path = DEFAULT_FRAMES_OUTPUT,
    strategy: str = DEFAULT_STRATEGY_ID,
    result: SimulationResult | None = None,
) -> Path:
    if result is None:
        print("Executando simulação...")
        result = run_simulation(
            maze_path=maze_file,
            display_report=False,
            strategy_id=strategy,
        )

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="ascii") as out:
        for index, frame in enumerate(result.frames, start=1):
            out.write(f"=== FRAME {index} ===\n")
            out.write(frame + "\n")
            out.write("=" * 50 + "\n\n")

    print(f"Frames salvos em: {output_path}")
    return output_path


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera vídeo e/ou arquivos de texto com os frames da simulação.",
    )
    parser.add_argument(
        "--maze",
        default=DEFAULT_MAZE_PATH,
        help=f"Caminho para o arquivo do labirinto (padrão: {DEFAULT_MAZE_PATH}).",
    )
    parser.add_argument(
        "--video",
        default=str(DEFAULT_VIDEO_OUTPUT),
        help="Arquivo MP4 de saída (padrão: results/videos/maze_simulation.mp4).",
    )
    parser.add_argument(
        "--frames",
        default=str(DEFAULT_FRAMES_OUTPUT),
        help="Arquivo de texto para salvar os frames (padrão: results/frames/frames.txt).",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=3,
        help="Quadros por segundo do vídeo (padrão: 3).",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=20,
        help="Tamanho do bloco em pixels (padrão: 20).",
    )
    parser.add_argument(
        "--strategy",
        default=DEFAULT_STRATEGY_ID,
        help="Estratégia de movimentação (padrão: exploration).",
    )
    parser.add_argument(
        "--skip-video",
        action="store_true",
        help="Pula a geração do vídeo e salva apenas os frames em texto.",
    )
    parser.add_argument(
        "--skip-text",
        action="store_true",
        help="Pula o arquivo de texto e gera apenas o vídeo.",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> None:
    import sys

    namespace = parse_args(argv or sys.argv[1:])

    if not namespace.skip_text:
        save_frames_text(
            maze_file=namespace.maze,
            output_file=namespace.frames,
            strategy=namespace.strategy,
        )

    if not namespace.skip_video:
        try:
            create_video(
                maze_file=namespace.maze,
                output_file=namespace.video,
                fps=namespace.fps,
                scale=namespace.scale,
                strategy=namespace.strategy,
            )
        except RuntimeError as exc:
            print(exc)
            print("Instale as dependências opcionais com: pip install opencv-python numpy")


if __name__ == "__main__":
    main()
