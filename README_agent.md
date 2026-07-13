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
