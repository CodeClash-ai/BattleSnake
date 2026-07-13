# Agent notes for future CodeClash rounds

Round 1 changed `main.py` from a faithful clone of `pambrose__pambrose-kotlin`'s SimpleSnake into a conservative survival bot.

Opponent analysis from `/logs/rounds/0`:
- Round 0 was clone-vs-clone: 78 wins / 83 losses / 89 ties for us over 250 sims.
- Games ended very early (avg ~4.6 turns) because the Kotlin SimpleSnake blindly moves toward the **farthest** food with x-axis priority and has no collision/wall avoidance.
- The opponent behavior is predictable from the old comments in `main.py`: choose farthest food (first max Manhattan), else center; if x differs move horizontally, else vertical, else up.

Current `main.py` strategy:
- Avoids out-of-bounds, bodies (with tail-moving approximation), self-collisions.
- Avoids equal/longer enemy head-to-head danger and the predicted next square of the known opponent.
- Scores legal moves mostly by flood-fill reachable area, with small preferences for central/roomy positions and food when health is low.
- Local smoke test against a recreated SimpleSnake opponent (`quick_eval.py` + `/tmp/opp.py` during this edit) got 250/250 wins for seeds 0..249.

Useful file added:
- `analyze_logs.py`: summarizes `/logs/rounds/0` outcomes and death samples. It is simple but useful as a template for new logs; later updated to infer opponent names from any logdir.

Potential future improvements:
- If opponent changes, add stronger opponent modeling or minimax. Current bot is intentionally survival-first because known opponent self-destructs.
- Consider preserving deterministic behavior; randomness can turn easy wins into ties.

Round 2 notes (current editor):
- Reviewed `/logs/rounds/1/results.json`: our Round 1 bot swept the opponent 250/250, with no losses or ties. Average game length in logs was about 7.9 turns (local `quick_eval.py` avg differs slightly because it computes from local replay states).
- Re-ran local batch with `N=250 python quick_eval.py`: again 250 wins / 0 losses / 0 ties against `tools/simple_opponent.py`.
- I intentionally left `main.py` unchanged to avoid regressing a perfect matchup. The opponent still appears to be the same deterministic farthest-food SimpleSnake.
- If future logs stop showing a sweep, first inspect whether the opponent changed. Otherwise keep this survival-first bot; it is already optimal for the known opponent in the sampled seeds.

Round 3 notes (current editor / prompt calls this round 1 but logs show only `/logs/rounds/0`):
- Rechecked `/logs/rounds/0/results.json`: our current bot won the recorded match, score 20-0.
- Ran `python analyze_logs.py /logs/rounds/0`; sampled games were all wins and short (avg ~6.35 turns).
- Ran `N=500 python quick_eval.py` against `tools/simple_opponent.py`; result was 500 wins / 0 losses / 0 ties, avg ~6.05 turns.
- Made one small `main.py` tweak after testing: predicted head-to-head squares are still avoided when the opponent is equal/longer, but are now mildly preferred when we are longer (a safe killing attack). Re-tested with `N=500 python quick_eval.py`: still 500 wins / 0 losses / 0 ties, avg ~6.02 turns. After making `analyze_logs.py` opponent-name agnostic, `N=250 python quick_eval.py` still showed 250 wins / 0 losses / 0 ties. The known opponent remains deterministic farthest-food SimpleSnake; avoid broad strategy changes unless future logs show the opponent changed.

Round 2 notes (gpt-5-5 current run):
- Available logs now include `/logs/rounds/1`; results are still a sweep for us (20-0 match score, `analyze_logs.py` shows 20/20 wins, avg 5.6 turns).
- Current `main.py` was re-tested locally with `N=500 python quick_eval.py` against `tools/simple_opponent.py`: 500 wins / 0 losses / 0 ties, avg turn ~6.01.
- I left `main.py` unchanged. The known opponent remains the deterministic farthest-food SimpleSnake and our survival-first bot is already perfect on sampled seeds; avoid unnecessary strategy churn unless new logs show the opponent changed.

Round 1 notes (gpt-5-5 current run):
- Only `/logs/rounds/0` is available in this environment; it is a 38-0 sweep for us against `Nettogrof__nessegrev-java` (confirmed with `python analyze_logs.py /logs/rounds/0`).
- The recorded opponent differs from the older `tools/simple_opponent.py` notes: every observed opponent transition in the logs is `(0, +1)`, i.e. it blindly moves up until death, sometimes after eating center food.
- Current `main.py` still wins this opponent cleanly because it is survival-first and avoids walls/bodies/head-to-heads. I left player code unchanged to avoid regressing a perfect matchup.
- Local smoke tests this round: `N=500 python quick_eval.py` vs `tools/simple_opponent.py` => 500 wins; a temporary always-up opponent test produced 500 wins, and the persisted `tools/up_opponent.py` smoke test produced 100/100 wins.
- Added `tools/up_opponent.py` as a persisted local recreation of the observed always-up opponent for future teammate testing.

Round 2 notes (gpt-5-5 current run, logs `/logs/rounds/1`):
- Rechecked `/logs/rounds/1/results.json`: still a match sweep for us, 28-0. Only 28 of 250 sim jsonl files are non-empty, all wins.
- Important new observation: unlike round 0's always-up logs, two non-empty round-1 games lasted very long (`sim_242` to turn 399, `sim_245` to turn 227). In these, Nettogrof behaved like a vertical lawnmower/serpentine bot: continue up/down a column, shift left at top/bottom, reverse; it eats food incidentally and can survive a long time.
- `main.py` now adds a conservative `_nettogrof_serpentine_move` predictor used only for opponents whose name contains `Nettogrof`. It feeds into the existing predicted-head-square scoring. Equal/longer predicted collisions are still avoided; attacks are only meaningfully rewarded when we are at least 3 longer and have enough space. This preserved perfect local results vs the old simple/up opponents.
- Added `tools/lawnmower_opponent.py` as an approximate local recreation of the long-game behavior. Smoke tests this edit: `N=200 python quick_eval.py` => 200 wins vs `tools/simple_opponent.py`; `N=100 python /tmp/eval_up.py` => 100 wins vs `tools/up_opponent.py`. A quick temporary `N=50` test vs `tools/lawnmower_opponent.py` got 48 wins / 2 losses; this opponent recreation is harsher/not exact, so future teammates may want to improve general endgame/space partitioning if logs show losses.

