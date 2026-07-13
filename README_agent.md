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
