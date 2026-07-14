# Agent Notes (condensed)

**IMPORTANT:** This file was condensed from a 7500+ line history that had
grown unwieldy across ~50 sessions. The FULL verbose history (every past
session's detailed writeups, all root-cause investigations, all A/B test
results) is preserved in `docs/HISTORY_ARCHIVE.md` -- search it if you
want deep detail/precedent on any specific topic mentioned below. This
file should stay SHORT: append only a brief summary of what you did each
session, and move anything long-form into the archive.

## Always do this first
```bash
python3 tools/analyze_logs.py
```
Ground truth on real round results. Opponent NAME AND BEHAVIOR CHANGES
almost every session -- never trust old prose about "the opponent" below,
always re-derive fresh.

## Current bot architecture (main.py, ~1050 lines)
Greedy 1-ply heuristic + several supplementary lookahead/adversarial
layers, refined over ~50 sessions of real-match-loss-driven debugging.
Pipeline per move:
1. Enumerate physically-legal candidates (in-bounds, not self/opponent-
   body-blocked; tail cells treated as vacating unless the snake just ate).
   **No hard categorical pre-filter on ANY risk factor** -- every legal
   candidate always competes on score together (a past hard h2h filter
   bug caused a certain-death trap to be the ONLY pool option once).
2. Per-candidate BFS flood-fill (`_flood_fill`, uncapped) -> `space`,
   `reached_tail`, `exits` (open neighbors), reachable food set.
3. `will_eat` detection: if landing on food, our tail doesn't vacate this
   turn -- flood-fill accounts for this (own tail treated as blocked).
4. `_lookahead_min_space`: bounded (depth 6, deeper if we have a
   dominant length advantage) forward simulation -- our future self
   greedily maximizes space (+ mild exits preference), opponents modeled
   adversarially (worst-case-for-us) each simulated step. Used as
   `effective_space = max(space, lookahead_space) if will_eat else space`
   to fix a real bug where eating food looked falsely-dangerous at 1-ply.
   Also a smaller supplementary score penalty
   `-lookahead_weight * (my_len - lookahead_space)`, weight/depth scaled
   UP when we have a big dominant length advantage over the opponent.
5. Hard space-safety tiers using `effective_space`: `-1000/cell` if
   `< my_len`, `-20/cell` if `< 1.5x my_len`.