Round 1 notes (gpt-5-5 current run vs `csauve__bookworm`):
- `/logs/rounds/0` is a 20-0 sweep for us. Opponent deaths are at walls after moving straight; observed first/continuation moves are mostly default `up`, with some straight `left`/`down` depending on opening/neck, all ending by turn 10.
- Current code was retested: `N=500 python quick_eval.py` vs `tools/simple_opponent.py` => 500 wins; `N=100 python /tmp/eval_tool.py tools/up_opponent.py` => 100 wins; `python analyze_logs.py /logs/rounds/0` confirms 20 wins.
- Small `main.py` change this round: add `_continuation_or_default_move` prediction for all opponents (straight-line next square, stacked starts default up) in addition to farthest-food and Nettogrof predictors. This better covers the observed `csauve__bookworm` straight movement without altering survival-first scoring; simple/up tests remain perfect.
- I also saved `tools/bookworm_opponent.py` from `origin/human/csauve/bookworm` for future reference, but it is too slow/hangs in local arena because its 0.30s/move search is expensive under the local batch runner. Do not use it for quick large evals unless you reduce its TIME_BUDGET.

Round 2 notes (gpt-5-5 current run vs `csauve__bookworm`, logs `/logs/rounds/1`):
- `/logs/rounds/1/results.json` is still a 20-0 sweep for us, same as round 0.
- `python analyze_logs.py /logs/rounds/1` reports 20/20 wins, avg final turn 6.4, max turn 10. Opponent transitions in rounds 0/1 are dominated by `(0,+1)` with a few straight left/down continuations, so it is still dying quickly by wall collision.
- Re-ran `N=500 python quick_eval.py` vs `tools/simple_opponent.py`: 500 wins / 0 losses / 0 ties, avg turn about 5.9.
- Left `main.py` unchanged to avoid regressing an already perfect matchup. The survival-first strategy plus straight/default opponent prediction is sufficient for current `csauve__bookworm` logs.
- Minor tooling note: `tools/bookworm_opponent.py` now honors `BOOKWORM_TIME_BUDGET` for attempted local speed testing, but it can still hang/consume CPU in local batch play; avoid using it for large evals unless you manage processes carefully.

Round 1 notes (gpt-5-5 current run vs `coreyja__improbable-irene`):
- `/logs/rounds/0/results.json` is a 20-0 sweep for us. `python analyze_logs.py /logs/rounds/0` shows all 20 logged games are wins, avg final turn 5.15, max 10.
- Observed opponent transitions in these logs are overwhelmingly `(0,+1)` (76 of 83), with only a few first/early horizontal moves. It usually drives into the top wall; current straight/default-up prediction and survival-first policy already cover it.
- Re-ran `N=200 python quick_eval.py` vs `tools/simple_opponent.py`: 200 wins / 0 losses / 0 ties. I left `main.py` unchanged to avoid regressing a perfect logged matchup.
- Added `tools/improbable_irene_opponent.py`, copied from `origin/human/coreyja/improbable-irene`, with env knobs `IRENE_TIME_LIMIT` and `IRENE_MAX_ITERATIONS` defaulting low for local testing. Caution: even with low limits it can be CPU-heavy/slow in batch play and does not reproduce the logged early wall deaths under all settings; kill stray processes if experimenting.

Round 2 notes (gpt-5-5 current run vs `coreyja__improbable-irene`, logs `/logs/rounds/1`):
- `/logs/rounds/1/results.json` is another 20-0 sweep for us; `python analyze_logs.py /logs/rounds/1` reports 20/20 wins, avg final turn 5.75, max 10.
- Opponent behavior is still effectively a wall-crasher/straight mover in production logs: transition counts in round 1 are `(0,+1)` 85 times, `(0,-1)` 9 times, `(-1,0)` once; first moves are 17 up, 2 down, 1 left. Our existing survival-first bot plus straight/default-up prediction already handles this.
- Re-ran `N=100 python quick_eval.py` vs `tools/simple_opponent.py`: 100 wins / 0 losses / 0 ties, avg turn 5.94. I left `main.py` unchanged to avoid regressing a perfect logged matchup.
- Tooling change only: `analyze_logs.py` now prints opponent head-delta transition counters and first-transition counters, which makes it easier to spot whether future opponents are still defaulting/continuing straight or have changed strategy.
- Caution: local batch attempts against `tools/improbable_irene_opponent.py` can hang/timeout and leave defunct processes even with low `IRENE_TIME_LIMIT`; the production logs are more reliable for this matchup.

Round 1 notes (gpt-5-5 current run vs `graeme-hill__snakebot`):
- `/logs/rounds/0/results.json` is a 65-0 sweep for us; `python analyze_logs.py /logs/rounds/0` reports 65/65 wins, avg final turn ~6.7, max 21.
- Observed opponent pathing often moves straight until a wall/edge then turns (transition counts: up 209, left 84, right 63, down 15). It still dies quickly in all logged games; current survival-first `main.py` handles it cleanly.
- Re-ran `N=200 python quick_eval.py` vs `tools/simple_opponent.py`: 200 wins / 0 losses / 0 ties, avg turn ~5.9. I left `main.py` unchanged to avoid regressing a perfect logged matchup.
- Added `tools/graeme_hill_snakebot.py`, copied from `origin/human/graeme-hill/snakebot`, as a reference recreation of this opponent. Caution: it is CPU-heavy/slow under the local batch runner even after lowering the default env-controlled `GRAEME_TIME_BUDGET`; use small N and expect possible no-state/timeouts.

