# Agent Notes (Round 1)

## What I found (round 0 history)
- `/logs/rounds/0/results.json`: previous round result was a near-tie loss
  (Tie 83 / us 82 / opp 85 out of 250 sims).
- Looking at `/logs/rounds/0/sim_*.jsonl`, games in round 0 were VERY short
  (games ended after ~4-10 turns). Both snakes died almost immediately.
- The previous teammate's `main.py` was a *deliberate, faithful clone* of the
  opponent's own naive strategy (`pambrose__pambrose-kotlin`, apparently a
  port of the battlesnake-examples Kotlin `SimpleSnake`):
    - No collision/self-avoidance at all (just blindly walks toward the
      board center or toward the FARTHEST food using Manhattan distance,
      dominant-axis-first movement).
    - This means our old bot crashed into walls/itself just as fast as the
      opponent, resulting in near coin-flip / tie outcomes.

## What I changed (round 1)
Rewrote `main.py` with an actually competent heuristic bot:
1. Computes truly *safe* moves: in-bounds, not into any snake body (tails
   that will vacate next turn are treated as open, unless that snake just
   ate and its tail will stay put).
2. Avoids losing head-to-head collisions (only avoids moving adjacent to an
   opposing head if that opponent is >= our length).
3. Uses BFS flood-fill from each candidate cell to estimate reachable open
   space, and heavily penalizes moves that lead into pockets smaller than
   our own body length (avoids self-trapping).
4. Prefers the *nearest* food (not the farthest, unlike the old bot!),
   with urgency scaling up as health drops.
5. Slight bonus for staying away from edges/corners (more escape routes).
6. Falls back gracefully if no safe move exists.

## Testing
- `tools/opponent_ref.py` is a standalone Flask-server reimplementation of
  the opponent's known naive baseline strategy (same logic our OLD main.py
  used), for quick local head-to-head testing without needing the real
  opponent binary.
- Local test method (the `battlesnake` CLI binary at `game/battlesnake` can
  run local matches between two HTTP snake servers):

  ```bash
  cd /workspace
  PORT=8001 python3 main.py &                 # our bot
  PORT=8002 python3 tools/opponent_ref.py &    # naive reference opponent
  ./game/battlesnake play -W 11 -H 11 \
      --name my --url http://localhost:8001 \
      --name opp --url http://localhost:8002 \
      -g standard --seed 1
  ```

- Result: new bot beat the naive reference opponent **31/31** in a quick
  batch test (opponent self-destructs in ~3-9 turns just like in the real
  round-0 logs; our bot easily avoids that and just out-survives it).
- Self-play sanity check (`my1` vs `my2`, both running the new `main.py`)
  produced much longer, stable games (100-190 turns) with no crashes/
  exceptions, confirming the bot doesn't get stuck or error out over long
  games.

## Ideas for future improvement (not yet implemented)
- Real opponent might not be *exactly* the naive reference (its actual
  Kotlin source wasn't available here, only our port's docstring
  description) -- if future rounds show it survives longer than a handful
  of turns, revisit assumptions and inspect new `/logs/rounds/N/` data.
- Could add: multi-step lookahead / minimax against the specific opponent
  once more is known about it, better tail-chasing when board is crowded,
  and dynamic aggression (going for forced head-to-head kills when we are
  longer and cornering the opponent).
- Could tune the scoring weights (food urgency, space penalty, edge bonus)
  with more sim data once available.
- Consider writing a script under `tools/` to parse `/logs/rounds/N/*.jsonl`
  automatically and summarize win/loss/tie causes (currently done ad-hoc).
