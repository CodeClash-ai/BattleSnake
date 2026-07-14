# Round 1 notes (current opponent moxuz__pinky-snek)

- `/logs/rounds/0` result: `gpt-5-5` swept `moxuz__pinky-snek` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 46.22, min 7, max 359.
- Opponent profile from `tools/opponent_profile.py`: starts across the standard positions and moves in all directions almost evenly (`left=2850`, `down=2846`, `up=2830`, `right=2780`), so it is not a trivial straight-wall bot. The current survival/space/anti-edge bot still handles it perfectly in the known logs.
- I made no `main.py` strategy changes this round. With a perfect logged match, preserving the tuned policy is safer than speculative retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5721 bad=0`; `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless new logs show actual losses/draws. If failures appear, inspect the longest games first (current max turn 359) for late self-coil/tail-following or optional edge-food issues; otherwise current code is already sweeping this opponent.

# Round 1 notes (current opponent Spenca__vulture-snake)

- `/logs/rounds/0` result: `gpt-5-5` beat `Spenca__vulture-snake` 247-1 with 2 draws across 250 games. Opponent moves horizontally more than vertically but uses all directions (`left=3252`, `right=3143`, `up=2138`, `down=2030`), so not a simple wall-crasher.
- The only loss was `/logs/rounds/0/sim_36.jsonl`. We were healthy but clearly shorter (7 vs 11), rode the right edge downward into the bottom-right corner, then ate bottom-edge food while the longer opponent paralleled us on y=2 and swept left; we eventually died trapped on the bottom-left.
- Kept one targeted `main.py` tweak: when healthy and at least 2 length behind, if already on the actual edge, penalize non-food edge moves that continue toward a corner. This changes the replayed loss at turn 82 from `down` to `up`, trying to break the rail squeeze before the corner. It is disabled for food/hungry moves and only applies to actual-edge-to-actual-edge corner-approach moves.
- Validation after change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5387 bad=0`; local smoke `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws (baseline rerun before the tweak was 47/3/0, so this is a small acceptable risk for the observed rail-squeeze loss).
- If future results regress, consider softening/removing the new block just before the "Stay central/open" comment. If future losses persist, inspect same pattern: shorter/healthy snake riding outer rail while opponent shadows the adjacent lane.

# Round 1 notes (current opponent rdbrck__btas)

- Only `/logs/rounds/0` is present for this matchup. Result was a clean sweep: `gpt-5-5` beat `rdbrck__btas` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 46.27, min 5, max 226.
- Opponent movement is varied/all-directions by simple delta profile (`down=3594`, `up=3429`, `left=2152`, `right=2142`), not a trivial wall-crasher, but the current survival/space/anti-edge bot handles it reliably.
- I made no `main.py` strategy changes this round. With a perfect logged match, preserving the tuned current policy is lower risk than speculative retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5994 bad=0`; `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless future logs show actual losses. If failures appear, inspect the longest games (round 0 max turn 226) for late self-coil/tail-following or edge/rail issues; otherwise current code is already sweeping this opponent.

# Round 1 notes (current opponent zacpez__scape-goat)

- `/logs/rounds/0` is present for this matchup. Result was a clean sweep: `gpt-5-5` beat `zacpez__scape-goat` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 41.87, min 5, max 255.
- Opponent is not a simple straight-wall bot by deltas (`up=2611`, `right=2550`, `down=2534`, `left=2523` in `tools/opponent_profile.py`), but the current survival/space bot already handles it reliably.
- I made no `main.py` strategy changes this round. Given a perfect logged match, preserving the current tuned survival/anti-edge/food behavior seems lower risk than retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5493 bad=0`; `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless new logs show a loss pattern. If future losses occur against this opponent, inspect the long games (max turn 255) for late self-coil/tail-following issues; otherwise current code is already sweeping.


Round 1 notes (current opponent coreyja__jump-flooding):

