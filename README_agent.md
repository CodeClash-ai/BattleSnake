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

## Round 1 (this round, actual round-1 log analysis + fix) update

**Real status check first:** Only `/logs/rounds/0/` exists so far (contrary to
some earlier notes above that assumed a "round 1"/"round 2" already
happened -- those were written by teammates who mislabeled which round they
were in; ignore round numbers in the prose above, trust the actual
`/logs/rounds/` directory contents each time). Round 0's real opponent was
**`Nettogrof__nessegrev-java`**, and the result was **25 wins / 2 losses**
out of 27 real games (see `tools/analyze_logs.py` output), NOT a perfect
sweep like earlier notes assumed for a different (older/different) opponent
name. So this round's job was to find out *why* we lost those 2 games and
fix it.

**Root cause of the 2 losses (`sim_245.jsonl`, `sim_249.jsonl`):** Both
losses happened in *long* games (100+ turns) where our snake grew very
large (length ~19 on an 11x11 board) and, over many turns, coiled itself
into a 2-row-hugging spiral along the top wall with **no branching moves
left** (self-body blocked 3 of 4 directions repeatedly, forcing a straight
march along the wall into the top-left corner). The opponent's small body
happened to occupy the corner's other exit cell, so by the time our snake
reached the corner it had zero legal moves. Traced back turn-by-turn
(see analysis commands in this round's trajectory / re-derivable via the
`python3 -c` snippets against `/logs/rounds/0/sim_245.jsonl`): the fatal
commitment happened turns *before* the actual death, while there was
still technically "enough" reachable space by the old bot's flood-fill
metric -- but the old flood-fill was capped very low
(`cap = max(my_len + 2, 8)`, e.g. only 21 cells checked for a
length-19 snake) so it could not distinguish "leads into a big open
region" from "leads into a merely-adequate-looking corridor that
tightens later as our own tail continues occupying it." This is a classic
battlesnake self-trap failure mode from greedy 1-ply heuristics.

**Fix implemented in `main.py` this round:**
1. Replaced the capped `_flood_fill_size` with a general `_flood_fill()`
   that does a **full/uncapped** BFS by default (board is tiny -- even
   121 cells is trivial to fully explore every turn) so candidate moves
   leading to meaningfully bigger open regions are now actually scored
   higher instead of both saturating the same low cap and looking tied.
2. Added a **tail-reachability check**: `_flood_fill()` now also reports
   whether the search reached our own tail cell (which is always treated
   as vacating soon, same logic as before). If a candidate move still
   lets us path back to our own tail, that's a strong classic signal
   we're not walling ourselves in; added `+15` bonus if reachable, `-60`
   penalty if not (once `my_len >= 4`), on top of the existing
   space-based scoring.
3. Added a softer "risky-but-not-immediately-fatal" penalty tier: if
   reachable space is between `my_len` and `my_len * 1.5`, apply a mild
   scaled penalty (previously there was only a *hard* penalty below
   `my_len` and then nothing -- no gradient telling it to prefer roomier
   options when several candidates all technically clear the `my_len`
   bar).
4. Kept everything else the same (nearest-food seeking with health-based
   urgency, head-to-head avoidance vs equal/longer snakes, edge-distance
   bonus, exception-safe fallback, etc).

**Testing done:**
- `python3 -c "import ast; ast.parse(open('main.py').read())"` -- syntax OK.
- Ran real `game/battlesnake` CLI self-play: new `main.py` vs the old
  (pre-this-round) `main.py`, seeds 1-15, 11x11 standard: **new won 8/15**,
  old won 7/15 -- roughly even, as expected for two similarly-capable
  heuristic bots playing each other (this test mainly confirms no
  regression/crash, not a strict improvement signal against *itself*).
  No errors/exceptions/tracebacks in either server's logs across all
  games, several of which ran 100-210 turns (good exercise of the
  long-game/self-trap-prone code paths that mattered for the round-0
  losses).
