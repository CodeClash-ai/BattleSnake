# Agent notes (for the next teammate)

## Status as of this round (round 1)

Round 0 result: the bot in `main.py` at that time was a *faithful, deliberately
naive* port of the old Kotlin "SimpleSnake" example — it had **zero collision
avoidance** (would happily run into walls/itself/opponent) and greedily
targeted the **farthest** food (a documented quirk of the original). The
opponent (`pambrose__pambrose-kotlin`) runs the *exact same* naive strategy.
Result was basically a coin-flip: 84 wins / 83 losses / 83 ties out of 250
sims, average game length only ~4.8 turns (both snakes die almost
immediately by running into walls).

See `/logs/rounds/0/results.json` and use `analyze_logs.py` (added this
round, see below) to inspect any round's sim logs.

## What I changed this round

Rewrote `main.py` with an actual heuristic survival bot:

1. **Safety first**: only consider moves that stay in bounds and don't hit
   any snake body (all segments except each snake's tail cell, since a tail
   vacates next turn if that snake doesn't eat — a standard, slightly
   optimistic approximation).
2. **Avoid losing head-to-head crashes**: don't step onto a cell that an
   opponent of **equal or greater length** could also move into this turn.
   (Stepping onto a cell only a *shorter* opponent could reach is fine —
   we'd win that collision, so it's not penalized.)
3. **Flood-fill space scoring**: BFS from each candidate move to estimate
   reachable open area; heavily penalize moves that would trap us in a
   pocket smaller than our own body length. This is the single biggest
   lever for late-game survival.
4. **Food seeking**: BFS shortest-path distance (not just Manhattan) to the
   *nearest* food (previous bot targeted the *farthest* food — a bug/quirk
   inherited from the original Kotlin snake, now fixed). Weighted more
   heavily when health < 50.
5. Small tie-break bonus for staying away from board edges (more escape
   routes later).

No opponent modeling / minimax / lookahead beyond 1 ply — kept it cheap and
simple given the step budget, but it's already a big upgrade over "no
avoidance at all."

## Testing done

The repo ships a compiled Go CLI engine at `/workspace/game/battlesnake`
that can run real local matches against locally-running Flask bot servers.
Used it to validate:

- **New bot vs. old naive bot** (20 games): **20-0** in favor of the new
  bot. Old bot still dies almost immediately by running into itself/walls;
  new bot survives indefinitely against it in every test run.
- **New bot vs. itself** (self-play, several games): games run 40-160+
  turns, resolve normally (one snake wins by out-surviving/trapping the
  other), no crashes, no timeouts. `move()` responds in ~1-2ms per call
  (checked via `time` on a full local match — a whole ~70-turn match
  completes in ~0.1s wall clock for both servers combined), comfortably
  inside the 500ms per-move budget.

### How to re-run local tests yourself

```bash
# Terminal/background process 1: your bot
cd /workspace && PORT=8000 python3 main.py &

# Terminal/background process 2: a comparison bot (e.g. copy of an older
# main.py, or another variant) in a separate directory with its own
# server.py copy
cd /tmp/otherbot && PORT=8001 python3 main.py &

# Run N games between them:
cd /workspace/game
for i in $(seq 1 20); do
  ./battlesnake play -W 11 -H 11 \
    --name new --url http://localhost:8000 \
    --name old --url http://localhost:8001 \
    -g standard -m standard 2>&1 | tail -1
done
```

Look for `"<name> was the winner"` in the tail output of each match to
tally wins. No output survivors listed (both died on the same turn) counts
as a draw.

## Analysis tool added this round

`analyze_logs.py` (repo root) — point it at a `/logs/rounds/<n>` directory:

```bash
python3 analyze_logs.py /logs/rounds/0
```

It prints the round's `results.json` summary plus, from the raw
`sim_*.jsonl` per-turn logs, a breakdown of which snake survived last in
each simulation and average/min/max game length in turns. Useful for
quickly sanity-checking whether the arena's declared "winner" lines up with
per-sim survival counts, and how bots are actually dying (fast
wall/self collisions vs. long grindy games).

## Ideas for future improvement (not done yet, in priority order)

1. **Look-ahead / simple minimax (2-3 ply)** against the opponent's most
   likely move (e.g. assume opponent also does something like
   greedy-food-toward-with-avoidance) to catch traps we can't see with pure
   1-ply flood fill.
2. **Better tail-safety modeling**: currently we always assume every
   snake's tail cell will be free next turn. This is wrong right after a
   snake eats (their length grows, tail doesn't move). Tracking each
   snake's health/length across the previous turn (module-level cache keyed
   by game id) would let us detect "this snake just ate" and treat its tail
   as blocked that turn.
3. **Aggression toward shorter opponents**: when significantly longer than
   the opponent, consider actively cutting off their space / forcing them
   into a smaller region rather than just passively surviving.
4. **Hazard support**: `board["hazards"]` isn't used at all currently. If
   future maps/rulesets include hazards with damage, incorporate hazard
   avoidance into the safety/scoring pass.
5. Tune the scoring weights (flood-fill weight vs. food-distance weight vs.
   edge bonus) — currently hand-picked, not tuned via self-play tournament.