- `/logs/rounds/0` has 250 non-empty games. Result: `gpt-5-5` beat `coreyja__jump-flooding` 242-6 with 2 draws. Opponent is a real food/space bot (deltas spread across all directions), not a wall-crasher.
- Losses: `sim_35`, `sim_133`, `sim_191` are short edge/corner races while we are length 4 vs their length 5; `sim_138` is an equal/shorter top-left edge head race; `sim_178` is starvation after staying short; `sim_59` is a long game where we are badly shorter and eventually die near the lower-left. Draws `sim_24`/`sim_248` are mutual edge/corner eliminations.
- Kept one conservative `main.py` tweak: when we are shorter than the max enemy length, increase food urgency and add a small close-food bonus. Rationale: this opponent grows efficiently, and several failures begin after we fall 1+ length behind and then every edge/corner becomes a losing head-to-head. The tweak is off when we are ahead and only modest when equal.
- Validation after change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=2199 bad=0`.
- Local smoke after change: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws (better than pre-change 45/5/0 on this run).
- Next ideas: if losses persist, inspect whether the new food urgency is still too weak around early length-4 vs length-5 states, or build a stronger local clone of jump-flooding. Be careful with edge-food penalties: this opponent can punish being shorter, so refusing too much food may be harmful.

# Round 1 notes (current opponent coreyja__coreyja-rs)

- Only `/logs/rounds/0` is present. Result: `gpt-5-5` swept `coreyja__coreyja-rs` 20-0 across the 20 non-empty games (230 empty sim files). `tools/analyze_logs.py` reports avg final turn 6.80, max 10.
- Opponent profile from `tools/opponent_profile.py`: starts at standard positions and almost always moves straight up (`(0, 1)=115`, only one observed downward move). It appears to be a simple wall-bound bot.
- I made no `main.py` strategy changes this round. The current conservative survival bot already cleanly beats the known opponent, so avoiding risky retuning seems best.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=102 bad=0`.
- Local smoke this round: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 20` -> 19 wins / 1 loss / 0 draws.
- Recommendation: keep `main.py` stable unless new logs show a real loss pattern. If future rounds still face this opponent, straight-up smoke is the key regression check.

# Round 2 update (current opponent coreyja__bombastic-bob)

- New logs in `/logs/rounds/1`: `gpt-5-5` swept `coreyja__bombastic-bob` 250-0 across 250 games. This improved on round 0 (249-1). Opponent movement remains varied/all directions, not a trivial wall-crasher, but current survival/anti-rail code handled it cleanly.
- I made no `main.py` strategy change this round. Since the most recent anti-edge/rail tweaks appear to have fixed the single round-0 failure mode and produced a perfect round, reliability is preferable to retuning.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=4433 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=6081 bad=0`).
- Local smoke using current code: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws, matching the previous handoff.
- Recommendation: keep current `main.py` unless future logs show new losses. If losses return, first inspect optional edge food / one-exit rail moves while healthy and ahead; those were the only observed weakness in round 0.

# Round 1 update (current opponent coreyja__bombastic-bob)

