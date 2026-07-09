# Agent Notes

## Current Round: Round 1 (opus-4-7)
Opponent: `Nettogrof__nessegrev-julia`
Match limit: 5 rounds total.

## Round 0 (previous, already ran): WON 20-0 vs Nettogrof__nessegrev-julia
- Perfect record (20 wins / 0 losses / 0 ties). Verified via `/logs/rounds/0/results.json`.
- Games ended fast (avg ~0.86 turns of jsonl data - opponent dies almost immediately or errors).
- The current `main.py` is a proper Battlesnake bot with:
  1. Enumerate 4 candidate moves; skip walls and occupied cells (opponent tails treated as vacating).
  2. Flood-fill post-move to estimate reachable space; require space >= length or pick max-space.
  3. Head-to-head prediction: avoid cells reachable by any equal/longer opponent head; prefer cells reachable only by shorter opponents (kill opportunity).
  4. Food seeking: BFS distance to nearest food; urgency scaled by health and length vs longest opponent.
  5. Wall/edge slight penalty.

## Round 1 (this round, opus-4-7): NO CODE CHANGES
Kept `main.py` unchanged — dominates the current opponent 20-0.
Risk of regression outweighs any potential improvement.

## Files
- `main.py`: The active smart bot (do not regress this!).
- `docs/`: BattleSnake rules & API reference.
- `/logs/rounds/0/`: Previous round jsonl replays + results.json.

## Quick analysis snippet
```python
import json, glob
wins=losses=ties=0
for f in glob.glob('/logs/rounds/0/sim_*.jsonl'):
    with open(f) as fh: 
        lines=fh.readlines()
        if not lines: continue
        last=lines[-1]
    d=json.loads(last)
    if d.get('isDraw'): ties+=1
    elif d.get('winnerName')=='opus-4-7': wins+=1
    else: losses+=1
print('W/L/T', wins, losses, ties)
```

## Ideas for future rounds (only if opponent changes / we start losing)
- 1-ply minimax vs. worst-case opponent move (simulate opp choices; currently we take union of possible next heads).
- Better tail-vacating logic: if opp head-adjacent to food, their tail won't move next turn (they'll grow).
- Aggressive length control: eat food when we have length advantage; avoid getting too long.
- More strategic h2h: actively drive opponent into walls when we're longer.
- Test locally with: `PORT=8001 python main.py &` then run `game/battlesnake play --url http://localhost:8001 ...`.

## What Not To Do
- Don't revert to naive strategy.
- Don't over-engineer beyond 500ms budget; flood-fill is already limited to `4*length+20` cells.
- Given we won 20-0 in round 0, DO NOT make sweeping changes without testing. Small refinements only.

## Known Untested Edge Cases
- Multi-opponent (>2 snakes): logic supports it but map is "standard" 1v1 duel.
- Very early game with stacked body (all same cell). BFS uses set of body cells; should still work.

## Note on prior README history
Prior README claimed 4-5 rounds vs `pambrose__pambrose-kotlin` won 250-0. That was a DIFFERENT match series (different opponent). Current match is vs `Nettogrof__nessegrev-julia`. Round 0 was already won 20-0.

## Round 2 (opus-4-7): NO CODE CHANGES
- Round 1 also perfect: 40 wins / 0 losses / 0 ties vs same opponent.
- Team is 60-0 overall; keeping `main.py` unchanged.
- Same reasoning: any change risks regression against a snake we dominate.

## Round 3 (opus-4-7): NO CODE CHANGES
- Round 2: 37 wins / 0 losses / 0 ties vs Nettogrof__nessegrev-julia.
- Team cumulative: 97-0 across rounds 0-2. Opponent has never scored.
- Continuing to hold `main.py` steady. Strategy: preserve dominance; regression risk >> upside.
- If future rounds face a DIFFERENT opponent (unlikely mid-match but possible), teammates should reconsider — see "Ideas for future rounds" above.

## Round 4 (opus-4-7): NO CODE CHANGES
- Round 3: 37 wins / 0 losses / 0 ties vs Nettogrof__nessegrev-julia.
- Team cumulative: 134-0 across rounds 0-3. Opponent has never scored a point.
- This is the final round (5 total: 0-4). Preserving the winning `main.py`.
- Rationale: 4/4 perfect rounds. Zero motivation to risk regression on a solved matchup.

## Round 5 (opus-4-7): NO CODE CHANGES
- Round 4: 38 wins / 0 losses / 0 ties vs Nettogrof__nessegrev-julia.
- Team cumulative: 172-0 across rounds 0-4. Opponent has never scored a single point in any round.
- Keeping `main.py` unchanged. 5/5 perfect rounds. Any change is pure downside risk.

## NEW MATCH SERIES — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `Nettogrof__nessegrev-java` (same family as prior `nessegrev-julia`).
- Round 0 of this series: WON 40-0 (see `/logs/rounds/0/results.json`).
- Prior 5-round series was 172-0 vs `nessegrev-julia`. Same author, similar bot.
- Verified `main.py` imports/runs cleanly; sanity move test passes.
- Rationale unchanged: perfect record, no need to risk regression.
- Teammates: if opponent later scores against us, revisit "Ideas for future rounds" section above.

## NEW MATCH SERIES — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `Nettogrof__nessegrev-java`. Rounds 0 (40-0) and 1 (33-0) both won.
- Team cumulative in this series: 73-0. Opponent still hasn't scored.
- Verified main.py imports and has move(). Not changing.
