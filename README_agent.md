# Agent Notes

## Round 0 (naive baseline): LOST 75-98 (77 ties)
The initial `main.py` was a *faithful port* of pambrose's naive Kotlin bot — no collision avoidance, aimed at the *farthest* food, priority x-over-y.

## Round 1 (opus-4-7) — WON 250-0 (perfect!)
Round 1 teammate replaced `main.py` with a proper Battlesnake bot:
- Enumerate 4 candidate moves; skip walls and occupied cells (opponent tails treated as vacating).
- Flood-fill post-move to estimate reachable space; require space >= length or pick max-space.
- Head-to-head prediction: avoid cells reachable by any equal/longer opponent head; prefer cells reachable only by *shorter* opponents (kill opportunity).
- Food seeking: BFS distance to nearest food, urgency scaled by health, length vs longest opponent.
- Wall/edge slight penalty.

## Round 2 (opus-4-7) — no code change; kept the winning bot
Verified 250 wins / 0 losses / 0 ties against pambrose__pambrose-kotlin in round 1 (see `/logs/rounds/1/results.json`).
Since the strategy already dominates the opponent, I did NOT modify `main.py` to avoid regressions. The opponent uses a naive farthest-food strategy with no collision avoidance — any collision-safe bot handily beats it.

## Files
- `main.py`: The active smart bot (do not regress this!).
- `docs/`: BattleSnake rules & API reference.
- `/logs/rounds/{0,1}/`: Previous round jsonl replays + results.json.

## Quick analysis snippet
```python
import json, glob
wins=losses=ties=0
for f in glob.glob('/logs/rounds/1/sim_*.jsonl'):
    with open(f) as fh: last=fh.readlines()[-1]
    d=json.loads(last)
    if d.get('isDraw'): ties+=1
    elif d.get('winnerName')=='opus-4-7': wins+=1
    else: losses+=1
print('W/L/T', wins, losses, ties)
```

## Ideas for future rounds (only if opponent changes / we start losing)
- 1-ply minimax vs. worst-case opponent move (simulate opp choices; currently we take union of possible next heads).
- Better tail-vacating logic: if opp head-adjacent to food, their tail won't move next turn (they'll grow) — right now we assume all tails vacate.
- Aggressive length control: eat food when we have length advantage to maintain lead but avoid getting too long (space becomes tight).
- More strategic h2h: actively drive opponent into walls when we're longer.
- Test locally with: `PORT=8001 python main.py &` then run `game/battlesnake play --url http://localhost:8001 ...`.

## What Not To Do
- Don't revert to naive strategy.
- Don't over-engineer beyond 500ms budget; flood-fill is already limited to `4*length+20` cells.
- Given we won 250-0, DO NOT make sweeping changes without testing. Small refinements only.

## Known Untested Edge Cases
- Multi-opponent (>2 snakes): logic supports it but map is "standard" 1v1 duel per round 0/1 logs.
- Very early game with stacked body (all same cell). BFS uses set of body cells; should still work since duplicates collapse.

## Round 3 (opus-4-7) — no code change; kept the winning bot
Verified 250-0 win in round 2 against pambrose__pambrose-kotlin (see `/logs/rounds/2/results.json`).
Two consecutive perfect matches; no need to modify. Same recommendation: only iterate if opponent changes.

## Round 4 (opus-4-7) — no code change; kept the winning bot
Verified 250-0 win in round 3 against pambrose__pambrose-kotlin (see `/logs/rounds/3/results.json`).
Three consecutive perfect matches. Same opponent, same dominance. No modifications.

## Round 5 (opus-4-7) — FINAL ROUND; no code change; kept the winning bot
Verified 250-0 win in round 4 against pambrose__pambrose-kotlin (see `/logs/rounds/4/results.json`).
FOUR consecutive perfect matches (rounds 1-4). Same opponent, same dominance.
Kept `main.py` unchanged to avoid regression risk in the final round.
