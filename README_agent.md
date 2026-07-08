# Agent Notes (Round 1 - opus-4-8)

## Game
- BattleSnake standard 11x11, 1v1 vs `pambrose__pambrose-kotlin`.
- Ruleset: foodSpawnChance=15, minimumFood=1, timeout=500ms.
- Coords: y-up, bottom-left origin. up=y+1, down=y-1, left=x-1, right=x+1.

## Opponent
- The opponent is the naive pambrose SimpleSnake: NO collision avoidance,
  targets the FARTHEST food, x-dominates-y priority. It routinely walks into
  walls and itself. A basic survival bot should beat it easily.
- Round 0 baseline (both bots identical naive) was a Tie 80 vs 76.

## What I did
- Rewrote `main.py` into a proper survival bot:
  - Filters lethal moves (walls, bodies; tails treated as vacating unless
    the snake is at health==100 i.e. just ate).
  - Flood-fill of reachable free space from each candidate head cell to avoid
    getting trapped (dominant scoring term).
  - Head-to-head logic: contest H2H only when strictly longer (+60), avoid
    equal-length (mutual death, -200) and losing (-400).
  - Food/health: hunger urgency scales as health drops.
  - Mild edge penalty + central control preference.
- Backed up original naive bot as `main_old_naive.py`.

## Files
- `main.py` - the live bot.
- `main_old_naive.py` - original naive bot (opponent equivalent).
- `run_test.sh N` - harness to play N games new-vs-naive using ./game/battlesnake.
  NOTE: the background-server lifecycle in this sandbox is finicky (each bash
  command is a fresh subshell that kills bg children on exit). The servers
  DO run fine when launched from /workspace with correct cwd; if run_test shows
  all ties, it's the harness not finding a live server, not the bot. Verify bot
  logic instead with direct `from main import move` unit calls (examples below).
- Manual unit test example:
  python3 -c "from main import move; print(move({...gamestate...}))"

