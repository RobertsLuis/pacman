"""HTML viewer generator for the maze simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from utils.simulation import (
    DEFAULT_MAZE_PATH,
    DEFAULT_STRATEGY_ID,
    SimulationResult,
    run_simulation,
)

DEFAULT_OUTPUT = Path("results/html/animation.html")

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset=\"utf-8\">
    <title>Simulação do Labirinto - Pac-Man IA</title>
    <style>
        body {{
            font-family: monospace;
            background: #000;
            color: #0f0;
            padding: 20px;
        }}
        .maze {{
            font-size: 16px;
            line-height: 1.2;
            white-space: pre;
            border: 2px solid #0f0;
            padding: 10px;
            background: #001100;
        }}
        .controls {{
            margin: 20px 0;
        }}
        button {{
            padding: 10px;
            margin: 5px;
            font-size: 16px;
            background: #0f0;
            color: #000;
            border: none;
            cursor: pointer;
        }}
        button:hover {{
            background: #0a0;
        }}
        .frame-info {{
            color: #ff0;
            margin: 10px 0;
            font-size: 18px;
        }}
        .legend {{
            margin-top: 20px;
            color: #888;
            background: #222;
            padding: 15px;
        }}
        select {{
            padding: 5px;
            margin: 5px;
            background: #333;
            color: #fff;
            border: 1px solid #0f0;
        }}
    </style>
</head>
<body>
    <h1>Simulação do Labirinto - Pac-Man IA</h1>
    <h2 style=\"color:#ff0;\">Estratégia: {strategy_label} ({strategy_id})</h2>
    <div class=\"frame-info\">
        <span>Frame: <span id=\"frameNum\">1</span>/{total}</span>
        <span style=\"margin-left: 20px;\">Status: <span id=\"status\">Pronto</span></span>
    </div>
    <div class=\"controls\">
        <button onclick=\"play()\">Play</button>
        <button onclick=\"pause()\">Pause</button>
        <button onclick=\"reset()\">Reset</button>
        <button onclick=\"stepForward()\">Próximo</button>
        <button onclick=\"stepBackward()\">Anterior</button>
        <span style=\"margin-left: 20px; color: #fff;\">Velocidade:</span>
        <select id=\"speed\" onchange=\"setSpeed()\">
            <option value=\"1000\">Lenta</option>
            <option value=\"500\" selected>Normal</option>
            <option value=\"200\">Rápida</option>
            <option value=\"100\">Muito rápida</option>
        </select>
    </div>
    <div class=\"maze\" id=\"mazeDisplay\">{first_frame}</div>
    <div class=\"legend\">
        <p>X = Parede | _ = Espaço livre | o = Comida</p>
        <p>E = Entrada | S = Saída | N/S/L/O = direção do agente</p>
    </div>
    <script>
        const frames = {frames_json};
        let currentFrame = 0;
        let isPlaying = false;
        let intervalId = null;
        let speed = 500;

        function updateDisplay() {{
            document.getElementById('mazeDisplay').textContent = frames[currentFrame];
            document.getElementById('frameNum').textContent = currentFrame + 1;
            if (currentFrame === frames.length - 1) {{
                document.getElementById('status').textContent = 'Concluída';
                pause();
            }} else {{
                document.getElementById('status').textContent = isPlaying ? 'Executando' : 'Pausada';
            }}
        }}

        function play() {{
            if (!isPlaying && currentFrame < frames.length - 1) {{
                isPlaying = true;
                intervalId = setInterval(() => {{
                    if (currentFrame < frames.length - 1) {{
                        currentFrame++;
                        updateDisplay();
                    }} else {{
                        pause();
                    }}
                }}, speed);
                updateDisplay();
            }}
        }}

        function pause() {{
            isPlaying = false;
            if (intervalId) {{
                clearInterval(intervalId);
                intervalId = null;
            }}
            updateDisplay();
        }}

        function reset() {{
            pause();
            currentFrame = 0;
            updateDisplay();
        }}

        function stepForward() {{
            if (currentFrame < frames.length - 1) {{
                pause();
                currentFrame++;
                updateDisplay();
            }}
        }}

        function stepBackward() {{
            if (currentFrame > 0) {{
                pause();
                currentFrame--;
                updateDisplay();
            }}
        }}

        function setSpeed() {{
            speed = parseInt(document.getElementById('speed').value);
            if (isPlaying) {{
                pause();
                play();
            }}
        }}

        document.addEventListener('keydown', function(event) {{
            switch(event.code) {{
                case 'Space':
                    event.preventDefault();
                    if (isPlaying) pause(); else play();
                    break;
                case 'ArrowRight':
                    stepForward();
                    break;
                case 'ArrowLeft':
                    stepBackward();
                    break;
                case 'KeyR':
                    reset();
                    break;
            }}
        }});

        updateDisplay();
    </script>
</body>
</html>
"""


def save_animation_html(
    maze_file: str = DEFAULT_MAZE_PATH,
    output_file: str | Path = DEFAULT_OUTPUT,
    strategy: str = DEFAULT_STRATEGY_ID,
    result: SimulationResult | None = None,
) -> Path:
    if result is None:
        result = run_simulation(
            maze_path=maze_file,
            display_report=False,
            strategy_id=strategy,
        )

    frames_json = json.dumps(result.frames)
    first_frame = result.frames[0] if result.frames else ""

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        HTML_TEMPLATE.format(
            total=len(result.frames),
            first_frame=first_frame,
            frames_json=frames_json,
            strategy_label=result.strategy_label,
            strategy_id=result.strategy_id,
        ),
        encoding="utf-8",
    )

    print(f"Animação HTML salva em: {output_path}")
    return output_path


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera visualização HTML para a simulação Pac-Man IA.",
    )
    parser.add_argument(
        "--maze",
        default=DEFAULT_MAZE_PATH,
        help=f"Caminho para o arquivo do labirinto (padrão: {DEFAULT_MAZE_PATH}).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Caminho do arquivo HTML gerado (padrão: results/html/animation.html).",
    )
    parser.add_argument(
        "--strategy",
        default=DEFAULT_STRATEGY_ID,
        help="Estratégia de movimentação (padrão: exploration).",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> None:
    namespace = parse_args(argv or [])
    save_animation_html(
        maze_file=namespace.maze,
        output_file=namespace.output,
        strategy=namespace.strategy,
    )


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