- Did NOT have time this round to reproduce the *exact* round-0 loss
  scenario turn-by-turn against the new code (e.g. replaying
  `sim_245.jsonl`'s board states through the new `move()` directly) --
  **recommended next step for next teammate**: write a small script that
  loads a `sim_*.jsonl` frame (turn ~90-96 of `sim_245.jsonl`, where the
  fatal wall-hugging commitment was still avoidable) and feeds it as a
  synthetic `game_state` to `main.move()`, to directly verify the new
  scoring picks a different (safer) direction than what actually happened
  in the log. I ran out of step budget to build+validate that harness
  this round.

**For the next teammate:**
- Re-run `tools/analyze_logs.py` first thing to see the real round-1
  result. If losses persist and look similar (long game, big snake,
  cornered), consider going further: e.g. a proper N-ply lookahead/
  minimax, or a Hamiltonian-cycle-following mode once the snake gets very
  long relative to the board (guarantees no self-trap but is more complex
  and can look "passive").
- `tools/opponent_ref.py` models a different/older naive opponent
  (kotlin/pambrose-style, always walks toward *farthest* food) -- it is
  NOT a faithful model of `Nettogrof__nessegrev-java` (the java opponent
  actually survives much longer in real games, per round-0 logs: turn
  counts min=3 max=132 avg=15.9, and both real losses were 100+-turn
  games). Treat `opponent_ref.py` wins as only a weak smoke test now, not
  a strong signal, since it dies almost instantly and won't exercise the
  long-game self-trap issues. Consider building a truer local model of
  the actual java opponent if more of its behavior can be inferred from
  `/logs/rounds/0/sim_*.jsonl` (e.g. does it seek nearest/farthest food,
  does it avoid collisions at all -- it clearly survives much longer than
  the old "pambrose" description implied, so it's not fully naive).
- A backup of the pre-this-round `main.py` was NOT kept as a separate file
  in the end (removed `main.py.bak_round1` after confirming the new
  version). If you want to diff against round-0's exact submitted code,
  check git history / the round-0 agent trajectory logs instead.

## Round 2 (this actual round, real /logs/rounds/{0,1} verified) update

**Verified real results (via `tools/analyze_logs.py`, ground truth from
`/logs/rounds/N/results.json` + `sim_*.jsonl`):**
- `/logs/rounds/0/`: `sonnet-5` **25 wins / opponent 2 wins** (27 real games
  recorded), vs opponent `Nettogrof__nessegrev-java`. Turn counts min=3
  max=132 avg=15.9 -- this is the round where the previous teammate found
  and fixed the long-game self-trap bug (uncapped flood-fill + tail-
  reachability bonus/penalty, see the "Fix implemented in main.py this
  round" section above in this file for full details of that fix).
- `/logs/rounds/1/`: **20-0 perfect sweep** for `sonnet-5`, same opponent.
  Turn counts min=3 max=11 avg=6.7 -- opponent self-destructs almost
  immediately basically every game post-fix. This confirms the self-trap
  fix from the previous round worked and didn't introduce any regression:
  round 1 (after the fix) was strictly better than round 0 (0 losses vs 2).

**What I did this round:**
- Confirmed via `tools/analyze_logs.py` that both real rounds so far are
  wins for us (25-2 then 20-0), and that the round-0-to-round-1 self-trap
  fix (already in current `main.py`, described in detail earlier in this
  file) is holding up -- no further real losses since the fix landed.
- Read through the entirety of current `main.py` (283 lines) end-to-end:
  safe-move filtering w/ tail-vacate-aware collision checks, head-to-head
  avoidance vs equal/longer snakes, **uncapped** BFS flood-fill scoring
  with a graduated penalty (hard penalty below `my_len`, soft penalty
  below `1.5x my_len`), a tail-reachability bonus/penalty (can we still
  path back to our own tail after this move -- strong anti-self-trap
  signal), nearest-food seeking with health-based urgency scaling,
  edge-distance bonus, small tie-breaking randomness, and an exception-
  safe fallback (`except Exception: return {"move": "up"}` plus a
  no-safe-move degenerate fallback). Logic all looks correct and
  consistent with the module docstring; found no bugs.
- **IMPORTANT environment gotcha discovered/reconfirmed this round:**
  starting local test servers with plain `(cmd &)` inside a bash tool call
  can leave the *foreground* shell hanging/timing out on later commands in
  the same or later tool calls, and simple `PORT=X python3 main.py &`
  backgrounding is unreliable for chaining multiple test batches (a naive
  attempt this round caused two tool calls to time out / return exit code
  143 with no output at all, wasting steps). **Fix that worked reliably:**
  use `setsid nohup env PORT=X python3 main.py > /tmp/x.log 2>&1 < /dev/null &`
  followed by `disown -a`, e.g.:
  ```bash
  setsid nohup env PORT=9701 python3 main.py > /tmp/my.log 2>&1 < /dev/null &
  setsid nohup env PORT=9702 python3 tools/opponent_ref.py > /tmp/opp.log 2>&1 < /dev/null &
  disown -a
  sleep 1
  # now servers are fully detached and safe to use across subsequent
  # tool calls / commands in the same or even later calls, e.g.:
  ./game/battlesnake play -W 11 -H 11 --name my --url http://localhost:9701 \
      --name opp --url http://localhost:9702 -g standard --seed 1
  ```
  Also wrap each `battlesnake play` invocation in `timeout 15 ...` as a
  safety net regardless. Always use fresh, never-before-used port numbers
  per test batch within a round (lingering `<defunct>`/zombie processes
  from earlier tool calls in the same round can cause spurious "Address
  already in use" on port reuse, per prior teammates' notes -- confirmed
  again this round). When done testing, `pkill -9 -f "python3 main.py"`
  and `pkill -9 -f "opponent_ref.py"` to clean up before finishing your
  turn (courtesy to whoever/whatever runs after you in the same sandbox).
- After fixing the server-detachment issue, ran a clean local batch:
  **10/10 wins** for `main.py` vs `tools/opponent_ref.py` (seeds 1-10,
  11x11 standard), games ending in 4-6 turns each -- consistent with the
  real round-1 log distribution (avg 6.7 turns). An earlier *broken*
  attempt this round (before fixing the detachment issue) had produced
  a misleading 2-3/5 "win" batch with some 100-200 turn games -- almost
  certainly due to stale/zombie server processes from a previous test
  answering requests inconsistently, NOT a real bot weakness. If you see
  weird/inconsistent results in a local test batch, suspect the harness
  before suspecting `main.py` -- always verify server logs
  (`/tmp/*.log`) don't show "Address already in use" before trusting
  local results.
- **Decision:** made NO functional changes to `main.py` this round. Real
  match data (rounds 0-1) shows the current strategy is strong (25-2 then
  20-0), the previous round's self-trap fix is validated by the improved
  round-1 result, and this round's (corrected) local testing found no new
  bugs. Further tinkering right now is unnecessary risk.

**Suggestions for next teammate:**
- First thing: run `python3 tools/analyze_logs.py` to check
  `/logs/rounds/2/` (this round's real result, generated after you
  submit) once it exists for your round. If it's still a clean sweep or
  near-sweep, further exotic changes (multi-ply search, Hamiltonian
  cycles, etc.) are probably not worth the risk. If losses reappear,
  inspect the specific `sim_*.jsonl` for the failure mode (as was done
  for the round-0 losses -- see the detailed "Fix implemented in main.py"
  section above for the methodology: find the losing sim files, trace
  turn-by-turn body positions in the turns leading up to death, and look
  for the point where fewer alternatives were available than the scoring
  metric suggested).
- If you want to do local server-based testing, copy the
  `setsid nohup ... & disown -a` pattern above verbatim -- it's the
  reliable way now; don't waste steps rediscovering the port/hang issue.
- The opponent's actual name across both real rounds so far has been
  consistently `Nettogrof__nessegrev-java`. `tools/opponent_ref.py` is
  still just a rough/naive stand-in (farthest-food, dominant-axis, zero
  collision-avoidance) and is NOT a verified faithful model of the real
  java opponent -- it's useful only as a cheap sanity/regression smoke
  test for our own bot (no exceptions, no infinite loops, wins easily
  against something naive), not as a strong predictor of real-match
  score. Treat its results as directional only.

## Round (this session) update -- ground-truth check + robustness re-verification

**IMPORTANT ground truth correction:** Ignore round numbers/opponent names
mentioned in the very long prose history above -- they were written by
different teammates who were sometimes confused about which round they
were actually in, and the opponent's name has changed between sessions
(seen so far: `Nettogrof__nessegrev-java`, and now `csauve__bookworm`).
**Always regenerate ground truth yourself** by running:

```bash
python3 tools/analyze_logs.py
```

At the start of *this* session, `/logs/rounds/` contained **only
`/logs/rounds/0/`**, result: **perfect 20-0 sweep** for `sonnet-5` against
`csauve__bookworm` (see `/logs/rounds/0/results.json`). Real games are
very short (turn counts min=3 max=11 avg=7.0 per `analyze_logs.py`) --
the opponent self-destructs almost immediately every game, same pattern
as previous opponents in earlier notes above.

**What I did this session:**
- Read all of `main.py` (283 lines) end-to-end. Strategy: safe-move
  filtering (in-bounds, body-collision incl. tail-vacate logic, avoid
  head-to-head vs equal/longer snakes) -> uncapped BFS flood-fill space
  scoring with graduated penalties + a tail-reachability bonus/penalty
  (anti-self-trap) -> nearest-food seeking w/ health-based urgency ->
  small edge-avoidance bonus -> tiny tie-break randomness -> exception-
  safe fallback. No bugs found; logic is sound and consistent with its
  own docstring.
- Verified `main.py` parses cleanly (`ast.parse`).
- Ran real local test games via the actual `game/battlesnake` CLI binary:
  - `main.py` vs `tools/opponent_ref.py` (naive stand-in bot): **5/5
    wins**, games ending in 4-6 turns -- matches the real round-0 log
    distribution (avg 7 turns) closely.
  - `main.py` vs itself (self-play), 3 games: all completed cleanly with
    no exceptions, including a 136-turn and a 115-turn game (exercises
    long-game / big-snake / self-trap-avoidance code paths, not just the
    instant-opponent-death case). Checked `/tmp/*.log` server output for
    "error"/"exception"/"traceback" -- none found.
- **Decision: made NO functional changes to `main.py` this session.** The
  bot is already winning maximally (20/20) in the only real round played
  so far, and fresh local testing (both vs. the naive reference and in
  self-play/long games) found zero bugs, crashes, or obviously-wrong
  decisions. Given the small step budget per session and that this
  strategy is undefeated in real play, I judged further tinkering to be
  pure risk without a concrete failure mode to fix (unlike the earlier
  documented round where real losses in `/logs/rounds/0/sim_*.jsonl`
  motivated the uncapped-flood-fill + tail-reachability fix -- that fix
  is still in place and working).

**Environment gotcha found/reconfirmed this session (save yourself the
steps):** `pkill -f "<pattern>"` / `pgrep -f "<pattern>"` will match
**their own shell command line** if the pattern string (e.g. `main.py` or
`opponent_ref.py`) literally appears in the command you just ran, because
`-f` matches the *full* command line of every process including the
`bash -c "..."` wrapper for your own command. This can SIGKILL your own
shell mid-command (shows up as exit code 137 with no output at all,
looking like an unrelated hang/timeout). **Prefer plain `ps aux | grep py`
+ manual `kill -9 <pid>` by PID**, or use a pattern that does NOT
textually appear elsewhere in your command (e.g. add a distinguishing
env var), when cleaning up background test servers.

**Suggestions for next teammate:**
- Start by running `python3 tools/analyze_logs.py` to see the actual
  latest `/logs/rounds/` ground truth -- don't trust old prose in this
  file about round numbers/opponent names, they've been wrong/stale
  before.
- If a real loss shows up in a future round, find the specific losing
  `sim_*.jsonl`, trace the board state turn-by-turn in the moments before
  death (see the detailed methodology written up earlier in this file
  under "Fix implemented in main.py this round" for the round where the
  uncapped-flood-fill + tail-reachability fix was added -- that's the
  template to follow: find where fewer alternatives existed than the
  scoring metric assumed, and patch the specific gap).
- The opponent has changed names across sessions but has consistently
  been a bot that self-destructs almost immediately (dies within ~3-11
  turns) in every real game logged so far. If a future opponent survives
  much longer / plays competently, that's the signal to invest in real
  lookahead (2-3 ply minimax/expectimax) instead of the current greedy
  1-ply heuristic -- not needed yet.
- `tools/opponent_ref.py` + `tools/analyze_logs.py` remain the fastest
  smoke-test tools; the `setsid nohup ... & disown -a` server-launch
  pattern documented earlier in this file still works for local
  `game/battlesnake` CLI testing.

## Round 2 (this session) update -- ground truth re-verified, no changes needed

**Ground truth (via `python3 tools/analyze_logs.py`):** `/logs/rounds/`
contains rounds `0` and `1` only at the start of this session, both
**perfect sweeps** for `sonnet-5` against opponent `csauve__bookworm`:
- Round 0: 20-0 (20 real games), turn counts min=3 max=11 avg=7.0.
- Round 1: 35-0 (35 real games), turn counts min=3 max=11 avg=6.7.

Opponent still self-destructs almost immediately every real game (avg
~7 turns) -- same pattern noted by prior teammates for earlier-named
opponents. No evidence yet of a competent/long-surviving opponent.

**What I did this session:**
- Re-ran `tools/analyze_logs.py` to confirm the above ground truth fresh
  (don't trust old prose about round numbers/opponent names in this file
  -- confirmed again this session that they've drifted across sessions).
- Read all of `main.py` end-to-end again; logic is unchanged from what's
  described earlier in this file (safe-move filtering w/ tail-vacate
  logic + head-to-head avoidance vs equal/longer snakes -> uncapped BFS
  flood-fill space scoring w/ graduated penalty + tail-reachability
  bonus/penalty -> health-scaled nearest-food seeking -> edge-avoidance
  bonus -> tiny tie-break randomness -> exception-safe fallback). No
  bugs found.
- Ran hand-built edge-case tests directly against `main.move()`: (1) a
  snake with only one truly safe direction, (2) a two-snake board with no
  food, (3) a fully self-boxed-in 3x3 corner scenario with **zero** safe
  moves at all (tests the doomed-snake fallback branch that ignores body
  blocks). All three returned valid `{"move": ...}` dicts, no exceptions.
- Ran a real local batch via `game/battlesnake` CLI: `main.py` vs
  `tools/opponent_ref.py`, seeds 1-5, 11x11 standard -- **5/5 wins**,
  games ending in 4-6 turns, matching the real match log distribution.
- Ran a real self-play game (`main.py` vs itself, seed 42) that ran a
  full **184 turns** with no exceptions/errors in either server's log --
  confirms continued stability in long, crowded, big-snake games (where
  the earlier self-trap bug used to bite, per the historical "Fix
  implemented in main.py this round" section far above in this file --
  that fix is still in place, still working, still uncapped flood-fill +
  tail-reachability check).
- Cleaned up all background test server processes afterward (`kill -9` by
  PID, not `pkill -f` -- see the environment gotcha noted earlier in this
  file about `-f` patterns matching your own shell command).

**Decision: made NO functional changes to `main.py` this session.** Both
real rounds played so far are perfect sweeps (55/55 total real games won,
0 losses/draws) against the actual current opponent, and fresh local
testing (edge cases, naive-opponent smoke test, and a long 184-turn
self-play game) found zero bugs or crashes. There is no concrete observed
failure mode to fix right now, so further tinkering would be pure risk
for no measurable upside -- consistent with the judgment calls made in
several previous sessions documented above.

**Suggestions for next teammate (still valid, unchanged in substance):**
- Always start with `python3 tools/analyze_logs.py` for ground truth --
  ignore stale round-number/opponent-name claims elsewhere in this file.
- If a real loss ever appears in `/logs/rounds/N/results.json`, use the
  methodology documented earlier in this file (find the losing
  `sim_*.jsonl`, trace board state turn-by-turn before death, identify
  where the scoring heuristic's assumptions broke down) to diagnose and
  patch a *specific* gap, rather than broad rewrites.
- The bot is still purely greedy/1-ply. This has been sufficient so far
  because the opponent has never survived long/played competently in any
  real game logged to date. If that ever changes, short lookahead
  (2-3 ply minimax/expectimax against actual opponent behavior) is the
  natural next investment -- not needed yet.
- Server-testing gotchas (all still accurate): use
  `setsid nohup env PORT=X python3 main.py > /tmp/x.log 2>&1 < /dev/null &`
  + `disown -a` to detach cleanly across tool calls; use fresh unused
  port numbers each batch; clean up with `kill -9 <pid>` by PID from
  `ps aux` rather than `pkill -f <pattern>` (which can kill your own
  current shell command if the pattern string appears in it).

## Round (this session, N) update -- ground truth re-verified again, no changes needed

**Ground truth (via `python3 tools/analyze_logs.py`):** at the start of
this session `/logs/rounds/` contained only `/logs/rounds/0/`, result:
**perfect 20-0 sweep** for `sonnet-5` against opponent
`coreyja__improbable-irene` (yet another new opponent name -- as noted
repeatedly above, the opponent's identity/name has varied across
sessions; always re-derive from `results.json`, don't trust old prose).
Turn counts: min=3 max=11 avg=5.8 -- opponent self-destructs almost
immediately every real game, consistent with the long pattern seen across
essentially all previous sessions regardless of opponent name.

**What I did this session:**
- Ran `tools/analyze_logs.py` for ground truth (see above).
- Read all of `main.py` end-to-end again (283 lines, unchanged from prior
  sessions' description: safe-move filtering w/ tail-vacate logic + H2H
  avoidance vs equal/longer snakes -> uncapped BFS flood-fill space score
  w/ graduated penalty + tail-reachability bonus/penalty -> health-scaled
  nearest-food seeking -> edge-avoidance bonus -> tiny tie-break
  randomness -> exception-safe fallback). No bugs found, parses cleanly
  (`ast.parse`).
- Ran a real local batch via `game/battlesnake` CLI: `main.py` vs
  `tools/opponent_ref.py` (naive stand-in), seeds 1-8: **8/8 wins**, games
  ending in 4-6 turns -- matches the real round-0 log distribution
  closely.
- Ran 3 real self-play games (`main.py` vs itself) at seeds 11/22/33:
  ran 154, 101, and 22 turns respectively with clean wins/losses between
  the two identical bots and **zero exceptions/errors** in either
  server's log (`grep -i "error|exception|traceback"` on both logs came
  back empty). This continues to exercise the long-game/big-snake/
  self-trap-avoidance code paths (the fix for which is documented in
  detail earlier in this file under "Fix implemented in main.py this
  round") with no regressions.
- Cleaned up background test server processes afterward.
- **Decision: made NO functional changes to `main.py` this session.**
  Rationale (same as essentially every prior session): the only real
  round played so far is a perfect sweep, fresh local testing (naive-
  opponent smoke test + multi-hundred-turn self-play) found zero bugs or
  crashes, and there is no concrete observed failure mode in real match
  data to fix. The bot remains purely greedy/1-ply heuristic; this has
  been sufficient in every real round logged across all sessions so far
  because no opponent encountered yet has survived long enough to expose
  a weakness beyond the historical self-trap bug (already fixed).

**Suggestions for next teammate (unchanged in substance from many prior
sessions -- this pattern has been extremely stable):**
- Always start with `python3 tools/analyze_logs.py` for real ground
  truth; ignore stale round-number/opponent-name claims in old prose
  above (confirmed once again this session that opponent identity drifts
  session-to-session: seen so far across the full history of this file --
  pambrose-kotlin(-style reference only), `Nettogrof__nessegrev-julia`,
  `Nettogrof__nessegrev-java`, `csauve__bookworm`, and now
  `coreyja__improbable-irene`).
- If a real loss ever shows up in a future `results.json`, use the
  documented methodology (find the losing `sim_*.jsonl`, trace board
  state turn-by-turn before death, identify exactly where the scoring
  heuristic's assumptions broke down, patch that specific gap) rather
  than broad rewrites -- this is exactly how the uncapped-flood-fill +
  tail-reachability anti-self-trap fix (still in place, still working)
  was found and fixed previously.
- If a future opponent ever plays competently / survives long (unlike
  every opponent seen so far, which self-destructs in ~3-11 turns nearly
  every real game), that's the trigger to invest in real lookahead
  (2-3 ply minimax/expectimax) instead of continuing to rely on the
  current greedy 1-ply heuristic -- not needed yet based on all evidence
  to date.
- Server-testing gotchas (all still accurate, reconfirmed again this
  session): use
  `setsid nohup env PORT=X python3 main.py > /tmp/x.log 2>&1 < /dev/null &`
  + `disown -a` to detach across tool calls; use fresh/unused port
  numbers each batch; clean up test servers with `kill -9 <pid>` found
  via `ps aux` (NOT `pkill -f <pattern>`, which can match and kill your
  own current shell command if the pattern text appears in it).

## Round (this session) update -- ground truth re-verified, still winning, no changes

**Ground truth (via `python3 tools/analyze_logs.py`) at start of this
session:** `/logs/rounds/` contained `0` and `1`, both **perfect sweeps**
for `sonnet-5` against opponent `coreyja__improbable-irene`:
- Round 0: 20-0 (20 real games), turn counts min=3 max=11 avg=5.8.
- Round 1: 22-0 (22 real games), turn counts min=3 max=178 avg=22.3 --
  note this round included at least one much longer game (178 turns) than
  round 0's max of 11, and we still won every real game, which is a good
  sign the historical self-trap fix (uncapped flood-fill + tail-
  reachability bonus/penalty, documented in detail earlier in this file)
  continues to hold up even as games get longer/more complex.

**What I did this session:**
- Confirmed the above via `tools/analyze_logs.py`.
- Read `main.py` (283 lines, unchanged) top-to-bottom again; confirmed
  `ast.parse` succeeds; logic matches its own docstring (safe-move
  filtering w/ tail-vacate + H2H avoidance vs equal/longer snakes ->
  uncapped BFS flood-fill scoring w/ graduated penalty + tail-
  reachability bonus/penalty -> health-scaled nearest-food seeking ->
  edge-avoidance bonus -> tiny tie-break randomness -> exception-safe
  fallback). No bugs spotted.
- Ran a fresh local batch via the real `game/battlesnake` CLI: `main.py`
  vs `tools/opponent_ref.py` (naive stand-in), seeds 1-6: **6/6 wins**,
  games ending in 4-6 turns (matches round-0 distribution). No
  error/exception/traceback lines in either server log.
- Ran one self-play game (`main.py` vs itself, seed 99): completed
  cleanly after **88 turns** with a winner determined, zero exceptions in
  either server's log. Exercises the longer-game code paths relevant to
  round 1's 178-turn max game.
- Cleaned up all background test server PIDs afterward.

**Decision: made NO functional changes to `main.py` this session.**
Rationale: both real rounds played so far are perfect sweeps (42/42 total
real games won across rounds 0-1, 0 losses/draws) against the actual
current opponent (`coreyja__improbable-irene`), including a round with a
much longer max game length (178 turns) than before with no losses --
strong evidence the bot's anti-self-trap logic scales fine to longer
games. Fresh local testing this session (naive-opponent smoke test +
self-play) found zero bugs, crashes, or exceptions. No concrete failure
mode exists to justify changing scoring weights/logic right now; doing so
would be pure risk for no observed upside.

**Suggestions for next teammate (same guidance as many prior sessions,
still valid):**
- Always start with `python3 tools/analyze_logs.py` for real ground
  truth; ignore stale round-number/opponent-name claims elsewhere in this
  file (opponent identity has changed name almost every session so far:
  see the long list accumulated above -- most recently
  `coreyja__improbable-irene`).
- If a real loss ever shows up in a future `results.json`, use the
  documented methodology (find the losing `sim_*.jsonl`, trace board
  state turn-by-turn before death, identify exactly where the scoring
  heuristic's assumptions broke down, patch that specific gap) -- this is
  how the uncapped-flood-fill + tail-reachability fix was originally
  found and remains the template for future fixes.
- Round 1 this session had a max turn count of 178 (vs round 0's max of
  11) -- worth keeping an eye on whether future rounds keep trending
  toward longer games (opponent improving / surviving longer). If a
  future opponent starts playing competently and turn counts/losses climb
  together, that's the trigger to invest in real lookahead (2-3 ply
  minimax/expectimax) instead of the current greedy 1-ply heuristic.
- Server-testing gotchas (all reconfirmed working again this session):
  use `setsid nohup env PORT=X python3 main.py > /tmp/x.log 2>&1 < /dev/null &`
  + `disown -a` to detach across tool calls; use fresh/unused port
  numbers each batch; clean up test servers with `kill -9 <pid>` found
  via `ps aux` (NOT `pkill -f <pattern>`, which can match and kill your
  own current shell command if the pattern text appears in it).

## Round (this session) update -- FOUND & FIXED a real self-trap bug (food-eating tail-freeze)

**Ground truth (`python3 tools/analyze_logs.py`) at start of session:**
`/logs/rounds/0/` only, opponent `graeme-hill__snakebot`, result **83 wins /
4 losses** out of 87 real games. Turn counts min=3 max=278 avg=25.3 (much
longer games than most previous sessions' opponents).

**Root cause of all 4 losses (sim_172/175/232/245.jsonl), found by replaying
real match states directly through `main.move()`:** All 4 losses were very
long games where our snake grew huge (30-36 length on an 11x11 board) and
died coiled in a self-made pocket. Traced `sim_172.jsonl` turn-by-turn by
feeding the *actual logged board states* into `main.move()` (confirmed it
reproduces the exact same losing move sequence as the real game -- see the
one-off script used this session, not saved as a file, but the technique
is: load a `sim_*.jsonl`, for each frame set `state["you"]` to our snake's
own dict from `board.snakes`, call `main.move(state)`, compare to what
actually happened next frame).

Found the *exact* turn where things went wrong: at turn 254, our snake had
3 tied-looking safe options (up/down/left), all reporting `space=35,
reached_tail=True` under the old flood-fill. It picked `left`, which
happened to land on a **food cell**. But eating food means the snake
**grows instead of its tail vacating** that turn -- and the old
`_flood_fill` call for scoring candidates always treated our own tail cell
as free/vacating (via `_occupied_cells`'s "did I eat last turn" check),
regardless of whether *this candidate move itself* would cause eating.
This let the bot believe "eating this food is totally safe, I can still
reach my tail" when in fact eating froze the tail in place and collapsed
its real reachable space from 35 down to ~23 the very next turn, which
then forced a series of single-option corridors ending in a dead corner
cell 21 turns later (turn 277 in the real log).

**Fix implemented in `main.py` this session (small, targeted):** in the
per-candidate scoring loop, added a check: if a candidate cell `npt` is a
food cell, treat our own tail cell as *still blocked* for that candidate's
flood-fill (`eff_blocked = blocked | {my_tail}`), since it won't actually
vacate this turn. This makes the space/reached-tail scoring correctly
reflect the real post-eating board and rank that option much lower
(hard `space < my_len` penalty + `-60` no-tail-reach penalty instead of
`+15`) whenever eating would meaningfully shrink our free space. Verified
by directly re-running the exact same turn-254 board state from
`sim_172.jsonl` through the patched `move()`: it now picks `down` (a
different branch that keeps `space=35, reached_tail=True` *without*
eating) instead of the fatal `left`/food branch. This is a minimal,
well-isolated change -- only affects scoring of candidates that land on
food cells, doesn't touch anything else.

**Testing done:**
- `ast.parse` syntax check: OK.
- Replayed the losing `sim_172.jsonl` states through both the old and new
  `move()` logic side-by-side (see above) -- confirmed the new code
  changes the pivotal turn-254 decision away from the food cell that led
  to death.
- Local batch vs `tools/opponent_ref.py` (naive stand-in), seeds 1-5:
  **5/5 wins**, 4-6 turns each, no errors/exceptions in either server log
  -- confirms no regression/crash from the change on the common/easy case.
- Did NOT have time this session to run a full long multi-hundred-turn
  self-play regression batch to double check the fix doesn't introduce a
  *different* subtle issue elsewhere (e.g. becoming overly food-averse in
  some edge case) -- **recommended next step for next teammate**: run
  several self-play games (`main.py` vs itself) for 100+ turns and check
  for exceptions/weird stalling, and if possible replay `sim_175.jsonl`,
  `sim_232.jsonl`, `sim_245.jsonl` (the other 3 real losses from this
  session's round) through the new code the same way to see if this same
  fix also resolves those (likely, since all 4 were long-game self-traps,
  but not yet individually confirmed).

**For next teammate:**
- First: `python3 tools/analyze_logs.py` for fresh ground truth on how
  this fix actually performed in the next real round.
- If losses persist, use the exact replay-through-`move()` technique
  documented above (it's very effective -- found this bug directly from
  real match data in a handful of steps) on the new losing sim files.
- Other candidate follow-up hardening ideas (not yet implemented,
  speculative): the same "will this move cause MY tail to freeze" logic
  could be extended to *opponent* snakes when checking head-to-head/
  space-sharing risk (if an opponent is adjacent to food, they may also
  grow and not vacate their tail -- currently only accounted for via the
  post-hoc "did they eat last turn" check on the CURRENT frame, not
  predictively for opponents' upcoming moves). Low priority since our own
  eating was the actual observed failure mode, not opponents'.
- Server-testing gotchas (reconfirmed working this session): use
  `setsid nohup env PORT=X python3 main.py > /tmp/x.log 2>&1 < /dev/null &`
  + `disown -a`; use `ps aux | grep <pattern> | grep -v grep | awk
  '{print $2}' | xargs -r kill -9` to clean up (avoid `pkill -f`, which
  can match and kill your own current shell command).

## Round (this session) update -- FOUND & FIXED a major starvation bug (4/5 losses)

**Ground truth (`python3 tools/analyze_logs.py`) at start of session:** both
`/logs/rounds/0/` and `/logs/rounds/1/` existed, opponent
`graeme-hill__snakebot`:
- Round 0: 83 wins / 4 losses (87 real games), turns min=3 max=278 avg=25.3.
- Round 1: 82 wins / 5 losses (87 real games), turns min=3 max=239 avg=17.3.

**Root cause investigation (this session):** grouped losses by checking
our snake's health history in each losing `sim_*.jsonl`
(`/logs/rounds/1/sim_{213,214,216,227,231}.jsonl` were the 5 round-1
losses). **4 of 5** round-1 losses were pure **starvation** deaths: health
ticked steadily 10->9->...->1->0 with our snake's length stuck flat for
80-200+ turns despite being on a wide-open board with abundant food and no
opponent nearby. Replayed the exact logged board state at intermediate
turns directly through `main.move()` (technique: build a synthetic
`game_state` from the sim frame's `board` + our own snake dict as `you`,
call `main.move(state)` directly, print per-candidate diagnostics) and
found the bug in `sim_213.jsonl` turn 50: head at `(7,7)`, health 52,
**food directly adjacent** at `(7,6)`, 113+ open cells everywhere -- and
the bot chose to walk AWAY from the food anyway.

**Exact mechanism:** the old scoring had a flat `+15` bonus / `-60`
penalty for whether a candidate move preserved "can I still BFS-path back
to my own tail" (`reached_tail`), applied unconditionally once
`my_len >= 4`, with NO regard for how much open space was actually
available. Eating food freezes your tail in place for that turn (doesn't
vacate), so almost any adjacent-food move loses `reached_tail` for one
turn -- even in a 113-open-cell board where this is obviously irrelevant.
That flat -60/+15 swing (75 points) dwarfed the food-attraction bonus
(capped at ~60 even at critical health), so the bot reliably preferred
"walk in a small loop forever, keep `reached_tail=True`" over "eat the
food right next to me," turn after turn, until it starved to death. This
is exactly the kind of failure the game's realistic long-running matches
exposed that short local smoke tests (naive-opponent 5-turn blowouts)
never would have caught -- **local testing against `opponent_ref.py` was
totally blind to this bug** since those games end almost instantly, well
before health ever gets low. Lesson for future sessions: replaying REAL
match sim files (especially long/losing ones) through `main.move()`
directly is far more valuable than local smoke tests against the naive
reference bot once the easy bugs are fixed.

**Fix implemented in `main.py` this session:**
1. The tail-reachability bonus/penalty is now gated by an
   `open_threshold = max(my_len * 4, 24)`: if post-move reachable `space`
   is at/above that threshold (comfortably open board), the bonus/penalty
   collapses to a tiny `+3`/`0` tie-break instead of the old flat
   `+15`/`-60` -- losing tail-reachability for one turn on a wide-open
   board is a non-issue and should not scare the bot away from food.
   Below the threshold (actually tight/cramped situations -- the
   scenario this penalty was originally added for, per earlier session
   notes in this file), the original `+15`/`-60` behavior is preserved
   unchanged, since THAT fix (from an earlier session, for real
   self-trap corner-death losses) is still valid and still needed.
2. Food urgency now ramps up smoothly and much more steeply as health
   drops (`urgency = 1.0 + 8.0 * ((60 - health)/60)**2` below 60 health,
   vs. the old flat 1.5x/3x step function), plus a new explicit bonus
   (`+40 * (60-health)/60`) specifically for a candidate move that eats
   food *this turn* (`nearest == 0`) once health <= 60 -- makes
   "immediately eat adjacent food" dominate over "stay in a safe loop"
   once health is a real concern, without needing to touch the hard
   space-safety penalties (space < my_len is still hard-blocked exactly
   as before -- this fix does NOT make the bot eat into real death
   traps, only removes the *false* trap signal on open boards).

**Testing done this session:**
- `ast.parse` syntax check: OK.
- Replayed `sim_213.jsonl` turn 50 (the exact bug instance) through the
  patched `move()`: now correctly returns `down` (eats the adjacent food)
  instead of the old `right` (walks away). Verified across several other
  turns (14/20/30/50/70/90) in the same losing game -- bot now reliably
  eats nearby food at low/medium health instead of avoiding it.
- Local batch via real `game/battlesnake` CLI: `main.py` vs
  `tools/opponent_ref.py`, seeds 1-8: **8/8 wins**, 4-7 turns each, zero
  errors/exceptions in server logs (unchanged from before -- confirms no
  regression on the easy case).
- Self-play (`main.py` vs itself), 5 total games across two batches
  (seeds 11/22/33/44/99): games ran 54-266 turns, all completed cleanly
  with a winner, **zero exceptions** in any server log. Explicitly
  checked the health/length of the final frame of one long self-play game
  (seed 99, 98 turns) -- loser died at health 82/92 (i.e. a real collision
  death, NOT starvation), confirming the new urgency curve doesn't cause
  any new pathological "eats too aggressively into danger" behavior in
  normal competitive play.
- Did NOT do a full forward re-simulation of the real opponent
  (`graeme-hill__snakebot`)'s actual behavior against the new bot (no
  local reimplementation of that specific opponent exists yet -- only
  `tools/opponent_ref.py`, which models an older/different/naive
  opponent and is a weak proxy). The real validation will be
  `/logs/rounds/2/results.json` after this session's submission.

**For next teammate:**
- First: run `python3 tools/analyze_logs.py` for real ground truth on how
  this fix performed against the real opponent in the next round. If
  round-2 losses/turn-counts drop significantly vs round 1 (82-5, avg 17.3
  turns) that's strong confirmation the starvation bug was the main
  problem. Round 0's 4 losses (`sim_172/175/232/245.jsonl`) were a
  *different*, already-fixed issue (real cramped self-traps in very long
  big-snake games -- see the much earlier "Fix implemented in main.py this
  round" section in this file); if losses of THAT flavor reappear, that's
  unrelated to this session's fix and needs separate investigation.
- If starvation losses somehow still occur, check whether the
  `open_threshold` gating logic needs tuning (e.g. maybe it should also
  consider distance-to-food, not just space; or the low-health urgency
  curve needs to be even steeper), and re-run the same
  replay-through-`move()` diagnostic technique documented above (extend
  the one-off script in this session's trajectory: build synthetic
  `game_state` from a sim frame + call `main.move()` directly + print
  per-candidate `space`/`reached_tail`/scores) on the new losing sim
  files to pinpoint exactly where the decision goes wrong, the same way
  this bug was found.
- General methodology reminder (now proven twice): local smoke tests vs.
  `tools/opponent_ref.py` (games ending in ~5 turns) are USELESS for
  catching health/starvation/long-game bugs since health never gets low
  in those games. Always additionally spot-check real losing
  `sim_*.jsonl` files from actual rounds by replaying specific frames
  through `main.move()` directly -- this is dramatically more effective
  than blind local batch testing for finding real bugs.
- Server-testing gotchas (all reconfirmed working this session): use
  `setsid nohup env PORT=X python3 main.py > /tmp/x.log 2>&1 < /dev/null &`
  + `disown -a` to detach across tool calls; use fresh/unused port
  numbers each batch; clean up test servers by finding PIDs via `ps aux`
  and `kill -9 <pid>` directly (NOT `pkill -f <pattern>`, which can match
  and kill your own current shell command if the pattern text appears in
  it -- confirmed multiple times across sessions now).

## Round (this session) update -- ground truth re-verified, no changes needed

**Ground truth (`python3 tools/analyze_logs.py`) at start of session:**
`/logs/rounds/` contained only `/logs/rounds/0/`, opponent
`coreyja__devious-devin` (yet another new opponent name, as usual --
opponent identity keeps changing session to session, don't trust old
prose about names/rounds elsewhere in this file). Result: **perfect 20-0
sweep** for `sonnet-5`. Turn counts min=3 max=11 avg=7.3 -- opponent
self-destructs almost immediately every real game, consistent with the
long-standing pattern across nearly every session in this file's history.

**What I did this session:**
- Ran `tools/analyze_logs.py` for ground truth (above).
- Read all of `main.py` (329 lines) end-to-end. Confirmed all the
  historically-important fixes documented earlier in this file are still
  present and intact:
  - safe-move filtering w/ tail-vacate-aware collision checks + H2H
    avoidance vs equal/longer opposing snakes,
  - **uncapped** BFS flood-fill space scoring w/ graduated penalty
    (hard penalty if `space < my_len`, soft penalty if `< 1.5x my_len`),
  - the "food-eating freezes tail" fix (treats own tail cell as still
    blocked in a candidate's flood-fill if that candidate move lands on
    food), which fixed a real self-trap death from an earlier session,
  - the "open_threshold" gating on the tail-reachability bonus/penalty
    (only a big +15/-60 swing when space is actually tight, tiny +3/0
    tie-break when space is comfortably large) -- this fixed the
    starvation bug from an earlier session where the bot avoided all
    nearby food forever on wide-open boards to preserve tail-reachability.
  - smooth health-based food urgency ramp + explicit "eat right now"
    bonus at low health.
  No bugs found; `ast.parse` succeeds cleanly.
- Ran a real local batch via `game/battlesnake` CLI: `main.py` vs
  `tools/opponent_ref.py` (naive stand-in reference bot), seeds 1-5:
  **5/5 wins**, games ending in 4-7 turns -- matches the real round-0 log
  distribution (avg 7.3 turns) closely.
- Ran 3 real self-play games (`main.py` vs itself), seeds 41/42/43: ran
  256, 242, and 158 turns respectively, all completed cleanly with a
  determined winner and **zero exceptions/errors** in any server log
  (`grep -iE "error|exception|traceback"` on all logs came back empty).
  This exercises the long-game / big-snake / starvation-avoidance /
  self-trap-avoidance code paths (where all the historical bugs were
  found and fixed) with no regressions observed.
- Cleaned up all background test server processes by PID afterward (not
  `pkill -f`, per the standing gotcha documented earlier in this file).
- **Decision: made NO functional changes to `main.py` this session.**
  Rationale (consistent with the large majority of prior sessions in this
  file): the only real round played so far this cycle is a perfect sweep
  (20/20) against the actual current opponent, and fresh local testing
  this session (naive-opponent smoke test + three long self-play games up
  to 256 turns) found zero bugs, crashes, exceptions, or obviously-wrong
  decisions. There is no concrete observed failure mode in real match
  data to fix right now; the last two real bugs found in this codebase's
  history (self-trap-from-eating-food and starvation-from-tail-anxiety,
  both documented in detail earlier in this file) were both found via
  replaying REAL losing `sim_*.jsonl` frames through `main.move()`
  directly, not through generic local smoke testing -- there are no
  losing sim files to replay this session since the result is a clean
  sweep, so there's nothing concrete to chase. Speculative changes here
  would be pure risk for no measurable upside.

**Suggestions for next teammate (same core guidance as essentially every
prior session, still valid and still the fastest path to real
improvements):**
- Always start with `python3 tools/analyze_logs.py` for real ground
  truth; ignore stale round-number/opponent-name claims in old prose
  elsewhere in this file (opponent identity has changed on nearly every
  single session so far -- full list accumulated across this file's
  history: pambrose-kotlin-style reference, `Nettogrof__nessegrev-julia`,
  `Nettogrof__nessegrev-java`, `csauve__bookworm`,
  `coreyja__improbable-irene`, `graeme-hill__snakebot`, and now
  `coreyja__devious-devin`).
- **If a real loss ever shows up** in a future `results.json`, the most
  effective methodology (proven at least twice now, see the detailed
  "Fix implemented in main.py this session" sections earlier in this
  file) is: find the losing `sim_*.jsonl`, build a synthetic
  `game_state` from a specific frame (set `you` to our snake's own dict
  from `board.snakes`, keep the rest of the board state as-is), call
  `main.move(state)` directly, and compare/trace against what actually
  happened -- this finds the exact turn+reason far faster than generic
  local smoke testing against `tools/opponent_ref.py` (which ends games
  in ~5 turns and is blind to health/starvation/long-game self-trap bugs
  by construction).
- The bot remains purely greedy/1-ply heuristic. This continues to be
  sufficient because no real opponent encountered across the entire
  history of this file has ever survived long enough / played well enough
  to expose a weakness beyond the two already-fixed bugs (self-trap via
  food-eating tail-freeze, and starvation via over-cautious tail-anxiety
  on open boards). If a future opponent starts playing competently and
  losses start appearing in real match data, that's the trigger to invest
  in short lookahead (2-3 ply minimax/expectimax) -- not needed yet.
- Server-testing gotchas (all reconfirmed working again this session):
  use `setsid nohup env PORT=X python3 main.py > /tmp/x.log 2>&1 < /dev/null &`
  + `disown -a` to detach across tool calls; use fresh/unused port
  numbers each batch; clean up test servers by finding PIDs via
  `ps aux | grep -E "main.py|opponent_ref"` and `kill -9 <pid>` directly
  (NOT `pkill -f <pattern>`, which can match and kill your own current
  shell command if the pattern text appears in it).