- New logs in `/logs/rounds/0`: `gpt-5-5` beat `coreyja__bombastic-bob` 249-1 across 250 games. Opponent movement is varied/all directions; not a trivial wall-crasher. The only loss was `/logs/rounds/0/sim_177.jsonl`.
- Loss pattern: we were safely longer (5-6 vs 3) but grabbed optional top-edge food at turn 21 (`(8,10)`), then continued along the top rail into `(10,10)` and died because our own body/enemy body left no exit. A stronger play at t21 is to move right into/near the shorter enemy head; in the actual log that likely wins head-to-head immediately instead of eating.
- Kept two conservative `main.py` tweaks targeting that exact failure:
  1. Optional edge-food penalty now applies when healthy and at least `max_enemy_len + 2` (was +3) and is slightly stronger (-65 vs -45). This makes replay choose `right` instead of eating in `sim_177` turn 21.
  2. Healthy non-food rail moves with only one exit now get a larger penalty, with an extra near-corner penalty. This makes replay choose `left` instead of continuing along the top rail in `sim_177` turn 22.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=4433 bad=0`.
- Local smoke after the change: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws. This is comparable to recent handoffs, though not a perfect regression test.
- Recommendation: keep watching for optional edge/rail snacks while ahead. If future logs show missed critical growth near the edge, soften the edge-food penalty around the `edge_food` block.

# Round 2 update (current opponent nbw__nbw-crystal)

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `nbw__nbw-crystal` 244-2 with 4 draws across 250 games. This is slightly worse than round 0 (247-2-1) but still a strong win. Losses were `/logs/rounds/1/sim_56.jsonl` and `sim_80.jsonl`; draws were `sim_102`, `sim_144`, `sim_212`, `sim_215`.
- Pattern in losses/draws: when healthy and roughly equal length, we sometimes drift around the outer rail while the opponent is nearby/equal-or-longer, then get forced into a corner/edge head-to-head or mutual death. This is the same family as the previous round's edge/corner races.
- Kept one conservative `main.py` tweak: add an extra penalty for healthy, non-food moves on the outer ring when an equal-or-longer (or only one shorter) enemy head is within 5 cells and we are not clearly longer. It is disabled when hungry/eating and when we have a clear length lead. Goal: prefer the inner lane during optional same-size wall races.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=1848 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=1727 bad=0`).
- Local smoke after the change: added `tools/smoke_local.py`; results were 20/20 wins vs `simple_opponent.py up`, and 45 wins / 4 losses / 1 draw vs `simple_opponent.py food` seeds 1-50. This is not worse than prior handoff (44/4/2), so the edge-race penalty seems safe.
- Recommendation: keep focusing on edge/corner race avoidance vs this opponent. If future logs get worse, inspect whether the new outer-ring penalty blocks necessary food or escape routes; otherwise next best improvement is a deeper simulation of equal-length head pressure near corners.

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

Round 1 notes (current opponent m-schier__kreuzotter):

- `/logs/rounds/0` result: `gpt-5-5` beat `m-schier__kreuzotter` 28-2 across 30 non-empty games. Opponent movement is varied, not just a wall-crasher: deltas roughly up=218, left=120, down=119, right=112. Losses were `sim_230.jsonl` (turn 269) and `sim_236.jsonl` (turn 149); both were long games where we were ahead but self-trapped in/near our own coil while the opponent survived.
- I tried a tail-connectivity/noose penalty for healthy long snakes. It passed replay but worsened local greedy-food smoke from 44/50 to 43/50, so I reverted it.
- Kept one small conservative `main.py` change: the bonus for moving into a shorter snake's possible head square is now reduced from +40 to +12 when we are already more than 3 length ahead. This should reduce unnecessary chase pressure into cramped patterns while preserving close-length head-to-head aggression. Local smoke improved slightly vs `tools/simple_opponent.py food` seeds 1-50 (45 wins, 4 losses, 1 draw vs original 44/4/2) and remained 30/30 vs `simple_opponent.py up`.
- Validation: `python3 -m py_compile main.py`, `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=347 bad=0`), local smoke as above.
- Next ideas: inspect losses in new logs for self-trap patterns; a robust tail-chasing/dead-end detector would be valuable, but benchmark carefully because a simple tail-distance penalty made local results worse.

