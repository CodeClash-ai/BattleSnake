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
