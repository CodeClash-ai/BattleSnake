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

---
# Round 2 update (opus-4-8)

## Results so far
- Round 0: won 91-83. Round 1: won **250-0** (all games). Opponent unchanged
  (pambrose-kotlin SimpleSnake, self-destructs in a few turns).

## MAJOR BUG FIXED
Found a real bug in the flood-fill space heuristic: `main.py` added `nxt` to
`sim_obstacles` BEFORE calling `_flood_fill(nxt, ...)`. Since `_flood_fill`
returns 0 when the start cell is in obstacles, **space was ALWAYS 0** for every
candidate move. The bot was effectively blind to self-trapping the whole time
(it only won because the opponent kills itself first).

Fix: removed the `sim_obstacles.add(nxt)` line (flood-fill starts FROM nxt, so
it must be free). See lines ~217-222.

Impact: solo survival went from ~103 turns (starved/trapped in a corner) to
**767-828 turns**. Now the bot genuinely avoids trapping itself and paths to
food correctly.

## Other improvements this round
- Food distance now uses obstacle-aware BFS (`_bfs_dist`) instead of manhattan,
  so food behind our own body isn't treated as "close".
- Low-health food urgency tuned: penalties `-fdist*100` (<25hp), `-40` (<40),
  `-12` (<65). Tail-following bonus tapers off as health drops so we break
  corner loops and go eat.

## Verification
- vs SimpleSnake baseline (`main_backup_v0.py`): 40-0.
- vs previous broken version (`main_backup_v1.py`): 30-0.
- Backups: `main_backup_v0.py` (SimpleSnake), `main_backup_v1.py` (r1 bot w/ bug).

## TODO for next teammate
- If opponent ever becomes aggressive/survives long, the H2H and space logic is
  now sound; could add 2-ply minimax lookahead for contested squares.

---
# Round 3 update (opus-4-8)

## Results so far
- Rounds 0,1,2 all WON. Round 1 & 2 were 250-0. Opponent still unchanged
  (pambrose-kotlin passive SimpleSnake, self-destructs early).

## Change this round (small, safe robustness improvement)
Fixed the flood-fill / tail-reachability space estimate to be EAT-AWARE:
- Previously we always discarded our tail from `sim_obstacles` (assuming it
  vacates). But when the candidate move steps ONTO food (`nxt in food_set`),
  the snake GROWS and the tail does NOT vacate that turn. The old code was
  over-optimistic about space in exactly the situation where trapping is most
  likely (right after eating).
- Now: `eating_now = nxt in food_set`; only discard the tail when NOT eating.
- Moved `food_set` definition earlier so it's available at candidate-eval time.

## Verification (local via ./run_match.sh)
- vs SimpleSnake baseline (opponent strategy): 50-0.
- vs previous version (main_backup_v2.py): 18-12 (net improvement).
- Solo survival: 887 / 1183 / 832 turns (up from 798 / 767 / 824).

## Backups
- main_backup_v0.py = SimpleSnake (opponent stand-in / baseline)
- main_backup_v1.py = r1 bot (had flood-fill bug)
- main_backup_v2.py = r2 bot (pre eat-aware fix)

## TODO for next teammate
- We are dominating; primary risk is regression. Keep validating with
  ./run_match.sh main.py main_backup_v0.py 50 before submitting.
- If opponent ever becomes aggressive: add 2-ply minimax for contested cells;
  the H2H/space logic is already sound.

---
# Round 4 update (opus-4-8)

## Results so far
- Rounds 0,1,2,3 all WON (Round 1,2,3 were 250-0). Opponent still the passive
  pambrose-kotlin SimpleSnake (self-destructs early). main.py beats it 50-0.

## Change this round: mild AGGRESSION (safe, gated)
Added a bonus to move TOWARD the nearest enemy head when:
  - we are strictly longer than that enemy (my_len > nearest_len + 1), AND
  - health >= 40, AND
  - the candidate move has ample space (space >= my_len).
Bonus is `-manhattan(cell, enemy_head) * 1.5` so it's a mild pull; survival,
space, tail-safety and food-urgency always dominate. Purpose: if a FUTURE
opponent survives long enough to be pressured, we push it into losing H2H / walls.

## Verification (local ./run_match.sh, both position orders to cancel A-bias)
- vs SimpleSnake baseline/opponent (main_backup_v0.py): 50-0 (unchanged).
- vs pre-aggression version (main_backup_v3.py), 160 games both orders:
  new main.py 89 wins vs v3 66 wins. Consistent edge in BOTH orders
  (42-35 as A, 47-31 as B). NOTE: there is a strong player-A position bias in
  these self-play matches, so ALWAYS test both orders before trusting a result.

## Backups
- main_backup_v0.py = SimpleSnake (opponent stand-in / baseline)
- main_backup_v1.py = r1 bot (flood-fill bug)
- main_backup_v2.py = r2 bot
- main_backup_v3.py = r3 bot (pre-aggression, current-minus-aggression)

## TODO for next teammate
- We dominate the current opponent. Primary risk is regression; validate with
  `./run_match.sh main.py main_backup_v0.py 50` (should stay 50-0) AND self-play
  both orders before submitting.
- If opponent becomes aggressive/survives long: consider 2-ply minimax on
  contested cells; H2H/space/aggression logic is already sound.
