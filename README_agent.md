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

## Round 2 update

Round 1 result: **250-0 total win** (see `/logs/rounds/1/results.json`).
The Kotlin opponent's naive strategy dies almost immediately (avg ~3.9
turns/sim, see `python3 analyze_logs.py /logs/rounds/1`) by crashing into
itself/walls, since it still has zero collision avoidance. Our heuristic
survival bot from round 1 never lost a single simulation.

### What I changed this round (round 2)

Given the dominant win rate, I made small, low-risk correctness/quality
improvements rather than a rewrite, to avoid regressing a 100%-win bot:

1. **Fixed tail-vacate approximation for snakes that just ate.** Previously
   `_build_blocked` always assumed every snake's tail cell frees up next
   turn. This is wrong the turn after a snake eats: the body array has a
   duplicated last segment (two trailing segments at the same coordinate,
   the standard Battlesnake growth representation), and that cell will
   *still* be occupied by the new tail after the coming move. This is now
   detected statelessly (`body[-1] == body[-2]`) and such tails are kept
   in `blocked`. This mostly matters in longer/self-play-style games; it
   should never fire against the current 3-4-turn-lived opponent, but
   makes the bot strictly more correct for any tougher opponent in future
   rounds.
2. **Added mild opportunistic aggression.** Previously we only avoided
   `risky_cells` (equal-or-longer opponent could reach). Now we also
   compute `winnable_cells` (cells only a strictly-shorter opponent's head
   could reach this turn) and give a small score bonus (+15) for moving
   into one -- since a head-to-head there kills the shorter snake and we
   survive. This only nudges among already-safe/high-scoring candidates
   (space/food scoring still dominates), so it shouldn't cause reckless
   plays.

### Testing done this round

- Verified `main.py` parses and `move()` runs correctly on a synthetic
  `game_state` (see quick inline test in shell history / just re-run
  similar snippet if needed).
- Ran the new bot against an unmodified copy of the pre-round-2 `main.py`
  (`/tmp/oldbot`, not persisted -- recreate from git history/round-1 logic
  if you want to re-run this) via the local `battlesnake` CLI engine.
  ~50 games total, roughly even split (expected: both are very similar
  heuristics playing each other, not a proxy for opponent strength). Games
  ran 26-285 turns with no crashes, no exceptions in server logs
  (`grep -i "error\|traceback\|exception"` clean). This mainly confirms
  no regression/crash was introduced, not a strength delta -- the real
  opponent is much weaker (no collision avoidance at all) so round-1's
  100% win rate should be untouched or improved by these changes.

### IMPORTANT environment gotcha for whoever tests locally next

Each bash tool call in this harness runs in a **fresh subshell** -- plain
`cmd &` background jobs die/become unreachable once the tool call
returns. To start a long-lived local Flask test server that survives into
your *next* tool call, use:

```bash
setsid nohup env PORT=8000 python3 main.py > /tmp/new.log 2>&1 < /dev/null &
disown
```

Also: avoid `pkill -f main.py` (or any pattern) inside a command whose own
command-line text contains that same string -- `pkill -f` matches against
the full command line of *all* processes including bash invocations
built from your own heredoc/inline script, so it can kill itself/sibling
processes unexpectedly. Prefer killing by PID (`ps aux | grep main.py`)
or a more specific pattern.

### Ideas for future improvement (carried over / updated)

1. **Look-ahead / simple minimax (2-3 ply)** -- still not done. Given the
   current opponent is trivial, this is low priority *unless* future
   rounds introduce a stronger opponent.
2. ~~Tail-vacate-after-eating fix~~ -- **done this round**.
3. **Tune aggression further**: right now it's a flat +15 bonus gated
   only by reachability, not by whether the resulting head-to-head is
   actually favorable board-position-wise (e.g. could still walk us into
   a smaller pocket -- though the space/flood-fill penalty should catch
   the worst cases already since it's just an additive bonus, not an
   override).
4. **Hazard support**: `board["hazards"]` still unused.
5. **Formal weight tuning**: flood-fill weight / food-distance weight /
   edge bonus / aggression bonus are all hand-picked, not swept via
   self-play tournament. Would be a good next step if a stronger opponent
   shows up and 1-ply heuristics stop being sufficient.

### Files

- `main.py` -- the bot.
- `analyze_logs.py` -- point at `/logs/rounds/<n>` to summarize
  results.json + per-sim win/turn-count stats.
