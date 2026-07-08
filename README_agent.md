# Agent Notes (read me first)

## Current status
- Bot (`main.py`) rewritten from the naive pambrose "SimpleSnake" port into a
  proper survival bot. Result vs the round-0 opponent (same naive SimpleSnake):
  **~40-0 / 30-0** in local sims. Solo survival: 88 -> 174 turns after tuning.

## Match setup
- Game: BattleSnake standard, 11x11, 2 snakes, y-up coords (up = y+1).
- Opponent in logs = `pambrose__pambrose-kotlin` = naive SimpleSnake:
  NO collision avoidance, targets the FARTHEST food -> suicides in ~3-5 turns.
- My bot in logs = `opus-4-8`.

## What main.py does now
1. Collision avoidance: walls, self, all snake bodies.
2. Tail handling: a tail square is passable next turn unless the snake just ate
   (detected via duplicated last two body segments).
3. Flood-fill space eval after each candidate move; heavily penalizes moves that
   leave less space than my length (trap avoidance). This is the key survival win.
4. Head-to-head: avoid squares an equal/longer enemy head could reach
   (-1000); seek squares where a SHORTER enemy could be (+500) to eat them.
5. Food: hunger-weighted. Weak pull when healthy (0.4) to stay short/nimble,
   strong when hungry (<50 ->5, <25 ->12). Staying short avoids self-traps.

## How to test (rebuild not needed; binary at /tmp/battlesnake)
```
cd /workspace/game && go build -o /tmp/battlesnake ./cli/battlesnake   # if missing
# start my bot:
cd /workspace && PORT=8000 python3 main.py &
# start opponent (naive backup saved as main_simplesnake_backup.py):
cp main_simplesnake_backup.py /tmp/opp_main.py && cp server.py /tmp/server.py
cd /tmp && PORT=8001 python3 opp_main.py &
# run a match:
/tmp/battlesnake play -W 11 -H 11 --name mybot --url http://localhost:8000 \
    --name opp --url http://localhost:8001 -g standard
# solo survival:
/tmp/battlesnake play -W 11 -H 11 --name mybot --url http://localhost:8000 -g solo
```
- Winner printed on last line: "<name> was the winner." (or draw/no winner).

## Files
- `main.py`               : current smart bot.
- `main_simplesnake_backup.py` : original naive port (kept as sparring opponent).

## Ideas for future rounds (if opponent gets smarter)
- Add 1-2 ply minimax / lookahead for head-to-head duels.
- Prefer moves that reduce opponent's flood-fill space (area control / trapping).
- Cut off opponent access to food when we're longer.
- Corner/edge avoidance heuristic to keep escape routes open.
