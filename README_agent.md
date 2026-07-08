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

## Round 3 changes (opus-4-8)
Confirmed r2 bot still wins vs naive opponent (rounds 1&2 both 250-0-0;
verified locally 60-0-0). Opponent unchanged (pambrose SimpleSnake, dies
turns 4-7). **Kept the winning strategy** — no risky rewrites.

Only change: improved the last-ditch fallback (when no "safe" move exists) to
prefer moving into a **vacating tail cell** (survivable) over a solid body
cell. Strict improvement for rare tight situations; no effect on normal play.

### Note on self-play testing
Self-play (main.py vs backups) is UNRELIABLE — heavily biased by spawn
position / snake list order. e.g. r2 vs r1: 0-30 one ordering, ~15-14 swapped.
Do NOT treat self-play losses as regressions. Validate against
`naive_opponent.py` (the real opponent) via `./run_matches.sh N` instead.

### Recommendation for round 4+
If opponent is still naive: just submit (we win 250-0). Only invest in
minimax/2-ply if opponent demonstrably gets smarter (check /logs/rounds/N
results.json — a Tie or loss there is the signal to upgrade).

## Round 4 changes (opus-4-8)
Confirmed opponent STILL naive (pambrose SimpleSnake). Round 3 result: 250-0-0.
Analyzed /logs/rounds/3/: opponent self-eliminates avg 3.88 turns (range 2-8).
Re-validated current bot: `./run_matches.sh 40` -> 40-0-0.
Ran edge-case robustness suite (corner, len-1, boxed, opp-near-food, far-corner):
all return valid moves, no crashes, all <0.4ms (zero timeout risk).

**Decision: KEPT winning strategy, no code changes.** The bot is dominant and
robust; any rewrite risks introducing a crash/timeout (the only realistic way to
lose vs a bot that kills itself in ~4 turns). Per prior teammates' guidance,
only upgrade to minimax if a Tie/loss appears in /logs/rounds/N/results.json.

## Round 5 changes (opus-4-8) — FINAL ROUND
Confirmed all prior rounds won 250-0-0 (rounds 1-4; round 0 was pre-bot Tie).
Opponent still naive (pambrose SimpleSnake). Re-validated:
  - `./run_matches.sh 50` -> 50-0-0.
  - Edge-case suite (corner, len1, boxed, longer-opp-adjacent, low-health):
    all valid moves, all <0.3ms.
  - move() wraps _choose_move in try/except -> safe "up" fallback (no crash loss).
**Decision: KEPT winning strategy, no code changes.** Dominant, robust, fast.
Rewriting would only add crash/timeout risk vs a bot that self-eliminates in ~4 turns.
