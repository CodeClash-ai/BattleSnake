# Agent Notes (CodeClash BattleSnake)

## Current status
- Opponent: `pambrose__pambrose-kotlin` = a NAIVE SimpleSnake (targets the
  FARTHEST food, NO collision/wall/self avoidance). Original code preserved in
  `main_original_backup.py`.
- Round 0 result (before my changes): Tie-heavy (we won 84, opp 74, 92 ties)
  because the OLD main.py was also the naive SimpleSnake.

## What I did (round 1)
Rewrote `main.py` into a proper survival bot:
  - Enumerates 4 moves, applies HARD constraints: no walls, no self/body,
    tail treated as free unless snake likely grew.
  - Head-to-head logic: huge penalty if opp head could reach the cell and is
    >= our length; bonus if we'd win the H2H.
  - Flood-fill space estimation (avoid trapping ourselves) — dominant term.
  - Food seeking scaled by hunger (aggressive when health<40, mild otherwise),
    targets NEAREST food.
  - Mild center preference for mobility.
  - Safe fallback if no good move.

## Test results
- `python3 sim.py 100`  -> new bot 100, original 0 (local approximate simulator)
- `./run_real.sh 30`    -> REAL CLI games: new=30 old=0 draw=0
- Mirror matches (bot vs itself) run to ~125 turns fine, no crashes/errors.

## Tools
- `sim.py N`      : fast approximate simulator; new main vs main_original_backup.
- `run_real.sh N` : REAL engine games using ./game/battlesnake binary. Serves
                    new bot on :8000 and original on :8001 via Flask, runs N
                    games, prints win tally. (Uses /tmp/opp for opponent copy.)
- `main_original_backup.py` : the opponent/original naive snake.

## Ideas for future rounds (if opponent gets smarter)
- Deeper lookahead / minimax (2-3 ply) for H2H and space.
- Better tail-chasing endgame; cut off opponent's space.
- Voronoi/territory control scoring instead of pure flood-fill.
- Tune food weights; currently very survival-focused.
