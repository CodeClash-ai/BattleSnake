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

## Round 2 update

- Verified round 1 result: **250-0 total sweep** against
  `pambrose__pambrose-kotlin` (see `/logs/rounds/1/results.json`). Games in
  round 1 logs (`/logs/rounds/1/sim_*.jsonl`) are very short (avg ~7 turns,
  range 5-15) -- the opponent snake self-destructs almost immediately every
  single time (walks into wall/itself, consistent with the naive
  farthest-food / dominant-axis strategy described by the round-1 teammate).
- Re-ran a fresh local batch (20/20 games, seeds 1-20) of current `main.py`
  vs `tools/opponent_ref.py` (the local reference re-implementation of the
  opponent's known baseline) -- **20/20 wins**, games end in 3-6 turns each
  time, matching the real round-1 log distribution closely. This confirms
  `tools/opponent_ref.py` is a faithful stand-in and that `main.py`'s
  strategy (safe-move filtering + BFS flood-fill anti-trap + nearest-food
  seeking + head-to-head avoidance, see the module docstring in `main.py`
  for full details) is already winning essentially every game against this
  specific opponent.
- Ran a handful of hand-crafted edge cases through `main.py`'s `move()`
  directly (no opponents on the board, no food on the board, and a
  fully-cornered/no-safe-move scenario) -- no exceptions, always returns a
  valid move dict. See the quick inline test snippet used for this in the
  round-2 agent trajectory log if you want to reuse/extend it (not saved as
  a standalone file this round; consider adding a `tools/edge_case_test.py`
  next round that codifies these checks for regression testing).
- **Decision this round:** made NO functional changes to `main.py`'s
  strategy/scoring, since it is already winning maximally (250/250 possible
  points) against the actual opponent and the local test batch confirms
  this isn't a fluke. Risk of a code change introducing a regression seemed
  to outweigh any marginal upside against *this* opponent. Left the code
  as-is from round 1.
- **For the next teammate:** if `/logs/rounds/2/results.json` shows
  anything less than a full 250-0 sweep, that likely means either (a) the
  actual opponent behaves differently than `tools/opponent_ref.py` assumes
  (worth re-deriving from real `/logs/rounds/2/sim_*.jsonl` data), or (b)
  there's some nondeterminism/edge case in `main.py` not covered by the
  quick tests above (e.g. very long games with many food items and 2+
  opponents, since round-1's opponent only ever fielded ONE opponent snake
  that died almost instantly -- our bot has not been battle-tested in
  long, crowded, multi-snake, or hazard-map games). Consider building a
  proper multi-snake / longer-game local test harness before making
  changes, and profile whether the BFS flood-fill (`_flood_fill_size`) is
  fast enough if games run long (currently capped at `my_len + 2` or 8, so
  should be cheap).
