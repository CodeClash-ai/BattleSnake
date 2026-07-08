# Agent Notes (round 1 by opus-4-8)

## Situation
- Opponent is `pambrose-kotlin` == the original SimpleSnake (farthest-food, NO
  collision avoidance). It self-destructs (wall/self) within ~4 turns.
- Our old bot (`main_backup_v0.py`) was an identical SimpleSnake port -> 50/50
  coin-flip matches. Round 0 result was 91-83 (barely won).

## What I did
Rewrote `main.py` into a proper survival bot:
- Avoids walls, own body, other snake bodies (tail handling included).
- Flood-fill space check per candidate move (avoid self-trapping).
- Tail-reachability bonus (can chase own tail = rarely trapped).
- Head-to-head awareness: avoid losing H2H, seek winning H2H (we're longer).
- Food urgency scales with health (eat harder when starving).

## Results (local, `./run_match.sh`)
- vs old SimpleSnake: **80-0** (crushes it). This is the real opponent's strategy.

## Tools for teammates
- `./run_match.sh <botA.py> <botB.py> <N>` : runs N games, prints win counts.
  Uses the compiled CLI at `/workspace/battlesnake_cli`.
- Build CLI: `cd game && go build -o /workspace/battlesnake_cli ./cli/battlesnake`
- Solo survival test: `battlesnake_cli play -W 11 -H 11 -n A -u http://localhost:8001 -g solo -r <seed>`
- `main_backup_v0.py` = original SimpleSnake (baseline / stand-in for opponent).

## Known weakness / TODO for next teammate
- Solo survival caps at ~103 turns: bot starves in a corner loop at low health
  because tail-following bonus and space heuristic fight food-seeking. This does
  NOT matter vs the current passive opponent (it dies first), but if a future
  opponent survives long, IMPROVE food-commit logic:
  - Consider A* pathfinding to nearest SAFE food and commit to the path.
  - Reduce/disable tail-following bonus when health < ~30 so we break the loop.
  - Make sure flood-fill uses tail-move simulation for the *path* not just 1 step.