6. Adversarial 1-ply `worst_space` (opponent's own best/worst legal move)
   + `_opp_two_ply_reachable` contested-exits penalty (`-150` if an
   equal/longer opponent could also reach our only exit).
7. Corner/dead-end food-trap penalties: eating food that lands on a
   `exits<=1` cell: `-70` (health-gated, fades to 0 by health<=40);
   `exits==2`: `-25` (same gating). **Do NOT increase these past ~70/25
   without an 15-20+ seed self-play A/B** -- a 260/90 version was shipped
   once, caused a real-round regression, and had to be reverted.
8. Head-to-head danger (`_opp_candidate_cells` + `_predict_opp_move`,
   simple nearest-food-else-center opponent-move predictor): if a
   candidate matches the opponent's PREDICTED move: heavy penalty; if
   merely one of their other legal moves: lighter penalty. Values differ
   for equal-length (mutual-elimination draw risk) vs strictly-longer
   (certain-loss) opponents:
   - Longer opponent: 900.0 (predicted) / 300.0 (legal-but-unlikely).
   - Equal-length opponent: 300.0 / 90.0 (softened over several sessions
     from an original flat 900/300 -- equal-length collision is a DRAW,
     not a loss, so being this cautious was costing food-race contests).
     **This lever is sensitive**: 450/150 helped a real round; a further
     push to 300/100 for a DIFFERENT opponent was rejected via self-play
     A/B (2/7); 350/110 then 300/90 helped for opponent `TheApX__hungry`
     across two sessions with positive self-play A/B each time. Move in
     SMALL increments only, always validate via self-play A/B first.
9. Food attraction: `growth_damp * urgency * (130.0/(nearest+1))`, only
   counting REACHABLE food (fixed a symmetric-orbit starvation-draw bug
   where unreachable walled-off food kept "winning" as nearest-food
   target). `urgency` ramps up steeply as health drops. Coefficient
   history: 20 -> 55 -> 90 -> 130 across several sessions, each time
   fixing a real "under-eating"/growth-rate-disadvantage loss pattern
   against a specific opponent, each validated via self-play A/B before
   shipping. NOT confirmed to help indefinitely -- one session found
   pushing further (for `coreyja__famished-frank`) validated positively
   in self-play but did NOT improve the real round (self-play can be a
   misleading proxy for a genuinely strong/fast-growing opponent).
10. `growth_damp`: softens food-urgency once we're already big
    (`my_len > 25% of board`) AND ahead of the longest opponent, plus an
    extra advantage-gated damping term for a DOMINANT lead. **This lever
    has been pushed harder at least twice and BOTH times regressed
    clearly in self-play A/B (36.6%, and untested-directly-but-implied)
    -- do not strengthen further without a fundamentally different
    validation method.**
11. Edge/corner avoidance bonus, boosted 0.3->4.0 when a comparable-size
    threat is within Manhattan distance 5 (`threat_near`).
12. `_HEAD_HISTORY` anti-stalemate: if stuck in a small position loop
    (<=5 unique cells over 16 turns), bonus for moves that break out.
13. Exception-safe fallback (`except Exception: return {"move": "up"}`,
    plus a "no legal moves, pick least-bad in-bounds direction" branch).

## The one big remaining unsolved failure class
**"Dominant-length self-trap":** across dozens of sessions/opponents, the
single most common remaining loss pattern is: our snake gets MUCH longer
than the opponent (often 3x-10x+), health is comfortable, and ~20-40
turns later it dies coiled in a self-made spiral/corridor with zero
escape -- confirmed via `tools/replay_frame.py --last` showing ZERO legal
moves at the final logged frame in the vast majority of these losses.
Root cause: a single-snapshot (even 1-ply-adversarial, even the bounded
`_lookahead_min_space`) flood-fill cannot see that a large-looking open
region will narrow to nothing several turns later as OUR OWN body
continues consuming the corridor while we advance through it.

**Already tried and REJECTED (via direct self-play A/B, confirmed
regressions, do not re-attempt without a fundamentally different
validation method):**
- Strengthening `growth_damp`'s dominant-advantage extra-damping further: 36.6% win rate.
- Strengthening `_lookahead_min_space`'s dominant-advantage weight/depth scaling further: 0/8.
- Scaling the generic `exits<=1`/contested-exits penalty by the same advantage factor: 35.7%.

All three failed for the same likely reason: self-play (two identical,
symmetric, equally-aggressive bots) is a poor proxy for the real
scenario (a persistently small/passive/slow-growing real opponent) --
"be more cautious while ahead" just means losing a fair growth race
against an equally-aggressive self-play mirror, even if it might help
against the real trigger scenario.

**Better validation tool (built + confirmed effective in a past
session):** `tools/passive_opponent.py` -- a bot that deliberately avoids
food unless health<=40, so it stays small/passive like the real
opponents that trigger this bug. Reproduces the dominant-length
self-trap at roughly 1-in-4 to 1-in-6 local games (vs ~8-15% in real
rounds) -- MUCH faster feedback than waiting for real rounds. Use this
(not self-play) to validate any future fix attempt for this failure
class:
```bash
setsid nohup env PORT=X python3 main.py > /tmp/my.log 2>&1 < /dev/null &
setsid nohup env PORT=Y python3 tools/passive_opponent.py > /tmp/pas.log 2>&1 < /dev/null &
disown -a; sleep 1
timeout 20 ./game/battlesnake play -W 11 -H 11 --name my --url http://localhost:X \
    --name passive --url http://localhost:Y -g standard --seed N -o /tmp/pg_N.jsonl
python3 tools/replay_frame.py /tmp/pg_N.jsonl --name my --last   # check if it reproduced
```

**Still-unimplemented "textbook correct" fix (flagged by ~10 sessions,
never attempted at full scale):** genuine recursive N-turn self-play
simulation using the bot's OWN FULL scoring function (not a simplified
proxy -- a pure space-maximizing proxy AND a whole-region corridor-shape
metric have both been tried and DISPROVEN as adequate substitutes on
real failing examples). Would need careful performance profiling
(recursive calls are much more expensive than the current cheap
lookahead proxy) and thorough self-play + passive-opponent validation
before shipping, given move-timeout forfeits are a much worse failure
mode than the self-trap losses it might fix. This remains the single
highest-potential-value, highest-risk investment not yet attempted.

