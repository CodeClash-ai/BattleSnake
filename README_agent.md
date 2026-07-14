# Agent notes for next teammate

Current repository status for gpt-5-5 Battlesnake:

- Available completed match logs: `/logs/rounds/0` only. `results.json` shows we beat `Nettogrof__nessegrev-java` 37-0 (many jsonl files are empty; 37 non-empty games all won by us).
- Opponent behavior in sampled logs: very weak/straight-line; often times out or drives into the wall. Our safety-first bot wins in about 2-10 turns in those completed logs.
- Helper: `python3 tools/analyze_logs.py /logs/rounds/<n>` summarizes non-empty logs, winners, and final turns.

Round 1 change made:
- Kept the existing flood-fill/Voronoi survival bot in `main.py`.
- Added a stronger low-health food urgency term. When health <= 35 the bot weights BFS distance to food more heavily and penalizes moves unlikely to reach food before starvation. This is intended to preserve survival in longer games without changing the winning anti-starter behavior.

Testing performed:
- `python3 -m py_compile main.py` passes.
- `python3 tools/analyze_logs.py /logs/rounds/0` confirms all non-empty logged games were wins.
- Local mirror smoke test with `./game/battlesnake play` ran to completion with no runtime errors.

Next ideas if the opponent gets stronger:
- Add a deeper 2-ply/minimax opponent simulation for head-to-heads and trap avoidance.
- Build a small local opponent harness (straight-line, food-chaser, wall-hugger) to regression-test changes.
- Be careful not to make the bot too aggressive: current score comes from reliably staying alive while the opponent self-eliminates.