Round 2 notes (gpt-5-5 current run vs `graeme-hill__snakebot`, logs `/logs/rounds/1`):
- New logs are no longer perfect: `/logs/rounds/1/results.json` is 58-1 for us. The sole loss is `sim_232.jsonl`, a long 328-turn game where Graeme grew to length 31 and we stayed length 20, then got boxed in.
- `python analyze_logs.py /logs/rounds/1` reports 58 wins / 1 loss, avg final turn ~12; most games still end very early by opponent wall/body crash.
- Made a conservative `main.py` adjustment: normal food attraction is stronger (`nearest_food * 8` instead of almost zero when healthy) so we grow more in rare long games, while still staying survival-first; also added a small late/endgame penalty for stepping into tiny pockets when a much larger enemy exists.
- Retested `N=200 python quick_eval.py` vs `tools/simple_opponent.py`: 200/200 wins, avg turn ~3.7 (faster than before because food pressure changes paths).
- Future work if Graeme losses continue: build a faster local eval harness for `tools/graeme_hill_snakebot.py` or add explicit opponent-territory/minimax in long games. Direct local batch vs that tool can be slow/time out.

Round 1 notes (gpt-5-5 current run vs `coreyja__devious-devin`):
- `/logs/rounds/0/results.json` is a 35-0 sweep for us. `python analyze_logs.py /logs/rounds/0` shows all logged opponent transitions are `(0,+1)` and every opponent response latency is 500ms in samples, so production `devious-devin` appears to time out and default upward until wall death.
- Kept the survival-first strategy, but slightly increased normal food pressure in `main.py` (`nearest_food` weight when healthy 8 -> 16, low health 12 -> 20) to grow better if this opponent ever returns valid moves / enters long games. Smoke tests remained perfect vs wall-crash bots: `N=100 python quick_eval.py` and `N=100 python /tmp/eval_tool.py tools/up_opponent.py` both swept.
- Added `tools/devious_devin_opponent.py`, copied from `origin/human/coreyja/devious-devin`, with local env knobs `DEVIN_TIME_LIMIT` and `DEVIN_MAX_DEPTH` defaulting to low values. It can be used for small tactical tests but does not match production logs (production is timing out/default-up); local low-depth tests are mixed and slow-long, so don't overfit without new loss logs.

Round 2 notes (gpt-5-5 current run vs `coreyja__devious-devin`, logs `/logs/rounds/1`):
- `/logs/rounds/1/results.json` is still a sweep for us, 22-0. `python analyze_logs.py /logs/rounds/1` shows 22 wins, avg final turn ~15.1, with two longer wins (sim_248 to turn 55 and sim_249 to turn 163).
- Production Devin no longer only default-up every game: transitions include up/down/left/right in the two long games, but it still eventually dies or loses to our current survival/food play.
- `main.py` change this round: added `_distance_map` and `_territory_count` (Voronoi-style reachable-space estimate) and a modest territory score bonus. This should help rare long games by preferring cells we can reach before the opponent, not just raw flood-fill area.
- Smoke tests after the change: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` => 100/100 wins; `N=100 python /tmp/eval_tool.py tools/up_opponent.py` and simple opponent both swept. A local approximate low-depth Devin batch (`DEVIN_TIME_LIMIT=0.005 DEVIN_MAX_DEPTH=2`) improved over the pre-change quick sample but is noisy and not production-fidelity (examples: 19/20 wins once, around 45/50 wins in a later sample), so trust production logs more.
- Avoid overfitting to `tools/devious_devin_opponent.py`; it is an approximate port with different time behavior. If future logs show losses in long games, inspect those specific loss logs before changing the survival-first core.

Round 1 notes (gpt-5-5 current run vs `m-schier__kreuzotter`):
- `/logs/rounds/0/results.json` is a 40-0 sweep for us. `python analyze_logs.py /logs/rounds/0` reports 40/40 wins, avg final turn 5.6, max 10.
- Production Kreuzotter appears to be timing out/defaulting: observed opponent first moves are 37 up, 1 left, 1 right, 1 down; overall transitions are overwhelmingly `(0,+1)`. Opponent latency in states is mostly 500/501ms. It dies at top wall quickly (max length only 4).
- Current `main.py` already predicts straight/default-up behavior and remains survival-first, so I left it unchanged to avoid regressing a perfect logged matchup.
- Smoke test this round: `N=200 python quick_eval.py` vs `tools/simple_opponent.py` => 200 wins / 0 losses / 0 ties, avg turn ~5.6.
- If future logs show Kreuzotter returning valid moves and causing long games, inspect those losses before changing strategy; the origin branch `origin/human/m-schier/kreuzotter` contains a large Python port with `TIME_BUDGET = 0.30` that may be useful for reference but may also be slow under local batch eval.

Round 2 notes (gpt-5-5 current run vs `m-schier__kreuzotter`):
- `/logs/rounds/1/results.json` dropped to 31-2 for us. The losses were long games `sim_232` (turn 162) and `sim_249` (turn 215), where production Kreuzotter started returning real moves, grew, and we died after walking along an edge into a one-cell corridor/box.
- `main.py` changes this round: added conservative one-ply enemy-next-space scoring (`safe_area`) and `_articulation_risk` choke penalties. This tries to avoid moves whose raw flood-fill is large only because it ignores that an opponent can immediately cut a corridor, while keeping normal survival/food behavior.
- Also increased edge preference a bit (edge_dist weight 8 -> 32) because in the logged losses the only difference between a safer central move and a corridor edge move was small territory/food scoring.
- Tests after changes: `N=200 python quick_eval.py` and `N=100 python quick_eval.py` vs `tools/simple_opponent.py` remained perfect. Against `tools/lawnmower_opponent.py` (rough long-game proxy), a 50-game batch improved from 49-1 before final choke tuning to 50-0 after; a larger 100-game run timed out due to long games and was killed.
- Added `tools/kreuzotter_opponent.py` copied from `origin/human/m-schier/kreuzotter` with env knobs `KREUZ_TIME_BUDGET` and `KREUZ_MAX_DEPTH`, but local runs were too slow/no-state under the batch harness. Use with caution/small N only.

Round 1 notes (gpt-5-5 current run vs `nbw__nbw-crystal`):
- `/logs/rounds/0/results.json` is favorable but not perfect: 200 wins / 40 losses / 10 ties over 250 games. `python analyze_logs.py /logs/rounds/0` shows real long games (avg ~89 turns, max 347) and opponent transitions are balanced across all directions, consistent with a competent Voronoi/area bot rather than a wall-crasher.
- Added `tools/nbw_crystal_opponent.py`, copied from `origin/human/nbw/nbw-crystal`, as a local reference opponent. It is slower than simple bots; use small batches/timeouts. Example harness used this round was a temporary `/tmp/eval_nbw_detail.py`.
- `main.py` changes: made equal/longer head-to-head avoidance much stricter (`h2h_risk` penalty now effectively overriding space score) after inspecting `sim_9` where our old scoring chose a fatal head-to-head-adjacent move because flood-fill looked huge. Also increased food pressure when we are not longer than the enemy, because many nbw losses happen after falling behind in length/territory.
- Smoke tests: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` remained perfect. Small local tests vs the copied nbw bot were noisy/slow but still favorable (e.g. 9/10 wins after food tuning; copied bot may not exactly reproduce production ordering/timing).
- Future work: inspect production loss logs for starvation/boxing patterns and consider a deeper minimax/Voronoi path planner for long games. Be careful not to weaken the survival-first core that beats timeout/wall-crash opponents.

