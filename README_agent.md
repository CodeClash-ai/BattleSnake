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

## Round 1 (this round) update

**Context correction:** Despite the "Round 2 update" section above (written
by a previous agent run), the *actual* `/logs/rounds/` directory on disk
only contains a single completed round: `/logs/rounds/0/`. That round's
opponent is `Nettogrof__nessegrev-julia` (NOT `pambrose__pambrose-kotlin`
as described earlier in this file) -- the opponent apparently changed
between whatever the earlier notes were based on and the actual current
match series. Take the opponent-specific claims above (esp. mentions of
"pambrose-kotlin") with a grain of salt; `tools/opponent_ref.py` is still
modeling the *old* pambrose-style naive bot, not necessarily
`Nettogrof__nessegrev-julia` exactly. That said, both opponents behave
almost identically in practice: looking at `/logs/rounds/0/sim_*.jsonl`,
`Nettogrof__nessegrev-julia` also self-destructs almost immediately
(observed deaths at turn 2, turn 4, etc. in the real match logs), so
`tools/opponent_ref.py` remains a reasonable/conservative local stand-in
for quick smoke testing even if not byte-for-byte accurate.

**Round 0 result:** `sonnet-5` swept **20-0** (see
`/logs/rounds/0/results.json`, `scores: {sonnet-5: 20, Nettogrof...: 0.0}`).
Note: of the 250 `sim_*.jsonl` files in that directory, only 20 are
non-empty (i.e. only 20 games actually ran/were recorded) and our bot won
all 20 of them. The other 230 files are empty (0 bytes) -- this looks like
some harness artifact (pre-allocated file slots not used), not evidence of
draws/unplayed games affecting score.

**What I did this round:**
- Re-verified `main.py`'s strategy is intact and functioning (safe-move
  filtering + BFS flood-fill anti-trap + nearest-food seeking + head-to-head
  avoidance -- see module docstring for full details). No functional
  changes made; the bot was already winning maximally.
- Ran fresh edge-case sanity checks by calling `main.move()` directly with
  hand-built game states (no food/no opponents, cornered snake, a fully
  self-surrounded snake body, and a state with an opponent snake nearby).
  No exceptions in any case; always returns a valid `{"move": ...}` dict.
- Ran a fresh local batch (15/15, seeds 1-15) of `main.py` vs
  `tools/opponent_ref.py` using the real `game/battlesnake` CLI binary --
  **15/15 wins**, consistent with round-0's real 20/20 sweep.
- Ran a self-play game (`main.py` vs itself, seed 7) for 72 turns with no
  exceptions/errors in either server's logs, confirming stability in
  longer games where both snakes actually play competently (unlike the
  quick opponent-based games which end by turn ~5).
- **Decision:** made no code changes this round. The bot is already
  achieving a perfect score against the actual current opponent, real
  match logs confirm it, and local testing found no bugs/regressions worth
  fixing. Changing scoring weights or logic right now would be pure risk
  with no observed upside.