## Tools available
- `tools/analyze_logs.py` -- win/loss/draw + turn-count summary per round.
  Run first, always.
- `tools/replay_frame.py` -- replay a real (or locally-generated) sim
  file frame through `main.move()` directly. `--last` finds our last
  frame and checks if we already had 0 legal moves (classic self-trap
  signature). `--turn N` replays a specific turn. `--diag` dumps
  per-candidate space/reached_tail/will_eat. `--name X` for non-
  `sonnet-5`-named snakes (e.g. local test games).
- `tools/passive_opponent.py` -- local passive/food-avoidant stand-in
  opponent, specifically useful for the dominant-length self-trap class
  (see above). Restart its server after editing (no hot-reload).
- `tools/opponent_ref.py` -- old naive/self-destructing reference bot,
  only useful as a trivial smoke test (games end in ~5 turns), NOT
  useful for any health/long-game/self-trap investigation.

## Validation methodology (proven, use for ANY scoring-weight change)
1. Fix a concrete, diagnosed root cause (replay real losing sim frames
   via `tools/replay_frame.py`, find the exact pivotal turn+decision).
2. `ast.parse` syntax check.
3. Fuzz test: run several hundred randomized synthetic board states
   through `move()` directly, check for exceptions.
4. Performance check: time `move()` on long snakes (40-70 segments) +
   multiple opponents, confirm well under any realistic move timeout.
5. **NEW-vs-OLD self-play A/B** (save a pristine pre-change copy to
   `/tmp/oldbot/` -- remember to also copy `server.py`, since `main.py`
   imports `from server import run_server` -- run both concurrently via
   the real `game/battlesnake` CLI for 10-20 seeds, count wins). This has
   caught real regressions from "looked good in theory" changes MANY
   times across this project's history. For the dominant-length-self-trap
   class specifically, use `tools/passive_opponent.py` instead/also (see
   above), since self-play has been shown to be misleading for that one
   specific failure class.
6. Only ship if the A/B shows a real (not noise-level, ideally >60%)
   positive result, or if it's a purely-additive safety check that
   cannot make any existing correct decision worse (e.g. adding a new
   supplementary penalty term with a small weight).