Round 2 notes (gpt-5-5 current run vs `nbw__nbw-crystal`):
- New `/logs/rounds/1/results.json` improved strongly over round 0: 245 wins / 3 losses / 2 ties over 250 games. `python analyze_logs.py /logs/rounds/1` shows avg final turn ~21.6, max 131.
- Remaining failures were long-game/endgame issues (`sim_24`, `sim_73`, `sim_138`, `sim_166`, `sim_226`): starvation/low-health orbiting in food-rich boards, or getting squeezed along board edges by a larger/equal nbw.
- `main.py` changes this round: nonlinear low-health food pressure (much stronger under health 30/15), bigger on-food bonus when hungry, slightly stronger length-catchup food pressure, and an extra interior bias/edge penalty when the enemy is at least 2 longer. The intent is to address the observed starvation/edge-box losses while keeping the survival-first core.
- Smoke tests: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` stayed perfect. Local copied `tools/nbw_crystal_opponent.py` is only an approximation and is noisy/slow: after changes, `N=50` got 50/50; `N=70 timeout 25 ...` got 69/70, with the same local seed 51 loss delayed from turn 86 to turn 200 after edge tuning. Do not overfit solely to the copied bot.

Round 1 notes (gpt-5-5 current run vs `Xe__since`):
- `/logs/rounds/0/results.json`: 242 wins / 5 losses / 3 ties over 250. Opponent is a real pathing bot (balanced moves, avg ~100 turns), not a timeout wall-crasher.
- Added `tools/xe_since_opponent.py` from `origin/human/Xe/since` as a local reference; fixed its import path. It is slow/noisy and not exact, so use small `N` only.
- Inspected losses: common issue was losing head-to-head/endgame when Xe hunts our head after becoming longer/equal (e.g. sim_57, sim_143), or falling behind in length. `main.py` now includes a Xe-specific one-step predictor matching its nearest-food / hunt-head target choice and left/right/down/up A* tie order. For Xe only, generic farthest-food/straight predictions are disabled to avoid over-penalizing all adjacent squares. Equal/longer predicted collisions now carry a much stronger penalty.
- Also increased catch-up food pressure and on-food bonus when we are not longer than the enemy; intent is to avoid the long-game length deficits that caused most failures.
- Smoke: `N=50 python quick_eval.py` vs simple remained perfect before final food-pressure tweak; a tiny `N=10` local Xe batch after predictor was 9-1 (seed 0 still problematic, but the local port may differ). Final food tweak compiled but the eval timed out, so future teammate should rerun small Xe/production-log checks.

Round 2 notes (gpt-5-5 current run vs `Xe__since`, logs `/logs/rounds/1`):
- `/logs/rounds/1/results.json` regressed from round 0 but is still favorable: 235 wins / 13 losses / 2 ties. `python analyze_logs.py /logs/rounds/1` shows long games (avg ~93 turns, max 271) against a real balanced pathing bot.
- Inspected losses/ties (`sim_37`, `69`, `127`, `138`, `144`, `175`, `185`, `191`, `207`, `214`, `218`, `236`, `238`, `243`, `249`). Many failures were not simple starvation; we often chased/ate food right beside a longer/equal Xe and then got sealed by its body wall or head pressure (e.g. `sim_249` around turns 132-133, `sim_207` around turn 70). Some endgames still die at edges when length-disadvantaged.
- `main.py` change this round: added `_nearest_uncontested_food_distance` and `_food_contested_from`. When we are not longer and health is not critical, catch-up food pressure now targets food we can reach before Xe rather than food Xe can claim first; stepping onto food adjacent to an equal/longer enemy head is penalized. This is intended to reduce “greedy contested food” traps while preserving low-health emergency eating.
- Smoke tests after the change: `N=250 python quick_eval.py` vs `tools/simple_opponent.py` remained perfect (250/250 wins, avg turn ~4.8). Local `tools/xe_since_opponent.py` remains too slow/hang-prone in this environment, so evaluate primarily from production logs or very small carefully-timeboxed tests.
- Future work: if Xe losses continue, build an offline scorer/replayer for the production loss states so candidate moves can be compared without running the slow local server opponent. Focus on endgame territory/edge escapes and contested-food decisions.


Round 1 notes (gpt-5-5 current run vs `ccSnake2018__ccsnake`):
- `/logs/rounds/0/results.json` was favorable but not perfect: 245 wins / 5 losses over 250. Opponent is the old ccSnake2018 port: nearest-food plus recursive 5-ply security/danger grid, not a timeout wall-crasher.
- Added `tools/ccsnake_opponent.py` copied from `origin/human/ccSnake2018/ccsnake` for local reference testing. It is moderately slow but usable for small batches (e.g. `timeout 30 bash -lc 'N=50 python /tmp/eval_cc.py'`).
- Inspected production losses, especially `sim_141`: our generic equal/longer adjacent-head rule overblocked all squares next to ccSnake. Since ccSnake itself avoids our possible next head cells, this made us choose a one-cell top-edge trap instead of a large safe adjacent move.
- `main.py` change: for opponent names containing `ccsnake`/`ccsnake2018`, skip the generic adjacent-head `h2h_risk` penalty while keeping predicted-move penalties and all normal body/space checks. This changes the logged `sim_141` turn-42 decision from fatal `up` to roomier `down`; simple-opponent smoke (`N=100 python quick_eval.py`) stayed 100/100.
- Local copied-ccSnake batches are noisy/not exact: after this change, `N=20` got 20/20; a `N=50` quick run got 48/50. Production logs should remain the primary guide. Future work: inspect any new ccSnake losses and consider an explicit predictor based on its nearest-food/security choice if needed.


Round 2 notes (gpt-5-5 current run vs `ccSnake2018__ccsnake`):
- `/logs/rounds/1/results.json` regressed to 238 wins / 11 losses / 1 tie. The failures were mostly exact tactical head-to-head collisions where last-state replay with `tools/ccsnake_opponent.py` predicted ccSnake's chosen next square.
- `main.py` change: added `_ccsnake2018_predicted_move`, which imports/runs the local `tools/ccsnake_opponent.py` port with `you` swapped for ccSnake and uses that single predicted square in the existing predicted-head penalty. We still skip the broad generic adjacent-head blocking for ccSnake, because that broad rule caused earlier self-trap losses; now only ccSnake's deterministic chosen move is strongly avoided when equal/longer.
- Sanity checks after change: the 12 round-1 bad final decision states now choose non-colliding alternatives; `N=100 python quick_eval.py` vs simple still swept; `N=50 python /tmp/eval_cc.py` vs copied `tools/ccsnake_opponent.py` got 50/50 wins (local port is approximate but useful for this tactic).
- Future focus if losses remain: inspect whether production ccSnake diverges from the copied port in earlier strategic choices, or add a small offline replay evaluator to compare candidate moves at production loss states.

Round 1 notes (gpt-5-5 current run vs `coreyja__bombastic-bob`):
- `/logs/rounds/0/results.json` is 249 wins / 1 loss over 250. Opponent is `coreyja__bombastic-bob`, whose origin code is a random "reasonable move" bot: chooses uniformly among in-bounds non-body moves (it does not do food/space/head-to-head planning).
- `python analyze_logs.py /logs/rounds/0` shows balanced random-looking transitions and avg final turn ~29.8. The sole loss is `sim_122` at turn 76: Bob was length 8 vs our length 7 and randomly took the same next square after we had moved too close to its head in a cramped local position.
- Added `tools/bombastic_bob_opponent.py` as a local recreation copied from `origin/human/coreyja/bombastic-bob`. A large local batch timed out before completion due to the 30s tool limit, so no player-code change was made; current code is already 99.6% in production logs and still sweeps the simple smoke test (`N=50 python quick_eval.py`).
- Potential future improvement if Bob losses recur: add a Bob-specific random-legal-move predictor / risk model for longer Bob, and avoid drifting within one move of a longer random head unless all alternatives are worse. Inspect `sim_122` turns 74-75 as the template failure.

Round 2 notes (gpt-5-5 current run vs `coreyja__bombastic-bob`, logs `/logs/rounds/1`):
- `/logs/rounds/1/results.json` is now a perfect 250-0 sweep for us. `python analyze_logs.py /logs/rounds/1` shows Bob's moves are balanced/random-looking, avg final turn ~27, max 121.
- I revisited the only earlier production loss (`/logs/rounds/0/sim_122`). At turn 74 our bot moved into a cell where, after one legal random Bob move, all exits were adjacent to a longer Bob head; we then lost the head-to-head on turn 76.
- Small `main.py` tweak this round: for opponents named `bombastic-bob` that are equal/longer, track all legal random next-head squares and penalize candidate moves with 0 or 1 clean next-turn exits not adjacent to those possible Bob heads. This is intentionally Bob-specific to avoid weakening aggressive/normal play against deterministic opponents.
- Sanity checks after the change: the logged loss decision at round0 `sim_122` turn 74 changes from `up` to safer `down`; `N=100 python tools/eval_bombastic_bob.py` vs `tools/bombastic_bob_opponent.py` got 100/100 wins; `N=100 python quick_eval.py` vs simple also stayed 100/100. A larger Bob batch hit the 30s command timeout due to long games, but left only defunct battlesnake processes.

Round 1 notes (gpt-5-5 current run vs `coreyja__coreyja-rs`):
- `/logs/rounds/0/results.json` is a 40-0 sweep for us. `python analyze_logs.py /logs/rounds/0` reports 40/40 wins, avg final turn ~5.1, max 10.
- Despite the origin code being a Hovering-Hobbs style minimax/flood-fill bot, production logs show it mostly times out/defaults upward: opponent transitions are 155 up, only 4 right and 4 down; most response latencies are 500/501ms. It dies quickly at the top wall or center.
- Current `main.py` already handles this with survival-first play plus straight/default-up prediction, so I left player code unchanged to avoid regressing a perfect logged matchup. Smoke test: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` stayed 100/100.
- Added `tools/coreyja_rs_opponent.py` copied from `origin/human/coreyja/coreyja-rs` with env knob `COREYJA_RS_TIME_BUDGET` defaulting to 0.03s and an import-path fix. It is CPU-heavy/hang-prone in local batch eval even with low budget (a 30-game attempt timed out around seed 20 and had to be killed), so use only tiny/timeboxed tests and trust production logs first.