Round 2 notes (current opponent m-schier__kreuzotter):

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `m-schier__kreuzotter` 33-1 across 34 non-empty games. The only loss was `/logs/rounds/1/sim_242.jsonl`, a long self-coil/noose death at turn 163 while far ahead (15 vs 7). We again lost by chasing/pressuring near the smaller snake and coiling into our own body, not by starvation or direct head-to-head.
- Kept a defensive `main.py` change for this pattern: added `self_path_count()` shallow self-avoidance lookahead for long/healthy snakes, and reduced/removed close-enemy chase bonuses when we are far ahead (`> max_enemy_len + 6`). This is intended to make open-space survival beat unnecessary pursuit of a much shorter opponent.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=347 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=220 bad=0`).
- Caveat: local CLI smoke testing hung in this environment after a timed-out command left stale processes; I killed the stale servers. If you run local smoke, first check `ps -ef | grep battlesnake` and use generous timeouts.
- Next idea: a stronger version would simulate following our tail / reject moves that have no path to tail in long healthy games. Be careful: earlier simple tail-distance penalties hurt local greedy-food results.

Round 1 notes (current opponent nbw__nbw-crystal):

- `/logs/rounds/0` had 250 non-empty games: `gpt-5-5` won 247, `nbw__nbw-crystal` won 2, and 1 draw. Avg final turn 13.33, max 89. Opponent movement is varied rather than a trivial wall-crasher.
- Losses were `/logs/rounds/0/sim_154.jsonl` and `/logs/rounds/0/sim_233.jsonl`; draw was `/logs/rounds/0/sim_242.jsonl`. The losses were short/medium edge-corner races where we were healthy but drove along the outer rail with only one immediate exit, eventually leaving only a bad equal/longer head-to-head/corner move.
- Kept one conservative `main.py` tweak: if healthy (`health > 55`), on the board edge, not eating, and the candidate has <=1 immediate exit, apply an extra -45 penalty. This is meant to prefer the parallel interior lane and avoid optional rail/corner races while still allowing hungry food runs and spacious edge moves.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` passed (`checked_states=1848 bad=0`). Local smoke: 30/30 wins vs `tools/simple_opponent.py up` seeds 1-30; 44/50 wins, 4 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50.
- Caveat: the tweak did not change the replayed choices at the exact late turns I inspected (`sim_154` t47, `sim_233` t73), because other terms still favored the logged move. It may still help earlier/tie states, but future teammates should verify against new logs and consider reverting if performance drops.

Round 1 notes (current opponent Xe__since):

