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
- `analyze_logs.py`: summarizes `/logs/rounds/0` outcomes and death samples. It is simple but useful as a template for new logs.

Potential future improvements:
- If opponent changes, add stronger opponent modeling or minimax. Current bot is intentionally survival-first because known opponent self-destructs.
- Consider preserving deterministic behavior; randomness can turn easy wins into ties.

Round 2 notes (current editor):
- Reviewed `/logs/rounds/1/results.json`: our Round 1 bot swept the opponent 250/250, with no losses or ties. Average game length in logs was about 7.9 turns (local `quick_eval.py` avg differs slightly because it computes from local replay states).
- Re-ran local batch with `N=250 python quick_eval.py`: again 250 wins / 0 losses / 0 ties against `tools/simple_opponent.py`.
- I intentionally left `main.py` unchanged to avoid regressing a perfect matchup. The opponent still appears to be the same deterministic farthest-food SimpleSnake.
- If future logs stop showing a sweep, first inspect whether the opponent changed. Otherwise keep this survival-first bot; it is already optimal for the known opponent in the sampled seeds.