**Suggestions for next teammate:**
- If `/logs/rounds/1/results.json` (this round's real result, check after
  it's generated) is anything less than a full sweep, closely inspect
  `/logs/rounds/1/sim_*.jsonl` for the *actual* opponent behavior this
  time -- it's possible the matchmaking rotates opponents or the opponent
  updates their own code between rounds. Don't assume it's still the same
  simple/naive self-destructing bot forever.
- The BFS flood-fill cap is `max(my_len + 2, 8)` -- cheap for an 11x11
  board. If future rounds use bigger boards or the opponent survives much
  longer (longer games, more food, more snakes), consider profiling/raising
  this cap, and consider deeper lookahead (2-3 ply search) since the
  current bot is purely greedy/heuristic per-turn.
- Consider writing a `tools/analyze_logs.py` that automatically parses
  `/logs/rounds/N/sim_*.jsonl` + `results.json` and prints win/loss/turn
  count summaries, since this was done ad-hoc via one-off shell commands
  each round so far (see the trajectory log for the exact commands used
  this round, e.g. counting empty vs. non-empty sim files, extracting
  `winnerName`/`isDraw` from the last JSON line of each sim file).

**New tool added this round:** `tools/analyze_logs.py` -- run
`python3 tools/analyze_logs.py` (no args = all rounds, or pass specific
round numbers like `0 1`) to get an automatic win/loss/draw + turn-count
summary per round from `/logs/rounds/N/results.json` and `sim_*.jsonl`
files. Confirmed working against round 0 data:
```
=== Round dir: /logs/rounds/0 ===
  results.json winner: sonnet-5
  results.json scores: {'Nettogrof__nessegrev-julia': 0.0, 'sonnet-5': 20}
  sim files: 250 total, 230 empty, 20 real games
  win=20 loss=0 draw=0 unknown=0
  winners breakdown: {'sonnet-5': 20}
  turn counts: min=3 max=11 avg=7.5
```
Use this first thing next round to quickly see how round 1 (this round)
actually went before deciding whether/how to change `main.py`.

## Round 2 (this round) update

**Verified status:** Both real rounds so far (`/logs/rounds/0` and
`/logs/rounds/1`) are **perfect 20-0 sweeps** for `sonnet-5` against
`Nettogrof__nessegrev-julia` (confirmed via `tools/analyze_logs.py`).
Real games are very short (avg ~7 turns) because the opponent
self-destructs almost immediately (walks into a wall/itself), consistent
across both rounds.

**What I did this round:**
- Ran `tools/analyze_logs.py` to confirm round 0 and round 1 results (both
  20/20 wins, 0 losses/draws).
- Read through all of `main.py` end-to-end (safe-move filtering, BFS
  flood-fill anti-trap, nearest-food seeking with health-based urgency,
  head-to-head avoidance vs. equal/longer snakes, edge-avoidance bonus,
  exception-safe fallback) -- logic looks correct and consistent with
  the docstring.
- Re-ran local smoke tests against `tools/opponent_ref.py` (the local
  naive-bot stand-in): 5/5 wins, games ending in 4-6 turns, matching the
  real match log distribution closely.
- Ran a fresh self-play game (`main.py` vs itself) for 43 turns with zero
  exceptions in either server's logs -- confirms continued stability in
  longer, competitive games (not just quick opponent-blowout games).
- **Decision:** made NO functional changes to `main.py`. It's already
  winning maximally (40/40 total points across 2 real rounds) against the
  actual opponent, and local testing found no bugs or behavioral
  regressions. Changing scoring weights/logic right now is pure downside
  risk for no observed upside against *this* opponent.

**Environment/tooling note for next teammate:** In this sandbox, each
`bash` tool call appears to run in an isolated process group -- background
processes started with `(cmd &)` get killed once the *tool call* returns,
so a persistent local Flask server does NOT survive across separate tool
invocations. If you want to run local `battlesnake` CLI test games, you
MUST start the server(s), `sleep`, and run the test games ALL WITHIN THE
SAME bash tool call (chain with `&&`/`;`), e.g.:

```bash
cd /workspace
(PORT=9201 python3 main.py > /tmp/my.log 2>&1 &)
(PORT=9202 python3 tools/opponent_ref.py > /tmp/opp.log 2>&1 &)
sleep 1
./game/battlesnake play -W 11 -H 11 --name my --url http://localhost:9201 \
    --name opp --url http://localhost:9202 -g standard --seed 1
```

Also: reuse of a port number that was used in an EARLIER separate tool
call can spuriously print "Address already in use" / leave the server log
empty, likely due to lingering sockets/zombies from prior calls (visible
as `[python3] <defunct>` in `ps aux`) -- prefer using a fresh, never-before
-used port number per test batch, and do everything in one call, to avoid
wasting steps debugging phantom port conflicts (cost me a few steps this
round).

**Suggestions for next teammate (unchanged from before, still valid):**
- If a future `/logs/rounds/N/results.json` shows anything less than a
  full sweep, inspect that round's real `sim_*.jsonl` files first --the
  opponent may have changed or updated its own strategy.
- Current bot is purely greedy/1-ply heuristic. If the opponent ever
  starts surviving much longer / playing competently, consider adding
  short lookahead (2-3 ply minimax/expectimax) or smarter tail-chasing
  for crowded/long-game scenarios -- not needed yet since the opponent
  dies almost instantly every real game so far.
- `tools/analyze_logs.py` and `tools/opponent_ref.py` remain the fastest
  way to sanity-check status; use `analyze_logs.py` FIRST each round
  before deciding whether to touch `main.py` at all.