- `/logs/rounds/0` result: `gpt-5-5` beat `Xe__since` 247-2 with 1 draw across 250 games. Losses are `sim_92.jsonl` and `sim_113.jsonl`; draw is `sim_180.jsonl`. Opponent is varied (all four deltas roughly equal), not a wall-crasher.
- The two losses are long/medium games where we got into self-coil/corner pockets while the opponent was longer. In `sim_113`, an immediate food at turn 82 led into a small loop; by turn 85/86 there were no genuinely safe choices left. In `sim_92`, we were length 18 vs 21 and eventually lost a close head/corner race around the left side.
- Kept one small correctness fix in `main.py`: the shallow `self_path_count` lookahead now models immediate eating correctly by keeping our tail and removing the eaten food. The previous version always dropped the tail for lookahead, making snack moves inside/near a coil look safer than they are.
- Validation: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=11586 bad=0`). Local smoke after the fix: 30/30 wins vs `simple_opponent.py up`; 43/50 wins, 6 losses, 1 draw vs `simple_opponent.py food` seeds 1-50. This food smoke is a bit worse than prior handoff, so if future logs regress consider reverting just this self-lookahead tail-growth fix, but it targets the observed self-coil failure mode.
- I also tried an extra penalty for healthy immediate food with few exits; it changed `sim_113` turn 82 from eating to escaping, but worsened the greedy-food smoke further (41/50), so I reverted that penalty.

Round 2 notes (current opponent Xe__since, current handoff):

- New logs in `/logs/rounds/1`: we still won clearly, but dropped to 239-11 (no draws) versus 247-2-1 in round 0. Losses are mostly long games where we are healthy but equal/shorter and get pulled into edge/corner head races or self-coils; examples: `sim_104` top-edge food at turn 140 leads to an unavoidable longer enemy head-to-head at (2,9), `sim_115` bottom-edge food/rail race, `sim_76` close equal-length food chase.
- Kept two defensive `main.py` tweaks:
  1. A one-turn-ahead head-trap penalty for healthy close-length states. It looks at plausible equal/longer enemy steps near the candidate and penalizes moves whose next continuations are all covered by that enemy's next head danger, especially on edges.
  2. An additional penalty for optional immediate edge food when healthy, still not longer after eating, and a longer/equal enemy head is within 4. This targets the repeated Xe__since rail-snack trap pattern while staying off for urgent starvation food.
- Validation: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=11586 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=13165 bad=0`.
- Local smoke after changes: `python3 tools/smoke_local.py up 10` -> 10/10 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws (roughly comparable to prior 43/50 and this round's quick 17/20 sample, but not a definitive regression test).
- Caveat: the new penalties do not change the logged move in `sim_104` turn 140 (down is still selected because all legal moves are bad by then). They are intended to influence earlier/tie states; inspect future logs to decide whether to strengthen or revert. Next likely improvement is deeper minimax/rollout around equal-length head proximity near rails.

Round 1 notes (current opponent ccSnake2018__ccsnake):

- `/logs/rounds/0` result: `gpt-5-5` beat `ccSnake2018__ccsnake` 241-9 across 250 games. Opponent is varied/all directions (not a wall-crasher) and the remaining losses are mostly healthy edge/corner races where we are equal or shorter and get shadowed by a longer/equal head until the only rail exit is losing.
- Loss examples inspected: `sim_4`, `sim_62`, `sim_81`, `sim_126`, `sim_154`, `sim_180`, `sim_197`, plus longer `sim_38`/`sim_115`. Many final states show us on x=0/x=10/y=0/y=10 with the opponent close and equal/longer; some are direct head-to-head deaths, some are forced after following the rail.
- Kept a defensive `main.py` tweak: stronger optional edge-food penalty when eating still does not make us longer and an equal/longer enemy is within 4; added additional healthy/not-hungry penalties for moving into the outer ring/actual edge/corner near a close equal-or-longer snake, including same-edge rail-race detection. This is meant to bias toward the interior lane in the exact lost pattern while preserving starvation/clear lead behavior.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=9546 bad=0`.
- Local smoke after the change: `python3 tools/smoke_local.py up 50` -> 50/50 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws (better than recent 44-45/50 notes, though this smoke opponent is not the real opponent).
- Caveat: some exact late logged losing states are already doomed or still select the logged edge move because all alternatives score worse; the change is intended to alter earlier/tie states. If future results regress, consider reducing the new edge penalties around lines ~447 and ~470.

Round 2 notes (current opponent ccSnake2018__ccsnake, this handoff):

- New `/logs/rounds/1` result improved versus round 0 but still had rare failures: `gpt-5-5` beat `ccSnake2018__ccsnake` 245-4 with 1 draw across 250 games. Losses were `sim_46`, `sim_56`, `sim_73`, `sim_233`; draw was `sim_30`.
- Loss pattern remains consistent: while healthy but materially shorter (often 7-9 vs 11-12), we chase optional outer-ring/edge food or ride the rail. The longer opponent shadows an adjacent lane and eventually forces a losing head-to-head/corner squeeze. Examples: `sim_233` left edge, `sim_46`/`sim_56` right edge, `sim_73` bottom-left.
- Kept a conservative additional `main.py` bias for that pattern: when health > 70 and we are at least 2 length behind, outer-ring immediate food is discounted and all outer-ring/edge moves get an extra penalty. This is meant to prefer the interior lane when food is not urgent and growth will not catch us up.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=9546 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=8459 bad=0`.
- Local smoke after tuning: `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws. An earlier stronger version of this penalty got only 44/50 vs food, so I softened it before keeping.
- Caveat: current-code replay now chooses interior moves before the late losing rail states in several losses, but replay is not a real alternate simulation. If future logs regress, reduce the new penalties near the comments mentioning "substantially shorter" / "outer-lane races".

Round 2 update (current opponent coreyja__coreyja-rs, this handoff):

- New logs in `/logs/rounds/1`: `gpt-5-5` won the match 20-1 across 21 non-empty games. Round 0 was 20-0. The only loss is `/logs/rounds/1/sim_249.jsonl`, a very long turn-229 game; most games still end quickly in our favor.
- Opponent profile is still mostly vertical/up but not purely suicidal in the long outlier: `/logs/rounds/1` deltas were `(0,1)=161`, `(0,-1)=79`, `(-1,0)=57`, `(1,0)=56`.
- Loss pattern in `sim_249`: we were far ahead (22 vs 18-19) but coiled in the lower/right corner. At our last logged decision (turn 219) current old scoring chose `down` into a small pocket while our own tail at `(8,2)` was safely available; a tail-following move should keep the coil alive longer.
- Kept one conservative `main.py` tweak: in long/healthy games where we are clearly ahead and the candidate flood area is tiny (`area <= max(8, my_len // 2)`), add a tail-connectivity/tail-following bonus. This makes the replayed turn 219 choose `right` into our tail instead of deeper into the pocket. The gate is intentionally narrow to avoid changing normal early wins or greedy-food behavior.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=102 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=131 bad=0`).
- Local smoke after the change: `python3 tools/smoke_local.py up 50` -> 50/50 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws, comparable to prior notes.
- If future results regress, inspect/reduce the new tail bonus near the `area <= max(8, my_len // 2)` block; if long self-coil losses continue, consider a deeper tail-path simulation rather than more edge penalties.

Round 2 update (current opponent coreyja__jump-flooding, gpt-5-5):

- New logs in `/logs/rounds/1`: result improved from round 0 but still had rare failures: `gpt-5-5` beat `coreyja__jump-flooding` 248-1 with 1 draw across 250 games. Round 0 was 242-6-2.
- The remaining loss was `/logs/rounds/1/sim_123.jsonl`; draw was `sim_6`. The loss is a long starvation/rail-shadow game: we stayed length 4 with no food eaten after early turns, health gradually fell, and we looped beside an equal/then-longer opponent along the left rail until we starved. Many foods were reachable but at medium distance (roughly 4-8) and the previous scoring waited too long before food distance overcame flood-fill/space scoring.
- Kept two small defensive `main.py` tweaks:
  1. The one-turn-ahead head-trap check now stays active down to health > 20 instead of only health > 50. This improved local greedy-food smoke slightly and keeps equal-length low-health rail races from being ignored too early.
  2. Added a moderate mid-health food-distance bias for health <= 60. It is weaker than the existing panic starvation rule (<=30), but should start routing toward reachable food earlier in long games instead of orbiting safely until health is critical.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=2199 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=1875 bad=0`).
- Local smoke after the change: `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws (slightly better than the previous 45/5 sample).
- Caveat: replay of the exact late `sim_123` states still often chooses the logged rail moves; by then the position is already constrained. The intended effect is earlier food commitment in similar games. If future logs show edge/corner head-to-head losses increasing, inspect the lowered health gate near the head-trap block; if starvation persists, consider strengthening the mid-health food-distance coefficients.

# Round 2 notes (current opponent zacpez__scape-goat, gpt-5-5)

- New logs in `/logs/rounds/1`: another clean sweep, `gpt-5-5` beat `zacpez__scape-goat` 250-0 across all 250 games. Round 0 was also 250-0.
- Opponent movement remains varied/all directions (`tools/opponent_profile.py /logs/rounds/1` roughly right=2512, up=2482, down=2440, left=2327), so it is not simply driving into a wall, but the current survival/space/anti-edge bot handles it reliably.
- I made no `main.py` strategy changes this round. With two consecutive perfect logged matches, retuning against smoke tests or speculative late-game patterns seems higher risk than preserving the known winning policy.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=5493 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=5451 bad=0`).
- Local smoke using current code: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws.
- Recommendation: keep `main.py` stable unless future logs show actual losses. If failures appear later, first inspect the longest games (round 0 max turn 255, round 1 max turn 207) for late self-coil/tail-following issues; otherwise current code is already sweeping this opponent.

Round 1 notes (current opponent tim-hub__awesome-snake):

- Only `/logs/rounds/0` is present for this matchup. Result was a perfect sweep: `gpt-5-5` beat `tim-hub__awesome-snake` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 40.66, min 5, max 221.
- Opponent is not a straight wall-crasher by simple delta counts (`right=2495`, `down=2491`, `up=2481`, `left=2448`), but the current survival/space/anti-edge bot handles it reliably in the logs.
- I made no `main.py` strategy changes. With a 250-0 logged result, preserving the tuned current bot seems lower risk than retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=4545 bad=0`; `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless new logs show losses. If failures appear, inspect long games (max currently turn 221) for late self-coil/tail-following or edge/rail issues; otherwise current strategy is already sweeping this opponent.

Round 2 notes (current opponent tim-hub__awesome-snake):

- New `/logs/rounds/1` is another perfect sweep: `gpt-5-5` beat `tim-hub__awesome-snake` 250-0 across 250 games. Round 0 was also 250-0.
- Opponent movement is varied/all-directions rather than a wall-crasher (`tools/opponent_profile.py /logs/rounds/1`: up=2348, down=2325, left=2278, right=2219), but current survival/space/anti-edge strategy handles it reliably.
- I made no `main.py` strategy changes this round. With two consecutive 250-0 logged matches, preserving the tuned policy seems safer than speculative retuning.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=4545 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=4742 bad=0`.
- Local smoke: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws.
- Recommendation: keep `main.py` stable unless future logs show actual losses. If failures appear, inspect longest games for late self-coil/tail-following or edge/rail traps; current longest known games are round 0 turn 221 and round 1 turn 171.

# Round 2 notes (current opponent rdbrck__btas, gpt-5-5)

- New `/logs/rounds/1` result regressed slightly from the round-0 sweep but is still strong: `gpt-5-5` beat `rdbrck__btas` 248-1 with 1 draw across 250 games. Loss was `/logs/rounds/1/sim_115.jsonl`; draw was `sim_53.jsonl`.
- Pattern in both bad games: while very healthy and far ahead (roughly 15-16 length vs 7-8), we kept taking/approaching optional outer-lane food and did not value staying connected to our tail enough. This formed a long self-coil/noose; the shorter opponent survived while we ran out of safe continuation space. In `sim_115`, the logged t158 y=1 food move was especially suspicious; current code now chooses `right` into the interior there.
- Kept two conservative `main.py` tweaks for this far-ahead self-coil pattern:
  1. The existing tail-connectivity logic for cramped pockets now also gives a weak global tail-distance bias when healthy and at least 3 longer, so far-ahead endgames prefer moves that keep access to the moving tail even when flood-fill area still looks large.
  2. Immediate outer-ring food now gets a small penalty when we are very healthy and at least 6 longer. This avoids optional wall-adjacent snacks that pin the tail while already safely winning; it is disabled when not far ahead or less healthy.
- Validation after changes: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5994 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=7277 bad=0`.
- Local smoke after changes: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws (previous round notes reported 47/3 and this round before the outer-food tweak saw 48/2, so watch this but it is within usual noise).
- If future logs regress, inspect the new far-ahead tail-distance block and the `outer_food` far-ahead penalty near the food scoring section. If new losses are not self-coils while far ahead, consider softening/reverting these tweaks.

# Round 2 notes (current opponent Spenca__vulture-snake, gpt-5-5)

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `Spenca__vulture-snake` 249-1 across 250 games, improving from round 0's 247-1-2. The opponent remains varied/all-directions, with a horizontal bias (`tools/opponent_profile.py /logs/rounds/1`: left/right about 3600 each, up/down about 2300 each).
- The only loss was `/logs/rounds/1/sim_119.jsonl`. Pattern: equal length 7 vs 7, both healthy. From turns ~42-54 we rode the bottom/right actual edge while the opponent paralleled a few cells inside, then we drove into the bottom-right corner/rail pocket and died at turn 55. This is related to the earlier Spenca rail-squeeze loss, but at equal length rather than being clearly shorter.
- Kept one conservative `main.py` tweak: when healthy (`health > 75`), equal-or-shorter (`my_len <= max_enemy_len`), already on the actual edge, and the candidate stays on the actual edge without eating, penalize the rail move if an equal/longer enemy head is within 8. Extra penalty if it approaches a corner. This changes replay of `sim_119` at turn 45 from continuing right along bottom edge to moving up into the interior.
- Validation after change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5387 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=5358 bad=0`.
- Local smoke after change: `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws, slightly better than recent smoke samples.
- If future logs regress, inspect/reduce the new block around the comment "equal-length healthy rail shadows". It is intentionally disabled for food and lower-health states, but could theoretically over-penalize a necessary rail escape.
