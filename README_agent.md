# Agent notes for next teammate

Current repository status for gpt-5-5 Battlesnake:

- Completed match logs available this round: `/logs/rounds/0`.
- Round 0 result: won 20-0 against `csauve__bookworm`.
- Opponent profile from round 0: `csauve__bookworm` mostly drives vertically until it hits a wall. Starts in top half go down; starts elsewhere go up. It never beat us in non-empty logs.

Useful helper scripts:

- `python3 tools/analyze_logs.py /logs/rounds/<n>` summarizes non-empty logs, winners, and final turns.
- `python3 tools/opponent_profile.py /logs/rounds/<n>` counts opponent start positions and observed move deltas.
- `python3 tools/inspect_round.py /logs/rounds/<n>` prints the first non-empty game turn-by-turn for quick manual inspection.
- `python3 tools/replay_moves.py /logs/rounds/<n>` replays current `main.move` over logged states and checks it always returns a valid direction.
- `tools/simple_opponent.py` is a tiny Flask opponent for local smoke tests, e.g. start our server and `python3 tools/simple_opponent.py up 8001`, then use `./game/battlesnake play ...`.

Bot status:

- Main player code is `main.py`.
- Strategy is a compact safety-first flood-fill/Voronoi survival bot with head-to-head avoidance, center/open-space preference, and food urgency.
- This round I made one conservative change: when health <= 30, reachable food distance gets an extra direct score penalty/bonus so the bot is less likely to let flood-fill area dominate and starve in longer games. This should not affect the short current-opponent games unless health is genuinely low.
- Given current logs, reliability is the priority. Avoid risky aggression unless future logs show a stronger opponent.

Testing performed this round:

- `python3 tools/analyze_logs.py /logs/rounds/0` confirms all 20 non-empty games were wins.
- `python3 tools/opponent_profile.py /logs/rounds/0` confirms the opponent's vertical straight-line behavior: deltas `(0, 1)` and `(0, -1)` only.
- `python3 -m py_compile main.py` and `python3 tools/replay_moves.py /logs/rounds/0` pass (`checked_states=59 bad=0`).
- Local CLI smoke tests using `tools/simple_opponent.py`: 10/10 wins vs `up`, 10/10 wins vs greedy `food`.

Next ideas if the opponent gets stronger:

- Add a deeper 2-ply/minimax opponent simulation for head-to-heads and trap avoidance.
- Build more local regression opponents (wall-hugger, tail-chaser, aggressive head-to-head) and run many seeded games before changing scoring weights.
- Be careful not to make the bot too aggressive: current wins come from staying alive while simple opponents self-eliminate.
