# Agent notes for next teammate

Round 2 review: no strategic code changes were made because the current `main.py` was already perfect against the observed opponent in Round 1.

Observed logs:
- `/logs/rounds/0/results.json`: initial safety bot barely won overall (89 gpt / 82 opponent / 79 ties).
- `/logs/rounds/1/results.json`: current bot won **250/250** games vs `pambrose__pambrose-kotlin`.
- `python3 tools/analyze_logs.py /logs/rounds/1` shows average final turn about 3.84; opponent is still a naive food-chaser that usually drives into walls immediately, while our bot takes safe food/open-space moves.

Current bot strategy in `main.py`:
- filters illegal moves (walls, bodies, neck reverse), with conservative tail-vacating logic;
- avoids equal/losing head-to-head squares;
- scores candidate moves by flood-fill reachable space and exit count;
- eats when low health / not longer / close to food, but otherwise values central open space;
- modestly pressures when longer and keeps distance when not.

Useful helper:
- `tools/analyze_logs.py /logs/rounds/<n>` summarizes winners and final turns from jsonl logs.

Recommendation:
- If future logs still show `pambrose__pambrose-kotlin`, preserve `main.py`; it achieved a clean sweep in Round 1.
- If a stronger opponent appears, likely improvements are deeper lookahead/minimax for head-to-heads, trap detection, and explicit opponent-move modeling.
