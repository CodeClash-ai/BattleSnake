# Agent notes for next teammate

Current repository status for gpt-5-5 Battlesnake:

- Completed match logs now available: `/logs/rounds/0` and `/logs/rounds/1`.
- Results so far are excellent: round 0 won 37-0, round 1 won 33-0 against `Nettogrof__nessegrev-java`.
- Only a subset of sim files are non-empty, but every non-empty logged game in both rounds was won by us.
- Opponent profile from both rounds: `Nettogrof__nessegrev-java` appears to always move `up` (all observed head deltas are `(0, +1)`) and usually dies by hitting the top wall on turns 2-10. Our survival-first bot wins by not self-eliminating.

Useful helper scripts:

- `python3 tools/analyze_logs.py /logs/rounds/<n>` summarizes non-empty logs, winners, and final turns.
- `python3 tools/opponent_profile.py /logs/rounds/<n>` counts opponent start positions and observed move deltas. This confirmed the always-up behavior in rounds 0 and 1.
- `python3 tools/inspect_round.py /logs/rounds/<n>` prints the first non-empty game turn-by-turn for quick manual inspection.
- `python3 tools/replay_moves.py /logs/rounds/<n>` replays current `main.move` over logged states and checks it always returns a valid direction.

Bot status:

- Main player code is `main.py`.
- Strategy remains a compact safety-first flood-fill/Voronoi survival bot with head-to-head avoidance, center/open-space preference, and low-health BFS food urgency.
- Given the current opponent, do **not** make risky aggressive changes unless logs show the opponent improved. Reliability is enough to win because the opponent self-eliminates.

Testing performed this round:

- `python3 tools/analyze_logs.py /logs/rounds/1` confirms all non-empty round 1 games were wins.
- `python3 tools/opponent_profile.py /logs/rounds/0` and `/logs/rounds/1` confirm all observed opponent moves were up.
- `python3 -m py_compile main.py tools/*.py` passes.
- `python3 tools/replay_moves.py /logs/rounds/0` checked 98 logged states with no bad moves; `/logs/rounds/1` checked 132 states with no bad moves.
- Attempted `(cd game && go test ./...)`; it timed out while trying to download Go test dependencies. This does not affect Python bot validity.

Next ideas if the opponent gets stronger:

- Add a deeper 2-ply/minimax opponent simulation for head-to-heads and trap avoidance.
- Build local regression opponents (straight-line, food-chaser, wall-hugger) to test changes.
- Be careful not to make the bot too aggressive: current score comes from reliably staying alive while the opponent self-eliminates.
