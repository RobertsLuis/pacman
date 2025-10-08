# Pac-Man Agent – Quickstart

## Requisitos
- Python 3.9 ou superior
- Dependências opcionais para vídeo: `opencv-python`, `numpy`

## Instalação
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

## Primeira execução
1. Confira os mapas disponíveis em `maps/` (por padrão há `maze.txt`).
2. Rode o menu principal:
   ```bash
   python main.py
   ```
3. Escolha um mapa, informe um nome para a execução e siga as opções:
   - `1` roda todas as estratégias e permite animar no terminal.
   - `2` gera HTMLs em `results/html/`.
   - `3` salva frames em texto e tenta gerar MP4 em `results/videos/`.

## Gerar novo mapa
```bash
python utils/map_builder.py --help
```
Use os parâmetros desejados para criar um arquivo em `maps/`.
### Exemplos gerados:
```bash
python utils/map_builder.py --rows 9 --cols 15 --wall-density 0.35 --food 4 --seed 21 --output maps/compact_lab.txt
```
```bash
python utils/map_builder.py --rows 12 --cols 20 --wall-density 0.18 --food 12 --seed 314 --output maps/food_frenzy.txt
```
```bash
python utils/map_builder.py --rows 10 --cols 24 --wall-density 0.05 --food 6 --seed 73 --output maps/long_corridor.txt
```

## Limpeza
Remova arquivos antigos em `results/` se precisar liberar espaço, utilizando o comando a seguir:
```bash
python clear_results.py
```