Round 2 notes (gpt-5-5 current run vs `coreyja__coreyja-rs`, logs `/logs/rounds/1`):
- `/logs/rounds/1/results.json` is another sweep for us, 33-0. `python analyze_logs.py /logs/rounds/1` reports 33/33 wins, avg final turn ~5.9, max 10.
- Production `coreyja-rs` is still effectively timing out/defaulting upward: round-1 opponent transitions are mostly `(0,+1)` (132 times), first moves 28 up out of 33. It dies quickly at top wall/center/body; no long games or losses observed.
- Re-ran `N=200 python quick_eval.py` vs `tools/simple_opponent.py`: 200/200 wins, avg turn ~5.0. Also sanity-imported `main.py`.
- I left player code unchanged to avoid regressing an already perfect matchup. Current survival-first policy plus straight/default-up prediction is sufficient for this opponent. If future logs show `coreyja-rs` returning real moves/long games, inspect those specific logs before changing; local `tools/coreyja_rs_opponent.py` is CPU-heavy/hang-prone and may not match production timeout behavior.

Round 1 notes (gpt-5-5 current run vs `coreyja__jump-flooding`):
- `/logs/rounds/0/results.json` is favorable but not perfect: 238 wins / 3 losses / 9 ties over 250. Opponent is a real greedy Manhattan-Voronoi territory bot (balanced directions, avg ~44 turns), not a timeout wall-crasher.
- Added `tools/jump_flooding_opponent.py` from `origin/human/coreyja/jump-flooding` with an import-path fix for local reference testing. Local batch vs this copied bot is usable: `N=100 python /tmp/eval_jump.py` style harness got roughly low-90s wins, a few losses/ties; it is approximate but captures the opponent style.
- `main.py` change: added `_jump_flooding_predicted_move`, a one-ply predictor for the opponent's legal-move filter + whole-board Manhattan Voronoi scoring. It feeds the existing predicted-head collision penalty, so exact equal/longer predicted head-to-head squares are avoided more strongly. I also made predicted head collision penalties much larger globally to stop flood-fill terms from overwhelming them.
- Smoke tests: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` still swept; local `N=100` vs copied jump-flooding after the predictor was about 92 wins / 4 losses / 4 ties (noisy, not production-exact). Broad edge-avoidance tuning looked worse locally and was reverted.
- Remaining production failures (sim_57, sim_155, sim_235) are mostly edge/corner endgames when we are shorter/equal and get forced or boxed. Future work: inspect earlier decisions in those logs, not just the last turn, and consider a small offline candidate scorer/replayer for production states.

Round 2 notes (gpt-5-5 current run vs `coreyja__jump-flooding`, logs `/logs/rounds/1`):
- `/logs/rounds/1/results.json` is 234 wins / 9 losses / 7 ties (slightly worse than round 0's 238/3/9). Remaining losses are mostly edge/corner chases where jump-flooding is equal/longer and our bot keeps moving along the wall until no legal exit (e.g. sim_10, 11, 72, 122, 170).
- Changed `main.py` to treat jump-flooding like ccSnake for broad adjacent-head risk: skip the generic adjacent-cell h2h blanket and rely on the exact `_jump_flooding_predicted_move` square. This avoids overblocking all inward escape cells near its head.
- Added a jump-flooding-specific edge/corner heuristic: when jump-flooding is at least as long and within Manhattan 3, edge moves that head back toward mid-board get a large bonus over moves deeper into a corner. This changes one logged bad state (`sim_10` turn 48) from continuing up the right wall to moving down away from the corner; simple-opponent smoke stayed perfect.
- Smoke tests: `N=100 python quick_eval.py` vs simple => 100/100 wins. Local approximate `tools/jump_flooding_opponent.py` batch after changes: `N=100 python /tmp/eval_jump.py` => 93 wins / 4 losses / 3 ties, similar to previous local results (the copied bot is only an approximation and noisy).
- Future work: build an offline replayer/scorer for production jump-flooding loss states to evaluate earlier wall-escape choices; current one-step local server tests don't exactly reproduce production long-game decisions.

Round 1 notes (gpt-5-5 current run vs `zacpez__scape-goat`):
- `/logs/rounds/0/results.json` is a perfect 250-0 sweep for us. `python analyze_logs.py /logs/rounds/0` reports avg final turn ~28.6, max 167; opponent transitions are balanced/random-looking, not a timeout wall-crasher.
- Opponent origin branch is `origin/human/zacpez/scape-goat`. I added `tools/scape_goat_opponent.py` as a local recreation/reference (with import path fixed). The opponent is mostly a quirky Go port that excludes edge/neck moves, then accidentally reintroduces them, and uses time-nanosecond random choice plus a legal-move fallback.
- I experimented with Scape-Goat-specific random/edge-pocket penalties in `main.py`. Small samples were noisy (one 150-game local run improved to 150/150, another 100-game run still had a random loss), so I reverted player-code changes to avoid overfitting/regressing the production-perfect bot. Current `main.py` remains unchanged from the prior successful strategy.
- Smoke after revert: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` => 100/100 wins. Local Scape-Goat recreation before revert was roughly 149/150; production logs are better evidence and currently perfect.
- Future work only if new logs show losses: inspect the specific random Scape-Goat long-game loss states and consider a cautious Bob-like random-legal-head risk model when Scape-Goat is equal/longer. Do not broadly increase edge penalties without production losses; existing long-game heuristics are tuned for many previous opponents.

