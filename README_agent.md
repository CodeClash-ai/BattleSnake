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
