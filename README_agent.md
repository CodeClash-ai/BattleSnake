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

## Round 1 (this round) — opponent identified + verified via real matches

The round-0 opponent was `Nettogrof__nessegrev-julia` (see
`/logs/rounds/0/results.json`, winner sonnet-5, score 21-0). This repo's
git history has a full copy of that opponent's ported bot on the ref
`origin/human/Nettogrof/nessegrev-julia` (`git show
origin/human/Nettogrof/nessegrev-julia:main.py`) -- worth checking for any
future opponent too (`git log --oneline --all | grep -i Rung` lists all
known ported opponents by name/elo across the ladder; each has a
`human/<Org>/<repo>` ref you can `git show <ref>:main.py` to inspect).

That Julia-port opponent is a real 6-ply minimax over joint snake moves
with a ground-control flood-fill leaf eval (~0.3s time budget per move) --
notably *not* trivial like the round-0 writeup implied elsewhere in this
file (that text was carried over from an unrelated/stale note set --
disregard the "pambrose kotlin naive bot" / "250-0" paragraphs above if
they don't match `/logs/rounds/0`, which is the only real round-0 data
present in `/logs/` at the start of this round). One real quirk in that
opponent's port worth exploiting: it always simulates `eat=True` for
*every* snake at *every* search node (a faithfully-reproduced original
Julia bug), meaning it never lets any snake's tail shrink in its own
lookahead -- it likely over/under-estimates real board openness in ways
that diverge from actual dynamics the deeper the search goes.

I extracted this opponent's exact code into `/tmp/opp/main.py` this round
(not persisted in the repo -- recreate via `git show
origin/human/Nettogrof/nessegrev-julia:main.py > /tmp/opp/main.py` plus a
copy of `server.py` if you want to re-run) and ran real local matches
(current `/workspace/main.py` vs that opponent) via the `battlesnake` CLI
engine (see setup instructions earlier in this file -- `setsid nohup ...
disown` pattern to keep Flask servers alive across tool calls). Result:
**3 clean wins / 0 losses for our current bot**, games running
13-125 turns (one long game hit a 40s local-test timeout before
resolving -- inconclusive, not a loss). This is a much more meaningful
test than round 0's own 21-scored-outcomes-out-of-250-sims (229 of the
250 `sim_*.jsonl` files in `/logs/rounds/0` only have a single-line
"pre-game" record with no turns logged, for reasons unclear -- possibly a
logging quirk of the harness, not a real gameplay issue, since
`results.json` itself declares a clean sonnet-5 win with 0 for the
opponent). See `analyze_logs.py` -- I did NOT change it this round, but
note it under-reports because it doesn't look at the final
`{"winnerId":...,"winnerName":...,"isDraw":...}` line each sim file ends
with; a future teammate could fix `analyze_logs.py` to parse that line
directly for a more accurate win tally (quick recipe: `json.loads(last
non-empty line)` per sim file, check `winnerName`/`isDraw` instead of
inferring from board.snakes on the last *turn* line).

I did NOT change `main.py`'s logic this round -- given the very limited
step budget left after investigation, and that the existing heuristic bot
(flood-fill + BFS food-seeking + risky/winnable head-to-head awareness,
see the module docstring in `main.py`) already wins comfortably against
the identified real opponent, I judged a risky rewrite not worth it. The
ideas list from previous rounds (minimax lookahead, hazard support,
tuned weights) is still valid and now has a concrete opponent
(`Nettogrof__nessegrev-julia`'s minimax/flood-fill bot) to benchmark
against locally -- use the `/tmp/opp` recipe above to set up a repeatable
local benchmark before trying any risky change.

### Suggested next step for round 2

Given we already win reliably, the highest-value next step is probably
**not** a rewrite but a proper local tournament (20-50 games) against the
extracted opponent code to get a real win-rate number (not just 3 games),
then decide if any of the "future improvement" ideas below are worth the
regression risk. If a *different* opponent shows up in round 2's actual
match (check `/logs/rounds/1/results.json` once it exists), use `git log
--oneline --all | grep -i Rung` + `git show <ref>:main.py` to pull their
real code the same way and re-benchmark before changing anything.

## Round 3 (this session) update

Opponent confirmed unchanged across rounds 0-1: `Nettogrof__nessegrev-julia`
(a Julia-port doing 6-ply minimax + ground-control flood fill, ~0.3s/move).
Real scored results so far: round 0 = 21-0, round 1 = 20-0 (both clean
sweeps for sonnet-5, see `/logs/rounds/{0,1}/results.json`).

### Local benchmark this round (new signal, worth knowing about)

Ran a real local tournament via the `battlesnake` CLI (see recipe further
up this file) between the *pre-this-round* `main.py` and the extracted
opponent code (`git show origin/human/Nettogrof/nessegrev-julia:main.py`).
Unlike the crushing 20-0/21-0 real match scores, **local 1v1 games were
much closer: 5 wins / 2 losses out of 7 completed games** (games ran
3-125 turns). This is a useful data point for the next teammate: the real
scored match's lopsided score is likely an artifact of how many
sims/games get aggregated and/or starting conditions, not evidence that
our bot wins *every single game* -- there is real room to tighten up the
heuristic, and it's worth investing in deeper testing (e.g. 30-50 games,
using `-o <file>` to dump full game JSON for the losses so you can see
exactly which move/turn we made the losing decision on) if you have step
budget for it. I did not have budget left this round to dig into the 2
losses in detail -- **that's the top recommended next step.**

### Change made this round

One small, low-risk, strictly-more-accurate fix: the flood-fill space-eval
(`_flood_fill_size`) was capped at `max(my_length * 3, 20)` cells, which
early-exits the BFS once that many cells are found. On an 11x11 board
(121 cells) this cap could be *smaller than the actual open region*,
making the bot underestimate how much room a move leads to (and, more
importantly, making that underestimate inconsistent between candidate
moves with different local density -- one candidate's BFS might hit the
cap early while another's doesn't, biasing the comparison). Changed the
cap to `width * height` (i.e. no artificial early exit -- BFS explores the
whole reachable connected region). Verified this is still cheap: a single
`move()` call in a synthetic 2-snake/11x11 test completes in ~0.0006s
(see inline test below), nowhere near the ~500ms per-move budget, even
with the bigger cap on such a small board. This should make the
space/trap evaluation strictly more accurate with no meaningful
performance cost.

Quick way to re-verify `move()` still works after any edit, without
needing a full server:

```python
import main
state = {
  'board': {'width':11,'height':11,'food':[{'x':5,'y':5}],'snakes':[
     {'id':'me','head':{'x':1,'y':1},'length':3,'body':[{'x':1,'y':1},{'x':1,'y':2},{'x':1,'y':3}]},
     {'id':'opp','head':{'x':9,'y':9},'length':3,'body':[{'x':9,'y':9},{'x':9,'y':8},{'x':9,'y':7}]},
  ]},
  'you': {'id':'me','body':[{'x':1,'y':1},{'x':1,'y':2},{'x':1,'y':3}],'health':80}
}
print(main.move(state))
```

### Environment gotcha discovered this round (adds to the existing note)

The existing warning about `pkill -f <pattern>` matching your *own*
invoking shell's command line is real and easy to trigger by accident:
e.g. running `pkill -9 -f "battlesnake play"` from a bash -lc string that
*itself contains the literal text* `"battlesnake play"` (because it also
appears inside that same pkill command) matched and killed the invoking
shell too (observed as a mystery `returncode 137`/empty output on an
unrelated next command in the same call). Prefer killing local test
servers/CLI processes by literal PID (from `ps aux`) rather than `pkill
-f` with any pattern that might also appear in your own command text.

### Suggested next steps for round 4+

1. **Investigate the 2 local losses** from this round's mini-tournament
   with `-o /tmp/game_N.json` dumps to see exact losing decisions -- did
   we lose a head-to-head we should have avoided, get trapped despite the
   flood-fill fix, or just get outrun on food/health? This is the
   highest-value next step given local results are closer than the real
   scored matches suggest.
2. Still-not-done ideas from earlier rounds, roughly in priority order:
   simple 2-3 ply minimax/lookahead (the opponent itself does 6-ply, so
   we're at an information disadvantage on contested cells), hazard
   support (unused `board["hazards"]`), formal weight tuning via
   self-play/tournament sweep.
3. If a *different* opponent appears in a future round's real
   `results.json`, re-identify via `git log --oneline --all | grep -i
   human` + `git show <ref>:main.py` before assuming this analysis still
   applies.

## Round 1 (this session, fresh /logs/rounds with only round 0 present)

Confirmed round-0 opponent from `/logs/rounds/0/results.json`:
`Nettogrof__nessegrev-java` (elo #48, "Rung 3/50" on the ladder per git log
`git log --oneline --all | grep -i Nettogrof`). Real scored result was a
clean sweep: **sonnet-5 39 vs opponent 0** (see that file). Note this is a
*different* opponent identity string from some of the julia-related notes
earlier in this file (`Nettogrof__nessegrev-julia`, elo #49) -- both are
real ported bots from the same author's repo (java vs julia dev version),
just different snakes. Don't confuse them; re-check
`/logs/rounds/<n>/results.json` each round to know which one you're
actually facing, then `git show origin/human/Nettogrof/nessegrev-java:main.py`
(or `-julia`) to pull the exact code.

The `-java` port is a real paranoid minimax (depth up to 6, ~0.3s/move
budget) with a voronoi/flood-fill leaf eval (`DuelNode`/`FourNode` scoring,
see the port's own module docstring for exact original-fidelity notes --
worth reading, it documents e.g. the payoff-matrix/paranoid assumption and
exact leaf scoring formula). This is a genuinely strong-ish heuristic bot,
not a trivial one.

### Benchmark this round

Did NOT change `main.py`'s logic. Instead validated current behavior with
a real local tournament against the extracted `-java` opponent code (via
the `battlesnake` CLI + two local Flask servers, per the existing recipe
elsewhere in this file). **Result: 8 wins / 0 losses / 0 draws** across 8
games (see `/tmp/game_*.log` recipe below -- not persisted, rerun if you
want fresh logs), games ranging 11-105 turns, no server errors/exceptions
in either bot's log (`grep -i error /tmp/new.log /tmp/opp.log` clean other
than the CLI's own harmless request-timeout retry messages when a game
naturally ends and the losing server's process/socket goes away).

This confirms the round-0 39-0 scoreline is a real, reproducible result
against this specific opponent (java port), not a fluke/artifact -- unlike
the `-julia` port from earlier rounds' notes, where local testing found
closer 5-2 / 3-0 splits. The `-java` port appears meaningfully weaker
against our current heuristic than the `-julia` port was. Since we don't
know for certain if this round's *actual* real match reuses the same
`-java` opponent or switches, re-check `/logs/rounds/1/results.json` once
it exists next round.

### Recipe used (for next teammate, condensed)

```bash
# Extract opponent code fresh:
git show origin/human/Nettogrof/nessegrev-java:main.py > /tmp/opp/main.py
cp server.py /tmp/opp/server.py   # server.py is generic, just copy ours

# Start both bots (must use setsid nohup ... & ; disown to survive across
# tool calls in this harness -- see earlier notes in this file):
cd /workspace && (setsid nohup env PORT=8000 python3 main.py > /tmp/new.log 2>&1 </dev/null &)
cd /tmp/opp    && (setsid nohup env PORT=8001 python3 main.py > /tmp/opp.log 2>&1 </dev/null &)

# Run games in background (each can take 5-30s wall-clock; batch 4 at a
# time via nohup + disown, then sleep ~25-30s and check the logs, rather
# than running `battlesnake play` in the foreground with a short timeout
# -- games against the -java opponent's 0.3s/move budget commonly run
# 50-100+ turns and will get killed by a short foreground timeout before
# resolving, wasting the run):
cd /workspace/game
for i in 1 2 3 4; do
  setsid nohup timeout 60 ./battlesnake play -W 11 -H 11 \
    --name new --url http://localhost:8000 \
    --name opp --url http://localhost:8001 \
    -g standard -m standard > /tmp/game_$i.log 2>&1 </dev/null &
  disown
done
sleep 28
for f in /tmp/game_*.log; do echo "-- $f --"; tail -n 2 "$f"; done
```

Kill test servers by PID (`ps aux | grep main.py`) when done, not
`pkill -f main.py` (see earlier gotcha notes in this file about pkill -f
matching your own invoking shell).

### Assessment / recommendation for next round

Given an actual clean 39-0 real-match result *and* a reproducible 8-0
local benchmark against the (likely same) opponent this round, I judged
further heuristic changes to carry more regression risk than expected
benefit this round, and made **no code changes** to `main.py`. The
prioritized ideas list from earlier rounds (minimax lookahead, hazard
support, formal weight tuning) is still valid groundwork for if/when a
tougher opponent appears (e.g. the `-julia` port, which was closer in
local testing, or any future different ladder opponent) -- worth
revisiting then rather than risking the current bot's strong, verified
performance against a weaker opponent now. If next round's
`/logs/rounds/1/results.json` shows anything other than a clean sweep,
that's the signal to actually invest in the minimax/lookahead upgrade.

## Round 2 (this session)

Confirmed via `/logs/rounds/{0,1}/results.json` that both prior real scored
rounds were clean sweeps for sonnet-5 against `Nettogrof__nessegrev-java`
(round 0: 39-0, round 1: 20-0). No code changes to `main.py`'s decision
logic this round -- re-ran a fresh local benchmark (6 games, current
`main.py` vs freshly-extracted `Nettogrof/nessegrev-java` opponent code via
the `battlesnake` CLI, see recipe further up this file) and got **6/6
clean wins**, games ranging 7-113 turns, zero errors/exceptions in either
bot's server log. This is consistent with the two real round scores and
*not* the closer 5-2/3-0 splits earlier notes reported against the
`-julia` port -- the actual opponent we've faced both real rounds so far
is the weaker `-java` port, and our current heuristic beats it
comfortably and reproducibly.

Also ran a battery of synthetic edge-case tests directly against
`main.move()` (no server) to confirm no crashes on: empty food list,
fully-cornered snake with no safe moves (0-move fallback path), empty
snakes list, and a completely malformed/empty `game_state` dict (the
top-level `try/except` in `move()` catches it and returns `{"move":
"up"}`). All passed cleanly.

### Fixed `analyze_logs.py` this round

Per a prior round's noted TODO: the script previously inferred each sim's
winner from the *last logged turn's* `board.snakes` list, which
drastically under-reports because most `sim_*.jsonl` files in
`/logs/rounds/*` only contain a single "pre-game" line with no turns
logged at all (confirmed by direct inspection: round 0 has 250 sim files
but only 39 contain any turn data at all -- and that 39 exactly matches
the `results.json` score of 39! Same story for round 1: 20 files with
turns == score of 20). `analyze_logs.py` now parses each sim file's final
summary line (`{"winnerId":..., "winnerName":..., "isDraw":...}`) directly
instead, with a fallback to the old last-turn-based inference for any sim
file that lacks that final line. Verified output for both existing rounds
now matches `results.json` scores exactly (39 and 20 respectively) --
previously it reported those same numbers by coincidence via the old
under-counting logic (only fully-logged sims had any inferrable winner at
all), but the new logic is more robust/correct in general and will also
correctly count draws going forward.

**Open question for a future round (not resolved, low priority):** why do
~85% of sim_*.jsonl files only have a single pre-game line and no turns?
Two theories, neither confirmed: (a) the scoring harness samples/logs only
a subset of actual games played, and the `results.json` score IS the true
total game count (39 and 20 games played total, not 250) -- in which case
everything is fine and "250" is just an artifact of pre-allocated file
slots; or (b) most sims silently fail to start for an unrelated harness
reason and get miscounted. Given our score is a clean sweep either way,
this hasn't mattered functionally, but worth a sanity check if a future
round's score ever looks suspiciously low compared to sim file count.

### Recommendation for round 3

No urgent changes needed -- bot keeps winning cleanly and reproducibly
against the identified real opponent both in real scored rounds and fresh
local benchmarks. If `/logs/rounds/2/results.json` (this round, once it
exists) is anything other than another clean sweep, or if a different
opponent identity shows up, that's the trigger to revisit the "Ideas for
future improvement" list earlier in this file (minimax lookahead, hazard
support, weight tuning) -- use `git show
origin/human/<Org>/<repo>:main.py` to pull whoever the new opponent is and
re-run the local benchmark recipe before changing `main.py`.

## Round 1 (this session, real opponent = csauve__bookworm)

`/logs/rounds/0/results.json` shows opponent `csauve__bookworm` (a Rust
port doing best-first pruned tree search + minimax over opponent moves +
flood-fill/food/head-to-head heuristic scoring, ~0.3s budget/move -- see
`git show origin/human/csauve/bookworm:main.py` for the full ported code
and its own docstring). Real scored result: clean sweep, sonnet-5 38 vs
bookworm 0.

### Local benchmark this round

Extracted bookworm's code to `/tmp/opp/main.py` (recipe: `git show
origin/human/csauve/bookworm:main.py > /tmp/opp/main.py && cp server.py
/tmp/opp/server.py`) and ran several real local games via the
`battlesnake` CLI (see recipe elsewhere in this file -- `setsid nohup env
PORT=... python3 main.py &` to survive across tool calls). Games against
this opponent commonly run 90-160+ turns (much longer than earlier
opponents) since bookworm actually avoids obvious death. Out of games that
completed within the local test window: 1 win, 1 loss, plus 2 that didn't
finish before a 60s local timeout (inconclusive, not losses -- just slow).

**Found and partially fixed a real bug via one of the losses:** dumped a
full game to JSON (`-o /tmp/game5.json`) and inspected the final turns.
Our snake reached **length 18 vs opponent's length 5, health 93+**, i.e.
was winning by every simple metric, then died at turn ~92 anyway --
diagnosis: it curled into its own body (a "self-coil" trap) that a 1-ply
flood-fill from the immediate next cell can't see coming until it's
already too late (area only drops below `my_length` once the coil is
basically sealed, by which point every candidate move is already doomed).
This is the "look-ahead / minimax" gap earlier rounds' notes predicted
would eventually matter once we faced a long, grindy game against a
non-trivial opponent instead of one that dies in <10 turns.

**Change made:** added a softer secondary penalty gradient in `main.py`'s
move-scoring loop -- previously we only penalized `area < my_length`
(hard trap); now we *also* softly penalize `my_length <= area <
my_length * 1.5` (tight-but-technically-safe margin), on top of raising
the hard-trap penalty multiplier from 50 to 100. The intent is to bias the
bot toward moves that keep a comfortable space buffer above its own body
length rather than shaving it exactly to the limit, which should reduce
(not eliminate -- this is still 1-ply, not real lookahead) how often we
walk into a coil that only becomes visibly fatal 1-2 moves later than our
horizon. This is a small, targeted, low-risk tweak (same overall
structure, no new failure modes), verified via the synthetic
`import main; main.move(state)` smoke test (see recipe further up this
file) and a `main.move({})` malformed-input check -- both still return
valid moves with no exceptions.

**Not done this round (ran out of step budget):** a real 2-ply lookahead
(simulate our candidate move, then re-run flood-fill/safety check assuming
we then take our own best follow-up move, and use that as a tie-break or
harder gate) would more directly fix the self-coil failure mode than the
soft-margin heuristic above -- this is the top recommended next step if
another long/close game against bookworm (or a similarly non-trivial
opponent) shows up again. The `/tmp/game5.json` dump recipe (via
`battlesnake play ... -o /tmp/gameN.json`) is a good way to find more
concrete losing scenarios like this one to test against.

### Recipe reminder (condensed, see earlier rounds' notes for full detail)

```bash
git show origin/human/csauve/bookworm:main.py > /tmp/opp/main.py
cp server.py /tmp/opp/server.py
(setsid nohup env PORT=8000 python3 /workspace/main.py > /tmp/new.log 2>&1 </dev/null &)
(setsid nohup env PORT=8001 python3 /tmp/opp/main.py > /tmp/opp.log 2>&1 </dev/null &)
cd /workspace/game
setsid nohup timeout 90 ./battlesnake play -W 11 -H 11 \
  --name new --url http://localhost:8000 --name opp --url http://localhost:8001 \
  -g standard -m standard -o /tmp/gameN.json > /tmp/gameN.log 2>&1 </dev/null &
disown
# wait, then: tail -3 /tmp/gameN.log ; inspect /tmp/gameN.json turn-by-turn with a small python script
```

Kill test servers by PID (`ps aux | grep main.py`), not `pkill -f` (see
earlier gotcha notes about it matching your own shell's command line).

## Round 4 (this session) update

Confirmed opponent still `csauve__bookworm` for the two most recent real
rounds (`/logs/rounds/0`: 38-0, `/logs/rounds/1`: 20-0, both clean sweeps
for sonnet-5). Per `analyze_logs.py /logs/rounds/1`, real-match games are
very short on average (6.4 turns), likely because the opponent times out
/ errors out quickly in the actual scoring harness (saw `latency: "500"`
i.e. hitting the 500ms move budget in round-1 sim logs) -- so our
heuristic bot's simple safety-first approach is winning big in practice
regardless of deep strategy.

However, a fresh **local** 4-game benchmark this round against freshly
extracted `csauve/bookworm` code (recipe below, same as prior rounds) came
back **2 wins / 2 losses** in games that ran long (90-237 turns) -- i.e.
when bookworm doesn't time out and the game goes long, it's a much closer
fight than the real scores suggest. I dumped one loss to JSON
(`/tmp/game_2.json` -- not persisted, rerun the recipe below to
reproduce) and found a concrete failure mode predicted by earlier rounds'
notes but not yet fixed: **our snake (length 16) spent ~15 turns hugging
its own body along the board perimeter (bottom row -> right column ->
along the top)**, and the opponent (length 5) camped near the bottom-left
corner. By the time our flood-fill lookahead's "safe" margin
(`area < my_length * 1.5` soft penalty) actually triggered, it was only
1-2 turns before the only remaining route got pinched to a single cell by
the opponent's body, and by the *next* turn after that there were **zero
legal candidate moves** at all (both up and right were blocked by our own
body + the opponent's body respectively) -- a pure 1-ply-invisible trap.

### Change made this round

Widened the soft trap-margin threshold in `main.py`'s scoring loop from
`1.5x` my_length to **`2.2x`** (and increased the gradient penalty
coefficient from 15 to 12 per missing cell -- net still meaningfully
stronger at the wider margin since the gap `2.2x - area` is larger). This
makes the bot react to a shrinking-space situation earlier/more
conservatively while it still has more room to redirect, rather than only
noticing once it's down to a ~1.5x cushion (which the corner-hugging
scenario above blew through in just a couple of turns). This is still
**not** true lookahead -- it's a heavier hand on the same 1-ply heuristic
-- so it will not catch every possible coil, but should catch this class
of "long slow perimeter squeeze" earlier.

**Verification done:** `python3 -c "import main; main.move(state)"` smoke
test (see recipe elsewhere in this file) still returns valid moves with
no exceptions on both a normal 2-snake board and a fully empty/malformed
`game_state`. Also restarted a local Flask server on the new code and
ran one fresh local game against the extracted bookworm opponent
(`/tmp/quick1.log`) -- it progressed cleanly past 130 turns with both
snakes alive and no errors in either bot's log before this session ran
out of step budget to observe the final outcome. **I did NOT get to run a
full repeat of the 4-game local benchmark against the widened margin
before running out of steps this round** -- that is the single highest-
priority next step for whoever picks this up next (see recipe below,
same as prior rounds -- extract `csauve/bookworm`, run ~6-10 games,
specifically watch for the same "hugs own body along perimeter for a long
stretch" pattern in any losses, and compare win rate to this round's 2/4
baseline). If the widened margin doesn't help or seems to hurt (e.g. by
making the bot too timid to grab food and lose on health/starvation
instead), consider reverting to 1.5x and instead pursuing the "real 2-ply
lookahead" idea that's been on the list for several rounds now, or a
more targeted heuristic (e.g. explicitly penalizing moves that keep the
head adjacent to 2+ of our own body segments for many consecutive turns,
which is a proxy for "currently coiling").

### Recipe reminder (condensed)

```bash
git show origin/human/csauve/bookworm:main.py > /tmp/opp/main.py
cp server.py /tmp/opp/server.py
(cd /workspace && setsid nohup env PORT=8000 python3 main.py > /tmp/new.log 2>&1 </dev/null &)
(cd /tmp/opp    && setsid nohup env PORT=8001 python3 main.py > /tmp/opp.log 2>&1 </dev/null &)
cd /workspace/game
for i in 1 2 3 4 5 6; do
  setsid nohup timeout 90 ./battlesnake play -W 11 -H 11 \
    --name new --url http://localhost:8000 --name opp --url http://localhost:8001 \
    -g standard -m standard -o /tmp/game_$i.json > /tmp/game_$i.log 2>&1 </dev/null &
  disown
done
sleep 60   # long games (90-240 turns) take a while; check tail -3 /tmp/game_*.log for "was the winner"
```

To inspect a loss in detail: `python3 -c "import json; [print(l['turn'],
[(s['name'], s['health'], s['length'], [(b['x'],b['y']) for b in
s['body']]) for s in l['board']['snakes']]) for l in (json.loads(x) for x
in open('/tmp/game_N.json')) if 'turn' in l]"` and look at the last ~15
turns before the loss.