Round 2 notes (gpt-5-5 current run vs `zacpez__scape-goat`, logs `/logs/rounds/1`):
- New production result was 248 wins / 1 loss / 1 tie, down from the round-0 sweep. `python analyze_logs.py /logs/rounds/1` shows Scape-Goat is still random/balanced, avg final turn ~29.4, max 180.
- The bad games are `sim_185` (loss, turn 72) and `sim_197` (tie, turn 61). In both, Scape-Goat was equal/longer and our bot entered/continued in a small local pocket where all exits were adjacent to possible random Scape-Goat head moves.
- `main.py` tweak this round: extended the existing Bombastic-Bob random-legal-head escape heuristic to `scape-goat` when the opponent is equal/longer. This penalizes candidate moves that leave 0 or 1 clean next-turn exits not adjacent to Scape-Goat's possible random next heads. It changes some earlier decisions in the logged bad games while preserving the survival-first core.
- Smoke tests: `N=100 python /tmp/eval_scape.py` vs `tools/scape_goat_opponent.py` got 100/100 wins after the change; `N=100 python quick_eval.py` vs simple remained 100/100. A larger timeboxed local Scape-Goat run got 149 wins / 1 tie before timeout, so the local port remains noisy/random and not definitive.
- If Scape-Goat losses continue, inspect the new specific logs; likely next target is a more probabilistic multi-turn escape model for random legal moves when we are shorter/equal, not broad edge penalties.

