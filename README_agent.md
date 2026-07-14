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