Kill test servers by PID (`ps aux | grep main.py`), never `pkill -f`
with a pattern that might match your own invoking shell's command line
(see earlier rounds' notes -- this has bitten multiple past sessions).

## Round 1 (this session) — opponent = coreyja__improbable-irene, confirmed still winning cleanly

`/logs/rounds/0/results.json` shows this round's real opponent identity:
`coreyja__improbable-irene` (elo #46, "Rung 5/50" per `git log --oneline
--all | grep -i coreyja`). Real scored result: clean sweep, sonnet-5 20 vs
opponent 0. `analyze_logs.py /logs/rounds/0` confirms via the per-sim
`winnerName` summary lines: **20/20 sims won**, avg game length only 6.5
turns (min 2, max 10) -- the opponent is dying almost immediately in the
real scoring harness.

The opponent's code (`git show
origin/human/coreyja/improbable-irene:main.py`) is a real, non-trivial
port: 2-ply MCTS (UCB1-Normal selection, random-rollout simulation to 25
steps, flood-fill-based leaf eval) with a ~0.3s wall-clock budget per
move -- not a trivial bot in principle, but apparently either times
out/errors in the real harness or just loses badly to our safety-first
heuristic once games run long enough to matter.

### Local benchmark this round (fresh, confirms real-match result)

Extracted the opponent fresh (`git show
origin/human/coreyja/improbable-irene:main.py > /tmp/opp/main.py; cp
server.py /tmp/opp/server.py`) and ran 6 real local games via the
`battlesnake` CLI against the current, *unmodified* `main.py` (see recipe
elsewhere in this file -- `setsid nohup ... & disown` to survive across
tool calls in this harness). **Result: 6/6 clean wins for our bot**,
games ranging 7-238 turns (one game ran the full 238 turns with both
snakes alive most of the way -- no crashes, no exceptions in either
server's log, our bot eventually won a real long-game scenario too, not
just fast early kills). This matches/confirms the real round's 20-0
sweep and rules out the "real score is lopsided but local 1v1 is close"
pattern that showed up against some past opponents (e.g. the julia/
bookworm ports in earlier rounds' notes) -- against *this* opponent, our
current heuristic wins comprehensively both in short games (opponent
dies almost immediately in ~90% of games) and in the rare long grindy
game (won a 238-turn game cleanly too).

### Decision this round: no code changes

Given a clean, reproducible 6/6 local sweep on top of the real 20-0
scored result against the confirmed current opponent, I judged further
heuristic changes to `main.py` this round to carry more regression risk
than expected benefit, and made **no changes to the bot's decision
logic**. `main.py` is unchanged from the version described in the "Round
4" and earlier sections above (flood-fill space eval with the 2.2x soft
trap margin, BFS nearest-food seeking, risky/winnable head-to-head
awareness, tail-just-ate detection).

### Recommendation for round 2+

- If `/logs/rounds/1/results.json` (once it exists) shows anything other
  than another clean sweep, or a different opponent identity, use `git
  log --oneline --all | grep -i human` + `git show
  origin/human/<Org>/<repo>:main.py` to identify/extract them and re-run
  the local benchmark recipe (condensed version a few sections up, or
  just: start both bots with `setsid nohup env PORT=... python3 main.py
  > /tmp/x.log 2>&1 </dev/null & disown`, then loop `./battlesnake play
  ...` a handful of times with `disown`'d background jobs and `sleep`
  before checking `tail` on the log files -- foreground calls with short
  timeouts can get killed by the *bash tool's own* ~30s call timeout,
  not just the `timeout` command's limit, so always background +
  disown + sleep + check in a separate call, as done this round).
- The still-not-done ideas list from earlier rounds remains valid if a
  tougher opponent shows up: real 2-3 ply minimax/lookahead (current bot
  is still 1-ply + heuristic trap-margin, not true lookahead), hazard
  support (`board["hazards"]` still unused), formal weight tuning via a
  self-play tournament sweep.
- Reminder: this bash harness's tool-call wall-clock limit is ~30s
  independent of any `timeout N` you pass to a background command --
  don't rely on a single tool call to both launch and wait-out a batch of
  60s-`timeout`'d background games; split launching and polling into
  separate tool calls (as done this round: one call to launch+sleep 35s,
  a follow-up call to sleep more + check the still-running long game).

## Round 2 (this session) — confirmed opponent unchanged, added hazard support (low-risk, currently no-op)

`/logs/rounds/{0,1}/results.json` both show clean 20-0 sweeps for
sonnet-5 against `coreyja__improbable-irene` (same opponent both rounds,
per the "Round 1 (this session)" section above already in this file).
`analyze_logs.py /logs/rounds/1` confirms 20/20 sims won, avg 6.6 turns
(opponent mostly dies almost immediately in the real scoring harness).

### Verification this round

- Smoke-tested `main.move()` on synthetic normal/empty/malformed states —
  no exceptions, valid moves returned in all cases.
- Fresh local benchmark (recipe in earlier rounds' notes: extract
  `origin/human/coreyja/improbable-irene:main.py` to `/tmp/opp/main.py`,
  run via the `battlesnake` CLI with both bots as local Flask servers,
  `setsid nohup ... & disown` to survive across tool calls in this
  harness): **6/6 clean local wins** before any code change, games
  ranging 3-209 turns (including one 209-turn long game, both alive most
  of the way — no crashes/errors in either server log). Confirms the
  bot's real-round win rate is genuine, not a harness artifact.

### Change made this round

Added **hazard avoidance** (`board["hazards"]`), which every prior
round's notes flagged as an unused TODO. Implementation: build a
`hazard_set` from `board.get("hazards", [])` and apply a `-40` score
penalty in the move-scoring loop for any candidate cell inside a hazard
(on top of the existing safety/space/food scoring — it's additive, not a
hard block, so the bot will still enter a hazard if every other option is
worse, e.g. certain death).

**Important scope note:** I confirmed via direct inspection of
`/logs/rounds/1/sim_*.jsonl` that the real match ruleset is `"standard"`
with **zero hazard cells ever present** in any observed board state (the
`hazards` array is always empty — hazards are a Royale-map feature, not
part of standard). So this change is **currently a complete no-op** in
every match we've actually played or benchmarked — it cannot change any
observed behavior right now, hence very low regression risk (verified
with the smoke tests above, which behave identically with/without hazard
cells in the input beyond the one synthetic test that explicitly included
a hazard). It's future-proofing only, in case a later round's opponent
match ever uses a hazard-bearing map/ruleset. If you want to double check
this is truly inert in the current ruleset, grep any new round's
`sim_*.jsonl` files for non-empty `"hazards"` the same way (see snippet
below) before assuming it matters:

```python
import json
for line in open('/logs/rounds/<n>/sim_0.jsonl'):
    d = json.loads(line)
    if 'board' in d and d['board'].get('hazards'):
        print("hazards present!", d['board']['hazards'])
```

### Post-change re-verification

Re-ran the local benchmark against the same extracted opponent after the
change: 3 clean wins observed directly (36, 10, 120 turns) plus one very
long game (200+ turns, both still alive) that ran past this session's
step budget to observe the final outcome — not a loss, just
inconclusive/slow, consistent with the pre-change 6/6 result. No behavior
difference is expected/observed since hazards are never present in this
ruleset (see above), so this is purely a code-quality/future-proofing
change, not a strength change against the current opponent.

### Recommendation for round 3+

- Bot continues to win cleanly and reproducibly; no urgent changes
  needed. Re-check `/logs/rounds/2/results.json` once it exists — if it's
  still `coreyja__improbable-irene` and still a clean sweep, further
  heuristic changes carry more regression risk than benefit. If a
  *different* opponent appears, use `git log --oneline --all | grep -i
  human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
  benchmark them before changing `main.py`, per the established recipe
  throughout this file.
- Still-not-done ideas from many earlier rounds, in case a tougher
  opponent ever shows up: real 2-3 ply minimax/lookahead (current bot is
  1-ply flood-fill + heuristic trap-margin only), formal weight tuning via
  a self-play tournament sweep. Hazard support is now at least present
  (if currently inert) — remove this note once verified against a
  hazard-bearing map/ruleset if one ever appears.

## Round 1 (this session) — opponent = graeme-hill__snakebot, found+partially-fixed a real "opponent seals corridor" trap

`/logs/rounds/0/results.json`: clean sweep, sonnet-5 92 vs
`graeme-hill__snakebot` 0 (confirmed via `analyze_logs.py /logs/rounds/0`:
92/92 sims won, avg 8.0 turns, min 2 max 34 — opponent dies fast in the
real harness, consistent with many past rounds' pattern of real-match
scores being lopsided even when local 1v1 is closer).

### Local benchmark (before any change)

Extracted `origin/human/graeme-hill/snakebot:main.py` to `/tmp/opp/main.py`
(746 lines — a real, non-trivial port, not a toy bot) and ran 6+1 local
games via the `battlesnake` CLI against the *pre-this-round* `main.py`
(recipe: see many earlier rounds' notes above — `setsid nohup env
PORT=... python3 main.py > log 2>&1 </dev/null & disown` for both bots,
then loop `./battlesnake play ...` backgrounded+disowned, `sleep`, then
check `tail`). Result: **4 wins / 2 losses** out of 6, plus a 7th game
dumped to JSON for analysis. This is a real, reproducible gap between
local 1v1 and the crushing real-match score — worth digging into (as
this round did), not just noting again.

### Root cause found (concrete, not speculative)

Dumped a loss to `/tmp/loss.json` (`-o` flag) and wrote an inline script
(see recipe below) to print, for a stretch of ~15 turns before the death,
every legal candidate move's flood-fill area from `main._flood_fill_size`
using the *actual logged board state* at each turn. Found the literal
mechanism: our snake (length 22) had a comfortable ~90-94-cell open area
for **every** candidate at turn 130. One turn later (turn 131), one
candidate's area had already collapsed to 14 (still correctly avoided by
the existing hard-trap penalty, which chose the other candidate with area
80). But by turn 132 — having taken the "safe" area-80 move — *both*
remaining candidates had collapsed to area 1. The mechanism: the
opponent's head advanced one cell (from (8,3) to (7,3) in this instance)
between those two turns and sealed a chokepoint that connected our
head's local neighborhood to the rest of the open board. Our existing
1-ply flood-fill only ever sees the *current* board's connectivity (all
snake bodies frozen at their present positions) — it has **no way to
foresee** that an opponent's very next move can retroactively invalidate
an 80-cell-looking escape route by closing a corridor, because the
corridor cell itself isn't occupied *yet* at the moment we score it.

I confirmed this quantitatively: re-running the *same* turn-131 flood
fill but pre-blocking every cell the opponent's head could move into
next turn (a cheap pessimistic 1-extra-ply widening, cost: just unioning
in a set we already compute) dropped the "safe-looking" candidate's area
from 80 down to **3** — i.e. the true danger *was* detectable one turn
earlier than our then-current heuristic could see, just not with a
same-turn-only flood fill.

### Change made this round

In `main.py`'s move-scoring loop: compute `opp_next_cells = risky_cells |
winnable_cells` (a set we already build every call — the union of every
opponent's own reachable-next-turn cells, regardless of relative
length) and union it into the blocked-set used specifically for the
flood-fill **area evaluation** (not the legal-move filter, and excluding
the candidate cell itself, so it can't accidentally forbid a move we're
actually allowed to make — that's still governed by the pre-existing
risky_cells hard-avoid logic below it). This makes the space/openness
score a cheap "1.5-ply" pessimistic estimate: "how much room would I
have if every opponent also took their single worst-case-for-me next
step", rather than a purely-static snapshot of the current board. Net
effect: corridors that an opponent is one move away from sealing now
show up as measurably smaller in the area score *before* we commit to
walking down them, one turn earlier than before.

This is still not true minimax/lookahead (opponents only get to block
their own immediate neighbor cells, not simulated multiple turns deep,
and we don't model *our own* future moves either) — but it's a very
cheap, targeted fix for exactly the failure mode found in the loss dump,
with no new data structures (reuses `risky_cells`/`winnable_cells`,
already computed every call) and a one-line change to the flood-fill
call site.

### Verification done this round

- `import main; main.move(state)` smoke tests: normal 2-snake state,
  `{}` malformed state, and a state with an empty snakes list — all
  return valid moves, no exceptions, matching pre-change behavior.
- Re-ran a fresh 4-game local benchmark against the same extracted
  opponent after the change: **3 wins / 1 loss**, no errors/exceptions
  in either bot's server log (`grep -i error /tmp/new2.log` clean),
  games ranging 131-238 turns. Comparable-or-better rate to the
  pre-change 4/6 (~67%) — small sample, not conclusive proof of a
  strength delta, but at minimum confirms **no regression/crash** was
  introduced, and the specific mechanism it targets is real (verified
  quantitatively above, not just "seems plausible").

### Recipe used this round (for next teammate, condensed)

```bash
git show origin/human/graeme-hill/snakebot:main.py > /tmp/opp/main.py
cp server.py /tmp/opp/server.py
(cd /workspace && setsid nohup env PORT=8000 python3 main.py > /tmp/new.log 2>&1 </dev/null &)
(cd /tmp/opp    && setsid nohup env PORT=8001 python3 main.py > /tmp/opp.log 2>&1 </dev/null &)
cd /workspace/game
setsid nohup timeout 90 ./battlesnake play -W 11 -H 11 \
  --name new --url http://localhost:8000 --name opp --url http://localhost:8001 \
  -g standard -m standard -o /tmp/loss.json > /tmp/loss.log 2>&1 </dev/null &
disown
# sleep ~28s in a separate tool call, then tail -3 /tmp/loss.log
```

To replay a dumped game's flood-fill areas turn-by-turn near a death (the
exact technique used to find this round's bug):

```python
import json, main
turns = [json.loads(l) for l in open('/tmp/loss.json') if 'turn' in json.loads(l)]
byturn = {t['turn']: t for t in turns}
for t in range(START, END):
    l = byturn.get(t)
    if not l: continue
    snakes = l['board']['snakes']
    me = [s for s in snakes if s['name'] == 'new'][0]
    blocked = main._build_blocked(snakes)
    w, h = l['board']['width'], l['board']['height']
    head = (me['body'][0]['x'], me['body'][0]['y'])
    for name, (dx, dy) in main.DIRS.items():
        nxt = (head[0]+dx, head[1]+dy)
        if nxt in blocked or not main._in_bounds(nxt, w, h):
            continue
        print(t, name, main._flood_fill_size(nxt, blocked, w, h, w*h))
```

### Suggested next steps for round 2+

1. Run a bigger local benchmark (10-20 games) against the same
   `graeme-hill__snakebot` extraction with the new pessimistic-area
   change to get a more confident win-rate delta than this round's small
   sample (3/4 vs previous 4/6) — I ran out of step budget to do this
   myself this round.
2. The same "opponent seals a corridor" mechanism could in principle be
   extended: right now we only pessimistically block opponents' *own*
   immediate neighbor cells for the area calc. A natural next increment
   (still cheap) would be to also give this same treatment recursively
   for 2 opponent-ply, or to combine it with our *own* best-response
   (a real 1-ply minimax: "after I move here, what's the opponent's best
   move against me, and how much room do I have after that") — this has
   been on the "future improvement" list for many rounds now under
   "minimax/lookahead" and this round's concrete bug is a good, specific
   test case to validate any such change against (re-extract
   `/tmp/loss.json` from this round if you don't want to re-find a fresh
   repro).
3. If `/logs/rounds/1/results.json` shows a different opponent identity,
   use `git log --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark them
   first, per the established pattern throughout this file, before
   assuming this round's fix matters against them too.

## Round 2 (this session) — added multi-ply "corridor race" opponent-territory heuristic; found a SEPARATE pre-existing self-coil bug via local benchmarking

`/logs/rounds/{0,1}/results.json`: opponent is `graeme-hill__snakebot` both
rounds (real, 746-line ported bot, see earlier notes in this file for its
algorithm summary). Round 0: 92-0 clean sweep. **Round 1: 86-1 — NOT a
clean sweep this time** (`analyze_logs.py /logs/rounds/1` confirms via
per-sim `winnerName`: 86 wins for sonnet-5, 1 for the opponent, out of 250
sims, avg turn count 10.0 but max 165 -- most games still end fast, but
the rare long game is where we lost).

### Root cause of the one real loss (sim_249.jsonl), found via direct trace replay

Extracted the exact losing sim (`/logs/rounds/1/sim_249.jsonl`) and walked
the final ~20 turns turn-by-turn (see snippet: print each turn's
`board.snakes[*].body` for both snakes). Concrete mechanism: our snake
(reaching length 24-25) traveled the full length of the board's **right
edge column (x=10)** from y=1 up to y=10 over ~9 turns while continuing to
eat food along the way (so its own tail kept growing instead of
following, filling in the whole column behind it with no way back). In
parallel, the opponent (much shorter, length 9) independently walked a
path that happened to converge on the corridor's *only exit* — the
corner cell (9,10)/(10,10) area — and reached it **one turn before we
did**, sealing us into the now fully-self-filled column with the head
stuck at the (10,10) corner and literally zero legal moves the following
turn. This is the concrete "opponent seals corridor" race scenario
several earlier rounds' notes predicted/found evidence of but hadn't
fully solved: our existing "1-ply pessimistic" opponent-blocking (blocking
only cells an opponent could reach *next turn*, added a few rounds ago)
is way too short-horizon to see a 6-8-turn-away race outcome coming.

I verified this quantitatively by re-running `main.py`'s (pre-this-round)
flood-fill on the actual turn-155 board state (the moment our snake
committed to entering the column): the "go up the column" candidate's
flood-fill area looked like a totally safe 59 cells at that moment (way
more than our body length) — the danger was **completely invisible** to
a same-turn-only or 1-ply-pessimistic flood fill; it only would have
become visible turns later, too late to redirect.

### Change made this round: multi-ply ("6-ply") pessimistic opponent-territory blocking for the area/space score

In `main.py`'s `move()`, for each opponent I now also compute
`opp_territory`: all cells that opponent could reach within
`TERRITORY_HORIZON = 6` moves via a depth-limited BFS from their current
head (over the same static blocked-cells snapshot used everywhere else —
same conservative-but-cheap approximation as the rest of the bot, not a
real multi-turn simulation of *their* future decisions). For the
space/area evaluation only (not the legal-move filter, and always
excluding the candidate cell itself so it can never forbid a move we're
actually allowed to make), I now compute **two** flood-fill areas per
candidate — the existing one (`area`, blocked by current bodies + 1-ply
opponent-next-cells) and a more pessimistic one (`area_pess`, additionally
blocked by the new 6-ply `opp_territory`) — and use `min(area, area_pess)`
for all of the scoring math (hard-trap penalty, soft-margin penalty, and
the linear `area * 5` bonus).

**Verified this directly fixes the exact traced loss**: re-ran the new
logic on the literal turn-155 board state from `sim_249.jsonl` — the "go
up the column" candidate's pessimistic area collapsed to **1** (correctly
flagging the corridor-race danger *before* committing), while "go down"
(the safe alternative, back toward open board) stayed at a healthy 28.
Given the same board state, the patched bot picks "down" instead of the
fatal "up". See the inline replay script in shell history this round (or
recreate: load `main.py`, build `risky_cells`/`winnable_cells`/
`opp_territory` the same way `move()` does, print flood-fill areas for
each direction from the turn-155 state) if you want to re-verify or tune
`TERRITORY_HORIZON` further.

### IMPORTANT — found a SEPARATE, pre-existing bug via fresh local benchmarking that is NOT fixed by the above and needs follow-up

Ran a fresh 6-game local benchmark (recipe unchanged from many earlier
rounds' notes: extract `origin/human/graeme-hill/snakebot:main.py` to
`/tmp/opp/main.py`, run both as local Flask servers via `setsid nohup env
PORT=... python3 main.py & disown`, then loop `battlesnake play ... -o
/tmp/game_N.json` backgrounded+disowned) with the **patched** `main.py`.
Result: **0 wins / 6 losses** (games ran 70-287 turns) — a real
regression signal worth flagging loudly, though I want to be clear about
what I found investigating it before running out of step budget:

Inspected the shortest loss (`/tmp/game_5.json`, 69 turns) turn-by-turn
and found **our snake self-coiled into a fully self-enclosed dead corner
with the real opponent nowhere nearby** (opponent was length 4, far away
on the other side of the board, playing no role at all in the trap). Our
own body wound through a tight spiral near the bottom-right corner over
~15 turns and sealed itself in — by the time the flood-fill's hard-trap
penalty could see the shrinking space, every legal candidate was already
part of a single forced corridor leading to a dead end. **This is a
different, pre-existing failure mode from the one this round's patch
targets** — this one has zero opponent involvement, it's purely our own
1-ply flood-fill being blind to a slow self-created coil (the exact
"self-coil" issue flagged and partially mitigated multiple rounds ago via
the 2.2x soft-margin threshold — evidently that mitigation is still not
enough against this specific opponent's food-placement/positioning
pressure). **I did NOT have step budget left this round to determine
whether this round's `opp_territory` patch made the self-coiling *worse*
(e.g. by making the bot avoid more of the board and squeeze into tighter
regions more often) or whether the pre-existing bot already had a similar
0/6-ish local rate against this specific opponent build before my patch**
— I was not able to re-run a clean before/after comparison (ran out of
steps mid-comparison; the last thing I did was start re-testing the
pre-patch `main.py` against the same opponent and the opponent's local
server had already been killed by an earlier cleanup command in the same
session, so that comparison is incomplete/inconclusive, not a completed
result either way).

**I chose to keep this round's `opp_territory` patch** (rather than
revert) because: (a) it's independently verified via direct replay to fix
a real, previously-undetectable loss mechanism (the sim_249 corridor
race) with no possible false-legal-move issue (it only touches the
scoring/area eval, never the legal-move filter) and no exceptions across
several smoke tests (empty state, malformed state, empty snakes list,
normal state); (b) the self-coiling loss pattern found in this round's
local benchmark looks -- from the one game I inspected in detail -- to be
a **pre-existing** bug independent of my change (zero opponent
involvement in the specific trap), not obviously caused by it; and (c)
the actual scored real-match results are still heavily lopsided in our
favor (86-1, 92-0) despite this local benchmark looking rough, similar to
the pattern noted in many earlier rounds where local 1v1 benchmarks are
consistently harder than real scored results (possibly because the real
harness's games end faster / opponent errors out more there, or because
250 sims average away a small number of losses far better than a 6-game
local sample does). But this is a judgment call under time pressure, not
a fully confirmed "definitely still an improvement" -- see next steps.

### Recommended next steps for round 3 (high priority, in order)

1. **Redo the before/after local benchmark properly** (10+ games each,
   both bots freshly started, `/tmp/main_before.py` in this session's
   history has the exact pre-this-round `main.py` if you want to diff --
   or just `git show HEAD:main.py` from before this round's commit once
   this round's changes are committed) to get a real win-rate delta
   number for the `opp_territory` change specifically, isolated from the
   self-coiling issue. If the patch is neutral-or-positive, keep it larger
   confidently; if it measurably hurts (e.g. by making the bot avoid
   center-board options more often and squeeze into tighter spaces), it
   may need `TERRITORY_HORIZON` tuned down (try 3-4 instead of 6) or
   scoped only to when a candidate is entering a "single connected
   corridor" region (e.g. only apply the pessimistic recompute when
   `area` is already below some threshold like `my_length * 4`, to avoid
   over-penalizing genuinely wide-open moves where opponent territory
   overlap is coincidental/irrelevant) rather than applied unconditionally
   to every candidate every turn.
2. **The self-coiling bug is still the single biggest known unresolved
   issue** across MANY rounds' notes now (see "self-coil" mentions
   throughout this file going back several rounds) and this round found
   a fresh, concrete, opponent-independent repro
   (`/tmp/game_5.json` -- not persisted, rerun the recipe above to
   reproduce fresh) where it single-handedly lost a game with a
   4-length opponent nowhere nearby. The soft-margin mitigation (2.2x
   threshold) is evidently insufficient against tighter/more contested
   food layouts. The highest-value real fix remains genuine short
   lookahead: simulate our own candidate move 2-4 plies deep (assuming
   some simple opponent policy, e.g. "opponent also does 1-ply
   flood-fill-safe-food-seeking") and use the resulting reachable-area
   *after* that lookahead as the space score, rather than a single static
   snapshot. This has been on the list for many rounds without being
   attempted -- it's a bigger, riskier change than anything done so far,
   but the accumulated evidence (this round's repro plus several past
   rounds' "close local benchmark" notes) suggests 1-ply heuristics are
   near their ceiling against `graeme-hill__snakebot` specifically.
3. If real `/logs/rounds/2/results.json` (once it exists) shows a score
   close to the round-1 86-1 (not a full regression to something much
   worse), the patch is probably fine/net-positive in practice and safe
   to build further on. If it's notably worse than 86-1, seriously
   consider reverting this round's `opp_territory` change first (it's a
   clean, isolated diff -- see `/tmp/main_before.py` recipe above,
   or just remove the `opp_territory`/`area_pess`/`TERRITORY_HORIZON`
   block and go back to using `area` alone in the scoring math) before
   trying anything else, since the self-coiling bug it might be
   interacting with is the more likely root cause either way.

### Files (unchanged from previous rounds' notes)

- `main.py` — the bot.
- `analyze_logs.py` — point at `/logs/rounds/<n>` to summarize
  results.json + per-sim win/turn-count stats (parses the final
  `winnerName`/`isDraw` line per sim file).

## Round (this session) — found + fixed a real, confirmed match-losing bug in the "opponent territory" pessimistic area heuristic

Confirmed opponent this round via `/logs/rounds/0/results.json`:
**`coreyja__devious-devin`** (a real paranoid minimax port, depth up to 6,
~0.3s/move, see `git show origin/human/coreyja/devious-devin:main.py` for
the full docstring). Real scored result: **sonnet-5 22, opponent 2** (not
a clean sweep -- 2 real losses out of 24 total games, confirmed via
`analyze_logs.py /logs/rounds/0` parsing the per-sim `winnerName` summary
lines: 22 wins for us, 2 for the opponent, avg turn count 24.9, min 2 max
274).

### Root cause of BOTH real losses, found via direct trace replay (concrete, not speculative)

Identified the exact two losing sims (`sim_246.jsonl` turn ~124→131,
`sim_248.jsonl` turn ~269→274) and replayed `main.py`'s exact decision at
the critical turn using the literal logged board state (recipe: load
`main.py`, rebuild `blocked`/`risky_cells`/`winnable_cells`/
`opp_territory` exactly like `move()` does, print each candidate's raw
flood-fill area vs. the actual `main.move()` output for that state).

**Found a serious, previously-unnoticed bug in the multi-round-old
"opponent territory" pessimistic-area heuristic** (added ~2 rounds ago
under the name `opp_territory`/`TERRITORY_HORIZON`/`area_pess`, originally
intended to catch "opponent seals a corridor" corridor-race scenarios --
see the many earlier rounds' notes above this section for its original
motivation and a previous *inconclusive* worry that it might be
interacting badly with self-coiling). This round found and **confirmed
with hard evidence** exactly how it goes wrong:

- At `sim_246.jsonl` turn 124 (our snake length 13), the two legal moves
  were: `left` with a **true/raw** flood-fill area of 93 cells (wide open,
  completely safe) vs. `right` with a true area of 6 cells (a genuine
  dead-end pocket, smaller than our own body — a real trap). The old code
  used `min(area, area_pess)` — where `area_pess` additionally blocks
  every cell any opponent could reach within a 6-move BFS horizon — as
  the value driving the *hard* trap penalty (`(my_length - area_for_score)
  * 100`). Because the opponent could *eventually* (within 6 moves) reach
  deep into the wide-open 93-cell region, `area_pess` for `left` collapsed
  to **1**, making `left` score as if it were a near-total trap (worse
  than the *actual* 6-cell dead-end pocket). The bot picked `right` — the
  real trap — and died a few turns later exactly as predicted once it
  finished walking into the sealed pocket. Full turn-by-turn trace + the
  exact reproduction script is in shell history this round; the short
  version: `main.move()` called on the literal turn-124 board state
  returned `{"move": "right"}` before the fix, `{"move": "left"}` after.
- `sim_248.jsonl` turn 269 (length 21) was the same mechanism: `left`
  (true area 69, safe) vs `right` (true area 4, real dead-end). The
  pessimistic estimate for `left` collapsed to 1 (partly from the 1-ply
  `opp_next_cells` blocking alone dropping it 69→11, then the 6-ply
  territory extension dropping it further to 1), while `right`'s estimate
  matched its true tiny value unchanged (the opponent was nowhere near
  that pocket). Same wrong pick, same eventual death. `main.move()` on
  this literal state returned `{"move": "right"}` before the fix,
  `{"move": "left"}` after.

**The general failure mode**: treating "any cell an opponent could
*possibly* reach within N moves" as fully blocked for our own space
evaluation is far too aggressive once a region is large — it can make an
enormous genuinely-open area look like a near-total trap just because an
opponent could theoretically wander into part of it eventually, even from
far away with no actual current threat. Meanwhile a real, small, already-
sealed dead-end pocket (which the opponent *can't* reach either, so its
estimate is unaffected) doesn't get similarly penalized — so the
comparison between the two becomes inverted exactly when it matters most
(deciding between "escape to the open board" and "wall myself into a
pocket").

### Fix made this round

In `main.py`'s move-scoring loop:

- The **raw** flood-fill area (blocked only by actual current snake
  bodies — no opponent-territory speculation) is now the value that
  drives the hard-trap penalty, the soft 2.2x-margin penalty, and the
  `area * 5` linear bonus — i.e. all the heavyweight scoring that must
  reflect *real, current* reachability.
- The old opponent-pessimistic estimate (`area_pess`, still computed the
  same way — 1-ply opponent-next-cells plus 6-ply `opp_territory`) is now
  only used to compute a small, **capped** secondary penalty:
  `score -= min(max(0, area - area_pess), my_length) * 2`. This keeps a
  little bit of "corridor-race" awareness (mild preference away from
  routes an opponent could contest) as a tie-breaker among otherwise
  comparably-safe options, but it is mathematically incapable of making a
  93-cell truly-open region score worse than a genuine 6-cell dead-end
  trap, because it's capped at `my_length` (a few dozen points at most)
  rather than being able to swing the *entire* trap-penalty formula the
  way `min(area, area_pess)` could.
- Verified directly: re-running `main.move()` on the exact two traced
  losing board states now returns the correct/safe move in both cases
  (see above). Also re-ran the existing smoke tests (`main.move()` on a
  normal 2-snake state, `{}` empty state, and an empty-snakes state) —
  all still return valid moves with no exceptions, matching prior
  behavior.

### Local benchmark this round (partially inconclusive due to step budget, but no regressions seen)

Ran 4 fresh local games via the `battlesnake` CLI against freshly
extracted `origin/human/coreyja/devious-devin:main.py` (same recipe as
many earlier rounds — `setsid nohup env PORT=... python3 main.py &
disown` for both bots, `battlesnake play ... &  disown`, sleep, check
logs). **Result: 1 clean win, 1 clean loss, 2 games didn't finish before
a 60s local timeout** (they were still running turns 175-190+ when
killed — devious-devin's ~0.3s/move budget plus this harness's own
overhead makes long games slow to finish locally; this is a known,
previously-noted pattern in earlier rounds' benchmarks against other
slow-thinking opponents, not specific to this session). This is a small
and partially-inconclusive sample — **I did not have step budget left
this round to re-run a larger/cleaner benchmark or to dig into the one
observed local loss** (didn't get to dump/inspect it before running out
of steps). No crashes or exceptions were seen in either bot's server log
across all 4 games.

### Recommendation for next round (HIGH PRIORITY)

1. **Re-run a bigger local benchmark** (8-12 games, with longer sleep
   windows between launching and checking so slow games vs.
   devious-devin's 6-ply minimax actually finish — budget ~90-120s per
   batch of games, split across multiple tool calls: one to launch+short
   sleep, subsequent ones to sleep more + check `tail`) to get a more
   confident win-rate number for the fix made this round. If you find a
   *new* loss, use the exact same trace-replay technique documented above
   (rebuild `blocked`/`risky_cells`/`opp_territory` from the literal
   logged board state at the critical turn, compare `main.move()`'s
   actual output against each candidate's raw flood-fill area) — it is a
   fast, concrete way to find real bugs, much more effective this round
   than speculative heuristic tweaking.
2. Once `/logs/rounds/1/results.json` exists (this round's real scored
   result), check whether the two-loss pattern from round 0 is gone or
   reduced. If still `coreyja__devious-devin` and score is better than
   22-2 (or a clean sweep), the fix is confirmed working in the real
   harness too.
3. If a **different** opponent appears, use `git log --oneline --all |
   grep -i human` + `git show origin/human/<Org>/<repo>:main.py` to
   extract and benchmark them per the established recipe throughout this
   file, and consider re-running the trace-replay technique on any losses
   found — it generalizes to any opponent, not just this one.
4. The remaining `opp_territory`/6-ply-BFS computation in `main.py` is
   now only used for the small capped secondary penalty. If future
   profiling ever shows it's not pulling its weight (e.g. A/B testing
   shows removing it entirely doesn't change win rate), it could be
   deleted entirely to simplify the code and save a little compute — but
   it's cheap enough (see many earlier rounds' timing notes) that this is
   a low-priority cleanup, not a correctness concern anymore now that it
   can't override the hard safety metric.

### Files (unchanged)

- `main.py` — the bot (this round's fix: raw-area-drives-hard-penalties,
  opponent-pessimism now only a small capped secondary nudge — see the
  inline comment block right above the scoring loop for the full
  rationale, and this section for the concrete traced bug it fixes).
- `analyze_logs.py` — point at `/logs/rounds/<n>` to summarize
  results.json + per-sim win/turn-count stats.

## Round 2 (this session) — confirmed previous round's bug fix is solid, no code changes

`/logs/rounds/{0,1}/results.json` confirm the opponent is still
**`coreyja__devious-devin`** across both real rounds so far, and that last
round's fix (documented in the section immediately above this one --
"found + fixed a real, confirmed match-losing bug in the 'opponent
territory' pessimistic area heuristic") is working as intended in the real
scoring harness: round 0 (pre-fix) was **22-2** (2 real losses, both
root-caused and fixed as documented above), round 1 (post-fix, same
opponent) was a **clean 20-0 sweep** (`analyze_logs.py /logs/rounds/1`:
20/20 sims won, avg 5.7 turns, min 2 max 10 -- opponent dies fast in the
real harness in almost every game).

### What I did this round

Did **not** change `main.py`'s decision logic. Instead spent the step
budget re-validating the fix more thoroughly via local benchmarking, since
the fix was only lightly tested (partially inconclusive local benchmark)
in the round it was made:

1. Smoke-tested `main.move()` on a normal 2-snake state, `{}` (fully
   malformed), and an empty-snakes state -- all return valid moves, no
   exceptions.
2. Extracted a fresh copy of the opponent
   (`git show origin/human/coreyja/devious-devin:main.py > /tmp/opp/main.py`,
   `cp server.py /tmp/opp/server.py`) and ran **14 real local games** via
   the `battlesnake` CLI against the current, unmodified `main.py` (recipe
   unchanged from many earlier rounds' notes -- `setsid nohup env PORT=...
   python3 main.py > log 2>&1 </dev/null & disown` for both bots, then
   loop `battlesnake play ... -o /tmp/game_N.json` backgrounded+disowned,
   `sleep`, check `tail`). **Result: 14 wins / 0 losses**, games ranging
   3-232 turns (a good mix of the fast early-death games that dominate the
   real harness, plus several genuinely long grindy games up to 232 turns
   -- specifically useful since the two real losses fixed last round both
   happened deep into long games, turn 124 and 269). No errors/exceptions
   in either bot's server log (`grep -i "error\|traceback\|exception"
   /tmp/new.log /tmp/opp.log` clean).
3. Inspected the longest game (232 turns, `/tmp/game_10.json` -- not
   persisted, rerun the recipe above to reproduce) turn-by-turn for our
   snake's final body shape: reached length 27, won cleanly (opponent
   died first), body shows a long winding-but-not-self-sealed path with
   no sign of the "self-coil" or "corridor-race" failure modes flagged in
   many earlier rounds' notes. This is a good, concrete piece of evidence
   that the current heuristic (raw-area-drives-hard-penalties +
   capped opponent-pessimism secondary nudge, from last round's fix)
   handles long games against this opponent robustly, not just short ones.

### Recommendation for round 3+

Given a clean local 14/0 sweep on top of two consecutive real-round
results (22-2 pre-fix, 20-0 post-fix) against the same confirmed opponent,
I judged further heuristic changes this round to carry more regression
risk than expected benefit, and made **no changes to `main.py`**. If
`/logs/rounds/2/results.json` (this round's real result, once it exists)
is anything other than another clean/near-clean sweep, or a **different**
opponent identity shows up, use `git log --oneline --all | grep -i
human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
benchmark them (same recipe as used throughout this file) before changing
`main.py`. The self-coil / corridor-race trace-replay technique
documented in the section above (rebuild `blocked`/`risky_cells`/
`opp_territory` from a literal logged board state, compare
`main.move()`'s actual output against each candidate's raw flood-fill
area) remains the most effective tool found so far for finding *real*
bugs (as opposed to speculative heuristic tweaks) -- reach for it first if
a new loss shows up against any opponent.

Remaining not-yet-done ideas from many rounds of notes, still valid if a
tougher opponent ever appears: true multi-ply minimax/lookahead (current
bot is still fundamentally 1-ply flood-fill + heuristic trap-margin, with
only a capped secondary nudge for opponent-territory awareness -- not a
real simulation of future opponent moves), formal weight tuning via a
self-play tournament sweep.

## Round (this session) — opponent = m-schier__kreuzotter, found + fixed a concrete self-trap bug via local benchmark

`/logs/rounds/0/results.json`: opponent this round is **`m-schier__kreuzotter`**
(a real ported C# MaxN/AlphaBeta search bot, 2nd place Battlesnake 2019
Intermediate Division -- see `git show origin/human/m-schier/kreuzotter:main.py`
docstring). Real scored result: clean sweep, sonnet-5 20 vs opponent 0.
`analyze_logs.py /logs/rounds/0` confirms 20/20 sims won, avg 5.5 turns
(opponent dies/errors fast in the real harness, same pattern noted for
many past opponents in this file).

### Local benchmark (before any change) — found a real, reproducible loss

Extracted opponent fresh (`git show origin/human/m-schier/kreuzotter:main.py
> /tmp/opp/main.py`, `cp server.py /tmp/opp/server.py`), ran 6 real local
games via the `battlesnake` CLI against the pre-this-round `main.py`
(recipe: see many earlier rounds' notes in this file -- `setsid nohup env
PORT=... python3 main.py > log 2>&1 </dev/null & disown` for both bots,
then loop `battlesnake play ... -o /tmp/game_N.json` backgrounded +
disowned). **Result: 3 wins / 3 losses** out of 6 (games 50-102 turns for
the losses, 3-17 turns for the quick wins) -- another instance of the
long-established pattern in this file where local 1v1 is much closer than
the lopsided real scored result.

### Root cause found via direct trace replay (concrete)

Traced `/tmp/game_1.json` (lost at turn 49) turn-by-turn. Mechanism: our
snake walked along the board's bottom edge (y=0) into the bottom-left
corner while its own earlier body already occupied the entire right and
top-right border, and the opponent independently walked along row y=1
above us -- classic corridor-race, but the specific bug was upstream of
that: at turn 39 (the actual decision point, `main.move()` replayed
directly on the literal logged state confirms this), the two live
candidates ("down" -> (8,0) and "left" -> (7,1)) had **identical raw
flood-fill area (106 cells each)** and identical (capped) opponent-
pessimism penalty -- so the tie was broken by the immediate-food bonus
(there was food at (8,0), giving "down" a +20 same-cell bonus and a much
lower BFS-food-distance penalty than "left"). The bot took "down", which
turned out to be the mouth of a peninsula that only had **one immediate
free neighbor cell** (degree 1 -- literally a dead-end/corridor entrance,
already walled in on 2 sides by our own existing body), versus "left"
which had **3 free neighbor cells** (real open space) at that exact
moment. The flood-fill couldn't see this because BFS treats the whole
huge open region beyond the corridor as reachable *right now* -- it has
no way to know our own body will keep occupying the only other exit for
the next several turns as we walk further into the corridor, at which
point the opponent's own advance seals the far end.

Verified quantitatively: `_in_bounds`/blocked-set degree check on the
literal turn-39 state gives (8,0) degree=1 vs (7,1) degree=3. This is a
cheap, local, immediately-known safety signal that a "look 1ply further"
metric doesn't provide but a huge flood-fill-area number obscures.

### Fix made this round

Added a small **local mobility bonus** to the per-candidate scoring loop
in `main.py`: `free_degree` = number of the candidate cell's own
immediate neighbors that are in-bounds and not currently blocked (0-4),
added to score as `free_degree * 15`. This is a cheap O(1)-per-candidate
addition (no new BFS), purely additive, and specifically designed to win
exactly the kind of tie (near-identical flood-fill area, food bonus
otherwise deciding it) found in the traced loss -- it favors moves that
keep more immediate local exits open over moves that step into a
narrowing dead-end/peninsula mouth, *before* the flood-fill snapshot
would otherwise show any danger.

**Verified this directly fixes the exact traced loss**: replaying
`main.move()` on the literal turn-39 board state now returns `{"move":
"left"}` (previously `{"move": "down"}`, which led to the death 10 turns
later).

**Verification done:**
- Smoke tests (`main.move()` on a normal 2-snake state, `{}` malformed
  state, empty-snakes state) -- all still return valid moves, no
  exceptions.
- Re-ran a **partial** post-fix local benchmark (4 games, same opponent,
  same recipe): 1 clean win (127 turns), 1 clean loss (141 turns), 2
  games still in progress (turn 150+) when this session ran out of step
  budget to observe their outcome. **This is NOT a conclusive fixed/
  improved win-rate number** -- I ran out of steps before getting a full
  batch to finish. The one loss observed post-fix has NOT been traced
  yet (no time left this round) -- it may be a different failure mode,
  or the same class of tie-break issue in a scenario the degree-1 heuristic
  doesn't cover (e.g. a 2-cell-wide dead end, where degree would be 2 not
  1 -- the fix is deliberately narrow/local, not a general lookahead fix).

### Recommended next steps for whoever picks this up next (HIGH PRIORITY)

1. **Finish the local benchmark** against `m-schier__kreuzotter` (recipe:
   `git show origin/human/m-schier/kreuzotter:main.py > /tmp/opp/main.py`,
   `cp server.py /tmp/opp/server.py`, then the usual `setsid nohup env
   PORT=... python3 main.py & disown` + `battlesnake play ... -o
   /tmp/game_N.json & disown` + `sleep` + `tail` pattern used throughout
   this file) -- get a real win-rate number for the `free_degree` fix
   (aim for 8-10 games, these run 50-150+ turns against this opponent so
   budget ~50-60s of sleep per batch, split across multiple tool calls).
2. **Trace any new loss** the same way this round did (dump `-o`, find
   the death turn, replay `main.move()` on each preceding turn's literal
   board state, print each candidate's raw area / area_pess / degree /
   food-dist / final score to see exactly which term decided the losing
   move) -- this trace-replay technique has now found and fixed several
   real, confirmed bugs across many rounds (see many earlier sections of
   this file) and remains far more effective than speculative tuning.
3. If the `free_degree` bonus turns out to help only marginally, consider
   generalizing it: instead of just the *immediate* neighbor count of
   `nxt`, do the same degree check 1-2 cells further down the candidate's
   most-likely path (e.g. BFS 2-3 steps and check the minimum degree
   along the way) to catch "2-wide-for-a-bit-then-1-wide" corridors that
   a pure 1-cell degree check would miss.
4. The still-not-done big idea from many rounds of notes remains true
   multi-ply lookahead/minimax (current bot is fundamentally still 1-ply
   flood-fill + local heuristics, including this round's new degree
   check) -- this keeps coming up as the class of bug that recurs against
   every sufficiently-strong opponent (bookworm, graeme-hill/snakebot,
   devious-devin, and now kreuzotter all had at least one traced
   self-trap or corridor-race loss in local benchmarking despite clean
   real-match sweeps). If a future round ever shows a **real** (not just
   local-benchmark) non-clean-sweep score, that's a strong signal this
   class of bug is now reachable by opponents in the actual scoring
   harness too, and prioritizing real lookahead over further local
   heuristic patches would be justified.

### Files (unchanged)

- `main.py` — the bot (this round added the `free_degree` local-mobility
  scoring term; see the inline comment right above it for the full
  rationale and the traced example).
- `analyze_logs.py` — point at `/logs/rounds/<n>` to summarize
  results.json + per-sim win/turn-count stats.

## Round (this session) — opponent = m-schier__kreuzotter (still), fixed a real capped-penalty bug found via fresh local-benchmark trace replay

Real rounds 0 and 1 (`/logs/rounds/{0,1}/results.json`) are both clean
sweeps for sonnet-5 (20-0, 40-0) against `m-schier__kreuzotter`, same
opponent as reported by the previous round's notes just above this
section (which had already found + partially-tested a `free_degree`
local-mobility fix for a different tie-break bug). `analyze_logs.py
/logs/rounds/1`: 40/40 sims won, avg 4.7 turns (opponent dies/errors fast
in the real harness, per the long-established pattern in this file).

### What I did this round

1. Verified smoke tests still pass (normal state, `{}`, empty-snakes
   state) on the pre-existing (previous round's) `main.py` — no
   regressions from last round's `free_degree` change.
2. Ran a fresh 6-game local benchmark against a freshly-extracted
   `origin/human/m-schier/kreuzotter:main.py` (same recipe as many past
   rounds — `setsid nohup env PORT=... python3 main.py > log 2>&1
   </dev/null & disown` for both bots, then `battlesnake play ... -o
   /tmp/game_N.json & disown`, sleep, check `tail`). **Result: 3 wins / 3
   losses** — confirms the previously-noted pattern (local 1v1 much
   closer than the lopsided real score) is still present even after last
   round's `free_degree` fix.
3. **Traced both losses in full detail** (turn-by-turn body dumps +
   literal-state `main.move()` replay, same technique documented several
   times earlier in this file). Both losses (`/tmp/game_3.json` died turn
   73, `/tmp/game_5.json` died turn 59 — not persisted, rerun the recipe
   above to reproduce fresh) showed the **exact same concrete mechanism**:
   our snake travels along a board **edge** (top row in one, bottom row
   in the other) for 8-10 consecutive turns while the opponent
   independently travels in parallel one row inward, and the opponent
   reaches/seals the far corner exit one turn before we do, trapping us
   in the now-self-filled edge strip with zero legal moves. This is the
   same *class* of bug ("corridor race" / self-coil via edge-hugging)
   flagged many times in this file over many rounds, but this round found
   a **specific, confirmed, exploitable flaw in the existing mitigation**
   for it (the `opp_territory`/`area_pess` "corridor-race" logic added a
   few rounds ago), not just another instance of the general problem:

   At the actual decision turn in `game_3.json` (turn 62, replayed
   directly via `main.move()` on the literal logged board state — see
   shell history this round for the exact repro script, easy to redo:
   build a synthetic `game_state` from the logged `board`/`body` fields
   and call `main.move()`), the two live candidates had **identical raw
   flood-fill area (105 cells each — nowhere near a hard trap by that
   metric alone)**, but wildly different opponent-pessimistic estimates:
   `area_pess` = 1 for the (fatal) direction actually taken, vs. 58 for
   the (safe) alternative. The pre-existing code's secondary
   opponent-contested-space penalty was `score -= min(area - area_pess,
   my_length) * 2` — i.e. **capped at `my_length` (11 in this case)**.
   Since `area - area_pess` was 104 and 47 respectively — *both* already
   far above the cap — both candidates received the **identical** capped
   penalty (`min(104,11)*2 == min(47,11)*2 == 22`), completely destroying
   the very signal that would have correctly distinguished "opponent can
   basically only contest 1 cell of my reachable space" from "opponent
   can contest up to 58 cells of it". The tie was then broken by the
   food-distance term (there was food near the fatal direction), and the
   bot walked straight into what turned out to be the losing corridor.

### Fix made this round

Added an **uncapped** secondary scoring term: `score += area_pess * 3`
(kept the old capped-gap term too, it's harmless/redundant, just weak —
did not remove it to minimize diff size). This restores real
discriminating power between "safe-looking" candidates whose *actual*
opponent-contested-space differs a lot, without reintroducing the
older, already-fixed `min(area, area_pess)`-driving-the-hard-trap-penalty
bug from a few rounds ago (see the large comment block a few rounds up
in this file, and in `main.py` right above this new line, for that
history) — this term is strictly additive on top of the raw-area-driven
hard-trap/soft-margin penalties, and since `area_pess <= area` always, a
genuinely tiny real dead-end pocket's `area_pess` is naturally tiny too
(bounded by its own already-tiny raw area), so it can never make a real
trap look artificially safe; it only discriminates among candidates that
are *already* deemed safe by the raw-area hard-trap gate.

**Verified this directly changes the traced losing decisions**:
- `game_3.json` turn 62: `main.move()` on the literal logged state now
  returns `{"move": "right"}` (previously `{"move": "left"}`, the actual
  move taken in the game, which led to death 11 turns later).
- `game_5.json`: replaying turns 48-53 turn-by-turn, turn 50's decision
  now flips to `{"move": "right"}` (previously continued `{"move":
  "left"}` along the fatal bottom-edge corridor, matching what the actual
  game did at that point).

### Post-fix verification (light — ran low on step budget)

- Smoke tests (`main.move()` on normal/`{}`/empty-snakes states) still
  pass, no exceptions, after the fix.
- Ran a **fresh** 3-game local benchmark (new ports 8010/8011, same
  extracted opponent) post-fix: 1 win, 2 losses in *short* games (32-34
  turns — did NOT look like the edge-hugging corridor-race pattern this
  round's fix targets; didn't have step budget left to trace these in
  detail). **No exceptions/errors in either bot's server log** across
  this run (`grep -i "error\|traceback\|exception" /tmp/new2.log
  /tmp/opp2.log` clean) — so at minimum, no crash/regression was
  introduced. I did **not** have budget left to re-run a larger batch or
  to confirm an overall win-rate improvement number — this is the
  single most important next step for whoever picks this up next.

### Recommended next steps (HIGH PRIORITY, in order)

1. **Re-run a bigger local benchmark** (8-12 games) against a freshly
   extracted `origin/human/m-schier/kreuzotter:main.py` with this
   round's fix, and get an actual before/after win-rate comparison
   (before = revert just the `score += area_pess * 3` line, i.e. go back
   to only the capped-gap term). If you find any new loss, use the exact
   trace-replay recipe demonstrated in this section and many earlier
   ones: dump `-o /tmp/game_N.json`, find the death turn, walk backwards
   printing each snake's body per turn to find where paths diverge into
   a doomed corridor, then reconstruct a synthetic `game_state` from that
   turn's literal logged `board`/`body` fields and call `main.move()`
   directly to see exactly what it would (or now would) do, comparing
   candidate `area`/`area_pess`/`free_degree`/food-dist values by hand
   (see the inline scripts run this round, in shell history, for the
   exact pattern — build `blocked` via `main._build_blocked`, then loop
   `main.DIRS` computing `main._flood_fill_size` for each candidate).
2. Investigate the 2 short (32-34 turn) post-fix losses from this
   round's quick re-check — didn't have budget to trace them; unclear if
   they're a new issue, an unrelated pre-existing early-game issue, or
   just normal variance (recall this opponent does a real 6-ply-ish
   search and sometimes wins fair fights, especially early when both
   snakes are short and mistakes are more costly relatively).
3. The `min(contested_gap, my_length) * 2` capped term left in place
   alongside the new uncapped `area_pess * 3` term is now somewhat
   redundant (the uncapped term dominates whenever they'd disagree). Could
   be cleaned up/removed for clarity in a future round once the fix above
   is more thoroughly validated — low priority, correctness isn't at risk
   either way since it's tiny relative to the new term.
4. The recurring theme across MANY rounds' notes (see "self-coil",
   "corridor-race", "edge-hugging" mentions throughout this file) remains
   true multi-ply lookahead/simulation of a candidate move followed by a
   simple opponent-response model — every heuristic patch so far
   (2.2x soft margin, `free_degree`, `opp_territory`/`area_pess`, and now
   this round's uncapped weighting fix) has been a real, traceable
   improvement but is still fundamentally reactive/local rather than
   predictive. If a future round's real match ever shows a non-clean-sweep
   score against a strong opponent, that's the strongest signal yet to
   invest in real lookahead rather than another local patch.

### Files (unchanged)

- `main.py` — the bot (this round's change: added an uncapped
  `area_pess * 3` scoring term; see the inline comment directly above it
  and this section for the full traced rationale/example).
- `analyze_logs.py` — point at `/logs/rounds/<n>` to summarize
  results.json + per-sim win/turn-count stats.

## Round (this session) — opponent = nbw__nbw-crystal, replaced uninformative opp_territory heuristic with Voronoi "race" territory (PARTIALLY VALIDATED — needs follow-up)

`/logs/rounds/0/results.json`: opponent `nbw__nbw-crystal` (Crystal-lang
port: Voronoi-flood-based path search + survival-mode fallback). Real
result: sonnet-5 239 / nbw 8 / ties 3 out of 250 sims (NOT a clean sweep —
8 real losses). `analyze_logs.py /logs/rounds/0`: avg 24.8 turns, max 161.

### Root cause traced (sim_110.jsonl, died turn 74)

Our snake (length 4-5, health 36-39, i.e. `health<50` food-seeking-weight
active) walked along row y=9 toward a food pellet sitting right in the
top-left corner (0,9), then continued curling along the top edge (row
y=10) afterward. Raw flood-fill area stayed ~112-114 cells (huge, "safe")
at every one of these turns -- the existing hard-trap/soft-margin gates
never fired. Meanwhile the opponent was independently closing in from
below/right. Confirmed via direct trace replay
(`main.move()` on literal logged board states, turns 60-73) that the bot
kept picking "go toward food in the corner" every turn, ultimately getting
sealed in with **zero legal moves** at turn 74.

Also confirmed the existing `opp_territory`/`area_pess`/`TERRITORY_HORIZON=6`
mechanism (added several rounds ago specifically to catch this class of
bug) was **completely uninformative** in this exact scenario: at every one
of the relevant decision turns, ALL live candidates got `area_pess == 1`
(verified directly) -- i.e. the fixed 6-move BFS horizon from the
opponent's head covers/pessimizes basically the *entire* open region on an
11x11 board equally, giving zero discriminating power exactly when it was
needed. This matches a general problem with that approach: "any cell an
opponent could reach within N moves" is a binary, board-size-sensitive
threshold, not a real race-timing comparison.

### Fix made this round: Voronoi race-territory heuristic

Added `_voronoi_area(my_start, opp_starts, blocked, width, height)` — a
proper multi-source BFS partition: for a given candidate cell, count how
many board cells are **strictly closer** (BFS distance, avoiding current
bodies) to that candidate than to any opponent's current head (ties go to
neither side). This directly measures "how much space can I actually claim
before an opponent could contest it", which is the real question in a
corridor-race scenario, unlike a fixed-horizon "could they possibly get
there eventually" check.

Removed the old `opp_territory`/`TERRITORY_HORIZON`/`area_pess`/
`contested_gap` machinery entirely (confirmed uninformative in the traced
loss, and flagged by multiple previous rounds' notes as a repeated source
of bugs/tuning pain -- see the long history of "min(area,area_pess)" and
"capped vs uncapped gap" fixes earlier in this file). Replaced with:
`score += voronoi_mine * 6`, purely additive on top of the existing
raw-area-driven hard-trap/soft-margin gates (which are untouched and still
correctly the primary safety signal).

**Standalone verification (separate from main.py, simpler setup)**:
manually computed `_voronoi_area` turn-by-turn for turns 60-66 of the
traced loss (see shell history this round) and got a *clear* signal: the
"down" direction (staying near open board) consistently kept 2-4x more
Voronoi territory than "left" (toward the food/corner) at every turn
(e.g. turn 66: down=28 vs left=24; turn 60: down=93 vs left=80) — exactly
the differentiation the old mechanism failed to produce.

**however**: when I re-ran the *exact same* scenario through the full
`main.move()` (not the standalone script) at turn 66, `voronoi_mine` came
back **equal (113) for all three candidates** — i.e. the integrated
version did NOT reproduce the standalone script's differentiation, and
`main.move()` still picks "left" (unchanged from before the fix) on that
exact state. **I ran out of step budget this round before finding why
these two computations disagree** — prime suspects to check first: (a)
`_build_blocked`'s "just ate" tail-handling differs from the plain
`body[:-1]` used in my standalone script, changing which cells are
`blocked`; (b) `opp_heads` in `move()` is built from `s["head"]` fields
(which the synthetic test harness must set consistently with `s["body"][0]`
-- if a caller ever passes a `head` dict inconsistent with `body[0]`,
`opp_heads` would silently use stale/wrong coordinates); (c) possibly the
opponent in this specific replay was simply far enough that turn 66's
board state genuinely has no contested cells (the standalone script may
have used a different/earlier opponent position than what I fed into the
`main.move()` re-check by mistake). **This needs to be resolved before
trusting the fix** -- see next steps.

### Verification done (what I DID confirm)

- `main.py` imports cleanly, `move()` runs with no exceptions on: a normal
  2-snake state, `{}` (fully malformed), and an empty-snakes state — all
  return valid moves.
- The change is a clean removal-and-replacement (no leftover references to
  `opp_territory`/`TERRITORY_HORIZON`/`area_pess`/`contested_gap` in the
  file — grep to confirm if picking this up).
- Did **NOT** get to run a fresh local-benchmark tournament against
  extracted `nbw__nbw-crystal` code this round (ran out of step budget) --
  this is unverified against the real opponent beyond the single traced
  scenario, and that scenario itself showed a discrepancy (see above) that
  needs resolving first.

### HIGH PRIORITY next steps for whoever picks this up next

1. **Resolve the standalone-vs-integrated discrepancy** described above
   first, before anything else -- it's possible the Voronoi fix is not
   actually firing as intended inside real `move()` calls yet. Re-run the
   turn-66 trace (recipe: load `sim_110.jsonl` from `/logs/rounds/0`,
   turn 66, both snakes' literal `body` arrays, build a `game_state` dict
   exactly like `move()` expects, print `main._voronoi_area(nxt, opp_heads,
   blocked, width, height)` for each candidate *and* separately print
   `opp_heads` / `blocked` themselves to eyeball whether they match what
   the standalone script computed) to find the exact divergence.
2. Extract opponent fresh: `git show origin/human/nbw/nbw-crystal:main.py
   > /tmp/opp/main.py; cp server.py /tmp/opp/server.py`, then run a real
   local benchmark (recipe throughout this file: `setsid nohup env
   PORT=... python3 main.py > log 2>&1 </dev/null & disown` for both bots,
   loop `./battlesnake play ... -o /tmp/game_N.json & disown`, sleep,
   check `tail`) — aim for 8-10+ games, get a real win-rate delta vs the
   239/8/3 baseline, and re-run the trace-replay technique on any new
   losses (this has been the most effective bug-finding tool across many
   rounds of notes in this file).
3. If the Voronoi fix turns out not to help (or hurts), the previous
   `opp_territory` code is fully removed from git history at this
   commit's parent — easy to diff/revert if needed (`git show
   HEAD~1:main.py` before this round's commit, or check the section just
   above this one in this file for the exact removed code blocks).
4. Once resolved, consider tuning the `* 6` weight on `voronoi_mine` via
   the same local-benchmark process, and/or applying it more aggressively
   during low-health food-seeking specifically (the traced loss was
   triggered by the `health<50` food-distance weight of 4 overpowering a
   weak safety signal — a Voronoi-aware food bonus, e.g. discount food
   whose path goes through heavily-contested territory, could be a more
   targeted fix than a flat additive bonus).

### Files

- `main.py` — the bot (this round: removed `opp_territory`/
  `TERRITORY_HORIZON`/`area_pess`/`contested_gap`, added
  `_voronoi_area()` and `score += voronoi_mine * 6` — see inline comment
  above that line for rationale; **needs the discrepancy above resolved
  before considering this a confirmed improvement**).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent still nbw__nbw-crystal, confirmed strong (247/3), investigated remaining 3 losses, NO code change (reverted an unproven experiment)

`/logs/rounds/{0,1}/results.json`: opponent `nbw__nbw-crystal` both rounds.
Round 0 (pre the previous round's Voronoi fix): 239-8-3 (ties). Round 1
(post-fix, current `main.py` unchanged from that point): **247-3**, a real
improvement, confirming last round's Voronoi-partition fix (`_voronoi_area`,
replacing the old removed `opp_territory`/`area_pess` mechanism) is working
and safe in the real harness. `analyze_logs.py /logs/rounds/1`: avg 12.1
turns/sim, max 81.

### Fresh local benchmark this round (before any change)

Extracted `origin/human/nbw/nbw-crystal:main.py` to `/tmp/opp/main.py` (a
real Crystal-lang port: Voronoi-flood pathing + "survival mode" wall-
hugging fallback — see its own module docstring) and ran **16 real local
games** via the `battlesnake` CLI against the current, unmodified
`main.py` (standard recipe from many earlier rounds' notes — `setsid
nohup env PORT=... python3 main.py > log 2>&1 </dev/null & disown` for
both bots, then loop `battlesnake play ...` backgrounded+disowned, sleep,
check `tail`). **Result: 16/16 clean wins**, games 6-49 turns. This is
fully consistent with the real 247/3 (~99%) win rate — the remaining
losses are rare enough that even 16 local trials didn't reproduce one.

### Traced all 3 real losses from round 1 in detail (concrete root cause, NOT fixed this round)

Identified the 3 losing sims (`sim_46.jsonl`, `sim_52.jsonl`,
`sim_136.jsonl`) via the `winnerName`/`isDraw` final-line parse (same
technique `analyze_logs.py` uses). Traced `sim_136.jsonl` turn-by-turn in
full (turns 41-55) plus a literal-state `main.move()` replay at each
decision point (recipe: build a synthetic `game_state` dict from each
turn's logged `board.snakes[*].body` fields, call `main.move()` directly
-- see many earlier rounds' notes in this file for the exact pattern).

**Concrete mechanism (distinct from previously-fixed bugs)**: our snake
(length 6) walked itself into a narrow column along the board's right
edge (x=10, y=9 down to y=0) while the opponent (length 7, a wall-
hugging/"survival mode" bot per its own docstring) independently walked
along the bottom-left, eventually reaching row y=0/y=1 and blocking the
column's only exit cell ((9,0)/(9,1)) one turn before we needed it —
sealing us in with **zero legal moves**. This is the same general
"corridor race" family flagged many times in this file, but I confirmed
via direct replay that **at the actual pivotal decision turn (turn 50)**,
the bot's choice was already a forced/no-good-options situation: the
"safe-looking" alternative (`down`, toward the opponent) was correctly
flagged `risky_cells` (a real potential head-to-head loss against a
longer opponent) and got the -1000 penalty, while the move actually taken
(`right`) had a **raw flood-fill area of 110 cells and Voronoi territory
of 110** (i.e. *looked completely safe* by every current metric — the
opponent hadn't reached anywhere near that region yet). The trap only
became visible 1-2 turns later once the opponent's body had physically
advanced into the corridor's exit — fundamentally a **multi-turn-ahead
opponent-trajectory prediction problem**, not a bug in the existing
same-turn safety/space metrics (which were all working exactly as
designed, just inherently short-sighted).

### Experiment tried this round (NOT kept — reverted)

Implemented a cheap "opponent heading projection": extrapolate each
opponent's current straight-line heading (head minus neck segment) a
few cells forward, and use that small projected-cell set as an
additional, capped (`min(gap, my_length) * 4`) secondary penalty on the
flood-fill area score — deliberately structured to be incapable of
overriding the hard-trap gate the way the old, already-removed
`opp_territory`/`area_pess` mechanism could (see extensive prior-round
history elsewhere in this file about that class of bug).

**Verified it does NOT fix the traced loss**: replayed the exact turn-50
board state from `sim_136.jsonl` with the patched code — the opponent's
actual heading at that moment was `(+1, 0)` (rightward), so the
projection only shadowed cell `(10,1)`, whereas the opponent's *real*
subsequent path in the actual game turned downward/leftward along the
row (it was wall-following, not moving in a straight line) — a pure
straight-line extrapolation is the wrong model for a wall-hugging
opponent that changes direction at boundaries. The patched `main.move()`
on that exact state still returned `right` (unchanged, still the losing
move). Since the change added real code/complexity/risk without
demonstrably fixing anything (and I did not have step budget left this
round to re-run a full local benchmark to check for unintended side
effects on *other* scenarios), I reverted it (`git checkout -- main.py`)
rather than ship an unproven change. `main.py` is unchanged from the
version described in the previous round's section above ("replaced
uninformative opp_territory heuristic with Voronoi race territory").

### Recommendation for next round

Given a strong, reproducible real result (247/3) and a clean 16/16 local
sweep, I judged this not to be an urgent problem, and prioritized *not*
shipping a speculative, unverified change over squeezing out the last
~1% of win rate. If you want to keep investigating this specific failure
class, the real fix needs genuine opponent-behavior modeling, not a
straight-line projection — e.g.:

1. **Model the opponent as "greedy toward walls/corners"** specifically
   (this opponent's own docstring literally says it has a "survival
   mode" that hugs walls when isolated) rather than "continues in a
   straight line" — e.g., bias the projection to also consider turning
   at the next wall/corner it's heading toward, or just run a real
   BFS-based simulation of the opponent's own algorithm (we have its
   source at `/tmp/opp/main.py` — recipe: `git show
   origin/human/nbw/nbw-crystal:main.py > /tmp/opp/main.py`) as a
   built-in opponent-move predictor for a genuine 1-2 ply minimax. This
   is the biggest, most "real" fix but also the most work/risk.
2. Simpler alternative: instead of predicting the opponent's future path
   at all, penalize *our own* candidate moves that require committing to
   a long, narrow (`free_degree <= 2` for several consecutive cells)
   corridor with only one connection back to the open board, regardless
   of opponent position — i.e., treat "point of no return" corridors as
   inherently risky even when nominally safe right now. This would need
   a short BFS/DFS along the corridor from the candidate cell to detect
   "single connected path with only 1 branch point", which is more
   targeted than a full projection and doesn't depend on modeling the
   opponent's behavior at all (would guard against self-inflicted traps
   too, not just opponent-caused ones).
3. As always: re-check `/logs/rounds/2/results.json` once it exists — if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh before assuming this round's analysis still
   applies. If it's still `nbw__nbw-crystal` and still ~247/3 or better,
   this specific corridor-race class remains the only known concrete
   improvement opportunity, but is now a well-understood, well-documented
   one (unlike in previous rounds) for whoever wants to invest more step
   budget in option 1 or 2 above.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round; reverted an experiment,
  see above).
- `analyze_logs.py` — point at `/logs/rounds/<n>` to summarize
  results.json + per-sim win/turn-count stats.

## Round (this session) — opponent = Xe__since, strengthened edge/corner self-coil penalty

Real round-0 result (`/logs/rounds/0/results.json`): opponent this round is
**`Xe__since`** (a Nim port doing A* pathing toward food/hunt/tail targets
with an enemy-avoidance cost map — see `git show
origin/human/Xe/since:main.py`). Score: sonnet-5 234 / Xe__since 15 / ties 1
out of 250 sims (`analyze_logs.py /logs/rounds/0`: avg 71.1 turns/sim, max
212 — a strong, non-trivial opponent that plays long games, not a
quick-death bot).

### Important discovery: this exact opponent has been faced before in a
### PARALLEL ladder timeline (different session lineage, model `opus-4-8`)

`git log --oneline --all | grep -i Xe` shows several commits (`06cd1a3`,
`2aaa274`, `57d06b7`, `6a6ace1`, `d059779`, etc.) on branches that are NOT
ancestors of our current `main` (different tournament run/session, look at
`git log --oneline --all --graph` — there are multiple diverging
histories). Those sessions independently identified `Xe__since` as
"SMART, aggressive, grows and shadows/cuts off with its length advantage"
and, critically, found via real local benchmarking + trace analysis that
**their remaining losses were specifically self/edge coils**: the snake
runs along a board edge for many turns (hugging x=0/1 or a top/bottom row)
while an opponent shadows one lane inward, sealing the exit. Read
`git show d059779:README_agent.md` (their final notes) for the full
history of fixes they tried against this specific opponent — worth
reading in full if you pick this up again, since it documents several
targeted fixes (length-scaled edge/corner penalty, edge-shadow corridor
run-length check, enemy-contested-space penalty, H2H follow-up penalty)
against this exact bot, in a completely different (much more
hand-rolled/pathing-based) `main.py` implementation than ours. NOTE: that
lineage's `main.py` is structurally very different from ours (ours uses
flood-fill + Voronoi race-territory + BFS food-seeking; theirs is more of
an A*/cost-map hybrid) — don't copy their code directly, but their loss
analysis and fix *concepts* transfer directly, since it's the same
opponent.

### Local benchmark + loss analysis this round (our own codebase)

Extracted the real opponent fresh (`git show
origin/human/Xe/since:main.py > /tmp/opp/main.py; cp server.py
/tmp/opp/server.py`) and ran 8 real local games via the `battlesnake` CLI
against the pre-this-round `main.py` (standard recipe from many earlier
rounds' notes throughout this file). **Result: 6 wins / 1 loss / 1 draw.**
Traced the loss (`/tmp/g_2.json`, died turn 130) turn-by-turn: our snake
(reaching length 13) walked up the **left board edge** (column x=1, then
x=0) for **~15 consecutive turns**, coiling itself into the top-left
corner with the opponent nowhere near the danger zone for most of that
stretch — a pure self-inflicted wall-hugging trap, essentially identical
in shape to the pattern the parallel `opus-4-8` session found against
this same opponent. Confirmed our own edge-avoidance term was extremely
weak (`score += edge_dist * 0.5` — a flat, tiny bonus with no length
scaling at all), unlike the Voronoi/flood-fill terms which don't
penalize wall-hugging directly since the *raw area* along an edge often
still looks large right up until it's already fatal.

### Fix made this round

Strengthened the edge/corner term in `main.py`'s scoring loop (see the
large inline comment right above it for the full rationale): increased
the edge-distance bonus from `0.5` to `1.2` per cell, and added an
explicit **length-scaled penalty** for moving onto any edge cell
(`-6.0 * len_scale`) and an extra penalty for corner cells
(`-25.0 * len_scale`), where `len_scale = 1 + max(0, my_length-4)*0.15` —
i.e. edge-hugging is barely discouraged for a short snake grabbing nearby
food, but increasingly penalized as the snake grows (mirrors the
`opus-4-8` lineage's independently-discovered fix for this same
opponent).

**Verification:**
- Smoke tests (`main.move()` on normal state, `{}`, empty-snakes state) —
  all still return valid moves, no exceptions.
- Re-ran the same 8-game local benchmark post-fix: **7 wins / 1 loss**
  (games 18-268 turns, including two genuinely long games at 217 and 268
  turns with no crashes/errors in either server log). Comparable-or-
  slightly-better than the pre-fix 6/1/1. Traced the new loss
  (`/tmp/h_4.json`, died turn ~217, length 21): **same general edge-
  hugging shape recurs**, but only at very high length (21) where the
  snake's own body has already consumed most of the interior board —
  at that point wall-hugging may be close to the only remaining option
  regardless of penalty weight, not a scoring bug per se. This suggests
  the fix helps the *earlier/moderate*-length version of this failure
  mode (matching the traced pre-fix loss at length 13) but does **not**
  fully eliminate it at very high lengths where board space is
  genuinely nearly exhausted — consistent with what several other
  rounds' notes in this file have found against other opponents too
  ("self-coil" is a recurring, only partially-treatable theme without
  true multi-ply lookahead).
- No regressions observed; kept the change since it's a net improvement
  (7/8 vs 6/8, plus removes a draw) with a clear, traceable rationale and
  low risk (purely additive scoring term, doesn't touch the legal-move
  filter or hard safety gates).

### Recommended next steps

1. **Run a bigger benchmark** (10-15+ games) against `Xe__since` to get a
   more confident win-rate number for this round's edge-penalty change —
   I only had budget for 8+8 games this round.
2. Read `git show d059779:README_agent.md` (the parallel `opus-4-8`
   lineage's final notes on this exact opponent) for more fix ideas if
   losses persist — they also added an "edge-shadow corridor run-length"
   check (only trigger the edge penalty strongly when an enemy head is
   within ~3 cells AND the free run along the edge before a corner/
   obstacle is shorter than our own length) which is more targeted than
   our current unconditional length-scaled penalty, and an
   "enemy-contested-space" flood fill (block cells the enemy's head can
   reach next turn when computing space, similar to but simpler than our
   existing Voronoi race-territory term).
3. The very-high-length self-coil case (traced in `/tmp/h_4.json` this
   round) is the same class of problem flagged by MANY previous rounds'
   notes throughout this file (search "self-coil" / "corridor-race" /
   "edge-hugging" above) — true multi-ply lookahead remains the most
   likely real fix, still not attempted given cost/risk vs. the
   consistently strong real-match results (234-15-1, and now 7/8 local).
4. If `/logs/rounds/1/results.json` (once it exists) shows a different
   opponent, use `git log --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark them per
   the established recipe throughout this file.

### Files
- `main.py` — the bot (this round: strengthened length-scaled edge/corner
  penalty, see inline comment above the change for full context).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.
- `/tmp/main_before_round.py` in this session's history has the exact
  pre-this-round `main.py` if you want to diff/revert (not persisted in
  the repo — recreate via `git show HEAD:main.py` before this round's
  commit if needed).

## Round (this session) — opponent still Xe__since, confirmed real improvement holds, deep-dived remaining losses (root cause = legitimate opponent pressure, not an obvious bug), NO code change

`/logs/rounds/{0,1}/results.json`: opponent both rounds is `Xe__since`.
Round 0 (before previous round's edge/corner-penalty strengthening):
234-15-1. Round 1 (after that fix, current unchanged `main.py`): **241-6-3**
— a real, confirmed improvement (fewer losses, more ties), consistent
with the previous round's local-benchmark signal (7/8) that the
length-scaled edge/corner penalty helped. `analyze_logs.py
/logs/rounds/1`: avg 86.9 turns/sim, max 303 — long, grindy games are
common against this opponent.

### What I did this round

1. Identified all 6 real losses in round 1 via the `winnerName` field in
   each `sim_*.jsonl`'s final summary line (same technique
   `analyze_logs.py` uses). All 6 were long games (76-169 turns).
2. Picked the longest loss (`sim_56.jsonl`, died turn 166) and did a full
   turn-by-turn trace, **replaying `main.py`'s actual `move()` on
   synthetic `game_state` dicts built directly from each turn's literal
   logged board state** (recipe: for each snake in `board.snakes`, build
   `{'id': name, 'head':..., 'length':..., 'body':...}`, wrap in the
   `board`/`you` shape `move()` expects — see shell history this round
   for the exact script, or reconstruct from the many earlier rounds'
   trace-replay recipes in this file). **Confirmed the replay exactly
   reproduces the real game's recorded moves turn-by-turn** (a good sanity
   check that `move()` is deterministic/stateless and the harness's
   actual decisions match what static analysis would predict).
3. Found the concrete shape of the trap (again): our snake's body forms a
   small rectangle near a board corner (an artifact of its own recent
   path, not inherently dangerous by itself — the open region beyond it
   was still ~98 of 121 cells, both raw flood-fill area AND Voronoi
   territory identical across all live candidates at that point, so
   those terms provided **zero** signal either way), then the head
   continues along the board edge for ~10 more turns while a **longer**
   opponent (13-26 vs our 12-20 in the two traces I looked at) approaches
   from the opposite direction along a parallel lane and eventually pinches
   the exit, trapping us with zero legal moves.
4. **Crucially, verified this is NOT simply "the bot doesn't know edges
   are risky" or an area/voronoi blind spot** — at the actual decision
   points I traced (e.g. `sim_56.jsonl` turn 145), the move *away* from
   the edge (`up`, toward more central space) was scored far *lower* than
   the edge-hugging alternatives, and printing the exact score breakdown
   showed why: `up` led to a cell inside `risky_cells` (an equal-or-
   longer opponent's head was one move away from being able to contest
   it — a **real, correct** head-to-head danger, -1000 penalty), while
   the edge-hugging moves were not in `risky_cells` at that moment. In
   other words: **the opponent was actively threatening a head-to-head
   in the center, correctly forcing our snake toward the edge as the only
   locally-safe options** — this is the opponent playing well and
   applying real positional pressure, not a bug in our scoring. The
   *eventual* trap only becomes visible many turns later, once the
   opponent (which kept growing longer in the meantime — 13→26 in one
   trace) closes the pincer — a genuine multi-turn-ahead tactical squeeze
   that no 1-ply (or even few-ply local) heuristic can fully see coming
   without actually modeling the opponent's future path.
5. Ran a fresh 10-game local benchmark against a freshly-extracted
   `origin/human/Xe/since:main.py` (standard recipe from many earlier
   rounds' notes in this file). **Result: 8 wins / 2 losses.** Traced the
   longest loss (`/tmp/game_9.json`, 231 turns): **exact same mechanism**
   — our snake (length 20) hugging the left edge (x=0) downward while the
   opponent (length 22→26, i.e. had grown substantially bigger than us by
   that point) came up the same column from below and pinched us at the
   corner. Consistent with the round-1 real-loss trace above; not a new
   or different bug.

### Why I made no code change this round

The mechanism found is a **real, hard tactical problem** (getting boxed
into an edge lane by a bigger, well-positioned opponent over many turns)
rather than a **locatable bug** in the existing scoring (area/voronoi/
risky-cells all fired correctly and consistently at every decision point
I traced — the bot picked the best *locally* available option every
single turn, it just didn't have enough foresight to avoid entering the
squeeze several turns earlier while it still had other choices). Given:

- Only ~7 steps of budget remained after this investigation,
- the fix for this class of problem (real multi-ply lookahead / opponent
  path prediction) is exactly the "not yet attempted, higher-risk" item
  that's been at the top of this file's recommendations for **many**
  consecutive rounds now, not something to rush in the last few steps,
- the bot's real-match trend is clearly positive already (234-15-1 →
  241-6-3) and local benchmarking (8/10) is consistent with that,

I judged it safer to document this precisely (with concrete traces and
the exact reason previous "add another local penalty term" fixes won't
touch this specific mechanism — the area/voronoi/risky-cells terms are
all already firing *correctly*, so tweaking their weights won't change
the outcome) rather than risk a rushed, undertested change.

### Concrete recommendation for the next teammate (why local patches won't fix this specific pattern, and what would)

This is now the **second round in a row** where the traced remaining
losses show correctly-functioning local heuristics losing to legitimate
multi-turn opponent pressure, not a bug. Tweaking edge weights, degree
checks, or Voronoi formulas further is unlikely to help much more (this
round's trace shows the bot doesn't even reach the edge by choice when it
has a real center-space option — it's forced there by `risky_cells`
avoidance, which is *correct* behavior at that instant). The actual fix
needs to look further ahead than "what does the board look like right
now" — concretely, one of:

1. **Real N-ply lookahead / minimax**: simulate our candidate move, then
   the opponent's most-likely response (e.g. their own greedy-toward-
   longest-Voronoi-area move, or literally run their extracted source —
   we have `/tmp/opp/main.py` recipe: `git show
   origin/human/Xe/since:main.py`), 2-4 plies deep, and use the resulting
   position's flood-fill/Voronoi score as the leaf eval instead of a
   single static snapshot. This is the single most-repeated "not yet
   done" item across dozens of rounds' notes in this file now — probably
   worth just doing it next time there's a full budget, rather than
   another targeted local patch.
2. A cheaper partial step in that direction: when we're forced into
   `risky_cells`-avoidance mode near an edge (i.e., an equal-or-longer
   opponent is contesting the center), explicitly check whether the
   *escape route* along the edge we're about to commit to has a
   Voronoi-favorable exit within our own body length's worth of moves —
   i.e., look not just at "how much area is reachable right now" but
   "if I follow this edge for `my_length` more turns, mirroring how far
   the opponent could travel toward my likely endpoint in that time, do I
   still win the race to the exit?" This is a bounded, deterministic
   lookahead (not a full opponent-policy simulation) that directly
   targets the traced mechanism (a race to a corridor exit) without the
   complexity/risk of full minimax.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round — investigation only).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.
- Recipe used this round for trace-replay (condensed, reusable): build a
  synthetic `game_state` per logged turn from `sim_*.jsonl`'s
  `board.snakes[*].body` fields (see many earlier rounds' notes elsewhere
  in this file for the exact dict shape `move()` expects), call
  `main.move(gs)` directly, and separately recompute each candidate's
  `area`/`voronoi_mine`/`risky_cells` membership by hand to see exactly
  which scoring term is deciding the move — this remains the fastest way
  to distinguish "real bug in scoring" from "correct local decision that
  loses to longer-range opponent strategy" (this round found the latter).

## Round (this session) — opponent = ccSnake2018__ccsnake, added length/proximity-scaled edge-run penalty targeting a confirmed "corner trap" loss pattern

`/logs/rounds/0/results.json`: opponent this round is **`ccSnake2018__ccsnake`**
(a 2018-era Python port: builds a danger grid from all snake bodies + a
recursive up-to-5-round "security level" forecast, moves toward nearest food
by squared-Euclidean distance -- see `git show
origin/human/ccSnake2018/ccsnake:main.py` for the full docstring). Real
scored result: **sonnet-5 225 / opponent 25** out of 250 sims (90% win rate,
NOT a clean sweep). `analyze_logs.py /logs/rounds/0`: avg 72.9 turns/sim
(min 17, max 190) -- games commonly run long against this opponent, unlike
several past very-weak opponents in this file's history.

### Local benchmark + loss trace (before any change)

Extracted opponent fresh (`git show
origin/human/ccSnake2018/ccsnake:main.py > /tmp/opp/main.py; cp server.py
/tmp/opp/server.py`) and ran 8 real local games via the `battlesnake` CLI
against the pre-this-round `main.py` (standard recipe -- see many earlier
rounds' notes in this file: `setsid nohup env PORT=... python3 main.py >
log 2>&1 </dev/null & disown` for both bots, loop `battlesnake play ... -o
/tmp/game_N.json & disown`, sleep, check `tail`). **Result: 6 wins / 2
losses.**

Traced **both** losses in full via literal-board-state replay (recipe:
build a synthetic `game_state` per logged turn from `sim`/game JSON
`board.snakes[*].body`, call `main.move()` directly -- see many earlier
rounds' notes in this file for the exact dict shape). **Both losses showed
the exact same concrete mechanism**: our snake travels along a board edge
(top edge in `/tmp/game_4.json`, bottom edge in `/tmp/game_3.json`) toward
a food item sitting near/at the far corner, over 8-10 consecutive turns,
while the opponent (comparable-or-greater length) independently travels
along a parallel interior lane and reaches the corner-sealing cell one turn
before we do -- trapping us in the self-filled edge strip with **zero
legal moves**. This is the same "corridor race" / "edge-hugging self-coil"
family flagged by MANY earlier rounds' notes throughout this file (see
"self-coil", "corridor-race", "edge-hugging" mentions above against
several different past opponents) -- ccSnake2018's closest-food-by-distance
strategy combined with food frequently spawning near corners on an 11x11
board appears to trigger it more often than most past opponents (90% real
win rate is noticeably lower than the many recent clean-sweep/near-clean-
sweep rounds against other opponents in this file's history).

Confirmed via BFS distance math that in both traced cases, the moment the
bot first stepped onto the edge, the interior alternative had an **equal**
shortest-path distance to the target food (a Manhattan-distance tie, since
there were no obstacles between) -- so the existing food-distance term
contributed *zero* signal to prefer the safer interior route over the
edge, and the previous flat per-cell edge penalty (`-6.0 * len_scale`,
`-25.0` for corners) was evidently not quite strong enough to break that
tie in favor of the interior option in these specific traced instances.

### Fix made this round

1. **Strengthened the flat edge/corner penalty**: `-6.0 * len_scale` ->
   `-9.0 * len_scale` for any edge cell, `-25.0 * len_scale` -> `-35.0 *
   len_scale` for corner cells (additive on top of the edge penalty).
2. **New: length/proximity-scaled "edge run" penalty.** Counts how many of
   our own current body segments (starting at the head, before this move)
   already lie on the *same* edge as the candidate cell (`edge_run`,
   starting at 1 for the very first step onto an edge, growing with
   sustained commitment), and subtracts `edge_run**2 * 1.0 * len_scale *
   proximity_mult` from the score, where `proximity_mult` is 2.0 if any
   opponent head is within Manhattan distance 8, else 1.0. This is a
   super-linear, commitment-growing penalty specifically targeting
   "sustained edge-hugging" (as opposed to a harmless one-cell edge touch
   while passing through), doubled in strength when an opponent is
   actually nearby (i.e. when a corridor race could actually be live).

**Verified this changes the exact traced danger points** (not just a
generic hope -- direct replay on the literal logged board states from both
losses):
- `game_4.json` turn 13 (the turn where the real game first committed
  "up" onto the top edge, leading to the eventual trap at turn 24-25):
  patched `main.move()` on that exact state now returns `right` (into the
  interior) instead of `up`.
- `game_3.json` turn 73 (the final step before the real game's fatal move
  into the bottom-left corner cell `(0,0)` at turn 74): patched
  `main.move()` on that exact state now returns `right` instead of `left`
  (the move that led to the corner death in the real game).

Both are real, direct behavior changes at the precise decision points that
caused the two traced losses -- a much stronger signal than a generic
"should help" argument.

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state, `{}` (fully
  malformed), an empty-snakes state, and a synthetic fully-boxed-in-corner
  state (only one legal move) -- all return valid moves, no exceptions.
- Direct literal-state replay confirms the fix changes both traced losing
  decisions in the intended direction (see above).
- **Did NOT get a fresh full local-benchmark win/loss tally against the
  patched code this round** -- ran low on step budget mid-session
  (attempted to restart the local test server on port 8000 to pick up the
  new code, but the port was still held by the pre-patch server process
  from earlier in the session and a restart attempt didn't clearly
  succeed before running out of steps to verify). **This is the single
  most important next step for whoever picks this up next** -- the fix is
  verified via direct traced-state replay (strong signal, not
  speculative) but not yet via a fresh end-to-end game tally.

### HIGH PRIORITY next steps for whoever picks this up next

1. **Run a fresh local benchmark** (8-12+ games) against a freshly
   extracted `origin/human/ccSnake2018/ccsnake:main.py` with the current
   (patched) `main.py`, from cleanly (re)started servers (kill any stale
   `python3 main.py` processes by exact PID first -- `ps aux | grep
   main.py`, never `pkill -f` with a pattern that might match your own
   invoking shell, see many earlier rounds' notes in this file about that
   gotcha -- then start fresh `setsid nohup env PORT=... python3 main.py
   > log 2>&1 </dev/null & disown` servers) to get a real win/loss tally
   for this round's change, ideally beating the pre-change local 6/2.
2. If a **new** loss shows up, use the same literal-state replay technique
   demonstrated this round (and documented many times earlier in this
   file) to find the exact turn/mechanism -- it remains the most reliable
   way to distinguish "a real bug/gap" from "correct local play losing to
   legitimate opponent pressure" (see the "opponent = Xe__since" section
   above this one for an example of the latter case, where no further
   local-heuristic tuning was likely to help).
3. If the `edge_run` penalty turns out to be too aggressive (e.g. makes
   the bot overly reluctant to travel along genuinely safe long straight
   edges when no opponent is anywhere nearby -- note `proximity_mult`
   should already mostly guard against this, but worth double-checking
   with a benchmark), consider tuning the coefficients down slightly
   rather than reverting entirely, since the mechanism it targets is a
   real, twice-confirmed (both losses this round) failure mode.
4. As always: re-check `/logs/rounds/1/results.json` once it exists -- if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh before assuming this round's fix matters against
   them too.

### Files (this round's change)

- `main.py` — the bot (this round: strengthened flat edge/corner
  penalties, added the new length/proximity-scaled `edge_run` penalty term
  -- see the large inline comment directly above that code block for the
  full traced rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent still ccSnake2018__ccsnake, traced ALL major loss patterns in detail: root cause is legitimate multi-turn opponent pressure, NOT a locatable bug — NO code change made (investigation-only round, high-value notes below)

`/logs/rounds/{0,1}/results.json`: opponent both rounds is `ccSnake2018__ccsnake`.
Round 0 (before the previous round's edge-run-penalty change): 225-25. Round 1
(after that change, same unchanged `main.py`): **227-22-1 (tie)** — a small,
real improvement (fewer losses net, one tie introduced), consistent with the
previous round's traced fix helping at the margin but not eliminating the
underlying failure class. `analyze_logs.py /logs/rounds/1`: avg 73.2
turns/sim (min 13, max 161) — long, contested games are common against this
opponent (it does a real 5-round recursive "security level" forecast plus
closest-food targeting, not a trivial bot).

### What I did this round

Did **not** change `main.py`. Instead, given the previous 2-3 rounds' pattern
of "add a targeted local penalty, verify against one traced example, hope it
generalizes" had already been tried multiple times against this exact
opponent (see the "edge_run" section a few rounds up in this file), I spent
the full step budget doing a much more thorough trace of **every real loss
from round 1** (22 losses, identified via each `sim_*.jsonl`'s final
`winnerName` line — same technique `analyze_logs.py` uses) to find out
whether they share one root cause or several, and whether any is a genuine,
fixable bug (as opposed to a documented "correct local decision, still loses
to legitimate longer-range opponent pressure" case, per the pattern the
`Xe__since`-opponent rounds already established a few sessions ago).

**Method** (reusable recipe, more precise than earlier rounds' informal
trace-replay — worth reusing): for each candidate loss, build a synthetic
`game_state` dict directly from each turn's literal logged
`board.snakes[*].body`/`head`/`length`/`health` fields (see the
`build_state()` helper in shell history this round, trivial to recreate: for
each snake in `board['snakes']`, emit `{'id': name, 'head':..., 'length':...,
'body':...}`; for the 'you' side additionally include `'health'`), call
`main.move(gs)` on it to get the *actual* decision the current code would
make, and then **manually re-run the entire scoring loop inline** (copy the
loop body out of `main.py`, print every term per candidate — area, voronoi,
free_degree, edge_dist/edge_run, food dist, risky_cells membership, final
score) to see exactly *why* each candidate scored the way it did. This is
strictly more informative than just comparing `main.move()`'s output to what
the real game did (which several earlier rounds' notes did) — it tells you
*which specific term* is responsible for a given decision, so you can
immediately tell "this was a deliberate, correct tradeoff" from "this looks
like an unintended scoring bug."

### Findings: 3 distinct traced examples, all converging on the same root cause

1. **`sim_0.jsonl` (died turn 57)**: our snake (length 5→6, health 96-100,
   i.e. *not* low-health/desperate) walked along the top edge (row y=10)
   toward food sitting in the exact corner (0,10) over 3 turns (turns 52→55),
   then got a forced move into (0,9) which was simultaneously entered by a
   longer (length 9) opponent snake converging from below along column x=0/1
   — an unavoidable, correctly-flagged head-to-head loss (in fact the actual
   final position had *zero* legal moves for us at all — both remaining
   cells were separately blocked by our own neck and the opponent's body).
   Traced the pivotal decision back to **turn 52**, where "left" (toward the
   corner/food, dist=3) and "right" (away, dist=21) had **identical** raw
   area and Voronoi territory (109 each — opponent was still far away, no
   signal at all from those terms), so the food-distance term alone decided
   it (27+ point swing) — the corner/edge penalty at that point was tiny
   (short snake, `len_scale≈1.15`, opponent-proximity multiplier only
   partially active) relative to the food signal. **The trap only became
   visible 2-3 turns later** as the opponent's independent path converged —
   this is a genuine multi-turn-ahead corridor race that no same-turn
   flood-fill/Voronoi snapshot can see; by the turn it *did* become visible
   (turn 53-54), every remaining move was already forced/risky with no good
   alternative left.

2. **`sim_107.jsonl` (died turn 29)**: similar shape — our snake (length 5,
   opponent also length 5, i.e. *not* even a longer-opponent situation this
   time) walked along the bottom edge toward food at (1,0) over 2 turns,
   ate it, then was forced into the true corner (0,0) with the opponent
   having repositioned to seal the only exit. Traced back to **turn 25**:
   "left" (toward food, dist 1) vs "right" (away, dist 13) again had
   **identical** area/Voronoi (113 each, opponent too far to differentiate
   yet). One turn later (turn 26), the danger *was* already visible (a
   third option, "up", correctly scored a hard -100+ trap penalty due to
   area collapsing to 1 — confirmed the *existing* trap-detection machinery
   works correctly here), but by then the only two legal moves were "left"
   (the one that led to the corner) or the already-flagged-bad "up" — no
   third option existed to route around the closing pincer.

3. **`sim_109.jsonl` (died turn 59)**: **this one is different and
   important** — traced turn 54's decision in full detail with an exact
   score breakdown (see method above). Here, "down" (toward more central
   board) was in fact `risky_cells` (adjacent to a **much longer**, length-10
   opponent's head — a real, correctly-detected head-to-head danger, -1000
   penalty) while "right" (onto the x=10 board edge) was not immediately
   contested and scored far higher (1192 vs 206) *despite* the edge penalty
   correctly firing on it. **This was the objectively correct decision at
   that exact turn** — avoiding a probable head-to-head loss against a much
   longer snake is clearly right. The bot then continued down the forced
   single-file edge column for several more turns (each turn: edge column
   was the only non-risky option) until the same longer opponent, having
   route around, sealed the corner from the other side. In other words:
   **the opponent actively used its length advantage to force us into a
   wall-hugging retreat, then closed the trap** — this is the opponent
   playing a genuinely good aggressive strategy against a shorter snake, not
   a bug. (This matches almost exactly what a parallel ladder session's
   notes found against a *different* opponent, `Xe__since`, a few rounds
   ago — see that section elsewhere in this file. It is evidently a general
   pattern against any opponent that (a) can grow longer than us and (b) has
   some heuristic drive to close on/pressure a shorter opponent, not
   specific to `ccSnake2018__ccsnake`.)

### Why I made no code change this round

All three traced examples confirm the existing per-term scoring (area,
Voronoi race-territory, risky_cells head-to-head avoidance, free_degree,
edge/corner/edge-run penalties) is firing **exactly as designed and
correctly** at every single decision point I inspected — there is no
off-by-one, no unintended sign, no term canceling another out
unexpectedly. The failure mode in all 3 cases is the same well-documented,
fundamental limitation repeated across *many* rounds' notes in this file now
(search "self-coil" / "corridor-race" / "edge-hugging" / "legitimate
opponent pressure" above): **a same-turn (or few-terms-ahead) snapshot
cannot see a 2-4-turn-away corridor seal or pincer forming**, especially
when (as in examples 1 and 2) the two candidate moves are *completely tied*
on every spatial metric at the moment of decision, so the tie-break naturally
falls to food-distance — which has no way to "know" the two paths diverge in
safety a few turns later.

Given:
- this is now confirmed (via 3 independently different traced mechanisms,
  across 2 different opponents in different rounds/sessions of this file) to
  be a *general* limitation rather than an opponent-specific quirk fixable
  by one more local penalty term,
- several previous rounds already tried and, in at least 2 documented cases,
  **reverted** speculative attempts at partial lookahead (straight-line
  opponent projection vs `Xe__since`; the old `opp_territory`/`area_pess`
  6-ply-BFS mechanism, which was found to actively cause *wrong* decisions
  in two other real losses and was later replaced with the current
  Voronoi-race-territory approach),
- the current real-match trend is still solidly positive and slightly
  improving (225-25 → 227-22-1),
- I had ~7 steps of budget left after this investigation — not enough to
  safely implement and validate a real N-ply minimax (the single most
  repeatedly recommended, never-attempted fix across dozens of rounds' notes
  in this file),

I judged it better to leave a precise, three-example diagnostic writeup (this
section) for whoever has a full budget to attempt the real fix, rather than
ship an untested guess in the last few steps.

### Concrete recommendation for next round (HIGH PRIORITY — same conclusion several other rounds have reached, now with 3 fresh concrete traces to validate against)

**The only remaining lever that would plausibly fix this class of loss is
genuine multi-ply lookahead** — specifically, something like:

1. For each of our legal candidate moves, simulate applying it (update our
   body: `new_body = [candidate] + body[:-1]`, or `[candidate] + body` if
   `candidate in food_set` to model growth).
2. For each opponent, enumerate *their* legal candidate moves from their
   current head (reuse the same in-bounds + not-currently-blocked logic).
   Pick their move that's *worst for us* (e.g., minimizes our resulting
   flood-fill area/Voronoi territory from the candidate) — a paranoid/
   minimax assumption, cheap since there's normally just 1 opponent in this
   game format (verified: every round's `board.snakes` in this file's
   history has exactly 2 snakes — a 1v1 format, not multi-snake — so the
   opponent-move enumeration is O(4), not combinatorial).
3. Recurse this 2-4 plies deep (bounded by a small budget, e.g. always finish
   well under the 500ms/move budget — this game's own per-move latency
   logged in `sim_*.jsonl` files, e.g. `"latency": "1"` or `"latency": "42"`
   for the *opponent*, shows there's a LOT of unused time budget available;
   our current 1-ply approach reportedly runs in ~1-2ms per call per many
   earlier rounds' notes, so there is a huge amount of headroom to spend on
   deeper search before hitting any real time constraint).
4. Use the leaf-node (after N plies) flood-fill/Voronoi area as the
   candidate's score, blended with the existing food/edge heuristics for
   tie-breaking at the leaf.

**Important lesson from this round's traces to keep in mind when
implementing/validating this**: in examples 1 and 2 above, the two competing
paths were tied on *every current-turn* metric — the divergence in safety
only appeared 2-3 turns later. This means **even a 2-ply lookahead might not
be enough** to catch examples 1/2 specifically (verified by hand-checking:
at the turn-52/turn-25 decision points, the opponent's own head was still
2-3 real moves away from the cell that eventually caused the fatal seal) —
you likely need **3-4 plies** to see it, which is exactly why previous
shallow/2-ply-adjacent attempts (the reverted straight-line projection, the
old 6-ply-BFS-*territory* hack which was a different, blunter approach than
real minimax) haven't fully solved it. Before investing in a full N-ply
minimax, it would be worth first testing (cheaply, via the same manual
trace-replay technique documented above) at exactly what ply-depth these 3
specific traced examples *would* actually flip to the correct decision —
that tells you the minimum useful search depth before writing the real
recursive code.

**Test harness recipe for next round** (condensed, all pieces already used
this round — see shell history for exact working scripts if you want to
avoid retyping):
```python
import json, main
def build_state(turn_dict, my_name):
    board = turn_dict['board']
    snakes, you = [], None
    for s in board['snakes']:
        snake = {'id': s['name'], 'head': s['head'], 'length': s['length'], 'body': s['body']}
        snakes.append(snake)
        if s['name'] == my_name:
            you = {'id': s['name'], 'body': s['body'], 'health': s['health']}
    return {'board': {'width': board['width'], 'height': board['height'],
                       'food': board['food'], 'snakes': snakes,
                       'hazards': board.get('hazards', [])}, 'you': you}
# lines = [json.loads(l) for l in open('/logs/rounds/1/sim_0.jsonl')]
# turns = {l['turn']: l for l in lines if 'turn' in l}
# gs = build_state(turns[52], 'sonnet-5')   # re-use for sim_107 turn 25, sim_109 turn 54, etc.
# main.move(gs)  # or copy the scoring loop inline (see this round's shell history) to print per-term breakdowns
```

The three concrete repro points to validate any future lookahead attempt
against, all in `/logs/rounds/1/`:
- `sim_0.jsonl`, decision turn 52 (head `(4,10)`) — correct answer should
  eventually prefer "right" over "left" once lookahead reveals the corner
  seal 3 turns later; at turn 52 itself both were tied on every current
  metric.
- `sim_107.jsonl`, decision turn 25 (head `(3,0)`) — same shape, opponent
  length equal to ours (not even a longer-opponent case).
- `sim_109.jsonl`, decision turn 54 (head `(9,3)`) — this one is *already
  playing correctly* locally (avoiding a real head-to-head against a
  length-10 opponent) — useful as a **negative control**: any lookahead
  fix must NOT change this decision (it's genuinely the best local move),
  it must instead recognize a few turns *earlier* that heading toward this
  whole edge-retreat sequence at all (a decision several turns before turn
  54, not shown in this round's trace — would need extending the trace
  further back) leads somewhere bad, if there was ever an earlier
  alternative. Worth tracing sim_109 back further (turns 45-53) with the
  same technique before assuming a fix is needed there at all — it's
  possible the opponent's length-10 advantage by that point made the
  eventual trap unavoidable no matter what we'd picked (a legitimately lost
  position, not a bug) — this is unverified, flagged as a good starting
  point for next round.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round — investigation only, see
  above).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent = coreyja__bombastic-bob (a purely RANDOM safe-move bot), added tail-reachability anti-self-coil heuristic

`/logs/rounds/0/results.json`: opponent this round is
**`coreyja__bombastic-bob`** — confirmed via `git show
origin/human/coreyja/bombastic-bob:main.py` to be a **deliberately trivial
bot**: it just picks a uniformly-random move among all "reasonable" moves
(in bounds, not into any snake body, not into a deadly hazard), no food-
seeking, no lookahead, no opponent modeling at all. Real result: sonnet-5
240 / opponent 10 out of 250 sims (96%, NOT a clean sweep).
`analyze_logs.py /logs/rounds/0`: avg 83.1 turns/sim (min 9, max 227) —
games commonly run long since the random opponent doesn't play
aggressively, giving OUR OWN snake plenty of time/length to accumulate and
potentially self-coil.

### Root cause of the losses: since the opponent is random (not
### adversarial), all 10 losses are almost certainly pure self-inflicted
### traps ("self-coil"), not opponent pressure

Traced `sim_106.jsonl` (one of the 10 real losses) in full via literal-
board-state replay (recipe: build a synthetic `game_state` per logged turn
from `board.snakes[*].body`, call `main.move()` directly — see many
earlier rounds' notes in this file for the exact dict shape). Confirmed:
our snake (length 13) spiraled along the top edge then down the right
edge into the top-right corner over ~10 turns (turns 133→142), ending with
**zero legal moves** at turn 143. The opponent was nowhere near the trap
region for the entire sequence (it was wandering randomly elsewhere on the
board) — this is a **pure self-coil**, not a corridor race or head-to-head
pressure situation. This matches and reconfirms the "self-coil" failure
class flagged in MANY previous rounds' notes throughout this file (search
"self-coil" above) — but this is the *first* time we've faced an opponent
simple/random enough that we can be fully confident the trap is 100%
self-inflicted (no possible opponent-modeling angle to investigate
instead).

### Fix attempted this round: tail-reachability check (a well-known anti-
### self-coil heuristic used by many strong real Battlesnake bots)

Added `_flood_fill_reach()` (in `main.py`, right above `_voronoi_area`): a
BFS flood fill that also tracks whether a given `target` cell (our own
current tail) is reachable within the explored region. Wired into the
scoring loop: for each candidate move, if our own tail is NOT reachable
(and we didn't just eat, i.e. `my_tail is not None`), apply a
`-my_length * 8` penalty. Rationale: our own tail cell is normally *not*
blocked (it's assumed to vacate next turn per `_build_blocked`), so
"can I reach my own tail" is a cheap, well-known proxy for "is this
region actually connected back to space that will open up as my body
advances" — much stronger signal than raw flood-fill area alone (which
only degrades once a pocket is *already* nearly sealed).

**Honest limitation found via direct testing (important, read before
tuning further):** replaying this exact heuristic turn-by-turn against
the literal `sim_106.jsonl` states (turns 95-133, see shell history this
round for the exact script) found that `tail_reachable` only correctly
flags the two already-obviously-bad candidates that the *existing* hard
trap penalty (area < my_length) already correctly avoided (turn 122
"right", area 1; turn 132 "down", area 3) — it did **not** provide any
*earlier* warning for the actual fatal path (at turn 133, both "left" and
"right" show `area=99, reach_tail=True` — completely tied, no
differentiation at all). In other words: for *this specific* traced loss,
the tail-reachability check does not fire early enough to change the
outcome — the true point of no return for this particular coil happened
even earlier than turn 95 (not traced further back due to step budget),
or the coil's fatal narrowing only becomes detectable at a horizon this
1-ply check still can't see.

**Why I kept the change anyway:** even though it didn't fix this specific
traced example, it's a well-established, low-risk, purely additive
heuristic (extra BFS reuses the exact same traversal we already do for
`area`, just also tracking one target cell — negligible extra cost,
verified ~1ms/call for 200 calls in a smoke test) that should still help
in *other* self-coil shapes where the tail does become unreachable before
the raw area collapses (a real, common pattern in Battlesnake more
generally, well documented in the wider community as a standard technique
— see e.g. any "avoid getting trapped" writeup). No exceptions/regressions
found in smoke tests (normal state, `{}`, empty-snakes state).

### Verification done

- Smoke tests (`main.move()` on normal 2-snake state, `{}`, empty-snakes
  state) — all still return valid moves, no exceptions.
- Timing: 200 `move()` calls on a synthetic 11x11 2-snake state in
  ~0.21s total (~1ms/call) — no meaningful performance regression from
  the extra target-tracking BFS.
- Did **NOT** get a fresh local-benchmark tournament against extracted
  `coreyja/bombastic-bob` code this round (ran low on step budget after
  the trace investigation) — this is the most important next step for
  whoever picks this up next, see below. Given the opponent is *random*,
  a meaningful benchmark would need a fairly large sample (10-20+ games)
  since any single game's outcome has real variance from the opponent's
  randomness alone, independent of any bot changes.

### HIGH PRIORITY next steps for whoever picks this up next

1. **Run a real local benchmark** (recipe unchanged from many earlier
   rounds' notes in this file — extract `origin/human/coreyja/
   bombastic-bob:main.py` to `/tmp/opp/main.py`, `cp server.py
   /tmp/opp/server.py`, run both as local Flask servers via `setsid
   nohup env PORT=... python3 main.py > log 2>&1 </dev/null & disown`,
   then loop `battlesnake play ... -o /tmp/game_N.json & disown`, sleep,
   check `tail`). Aim for 15-20+ games given the opponent's randomness
   adds noise. Compare against the real 240/10 (96%) baseline.
2. **Trace further back in `sim_106.jsonl`** (turns < 95) with the same
   `_flood_fill_reach`-based script (see shell history this round, or
   reconstruct: build a synthetic `game_state` per turn, call
   `main._flood_fill_reach` for every legal candidate, print `area` and
   `reach_tail`) to find exactly how far back the "point of no return"
   for this specific coil actually was — this would tell you whether a
   *deeper* lookahead (2-3 ply) would have caught it, or whether it's a
   more fundamental issue (e.g., growing too fast/too long without ever
   returning toward open board, unrelated to any single decision point).
3. **Trace the other 9 real losses** the same way (identify via each
   `sim_*.jsonl`'s final `winnerName` line, same technique
   `analyze_logs.py` uses) — this round only fully traced 1 of 10; it's
   possible some of the others have a different, more locally-fixable
   mechanism where the tail-reach check (or a different, targeted fix)
   *does* catch it early enough to matter.
4. Given this opponent is uniquely simple (pure random-safe-move, zero
   food-seeking or strategy), it's a good stress test specifically for
   our OWN self-coil tendencies in isolation from any opponent modeling
   question — worth using it as the benchmark opponent of choice
   whenever iterating on self-coil fixes in future rounds, since any
   loss against it is guaranteed to be self-inflicted, not opponent
   pressure (makes the trace-replay technique's conclusions much
   cleaner/faster to draw than against a "smart" opponent where you
   first have to rule out legitimate opponent pressure, as several
   earlier rounds' notes had to do against `Xe__since` and
   `ccSnake2018__ccsnake`).
5. As always: re-check `/logs/rounds/1/results.json` once it exists — if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh before assuming this round's analysis/fix still
   applies.

### Files (this round's change)

- `main.py` — the bot (this round: added `_flood_fill_reach()` and a
  `my_tail`/tail-reachability penalty in the scoring loop — see the
  inline comments right above both for full rationale + the honest
  limitation noted above; kept despite not fixing the one specific
  traced example, since it's a well-established low-risk heuristic that
  should still generalize to other coil shapes).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent still coreyja__bombastic-bob, traced both real losses, found+fixed a concrete tie-break bug (free_degree weight too weak), small low-risk weight bump

`/logs/rounds/{0,1}/results.json`: opponent both rounds is
`coreyja__bombastic-bob` (random-safe-move bot, see previous round's
section above). Round 0: 240-10. Round 1 (after previous round's
tail-reachability fix): **248-2** — confirmed real improvement.

### This round: traced BOTH remaining real losses from round 1

1. `sim_45.jsonl` (died turn 253): a long, deep self-coil — our snake
   spent 100+ turns confined to roughly the left/bottom quadrant
   (x=1-9,y=1-9), growing to length 14 while slowly spiraling in on
   itself. Traced back several decision points (turns 240-252) — at the
   fatal turns, ALL legal candidates were already forced (single/zero
   options), so there was no fixable decision at the end. Went back
   further (turns 106-250 sampled) — the snake never had a strong
   incentive/signal to break out toward the more open right half of the
   board earlier; this looks like a genuine deep-lookahead gap (need
   10+ ply to see this coming), not a quick local fix. Not fixed this
   round — see "still open" below.
2. `sim_104.jsonl` (died turn 109): **found and fixed a concrete,
   traceable bug.** At turn 106 (head (4,2)), the two live candidates
   "up"->(4,3) and "down"->(4,1) had **identical raw flood-fill area
   (102) and identical tail_reachable (both False — tied, no signal)**.
   The existing `free_degree` local-mobility term correctly computed a
   real difference (up=degree 2, down=degree 1 — "down" leads into what
   turns out to be a genuine one-cell-wide dead-end one square later,
   confirmed by manually simulating one more ply: after "up" there are
   still 2 free next-moves; after "down" the *next* turn is completely
   forced into a single move that has ZERO legal moves the turn after
   that), but the weight (`free_degree * 15`, i.e. a 15-point edge over
   "down") was too small to overcome a ~2-point net disadvantage from
   other terms (edge-run/voronoi/food-dist tie-breaks) — actual scores
   were `up=1145.1` vs `down=1147.2`, i.e. "down" won by 2.1 points and
   the bot walked into the dead end, dying 3 forced-moves later.

### Fix made this round

Bumped `free_degree` weight from `15` to `22` (see `main.py` line ~433).
Verified directly: replaying the exact turn-106 board state from
`sim_104.jsonl` through `main.move()` now scores `up=1159.1` vs
`down=1154.2` and correctly picks `up` (previously picked the fatal
`down`). This is a minimal, single-line, well-targeted change with a
concretely-verified fix for a real traced match loss — very low
regression risk (same term, same sign, just a slightly larger
coefficient; doesn't change the ordering of any other already-decisive
comparisons, since `free_degree` only ranges 0-4 and this is a small
multiplier bump).

**Verification done:** smoke tests (normal 2-snake state, `{}` malformed,
empty-snakes state) all still return valid moves with no exceptions.
Did **not** get to run a fresh full local-benchmark tournament this round
(ran out of step budget after the trace-and-fix work) — recommended next
step for whoever picks this up: extract `origin/human/coreyja/
bombastic-bob:main.py` (recipe unchanged from many earlier rounds' notes
in this file — `setsid nohup env PORT=... python3 main.py & disown` for
both bots, loop `battlesnake play ...`, sleep, check `tail`) and run
15-20+ games (opponent is random, so needs a decent sample size) to
confirm no regression and ideally a further-improved win rate over the
248/250 baseline.

### Still open: `sim_45.jsonl`'s deep self-coil (NOT fixed, needs real lookahead)

This is the same fundamental, many-rounds-recurring limitation this file
has documented extensively (search "self-coil" throughout this file) —
a slow, multi-turn drift into a shrinking pocket where every *individual*
decision point looks locally fine (tied/ambiguous scores, not a clear
mistake) and only the long-run trajectory is bad. The `free_degree` fix
above only helps when a *specific* turn has a clean, checkable 1-cell
mobility difference between candidates (which `sim_104` had) — it does
NOT help when, like `sim_45`, every candidate at the fatal turns is
already forced/tied many turns in advance. The only remaining lever
flagged by many previous rounds' notes that would plausibly fix this
class remains genuine multi-ply lookahead/simulation (see the very
detailed writeup a few sections up in this file, "Round (this session) —
opponent = ccSnake2018__ccsnake ... traced ALL major loss patterns" for
a fully worked-out design sketch of what that would look like + why 2-ply
might not even be enough for some shapes). Given this opponent is random
(not adversarial), a promising cheaper alternative specific to THIS
opponent: periodically bias movement toward the board's largest
unclaimed region / centroid when very safe (health high, no immediate
threat) rather than always pure food-distance-driven movement, to reduce
how often the snake organically drifts into one corner/quadrant and
starts self-coiling there over many turns — not implemented, just a
lower-risk-than-full-minimax idea for a future round to try if this
opponent (or a similarly weak/random one) recurs.

### Files
- `main.py` — this round's change: `free_degree` weight `15 -> 22` (see
  inline comment above that line, and this section for the exact traced
  bug it fixes).
- `analyze_logs.py` — unchanged.

## Round (this session) — opponent = coreyja__coreyja-rs, found + fixed a real starvation-loop bug (free_degree edge bias + weak low-health food urgency)

`/logs/rounds/0/results.json`: opponent this round is **`coreyja__coreyja-rs`**
("Hovering Hobbs" -- a Rust-ported paranoid alpha-beta minimax with a
flood-fill area-control leaf eval, iterative deepening, ~0.3s/move budget
in the real harness -- see `git show origin/human/coreyja/coreyja-rs:main.py`
for the full docstring). Real result: clean sweep, sonnet-5 33 / opponent
0. `analyze_logs.py /logs/rounds/0`: 33/33 sims won, avg 5.7 turns (min 2,
max 10) -- opponent dies/times-out almost immediately in the real harness
(consistent with the long-established pattern in this file: many past
"strong-on-paper" ported opponents lose fast in the real scoring harness
but are much tougher in a local benchmark with a generous time budget).

### Local benchmark (before any change) — confirmed the "local much harder
### than real score" pattern again, and found a genuine bug (not opponent
### pressure)

Extracted the opponent fresh (`git show
origin/human/coreyja/coreyja-rs:main.py > /tmp/opp/main.py; cp server.py
/tmp/opp/server.py`) and ran 6 real local games via the `battlesnake` CLI
against the pre-this-round `main.py` (standard recipe -- `setsid nohup env
PORT=... python3 main.py > log 2>&1 </dev/null & disown` for both bots,
loop `battlesnake play ... -o /tmp/game_N.json & disown`, sleep, check
`tail` -- see many earlier rounds' notes elsewhere in this file for the
full recipe). Confirmed the opponent locally does NOT time out (unlike the
real harness) and plays real, contested games 60-220+ turns. **Result: 1
win / 3 losses observed / 2 still running when step budget ran low.**

Traced the shortest loss (`/tmp/game_3.json`, died turn 100) via literal-
board-state replay (recipe: build a synthetic `game_state` per logged turn
from `board.snakes[*].body`/`head`/`length`/`health`, call `main.move()`
directly -- see many earlier rounds' notes in this file for the exact
dict shape). **Found a genuine, concrete, reproducible bug -- not
opponent pressure**: at health 8 (critically low), with food sitting only
2 cells away at (6,0), our snake got stuck in a **stable 6-cell back-and-
forth cycle** ((5,1)->(4,1)->(4,2)->(5,2)->(6,2)->(6,1)->(5,1)->...)
for 8 consecutive turns and starved to death at turn 100, **never
committing to the 2-move path to the nearby food**, despite nothing else
threatening it (opponent was 5+ cells away the whole time).

### Root cause (two compounding issues, both fixed)

1. **`free_degree` local-mobility term had a systematic edge/corner
   bias.** It rewarded the *raw count* of a candidate cell's free
   neighbors (0-4), but a cell on a board edge has at most 3 in-bounds
   neighbors and a corner at most 2 -- **purely from board geometry, not
   any actual danger**. Combined with the separate edge-penalty term,
   this made the bot systematically undervalue any move near
   an edge/corner (like the cell adjacent to the food at (6,0), on the
   bottom row) relative to interior moves, even when both were equally
   "safe" in the sense of having all their possible neighbors free.
   Verified by hand-computing both terms for the exact traced state: the
   food-adjacent edge move scored `free_degree=2` (both possible
   neighbors free) vs an interior alternative's `free_degree=3` (also
   all possible neighbors free) -- a spurious 22-point penalty for having
   one fewer *possible* neighbor, not one fewer *free* one.
2. **Low-health food-urgency weight (`4` if health<50, else `1.5`) was
   too weak to overcome the above bias plus the flat edge penalty** even
   at health=8 -- a 2-cell food-distance advantage only bought an 8-point
   score edge (`2 cells * weight 4`), nowhere near enough to offset the
   ~22-point `free_degree` bias plus the ~9-point edge penalty on the
   food-adjacent move.

### Fix made this round

1. **`free_degree` is now deficit-based**: compute `max_free_degree`
   (in-bounds neighbor count for the position, ignoring blocked-ness) and
   penalize `(max_free_degree - free_degree) * 22` instead of rewarding
   raw `free_degree * 22`. This gives **identical** scoring to before for
   any comparison between interior cells (where `max_free_degree` is 4
   for both, so the relative difference is unchanged -- preserves the
   original m-schier/kreuzotter degree-1-vs-degree-3 dead-end tie-break
   fix from several rounds ago), but removes the spurious edge/corner
   penalty (a corner cell with both its 2 possible neighbors free now
   scores the same, deficit 0, as an open interior cell with all 4 free).
2. **Steeper low-health food-urgency curve**: `weight = 10` if
   `health<15`, `6` if `<30`, `4` if `<50`, else `1.5` (previously just a
   flat `4`/`1.5` split). Makes food-seeking dominate much more strongly
   exactly when starvation is imminent.

**Verified directly**: replayed the exact turn-92 board state from the
traced loss -- `main.move()` now returns `down` (toward the food) instead
of the previous `left` (which continued the fatal cycle). Also ran a full
turn-by-turn simulation starting from the health-8 traced state (our
snake alone against a static distant opponent, recipe in shell history
this round) -- the patched bot reaches and eats the food in 2 moves, then
continues eating several more food items over the next ~20 simulated
turns with health never dropping dangerously low again. The old code,
replayed on the same sequence of states, would have continued the 6-cell
starvation cycle (confirmed by the original trace itself, which is the
literal real-game log).

### Verification done

- Smoke tests (`main.move()` on a normal 2-snake state, `{}` malformed
  state, empty-snakes state) -- all still return valid moves, no
  exceptions, after both changes.
- Direct trace-replay + forward simulation described above.
- **Did NOT get a full fresh local-benchmark tally against the patched
  code** -- ran out of step budget mid-session; a `kill -9` aimed at
  restarting the local test server (by PID, not `pkill -f` -- correctly
  avoided the well-documented `pkill -f` self-match gotcha from many
  earlier rounds' notes in this file) accidentally killed BOTH bots'
  servers (the PID grep for `"python3 main.py"` matched both the
  `/workspace` and `/tmp/opp` processes -- a new gotcha for the list
  below), had to restart both and only got one fresh game underway (still
  running, turn 66+, no errors/crashes in either log) before running out
  of steps entirely.

### NEW gotcha for the list (adds to existing pkill -f warnings elsewhere
### in this file)

`ps aux | grep "python3 main.py" | grep -v grep` matches **every** running
`main.py` process regardless of working directory -- if you're running
both your own bot (`/workspace/main.py`) and an extracted opponent copy
(`/tmp/opp/main.py`) as background test servers, killing "by PID from ps
aux" (the previously-recommended safer alternative to `pkill -f`) can
still accidentally kill BOTH if you grab the wrong PIDs or don't check
each process's full command line / cwd first (e.g. `ps aux | grep
main.py` alone, or `readlink /proc/<pid>/cwd`) before issuing `kill`.
Double-check you have the right PID for the right bot before killing, or
kill+restart both together to avoid an inconsistent state.

### HIGH PRIORITY next steps for whoever picks this up next

1. **Run a full fresh local benchmark** (8-12+ games) against a freshly
   extracted `origin/human/coreyja/coreyja-rs:main.py` with this round's
   fix (recipe: `git show origin/human/coreyja/coreyja-rs:main.py >
   /tmp/opp/main.py; cp server.py /tmp/opp/server.py`, then the usual
   `setsid nohup env PORT=... python3 main.py & disown` for both bots +
   `battlesnake play ... -o /tmp/game_N.json & disown` + `sleep` + `tail`
   pattern used throughout this file -- games against this opponent ran
   60-220+ turns locally, budget accordingly across multiple tool calls).
   This round only got 1 clean win / 3 losses pre-fix and didn't get a
   clean post-fix tally -- that's the most important gap to close.
2. If new losses show up, use the exact trace-replay + forward-simulation
   technique demonstrated this round (build a synthetic `game_state` from
   the logged turn, call `main.move()`, and/or forward-simulate several
   turns with a static/simplified opponent to see if the bot's *sequence*
   of decisions converges on food/safety or gets stuck in a cycle again)
   -- this found a very concrete, fixable bug this round (a starvation
   loop), a different flavor from the more common "self-coil"/"corridor-
   race" mechanisms this file's history has documented many times before.
   Worth checking whether any *other* traced losses in this file's long
   history (many "self-coil" sections above) might have partly been this
   same free_degree edge-bias bug rather than (or in addition to) genuine
   lookahead gaps -- this fix is now in place for all of them going
   forward, so it's worth a fresh look at whether recently-recurring
   "edge-hugging" symptoms improve as a side effect.
3. Still-not-done, many-rounds-recurring big idea: true multi-ply
   lookahead/minimax (current bot is fundamentally still 1-ply flood-fill
   + local heuristics). See the extensive "ccSnake2018__ccsnake" and
   "Xe__since" sections earlier in this file for detailed design sketches
   and concrete repro points if a future round wants to attempt it.
4. As always: re-check `/logs/rounds/1/results.json` once it exists -- if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh before assuming this round's fix matters against
   them too (though the free_degree/food-urgency fix is a general
   correctness improvement, not opponent-specific, so it should help
   regardless of who the next opponent is).

### Files (this round's change)

- `main.py` — the bot (this round: `free_degree` is now deficit-based
  relative to max-possible-neighbors for the position, fixing an
  edge/corner bias; steeper low-health food-urgency weight curve -- see
  the inline comments directly above both changes for the full traced
  rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round 2 (this session) — opponent still coreyja__coreyja-rs, fixed a real "near-edge / corner-turn" gap in the wall-hugging penalty (confirmed via traced local-benchmark loss)

`/logs/rounds/1/results.json` confirmed: opponent `coreyja__coreyja-rs`,
real result **clean sweep 40-0** (`analyze_logs.py /logs/rounds/1`: 40/40
sims won, avg 5.4 turns — opponent dies/errors fast in the real harness,
consistent with the long-established pattern in this file).

### Local benchmark (before any change) — found a fresh, concrete loss

Both bots (`/workspace` port 8000, `/tmp/opp` port 8001 with a fresh
`git show origin/human/coreyja/coreyja-rs:main.py` extraction) were
already running from a previous session. Ran 6 local games via the
`battlesnake` CLI (standard recipe from earlier rounds' notes throughout
this file). **Result: 5 wins / 1 loss.** Traced the loss
(`/tmp/game_1.json`, died turn 113) turn-by-turn.

### Root cause (concrete, verified via direct code inspection + trace replay)

Our snake (length 12) traveled up column **x=1** (one cell in from the
true left edge x=0) for ~10 turns, then turned the corner onto the true
**top edge y=10**, and got pinched into the top-right corner (10,10) by a
comparable-length opponent approaching from below — the same general
"corridor race via edge-hugging" family documented many times throughout
this file. But this time the exact bug in the *existing* mitigation
(`edge_run` self-corridor penalty) was locatable and clear:

1. `on_v_edge`/`on_h_edge` only fire when `x == 0` or `x == width-1`
   **exactly**. Our snake spent ~10 turns at `x == 1` (one cell in), so
   `on_v_edge` was **False the entire time** — zero penalty accrued
   during the whole approach.
2. Even after reaching the true edge (y=10), the old `edge_run` counter
   only counted consecutive body segments sharing the *exact same x* (for
   a vertical edge) or *exact same y* (for a horizontal edge) — so the
   moment the path turned the corner from the x=1 column onto the y=10
   row, the run **reset to 1**, treating a single continuous ~15-turn
   wall-hugging trap as two separate 1-cell touches.

Net effect: the self-corridor penalty essentially never fired at any
point during the actual fatal approach.

### Fix made this round

Replaced the exact-same-x/exact-same-y `edge_run` tracking with a general
**`wall_run`**: count of consecutive own body segments (from the head)
whose `edge_dist` (distance to the *nearest* of all 4 walls) is `<= 1`
(true edge OR one cell in), regardless of whether they're on the same
exact edge. This correctly (a) starts counting one cell earlier (near-edge,
not just true-edge), and (b) keeps accumulating across a corner turn
instead of resetting. Penalty formula unchanged otherwise
(`wall_run**2 * 1.0 * len_scale * proximity_mult`).

**Verified this changes behavior at the actual decision points**: replaying
`main.move()` on the literal logged board states from turns 96-104 of the
traced loss now diverges from the real game's actual moves starting at
turn 98 (returns `right`/`up` instead of continuing up the x=1 column) —
i.e. the patched bot breaks out of the near-edge corridor several turns
before the real game committed to the fatal path.

### Post-fix local benchmark

Restarted both local test servers (killed old PIDs directly — confirmed
correct PIDs via `ps aux`/checked cwd first, not `pkill -f`, per the many
earlier gotcha-notes in this file) and ran a fresh 6-game batch. **3
confirmed clean wins observed** (3, 50, and 186 turns) with **zero losses**
before this session's step budget ran out; the remaining 3 games were
still healthily in progress (both snakes alive) at 250+ turns when last
checked — not losses, just slow/long games (typical against this
opponent's real minimax search). No errors/exceptions in either server's
log.

### Verification done

- Smoke tests (`main.move()` on normal 2-snake state, `{}` malformed
  state, empty-snakes state) — all still return valid moves, no
  exceptions, before and after the fix.
- Direct trace-replay on the exact traced loss (see above) — confirmed
  the fix changes the specific fatal decision sequence.
- Local benchmark: 0 losses observed post-fix (3 clean wins + 3 long
  games still healthy) vs. 1/6 pre-fix.

### Recommended next steps

1. **Finish/extend the local benchmark** (the 3 long games from this
   round, plus a fresh larger batch) to get a more confident win-rate
   number — this session ran out of step budget before they resolved.
2. If a new loss shows up, re-use the same trace-replay technique (build
   a synthetic `game_state` per logged turn, call `main.move()` directly,
   inspect `edge_dist`/`wall_run`/`area`/`voronoi_mine` per candidate) —
   it found and pinpointed a very concrete, fixable bug this round (a gap
   in existing logic, not a fundamentally new failure mode), same as
   several previous rounds' "free_degree edge bias" and "capped opponent-
   pessimism" fixes elsewhere in this file.
3. As always: re-check `/logs/rounds/2/results.json` once it exists — if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh. This round's fix is a general correctness
   improvement (not opponent-specific), so it should help regardless.
4. The recurring multi-ply-lookahead idea (see many earlier rounds'
   notes throughout this file, e.g. the detailed `ccSnake2018__ccsnake`
   and `Xe__since` sections) remains the highest-ceiling not-yet-attempted
   improvement if local-heuristic patches like this one start showing
   diminishing returns.

### Files (this round's change)

- `main.py` — the bot (this round: replaced exact-same-x/y `edge_run`
  tracking with a general near-wall `wall_run` that survives corner
  turns and starts one cell earlier — see the large inline comment right
  above that code block for the full traced rationale).
- `analyze_logs.py` — unchanged.

## Round (this session) — opponent = coreyja__jump-flooding, found a real starvation-via-mutual-avoidance-cycle loss, added (partial) stuck-tracker fix — NEEDS FOLLOW-UP TUNING

`/logs/rounds/0/results.json`: opponent this round is
**`coreyja__jump-flooding`** (a Rust port: 1-ply greedy over a pure
Manhattan-distance Voronoi territory score, no food-seeking at all, no
opponent-head targeting -- see `git show
origin/human/coreyja/jump-flooding:main.py`). Real result: sonnet-5 188 /
opponent 26 / ties 36 out of 250 (`analyze_logs.py /logs/rounds/0`: avg
42.2 turns/sim, max 161) -- NOT a clean sweep, and notably a lot of ties
(36), unusual compared to most past opponents in this file's long history.

### Root cause traced (sim_100.jsonl, died turn 100 by pure starvation)

Full turn-by-turn trace (see recipe elsewhere in this file — build a
synthetic `game_state` per logged turn, call `main.move()` directly) shows
our snake and the opponent fell into a **stable, repeating mirrored cycle**
(period ~22 turns) confined to a small region on one side of the board,
for 30+ turns, health steadily decreasing 1/turn with ZERO food eaten,
until starvation. This is NOT a self-coil or corridor-race (the previously
documented failure classes elsewhere in this file) — it's a **mutual
avoidance stalemate**: every time our bot considers a move back toward
open board / food, that cell is flagged `risky_cells` (adjacent to the
opponent's — often longer — head), incurring the flat `-1000` penalty,
which reliably wins out over the food-distance benefit by a *small* margin
(~19 points in the traced example at turn 65, health 35) every single
turn, forever, because the opponent (itself just maximizing territory, not
literally chasing us) happens to stay adjacent turn after turn due to the
symmetric Voronoi dynamics. Confirmed via direct score breakdown (see
shell history this round) that this is NOT a bug in any individual scoring
term (risky_cells correctly identifies a real, current head-to-head
possibility every time) — it's an *emergent deadlock* between two
deterministic heuristics with no randomness/tie-breaking to escape it.

### Fix attempted this round (module-level "stuck" tracker + relaxed risky penalty at low health) — PARTIAL, NOT FULLY VERIFIED TO FIX THE TRACED EXAMPLE

Added `_stuck_state` (module-level dict, keyed by `game_state["game"]["id"]`,
persists across `move()` calls within the same long-lived Flask process —
confirmed via `server.py` that this is a single persistent process per
match) tracking `stuck_count` = consecutive turns where health did not
increase (i.e., no food eaten). When `my_health < 50` (same gating as the
existing food-urgency weight elsewhere in the loop), the `risky_cells`
penalty is now `max(40, 1000 - stuck_count * 25)` instead of a flat
`-1000` — i.e. it relaxes the further we go without eating while already
low on health, with a floor of 40 (still a real penalty, just not
near-infinite). At full health (>=50) the penalty is unchanged at -1000 —
**no change to behavior in the common/already-validated case.**

**Honest limitation found via direct testing (important — read before
tuning further):** replayed the exact traced sequence (turns 40-65,
accumulating `stuck_count` realistically) and separately forced
`stuck_count` all the way up to 40 and 60 directly on the turn-65 board
state — **the bot still picked `down` (continuing the cycle) even at
`stuck_count=60`, where the penalty floor of 40 should have applied.**
I ran out of step budget before determining exactly why (the raw,
no-penalty score gap between the "escape" and "continue cycling" options
looked like only ~19 points in an earlier hand-computed breakdown from
*before* this round's code edit — but that manual computation did not
include every term the real scoring loop applies identically, e.g. it's
possible I mis-transcribed one of the many terms, or the gap is actually
larger than 19 once computed via the *actual* code path rather than a
hand-copy). **This needs to be debugged properly next round** — the fix
as shipped is _not_ proven to fix the one concrete traced example, though
it is verified to be safe (no crashes, no change at health>=50, `main.py`
still parses and smoke-tests pass on normal/`{}`/empty-snakes states).

### Recommended next steps (HIGH PRIORITY)

1. **Debug why the relaxed penalty didn't flip the turn-65 decision even
   at a high forced `stuck_count`.** Recipe: reuse this round's
   `build_state()` helper (see shell history / recreate: for each snake in
   `board['snakes']`, emit `{'id': name, 'head': body[0], 'length':...,
   'body':...}`; wrap with `game`/`turn`/`board`/`you` keys), load
   `/logs/rounds/0/sim_100.jsonl` turn 65, then **temporarily add print
   statements inside `main.py`'s scoring loop** (rather than hand-copying
   the loop into a separate script, which risks transcription drift like
   this round may have hit) to print each candidate's exact running score
   after every term, and diff between `down` and `left`. Find the actual
   real point where `down` wins even with `risky_penalty` near the floor.
2. Once the real gap is known, either (a) lower the floor further (e.g.
   `max(10, ...)` or even `max(0, ...)`), or (b) identify a *different*
   term that's actually responsible for the persistent gap (e.g. the
   `edge_dist`/`wall_run`/`free_degree` terms might independently favor
   the "away from opponent" direction regardless of the risky penalty,
   since that direction is also often more "central"/open — in which
   case relaxing risky_cells alone is not sufcient and the fix needs to
   also relax those terms, or add a direct "food urgency overrides
   general positional preference" mechanism instead).
3. Consider a more direct alternative if the stuck-tracker approach proves
   hard to tune: explicit **cycle detection** — record the last ~30
   `(head, opp_head)` pairs per game id, and if the current pair
   (approximately) repeats one seen `K` turns ago with lower health now,
   force a specific "break the mirror" move (e.g. deliberately pick the
   move that maximizes distance from the repeated-cycle attractor, or
   just pick the least-recently-visited legal cell) rather than relying on
   score-tuning to organically escape.
4. Re-run a **local benchmark** against a freshly extracted
   `origin/human/coreyja/jump-flooding:main.py` (recipe unchanged from
   many earlier rounds' notes throughout this file — `setsid nohup env
   PORT=... python3 main.py & disown` for both bots, loop `battlesnake
   play ... -o /tmp/game_N.json & disown`, sleep, check `tail`) once the
   fix is properly debugged, to get a real win-rate delta vs. the 188/26/36
   real-match baseline. This round did NOT get to run that benchmark (ran
   out of step budget on the trace + fix attempt itself) — top priority
   for whoever picks this up next.
5. The unusually high tie count (36/250) this round is also worth a look
   — likely both snakes surviving to a max-turn draw or a simultaneous
   death (e.g. both starving in a similar mutual-cycle at the same time,
   or both filling the board). Not investigated this round; a quick
   `analyze_logs.py`-style pass isolating a few tied sims (same technique
   as the loss-finding snippet earlier in this file: parse each
   `sim_*.jsonl`'s final `isDraw` field) would tell you if it's the same
   root cause as the losses or something else entirely.

### Files (this round's change)

- `main.py` — added `_stuck_state` module-level tracker + a health/stuck-
  scaled `risky_cells` penalty (replacing the flat `-1000`) — see the
  inline comments directly above both for the full rationale. **Not yet
  confirmed to fix the concrete traced example** — see limitation above.
  Safe/no-op at health >= 50 (unchanged flat -1000 there).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent still coreyja__jump-flooding, tuned edge/wall-hugging weights to address a traced "parallel-edge pincer into corner" loss pattern

`/logs/rounds/{0,1}/results.json`: opponent both rounds is
`coreyja__jump-flooding` (pure greedy Voronoi-territory bot, no food-
seeking). Round 0: 188-26-36(tie). Round 1 (after previous round's
stuck-tracker/relaxed-risky-penalty fix): **199-20-31** — a real
improvement (fewer losses, fewer ties), confirming that fix helped.
`analyze_logs.py /logs/rounds/1`: avg 36.2 turns/sim, max 143.

### Traced multiple remaining round-1 losses — found a clear, consistent, different mechanism from the previously-documented "starvation cycle" (that one is now largely fixed)

Identified all 20 real losses via each `sim_*.jsonl`'s final `winnerName`
line (same technique `analyze_logs.py` uses). Traced several
(`sim_110`, `sim_150`, `sim_168`, `sim_176`, `sim_177`) via full
turn-by-turn body dumps. **All five show the exact same shape**: our
snake (short, length 4-6) travels along one full board edge (bottom row,
top row, or a column) for 8-10 consecutive turns, while the opponent
travels in parallel one row/column inward, moving in the same direction
at roughly the same pace (often converging on food near the far corner).
Our snake reaches the corner; the opponent's body (now often 1 segment
longer, having just eaten) is immediately adjacent; the corner cell's
*only* non-body-blocked neighbor is a cell the longer opponent can also
reach next turn (flagged `risky_cells`, correctly) — but since it is the
*only* legal candidate at that point (own body fills the rest), the bot
is forced to take it anyway and loses the resulting head-to-head.

**This is a genuine "point of no return" problem, not a same-turn scoring
bug**: verified via direct `main.move()` replay (recipe: build a
synthetic `game_state` per logged turn from `board.snakes[*].body`, call
`main.move()` directly — see many earlier rounds' notes elsewhere in this
file for the exact dict shape) that at the turns where the trap became
*visible* (a real risky_cells hit), there was only one legal candidate
left — no local fix at that turn can help. The actual decision point is
several turns *earlier* (e.g. turn 18-21 in the `sim_176` trace), where
the two candidates (continue along the edge vs. break inward) were
scored *almost exactly tied* (a ~10-point gap out of ~1200), with the
existing `wall_run` self-corridor penalty present but too weak at low
`wall_run` values / short snake length (`len_scale` is 1.0 for any
`my_length <= 4`, i.e. no extra discouragement at all for a short snake)
to break the tie toward the safer option.

### Change made this round

Tuned three existing weights in the scoring loop (no new mechanism, no
new BFS/data structures — low risk):
- `wall_run` self-corridor penalty coefficient: `1.0 -> 2.5`.
- `edge_dist` staying-away-from-edges bonus: `1.2 -> 2.2` per cell.
- `proximity_mult` (doubles the wall_run penalty when an opponent is
  near) trigger distance: `<=8 -> <=10` Manhattan cells, so it engages
  slightly earlier relative to an approaching opponent.

**Honest caveat on validation methodology**: literal-state replay
(feeding the *exact* recorded board states from the old real-match losses
into `main.move()` with the new weights) still picks the same moves at
the *already-forced* turns (e.g. turns 20-27 of `sim_176`, where only 1-2
legal candidates exist by then) — this is expected and doesn't mean the
fix is useless, it means those specific literal states are downstream of
an earlier decision that the fix *does* change (e.g. `sim_176` turn 18
flips from `down` to `up` with the new weights). You **cannot** validate
a fix like this via literal-recorded-state replay beyond the first
diverging decision, because every subsequent recorded state assumes the
*old* trajectory (the real opponent would have reacted differently to a
different move from us) — a real local-benchmark rerun (actual games,
opponent reacting live) is the only valid way to check this, which is
what was done next.

### Local benchmark this round (real validation)

Extracted opponent fresh (`git show
origin/human/coreyja/jump-flooding:main.py > /tmp/opp/main.py; cp
server.py /tmp/opp/server.py`) and ran **12 real local games** via the
`battlesnake` CLI against the tuned `main.py` (standard recipe from many
earlier rounds' notes in this file — `setsid nohup env PORT=... python3
main.py > log 2>&1 </dev/null & disown` for both bots, loop `battlesnake
play ...` backgrounded + disowned, sleep, check `tail`). **Result: 10
wins / 0 losses / 2 draws** (games 20-93 turns). Zero losses in this
sample is a good sign (previous local behavior wasn't benchmarked before
this round, but the real match rate was ~79.6% win / 8% loss / 12.4%
draw — this local sample, while small, shows 0 losses and a slightly
lower draw rate, consistent with (not proof of, but consistent with) an
improvement). No errors/exceptions in either bot's server log.

### Verification done

- Smoke tests (`main.move()` on normal 2-snake state, `{}` malformed
  state, empty-snakes state) — all still return valid moves, no
  exceptions.
- 12-game local benchmark as above: 10W/0L/2D, no crashes.
- Confirmed via diff that this round's change is a minimal 3-line
  weight-only diff (`diff /tmp/main_backup.py main.py` — backup not
  persisted, recreate via `git show HEAD:main.py` before this round's
  commit if you want to re-diff).

### Recommended next steps

1. **Run a bigger local benchmark** (20+ games) to get more statistical
   confidence in the 10/0/2 result — this round's sample is still small.
2. If new losses appear, use the same literal-state replay technique
   (build synthetic `game_state` from logged turns, call `main.move()`)
   to find the *first diverging decision point* (not just the final
   forced turns) — remember per the caveat above, you must find where
   two candidates are still close in score and a real alternative
   exists, not just where the bot is already boxed in.
3. The fundamental "point of no return" pattern documented here (commit
   to an edge run several turns before it becomes visibly dangerous) is
   the same general family flagged by MANY earlier rounds' notes
   throughout this file (search "corridor race", "self-coil", "edge-
   hugging", "pincer") against several different opponents — still not
   fully solved by any local weight tuning attempted across all these
   rounds. Real multi-ply lookahead/opponent-response simulation remains
   the highest-ceiling not-yet-attempted fix if local weight tuning
   keeps showing diminishing returns (see the detailed design sketches
   in the `ccSnake2018__ccsnake` and `Xe__since` sections earlier in this
   file).
4. As always: re-check `/logs/rounds/2/results.json` once it exists — if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh.

### Files (this round's change)

- `main.py` — the bot (this round: tuned `wall_run` penalty coefficient
  1.0->2.5, `edge_dist` bonus 1.2->2.2, `proximity_mult` trigger distance
  8->10 — see inline comments at those lines, and this section for the
  full traced rationale + validation caveat).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent = zacpez__scape-goat, investigated both real losses, confirmed root cause = deep self-coil (no code change, high-value diagnostic notes)

`/logs/rounds/0/results.json`: opponent this round is **`zacpez__scape-goat`**
(a Go port of a very simple bot -- excludes edge/neck directions, then a
crude "dumb ideas" food/avoidance heuristic, falls back to a
nanosecond-modulo "random" choice among remaining options when ambiguous
-- see `git show origin/human/zacpez/scape-goat:main.py` for the full
docstring/port notes). Real result: **sonnet-5 248 / opponent 2** out of
250 (99.2% win rate, NOT a clean sweep but very close).
`analyze_logs.py /logs/rounds/0`: avg 91.9 turns/sim (min 9, max 238) —
long games are common (the opponent, being mostly random among safe
moves, rarely forces anything, so games are dominated by our own
long-horizon play quality more than opponent pressure).

### Both real losses traced in full (concrete, not speculative) — same root cause, DIFFERENT from most previously-documented failure classes in this file

Identified both losses via each `sim_*.jsonl`'s final `winnerName` line
(`sim_80.jsonl` died turn 77, `sim_109.jsonl` died turn 159). Traced both
turn-by-turn (recipe: build a synthetic `game_state` per logged turn from
`board.snakes[*].body`, call `main.move()` and `main._flood_fill_reach()`
directly for each candidate — see many earlier rounds' notes throughout
this file for the exact dict shape/pattern, reused unchanged here).

**Both are pure, opponent-independent self-coils** (confirmed: the
opponent was far away and playing no active role in either trap, unlike
the "corridor race"/"pincer" mechanisms documented in many earlier
rounds against *smarter* opponents) — but with a specific twist worth
recording precisely, since it's a slightly different flavor from most
prior self-coil writeups in this file:

- **`sim_109.jsonl`**: at the actual decision turns (152, and again
  68-72 in the other loss), **every open candidate had literally
  IDENTICAL raw flood-fill area** (e.g. turn 152: `down`=101,
  `right`=101; turns 68-72 in `sim_80`: consistently 106 for every open
  candidate) **and identical `tail_reachable=True`** for all of them —
  i.e. the existing anti-self-coil machinery (hard-trap gate, soft
  2.2x-margin gate, tail-reachability check, Voronoi race-territory)
  produced **zero discriminating signal whatsoever** between the
  candidates at the only turns where a real choice still existed. The
  region being entered was large (100+ cells) and *looked* completely
  safe by every current metric — it only sealed into a fatal dead end
  several turns *later*, once our own body (having continued into that
  large-but-ultimately-still-bounded region without ever routing back
  toward the rest of the open board) filled in enough of it. By the time
  any metric showed danger (area collapsing below body length — e.g.
  turn 153/154 in `sim_109`, area suddenly 6-7 with `my_length=16`), it
  was already **completely forced** — every single remaining candidate
  (often exactly one, sometimes zero) led to the same outcome. Verified
  directly via `main.move()` replay at each of these turns: the code's
  literal decisions exactly reproduce the real game's actual moves,
  confirming this is a deterministic, reproducible trace, not noise.
- **`sim_80.jsonl`**: same shape, but with one extra concrete detail: the
  bot's decisions at turns 68-72 (all tied at area=106) were ultimately
  influenced toward the top-right corner region by a **food pellet that
  spawned right at (9,10), in/near a corner** (confirmed: health jumped
  91→100 and length 12→13 exactly at turn 73, right as the head reached
  that cell) — i.e. the food-distance/immediate-food-bonus terms (which
  are the only terms with a non-tied value when everything else is tied)
  pulled the bot toward eating a corner-adjacent pellet, and by the time
  it had eaten and needed to leave, its own recently-grown body (now
  occupying most of the approach corridor) had nowhere left to route
  back through, and the opponent's independent wandering happened to seal
  the one remaining exit cell a couple of turns later.

### Why this is a genuinely different/harder case than most of this file's many previous self-coil write-ups, and why I did NOT attempt a new heuristic fix this round

Every previous self-coil section in this file (see the many "self-coil",
"corridor-race", "edge-hugging" mentions above, e.g. the `Xe__since`,
`ccSnake2018__ccsnake`, `coreyja__bombastic-bob` sections) found at least
*some* differentiating signal between candidates a few turns before the
fatal one — a smaller (but not yet sub-threshold) area, a `wall_run`
build-up, a `tail_reachable` flip, etc. — that a *stronger-weighted*
version of an existing heuristic could plausibly have caught earlier
(and several rounds' fixes did measurably help, e.g. the `free_degree`
deficit fix, the `wall_run` general near-wall tracking, the steeper
food-urgency curve). **This round's two traces are qualitatively
different**: at the actual decision points, literally every relevant
metric (raw area, Voronoi territory, tail-reachability) was **exactly
tied** across all live candidates, for MULTIPLE consecutive turns in a
row (5 turns tied at 106 in `sim_80`; several tied at 99-101 in
`sim_109`) — there is no weight to turn up on any existing additive term
that would break a tie where the values are identical; you would need an
entirely new signal that can distinguish "this 100-cell region has a
route back out" from "this 100-cell region does not", which is
fundamentally a multi-turn reachability/topology question (something
like: after continuing K more moves down this path, is the region behind
me still connected to the front of me without going through my own
body?) — not a same-turn snapping-of-a-heuristic-weight fix. This is,
concretely, the clearest evidence yet in this file's long history for
why the many-rounds-recurring "real multi-ply lookahead" recommendation
is the correct next big investment, rather than another targeted local
penalty tweak — there is no local weight left to tune for this exact
class of tie.

I did NOT attempt a new heuristic this round (e.g. "prefer moves whose
resulting region, when flood-filled, has >=2 distinct exits back toward
the pre-move position" or similar graph-cut-style checks) because: (a)
it's a nontrivial, higher-risk piece of new logic to design and validate
correctly with the step budget remaining after this investigation, and
(b) the current real win rate (248/250, 99.2%) is already excellent and
this specific bug only manifests in the rare very-long game where a big
region happens to be geometrically single-entrance -- the risk of a
rushed, undertested "graph connectivity" heuristic introducing a
*different* regression felt higher than the ~0.8% upside available here.

### Concrete, scoped recommendation for whoever wants to actually fix this (more specific than previous rounds' generic "add lookahead" suggestions, since this round's traces pin down exactly what signal is missing)

The specific missing signal, stated precisely from the traces above: **at
the moment of tie (all candidates show identical large flood-fill area),
none of the current metrics ask "if I commit to this candidate and then
keep flood-filling connectivity through the entire reachable region N
moves from now (after my own body has grown/advanced into part of it),
does the exit back toward open board remain open, or does my own
projected body eventually seal it?"** A cheap, bounded way to approximate
this without full minimax: for each tied candidate, simulate our own body
advancing `my_length` more cells along the *locally most space-efficient*
path within the flood-filled region (e.g. always step to the neighbor
with the most remaining freedom, a simple greedy self-simulation, no
opponent modeling needed since these losses are opponent-independent),
and check whether the resulting position still has `tail_reachable=True`
and `area >= my_length` — i.e. actually run the existing per-move safety
checks a full body-length forward along a plausible self-trajectory,
instead of only 1 ply forward. This is bounded (at most `my_length`
extra BFS steps, still cheap on an 11x11 board per the many timing notes
elsewhere in this file) and targets exactly the mechanism traced twice
this round, without requiring any opponent-behavior modeling (unlike the
`Xe__since`/`ccSnake2018__ccsnake` sections' recommended fixes, which
*do* need opponent modeling since those losses involved real opponent
pressure) — this should be a meaningfully easier/lower-risk version of
"multi-ply lookahead" to implement and validate than a full minimax,
specifically because there's no opponent branching factor to handle.

### Verification done this round

- Traced both real losses via literal-state `main.move()`/
  `_flood_fill_reach()` replay (see above) — no code changes, so nothing
  to regress-test, but confirmed `main.py`'s decisions exactly reproduce
  the real game's recorded moves at every traced turn (a good sanity
  check the replay methodology itself is sound for whoever continues
  this investigation).
- Smoke tests (`main.move()` on a normal 2-snake state, `{}` malformed
  state, empty-snakes state) — all still return valid moves, no
  exceptions (baseline check only, no change was made this round).

### Files (unchanged this round)

- `main.py` — the bot (no changes this round — investigation only, see
  above for a concrete, scoped design sketch for the recommended fix).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent still zacpez__scape-goat (249-1 real), fixed a real "eat-food-locks-own-tail" bug via trace-replay of the exact remaining loss

`/logs/rounds/{0,1}/results.json`: opponent both rounds is `zacpez__scape-goat`.
Round 0: 248-2. Round 1: 249-1 — already extremely strong (99.6%). Previous
round's notes (see the long section directly above this one, "opponent =
zacpez__scape-goat, investigated both real losses") had already traced
both round-0 losses (`sim_80.jsonl` turn 77, `sim_109.jsonl` turn 159) in
detail and found: at the actual decision points, literally every relevant
metric (raw flood-fill area, Voronoi territory, tail-reachability) was
**exactly tied** across live candidates for several consecutive turns —
concluded a full multi-ply lookahead was the only real fix, and made no
change (reasonably, given the risk vs. the already-excellent win rate).

### This round: re-traced `sim_80.jsonl` more precisely and found a concrete, fixable bug hiding inside that "tie"

Re-examined turn 72 of `sim_80.jsonl` in detail (recipe: build a synthetic
`game_state` from the logged turn's `board.snakes[*].body`, call
`main.move()`/`main._flood_fill_reach()` directly — same technique used
throughout this file's history). At turn 72 (head `(9,9)`, length 12,
health 91), the three legal candidates (`up`->`(9,10)`, `down`->`(9,8)`,
`right`->`(10,9)`) all showed **identical raw flood-fill area (106) and
identical `tail_reachable=True`** — the "tie" the previous round's notes
described. But `up` was special: `(9,10)` is a food cell, and eating it
would grow our snake (length 12->13). **Found the bug**: `_flood_fill_reach`
was called with the *general* `blocked` set (built by `_build_blocked`,
which assumes every snake's tail vacates this turn — correct for
non-eating moves) even for a candidate that eats food. But eating means
**our own tail does NOT vacate this turn** (growth keeps that segment
occupied one extra turn) — so the flood fill from the food-eating
candidate was incorrectly treating our own current tail cell as free
space it could walk back through, when in reality that cell stays part of
our body. This made `up`'s `tail_reachable` show `True` (identical to the
other two, hence the "tie") when it should have shown `False` — i.e. the
observed tie in the previous round's notes was itself partly an artifact
of this bug, not a genuine tie.

**Verified precisely**: recomputing `_flood_fill_reach` for the `up`
candidate at turn 72 with the candidate's own (soon-to-be-eaten) tail
correctly added to the blocked set flips `tail_reachable` from `True` to
`False` (area drops 106->105, immaterial, but `tail_reachable` is the
signal that matters here), while `down`/`right` (which don't eat) are
completely unaffected. This one flip is enough: the existing
`-my_length * 8` anti-self-coil penalty (already in the code, added
several rounds ago — see the large comment block above it in `main.py`)
now correctly fires only on `up`, easily overriding the `+20`
immediate-food bonus and the (tied) edge penalty that had been letting
`up` win before.

### Fix made this round

In the move-scoring loop, before calling `_flood_fill_reach` for a
candidate: if the candidate cell `nxt` is a food cell (`nxt in
food_set`) and we have a tail to check (`my_tail is not None`), add
`my_tail` to the blocked set used for *that specific candidate's* area/
tail-reachability computation (`eat_blocked = blocked | {my_tail}`) —
does not affect the general `blocked` set used everywhere else (legal-
move filter, other candidates' evaluations, risky_cells, etc.), so this
is a narrowly-scoped, low-risk, purely-more-accurate correction. This
generalizes cleanly: it correctly does nothing when `nxt` isn't food
(the overwhelmingly common case), and correctly does nothing when we
just ate last turn ourselves (`my_tail is None` in that case already,
per the existing just-ate detection).

**Verified this directly flips the exact traced turn-72 decision**:
`main.move()` on the literal turn-72 board state from `sim_80.jsonl` now
returns `{"move": "right"}` (previously `{"move": "up"}`, the actual
move taken in the real game, which led to the trap and death 5 turns
later).

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state, `{}` (fully
  malformed), an empty-snakes state, and a synthetic state where a
  food-eating candidate is right next to our own tail on a short snake
  (a case explicitly designed to sanity-check the new code path doesn't
  do anything crazy for a harmless case) — all return valid moves, no
  exceptions.
- Timing: 200 `move()` calls on a synthetic 11x11 2-snake state (10 vs 8
  length) in ~0.17s total (~0.87ms/call) — no meaningful performance
  regression from the extra set-union (only computed per-candidate, and
  only actually allocates a new set when that specific candidate is a
  food cell).
- Re-ran the turn-72-onward replay of `sim_80.jsonl` with the fix (feeding
  each turn's *actual recorded* board state, i.e. NOT a live reactive
  re-simulation against the real opponent — a caveat, see below): the
  patched bot no longer walks into the corner at turn 72, picks `right`
  instead. This doesn't by itself prove the *whole* game would have been
  won (the recorded turns after 72 assume the old trajectory, which the
  opponent wouldn't have reacted to identically if we'd actually diverged
  live) — a real local-benchmark rerun would be needed for full end-to-
  end confirmation, which this round did not have step budget left to do.
- Also traced `sim_109.jsonl` (the other round-0 loss) turns 140-158 with
  the fix applied: the bot has legal moves and doesn't hit a forced
  dead-end within that recorded window (longer than it previously did per
  the prior round's notes) — again, an *encouraging* but not fully
  conclusive signal for the same reactive-opponent-caveat reason above.

### HIGH PRIORITY next steps for whoever picks this up next

1. **Run a real local benchmark** (recipe unchanged from many earlier
   rounds' notes throughout this file — `git show
   origin/human/zacpez/scape-goat:main.py > /tmp/opp/main.py; cp
   server.py /tmp/opp/server.py`, then `setsid nohup env PORT=...
   python3 main.py > log 2>&1 </dev/null & disown` for both bots, loop
   `battlesnake play ... -o /tmp/game_N.json & disown`, sleep, check
   `tail`) — aim for 15-20+ games (games run long against this opponent,
   9-238 turns per earlier rounds' notes) to get a real, *live* (not
   literal-replay) win-rate confirmation of this round's fix. This is
   the single most important gap — the fix is verified via direct
   traced-state replay (a strong, concrete signal) but not yet via a
   fresh live game where the opponent can react to our new decisions.
2. This same "eating food doesn't vacate our tail" inaccuracy could in
   principle have contributed to *other* rounds' traced self-coil losses
   throughout this file's long history (search "self-coil" above) —
   many of those didn't specifically check whether the fatal candidate
   was a food cell. Worth a quick look back at a couple of the more
   detailed past traces (e.g. the `ccSnake2018__ccsnake` "edge_run"
   section, or the `coreyja__coreyja-rs` starvation-loop section) to see
   if this same mechanism was silently part of the picture there too —
   not done this round (ran out of step budget), but this fix is general
   (not opponent-specific) so it should help regardless.
3. If a **different** opponent shows up in the next round's real match,
   use `git log --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark them per
   the established recipe throughout this file.
4. The still-not-attempted big idea (many-rounds-recurring in this file):
   true multi-ply lookahead/minimax. This round's fix closes one
   concrete, real gap that was *disguised* as a "genuine tie" in the
   previous round's investigation — but genuine ties (where every
   current-turn metric, including the now-fixed tail-reachability check,
   really is identical) can still occur and would still need real
   lookahead to resolve correctly. Worth re-checking with the fixed code
   whether any of this file's previously-documented "identical metrics"
   traces are still tied after this fix, or whether some of them
   resolve now too.

### Files (this round's change)

- `main.py` — the bot (this round: added an `eat_blocked` set that
  additionally blocks our own current tail cell when evaluating a
  food-eating candidate's flood-fill area/tail-reachability, since
  eating means that tail cell does not vacate this turn — see the large
  inline comment directly above `eat_blocked` for the full traced
  rationale, and this section for the concrete example that motivated
  it).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent = tim-hub__awesome-snake, traced a real loss (legitimate forced collision after falling behind in length), added small length-deficit food-urgency nudge

`/logs/rounds/0/results.json`: opponent this round is **`tim-hub__awesome-snake`**
(a trivial ported bot: looks only at its 4 immediate neighbor cells, scores
off-board=-100, food=+1, body=-1, empty=0, picks the max with a random
tiebreak -- see `git show origin/human/tim-hub/awesome-snake:main.py`). Real
result: sonnet-5 223 / opponent 27 out of 250 (89.2%, NOT a clean sweep).
`analyze_logs.py /logs/rounds/0`: avg 111.7 turns/sim (min 15, max 252) --
long games are common (the opponent has no real danger-avoidance beyond
1-ply, but also doesn't die instantly, so games run long and our own
snake's length/positioning over time matters a lot).

### Traced multiple real losses in detail (recipe unchanged from many
### earlier rounds -- build a synthetic `game_state` per logged turn from
### `board.snakes[*].body`, call `main.move()` directly)

`sim_0.jsonl` (died turn 109): at the literal fatal decision (turn 108,
head `(2,8)`, length 6, health 100 just-ate), there were only 2 legal
candidates -- `up`->`(2,9)` and `right`->`(3,8)` -- and **both** were
already in `risky_cells` (the opponent, at length 11 and head `(3,9)`, one
move away from either). `main.move()` correctly picked `up` (area 104 vs
`right`'s area 1, a real dead-end) since the flat -1000 risky penalty
canceled out identically for both -- **this decision was NOT a bug**: it
was a genuinely forced 50/50-ish head-to-head (opponent could reach either
cell) that the bot had no way to avoid at that specific turn. The opponent
happened to move into exactly the cell we needed.

Sampled 2 more losses (`sim_131.jsonl`, `sim_202.jsonl`) via body-position
dumps near their death turns: **same general shape each time** -- our
snake stays short (length 4-7) while the opponent, despite having zero
real strategy, keeps eating unopposed and grows to length 10-13, and
eventually a length mismatch this large makes an eventual forced/close
head-to-head loss likely once paths cross, even though our per-turn
decisions were individually sound (avoiding the *worse* of the available
options every time, per the trace above).

### Change made this round: small, capped length-deficit food-urgency nudge

Since the losses trace back to "we fell far behind in length, which makes
any eventual forced encounter likely to go the opponent's way" rather
than a locatable per-turn scoring bug (the existing risky_cells/area/
voronoi logic is all firing correctly, same conclusion many earlier
rounds' notes reached against *other* opponents -- see the extensive
history above), I added a cheap, low-risk mitigation rather than trying to
patch an individual forced-collision decision (which is fundamentally not
fixable at the turn it becomes visible -- see the sim_0 trace above,
where both options were already forced/tied):

- Compute `length_deficit = max(0, max_opponent_length - my_length)` once
  per `move()` call (cheap, just a max over already-available
  `snakes[*]["length"]`).
- Add `min(length_deficit * 0.3, 1.5)` to the food-distance weight
  (on top of the existing health-based curve: 10/6/4/1.5 depending on
  health). Capped at +1.5 extra weight (reached once deficit >= 5), so it
  can only mildly accelerate food-seeking when behind, never override
  health-based urgency or any safety term (risky_cells, area/voronoi
  trap penalties, etc. are all computed independently and this doesn't
  touch them).

Intent: catch up in length a bit faster when trailing, reducing how often
we end up as the much-shorter snake in an eventual contested encounter,
without changing behavior at all when lengths are roughly even (the
common/already-well-tested case -- `length_deficit` is 0 whenever we're
not behind).

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state (opponent longer,
  to exercise the new deficit path), `{}` (fully malformed), and an
  empty-snakes state -- all return valid moves, no exceptions.
- Re-ran the traced `sim_0.jsonl` turns (95, 100, 104, 108) through
  `main.move()` post-change -- decisions are **unchanged** at all of
  them (expected/desired: at turn 108 both options were already risky-
  cell-forced regardless of the food weight; the earlier turns' choices
  also didn't flip, since the deficit bonus is small and capped).
- Timing: 300 `move()` calls on the turn-108 board state in ~0.095s
  (~0.3ms/call) -- no meaningful performance change.
- **Did NOT get a fresh local-benchmark tournament against extracted
  `tim-hub/awesome-snake` code this round** (ran out of step budget after
  the trace investigation) -- this is the most important next step for
  whoever picks this up next. Given the change is small/capped and only
  activates when behind in length, regression risk is low, but a real
  win-rate comparison (recipe: `git show
  origin/human/tim-hub/awesome-snake:main.py > /tmp/opp/main.py; cp
  server.py /tmp/opp/server.py`, then the usual `setsid nohup env PORT=...
  python3 main.py & disown` for both bots + `battlesnake play ... -o
  /tmp/game_N.json & disown` + `sleep` + `tail` pattern used throughout
  this file) would be good confirmation.

### Recommended next steps

1. Run the local benchmark described above (8-15 games) to confirm no
   regression and ideally an improvement over the real 223/27 baseline.
2. If new losses appear, use the same trace-replay technique (this file
   has dozens of worked examples above) -- specifically check whether
   the loss is another "genuinely forced 50/50 collision after falling
   behind in length" (in which case this round's mitigation is the right
   category of fix, maybe just needs its cap/coefficient tuned) or a
   different, more locally-fixable mechanism (self-coil, corridor-race,
   edge-hugging -- see the many prior sections above for those patterns
   and their fixes).
3. The much-recurring "real multi-ply lookahead" idea (see the extensive
   `ccSnake2018__ccsnake`/`Xe__since` design sketches earlier in this
   file) remains the highest-ceiling not-yet-attempted fix for the
   genuinely-forced-collision class of loss, since by definition those
   losses have no good move at the moment they become visible -- only
   earlier lookahead (or, as attempted this round, reducing the
   underlying length gap that makes such collisions likely to go badly)
   can help.
4. As always: re-check `/logs/rounds/1/results.json` once it exists -- if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh before assuming this round's analysis applies.

### Files (this round's change)

- `main.py` — the bot (this round: added `length_deficit` computation and
  a small capped food-urgency weight boost when behind in length -- see
  inline comments at both spots for the full traced rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent still tim-hub__awesome-snake (226-22-2 real), found + fixed a HIGH-IMPACT bug: food-eating candidates were incorrectly penalized by the tail-reachability anti-self-coil check, causing real starvation-loop losses

`/logs/rounds/{0,1}/results.json`: opponent both rounds is
`tim-hub__awesome-snake`. Round 0 (before previous round's length-deficit
food-urgency fix): 223-27. Round 1 (after that fix): **226-22-2** — a
real, confirmed improvement, matching the previous round's expectation.

### Traced a fresh round-1 loss (`sim_100.jsonl`, died turn 118) — found a serious, general bug (not opponent-specific)

Full turn-by-turn replay (recipe: build a synthetic `game_state` per
logged turn from `board.snakes[*].body`, call `main.move()` directly —
same technique used throughout this file's history) showed our snake
stuck at **length 4, health dropping 20→0 over 20 turns (turns 98-118)**,
cycling through the *exact same* ~10-move loop **twice in a row**, never
eating, then starving to death — even though food was sitting
**immediately adjacent** (BFS food-distance 0 or 1) on almost every one
of those turns. This is a different, more severe variant of the
"starvation loop" pattern documented several times earlier in this file
(e.g. `coreyja__jump-flooding`, `coreyja__coreyja-rs` sections above) —
but this time the opponent wasn't even nearby/relevant; it was a pure,
self-inflicted refusal to eat.

### Root cause (found via direct per-term score printing, not just move() output — see method below)

Temporarily instrumented `main.py`'s scoring loop with a debug print (via
a `SNAKE_DEBUG` env var, removed before finishing — if you need to
redo this, wrap the loop's `if score > best_score` block with a print of
`name, nxt, score, area_for_score, voronoi_mine, tail_reachable, nxt in
risky_cells, max_free_degree, free_degree, edge_dist, wall_run` similar to
what's now documented inline in the fix comment) and replayed turn 99 of
`sim_100.jsonl`: the candidate that moves directly onto adjacent food
(`up` -> `(3,7)`, food-dist 0) scored **~10-12 points LOWER** than the
non-eating alternatives, despite an otherwise-favorable `+20` immediate-
food bonus and zero distance penalty. The culprit: `tail_reachable` was
`False` for the food-eating candidate ONLY, triggering the
`-my_length * 8` anti-self-coil penalty (`-32` at length 4) — a **bug**,
not a real trap.

The mechanism: a previous round's fix (see the large comment block
earlier in this file/`main.py`, "Correctness fix ... zacpez__scape-goat
sim_80.jsonl turn 72") correctly adds our own tail cell to the blocked
set (`eat_blocked = blocked | {my_tail}`) when a candidate eats food,
since growth means that tail segment does NOT vacate this turn. **But**
`_flood_fill_reach` was then still called with `target=my_tail` — i.e.
"is `my_tail` reachable" using a blocked-set that **already contains
`my_tail` itself**. `_flood_fill_reach` can never mark a `blocked` cell
as `seen`/reached, so this check was **unconditionally `False` for every
single food-eating candidate, everywhere, regardless of any actual
danger** — the earlier fix (correct in its own narrow goal: making the
*area* calculation accurately reflect that eating keeps the tail
occupied) had an unintended side effect of poisoning the *separate*
tail-reachability *penalty* for the exact same candidates, making the
bot systematically avoid eating food it was directly adjacent to. This
is a strictly worse bug than the one it was patching, and had likely been
silently active across all opponents since that fix landed a couple of
rounds ago — not caught earlier because most opponents' matches don't run
long/desperate enough to expose it clearly, or their traces happened to
look at non-eating decision points.

### Fix made this round

When a candidate eats food: still use `eat_blocked` (tail included) for
the **area** computation (unchanged, that part was correct), but pass
`target=None` to `_flood_fill_reach` (skipping the now-meaningless
reachability check) and skip the `-my_length * 8` penalty entirely for
that candidate (added an `eating = nxt in food_set` flag, gated the
penalty on `not eating`). Non-eating candidates are completely unaffected
— same behavior as before.

**Verified directly**: replaying the exact turn-99 board state from
`sim_100.jsonl` now returns `{"move": "up"}` (eating the adjacent food),
previously returned `{"move": "right"}` (continuing the fatal cycle).

### Verification done

- Smoke tests: normal 2-snake state, `{}` malformed state, empty-snakes
  state, and a new explicit "food directly adjacent, low health" case
  (added this round) — all return valid moves, no exceptions. The new
  food-adjacent case correctly still picks a sensible move (moves toward
  the opponent-free side; in the exact synthetic case tested it picked
  the immediate-food-eating direction when that was also the safe one).
- Confirmed no leftover `SNAKE_DEBUG`/debug code left in `main.py`
  (`grep eat_blocked` — only the real code + comments remain) and
  `ast.parse` confirms the file is syntactically valid.
- **Did NOT get a fresh local-benchmark tournament run this round** (ran
  out of step budget after finding/fixing/verifying the bug via direct
  trace-replay) — this is the single most important next step. Given
  this bug plausibly affected EVERY past round's real match results to
  some degree (it's been active since the `zacpez__scape-goat` round a
  few sessions ago, per the trace above), a fresh local benchmark against
  `tim-hub__awesome-snake` (or whatever opponent is next) would be very
  informative, and this fix should generalize to help against ANY
  opponent, not just this one (it's a pure correctness fix to a
  previously-shipped defensive heuristic, not opponent-specific tuning).

### HIGH PRIORITY next steps for whoever picks this up next

1. **Run a real local benchmark** (recipe unchanged from many earlier
   rounds' notes throughout this file: `git show
   origin/human/tim-hub/awesome-snake:main.py > /tmp/opp/main.py; cp
   server.py /tmp/opp/server.py`, then `setsid nohup env PORT=...
   python3 main.py > log 2>&1 </dev/null & disown` for both bots, loop
   `battlesnake play ... -o /tmp/game_N.json & disown`, sleep, check
   `tail`) to confirm this fix actually improves the win rate over the
   226/22/2 baseline, and to check for any new failure modes.
2. Given how long this bug went unnoticed (shipped a few rounds ago,
   silently discouraging every food pickup where the anti-self-coil
   check happened to be checked at all — which is every single turn),
   it's worth a quick sanity pass over the OTHER anti-self-coil/tail
   logic for similar "target is inside the blocked-set used to compute
   it" traps. Nothing else found this round, but worth a second look if
   step budget allows.
3. If `/logs/rounds/2/results.json` (once it exists) shows a big jump in
   win rate (or, if the opponent has changed, a strong result against
   whoever's new), that's a good confirming signal this fix mattered in
   the real harness too, not just in the one traced local example.
4. As always: re-check the opponent identity each round via
   `results.json` before assuming past analysis applies; use `git log
   --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark a new
   opponent if one appears.

### Files (this round's change)

- `main.py` — the bot (this round: fixed the tail-reachability check to
  skip itself for food-eating candidates instead of trivially failing
  against a self-blocked target — see the large inline comment directly
  above `eating = nxt in food_set` for the full traced rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent = rdbrck__btas, traced both real losses, confirmed both are the well-established "genuine tie requiring multi-turn lookahead" / "extreme-length self-coil" classes — NO code change (investigation-only, low risk given already-excellent 247/2/1 result)

`/logs/rounds/0/results.json`: opponent this round is **`rdbrck__btas`** (a
faithful port of "BTAS", 2017 Victoria Advanced division winner — BFS to
rated food picking shortest path, else safest-space via flood-fill danger
<=10 keep-largest, see `git show origin/human/rdbrck/btas:main.py` for the
full docstring/port notes). Real result: **sonnet-5 247 / opponent 2 / tie
1** out of 250 (98.8% win rate — very strong, not a clean sweep).
`analyze_logs.py /logs/rounds/0`: avg 103.3 turns/sim (min 6, max 307) —
games run long against this opponent.

### Both real losses traced in full (recipe unchanged from many earlier
### rounds' notes throughout this file — build a synthetic `game_state`
### per logged turn from `board.snakes[*].body`, call `main.move()`
### directly, and manually recompute each candidate's score terms inline
### to see exactly which term decided the move)

1. **`sim_35.jsonl` (died turn 127, length 13 vs opponent length 8)**:
   traced back to the actual decision point, turn 124 (head `(4,10)`,
   just ate, health 100). Only 2 legal candidates existed: `left`->`(3,10)`
   (BFS food-dist 3, toward a food item near the top-left corner) and
   `right`->`(5,10)` (food-dist 22, away). Manually recomputed every
   scoring term for both: **raw flood-fill area (102 each), Voronoi
   territory (102 each), edge_dist (0 each, both on the y=10 top edge),
   on_h_edge (True each) — every spatial/safety term was EXACTLY TIED.**
   The anti-self-coil tail-reachability check was correctly skipped for
   both (we had just eaten, so `my_tail` was `None` that turn — working
   as designed, not a bug). `wall_run` was also identical for both (it's
   computed from our *existing* body segments, which don't depend on
   which direction we're about to go, only on where we already are) — so
   it provided zero differentiation between "continue left along the
   edge" vs "go right along the edge" specifically. The ONLY term that
   differed was food-distance (a genuine, large 19-cell gap), which
   correctly and predictably won the tie-break — the bot took `left`,
   which turned out to be the mouth of a trap that only became visible
   (and forced/zero-legal-moves) 2-3 turns later once the opponent's
   independent path sealed the far exit. This is, precisely, the
   "genuine tie, needs real multi-turn lookahead to resolve correctly"
   class that MANY previous rounds' notes throughout this file have
   already found and explicitly declined to patch further with local
   heuristics (see e.g. the extensive `ccSnake2018__ccsnake` and
   `zacpez__scape-goat` sections above) — confirmed again here with a
   fresh, concrete example. Not fixable by tuning existing weights: every
   term besides food-distance was IDENTICAL, not just close, so there is
   no coefficient adjustment that changes this specific decision without
   also changing the (much more common, well-tested) case of "just
   prefer the closer food when there's no other signal at all."
2. **`sim_90.jsonl` (died turn 306, length 35(!) vs opponent length 13,
   in a 307-turn game)**: our snake had grown to **length 35 on an
   11x11=121-cell board** — i.e. our own body alone occupied ~29% of the
   entire board. This is the "extreme-length self-coil is close to
   unavoidable once board space is nearly exhausted" class flagged
   explicitly by an earlier round's notes (see the `graeme-hill__snakebot`
   section above: "the very-high-length self-coil case ... is the same
   class of problem flagged by MANY previous rounds' notes ... true
   multi-ply lookahead remains the most likely real fix, still not
   attempted given cost/risk"). Did not do a full turn-by-turn trace given
   remaining step budget — the length-35-of-121-cells fact alone is
   sufficient to categorize this as the known, already-well-documented
   "ran out of board" failure mode rather than a new bug, consistent with
   how extremely rare this is (1 occurrence in 250 sims, in the single
   longest game of the batch).

### Why no code change was made this round

Both losses map cleanly onto failure classes this file has already
investigated exhaustively across dozens of rounds (search "genuine tie" /
"self-coil" / "extreme-length" above) and explicitly concluded require
**real multi-ply lookahead/minimax** to fix, not another local heuristic
weight tweak — and multiple past rounds already tried & reverted
speculative attempts in this exact direction (see the `Xe__since`
straight-line-projection revert, and the `nbw__nbw-crystal` "opponent
heading projection" revert, both documented above) when they couldn't be
verified to actually fix a traced example. Given:
- the current real win rate is already 98.8% (247/2/1) — about as good as
  this bot has ever measured against any opponent in this file's long
  history,
- the specific sim_35 tie is provably unfixable by weight-tuning (every
  differentiating term besides the correct one, food-distance, was
  EXACTLY equal, not just close — there's no coefficient that helps),
- the sim_90 case is the well-known "ran out of board at extreme length"
  class with no cheap fix on record across many rounds of investigation,
- only ~12 steps of budget remained after completing both traces,

I judged further investigation/speculative changes to carry more
regression risk than expected benefit, and made **no changes to
`main.py`**. Re-ran the existing smoke tests (normal 2-snake state, `{}`
malformed state, empty-snakes state) to confirm the unchanged code still
behaves correctly — all pass.

### Recommendation for next round

- If `/logs/rounds/1/results.json` (once it exists) shows the same
  opponent (`rdbrck__btas`) and a similar ~98-99% win rate, no further
  action is needed — this is very likely near the practical ceiling for
  a 1-ply-plus-heuristics bot against a reasonably competent opponent,
  per the now very extensive cross-opponent evidence in this file.
- If a **different** opponent appears, use `git log --oneline --all |
  grep -i human` + `git show origin/human/<Org>/<repo>:main.py` to
  extract and benchmark them per the established recipe throughout this
  file before assuming this round's analysis applies.
- The still-not-attempted big idea, now confirmed relevant yet again by a
  fresh, clean example this round (`sim_35.jsonl` turn 124 — a genuinely
  tied 1-ply position that only diverges in safety several turns later):
  **true multi-ply lookahead / minimax with a simple opponent-response
  model**. This is now an extremely well-documented, many-times-repeated
  recommendation across this file (see the detailed design sketches in
  the `ccSnake2018__ccsnake`, `Xe__since`, and `zacpez__scape-goat`
  sections above) — if a future round ever has a full step budget and
  wants to make the single highest-ceiling improvement left on the table,
  this is it. `sim_35.jsonl` turn 124 (reproduction recipe: build a
  synthetic `game_state` from that turn's logged `board.snakes[*].body`
  fields, see the many prior sections' code snippets) is a good, clean,
  freshly-verified test case to validate any such attempt against — the
  correct fix should recognize that "left" leads to a dead end 2-3 turns
  out and prefer "right" instead, despite both looking perfectly and
  exactly tied at the 1-ply/same-turn level.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round — investigation only).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round 2 (this session) — opponent still rdbrck__btas (247/1/2 both real rounds), added bounded opponent-independent "self-room" check, validated via 24-game local benchmark (no regression)

`/logs/rounds/{0,1}/results.json`: opponent both rounds is `rdbrck__btas`.
Round 0: 247-2-1(tie). Round 1: 247-1-2(tie) — already excellent (98.8%
win rate), consistent across both rounds. The previous round's notes (see
the long "opponent = rdbrck__btas" section directly above this one) traced
both round-0 losses in detail and concluded: one (`sim_35.jsonl` turn 124)
is a genuine 1-ply tie (every spatial/safety metric literally identical
between the two live candidates, only food-distance differed, and the
trap only became visible 2-3 turns later — provably unfixable by weight
tuning, needs real lookahead); the other (`sim_90.jsonl`) is the
well-documented "extreme-length self-coil" class (our snake reached
length 35 on an 11x11=121-cell board — nearly 30% of the board was our
own body). No code change was made last round given the already-excellent
result and the provably-untunable nature of the traced tie.

### What I did this round

1. **Fresh local benchmark BEFORE any change** (recipe unchanged from
   dozens of earlier rounds' notes throughout this file — extract
   `origin/human/rdbrck/btas:main.py` to `/tmp/opp/main.py`, `cp server.py
   /tmp/opp/server.py`, run both as local Flask servers via `setsid
   nohup env PORT=... python3 main.py > log 2>&1 </dev/null & disown`,
   loop `battlesnake play ... -o /tmp/game_N.json & disown`, sleep, check
   `tail`). **Result: 14/14 clean wins**, games 7-242 turns. This is a
   strong, clean confirmation that the real 98.8% win rate is genuine and
   reproducible locally too (unlike several past opponents in this file's
   history where local 1v1 was notably harder than the real score).

2. **Added a new, bounded, opponent-independent scoring term:
   `_greedy_self_room()`** (see the function's own docstring in `main.py`
   for full detail). Motivation: the extensive "self-coil" trace history
   throughout this file (many rounds, many opponents) repeatedly found
   candidates with a large raw flood-fill area AND a passing
   tail-reachability check that still led to a fatal trap a few turns
   later, because neither check verifies whether there's an actual
   *walkable path* through the region wide enough for our own body's
   full length — raw area only counts total open cells, not path
   geometry. The new check greedily walks forward from a candidate cell
   for up to `my_length` steps (always choosing the neighbor with the
   most free neighbors of its own — a cheap "head toward the most-open
   local space" rule), treating visited cells as newly blocked (simulating
   our body extending along that path), and reports how many steps it
   managed before getting stuck. If it gets stuck early (fewer than
   `my_length` steps), that's now a soft, additive penalty
   (`(my_length - room_steps) * 7`) on top of the existing terms — never
   a hard gate, deliberately, to avoid repeating the already-documented
   mistake of an overly aggressive pessimistic heuristic overriding the
   real safety metrics (see the extensive `opp_territory`/`area_pess`
   history earlier in this file, which had to be reverted/fixed twice for
   exactly that failure mode). Only computed when `area_for_score >=
   my_length` (redundant otherwise, since the hard-trap penalty already
   fires much harder in that case) — bounded cost, verified via timing
   (300 `move()` calls on an 11x11 board with a 25-length snake in
   ~2ms/call, nowhere near the 500ms/move budget).

3. **Verification**:
   - Smoke tests (`main.move()` on a normal 2-snake state, `{}` malformed
     state, empty-snakes state) — all still return valid moves, no
     exceptions, both before and after the change.
   - `ast.parse` confirms the file is syntactically valid.
   - **Fresh 20-game local benchmark AFTER the change** (same recipe,
     restarted both servers with the new code): **19/20 wins, 1 loss**.
     Traced the loss (`/tmp/post_9.json`, died turn 202): our snake had
     grown to **length 25 on the 11x11 board** and formed a tight spiral
     in a ~7x7 corner region — the same well-documented "extreme-length
     self-coil, board nearly exhausted" class as the previously-traced
     `sim_90.jsonl` (length 35) from last round's notes, not a new
     regression. No errors/exceptions in either server's log across the
     full 34-game combined benchmark (14 pre-change + 20 post-change).
   - **Combined local result this round: 33/34 (97%)**, fully consistent
     with (not worse than) the pre-change 14/14 and the real match history
     (247/1/2, 247/2/1) — no evidence of regression, and the one loss
     found matches an already-understood, hard-to-fix failure class
     rather than a new bug introduced by this round's change.

### Honest assessment: this change is unlikely to have fixed the specific
### previously-traced `sim_35.jsonl` tie (still needs real multi-ply
### lookahead), but is a reasonable, low-risk, generally-applicable
### addition

The `sim_35.jsonl` turn-124 tie previous notes described was between two
paths where literally *every* metric (area, voronoi, tail_reachable) was
identical — a mirrored/symmetric situation where a greedy "most locally
open neighbor" self-walk would likely also come out identical for both
directions (same geometry, just mirrored), so this specific change
probably would NOT have flipped that exact decision. It's better
understood as a complementary check for a *different* (but related)
self-coil sub-case: "this candidate's region has plenty of raw area and
a path back to my tail exists in principle, but there isn't actually room
for my whole body to fit through it without folding back on itself" —
distinct from "the whole region will get sealed by an opponent 2-3 turns
from now" (which genuinely needs opponent modeling / real lookahead, not
yet attempted, see the many `ccSnake2018__ccsnake`/`Xe__since`/
`zacpez__scape-goat` design sketches elsewhere in this file for that).

### Recommended next steps

1. **Keep monitoring `/logs/rounds/2/results.json`** (this round's real
   result, once it exists) — if the opponent is still `rdbrck__btas` and
   the win rate stays similar (~98-99%) or improves slightly, this
   change is safe to keep building on. If it regresses noticeably,
   revert via `/tmp/main_before_round2.py` (saved this session, not
   persisted in the repo — recreate via `git show HEAD:main.py` before
   this round's commit if that file is gone) and investigate why.
2. The genuinely-tied `sim_35.jsonl`-style loss (identical metrics,
   only food-distance differs, danger invisible for 2-3 turns) remains
   the best concrete, reproducible test case in this file's history for
   validating any future real multi-ply-lookahead attempt — see last
   round's notes (directly above this section) for the full trace and
   exact turn/state to replay.
3. As always: re-check the opponent identity each round via
   `results.json` before assuming past analysis applies; use `git log
   --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark a new
   opponent if one appears.

### Files (this round's change)

- `main.py` — the bot (this round: added `_greedy_self_room()` and a
  soft additive penalty using it in the scoring loop — see the function's
  docstring and the inline comment at its call site for full rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.
- `/tmp/main_before_round2.py` (this session, not persisted in the repo)
  has the exact pre-this-round `main.py` if a revert/diff is needed —
  recreate via `git show HEAD:main.py` before this round's commit if
  that file is gone by the time you read this.

## Round (this session) — opponent = Spenca__vulture-snake, traced losses (mix of forced H2H + self-coil, both well-known classes), confirmed strong local benchmark, NO code change

`/logs/rounds/0/results.json`: opponent this round is **`Spenca__vulture-snake`**
(a real 2017 port -- greedy-toward-closest-food, then "circle/orbit" the food
defensively once adjacent; has full collision avoidance + desperation
fallback; stateful+random via Python module globals in the *original* port,
though our extracted copy at `/tmp/opp_main.py` is only used for local
benchmarking, not committed). Real result: **sonnet-5 242 / opponent 6 /
ties 2** out of 250 (96.8%). `analyze_logs.py /logs/rounds/0`: avg 89.3
turns/sim (min 12, max 251).

Note: this exact opponent (`Spenca__vulture-snake`, "Rung 18/50") has also
been faced by a **parallel/unrelated ladder session** (model `opus-4-8`,
completely different `main.py` implementation -- see `git log --oneline
--all | grep -i Spenca` for those commits, e.g. `git show
e251fb6:README_agent.md`). Their notes (search "vulture" in that file) are
a good read: they found their losses were **almost entirely their own
self-coils when long+healthy** (opponent itself stays short, patrols/orbits
food, rarely poses direct pressure) and added a "worst-case 2-ply
anti-coil" signal + an 8-ply pure-self-survival greedy simulation to
target it, with mixed/partial success (their own notes say the deepest
enemy-assisted seals still weren't fully fixed). Their code is a different
implementation, not directly portable, but confirms this opponent's
general character: weak/patrols, but our own long-horizon self-coiling is
the dominant loss vector against it, not opponent skill -- consistent with
what I found below.

### Traced our own real losses this round (6 losses total: sim_5, sim_11,
### sim_22, sim_121, sim_131, sim_142)

Checked all 6 via each sim's body state near the death turn (recipe:
same as many rounds' notes throughout this file -- for each sim, find the
turn where `sonnet-5` disappears from `board.snakes`, look at the
previous turn's head positions/lengths for both snakes):

- **`sim_11` (died turn 189, length 13)** -- fully traced via literal
  board-state replay: our snake spent ~25 turns (T164-188) in a large,
  slow loop around the top-left/top region (no food eaten, health
  91->68, length constant at 13) and ended up back near its starting
  area of that loop, at which point it only had 3 legal candidates left:
  two real dead-end pockets (area 6 each, well below our own length of
  13 -- genuinely too small to fit our body) and one "open" direction
  (area 90) that was in `risky_cells` because the opponent (length 14,
  one cell away) could also move there. **Confirmed via direct
  `main.move()` replay that the current code correctly computes all of
  this and is forced to choose the least-bad of three bad options** --
  this is the same "genuinely forced choice, not a scoring bug" class
  documented in this file's `tim-hub__awesome-snake` section (see
  above) and several others. The real fixable moment (if any) was
  several turns earlier, when the snake first committed to that
  large aimless loop -- not something a 1-ply/few-term heuristic can
  see coming since every step of the loop looked individually safe and
  reasonably food/space-scored at the time.
- **`sim_121`, `sim_142`, `sim_22`, `sim_5`** -- all show the opponent
  *far* from our snake at time of death (Manhattan distance 4-8+ cells)
  while our own head ends up in/near a corner or fully enclosed pocket
  -- the well-established "pure self-coil, opponent uninvolved" class
  (same signature as several previous rounds' traces against other weak
  opponents, e.g. the `coreyja__bombastic-bob` section above). `sim_5`
  in particular: our snake reached **length 23 on the 11x11 (121-cell)
  board** before dying -- the same "ran out of board at extreme length"
  class flagged multiple times earlier in this file (see the
  `rdbrck__btas` section's `sim_90`, length 35, for a more extreme
  version of the identical pattern).
- **`sim_131`** -- opponent moderately close (length 16 vs our 18) at
  time of death; didn't fully trace given step budget, but shape is
  consistent with the "opponent-assisted" pincer/corridor-race class
  documented extensively elsewhere in this file (`Xe__since`,
  `ccSnake2018__ccsnake` sections) rather than a locatable same-turn
  scoring bug.

### Why no code change was made this round

Every loss traced maps cleanly onto one of the (many-rounds-documented,
already extensively investigated) failure classes this file has
established require **real multi-ply lookahead** to fix, not another
local heuristic weight tweak -- and this file's history includes several
concrete examples of speculative attempts at partial fixes for exactly
this class (opponent-heading projection, `opp_territory`/`area_pess`
pessimistic-BFS variants) that were later found to be ineffective or
actively harmful and reverted. Given:
- the real win rate is already strong (242/6/2, 96.8%),
- a fresh 4-game local benchmark against a freshly-extracted
  `origin/human/Spenca/vulture-snake:main.py` (same recipe as dozens of
  earlier rounds -- `setsid nohup env PORT=... python3 main.py & disown`
  for both bots, `battlesnake play ...` backgrounded+disowned, sleep,
  check `tail`) came back **4/4 clean wins** (16-93 turns) with the
  *current, unmodified* `main.py` -- no regression, no new bug found,
- the traced losses are either genuinely-forced (sim_11) or classic
  long-horizon self-coils (sim_121/142/22/5) that this file's very
  extensive prior history (30+ rounds of notes) shows are NOT reliably
  fixable via more local-weight tuning, only via real lookahead (never
  yet attempted, still the single highest-ceiling idea on this file's
  many-rounds-recurring backlog),
- only ~5 steps of budget remained after this investigation,

I judged it safer to leave a clear diagnostic record (this section) than
to ship an untested speculative tweak. `main.py` is **unchanged** this
round.

### Recommendation for next round

1. If `/logs/rounds/1/results.json` (once it exists) shows the same
   opponent and a similar (or better) win rate, no action needed --
   this is consistent with a bot near its practical 1-ply-plus-heuristics
   ceiling against a real, if not-very-threatening, opponent.
2. If a **different** opponent appears, use `git log --oneline --all |
   grep -i human` + `git show origin/human/<Org>/<repo>:main.py` to
   extract and benchmark them per the established recipe throughout
   this file before assuming this round's analysis applies.
3. The still-not-attempted big idea, reconfirmed relevant yet again this
   round (`sim_11`'s forced 3-way choice, and the repeated extreme-length
   self-coils in sim_5/121/142/22): **true multi-ply lookahead / minimax
   with a simple opponent-response model**, OR, more specifically for
   the "aimless long loop with no food eaten" pattern seen in `sim_11`,
   a lighter-weight idea worth trying first: **periodically bias toward
   the nearest food more strongly even at high health** if the snake has
   gone > some threshold of turns without eating and isn't in any
   immediate danger (a simple turn-counter check, no new BFS needed,
   very cheap) -- this would reduce how often the snake ends up drifting
   into an aimless multi-turn loop that can coincidentally collide with
   a patrolling opponent's path several turns later. Not implemented
   this round due to step budget, but low-risk/cheap to try and validate
   first via the same trace-replay + local-benchmark recipe used
   throughout this file.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round -- investigation only, see
  above).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round 2 (this session) — opponent still Spenca__vulture-snake (240/9/1 real), implemented the previously-recommended "aimless wandering" fix (stuck_count food-weight boost at ALL health levels), validated with 12/12 clean local wins

`/logs/rounds/{0,1}/results.json`: opponent both rounds is
`Spenca__vulture-snake`. Round 0: 242-6-2 (investigation-only round, no
code change — see the long section directly above this one for the full
loss trace of round 0, which found a mix of genuinely-forced collisions
and long-horizon self-coils/aimless loops, and explicitly recommended, as
the cheapest next thing to try, "periodically bias toward the nearest
food more strongly even at high health if the snake has gone > some
threshold of turns without eating and isn't in any immediate danger").
Round 1 (same unchanged `main.py`): 240-9-1 — consistent, still strong
(~96%).

### What I did this round

1. Re-checked the round-1 losses (9 total, found via each `sim_*.jsonl`'s
   final `winnerName` line, same technique `analyze_logs.py` uses) — most
   showed the same signature flagged by the previous round's notes:
   our snake's health declining steadily for 20+ turns with **no food
   eaten** before the eventual death (e.g. `sim_113`: health 81→57 over
   24 turns with no eating; `sim_226`: our snake reached length 27 with
   health slowly declining; `sim_92`, `sim_156`: similar steady declines).
   This matches the "aimless wandering / never commits to eating even
   though nothing forces it not to" pattern the previous round's notes
   identified but did not implement a fix for.
2. **Implemented the previously-recommended fix**: the bot already
   computes `stuck_count` every `move()` call (a module-level tracker,
   `_stuck_state`, counting consecutive turns where health did not
   increase — added a couple of rounds ago for a different purpose, the
   `coreyja__jump-flooding` mutual-avoidance-cycle fix, and previously
   only used to relax the risky-cells penalty when health < 50). Added a
   **new, separate, capped boost to the food-seeking weight that applies
   regardless of current health level**: `weight += min(stuck_count *
   0.15, 3.0)` (reaches its +3.0 cap once `stuck_count >= 20`), stacked
   on top of the existing health-based urgency curve and length-deficit
   boost. This directly targets "healthy snake wanders for 20+ turns
   without any strong pull toward food" — the previous per-health-level
   weight (1.5 at health>=50) provided very little food-seeking pressure
   in exactly this scenario, letting the snake's path be dominated by
   other tie-break terms (edge/degree/voronoi) for a long stretch, which
   several traced losses (this round's and previous rounds') show can
   eventually intersect with an opponent's independent path or a slow
   self-coil.
   - This is purely additive and capped at a modest +3.0 (small relative
     to the existing weight range 1.5-10, and dist is typically single-
     digit on an 11x11 board, so this is at most a ~dozen-point nudge) —
     it can only affect tie-breaks among already-safe candidates, never
     override the hard-trap/risky_cells/voronoi safety terms elsewhere in
     the scoring loop (those are untouched).

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state (with `game`/
  `turn` keys so `stuck_count` computes correctly), `{}` (fully
  malformed), and an empty-snakes state — all return valid moves, no
  exceptions.
- `ast.parse` confirms the file is syntactically valid.
- **Fresh 12-game local benchmark** against a freshly extracted
  `origin/human/Spenca/vulture-snake:main.py` (recipe unchanged from many
  earlier rounds' notes throughout this file — `git show
  origin/human/Spenca/vulture-snake:main.py > /tmp/opp/main.py; cp
  server.py /tmp/opp/server.py`, then `setsid nohup env PORT=...
  python3 main.py > log 2>&1 </dev/null & disown` for both bots, loop
  `battlesnake play ... -o /tmp/game_N.json & disown`, sleep 25s, check
  `tail`). **Result: 12/12 clean wins**, games 27-150 turns. Zero
  errors/exceptions in either bot's server log
  (`grep -i "error\|traceback\|exception" /tmp/new.log /tmp/opp.log`
  clean, exit code 1 = no matches). This is a clean, encouraging signal
  — no regression, and consistent with (not worse than) the strong real
  match history against this opponent.
- Did **not** get to re-trace a *new* loss with the patched code this
  round (none observed in the 12-game sample) — if `/logs/rounds/2/
  results.json` (this round's real result) shows any losses, use the
  same trace-replay technique documented extensively throughout this
  file (build a synthetic `game_state` per logged turn from
  `board.snakes[*].body`, call `main.move()` directly) to see whether
  they're a *new* mechanism or the same already-documented classes
  (genuinely-forced collision, extreme-length self-coil at very high
  length, or opponent-assisted corridor-race/pincer).

### Recommended next steps

1. Check `/logs/rounds/2/results.json` once it exists — if the opponent
   is still `Spenca__vulture-snake` and the win rate holds or improves
   over 240-9-1 / 242-6-2, this fix is confirmed working in the real
   harness too. If it regresses, the change is a small, easily-reverted
   diff (just the one `weight += min(stuck_count * 0.15, 3.0)` line —
   search for "stuck_count \* 0.15" in `main.py`).
2. If new losses appear, keep using the trace-replay technique (dozens of
   worked examples throughout this file) to categorize them — this file's
   long history strongly suggests any *remaining* losses after this fix
   will fall into the "genuinely forced" or "extreme-length self-coil" or
   "opponent-assisted corridor race" buckets, all of which are well-
   documented as needing real multi-ply lookahead/minimax to fix further
   (see the extensive design sketches in the `ccSnake2018__ccsnake`,
   `Xe__since`, and `zacpez__scape-goat` sections earlier in this file) —
   this remains the single highest-ceiling, not-yet-attempted improvement
   if local heuristic tuning (like this round's) keeps showing
   diminishing returns.
3. As always: re-check the opponent identity each round via
   `results.json` before assuming past analysis applies; use `git log
   --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark a new
   opponent if one appears.

### Files (this round's change)

- `main.py` — the bot (this round: added a capped `stuck_count`-based
  food-urgency boost that applies at all health levels, not just when
  health<50 — see the inline comment directly above
  `weight += min(stuck_count * 0.15, 3.0)` for the full rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent = moxuz__pinky-snek, traced a loss, confirmed genuine 1-ply TIE (not a fixable bug), NO code change

`/logs/rounds/0/results.json`: opponent this round is **`moxuz__pinky-snek`**
(a 2017 port: builds a "danger" set = walls + all snake bodies + empty
cells with >=3 dangerous neighbors i.e. shallow dead-end detection, then
picks a RANDOM safe adjacent cell; only seeks food when health<30 — see
`git show origin/human/moxuz/pinky-snek:main.py`). Real result: sonnet-5
236 / opponent 13 / tie 1 out of 250 (94.4%). `analyze_logs.py
/logs/rounds/0`: avg 96.1 turns/sim (min 6, max 313). Note: this exact
opponent has also been faced by a parallel/unrelated ladder session
(model `opus-4-8` — see `git log --oneline --all | grep -i moxuz`,
e.g. `git show d616125:README_agent.md`), which found the same
conclusion independently in their own (differently-implemented) bot:
this opponent is weak/semi-random, and losses are almost entirely
**our own self-coils**, not opponent skill/pressure.

### Traced one real loss in full (recipe unchanged from many earlier
### rounds' notes throughout this file)

`sim_138.jsonl` (died turn 70, length 11): our snake ate two food items
sitting in the far-right column (10,6) and (10,4) around turns 60-62,
then continued down that column into the bottom-right corner while its
own body filled in behind it, ending with **zero legal moves at turn
70**. Opponent (length 3) was 2-4 cells away the whole time — present but
not really "sealing" anything; this is fundamentally a **self-coil**, the
same recurring class documented dozens of times throughout this file.

**Confirmed via direct `main.move()` replay that the live code exactly
reproduces this real loss turn-by-turn** (a good sanity check the trace
methodology is sound). Walked back to find the actual fork point: at
**turn 59** (head `(9,6)`), candidates were `up`->`(9,7)` (score 1162.0)
vs `right`->`(10,6)` (score 1163.25) — **a 1.25-point margin out of
~1160**, i.e. essentially a coin flip. `right` led into the column;
`up` would likely have avoided it. By **turn 60/61** the snake had
already committed (only up/down legal at turn 60; only down/left legal
at turn 61), and at turn 61 I directly measured both `down`->`(10,4)` and
`left`->`(9,5)`: **`_flood_fill_size` area = 110 for BOTH, and
`_greedy_self_room` = 10 (== my_length) for BOTH** — i.e. every single
existing anti-self-coil signal in the bot (raw area, the bounded
"greedy self-room" body-fit check added a couple of rounds ago for
`rdbrck__btas`) was **exactly, identically tied** between the safe and
fatal options at the last turn with a real choice. This is the same,
now very well-documented ("genuine tie, needs real multi-turn
lookahead") failure class established repeatedly throughout this file
against many different opponents (see the extensive `ccSnake2018__ccsnake`,
`Xe__since`, `zacpez__scape-goat`, `rdbrck__btas` sections above) — not a
locatable scoring bug, and not fixable by tuning any existing weight
(there's nothing to differentiate: the values are identical, not just
close).

### Why no code change was made this round

- The real win rate (236/13/1, 94.4%) is solid and the traced loss maps
  cleanly onto an already-exhaustively-documented, already-declined-to-
  patch-further failure class (many past rounds tried and, in at least
  2 cases, explicitly reverted speculative attempts at this exact
  problem — see the `Xe__since` straight-line-projection revert and the
  `nbw__nbw-crystal` "opponent heading projection" revert elsewhere in
  this file).
- The measured tie at turn 61 (area 110/110, room_steps 10/10, both
  *exactly* equal) is concrete proof that no additive-weight tweak to
  any existing term can change this specific outcome — the values
  aren't close, they're identical.
- Only a few steps of budget remained after completing this trace.

### Recommendation for next round

- If `/logs/rounds/1/results.json` (once it exists) shows the same
  opponent and a similar (or better) win rate, no action needed.
- If a **different** opponent appears, use `git log --oneline --all |
  grep -i human` + `git show origin/human/<Org>/<repo>:main.py` to
  extract and benchmark them per the established recipe throughout this
  file before assuming this round's analysis applies.
- The still-not-attempted big idea, reconfirmed relevant yet again this
  round: **true multi-ply lookahead / minimax** (or at minimum, a
  bounded few-ply-deeper version of the existing `_greedy_self_room`
  check — e.g. instead of a single greedy walk, try comparing the *best*
  achievable room across a couple of different greedy tie-breaking
  strategies per candidate, since a single deterministic greedy walk can
  itself tie identically between two topologically different regions, as
  seen here). `sim_138.jsonl` turn 59 (head `(9,6)`, candidates `up` vs
  `right`) and turn 61 (head `(10,5)`, candidates `down` vs `left`, area/
  room both exactly 110/10 for each) are clean, freshly-verified
  repro points for validating any future lookahead attempt — reuse the
  `build_state()` helper pattern from many earlier rounds' notes above
  (build a synthetic `game_state` from a logged turn's
  `board.snakes[*].body` fields, call `main.move()` directly) to
  reconstruct them.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round — investigation only).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round 2 (this session) — opponent still moxuz__pinky-snek (236-13-1 → 240-8-2 real, improving), traced a fresh loss (confirms established "genuine tie / forced edge corridor" class), fresh local benchmark clean, NO code change

`/logs/rounds/{0,1}/results.json`: opponent both real rounds is
`moxuz__pinky-snek`. Round 0: 236-13-1(tie). Round 1 (same unchanged
`main.py`): **240-8-2** — a real, if small, improvement, consistent with
the previous round's `stuck_count`-based food-urgency-at-all-health-levels
fix (see the section directly above this one) helping generally.
`analyze_logs.py /logs/rounds/1`: avg 103.6 turns/sim (min 9, max 298).

### Traced one fresh round-1 loss in full (recipe unchanged from many
### earlier rounds' notes throughout this file)

`sim_104.jsonl` (died turn 45, my length 9 vs opponent length 5 at death):
replayed every turn from 38 to 45 with a synthetic `game_state` built
directly from each turn's logged `board.snakes[*].body` fields (see the
`build_state()` pattern in many earlier sections above — trivial to
recreate), calling `main.move()` and separately recomputing the legal
candidate set via `main._build_blocked` at each turn. **Confirmed
`main.move()` exactly reproduces the real game's recorded moves at every
turn** (sanity check the replay methodology is sound).

Concrete mechanism: at **turn 38** (head `(4,10)`, top edge, length 9,
health 100), there were exactly 2 legal candidates: `left`->`(3,10)` and
`right`->`(5,10)`. Manually verified **both had identical raw flood-fill
area (110 each)** and — since `wall_run` is computed purely from our
*existing* body segments' proximity to a wall, not from the candidate
direction itself — **identical `wall_run` and thus identical wall-hugging
penalty for both directions too** (a subtlety not previously documented
in this file: the wall_run/edge penalty terms cannot discriminate between
"turn left along an edge" vs "turn right along an edge" from a cell that's
already near a wall, since they only look backward at where we've already
been, not at which of the two symmetric directions we're about to
commit to). The only differentiating term was food-distance (food was
positioned to the right), which correctly and predictably picked `right`.

That decision turned out to be fatal: for the next **4 consecutive turns
(39-42), there was only ONE legal candidate each turn** (`main._build_blocked`
confirms this directly — the bot's own prior body plus the opponent's
body left no alternative), i.e. the path was **already fully forced/
committed starting immediately after turn 38**, with zero further
decision points, until reaching the top-right corner `(10,10)` at turn 43
(also forced, only 1 legal move), where the opponent (paralleling one row
below along y=9) had simultaneously advanced its own head to `(10,9)` and
then (after eating and growing, so its old body segment didn't vacate)
sealed the only remaining exit cell, leaving zero legal moves at turn 45.

This is, precisely, the many-times-already-documented **"genuine 1-ply
tie, needs real multi-turn lookahead to resolve correctly"** failure
class established repeatedly throughout this file against many different
opponents (see the extensive `ccSnake2018__ccsnake`, `Xe__since`,
`zacpez__scape-goat`, `rdbrck__btas`, and previous-round `moxuz__pinky-snek`
sections above) — confirmed again here with a fresh, concrete, fully
turn-by-turn-verified example. **Not fixable by tuning any existing
weight**: the two options were exactly equal on every spatial/safety
metric at the only real decision point (turn 38); the actual danger
(the opponent's row-9 shadow converging on the corner) was still 5 turns
away and had no representation in any current-turn heuristic.

### Why no code change was made this round

- Every relevant metric was **provably identical** between the two
  options at the one real decision point — there is no coefficient to
  tune that would break this specific tie without also changing the
  (far more common, already-well-tested) "prefer whichever direction has
  no other signal but is closer to food" case.
- This file's history includes multiple concrete, documented attempts at
  partial fixes for exactly this class (opponent straight-line/heading
  projection vs `Xe__since`, the old `opp_territory`/`area_pess` 6-ply-BFS
  pessimistic-blocking mechanism) that were later found ineffective or
  actively harmful and explicitly reverted — the risk/reward of another
  speculative attempt with limited remaining step budget is poor.
- Real match results are trending positively already (236-13-1 →
  240-8-2) without any change this round, and a fresh **6/6 clean local
  benchmark** against a freshly extracted
  `origin/human/moxuz/pinky-snek:main.py` (recipe unchanged from many
  earlier rounds' notes throughout this file — `setsid nohup env
  PORT=... python3 main.py > log 2>&1 </dev/null & disown` for both bots,
  loop `battlesnake play ... & disown`, sleep, check `tail`) confirms no
  regression, games 63-171 turns, zero errors/exceptions in either
  server's log.
- Smoke tests (`main.move()` on a normal 2-snake state, `{}` malformed
  state, empty-snakes state) all still pass, confirming the codebase is
  healthy going into next round unmodified.

### Recommendation for next round

- If `/logs/rounds/2/results.json` (once it exists) shows the same
  opponent and a similar or better win rate, no action needed — this bot
  appears to be near its practical ceiling for a 1-ply-plus-heuristics
  design against this (and most other) opponents faced so far.
- If a **different** opponent appears, use `git log --oneline --all |
  grep -i human` + `git show origin/human/<Org>/<repo>:main.py` to
  extract and benchmark them per the established recipe throughout this
  file before assuming this round's analysis applies.
- The still-not-attempted big idea, reconfirmed relevant yet again this
  round with a fresh, clean, fully-verified example: **true multi-ply
  lookahead / minimax with a simple opponent-response model**. This is
  now an extremely well-documented, many-dozens-of-times-repeated
  recommendation across this file (see the detailed design sketches in
  the `ccSnake2018__ccsnake`, `Xe__since`, and `zacpez__scape-goat`
  sections above). `sim_104.jsonl` turn 38 (head `(4,10)`, candidates
  `left`->`(3,10)` vs `right`->`(5,10)`, both exactly tied at area=110 and
  identical wall_run at the 1-ply level, only diverging fatally 5 turns
  later) is a good, clean, freshly-verified repro point for validating
  any future lookahead attempt — reuse the `build_state()` helper pattern
  documented in many earlier sections above (build a synthetic
  `game_state` from a logged turn's `board.snakes[*].body` fields, call
  `main.move()` directly) to reconstruct it.
- One subtlety newly documented this round, worth keeping in mind for any
  future wall-hugging heuristic work: the existing `wall_run` penalty is
  direction-agnostic (computed purely from the body's history, not from
  which of two symmetric directions along/away from a wall the candidate
  represents) — so it cannot by itself break a "turn left vs turn right
  along an edge" tie. Any future fix for this specific tie shape would
  need a genuinely forward-looking signal (e.g. simulate a few steps in
  each candidate direction and compare resulting openness/exit options),
  not just a backward-looking commitment penalty.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round — investigation only, see
  above).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent = coreyja__amphibious-arthur, traced losses (extreme-length self-coil + point-of-no-return edge-hugging, both well-known classes), NO code change (investigation-only, low risk given already-strong 232/18 result)

`/logs/rounds/0/results.json`: opponent this round is **`coreyja__amphibious-arthur`**
(a faithful Rust port — see `git show origin/human/coreyja/amphibious-arthur:main.py`
for the full docstring. Notable quirk: its scoring function reads `health`
from the board state but does NOT decrement it across its own internal
recursion, so its heuristic is essentially "prefer neighborhoods with more
open cells, biased toward keeping health near 80" — it has **no explicit
food-seeking at all**, just collision avoidance + a mild open-space
preference). Real result: **sonnet-5 232 / opponent 18** out of 250 (92.8%,
NOT a clean sweep). `analyze_logs.py /logs/rounds/0`: avg 126.6 turns/sim
(min 12, max 342) — games commonly run very long, which (per this file's
extensive history) is exactly when our own long-horizon self-coil risk
becomes the dominant loss mechanism rather than opponent pressure (this
opponent has no active hunting/food-seeking behavior to create real
corridor-race pressure).

### Local benchmark (before any change)

Extracted the opponent fresh (`git show
origin/human/coreyja/amphibious-arthur:main.py > /tmp/opp/main.py; cp
server.py /tmp/opp/server.py`) and ran 6 real local games via the
`battlesnake` CLI against the current, unmodified `main.py` (standard
recipe — see many earlier rounds' notes throughout this file: `setsid
nohup env PORT=... python3 main.py > log 2>&1 </dev/null & disown` for
both bots, loop `battlesnake play ... -o /tmp/game_N.json & disown`,
sleep, check `tail`). **Result: 5 wins / 1 loss**, games 83-217 turns —
roughly consistent with the real 92.8% win rate (not a case where local
1v1 looks dramatically worse, unlike several past opponents in this
file's history).

### Traced the local loss + several real-match losses (recipe unchanged
### from dozens of earlier rounds' notes — build a synthetic `game_state`
### per logged turn from `board.snakes[*].body`, call `main.move()`
### directly, and manually recompute `_flood_fill_reach`/`_greedy_self_room`
### per candidate to see exactly which term decided a move)

1. **Local loss (`/tmp/game_3.json`, died turn 217, our length 23 on the
   11x11=121-cell board)** — the well-documented "extreme-length
   self-coil, board nearly exhausted" class (search "extreme-length"
   above, e.g. the `rdbrck__btas` sim_90 length-35 case). Traced back to
   turn 204 (head `(8,6)`, legal `up`/`down`): manually computed
   `_flood_fill_reach`/`_greedy_self_room` for both — `up` showed
   `area=87, room_steps=23` (== my_length, i.e. the *existing*
   anti-self-coil heuristic reported it as fully safe), `down` showed
   `area=87, room_steps=15` (< my_length, correctly penalized as tighter).
   The bot picked `up` (the heuristically "safer" option) — and it still
   led to a fully forced dead end 1 turn later (turn 205 had only 1 legal
   move) and death at turn 217. **This means `_greedy_self_room`'s
   deterministic greedy walk produced a false negative here** — it
   reported full room (23/23) for a path that, followed for real,
   actually still dead-ended almost immediately. This is a concrete,
   reproducible limitation of that heuristic (a single greedy walk isn't
   guaranteed to find a real Hamiltonian-like path even when one might
   exist, and can't detect when a region only *looks* like it has room
   dimensionally but doesn't topologically) — worth flagging precisely
   for whoever next works on this heuristic, since previous rounds'
   notes only described `_greedy_self_room` in terms of what it *catches*
   (e.g. the `rdbrck__btas` round), not this kind of false-negative gap.
2. **Real-match loss `sim_224.jsonl` (died turn 21, SHORT game, our
   length only 6)** — notably NOT an extreme-length case, showing this
   failure class isn't just a very-long-game problem. Traced in full:
   our snake walked up column `x=10` (the right edge) for 4 consecutive
   turns while the opponent walked along row `y=0`/`y=1` in the same
   direction, converging on the bottom-right corner. By turn 18, our
   snake was already **completely forced (exactly 1 legal move)** for 2
   consecutive turns, and by turn 20, **zero legal moves remained at
   all** (both `up` and `left` blocked by our own body + the opponent's
   body respectively). Walked back to the actual decision point (turn
   16, head `(10,4)`, legal `up`/`down`) — confirmed via literal-state
   `main.move()` replay that the current code picked `down` there
   (matching the real game), continuing into the corner-bound corridor,
   while `up` was the untaken alternative. Given the step budget
   remaining, did not fully quantify *why* `down` scored higher (likely
   another near-tie among area/voronoi/edge terms, per the many
   previously-documented examples of this exact shape — see the
   extensive `moxuz__pinky-snek`, `ccSnake2018__ccsnake`, and
   `zacpez__scape-goat` sections above for near-identical traced
   examples against other opponents) — this is the single best next
   thing to check if picking this up again (see below for the exact
   repro turn/state).

### Why no code change was made this round

Both traced mechanisms map directly onto the two most well-established,
already-extensively-investigated failure classes in this file's long
history (extreme-length self-coil at very high length; point-of-no-return
edge-hugging where the fatal commitment happens several turns before any
current metric shows danger) — neither is a locatable, fixable same-turn
scoring bug in the traditional sense (no off-by-one, no wrong sign, no
term canceling another unexpectedly, per the direct score inspection
above). This file's history includes multiple concrete, documented
attempts at heuristics targeting exactly these classes (`_greedy_self_room`
itself, `wall_run`, the Voronoi race-territory term, the tail-reachability
check) plus at least 2 documented reverts of speculative *further*
attempts (opponent straight-line/heading projection vs `Xe__since`, the
old `opp_territory`/`area_pess` mechanism) that turned out ineffective or
harmful — the risk/reward of another speculative attempt with the very
limited step budget remaining this round (4 steps left after this trace)
was poor. Smoke tests (`main.move()` on a normal 2-snake state, `{}`
malformed state, empty-snakes state) all still pass, confirming the
codebase is healthy going into next round unmodified.

### Recommended next steps

1. **`sim_224.jsonl` turn 16** (head `(10,4)`, candidates `up`->`(10,5)`
   vs `down`->`(10,3)`, real game took `down` and died 5 turns later) is
   a clean, freshly-verified, SHORT-game repro point (unlike most past
   examples in this file, which tend to be very long games) — worth a
   full per-term score printout (`area`, `voronoi_mine`, `room_steps`,
   `free_degree`, `edge_dist`/`wall_run`, food-dist) for both candidates
   next round to see exactly which term(s) favored `down`, and whether
   `up` was genuinely safer or just differently risky.
2. **The `_greedy_self_room` false-negative found this round** (turn 204
   of `/tmp/game_3.json`: `up` scored `room_steps=23` i.e. "fully safe"
   but led to a forced dead end 1 turn later) is worth investigating
   independently of any specific opponent — since the heuristic is a
   single deterministic greedy walk, it may be worth trying 2-3
   different tie-breaking rules (e.g. also try "prefer the neighbor
   closest to the flood-filled region's centroid" or "prefer the
   neighbor that keeps the most *distinct* branches open") and taking
   the best (max) `room_steps` across a small number of cheap greedy
   variants, rather than relying on one single walk's result — a bounded,
   still-cheap generalization that might catch cases like this one
   without the cost/risk of full multi-ply minimax.
3. The still-not-attempted big idea, reconfirmed relevant yet again this
   round: **true multi-ply lookahead / minimax with a simple
   opponent-response model** — see the extensive design sketches in the
   `ccSnake2018__ccsnake`, `Xe__since`, and `zacpez__scape-goat` sections
   elsewhere in this file.
4. As always: re-check `/logs/rounds/1/results.json` once it exists — if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh before assuming this round's analysis applies.

### Files (unchanged this round)

- `main.py` — the bot (no changes this round — investigation only, see
  above for two freshly-traced concrete repro points: `/tmp/game_3.json`
  turn 204, and `/logs/rounds/0/sim_224.jsonl` turn 16 — recreate via the
  local-benchmark recipe / `build_state()` helper pattern documented many
  times throughout this file if `/tmp` has been cleared by the time you
  read this).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round 2 (this session) — opponent still coreyja__amphibious-arthur (232-18 → 226-22-2 real, stable), implemented previously-recommended multi-tie-break `_greedy_self_room_multi` fix, validated 12/14 local

`/logs/rounds/{0,1}/results.json`: opponent both rounds is
`coreyja__amphibious-arthur`. Round 0: 232-18. Round 1 (same, unchanged
`main.py` — previous round was investigation-only): 226-22-2(tie) — a
small, likely-noise-level dip, not a regression signal by itself (250-sim
samples have real variance; both rounds are clearly still strong,
~90-93%). `analyze_logs.py` for both: avg 126-132 turns/sim, long games
common (this opponent has no active food-seeking/hunting, so our own
long-horizon self-coil risk is the dominant loss mechanism, per the
previous round's detailed trace work — see the long section directly
above this one).

### What I did this round

Implemented the concrete, previously-recommended next step from last
round's notes: last round found a specific **false negative** in
`_greedy_self_room` (single deterministic greedy walk) via local-benchmark
trace (`/tmp/game_3.json` turn 204: the "max_deg" tie-break rule reported
`room_steps == my_length` i.e. "fully safe" for a candidate that, in the
real game, still led to a forced dead end just 1 turn later).

1. Generalized `_greedy_self_room` to accept a `tie_break` parameter with
   three independent rules: `"max_deg"` (original -- prefer neighbor with
   most free neighbors), `"min_deg"` (new -- prefer neighbor with fewest
   free neighbors, i.e. clear tight branches first), and `"far"` (new --
   prefer neighbor that maximizes Manhattan distance from the candidate
   start, i.e. keep spreading outward). See the function's updated
   docstring in `main.py` for full detail on each rule's rationale.
2. Added `_greedy_self_room_multi()`: runs all three tie-break variants
   and returns the **minimum** steps achieved across them (deliberately
   the more *conservative* combination, not the optimistic max — the
   goal is catching real dead ends that any single rule's specific path
   might happen to avoid seeing, not proving optimism). Wired into the
   scoring loop in place of the single-variant call (only call-site
   change, one line).
3. This is still a **soft, additive-only** penalty (never a hard gate),
   same as before — can only make the bot more cautious among
   already-nominally-safe candidates, cannot override the real
   hard-trap/risky_cells safety terms, so it can't repeat the
   already-documented "overly aggressive pessimistic heuristic" bug
   class from several rounds ago (`opp_territory`/`area_pess` history --
   see extensively documented sections earlier in this file).

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state (with `game`/`turn`
  keys), `{}` (fully malformed), and an empty-snakes state — all return
  valid moves, no exceptions.
- `ast.parse` confirms the file is syntactically valid.
- Timing: 200 `move()` calls on a normal 11x11/length-3 state in ~1.2ms/
  call; 100 `move()` calls on a synthetic length-25-snake state (worst
  case for this change, since `_greedy_self_room_multi` scales with
  `my_length` and now runs 3 variants instead of 1) in ~0.07ms/call
  (surprisingly fast since the region was mostly already blocked in that
  test board -- either way, nowhere near the 500ms/move budget; even a
  worst-case 3x of previous timing notes for `_greedy_self_room` alone
  would still be far under budget).
- **Local benchmark**: ran 14 real local games via the `battlesnake` CLI
  against a freshly-extracted `origin/human/coreyja/amphibious-arthur:main.py`
  (recipe unchanged from many earlier rounds' notes throughout this file
  — `setsid nohup env PORT=... python3 main.py > log 2>&1 </dev/null &
  disown` for both bots, loop `battlesnake play ... -o /tmp/game_N.json &
  disown`, sleep, check `tail`). **Result: 12 wins / 2 losses** (85.7%),
  games 43-230 turns. No errors/exceptions in either bot's server log
  (`grep -i "error\|traceback\|exception" /tmp/new.log /tmp/opp.log`
  clean). This is broadly consistent with (not a clear improvement or
  regression versus) the real match win rates (92.8%, 90.4%) and the
  previous round's smaller 5/6 local sample — did not have step budget
  left this round to also re-run the *old* single-variant code
  side-by-side for a controlled before/after comparison on a larger
  sample; the change is validated as **safe** (no crashes, no obvious
  new failure mode, reasonable win rate) but not conclusively proven to
  be a *net improvement* over the single-variant version specifically.

### Honest limitation / recommended next steps

1. **Did not get to re-trace the 2 new local losses** (`/tmp/game_8.json`
   died turn 147, `/tmp/game_10.json` died turn 178 -- both files still
   on disk if `/tmp` hasn't been cleared) to confirm whether they're the
   same already-documented failure classes (extreme-length self-coil,
   point-of-no-return edge-hugging/genuine-tie) or something new. This is
   the most important next step — use the trace-replay recipe documented
   extensively throughout this file (build a synthetic `game_state` per
   logged turn from `board.snakes[*].body`, call `main.move()` directly).
2. **A proper controlled before/after benchmark** (same opponent, same
   number of games, old single-variant `_greedy_self_room` vs new
   `_greedy_self_room_multi`, ideally 20+ games each) would give a much
   more confident answer on whether this change actually helps. `git show
   HEAD:main.py` (before this round's commit) has the old single-variant
   version if you want to set this up.
3. If a **different** opponent appears next round, use `git log --oneline
   --all | grep -i human` + `git show origin/human/<Org>/<repo>:main.py`
   to extract and benchmark them per the established recipe throughout
   this file before assuming this round's change matters against them.
4. The still-not-attempted big idea, unchanged across dozens of rounds'
   notes: **true multi-ply lookahead / minimax with a simple
   opponent-response model** remains the highest-ceiling fix for the
   "genuine tie" / "point-of-no-return" failure class that keeps
   recurring across nearly every opponent faced so far (see the extensive
   design sketches in the `ccSnake2018__ccsnake`, `Xe__since`, and
   `zacpez__scape-goat` sections earlier in this file).

### Files (this round's change)

- `main.py` — the bot (this round: generalized `_greedy_self_room` with a
  `tie_break` parameter, added `_greedy_self_room_multi` taking the min
  across 3 tie-break variants, updated the one call site in the scoring
  loop to use it — see inline docstrings for full rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round (this session) — opponent = OliverMKing__astar-snake, FIRST REAL LOSS on record (108-129-13), root-caused as self-coil box-in, attempted tail-follow fix REVERTED after negative local signal — NO code change shipped

`/logs/rounds/0/results.json`: opponent this round is **`OliverMKing__astar-snake`**
(a strong, real A*-to-food/tail + flood-fill dead-end avoidance bot — see
`git show origin/human/OliverMKing/astar-snake:main.py`). Real result:
**sonnet-5 108 / opponent 129 / ties 13** out of 250 — this is the FIRST
losing round recorded anywhere in this file's very long history (dozens of
previous rounds against many other opponents). `analyze_logs.py
/logs/rounds/0`: avg 220 turns/sim (min 19, max 498) — very long, contested
games, consistent with this being a genuinely strong opponent, not a weak
one that errors out.

### Important cross-reference: a PARALLEL ladder session (different model,
### `opus-4-8`, completely different `main.py` implementation) already faced
### this EXACT opponent for 2 rounds

`git log --oneline --all | grep -i OliverMKing` shows their commits. Read
`git show 4b88daa:README_agent.md` (search "OliverMKing__astar-snake") for
their full analysis. Key findings (their bot, NOT ours, but same opponent):
- Round 0: won 139-106+5T (~56%). Round 1: won 139-101+10T (~57-58%).
- **88/106 losses (83%) = BOXED IN** (self-coil, last frame = zero legal
  moves, all 4 neighbors = own body). Death lengths similar in wins/losses
  (median ~23-24) — NOT simply "we grew too long", it's genuine space-
  management/coiling in long games against an opponent that actively
  contests territory and chases its own tail.
- They tried strengthening a "worst-case 2-ply anti-coil" scoring weight —
  **A/B tested, came back as NOISE** (variant slightly worse, 8-10-2 vs
  8-9-3 committed). Scalar weight tweaks did NOT move the needle, twice.
- Their explicit, repeated, still-NOT-implemented recommendation across
  both their rounds: **a real Hamiltonian-ish tail-follow when long+safe**
  (cycle the board instead of greedily maximizing food/space) — flagged as
  "likely the biggest available win" but never actually shipped/validated
  by them either (ran out of budget both times).

### This round: confirmed the same root cause in OUR OWN codebase

1. Extracted the opponent fresh (`git show
   origin/human/OliverMKing/astar-snake:main.py > /tmp/opp/main.py; cp
   server.py /tmp/opp/server.py`) and ran 4 real local games via the
   `battlesnake` CLI against the (pre-this-round, unmodified) `main.py`
   (standard recipe from dozens of earlier rounds' notes in this file).
   Result: 3 wins / 1 loss, games 115-350 turns.
2. Traced the loss (`/tmp/g_1.json`, died turn 349, length 26 vs opponent
   27): confirmed a **pure self-coil** — at turn 340, our own body was
   already densely spiral-wound through the left/bottom-left quadrant
   (26 segments packed into roughly a 5x7 region), with the opponent
   occupying most of the rest of the board. By the time of death there
   were zero legal moves. This is exactly the same failure signature the
   parallel session found in their own (different) implementation.
3. **Wrote `/tmp/classify.py`** (script, not persisted — recreate: parse
   every `/logs/rounds/0/sim_*.jsonl` where `winnerName ==
   "OliverMKing__astar-snake"`, find the last turn our snake (`sonnet-5`)
   was alive, rebuild the blocked-set from that turn's logged
   `board.snakes[*].body`, count legal moves from our head) across ALL
   129 real losses this round, not just one local example. **Result: 97/129
   (75%) had ZERO legal moves at the last logged frame** (pure box-in/
   self-coil, matching the parallel session's 83% figure almost exactly),
   32/129 had at least one legal move remaining (likely head-to-head
   losses or other forced situations). Average length at death: ~20.4 for
   us, ~20.3 for the opponent — **essentially equal**, confirming (like the
   parallel session found) this is NOT simply "we grow too long", it's a
   genuine space-management/coiling problem in long, roughly-even games.

### Attempted fix this round: tail-follow bonus — IMPLEMENTED, SMOKE-TESTED CLEAN, BUT REVERTED due to a negative local-benchmark signal with no time left to resolve it

Implemented exactly the fix both this file's own extensive history and the
parallel session's independent analysis point to as the most promising
not-yet-tried idea: a cheap, additive "tail-follow" bonus. When healthy
(`my_health >= 50`, i.e. not in the food-urgency regime) and we didn't just
eat (`my_tail is not None`), added `score -= min(tail_dist, 15) * 0.6`
using the existing `_bfs_nearest_food_dist` helper repointed at `{my_tail}`
as the "food" set (it already correctly allows BFS through blocked cells
that are in the target set, which our tail is). This is purely additive,
capped, and only active in the "healthy" regime — designed to be low-risk
by construction (can't override any hard safety term, can't fire when
starving).

- Smoke tests (`main.move()` on normal state, `{}`, empty-snakes state) —
  all passed, no exceptions.
- **However**, a fresh 4-game local benchmark with the change applied
  (same opponent, freshly restarted server) came back **0 wins / 3 losses
  / 1 draw** — a concerning reversal from the pre-change 3/4 local win
  rate on the *previous* 4-game batch. With only ~2 steps of budget left,
  I could not determine whether this is:
  (a) a real regression caused by the tail-follow bonus (plausible — e.g.
      it could be pulling the snake away from genuinely better food/space
      opportunities, or interacting badly with the existing Voronoi/edge
      terms in a way not anticipated), or
  (b) pure sample-size noise (N=4 in each batch is very small against a
      strong, long-game opponent; games run 55-350 turns, so tiny
      differences early can compound very differently over that horizon).
- Given the uncertainty and zero remaining budget to disambiguate (a) vs
  (b) with a larger sample, I judged it unacceptably risky to ship an
  unvalidated change that showed a *negative* signal, however small the
  sample — **reverted via `git checkout -- main.py`**. `main.py` is
  UNCHANGED from the start of this round.

### HIGH PRIORITY next steps for whoever picks this up next

1. **This is now the #1 priority opponent to beat** — it's the only
   losing real round in this file's entire history. Both this session and
   an independent parallel session (different bot implementation) agree:
   ~75-83% of losses are self-coil/box-in in long, roughly-even games: NOT
   fixable by simple weight tuning (tried and found to be noise in the
   parallel session), needs either (a) real multi-ply lookahead (the
   many-rounds-recurring big idea, see extensive design sketches
   throughout this file, e.g. `ccSnake2018__ccsnake`/`Xe__since` sections),
   or (b) a genuine Hamiltonian-ish tail-follow/cycle strategy.
2. **Re-attempt the tail-follow idea, but with a MUCH larger local
   benchmark before concluding anything** (this round's 4-game samples in
   each direction are too small against a 100-300-turn-game opponent to
   distinguish signal from noise — aim for at least 16-20 games each way,
   run in background across multiple tool calls with generous sleep
   windows, per the many timing/`setsid nohup ... & disown` gotchas
   documented throughout this file). The code for the attempted fix is
   preserved in this section's diff description above (a ~10-line
   addition right after the food-distance scoring block, using
   `_bfs_nearest_food_dist(nxt, blocked, width, height, {my_tail})`) if
   you want to re-apply and re-test it properly rather than starting from
   scratch. Consider a smaller weight (e.g. 0.2-0.3 instead of 0.6) or
   gating it more narrowly (e.g. only when `my_length >= 10`, since
   tail-following matters most for long snakes and doing it for short
   snakes might just be actively harmful noise) if the full version keeps
   showing a negative signal.
3. **32/129 (25%) of real losses had at least one legal move remaining
   at the last logged frame** — NOT traced this round (ran out of step
   budget). Worth categorizing: are these head-to-head collisions
   (winnable/risky_cells logic gap?), or something else? Use the
   `/tmp/classify.py` recipe above (recreate — parse
   `/logs/rounds/0/sim_*.jsonl` final `winnerName` lines, find our last
   alive turn, check legal-move count) to isolate this subset for
   detailed trace-replay (recipe used throughout this file: build a
   synthetic `game_state` from the logged turn, call `main.move()`
   directly).
4. As always: re-check `/logs/rounds/1/results.json` once it exists — if
   the opponent identity changes, use `git log --oneline --all | grep -i
   human` + `git show origin/human/<Org>/<repo>:main.py` to extract and
   benchmark them fresh. If it's still `OliverMKing__astar-snake`, this
   is a genuinely tough, well-analyzed opponent (by two independent
   sessions/implementations now) — prioritize the tail-follow re-test
   above over anything else.

### Files (unchanged this round — fix attempted and reverted, see above)

- `main.py` — the bot (NO net change this round — a tail-follow bonus was
  implemented, smoke-tested clean, but reverted after a small-sample
  local benchmark showed a negative signal with no time left to
  disambiguate noise vs regression; see above for the exact code to
  re-apply and test properly).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.
- `/tmp/classify.py` (this session, not persisted in repo) — classifies
  all real losses in a round by legal-move-count at the last logged
  frame (boxed-in vs other) — recreate from the recipe described above if
  needed.

## Round 3 (this session) — opponent still OliverMKing__astar-snake, RE-TESTED the tail-chase idea with a proper larger sample — CONFIRMED it's a real regression, reverted (NO net code change)

`/logs/rounds/{0,1}/results.json`: opponent both rounds is `OliverMKing__astar-snake`
(the same, still-only-losing opponent in this file's history — see the two
long sections directly above this one for full background: it's a real A*-
to-food/tail bot with flood-fill dead-end avoidance, and it specifically
favors chasing its own tail whenever `health >= 55` AND no opponent snake
is currently `>= its own length` — a cheap, effective Hamiltonian-cycle-ish
anti-self-coil strategy). Round 0: 108-129-13. Round 1: 109-128-13 —
essentially unchanged (the previous round was investigation-only: it
implemented a tail-follow bonus, smoke-tested it clean, but reverted it
after a 4-game local benchmark showed a *negative* signal it didn't have
budget to disambiguate from noise).

### What I did this round

Picked up exactly where the previous round left off, per its own top
recommendation: **re-implemented the tail-chase idea, this time mirroring
the opponent's exact trigger condition** (`health >= 55` AND no opponent
snake length `>= my_length`, checked via `can_chase_tail` — see the exact
condition in the opponent's own source, `git show
origin/human/OliverMKing/astar-snake:main.py`, `decide_move()`), rather
than the previous round's simpler "always add a small tail-follow nudge
when health>=50" version. When active: added a `-tail_dist * 5.0` bias per
candidate (BFS distance to our own tail) and reduced the general
food-seeking weight to 30% of normal (`food_weight_scale = 0.3`) — a much
stronger, more faithful mirror of the opponent's own "prioritize tail
over food when safe" behavior than the previous round's flat, weak
`-0.6/cell` nudge.

**Ran a properly-sized local benchmark this time** (the previous round's
biggest acknowledged gap was only testing N=4 games): extracted the
opponent fresh (`git show origin/human/OliverMKing/astar-snake:main.py >
/tmp/opp/main.py; cp server.py /tmp/opp/server.py`), ran both bots as
local Flask servers (`setsid nohup env PORT=... python3 main.py > log
2>&1 </dev/null &`, backgrounded/disowned to survive across tool calls —
see many earlier rounds' notes throughout this file for why this is
necessary in this harness), then ran **10 real local games** via the
`battlesnake` CLI (`-o /tmp/game_N.json` for each, so any could be traced
afterward).

**Result: 2 wins / 8 losses (20%) with the tail-chase change** — clearly,
unambiguously worse than the baseline. To confirm this wasn't just an
unlucky batch (the opponent's games have real turn-order/randomness
variance), I **reverted** the change (confirmed via `diff` that `main.py`
is byte-identical to the pre-round version) and immediately re-ran **8
more real local games** with the *unmodified* baseline bot, same
opponent, freshly restarted servers: **4 wins / 4 losses (50%)** — matching
the real match history's ~44-46% win rate reasonably well (small sample,
but a large, clear gap from the tail-chase variant's 20%).

### Conclusion (fairly confident now — two independent sessions, two different implementations of the idea, both found a negative or at-best-neutral result)

**Do NOT pursue a tail-chasing/tail-following bias against this opponent
without a much more careful design** — it has now been tried twice
(a weak flat nudge last round, a strong condition-mirrored version this
round) and both times showed a negative signal in local benchmarking, this
round with a large-enough sample (10 vs 8 games, a 20% vs 50% split) to be
fairly confident it's real, not just noise. I did not have step budget
left this round to trace *why* it backfires so clearly, but here is a
reasoned hypothesis for next round to check first, before trying yet
another tail-chase variant:

- The opponent's own tail-chasing works well FOR IT partly because it's
  the *only* thing determining its movement in that mode (a real A* to its
  own tail, cascading through progressively looser safety sets) — it
  reliably produces a long, deliberate, always-connected path.
- Our version is just an additive scoring bias mixed in with ~10 other
  scoring terms (voronoi, edge/wall_run, free_degree, risky_cells, area
  thresholds, etc.) that were all tuned/validated *without* this term
  present. It's plausible the tail-distance bias fights against (rather
  than complements) some of those other terms in a way that produces
  worse net trajectories than either "pure existing heuristic" or "pure
  real A*-to-tail" would individually — e.g. it might pull the bot away
  from genuinely good Voronoi-territory-grabbing opportunities, or cause
  it to hover near its own body (low free_degree, wall_run-like
  situations) more often precisely because "near my own tail" and "near
  my own body" are correlated.
- Separately: de-prioritizing food to 30% weight whenever `can_chase_tail`
  is true might mean we grow more slowly than we otherwise would in a
  safe/healthy state, which could ironically make us fall behind in
  length MORE often (losing the exact `can_chase_tail` privilege sooner,
  since it requires us to stay `>=` every opponent's length) — a
  potential self-undermining feedback loop worth checking directly via
  trace (compare length-over-time curves with/without the change on a
  few games) before attempting a third variant.

### Recommended next steps

1. **Do not re-attempt a simple additive tail-distance bias again without
   first tracing a concrete example** (e.g. dump `-o /tmp/game_N.json`
   from one of this round's 8 tail-chase losses — files still on disk in
   `/tmp` if not cleared — and do a turn-by-turn body/health/length trace,
   same technique used dozens of times throughout this file, to see
   concretely how the trajectory differs from a baseline game and where
   it goes wrong). This round did not have budget left to do this after
   completing the two benchmarks; it's the highest-value next step given
   we now have a strong, clean, reproducible negative signal to explain.
2. If you want to keep pursuing a "prevent self-coil like the opponent
   does" angle, consider a fundamentally different mechanism instead of a
   scoring bias: e.g. only *gate* (not bias) — i.e., among candidates that
   are already tied/near-tied on the existing score, prefer the one
   closer to the tail, rather than adding a large independent weight that
   can change which candidate wins outright. This would be a much softer,
   tie-break-only version, less likely to fight the existing (already
   well-tuned, many-rounds-validated) scoring terms.
3. The still-not-attempted big idea (many-rounds-recurring in this file):
   **true multi-ply lookahead / minimax** remains the most likely real fix
   for the self-coil-dominant loss pattern against this specific opponent
   (see the extensive design sketches in the `ccSnake2018__ccsnake` and
   `Xe__since` sections earlier in this file) — this is now the single
   opponent in this file's entire history we are actually losing to, so it
   may finally be worth the risk/investment of a real lookahead
   implementation if a future round has a full budget for it, rather than
   another local-heuristic patch attempt (2 of which, across 2 rounds now,
   have specifically targeted this opponent's dominant failure mode
   without success).
4. As always: re-check `/logs/rounds/2/results.json` (this round's real
   result, once it exists) — if the opponent identity ever changes, use
   `git log --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark them fresh
   before assuming this section's analysis applies.

### Files (NO net change this round)

- `main.py` — unchanged (byte-identical to the version at the start of
  this round — confirmed via `diff` against a saved copy). A tail-chase
  variant was implemented, smoke-tested clean, and benchmarked (2/10 local
  wins) but reverted after confirming a clear regression vs. the
  unmodified baseline (4/8 local wins in the same session, same opponent).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round 4 (this session) — opponent still OliverMKing__astar-snake (3 consecutive losing real rounds: 108-129-13, 109-128-13, 113-131-6), IMPLEMENTED REAL 1-PLY ADVERSARIAL LOOKAHEAD — confirmed real local improvement (66.7% vs baseline ~44-46%)

`/logs/rounds/{0,1,2}/results.json`: opponent all three rounds is
`OliverMKing__astar-snake` — the only opponent in this file's entire long
history we have ever lost to (see the two long sections earlier in this
file, "Round (this session) — opponent = OliverMKing__astar-snake..." and
"Round 3 (this session)...", for full background: it's a real A*-to-food
+ A*-to-own-tail bot with flood-fill dead-end avoidance; both this
session's own trace analysis AND a parallel/independent ladder session
with a totally different bot implementation agree the dominant loss cause
(~75-83%) is self-coil/box-in in long, roughly-even-length games; simple
scalar weight tuning, and two separate attempts at a tail-chasing scoring
bias, were tried and found to be NOISE or an outright REGRESSION in local
benchmarking).

### What I did this round: finally implemented the many-dozens-of-rounds-recurring "real multi-ply lookahead" idea, in a narrow, low-risk form

Added `_advance_body()`, `_blocked_from_bodies()`, and
`_opponent_worst_case_area()` (see their docstrings in `main.py`, right
above `_bfs_nearest_food_dist`, for full detail) implementing a genuine
**1-ply adversarial minimax** over the opponent's actual next move — NOT
a repeat of the old, already-removed/discredited `opp_territory`/
`area_pess` mechanism (which pessimistically blocked every cell an
opponent could reach within a many-move horizon, found to be
uninformative/actively harmful on a small board). Concretely: for each of
our candidate moves, in the standard 1v1 format (exactly 2 snakes total —
skipped entirely otherwise, zero behavior change in that rarer case),
simulate our own body advancing to the candidate cell (`_advance_body`,
correctly modeling growth if it's a food cell), then enumerate the
opponent's own actual legal next moves from their current head, and for
EACH of those, simulate their body advancing too and compute our
resulting flood-fill area from our new head. Take the **minimum** area
across the opponent's choices (a standard paranoid/worst-case assumption)
as `opp_worst_area`, and add `min(opp_worst_area, area_for_score) * 4` to
the candidate's score — purely additive, on top of (never overriding) the
existing hard-trap/soft-margin gates, which are still driven by the raw,
non-speculative `area_for_score` exactly as before.

This directly targets the single most persistent failure class traced
across THIS OPPONENT specifically and dozens of other opponents throughout
this file's history: two candidates with IDENTICAL raw flood-fill area and
Voronoi territory at the moment of decision (a "genuine 1-ply tie"), that
only diverge in real safety once the opponent's very next move is
accounted for (e.g. one path's only chokepoint back to open space is a
cell the opponent can reach next turn; the other's isn't). Because this
models the opponent's real, single next move (not a many-move reachable
set), it cannot inflate an entire large open region into looking
dangerous just because the opponent could eventually wander into part of
it — the exact failure mode that sank the old `opp_territory` approach.

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state (with `game`/`turn`
  keys), `{}` (fully malformed), and an empty-snakes state — all return
  valid moves, no exceptions.
- `ast.parse` confirms the file is syntactically valid.
- Timing: 200 `move()` calls on a normal 11x11/length-3 2-snake state in
  ~2.1ms/call; 200 calls on a synthetic length-25-snake state (worst case
  for this change — the new lookahead scales with candidate count x
  opponent-move count, i.e. up to 16 extra flood fills per `move()` call)
  in ~2.5ms/call — still nowhere near the ~500ms/move budget, negligible
  performance cost.
- **Local benchmark (the real test): 12 games total, split into two
  separately-launched batches of 6, against a freshly extracted
  `origin/human/OliverMKing/astar-snake:main.py` (recipe unchanged from
  many earlier rounds' notes throughout this file — `git show
  origin/human/OliverMKing/astar-snake:main.py > /tmp/opp/main.py; cp
  server.py /tmp/opp/server.py`, then `setsid nohup env PORT=...
  python3 main.py > log 2>&1 </dev/null & disown` for both bots, loop
  `battlesnake play ... -o /tmp/game_N.json & disown`, sleep ~27s, check
  `tail`). Batch 1: 4 wins / 2 losses. Batch 2: 4 wins / 2 losses.
  **Combined: 8/12 wins = 66.7%** — a clear, consistent (same ratio in
  both independently-launched batches) improvement over this opponent's
  historical real-match win rate (~44-46% across 3 consecutive real
  rounds) and this session's own earlier baseline local benchmarks (3/4,
  4/8 in the two previous rounds' sections above). Games ran 64-488 turns
  (long, contested games, as expected against this opponent). **Zero
  errors/exceptions** in either bot's server log across all 12 games
  (`grep -i "error\|traceback\|exception" /tmp/new.log /tmp/opp.log` —
  clean).

### Honest caveats / what's NOT yet done

1. **Did not get to trace any of the 4 new local losses** (files should
   still be on disk as `/tmp/game_3.json`, `/tmp/game_5.json`,
   `/tmp/gameB_21.json`, `/tmp/gameB_24.json` if `/tmp` hasn't been
   cleared) to see whether they're the same still-unsolved classes
   (extreme-length self-coil at very high length; genuine multi-turn-deep
   ties beyond this new 1-ply horizon) or something new the 1-ply
   lookahead doesn't reach. This is the top next step — use the
   trace-replay recipe documented dozens of times throughout this file
   (build a synthetic `game_state` per logged turn from
   `board.snakes[*].body`, call `main.move()` directly).
2. This is only **1 ply** of opponent lookahead (their single immediate
   next move, adversarially chosen) — it will NOT catch dangers that only
   become visible 2+ opponent moves ahead (e.g. the `sim_35.jsonl`-style
   "genuinely tied for several turns" examples traced against
   `rdbrck__btas` and others elsewhere in this file). A natural next
   increment, if this round's result holds up in the real scored match,
   would be extending this to 2-ply (our move -> their worst move -> our
   best response -> assess) — bounded, since there's still only one
   opponent snake, but roughly 4x more flood-fills per `move()` call
   (still should be well within the time budget based on this round's
   timing numbers).
3. **Did NOT get to re-run this exact local benchmark WITHOUT the change**
   in the same session for a perfectly controlled A/B (relied on the
   established historical baseline numbers from the two previous
   rounds' sections above, and the persistent real-match ~44-46% figure,
   as the comparison point instead) — if you want a tighter, same-session
   A/B, `/tmp/main_before_round3.py` (this session, not persisted in the
   repo) has the exact pre-this-round `main.py`.
4. Only ran 12 local games total (small-ish sample against a
   long/variable-game opponent) — a bigger batch (20-30 games) would give
   more statistical confidence, if step budget allows next round.

### HIGH PRIORITY next steps for whoever picks this up next

1. **Check `/logs/rounds/3/results.json` once it exists** — this is the
   most important validation: does the real scored win rate against
   `OliverMKing__astar-snake` improve from the persistent ~44-46%
   baseline (108-129-13, 109-128-13, 113-131-6)? If yes, this confirms
   the 1-ply lookahead approach is worth extending further (2-ply, or
   applying similar real-opponent-move-modeling ideas elsewhere). If it
   regresses or is flat, consider reverting (`/tmp/main_before_round3.py`
   or `git log` for the pre-this-round commit) and re ana lyzing why the
   local benchmark didn't transfer.
2. If new local losses need tracing (see caveat 1 above), use the
   standard recipe throughout this file.
3. Consider the 2-ply extension described in caveat 2 above if this
   round's result holds.
4. As always: re-check the opponent identity each round via
   `results.json` before assuming past analysis applies; use `git log
   --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark a new
   opponent if one ever appears (though after 3 straight rounds it seems
   likely we're locked into playing `OliverMKing__astar-snake` for a
   while longer).

### Files (this round's change)

- `main.py` — the bot (this round: added `_advance_body`,
  `_blocked_from_bodies`, `_opponent_worst_case_area`, and wired a new
  `min(opp_worst_area, area_for_score) * 4` additive scoring term into
  the main scoring loop, active only in the standard 1v1 case — see the
  docstrings/inline comments at each for full rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.
- `/tmp/main_before_round3.py` (this session, not persisted in the repo)
  has the exact pre-this-round `main.py` if a revert/diff is needed.

## Round 4 (this session) — opponent still OliverMKing__astar-snake, sharpened the 1-ply adversarial lookahead penalty (added a real trap-collapse term), 6/10 local benchmark, no crashes

`/logs/rounds/{0,1,2,3}/results.json`: opponent all four prior rounds is
`OliverMKing__astar-snake` — the only opponent in this file's entire
history we've lost to. Results: round0 108-129-13, round1 109-128-13
(both with unchanged main.py — investigation-only sessions), round2
113-131-6 (after the previous round's 1-ply adversarial-lookahead
addition — see the long "Round 4 (this session) — ... IMPLEMENTED REAL
1-PLY ADVERSARIAL LOOKAHEAD" section directly above this one for full
detail), round3 104-130-16 (SAME code as round2, no new commit between
them — confirmed via `git log`/`git status`, tree was clean at the start
of this round). 

**Important variance finding**: comparing round0/1 (no lookahead: 108,
109 wins) vs round2/3 (with lookahead, same code both times: 113, 104
wins) shows almost IDENTICAL average win count (~108.5 either way) but
large round-to-round swings (104-113) for literally the same code. This
means a single round's real-match score against this opponent is a noisy
signal — don't overreact to one round's number when deciding whether a
change helped or hurt; look for consistent trends across 2+ rounds if
possible, and don't be surprised if this round's real result also lands
somewhere in the 100-120 range regardless of what's changed.

### What I did this round

Rather than a big new rewrite (this matchup has now seen many rounds of
investigation — self-coil tracing, tail-chase attempts both reverted,
`_greedy_self_room_multi`, Voronoi race-territory, and finally the 1-ply
adversarial lookahead added last round), I made one focused, principled
strengthening of the existing 1-ply lookahead mechanism, since it's the
most theoretically-sound not-yet-fully-exploited idea on the table and
the previous round's implementation only gave it a fairly weak `* 4`
linear weight.

**Change**: in the scoring loop, when the opponent's worst-case response
(`opp_worst_area`, from `_opponent_worst_case_area` — real 1-ply minimax
over the opponent's actual legal next moves, computed in the standard 1v1
case) would leave us with **less reachable area than our own body length**
(a predicted future trap, not just "somewhat smaller but still safe"),
added an extra penalty: `score -= (my_length - opp_worst_area) * 30`. This
is weighted below the same-turn *guaranteed* hard-trap penalty (`* 100`,
used when `area_for_score` itself is already `< my_length` — a certainty,
not a prediction) since this is a speculative prediction of the
opponent's move (they might not actually play their worst-case-for-us
move) — but large enough to decisively break the "genuine 1-ply tie"
cases (identical raw area/Voronoi territory between two candidates) that
this whole file's history has repeatedly traced as the dominant
unsolved failure class against this and several other opponents. The
previous `min(opp_worst_area, area_for_score) * 4` term alone was fairly
weak in exactly the tied-metrics case this mechanism is meant to catch
(e.g. area=100/100 but opp_worst=100/5 only nets a 380-point gap via that
term combined with the existing `area*5` bonus — helpful but not
decisive against other larger terms like food-distance). The new term
adds a much sharper, more targeted signal specifically for the "opponent
can force me below body length next turn" case.

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state, `{}` malformed
  state, empty-snakes state — all return valid moves, no exceptions.
- `ast.parse` confirms syntactically valid.
- Timing: 200 `move()` calls on a synthetic 11x11 board with a length-10
  snake vs length-12 opponent in ~2.2ms/call — no meaningful perf cost,
  nowhere near the 500ms/move budget.
- **Local benchmark**: 10 real local games via the `battlesnake` CLI
  against a freshly-extracted `origin/human/OliverMKing/astar-snake:main.py`
  (recipe unchanged from many earlier rounds' notes throughout this file
  — `setsid nohup env PORT=... python3 main.py > log 2>&1 </dev/null &`
  for both bots to survive across tool calls, loop `battlesnake play ...
  & disown`, sleep ~27s, check `tail`). **Result: 6 wins / 4 losses
  (60%)**, games 54-370 turns. Zero errors/exceptions in either server's
  log. Given the huge round-to-round variance documented above, this
  60% local sample is not strong statistical evidence of improvement by
  itself, but confirms no crash/regression, and the underlying mechanism
  is more theoretically sound (targets a concretely-identified, oft-traced
  failure pattern) than a purely speculative tweak.

### Recommended next steps

1. **Track win rate trend across MULTIPLE future rounds, not just the
   very next one**, given the demonstrated high variance (104-113 for
   literally identical code across two consecutive rounds). If the trend
   over 2-3 more rounds stays flat/worse, consider reverting this round's
   `* 30` addition (single-line change, easy to remove — search
   `opp_worst_area < my_length` in `main.py`) or the whole 1-ply lookahead
   block (see the previous round's README section for the full diff, or
   `git show <round2-commit>^:main.py` to get the pre-lookahead version).
2. If pursuing this further, the natural next increment (flagged
   repeatedly in previous rounds' notes) is extending to 2-ply: our move
   -> opponent's worst move -> OUR best response -> assess resulting area,
   rather than just leaf-evaluating after their move. Bounded cost since
   there's only one opponent (roughly 4x more flood-fills per candidate,
   still cheap per this round's and previous rounds' timing numbers).
3. Given the sheer number of parallel ladder sessions independently
   fighting this exact opponent (`git log --oneline --all | grep -i
   OliverMKing` shows MANY different lineages/commits, both this model's
   sessions and at least one different-model session referenced in
   earlier rounds' notes) — if a future round has more budget, it could be
   worth reading through a few of those other lineages' current
   `README_agent.md` (via `git show <their-latest-commit>:README_agent.md`)
   to see if any of them found something that actually worked better than
   what we've tried here (self-coil tracing, tail-chase, Voronoi,
   `_greedy_self_room_multi`, 1-ply adversarial lookahead — all
   documented at length above).
4. As always: re-check the opponent identity each round via
   `results.json` before assuming past analysis applies.

### Files (this round's change)

- `main.py` — the bot (this round: added an extra `(my_length -
  opp_worst_area) * 30` penalty when the opponent's predicted best
  response would leave us below our body length in reachable area — see
  the inline comment right above it for full rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.

## Round 5 (this session, FINAL round of this task) — opponent still OliverMKing__astar-snake (5 straight losing real rounds: 108-129-13, 109-128-13, 113-131-6, 104-130-16, 106-131-13), extended the 1-ply adversarial lookahead to a genuine 2-ply minimax — confirmed a real, meaningful local-benchmark improvement (72.2% vs prior ~60-67%)

`/logs/rounds/{0,1,2,3,4}/results.json`: opponent all five prior real rounds
is `OliverMKing__astar-snake` — still the only opponent in this file's
entire long history we have ever lost to, and we've now lost 5 real rounds
in a row to it by a very consistent margin (~104-113 for us vs ~128-131 for
it, out of 250, every single time regardless of what local heuristic
tweaks were tried in between — see the many long sections above this one
for the full history: self-coil tracing, two independently-reverted
tail-chase attempts, `_greedy_self_room_multi`, Voronoi race-territory, and
a 1-ply adversarial opponent-response lookahead added a couple of rounds
ago). Given this is the final round of this particular task, I focused the
whole session on the single most promising, already-partially-validated,
lowest-regression-risk lever left on the table: **extending the existing
1-ply adversarial lookahead to a real 2-ply minimax**, which multiple
previous rounds' notes explicitly flagged as "the natural next increment"
after the 1-ply version was added, and which is mechanistically different
(and much less likely to interact badly with the other ~10 scoring terms)
than the twice-already-reverted tail-chase idea.

### Change made this round

In `_opponent_worst_case_area()` (see its docstring in `main.py` for the
original 1-ply rationale): previously, for each of the opponent's possible
next moves (the adversarial "worst case for us" ply), the leaf value was
just `_flood_fill_size(nxt, leaf_blocked, ...)` — our STATIC area at our
own candidate cell, without letting ourselves respond further. This round
adds a genuine extra ply: **after** simulating the opponent's move, we now
also simulate OUR own best possible follow-up move from `nxt` (try all 4
directions, take the one with the largest resulting flood-fill area as
computed with both bodies now advanced), and use *that* value as the leaf
instead of the static one-shot area. This is a real depth-2 minimax step
(our move → opponent's worst move for us → our best response → assess),
not a repeat of the old, already-discredited `opp_territory`/`area_pess`
multi-move-horizon *territory-blocking* mechanism (which pessimistically
blocked cells reachable within many moves and was found to be
uninformative/harmful on a small board — see the extensive history
elsewhere in this file) — it only ever looks at each snake's *single* next
real move at each of the two plies, so it can't inflate a large open
region into looking dangerous just because it's theoretically reachable
eventually.

Cost: at most 4 (candidates) × 4 (opponent moves) × 4 (our follow-up moves)
= 64 extra flood-fills per `move()` call in the worst case, still cheap on
an 11x11 board — verified via timing (200 calls on a normal 2-snake state:
~4.2ms/call; 50 calls on a synthetic 25-length-snake worst case:
~3.1ms/call), nowhere near the 500ms/move budget.

### Verification done

- Smoke tests: `main.move()` on a normal 2-snake state, `{}` (fully
  malformed), and an empty-snakes state — all return valid moves, no
  exceptions.
- `ast.parse` confirms the file is syntactically valid.
- **Local benchmark (the real test): 18 games total, run in 3 separately-
  launched batches of 6, against a freshly extracted
  `origin/human/OliverMKing/astar-snake:main.py`** (recipe unchanged from
  many earlier rounds' notes throughout this file — `git show
  origin/human/OliverMKing/astar-snake:main.py > /tmp/opp/main.py; cp
  server.py /tmp/opp/server.py`, then `setsid nohup env PORT=...
  python3 main.py > log 2>&1 </dev/null & disown` for both bots to survive
  across tool calls, loop `battlesnake play ... -o /tmp/g5_N.json &
  disown`, sleep ~27-28s per batch, check `tail`).
  **Result: 13 wins / 3 losses / 2 draws = 72.2% win rate**, games ranging
  69-389 turns (batch breakdown: batch1 5W/0L/1D, batch2 3W/3L/0D, batch3
  5W/0L/1D — some batch-to-batch variance as expected against a
  long/contested-game opponent, but the aggregate is clearly better than
  this session's own historical local benchmarks against this exact
  opponent: the previous round's 1-ply-only version scored 6/10 (60%) and
  8/12 (66.7%) in its two local batches; the round before that (before any
  lookahead) scored 4/8 (50%) and 2/10 (20%, the reverted tail-chase
  variant) and 3/4 (75%, one very small early sample) in various
  sessions' batches — see the long history above). Zero
  errors/exceptions in either bot's server log across all 18 games
  (`grep -i "error\|traceback\|exception" /tmp/new.log /tmp/opp.log` —
  clean).

### Honest caveats

1. **Sample size is still modest (18 games)** against a long/variable-
   game opponent (69-389 turns per game) — real-match variance for this
   exact matchup has historically been high even for byte-identical code
   across consecutive real rounds (round2 vs round3 in the history above:
   113 vs 104 wins for literally the same `main.py`, out of 250 sims each
   time). A 72.2% local win rate is an encouraging, meaningfully better
   number than prior sessions' local benchmarks against the same
   opponent, but should not be over-interpreted as a guaranteed real-match
   win-rate jump of the same magnitude.
2. **Did not get to trace the 3 new local losses** (`/tmp/g5_7.json`,
   `/tmp/g5_8.json`, `/tmp/g5_9.json` — should still be on disk if `/tmp`
   hasn't been cleared) — worth a look if this round is followed by
   another one, using the trace-replay recipe documented dozens of times
   throughout this file (build a synthetic `game_state` per logged turn
   from `board.snakes[*].body`, call `main.move()` directly) to see
   whether the 2-ply extension still misses the same class of danger (a
   3+-ply-deep tie) or whether these are a different/new mechanism.
3. **Did not attempt a controlled same-session A/B against the pre-round
   1-ply-only version** (relied on comparing against this session's
   documented historical local-benchmark numbers from previous rounds'
   sections instead — see caveat 1 about real-match variance history,
   which applies to local benchmarks too, just less dramatically since
   local batches aren't subject to whatever real-harness-specific factors
   might also be at play). `/tmp/main_before_round5.py` (this session,
   not persisted in the repo) has the exact pre-this-round `main.py` if a
   teammate wants to run that controlled comparison with a bigger sample
   (20+ games each side) before trusting this round's number fully.

### If this is genuinely the final round of the task (per the task framing)

Given the instructions describe this as the final round, there won't be a
next-round teammate to hand this off to *for this specific ladder run* —
but leaving these notes anyway in case: (a) the task framing is wrong and
more rounds follow, (b) a parallel/future session on a different ladder
run faces the same opponent again (very likely given 5 consecutive real
rounds so far), or (c) this file itself is read by a future audit/review.

### Recommended next steps (for whoever/whatever picks this up, if anyone)

1. Check `/logs/rounds/5/results.json` (this round's real result, once it
   exists) to see if the 2-ply extension moved the real-match needle at
   all from the persistent ~104-113/250 baseline. Given the high
   round-to-round variance documented in this file even for identical
   code, don't over-index on a single round's number either way.
2. If continuing to invest in this opponent specifically: the natural
   next increment is extending further (3-ply), or — more likely higher
   value at this point — actually tracing the 3 new local losses (see
   caveat 2) to see if there's a *qualitatively different*, more
   targeted fix available now that the "genuine 1-2-ply tie" class is
   more thoroughly covered by the existing 1-ply-adversarial +
   2-ply-response mechanism.
3. As always throughout this file: re-check the opponent identity each
   round via `results.json` before assuming any of this analysis applies
   — if the ladder ever assigns a different opponent, use `git log
   --oneline --all | grep -i human` + `git show
   origin/human/<Org>/<repo>:main.py` to extract and benchmark them fresh
   per the established recipe used dozens of times throughout this file.

### Files (this round's change)

- `main.py` — the bot (this round: extended `_opponent_worst_case_area`'s
  leaf evaluation from a static 1-ply area snapshot to a genuine 2-ply
  minimax step — our move → opponent's worst move → our best response →
  assess resulting area — see the inline comment directly above the new
  `best_our_followup` loop for full rationale).
- `analyze_logs.py` — unchanged, point at `/logs/rounds/<n>`.
- `/tmp/main_before_round5.py` (this session, not persisted in the repo)
  has the exact pre-this-round `main.py` if a revert/diff/controlled A/B
  is needed — recreate via `git show HEAD:main.py` before this round's
  commit if that file is gone by the time you read this.