## Ideas for next teammate
- Add lookahead/minimax (depth 2-3) for better H2H trapping.
- Cache flood-fill; consider "chase own tail" endgame to survive longer.
- Actively trap the naive opponent (it's predictable: farthest-food, x>y).
- Fix run_test.sh server lifecycle (use setsid/nohup or a single long-lived
  server started in one command that also runs all games).

## Round 2 (opus-4-8) - CRITICAL FIXES
- **FIX 1**: main.py was MISSING the `if __name__ == "__main__"` server block ->
  round 1 scored 0 (invalid submit). RE-ADDED it. NEVER remove that block.
- **FIX 2**: Self-collision on turn ~2. At spawn, body segments stack on one
  cell, so tail "vacating" logic wrongly allowed moving onto neck. Added:
  (a) explicit neck-forbid (body[1] never allowed),
  (b) safe_tails = only tails whose cell count <= 1 (not stacked).
- Result vs naive: was 6/12; now **20/20 wins**.
- Verify before submit: `python3 -c "import main"` and check server starts
  (`python3 main.py` prints "Running Battlesnake").

## Round 3 (opus-4-8)
- R2 result: **WON 250-0** (all 250 sims). Opponent (naive pambrose)
  self-destructs into walls by turn ~4; opus NEVER dies (verified via
  /logs/rounds/2 analysis). Our bot is dominant.
- Verified current main.py: import OK, server block present. DO NOT remove it.
- Change made: improved the "no strictly-safe move" FALLBACK to pick the
  in-bounds move with the most flood-fill reachable space (was: first legal).
  Only affects near-death corners; no effect on normal play. Backup:
  main_r2_backup.py.
- **RELIABLE TESTING**: the HTTP harness (run_test.sh) does NOT work in this
  sandbox (background servers get killed at subshell exit; all games show tie).
  Instead use `python3 sim_offline.py` — an in-process game simulator
  (me vs main_old_naive.py). Currently reports 40/40 wins. Edit the load()
  path to test vs any other bot (e.g. main_r2_backup.py).
- Sanity vs r2 backup: ~18-19-3 (symmetric, no regression).

## Advice for next teammate
- The bot already wins 250/0. LOWEST-RISK play = submit as-is (just confirm
  `python3 -c "import main"` works and __main__ block present).
- If improving: use sim_offline.py to validate, never the HTTP harness.
- Possible upgrades: active trapping of the predictable naive opponent,
  minimax lookahead. But diminishing returns given 250/0.

## Round 4 (opus-4-8)
- R3 result: **WON 250-0** again (confirmed via /logs/rounds/3/results.json).
  analyze3.py (now points to round 3) shows survives:250 dies:0 — we NEVER die.
- Verified: `import main` OK, `python3 main.py` prints "Running Battlesnake",
  __main__ block present (line 249), move() has try/except -> "up" fallback.
- sim_offline.py: 40/40 wins, unchanged.
- DECISION: bot is fully dominant (250-0, zero deaths). Made NO code changes to
  main.py to avoid any regression risk. Submitted as-is.
- Next teammate: safest play is same — verify import + server + __main__ block,
  run sim_offline.py, then submit. Only touch main.py if you find an actual
  failure case (there are none against the naive pambrose opponent).

## Round 5 (opus-4-8) - FINAL
- R4 result: **WON 250-0** again (confirmed /logs/rounds/4/results.json).
- Verified: import OK, server starts, __main__ block (line 249), move() try/except.
- sim_offline.py: 40/0 wins, unchanged.
- DECISION: bot remains fully dominant (250-0, zero deaths, 4 rounds straight).
  Made NO code changes to avoid regression risk. Submitted as-is.

## NEW GAME SERIES — Round 1 (opus-4-8) — READ THIS FIRST
- **IMPORTANT**: This is a NEW opponent. All the notes ABOVE about the
  `pambrose-kotlin` opponent are from a PREVIOUS/DIFFERENT match series.
- **Current opponent: `Nettogrof__nessegrev-julia`** (Julia bot).
- Round 0 baseline result (/logs/rounds/0/results.json): **WON, score 34-0**.
  I wrote `analyze_new.py` (opponent-aware) — 34 games, 34 wins, 0 losses, 0 ties.
- Opponent behavior (from analyze_deaths.py): it mostly **self-destructs into
  walls/corners** early. Death-turn distribution: turn 2 (x11), turn 6 (x10),
  turn 10 (x9), plus a few long games (48/63/81 turns). In EVERY game the
  opponent dies and our bot survives. Zero deaths for us.
- Long games (sim_228/229/230): we survive to turns 48-81 with the opponent
  already dead; our flood-fill anti-trap keeps us alive indefinitely.

## New analysis tools I added
- `analyze_new.py` — win/loss/tie counter for the CURRENT opponent
  (Nettogrof-julia). Run: `python3 analyze_new.py`.
- `analyze_deaths.py` — shows where/when the opponent dies (head pos + turn).
- `check_long.py` — inspects the longest games' final states.

## Round 1 decision (opus-4-8)
- Bot wins 34-0 with zero deaths vs the current opponent. The existing
  flood-fill + H2H + hunger logic in main.py is fully dominant.
- Verified: `import main` OK; `python3 main.py` serves + returns correct info
  JSON; move() returns valid moves; try/except -> "up" fallback present;
  __main__ block at line 249 present. Edge-case tests (corner escape, low
  health food-seeking) pass.
- sim_offline.py still 40-0 vs naive (no regression).
- **DECISION: made NO changes to main.py** — no reason to risk regression on a
  34-0 dominant bot. Only added analysis tools + this documentation.
- Next teammate: safest play = verify import/server/__main__, run analyze_new.py
  on the latest /logs/rounds/, then submit. Only touch main.py if you find an
  actual loss in the logs (there are none so far).

## NEW SERIES — Round 2 (opus-4-8)
- R1 result (/logs/rounds/1/results.json): **WON 38-0**, zero losses/ties
  (verified via /tmp/an1.py = analyze_new.py pointed at rounds/1).
- Opponent (Nettogrof-julia) dies even FASTER now: death-turn dist {2:x, 6:x, 10:x};
  avg game length only 5.6 turns. It self-destructs into walls/corners early.
- Verified: import OK; `python3 main.py` prints "Running Battlesnake";
  __main__ block at line 249; move() try/except fallback present.
- Edge tests pass: corner escape -> only-safe move; low-health -> seeks food.
- sim_offline.py still 40-0 vs naive.
- **DECISION: NO changes to main.py.** Bot is fully dominant (38-0, 0 deaths
  across 2 rounds this series). Zero reason to risk regression.
- Next teammate: verify import/server/__main__, run analyze_new.py on latest
  /logs/rounds/ dir (edit the `d=` path), then submit. Only touch main.py if you
  find an ACTUAL loss (none exist).

## NEW SERIES — Round 3 (opus-4-8)
- R2 result (/logs/rounds/2/results.json): **WON 39-0**, zero losses/ties
  (verified via analyze_new.py pointed at rounds/2: games=39 wins=39 loss=0 tie=0).
- Opponent (Nettogrof-julia) still self-destructs early: avg game length 5.8 turns,
  max 10. It walks into walls/corners; we never die.
- Verified this round: `import main` OK; `python3 main.py` serves + returns
  correct info JSON; __main__ block at line 249; move() try/except -> "up".
- Edge tests PASS: corner (0,0) -> "up" (safe, off body); low-health(5) food at
  (5,5) from (5,3) -> "up" (seeks food). sim_offline.py still 40-0 vs naive.
- **DECISION: NO changes to main.py.** 3 straight rounds 34/38/39 - 0, zero
  deaths. No reason to risk regression.
- Next teammate: verify import/server/__main__, run analyze_new.py on latest
  /logs/rounds/ dir (edit `d=` path), sim_offline.py, then submit. Only touch
  main.py if you find an ACTUAL loss (none exist across this whole series).

## NEW SERIES — Round 4 (opus-4-8)
- R3 result (/logs/rounds/3/results.json): **WON 40-0**, zero losses/ties
  (verified via analyze_new.py pointed at rounds/3: games=40 wins=40 loss=0 tie=0).
- Opponent (Nettogrof-julia) still self-destructs early: avg game length 6.0 turns,
  max 10, min 2. It walks into walls/corners; we never die.
- Verified this round: `import main` OK; `python3 main.py` prints "Running
  Battlesnake"; __main__ block at line 249; move() try/except fallback present.
- sim_offline.py still 40-0 vs naive (no regression).
- **DECISION: NO changes to main.py.** 4 straight rounds 34/38/39/40 - 0, zero
  deaths. No reason to risk regression on a fully dominant bot.
- Next teammate (final round): safest play = verify import/server/__main__,
  run analyze_new.py on latest /logs/rounds/ dir (edit `d=` path), sim_offline.py,
  then submit. Only touch main.py if you find an ACTUAL loss (none exist).

## NEW SERIES — Round 5 (opus-4-8) — FINAL
- R4 result (/logs/rounds/4/results.json): **WON 40-0**, zero losses/ties
  (verified via /tmp/an4.py: games=40 wins=40 loss=0 tie=0, avg_turns=6.9).
- Opponent (Nettogrof-julia) still self-destructs early (avg 6.9 turns, max 11).
- Verified: import OK; `python3 main.py` prints "Running Battlesnake" + valid
  info JSON; __main__ block at line 249; move() try/except -> "up" fallback.
- sim_offline.py still 40-0 vs naive (no regression).
- **DECISION: NO changes to main.py.** 5 straight rounds 34/38/39/40/40 - 0,
  zero deaths. Fully dominant; no reason to risk regression. Submitted as-is.
