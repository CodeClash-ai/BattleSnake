# Agent Notes (CodeClash Battlesnake)

## Current status (after round 2 edits by opus-4-8)
The opponent is **pambrose SimpleSnake** (naive Kotlin port): NO collision
avoidance, walks straight toward the FARTHEST food. It self-eliminates in a
handful of turns very often.

### Round 1 result: **WON 250-0** (perfect record, 250/250 games).
Opponent dies avg ~6.7 turns in. We just need reliable survival.

## Bot architecture (main.py)
Survival-first, space-aware, greedy bot (1-ply heuristic):
  - Never moves into walls / bodies (treats vacating tails as passable;
    accounts for snakes that just ate = duplicated tail).
  - Flood-fill space evaluation per candidate move (weight * 10).
  - **Trap penalty**: extra big penalty if reachable space <= our length
    (avoids boxing ourselves in). [added r2]
  - Head-to-head: -1000 for tie/loss cells; +60 for kill opportunities.
  - **Food logic tuned** [r2]: urgent-eat when health<30; grow when we're not
    longer than rival or health<55; only mild pull when long+healthy (avoids
    over-eating and self-trapping).
  - **Aggression** [r2]: when we have ample space, pull toward shorter
    opponents' heads to set up cut-offs / H2H kills.

## Round 2 changes (this round)
Added trap penalty, tuned food weights, added aggression. Validated:
  - vs naive opponent: 80/80 wins.
  - vs round-1 bot (self-play): **49-0-1** — clear improvement.
  - move time 0.006 ms (zero timeout risk). Edge cases (corner, trapped,
    single-cell, longer opponent adjacent) all handled without crash.

## Backups
- `main_r1_backup.py`  — round 1 version (before r2 tuning).
- `main_v0_backup.py`  — original naive bot.

## Testing tools (in /workspace)
- `naive_opponent.py`  — the pambrose SimpleSnake, runnable server for tests.
- `run_matches.sh N`   — main.py vs naive_opponent.py via bundled
  `game/battlesnake` CLI, prints W/L/T. Usage: `./run_matches.sh 60`.
- Self-play test: start two servers on diff ports (PORT=8003 python3 main.py &
  PORT=8004 python3 main_rX_backup.py &) then loop `game/battlesnake play`.

## Ideas for future rounds (if opponent gets smarter)
- Minimax / 2-ply opponent move prediction (currently 1-ply heuristic).
- Longest-path / tail-chasing when space is tight.
- More aggressive flood-fill cut-off of opponent when we're clearly longer.
- Consider hazard map handling (ruleset has hazardDamagePerTurn=14) — not
  currently modeled; standard maps rarely have hazards but watch for it.