Round 1 notes (gpt-5-5 current run vs `tim-hub__awesome-snake`):
- `/logs/rounds/0/results.json` is very favorable but not perfect: 247 wins / 2 losses / 1 tie over 250. Opponent is `tim-hub__awesome-snake`, a simple random tiebreak bot that scores immediate neighboring cells: food +1, empty 0, body -1, wall -100. It therefore moves randomly among safe empty cells unless adjacent to food.
- Added `tools/awesome_snake_opponent.py` copied from `origin/human/tim-hub/awesome-snake` with an import-path fix for local testing. Small local batch after the change: `N=30 python /tmp/eval_awesome.py` got 30/30 wins; larger batches can hit the 30s command limit because random games can be long.
- Production failures (`sim_35`, `sim_138`, `sim_246`) were all near an equal/longer random-ish opponent head at board edges/pockets. Existing random-head escape heuristic only applied to Bombastic Bob/Scape-Goat; `main.py` now also applies it to names containing `awesome-snake`/`tim-hub`. This penalizes moves that leave 0 or 1 next-turn exits not adjacent to possible equal/longer random enemy head moves.
- Smoke test after change: `N=100 python quick_eval.py` vs simple still swept 100/100.

Round 2 notes (gpt-5-5 current run vs `tim-hub__awesome-snake`, logs `/logs/rounds/1`):
- New production result was 248 wins / 2 losses over 250. Awesome-Snake is still random-tie among immediate safe cells, with food scored above empty/body/wall.
- The two production losses (`sim_49`, `sim_199`) were equal-length edge/pocket traps where Awesome ate or approached food and our bot continued along the bottom/right edge until there were no legal exits.
- `main.py` changes this round: added an Awesome-Snake-specific immediate move score model for direct head-collision risk (only its max-scored adjacent cells are treated as likely), extended the random-ish escape heuristic to consider opponents that are one length shorter but can eat this turn, and added stronger interior/choke penalties near random-ish equal/near-equal enemies. Also made very-low-health food pressure much stronger to reduce starvation in long random games.
- Sanity tests after changes: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` stayed 100/100. Local `tools/awesome_snake_opponent.py` is noisy because of Python randomness; a 60-game timeboxed batch after final tuning got 60/60 wins, while an earlier pre-final batch was 59/60.
- Future work if Awesome losses continue: inspect new loss logs for whether they are starvation or pocket/head-risk. Be careful with broad edge penalties, but the current changes are random-opponent-specific and should not affect most deterministic opponents much.

Round 1 notes (gpt-5-5 current run vs `rdbrck__btas`):
- `/logs/rounds/0/results.json` is 248 wins / 2 losses over 250. `python analyze_logs.py /logs/rounds/0` shows BTAS is a real pathing bot (balanced transitions, avg final turn ~51, max 219), not a timeout wall-crasher.
- Added `tools/btas_opponent.py`, copied from `origin/human/rdbrck/btas`, with an import path fix so it can run locally from `tools/`.
- The two production losses (`sim_33`, `sim_227`) involved BTAS becoming longer/equal and creating tactical head pressure near edges/food. I added `_btas_predicted_move` in `main.py`, which runs the local BTAS port with `you` swapped to the enemy and feeds its one-step predicted next head into the existing strong predicted-collision penalty.
- Local sanity: `N=100 python /tmp/eval_btas.py` vs the copied BTAS port got 100/100 wins after the predictor; `N=50 python quick_eval.py` vs simple also stayed 50/50. Larger combined evals can hit the 30s tool timeout because BTAS games are longer.
- If future BTAS losses remain, inspect earlier edge/food choices in the new logs. The copied port seems useful and deterministic for one-ply tactical prediction, but production logs should remain the primary evidence.

Round 2 notes (gpt-5-5 current run vs `rdbrck__btas`, logs `/logs/rounds/1`):
- New production result improved to 249 wins / 0 losses / 1 tie. The tie was `sim_136` at turn 69: both snakes were equal length and died in a cramped lower-left head-pressure position. Our broad generic adjacent-head ban against BTAS over-penalized the inward/adjacent escape at turn 65, pushing us down to the bottom edge, while the copied BTAS one-ply predictor correctly identified the actual enemy move.
- `main.py` change this round: for BTAS only, generic adjacent-head risk is now a small soft penalty instead of the global fatal `h2h_risk` ban. We still use `_btas_predicted_move` for exact predicted head-to-head avoidance. This changes the logged tie path away from the immediate bottom-edge trap without opening reckless exact collisions.
- Smoke tests after the change: `N=100 python quick_eval.py` vs `tools/simple_opponent.py` stayed 100/100; `N=50 python /tmp/eval_btas.py` vs copied `tools/btas_opponent.py` got 50/50 wins. A previous 50-game local BTAS run with a too-broad BTAS skip produced a tie on seed 0, so keep the soft penalty rather than fully disabling adjacent risk.
- If future BTAS failures remain, inspect whether `_btas_predicted_move` diverges from production on the final few turns. The local copied port is useful but not perfect; broad edge/adjacent heuristics can trade one tie/loss for another.

Round 1 notes (gpt-5-5 current run vs `Spenca__vulture-snake`):
- `/logs/rounds/0/results.json` is 248 wins / 1 loss / 1 tie over 250. Opponent is Spenca's 2017 Vulture Snake, a closest-food seeker that can enter a defensive square/circling mode around food; transitions are balanced and games average ~41 turns.
- Added `tools/vulture_snake_opponent.py` copied from `origin/human/Spenca/vulture-snake` with an import-path fix, for local reference testing.
- Local reference smoke: `N=100 python /tmp/eval_vulture.py` got 100/100 wins once; a later quick `N=50` got 49 wins / 1 tie (seed 36), so the copied opponent is useful but has randomness in its desperation fallback. `N=50 quick_eval.py` failed after process cleanup issues/no-state, not because of a bot exception.
- I did not change `main.py`: current survival/space strategy is already 99%+ against production Vulture. The remaining bad production games (`sim_58` loss at turn 195, `sim_225` tie at turn 52) are long endgames involving Vulture's circling/desperation behavior and equal/longer head pressure. Future work: add a Vulture-specific one-ply predictor or random-desperation risk model, but test carefully because importing/running the Vulture port mutates its module-global state.

Round 2 notes (gpt-5-5 current run vs `Spenca__vulture-snake`, logs `/logs/rounds/1`):
- New production result stayed strong but not perfect: 248 wins / 2 losses over 250. Bad games were `sim_56` (turn 29, we lost a head-to-head after Vulture's circling move) and `sim_163` (turn 132, edge/endgame pressure). Round 0 bad games remain `sim_58` and `sim_225`.
- `main.py` now adds `_vulture_predicted_move`, which runs the local `tools/vulture_snake_opponent.py` port with `you` swapped to Vulture and feeds that predicted next square into the existing exact head-to-head avoidance. `start()` resets the port's module-global circling state between games.
- Also extended the random-ish head/escape heuristic to Vulture/Spenca, but with reduced edge/choke strength and only for equal/longer Vulture (unlike Awesome's one-short-can-eat case), because Vulture has random desperation fallbacks but is not purely random.
- Smoke tests after changes: `N=100 python quick_eval.py` vs simple stayed 100/100. Local Vulture batches are slow/noisy: added `tools/eval_vulture.py`; `python tools/eval_vulture.py` (N=50 default) got 50/50 wins after final tuning; an `N=100` run exceeded the 30s command limit and was killed. Local Vulture has global state/random desperation, so production logs should remain primary evidence.
- If losses persist, inspect whether the stateful `_vulture_predicted_move` diverges from production after long circling sequences. Be careful: importing/running the Vulture port during scoring mutates its globals, so only call it once per turn/opponent or reset at game start.

Round 1 notes (gpt-5-5 current run vs `moxuz__pinky-snek`):
- `/logs/rounds/0/results.json` is 248 wins / 1 loss / 1 tie over 250. Pinky-Snek is the moxuz/chrispouliot Battlesnake-AI-2017 port: marks bodies/walls/dead-end-ish cells dangerous, then chooses a random safe adjacent cell (adjacent food only when health < 30). Moves are balanced/random-looking; avg final turn ~31.5, max 198.
- Added `tools/pinky_snek_opponent.py` from `origin/human/moxuz/pinky-snek` with import path fixed, plus `tools/eval_pinky_snek.py` for local batches. Local full batches are slow because random games can run long; use `timeout 20 bash -lc 'N=20 python tools/eval_pinky_snek.py'` style checks.
- `main.py` changes: treat names containing `pinky-snek`/`moxuz` as randomish for the existing random-legal-head escape/edge-pocket heuristic, and skip broad adjacent-head h2h blocking like other random-ish bots. Also modestly increased direct on-food bonus (healthy and catch-up) to reduce falling behind in length against long random-safe games.
- Smoke tests after changes: `N=100 python quick_eval.py` vs simple remained 100/100; `timeout 20 bash -lc 'N=20 python tools/eval_pinky_snek.py'` got 20/20 wins. A larger 100-game Pinky batch hit the 30s command limit, so production logs remain the main signal.

Round 2 follow-up notes (gpt-5-5 current run vs `moxuz__pinky-snek`, logs `/logs/rounds/1`):
- New result regressed to 243 wins / 7 losses. Losses were long games (`sim_59`, `62`, `103`, `153`, `208`, `226`, `232`). Several were starvation despite nearby food, especially `sim_62` and `sim_153`, where low-health Manhattan food scoring plus large space terms led away from reachable food until health hit 0. Others were endgame/body-pocket traps against a much longer Pinky.
- `main.py` now adds `_shortest_food_distance` (BFS path distance to food) and uses it when health < 30, with much stronger emergency pressure under health 15/8. This changes the final starvation choices in the logged bad states toward reachable food (e.g. sim_62 turn 108 now goes up toward food instead of right).
- Smoke tests after this change: `N=100 python quick_eval.py` vs simple stayed 100/100. `timeout 25 bash -lc 'N=50 python tools/eval_pinky_snek.py'` got 49 wins / 1 tie; the copied Pinky port is random/noisy but still a useful small-batch reference.
- If losses persist, focus on the remaining non-starvation pocket/endgame failures (e.g. sim_226/sim_208 style: own body corridor with only a fatal continuation) and consider a deeper self-tail/escape planner rather than just stronger food pressure.

Round 1 notes (gpt-5-5 current run vs `coreyja__amphibious-arthur`):
- `/logs/rounds/0/results.json` is a perfect 250-0 sweep for us. `python analyze_logs.py /logs/rounds/0` shows Amphibious Arthur is a real low-latency space/health recursion bot, with balanced directions, avg final turn ~76, max 355.
- Added `tools/amphibious_arthur_opponent.py`, copied from `origin/human/coreyja/amphibious-arthur`, as a local reference opponent. Local smoke `N=50 python /tmp/eval_amph.py` got 50/50 wins; a later `N=30` got 30/30. Persisted evaluator: `tools/eval_amphibious_arthur.py` (`N=20` got 20/20). Batches are slower because games can be long.
- Small `main.py` change: added `_amphibious_arthur_predicted_move`, which runs the copied local port with `you` swapped to Arthur and feeds its one-ply chosen next square into the existing predicted-head collision scoring. This is conservative/redundant with generic adjacent-head avoidance when Arthur is equal/longer, but should help exact tactical head collisions if future seeds become harder.
- Smoke tests after the change: `N=100 python quick_eval.py` vs simple stayed 100/100; local Amphibious Arthur sample stayed perfect. Since production was already a sweep, avoid broad retuning unless new logs show losses; focus on specific long-game loss states if they appear.
