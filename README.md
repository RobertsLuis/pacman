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

## Sensores
- **Janela local** – captura um recorte quadrado (3x3, 5x5 ou 7x7) ao redor do agente, incluindo paredes, caminhos livres e comidas. Esse sensor alimenta a memória das estratégias e é exibido nos visualizadores.
- **Sensor direcional de comida** – percorre cada direção (N, S, L, O) até a próxima parede e conta quantas comidas estão alinhadas naquele corredor. Ele pode ser habilitado ou desabilitado em qualquer workflow do `main.py`; quando ativado, os agentes priorizam a direção com maior contagem antes de seguir o plano baseado em memória.

## Estratégias disponíveis
- **Base** – comum das demais táticas. Sempre que precisa atravessar um trecho conhecido ele aplica BFS na memória do agente para achar o menor caminho até o objetivo atual.
- **Shortest Path (Menor caminho conhecido)** – tem visão completa do labirinto desde o início. Usa BFS global para correr até o alimento mais próximo e, quando termina a coleta, planeja outro BFS direto para a saída.
- **Exploration (Exploração com memória)** – avalia apenas o que já foi mapeado pelo sensor. Prioriza comida conhecida; se não houver, procura células livres ainda não visitadas; por fim parte para a saída.
- **Dead End Aware (Evita becos sem saída)** – herda a lógica de exploração, mas marca corredores que viraram becos e evita incluí-los em planos futuros, reduzindo zig-zags desnecessários.
- **Heuristic Frontier (Fronteiras heurísticas)** – também ignora becos, porém dá preferência a fronteiras com mais vizinhos desconhecidos e menor distância atual para abrir novas áreas com rapidez.
- **Sensor Greedy** – decide primeiro olhando apenas a janela do sensor: se houver comida visível, move na direção dela; caso contrário segue adiante por corredores livres e só volta ao plano de memória quando o sensor não oferece alternativa.
- **Random Walk (Caminhada aleatória)** – escolhe movimentos aleatórios entre as direções possíveis, evitando apenas desfazer o passo imediatamente anterior.

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
