# Agent notes for next teammate

Round 1 replaced the original faithful `pambrose` SimpleSnake port in `main.py` with a safety-first Battlesnake.

Observed logs in `/logs/rounds/0` showed the opponent as `pambrose__pambrose-kotlin`, a very naive food-chasing snake. Baseline was only about 89 wins / 82 losses / 79 draws over 250 games because both snakes ran into walls quickly.

Current bot strategy:
- filters illegal moves (walls, bodies, neck reverse), allows vacating tails when safe;
- avoids equal/losing head-to-head squares;
- scores moves by flood-fill reachable space and exit count;
- gets food when low health / not longer / very close, but otherwise values central open space;
- modestly pressures when longer and keeps distance when not.

Local smoke test against a copy of the old `main.py` won 120/120 games (seeds 0-119, both name orders) using `./game/battlesnake play` with two local Flask servers.

Useful helper:
- `tools/analyze_logs.py /logs/rounds/0` summarizes winners and final turns from jsonl logs.

If future rounds face a stronger bot, likely next improvements are deeper lookahead/minimax for head-to-heads and trap detection. Against this opponent, survival is enough.
