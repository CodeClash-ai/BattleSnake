# Notes for teammate agents

## Round 1 (this round) — done by opus-4-7

### Situation at start
- Round 0 (previous round): tie between opus-4-7 and pambrose__pambrose-kotlin.
- We had the SimpleSnake reference bot (no collision avoidance!), so did the opponent, so we just tied.
- Average game length was ~4.5 turns because both snakes suicide constantly.

### Change I made
- Replaced `main.py` with a safety-first heuristic snake:
    - Enumerates 4 candidate moves, filters out illegal (walls, snake bodies).
    - Considers other snakes' tails movable (they'll vacate next turn) UNLESS they just ate (body[-1] == body[-2]).
    - Avoids head-to-head losses vs equal/longer opponents; prefers head-to-head kills vs shorter opponents.
    - Uses flood-fill from each candidate cell (excluding new head) to make sure we don't trap ourselves. Prefers space >= our length.
    - Scores remaining candidates by: reachable space (weight 2×), distance to nearest food via BFS (weighted higher when health low or when we're shorter), head-to-head kill bonus, mild center-tropism, wall/edge penalty.
- No pathfinding search deeper than 1 ply, but flood-fill gives good coarse trapping avoidance.

### Testing
Ran 50 local games against SimpleSnake baseline (in `/tmp/opp/`) with the local `game/battlesnake` CLI: **50W/0L/0D**. Solo game survives >80 turns.

### Files
- `main.py` — the bot (heuristic-based, no external deps beyond flask which is only used by `server.py`).
- `server.py` — Flask HTTP server (unchanged).

### How to test locally
```bash
# Start our bot
cd /workspace && PORT=8001 python3 main.py &
# Start baseline opponent
cp -r /workspace /tmp/opp   # then replace main.py with SimpleSnake
cd /tmp/opp && PORT=8002 python3 main.py &
# Play
/workspace/game/battlesnake play -W 11 -H 11 \
    --name me  --url http://localhost:8001 \
    --name opp --url http://localhost:8002 \
    -g standard
```

## Ideas for future rounds

1. **2-ply / minimax search**: currently we only look 1 move ahead. A shallow minimax over both snakes' next moves (16 leaves per ply) with a tight time budget would help against smarter opponents.
2. **Better trap detection**: flood-fill currently ignores dynamic tail motion during the fill. Doing a BFS that "advances" over turns and knows tails will vacate would give more accurate escape estimates. Look at "voronoi/territory" style scoring: split reachable squares by who reaches them first.
3. **Aggressive shortcutting**: when we're clearly longer than the opponent, drive toward their head to force head-to-head kills.
4. **Food timing**: right now food weight scales with health only; better to compute "can I reach food in health/2 turns and still have escape space".
5. **Opponent modeling**: if the opponent is still SimpleSnake, we can predict their move exactly (`_move_to` toward farthest food), and set traps.

## Analysis scripts (not written yet, feel free to add)

- Suggested: parse `/logs/rounds/*/sim_*.jsonl` and gather win/loss stats vs opponent per turn count, food events, etc. See snippet at top of round 1 shell history:
```python
import json, glob
for f in glob.glob('/logs/rounds/0/sim_*.jsonl'):
    lines = open(f).read().splitlines()
    last = json.loads(lines[-1])
    # 'winnerName', 'isDraw' fields available.
```

## Round 2 (this round) — done by opus-4-7

### Situation at start
- Round 1 was a PERFECT SWEEP: 250 wins, 0 losses, 0 draws vs pambrose__pambrose-kotlin.
- Average game length only ~7 turns (max 13). The opponent bot self-destructs very quickly.
- Verified: same opponent name in both round 0 and round 1.
- Longest game: sim_163.jsonl, 11 turns; opponent wandered aimlessly, never ate, then died.

### Analysis
- Ran `python3 -c "import json,glob; ..."` over `/logs/rounds/1/sim_*.jsonl`: 250W/0L/0D.
- The opponent (pambrose_kotlin) does not eat food, does not avoid walls well.
- Our safety-first heuristic bot easily outlives it (we eat food, avoid traps, avoid h2h losses).

### Change I made
- **NO CODE CHANGES to `main.py` this round.** Zero regressions is more valuable than marginal gains against a bot that dies in 7 turns.
- Added this note.

### Recommendation for future teammates
- If opponent stays the same (pambrose_kotlin): **do not touch main.py**. We already sweep 250/250.
- If opponent name in `/logs/rounds/{N-1}/sim_0.jsonl` is DIFFERENT: reconsider strategy.
  Look at avg game length and win% — if we're losing or tying, upgrade to 2-ply search / better voronoi flood fill (see ideas below).

### Quick diagnostic snippet (paste in bash)
```bash
python3 -c "
import json,glob
last_round = max(int(x) for x in __import__('os').listdir('/logs/rounds'))
wins=losses=draws=0; turns=[]
for f in glob.glob(f'/logs/rounds/{last_round}/sim_*.jsonl'):
    lines = open(f).read().splitlines()
    if not lines: continue
    last = json.loads(lines[-1])
    turns.append(len(lines))
    winner=last.get('winnerName','')
    if last.get('isDraw'): draws+=1
    elif winner=='opus-4-7': wins+=1
    else: losses+=1
print(f'round {last_round}: W={wins} L={losses} D={draws} avg_turns={sum(turns)/max(1,len(turns)):.1f}')
"
```

## Round (this one) — done by opus-4-7

### Situation at start
- Prior match was against **Nettogrof__nessegrev-julia** (NOT pambrose_kotlin from earlier README notes).
- Results in `/logs/rounds/0/`: 20 recorded games, **20W/0L/0D**. Only 20 of 250 sim slots have data (rest are empty files).
- Avg game length: 6.6 turns, max 11. Opponent dies quickly.
- Longest recorded game: sim_1.jsonl (10 turns, we won with length 5, full health, opponent gone).

### Change I made
- **NO CODE CHANGES to `main.py`.** Bot is winning 100% of recorded games. Prior teammate's safety-first heuristic (flood-fill + BFS food + h2h logic) is holding up.
- Verified bot starts, responds, and wins a local match against a trivial "always up" opponent.

### Note on prior README claims
- Earlier README notes mention rounds 0/1/2 with 250 wins vs pambrose_kotlin — those were from a *previous match* (not visible in current /logs).
- Current `/logs/rounds/0/` = the previous round of THIS match series. Different opponent name.
- Next teammate: check the snake name in `/logs/rounds/N/sim_*.jsonl` (any non-empty file) to confirm opponent identity!

### Recommendation
- If opponent stays Nettogrof__nessegrev-julia and results stay perfect: **don't touch main.py**.
- If a stronger opponent appears: implement 2-ply minimax (see prior "Ideas for future rounds" section).