7. If a change is later found to be a regression in a subsequent
   session (compare consecutive real rounds' `results.json`), revert
   immediately -- this has happened at least once (a corner-food-trap
   penalty bump from 70/25 to 260/90 was shipped without an A/B, caused
   a real regression, and was reverted next session).

## Environment / process gotchas (all reconfirmed many times)
- Use `setsid nohup env PORT=X python3 SCRIPT.py > /tmp/x.log 2>&1 < /dev/null &`
  followed by `disown -a` to launch background test servers reliably
  across tool calls. Use a fresh/unused port each batch.
- Clean up via `ps aux | grep python3` + `kill -9 <PID>` directly by PID.
  **Do NOT use `pkill -f "<pattern>"`** if the pattern text (e.g. a port
  number) might appear in your own current shell command line -- it can
  SIGKILL your own command mid-execution (exit 137, silent).
- `git stash` will revert uncommitted `main.py` changes if run casually
  (e.g. just checking status) -- prefer `git diff`/`git status` only, or
  use `git show HEAD:main.py > /tmp/oldbot/main.py` for a clean baseline
  copy without any stash risk.
- The outer `try/except Exception: return {"move": "up"}` in `move()`
  silently swallows real bugs in your OWN debug instrumentation too, not
  just genuine edge cases -- if a debug print never fires or you get
  suspiciously-uniform "up" results while testing, check for a hidden
  exception (temporarily replace the try/except with `if True:` in a
  scratch copy to surface it).
- Sim log files don't always log every turn for our snake -- if
  `tools/replay_frame.py --last` shows 0 legal moves, the actual fatal
  decision happened earlier and may not be recoverable from that file.

## Session log (most recent first, keep brief -- 5-10 lines per session)

**Session (round 1, NEW opponent `tyrelh__tyrelh-python`, first time seeing
this name -- round 0 results: 209W/31L/10D = 83.6% win rate, strong):** Ran
`tools/analyze_logs.py` first (only round 0 exists so far). Triaged all 31
losses via `tools/replay_frame.py --last`: **this is a DIFFERENT failure
class than the historically-documented "dominant-length self-trap"** --
in every loss checked (sim_105/153/233/96/22/48/24/244/65/223), my_len was
roughly EQUAL to or slightly LESS than opp_len (e.g. 6v7, 7v8, 21v22,
23v24), not massively ahead. These look like genuine close head-to-head
races where the opponent is a comparably-strong, comparably-fast-growing
snake (unlike prior opponents' `README`-documented small/passive/slow
profiles) -- so `tools/passive_opponent.py` may be a WORSE proxy for THIS
specific opponent than for previous ones; self-play is probably the more
representative validation method here.
Deep-dived one short loss (`sim_153`, turns 21-27) via `--diag`: at turn
22 our snake (len 6) had 3 legal moves all reporting IDENTICAL
`space=111, reached_tail=True` (up/down/right from (5,1), opponent at
(6,2), so `threat_near` and the 4.0 edge-avoidance weight WERE active) --
picked 'down', which walked along the bottom wall (y=0) rightward over
several turns into the bottom-right corner area, ending with only 1
legal move at turn 26, and the opponent (which had grown to len 7) took
the one escape cell via head-to-head at turn 27 for a clean forced kill.
The existing `exits`/`contested_exits` penalties and the threat-aware
edge_weight bonus (see main.py comments ~line 607-627) are already
designed to discourage exactly this, but evidently weren't enough to
outweigh whatever pulled us down/right (likely food attraction or the
degenerate space-tie not distinguishing corridor-narrowing risk this far
ahead) in this specific instance. Did NOT change scoring weights this
session -- given the extensive prior-session history of tuning these
exact levers backfiring in self-play A/B for OTHER opponents (see
sections above), and limited remaining step budget to properly A/B a new
change against this brand-new opponent, judged it safer to just document
this concrete repro case for a future session with more budget to
implement+validate a targeted fix (e.g. an extra penalty for "committing
to a 3rd+ consecutive move flush against the same wall while a
comparable/longer threat is within radius 5" -- distinct from the
existing single-step edge_weight bonus, which apparently didn't fire
strongly enough here since all 3 candidates scored as an exact tie on
the coarse space/reached_tail metrics).
Verified no regressions: `ast.parse` OK, 3/3 smoke wins vs
`tools/opponent_ref.py`, no exceptions in server logs. **No functional
changes shipped this session** (docs/analysis only, given 83.6% is
already a strong baseline and the new opponent's failure mode needs a
properly-validated fix, not a rushed one).
**For next teammate:** (1) opponent name is `tyrelh__tyrelh-python` --
re-run `tools/analyze_logs.py` fresh if round 1 has new logs by the time
you start, don't assume this opponent's behavior is unchanged. (2) The
concrete repro for the "wall-hugging corner trap despite tied
space-metric candidates" loss class is `/logs/rounds/0/sim_153.jsonl`,
turns 21-27 -- use `tools/replay_frame.py --turn N --diag` to inspect.
(3) Since this opponent seems comparably strong/fast-growing (not
passive), self-play A/B is probably a decent proxy here (unlike for the
old dominant-length-self-trap class) -- worth trying self-play A/B for
any fix to this specific corner-trap pattern before shipping.


**Session (round 2, opponent still `joshhartmann11__battlejake`, elo #17,
rung 34/50):** Ran `tools/analyze_logs.py` first: rounds 0 and 1 both
strong wins (224W/23L/3D = 89.6%, then 228W/22L/0D = 91.2%) against this
same opponent. Given the very high win rate and the extensively
documented history of 3+ prior sessions' tuning attempts on the
"dominant-length self-trap" failure class all being REJECTED via
self-play A/B (see section above -- do not re-attempt those specific
levers without a fundamentally different validation method), made **no
scoring/weight changes** this session to avoid risking a regression on
an already-strong bot (per tip #3 in the task instructions). Instead did
verification only:
- `ast.parse` syntax check: OK.
- 3/3 smoke-test wins vs `tools/opponent_ref.py` (naive baseline), no
  exceptions in server logs.
- 8-game batch vs `tools/passive_opponent.py` (the dominant-length-
  self-trap repro tool): 7/8 wins, 1 loss reproduced the known exact
  self-trap signature (my_len=39 vs opp_len=8, health=99, 0 legal moves
  at death, via `tools/replay_frame.py --last`) -- consistent with the
  ~1-in-6-to-1-in-8 documented base rate, not a new or worsening bug.
**For next teammate:** bot is unchanged from round 1's committed
version. The one remaining significant lever not yet attempted at full
scale is still the "genuine recursive N-turn self-play simulation using
the bot's own full scoring function" idea flagged in the section above
-- worth attempting if you have a full 30-step budget available and can
do thorough performance profiling + passive-opponent + self-play
validation before shipping (given move-timeout forfeits are a worse
failure mode than the rare self-trap losses it targets). If you don't
have that much budget, the safe default (given ~90% real win rate two
rounds running) is what this session did: verify no regressions, don't
touch the scoring weights blindly.

**Session (opponent `joshhartmann11__battlejake`, round 0: 224W/23L/3D,
89.6%):** Ran `analyze_logs.py` for ground truth. Triaged all 26
non-wins: 25/26 had ZERO legal moves at the last logged frame, my_len
massively exceeding opp_len in every one (e.g. 43 vs 12, 39 vs 15) --
confirmed this is the same, extensively-documented "dominant-length
self-trap" failure class (see above), for which 3+ previous sessions
already tried and cleanly rejected 3 different tuning levers via
self-play A/B. Confirmed the previously-implemented `effective_space`
fix (lets `_lookahead_min_space` override a falsely-pessimistic 1-ply
food-eating space reading) is intact. Ran a fresh 6-game batch vs
`tools/passive_opponent.py`: 5/6 wins, the 1 loss reproduced the exact
same dominant-length self-trap pattern (my_len 30 vs opp_len 7, health
99, 0 legal moves at death) -- consistent with known behavior, not a new
bug. Given the strong precedent of blind tuning attempts backfiring on
this exact failure class, made **no functional changes to `main.py`**
this session. Instead: condensed this file from 7526 lines down to a
manageable summary (moved full verbose history to
`docs/HISTORY_ARCHIVE.md` for reference) since the file had become
unwieldy to read each session. Ran standard regression tests
(`ast.parse`, 3/3 vs `tools/opponent_ref.py`, no exceptions in any server
log) -- all passed. **For next teammate:** if you want to seriously
tackle the dominant-length self-trap class, this file's "big remaining
unsolved failure class" section above has the full context + the one
concrete recommended next step (use `tools/passive_opponent.py` for
validation, consider genuine recursive self-play simulation) -- also
check `docs/HISTORY_ARCHIVE.md` (search "dominant-length self-trap" or
"adv_scale") for exhaustive prior-session detail if needed.

**Session (round 2, opponent `tyrelh__tyrelh-python`, still rung ~as
before -- round 0: 209W/31L/10D 83.6%, round 1: 209W/27L/14D 83.6%,
stable/strong):** Ran `tools/analyze_logs.py` first (per instructions).
Win rate held steady across rounds 0 and 1 (no regression from round-1's
"no functional changes" session). Triaged all 27 round-1 losses:
confirmed (again) these are NOT the old "dominant-length self-trap"
class -- in every loss, my_len was close to opp_len (equal or off by
1-2), consistent with round-1's finding that this specific opponent is a
comparably-strong, comparably-fast-growing snake.

Deep-dived a concrete new repro, `/logs/rounds/1/sim_49.jsonl` (turns
88-94, both snakes len ~10-11): bot walked along the bottom wall
(y=0) rightward for 3+ consecutive turns while a same-length opponent
approached, ending 0-legal-moves-dead at turn 94 -- same surface
"wall-hugging corner trap" symptom flagged in round-1's session for
`sim_153.jsonl`. But this time I actually instrumented `main.py`'s
scoring loop with temporary debug prints (see method below) and found
the ROOT CAUSE precisely, which is more specific than round-1's
writeup: at turn 90, head=(4,0), 'up'->(4,1) and 'right'->(5,0) both
report identical `space=102, reached_tail=True`, but they get WILDLY
different final scores (111 vs 249) -- NOT primarily from food/edge
terms (those are small and if anything favor 'up'), but from the
**bounded `_lookahead_min_space` term**: for 'up', the adversarial
forward simulation predicted `lookahead_space=0` (a hard future trap),
costing ~165 points; for 'right', the same simulation predicted
`lookahead_space>=my_len` (no penalty at all). In actual real-game play,
BOTH directions were apparently doomed (the bot picked 'right' repeatedly
over the next few turns and still died at turn 94, well within the
lookahead's own depth-6 window) -- i.e. **the lookahead's own bounded
forward simulation gave a false negative for 'right'**: it assumes our
*future self* greedily maximizes space at each simulated step, but the
REAL future self is driven by the full scoring function (food
attraction, edge terms, etc.), which in this exact position kept
choosing to hug the same wall rightward instead of maximizing space --
so the simplified proxy's predicted trajectory diverged from the
policy's actual trajectory, and the trap it should have caught 4 turns
later was invisible to it.

This is a concrete, reproducible instance of the long-flagged
"still-unimplemented textbook correct fix" idea in the "big remaining
unsolved failure class" section above (genuine recursive self-play using
the bot's OWN full scoring function instead of a simplified
space-maximizing proxy) -- except here it applies to a close-race
wall-hugging trap, not just the old dominant-length self-trap. This is
the first session with a fully concrete, instrumented, byte-level root
cause for this failure mode (previous sessions only had the
surface-level "wall-hugging" symptom, not the specific mechanism/lever).

**Did NOT ship a fix this session** (only ~5 steps of budget left after
the investigation) -- deliberately, per the validation methodology in
this file: any change to `_lookahead_min_space`'s internal simulated
policy is exactly the kind of change that needs full self-play A/B +
passive-opponent validation + perf profiling before shipping, and I did
not have the budget left to do that responsibly this session.

**Debug method used (reusable for next teammate)**: copy `main.py` to a
scratch path (e.g. `/tmp/dbgmain.py`), insert
`if os.environ.get('DBG'): print(...)` lines after specific score-mutating
lines (grep `main.py` for `score += \|score -= ` to find them all), copy
`tools/replay_frame.py` to a scratch path and redirect its
`import main as M` to import the scratch module instead, then run with
`DBG=1 python3 /tmp/dbg_replay.py <simfile> --turn N --diag`. This
gives a full per-term score breakdown per candidate direction, not just
the coarse space/reached_tail numbers `--diag` already prints -- much
faster than hand-tracing the scoring loop by eye. Recommend adding a
permanent `DBG` env-var-gated verbose mode directly into `main.py` itself
in a future session (behind the env var so it's zero-cost/silent in
real matches) so this doesn't need to be re-created from scratch each
time.

**For next teammate:** (1) Re-run `tools/analyze_logs.py` fresh -- don't
assume opponent/behavior unchanged. (2) The concrete, mechanistically-
diagnosed repro is `/logs/rounds/1/sim_49.jsonl` turn 90 (see above) --
a great test case for validating any future fix to
`_lookahead_min_space`'s internal simulated policy, since we now know
EXACTLY which internal term (the lookahead proxy's false-negative) is
responsible, not just the surface symptom. (3) Any fix attempt should
make the lookahead's simulated future-self use (a cheaper approximation
of) the REAL scoring function's actual move preferences instead of pure
space-maximization, per the long-standing "still-unimplemented" idea --
validate via self-play A/B AND replaying this exact sim_49/sim_153
scenario through `--diag` to confirm the false-negative is fixed, AND
performance-profile since recursive scoring is much more expensive.
(4) No functional changes shipped this session -- `main.py` is
byte-identical to round 1's committed version.

**Session (round 1, opponent zakwht__zakwht-2018, round 0: 214W/36L,
85.6%):** Ran `tools/analyze_logs.py` -- only round 0 exists (new
opponent). Triaged all 36 losses via `tools/replay_frame.py --last`:
consistently CLOSE-race deaths (my_len within 0-1 of opp_len at death,
e.g. 19v20, 10v11, 8v9) -- same general "wall-hugging trap" class
documented for opponent `tyrelh__tyrelh-python` in earlier sessions
(search README/archive for `sim_49`/`sim_153`), NOT the old
"dominant-length self-trap". Deep-dived `sim_143.jsonl` turns 85-88 in
full detail (debug-instrumented copy technique, see archive): at turn 85
(head (2,1), len 9, health 97, opp len 10 at distance 6 i.e. just
OUTSIDE the existing `threat_near` radius-5 gate), candidates were
`down` (eats food at (2,0), ON the y=0 wall, space=103, will_eat=True,
score~316) vs `left`/`right` (space=104, reached_tail=True, no food,
score~277/271) -- bot ate the wall food, then got pulled rightward along
the same wall for 2 more turns by the same dynamic while the opponent
closed in from the other side, ending in a 0-legal-moves death 3 turns
later. Confirmed via `docs/HISTORY_ARCHIVE.md` (search "Spenca") that
a previous session found widening the `threat_near` radius does NOT fix
this pattern (food-attraction magnitude dominates, not edge-weight) --
so did NOT retry that. Instead implemented the ALTERNATE fix that same
archived session explicitly flagged as untried: a small, health-gated
penalty (fades to 0 by health<=40, same `safety_margin` pattern as the
existing exits<=1/exits==2 food-trap penalties right above it in
main.py) specifically for eating food that lands ON a boundary wall
cell (`x in (0,width-1) or y in (0,height-1)`), regardless of `exits`
count. Tuned magnitude (-55 * safety_margin) by direct measurement via
`tools/replay_frame.py --diag` against the exact `sim_143` turn-85
scores (-40 was insufficient to flip the decision, i.e. left the ~40-
point food-bonus gap too small a margin; -55 flips `down`->`left` in
this exact real case) -- confirmed via a debug-print-instrumented scratch
copy of main.py (`/tmp/main_dbg.py`, see technique in earlier session
notes) that showed the raw per-candidate scores.
**IMPORTANT CAVEAT for next teammate -- this was NOT validated via
NEW-vs-OLD self-play A/B or passive-opponent batch this session** (ran
out of step budget after the diagnosis + implementation + syntax/fuzz
checks). Only checks done: `ast.parse` OK, 200-iter random-fuzz `move()`
smoke test with no exceptions, confirmed the exact `sim_143` turn-85
decision flips as intended. Per this file's own documented methodology
(section "Validation methodology"), this is NOT yet a fully-validated
change and carries real regression risk (a similar-looking
corner-food-trap penalty bump was shipped without A/B once before and
had to be reverted, see archive) -- **next session should run a 10-20
seed NEW-vs-OLD self-play A/B (old version = `git show HEAD:main.py`
before this session's commit) before trusting this further, and ideally
also re-run `tools/analyze_logs.py` on the resulting round to see if the
win rate improved, held steady, or regressed vs this round's 85.6%.** If
it regresses, the single line to look at is the new `if will_eat and
(npt[0] in (0, width - 1) or npt[1] in (0, height - 1)):` block
immediately after the `exits==2` food-trap penalty in the scoring loop
(easy to find via `grep -n "Food-on-wall penalty" main.py`) -- revert by
deleting that block (and its `safety_margin` line) if so.

**Session (round 2, opponent zakwht__zakwht-2018, round 0: 214W/36L
85.6%, round 1: 194W/56L 77.6% -- REGRESSION detected):** Ran
`tools/analyze_logs.py` first per instructions -- immediately noticed
round 1's win rate dropped 8pp vs round 0 (85.6% -> 77.6%) against the
SAME opponent, which is a red flag since this opponent's behavior
presumably didn't change. Checked `git diff HEAD~1 HEAD -- main.py`:
round 1's session shipped exactly one change, the "Food-on-wall penalty"
block (`-55.0 * safety_margin` for `will_eat` candidates landing on a
boundary wall cell) -- and that session's own commit notes explicitly
flagged it as **NOT validated via NEW-vs-OLD self-play A/B**, only
confirmed to flip one specific real-loss decision (`sim_143` turn 85).

Ran the recommended-but-skipped validation this session: NEW (with the
food-on-wall penalty, i.e. round-1-committed `main.py`) vs OLD (`git show
HEAD~1:main.py`, i.e. round-0-committed baseline) head-to-head via the
real `game/battlesnake` CLI, 35 seeds (1-20, then 21-35):
**new_wins=10, old_wins=24, draws=1 (~28.6% for the new/penalized
version)** -- a clear, consistent, non-noise-level regression, matching
the real round 0->1 win-rate drop almost exactly. This confirms the
food-on-wall penalty was a genuine net-negative change, not just
opponent variance.

**Action taken: REVERTED the food-on-wall penalty block entirely**
(`main.py` is now byte-identical to `git show HEAD~1:main.py`, i.e. the
round-0-committed version that scored 85.6%). Rationale for full revert
rather than re-tuning the magnitude: the block's own stated purpose (bias
away from wall-adjacent food when a non-wall alternative exists) is
already substantially covered by the existing edge/corner avoidance bonus
and the exits<=1/exits==2 food-trap penalties directly above it in the
scoring loop -- the new term was apparently double-penalizing/over-
correcting a case the existing terms already handle adequately, per this
A/B result. Verified: `ast.parse` OK, `diff` against `HEAD~1:main.py`
shows zero differences, 3/3 smoke-test wins vs `tools/opponent_ref.py`,
no exceptions in any server log during the 35-game A/B or the smoke test.

**Lesson reinforced for future sessions:** this is now the SECOND
documented instance (see the 260/90 corner-food-trap-penalty revert
mentioned in the "Validation methodology" section above) of an
un-A/B-validated scoring change getting shipped and causing a real
measurable regression the very next round. **Do not ship any scoring-
weight change without running the NEW-vs-OLD self-play A/B first**, even
under step-budget pressure at the end of a session -- an unvalidated
change is worse than no change, since the "no functional changes" option
is always safe and was explicitly available.

**For next teammate:** (1) Re-run `tools/analyze_logs.py` once round 2's
results land -- expect a return to something close to round 0's 85.6%
now that the regression is reverted (if not, the regression had a
different cause and needs fresh investigation via
`tools/replay_frame.py --last` on round 2's losses). (2) `main.py` is
now IDENTICAL to the round-0-committed version -- all the round-1
session's diagnostic writeup (sim_143 turn 85, the specific wall-food
mechanism) is still valid/interesting context if you want to design a
BETTER-validated fix for that exact scenario, but any such fix must go
through the A/B test above (or an equivalent one) before shipping this
time. (3) The close-race "wall-hugging trap" investigations from the
`tyrelh__tyrelh-python` sessions (search `sim_49`, `_lookahead_min_space`
false-negative) are a separate, deeper, still-unfixed issue -- not
addressed this session, still open for a future session with a full
budget for careful implementation + perf profiling + multi-method
validation.
