# Agent Notes (opus-4-8 BattleSnake)

## Current status: DOMINANT vs opponent
Round 0 baseline: both bots were the naive `SimpleSnake` port -> ~even (81/77/92 tie).
The opponent (`pambrose__pambrose-kotlin`) is the naive SimpleSnake: chases the
FARTHEST food, x-dominates-y priority, and has **NO collision avoidance**. It
walks into walls/itself/us and dies fast.

## What I did (round 1)
Rewrote `main.py` into a survival-first bot:
- Full collision avoidance: walls, all snake bodies, self.
- Tail handling: tails are treated as free next turn unless the snake just ate
  (health==100).
- Head-to-head avoidance: avoid cells an enemy head could also enter unless we
  are strictly longer (heavy -1000 penalty for losing/tying h2h; +30 bonus when
  we'd win a h2h).
- Flood-fill space evaluation: pick moves that keep the most reachable open
  space; penalize moves that leave less space than our body length (trap
  avoidance).
- Food logic: chase nearest food when hungry (health<60) or when not clearly
  longer than opponents; otherwise favor open space + center for safety.
- Wrapped in try/except returning "up" as a legal fallback.

## Results (local sims vs the naive opponent)
`bash test/match.sh 40` => **me=40 opp=0 tie=0**. Multiple runs 70-0 total.
Our bot wins essentially 100% because the opponent self-destructs.

## Test harness (test/)
- `test/opponent.py` = copy of the original naive bot (the opponent's strategy).
- `test/match.sh N` = runs N local games (our main.py on :8000 vs opponent on
  :8001) using `./game/battlesnake play`. Prints "RESULTS: me=X opp=Y tie=Z".
- `main_original_backup.py` = original naive main.py (pre-rewrite).

### Gotcha: running the flask server
`python main.py` mysteriously exits immediately in this env. Start servers via
`python -c "from server import run_server; import main; run_server({...})"`
instead (see test/match.sh). Winner string in game output is
"NAME was the winner." (not "is the winner").

## Ideas for future teammates
- Opponent is static/naive, so current bot is more than enough. Low risk.
- Could add lookahead/minimax vs stronger opponents, but unnecessary here.
- If opponent changes, re-copy their strategy into test/opponent.py and re-tune.
