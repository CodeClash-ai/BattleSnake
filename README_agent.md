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

Round 2 handoff notes:

- New logs are present in `/logs/rounds/1`. Result again favors us: `gpt-5-5` beat `coreyja__improbable-irene` 18-0. The 18 score matches the 18 non-empty sim logs; every non-empty logged game was a win.
- Re-ran log tools: `/logs/rounds/1` opponent deltas are almost all `(0, 1)` with a few `(1, 0)`, i.e. still a wall-bound straight-line/simple bot. Average game lasted only 6.56 turns.
- Validation this round: `python3 -m py_compile main.py`, `python3 tools/replay_moves.py /logs/rounds/0`, and `python3 tools/replay_moves.py /logs/rounds/1` all pass.
- Local smoke this round using current code: 30/30 wins vs `tools/simple_opponent.py up` on seeds 1-30; 44/50 wins, 4 losses, 2 draws vs `tools/simple_opponent.py food` on seeds 1-50. No `main.py` change kept; the known opponent remains much weaker than the greedy-food smoke opponent.
- Caution: when scripting CLI tests, `battlesnake play` logs to stderr, so capture `2>&1` before grepping for winners.

Round 1 (this handoff, graeme-hill__snakebot logs) notes:

- Only `/logs/rounds/0` was present this round. Result: `gpt-5-5` beat `graeme-hill__snakebot` 91-1 across 92 non-empty games (158 empty files). `python3 tools/analyze_logs.py /logs/rounds/0` reports avg final turn 17.83, min 2, max 237.
- Opponent profile is no longer the previously documented straight-only bot; observed deltas are spread across all directions: `(0,1)=556`, `(0,-1)=368`, `(1,0)=319`, `(-1,0)=306`. Still, we dominated 91-1.
- The single loss was `/logs/rounds/0/sim_248.jsonl`. We were ahead 23 length vs 17, ate unnecessary bottom-edge food at turn 169, pinned our tail, then spiraled into the lower-left corner and died on turn 185 while opponent survived. Current code replay of that logged state now chooses `left` at turn 169 rather than eating at `(4,0)`.
- Kept one conservative `main.py` tweak: when healthy and already at least 3 longer, immediate food on the board edge gets a small penalty, and the existing healthy/far-ahead near-food penalty was slightly broadened (`>= max_enemy_len + 4`, -25). Goal is to avoid optional wall snacks that can initiate self-traps without changing hungry/equal-length behavior.
- Validation this round: `python3 -m py_compile main.py` passes; `python3 tools/replay_moves.py /logs/rounds/0` passes (`checked_states=1238 bad=0`). Local smoke tests with the changed code: 30/30 wins vs `tools/simple_opponent.py up` seeds 1-30; 46/50 wins, 2 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50 (slightly better than previous handoff's 44/50 on the same smoke range, but not a perfect regression test).
- Recommendation: keep the conservative anti-edge-food tweak unless later logs show it costs early growth. For future improvements, focus on longer-game self-trap avoidance/tail-chasing once ahead; the known loss was not opponent aggression but our own wall spiral after eating.

Round 2 (current handoff, graeme-hill__snakebot) notes:

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `graeme-hill__snakebot` 94-0 across 94 non-empty games (156 empty). Avg final turn 8.17, max 34. Opponent deltas still varied but it died quickly; no losses to inspect.
- I kept one small `main.py` change: added an extra edge penalty only when healthy (`health > 60`) and the candidate edge move's flood-fill area is under 45% of the board. This is aimed at the same failure mode as the previous anti-edge-food tweak (long wall spirals / self-traps) while still allowing edge corridors when hungry or spacious.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=1238 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=372 bad=0`).
- Local smoke after the change: 30/30 wins vs `tools/simple_opponent.py up` seeds 1-30; 45/50 wins, 3 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50. I also tried simply increasing the wall penalty from 12 to 25, but that was worse (43/50 vs food), so I reverted to the conditional penalty.
- Note for local test scripts: winner log says `X was the winner` (not `X is the winner`).

Round 1 handoff notes (current opponent coreyja__devious-devin):

- Only `/logs/rounds/0` was present. Result: `gpt-5-5` beat `coreyja__devious-devin` 39-0 across all 39 non-empty logs (211 empty files). `tools/analyze_logs.py` reports avg final turn 6.08, max 10.
- Opponent profile: starts spread over standard positions, observed head deltas are almost entirely straight up: `(0, 1)=193`, with just 5 downward moves. It appears to run into the top wall quickly.
- I made no strategy change this round. Current safety-first bot is already sweeping the known opponent, and reliability seems more valuable than tuning against a simple wall-crasher.
- Validation this round: `python3 -m py_compile main.py` and `python3 tools/replay_moves.py /logs/rounds/0` passed (`checked_states=159 bad=0`).
- Local smoke: 100/100 wins vs `tools/simple_opponent.py up` seeds 1-100; 45/50 wins, 3 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50.
- Recommendation: keep current `main.py` unless new logs show losses. If experimenting, use the fixed seed smoke ranges above and make sure straight-up remains a clean sweep.

Round 2 notes (current opponent coreyja__devious-devin):

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `coreyja__devious-devin` 20-0 across all 20 non-empty logs (230 empty files). Avg final turn 7.00, min 2, max 11.
- Opponent profile remains extremely simple/wall-bound: `/logs/rounds/1` deltas were mostly straight up `(0, 1)=93`, with some down/left noise `(0, -1)=18`, `(-1, 0)=9`. It still dies quickly.
- I made no `main.py` strategy change this round. Current bot already swept both known rounds (39-0 and 20-0), and reliability against this weak opponent is more valuable than tuning.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=159 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=85 bad=0`).
- Local smoke using current code: 50/50 wins vs `tools/simple_opponent.py up` seeds 1-50; 44/50 wins, 4 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50.
- Recommendation: keep `main.py` stable unless future logs show losses or a new opponent strategy. If experimenting, benchmark against fixed seed ranges and ensure the straight-up smoke opponent remains a clean sweep.
