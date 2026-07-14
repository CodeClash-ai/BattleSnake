# Agent notes for next teammate

Current repository status for gpt-5-5 Battlesnake:

- Completed match logs available: `/logs/rounds/0`.
- Round 0 result: won 20-0 against `csauve__bookworm`.
- Opponent profile from round 0: `csauve__bookworm` mostly drives vertically until it hits a wall. Starts in top half go down; starts elsewhere go up. It never beat us in non-empty logs.
- Round 2 review: I re-checked the logs and re-ran validation/smoke tests. Because the current bot already swept the known opponent and the opponent appears extremely exploitable, I made no `main.py` strategy change this round (reliability > risky tuning).

Useful helper scripts:

- `python3 tools/analyze_logs.py /logs/rounds/<n>` summarizes non-empty logs, winners, and final turns.
- `python3 tools/opponent_profile.py /logs/rounds/<n>` counts opponent start positions and observed move deltas.
- `python3 tools/inspect_round.py /logs/rounds/<n>` prints the first non-empty game turn-by-turn for quick manual inspection.
- `python3 tools/replay_moves.py /logs/rounds/<n>` replays current `main.move` over logged states and checks it always returns a valid direction.
- `tools/simple_opponent.py` is a tiny Flask opponent for local smoke tests, e.g. start our server and `python3 tools/simple_opponent.py up 8001`, then use `./game/battlesnake play ...`.

Bot status:

- Main player code is `main.py`.
- Strategy is a compact safety-first flood-fill/Voronoi survival bot with head-to-head avoidance, center/open-space preference, and food urgency.
- Previous teammate made one conservative change: when health <= 30, reachable food distance gets an extra direct score penalty/bonus so the bot is less likely to let flood-fill area dominate and starve in longer games. This should not affect the short current-opponent games unless health is genuinely low.
- Given current logs, reliability is the priority. Avoid risky aggression unless future logs show a stronger opponent.

Testing performed in round 2:

- `python3 tools/analyze_logs.py /logs/rounds/0` confirms all 20 non-empty games were wins.
- `python3 tools/opponent_profile.py /logs/rounds/0` confirms the opponent's vertical straight-line behavior: deltas `(0, 1)` and `(0, -1)` only.
- `python3 -m py_compile main.py` passes.
- `python3 tools/replay_moves.py /logs/rounds/0` passes (`checked_states=59 bad=0`).
- Local CLI smoke tests this round: 10/10 wins vs `tools/simple_opponent.py up`; 50/50 wins vs a temporary greedy head-chasing opponent; 43/50 wins vs `tools/simple_opponent.py food`. Known opponent is much weaker than these local tests.

Next ideas if the opponent gets stronger:

- Add a deeper 2-ply/minimax opponent simulation for head-to-heads and trap avoidance.
- Build more local regression opponents (wall-hugger, tail-chaser, aggressive head-to-head) and run many seeded games before changing scoring weights.
- Consider adding dead-end/corridor detection for long games; in local tests vs the greedy food opponent, some losses came from eventually following a wall corridor into a self/enemy-body pocket.
- Be careful not to make the bot too aggressive: current wins come from staying alive while simple opponents self-eliminate.

Round 1 (current handoff) notes:

- I reviewed `/logs/rounds/0` again: scoreboard says `gpt-5-5` beat `coreyja__improbable-irene` 20-0; non-empty logs are still all wins. Opponent movement profile from logs is almost entirely straight upward with one left delta, so the current conservative survival bot is already well matched.
- Validation run this round: `python3 -m py_compile main.py` and `python3 tools/replay_moves.py /logs/rounds/0` both passed (`checked_states=47 bad=0`).
- Local smoke test vs `tools/simple_opponent.py up`: 30/30 wins.
- I briefly tried adding a second-step flood-fill tie-breaker to avoid future corridor traps. It preserved 30/30 vs straight-up but worsened local greedy-food results (45/50 vs the previous ~48/50 on seeds 1-50), so I reverted it. No strategy changes are currently pending.
- Recommendation: keep reliability unless future logs show a stronger or different opponent. If experimenting, compare across fixed seed ranges vs `simple_opponent.py food` and the known straight-line profile before keeping changes.
