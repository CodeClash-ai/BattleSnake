# Agent Notes

## Round 1 (opus-4-7) — Changes
The initial `main.py` was a *faithful port* of pambrose's naive Kotlin bot — no collision avoidance, aimed at the *farthest* food, priority x-over-y. Round 0 lost 75-98 (77 ties) against essentially the same bot (pambrose).

I replaced `main.py` with a proper Battlesnake bot:
- Enumerate 4 candidate moves; skip walls and occupied cells (opponent tails treated as vacating).
- Flood-fill post-move to estimate reachable space; require space >= length or pick max-space.
- Head-to-head prediction: avoid cells reachable by any equal/longer opponent head; prefer cells reachable only by *shorter* opponents (kill opportunity).
- Food seeking: BFS distance to nearest food, urgency scaled by health, length vs longest opponent.
- Wall/edge slight penalty.

## Files
- `main.py`: The active smart bot.
- `docs/`: BattleSnake rules & API reference.
- `/logs/rounds/0/`: previous round jsonl replays + results.json.

## Ideas for teammates
- Add a 1-ply minimax vs. worst-case opponent move (simulate opp choices; currently we just take union of possible next heads).
- Better tail-vacating logic: if opp head-adjacent to food, their tail won't move next turn (they'll grow) — right now we ignore that.
- Cache: not needed — game timeout is 500ms, we're fast.
- The opponent in Round 0 (pambrose__pambrose-kotlin) uses the same *farthest-food, no avoidance* logic (both bots are identical ports). Any collision-aware bot should crush it.
- Test locally with: `PORT=8001 python main.py &` then run `game/battlesnake play --url http://localhost:8001 ...`.

## Known Untested Edge Cases
- Multi-opponent (>2 snakes): logic supports it but map is "standard" 1v1 duel per round 0 logs.
- Very early game with stacked body (all same cell). BFS uses set of body cells; should still work since duplicates collapse.

## What Not To Do
- Don't revert to naive strategy. Even a moderately safe bot beats one that walks into walls.
- Don't over-engineer beyond 500ms budget; flood-fill is already limited to `4*length+20` cells.
