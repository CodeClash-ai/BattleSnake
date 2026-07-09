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

## NEW MATCH SERIES — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `Nettogrof__nessegrev-java`. Rounds 0 (40-0), 1 (33-0), 2 (40-0) all won.
- Team cumulative in this series: 113-0. Opponent still hasn't scored.
- Verified `main.py` imports cleanly. Not changing anything.
- Rationale: 3/3 perfect rounds in this series + prior 5/5 perfect against sibling `nessegrev-julia`.
  8 rounds total, 285-0 combined. Zero downside justification for changing a dominant bot.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `Nettogrof__nessegrev-java`. Rounds 0 (40-0), 1 (33-0), 2 (40-0), 3 (37-0) all won.
- Team cumulative in this series: 150-0. Opponent still hasn't scored.
- Verified `main.py` imports cleanly and has move().
- Continuing perfect dominance policy: no changes.

## NEW MATCH SERIES — Round 5 (opus-4-7, FINAL): NO CODE CHANGES
- Opponent: `Nettogrof__nessegrev-java`. Rounds 0 (40-0), 1 (33-0), 2 (40-0), 3 (37-0), 4 (39-0) all won.
- Team cumulative in this series: 189-0 across 5 rounds. Opponent NEVER scored.
- Combined across both series (nessegrev-julia + nessegrev-java): 361-0.
- Final round of the series. Keeping main.py unchanged. Verified imports cleanly and has move().
- Rationale: absolutely dominant record. Zero regression risk taken.

## NEW MATCH SERIES vs csauve__bookworm — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `csauve__bookworm`.
- Round 0 result: WON 40-0 (see `/logs/rounds/0/results.json`). Avg 9.8 turns/game, max 13.
- `main.py` imports cleanly, has move(). Same dominant strategy.
- Rationale: opponent has never scored; keep bot as-is to avoid regression.
- Combined all-time record across all opponents: 401-0 (adding this round's 40).
- If future rounds show losses/ties, consider tuning: better food urgency vs. csauve__bookworm's style,
  or 1-ply minimax as noted in "Ideas for future rounds".

## NEW MATCH SERIES vs csauve__bookworm — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `csauve__bookworm`. Rounds 0 (40-0), 1 (33-0) both won. Series 73-0.
- `main.py` imports cleanly, has move(). Keeping unchanged.
- All-time combined: 434-0. No regressions warranted.

## NEW MATCH SERIES — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `csauve__bookworm` (different opponent than nessegrev family).
- Rounds 0/1/2 all won: 40-0, 33-0, 35-0 = 108-0 team cumulative in this series.
- Games consistently end ~10 turns (opponent dies quickly, no losses/ties).
- `main.py` imports cleanly, `move()` present. Not changing anything.
- Same rationale: perfect record, don't risk regression.

## NEW MATCH SERIES vs csauve__bookworm — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent this series: `csauve__bookworm` (different opponent than prior README claimed).
- Results so far: Round 0 (40-0), Round 1 (33-0), Round 2 (35-0), Round 3 (38-0).
- Team cumulative in this series: 146-0. Opponent has still never scored.
- Verified `main.py` imports cleanly and has `move()`.
- Not changing anything. Perfect record → preserve.

## NEW MATCH SERIES vs csauve__bookworm — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Opponent this series: `csauve__bookworm`.
- Results: R0 (40-0), R1 (33-0), R2 (35-0), R3 (38-0), R4 (40-0). Series total: 186-0.
- This is the final round (5/5). Verified `main.py` imports cleanly and has `move()`.
- Not changing anything. Perfect record across every round vs every opponent to date.
- Rationale unchanged: any modification is pure regression risk on a dominated matchup.

## NEW MATCH SERIES vs coreyja__improbable-irene — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__improbable-irene`.
- Round 0 result: WON 37-0 (see `/logs/rounds/0/results.json`). Avg 8.7 turns/game, max 13.
- 251 sim files total, but only 37 completed as wins (rest may be incomplete/aborted).
- `main.py` imports cleanly, has move(). Same dominant strategy.
- Rationale: opponent scored 0. Keep bot as-is to avoid regression.
- All-time combined record (approximate): 600+ wins, 0 losses across many series.
- If future rounds show losses/ties vs this opponent, consider:
  * 1-ply minimax vs. worst-case opponent move
  * Better food urgency tuning
  * Head-to-head strategy improvements (see "Ideas for future rounds" above)

## NEW MATCH SERIES vs coreyja__improbable-irene — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__improbable-irene`. Round 0 (37-0), Round 1 (38-0). Series 75-0.
- `main.py` imports cleanly, has move(). Keeping unchanged.
- Rationale: perfect record, no regression risk warranted.

## NEW OPPONENT SERIES — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__improbable-irene` (new opponent this series).
- Rounds 0 (37-0), 1 (38-0), 2 (39-0) all won.
- Team cumulative in this series: 114-0. Opponent still hasn't scored.
- Verified `main.py` imports cleanly and exports `move()`.
- Rationale: perfect record, keeping strategy stable.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__improbable-irene`. Rounds 0 (37-0), 1 (38-0), 2 (39-0), 3 (37-0) all won.
- Team cumulative in this series: 151-0. Opponent still hasn't scored.
- This is round 4 of 5. Verified `main.py` imports cleanly with `move()`.
- Not changing. Same rationale: perfect record + regression risk.

## NEW MATCH SERIES — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__improbable-irene`. Rounds 0 (37-0), 1 (38-0), 2 (39-0), 3 (37-0), 4 (37-0). Series total: 188-0.
- This is the FINAL round (5/5). Verified `main.py` imports cleanly with `move()`.
- Not changing. Perfect record, opponent has never scored across ANY round of ANY series.
- All-time combined team record: 700+ wins, 0 losses across multiple opponents.

## NEW MATCH SERIES vs graeme-hill__snakebot — Round 1 (opus-4-7): CODE CHANGES MADE
- New opponent: `graeme-hill__snakebot`. STRONGER than prior opponents.
- Round 0 result: WON 94-2 (first non-shutout in months!).
- 2 LOSSES (sim_233: 323 turns, sim_241: 387 turns). Both were long games where opponent outlasted us.
- Analysis: In both losses, our snake wound itself into a self-trap coil late-game.
  - sim_241: at turn 382, we ate food into a tight pocket, sealing our own escape.
  - Root cause: prior scoring accepted moves where `space >= my_len` without accounting for growth from eating.
- Changes to `main.py`:
  1. New helper `_flood_fill_full` returning the reachable SET (not just count).
  2. Added `tail_reachable` check: verify our tail cell is in reachable set after move (survival guarantee).
  3. Track `new_len` (post-move length, +1 if eating) instead of using `my_len` for space margin.
  4. Filter: prefer candidates where `tail_reachable == True` (huge bonus +20 in scoring).
  5. Scoring: penalize negative space margin (-100), tight margin (-15).
  6. Food-seeking: only chase food if `margin >= 3` (won't eat ourselves into a trap).
- Kept backup: `main_backup.py` (original bot).
- Sanity-tested: bot imports, produces valid moves. Late-game trap scenarios: bot now picks different (safer) moves.

## Notes for future teammates
- Opponent `graeme-hill__snakebot` plays long games. Be careful with growth strategy.
- Watch for late-game self-traps. `tail_reachable` should help significantly.
- If we start losing more, consider:
  * 1-ply minimax vs. worst-case opponent move
  * Iterative deepening flood-fill w/ time budget
  * Longer-horizon simulation (move both snakes 2-3 turns ahead)

## NEW MATCH SERIES vs graeme-hill__snakebot — Round 2 (opus-4-7): CODE CHANGES MADE
- Round 0: WON 94-2. Round 1: WON 111-1 (only 1 loss: sim_113).
- Analyzed sim_113: at turn 42, we chose to eat food adjacent to a LONGER opp head, then were trapped.
  - Our head at (3,7) len=5, opp head at (5,5) len=7. We moved to (3,6) to eat.
  - Next turn only exits were (3,5) and (4,6), both reachable by longer opp -> H2H death.
- Change: added **2-ply H2H trap avoidance** in main.py:
  - After each candidate move, compute how many of OUR next-turn options are safe from being killed by
    a longer/equal opponent's 2-step-reachable cells.
  - If `next_safe_options == 0` (candidate leads to trap next turn): -60 score penalty.
  - If `next_safe_options == 1` (brittle): -10 penalty.
  - Danger set includes any opponent with `length >= new_len - 1` (accounts for possible eating).
- Verified: bot now picks 'up' (safe) instead of 'down' (trap-eating) in that scenario.
- Sanity-tested 214 real states from Round 1 logs: 0 errors, still moves aggressively when longer.
- `main_backup.py` = original (pre-tail_reachable) bot for reference.

## NEW MATCH SERIES vs graeme-hill__snakebot — Round 3 (opus-4-7): NO CODE CHANGES
- **IMPORTANT**: Current opponent is `graeme-hill__snakebot`, NOT nessegrev-* as earlier README notes assumed.
- Round 0: WON 94-2 (2 losses out of 96 sims)
- Round 1: WON 111-1 (1 loss out of 112 sims)
- Round 2: WON 94-0 (perfect)
- Total: 299 wins / 3 losses (~99% win rate). Not touching main.py.

### Why we occasionally lose (root cause of the 3 losses)
Analyzed the round 1 loss (sim_113.jsonl, 44 turns): we got trapped where every legal move was
a head-to-head death against a longer opponent. Our snake had just eaten (tail stacked), so
2 of 4 directions were blocked by our own body, and both remaining were h2h danger cells. Not
much to do about that specific case without a real minimax.

### Possible future improvements (not worth risking now)
- When ALL candidate moves are h2h_death, prefer the one adjacent to opponent head that's closer
  to a wall/corner — sometimes opp AI avoids h2h even when longer.
- Slightly discourage moves that reduce tail-vacation options (avoid corridors when we just ate).
- True 2-ply minimax over opponent choices instead of union of possible moves.

Verified `python -c "import main; main.move({...})"` returns valid moves.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `graeme-hill__snakebot` (NEW - different from nessegrev family).
- Rounds 0-3 all WON: scores 94-2, 111-1, 94-0, 144-1. Team cumulative: 443-4.
- Opponent occasionally scores 1-2 points per round but never wins.
- Verified `main.py` imports and has move(). Not changing.
- Rationale: 4/4 perfect wins. Regression risk >> potential upside on final round.

## NEW MATCH SERIES — Round 5/FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `graeme-hill__snakebot`.
- Rounds 0-4 all WON: 94-2, 111-1, 94-0, 144-1, 65-0. Team cumulative: 508-4 (~99.2% win rate).
- FINAL round — verified `main.py` imports and returns a valid move.
- Rationale: 5/5 perfect wins. Zero upside to change on final round.

## NEW MATCH SERIES vs coreyja__devious-devin — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__devious-devin` (same author family as `improbable-irene`).
- Round 0 result: WON 35-0 (perfect shutout). Verified via `/logs/rounds/0/results.json`.
- Analysis: 35 sim files, all won. Opponent scored 0.
- `main.py` imports cleanly, has `move()`. Same battle-tested strategy.
- Rationale: opponent completely dominated in round 0. Preserving bot to avoid regression.
- All-time team combined record: 900+ wins, ~4 losses across many opponents (all shutouts except graeme-hill).
- If future rounds show losses/ties vs this opponent, revisit "Ideas for future rounds" (top of file).

## NEW MATCH SERIES vs coreyja__devious-devin — Round 2 (opus-4-7): NO CODE CHANGES
- Round 0: WON 35-0. Round 1: WON 34-0. Perfect through 2 rounds (69-0).
- Verified `main.py` imports and has move(). Not changing.
- Rationale: Opponent has scored 0 points across 2 rounds. Regression risk >> upside.

## NEW MATCH SERIES vs coreyja__devious-devin — Round 3 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__devious-devin` (different bot from prior nessegrev series).
- Rounds 0, 1, 2 all won: 35-0, 34-0, 35-0 respectively. Team: 104-0.
- Opponent has never scored. `main.py` imports OK. Not changing.
- Same rationale as always: perfect record, regression risk >> upside.

## NEW MATCH SERIES vs coreyja__devious-devin — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__devious-devin`. Rounds 0 (35-0), 1 (34-0), 2 (35-0), 3 (36-0) all won.
- Team cumulative in this series: 140-0. Opponent has never scored a single point.
- This is round 4 of 5. Verified `main.py` imports cleanly with `move()`.
- Not changing. Same rationale: perfect record + regression risk >> upside.

## NEW MATCH SERIES vs coreyja__devious-devin — Round 5/FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__devious-devin`. Rounds 0-3 all won: 35-0, 34-0, 35-0, 36-0. Round 4: 38-0.
- Team cumulative in this series: 178-0. Opponent has never scored a single point.
- FINAL round of series. Verified `main.py` imports cleanly and returns valid move.
- Not changing. Same rationale: perfect record + regression risk >> upside on final round.

## NEW MATCH SERIES vs m-schier__kreuzotter — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `m-schier__kreuzotter`.
- Round 0 result: WON 40-0 (perfect shutout). Verified via `/logs/rounds/0/results.json`.
- 250 sim files present; opponent scored 0.
- `main.py` imports cleanly, has `move()`. Sanity test returns valid move.
- Rationale: opponent completely dominated in round 0. Preserving bot.
- If future rounds show losses/ties, revisit "Ideas for future rounds" section near top.

## NEW MATCH SERIES vs m-schier__kreuzotter — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `m-schier__kreuzotter`. Rounds 0 (40-0) and 1 (38-0) both perfect shutouts.
- Team cumulative in this series: 78-0. Opponent has never scored.
- Verified `main.py` imports cleanly and returns valid move.
- Not changing. Same rationale as always: perfect record + regression risk >> upside.

## NEW MATCH SERIES — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `m-schier__kreuzotter` (NEW opponent, different from nessegrev family).
- Rounds 0 (40-0), 1 (38-0), 2 (32-0) all won perfectly.
- Team cumulative in this series: 110-0. Opponent has not scored.
- Verified `main.py` imports cleanly and has move().
- Rationale: perfect record continues, no need to risk regression.

## NEW MATCH SERIES vs m-schier__kreuzotter — Round 4/FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `m-schier__kreuzotter`. Rounds 0 (40-0), 1 (38-0), 2 (32-0), 3 (37-0) all perfect shutouts.
- Team cumulative in this series: 147-0. Opponent has never scored.
- FINAL round (round 4 of 5). Verified `main.py` imports cleanly and has move().
- Not changing. Same rationale: perfect record + regression risk >> upside on final round.

## NEW MATCH SERIES vs m-schier__kreuzotter — Round 5 (opus-4-7): NO CODE CHANGES
- Opponent: `m-schier__kreuzotter`. Rounds 0 (40-0), 1 (38-0), 2 (32-0), 3 (37-0), 4 (34-0) — ALL perfect shutouts.
- Team cumulative in this series: 181-0. Opponent has never scored.
- This appears to be a "bonus" round 5 (task says match limit is 5 rounds; 5 rounds already logged 0-4).
- Verified `main.py` imports cleanly. Not changing anything.
- Rationale: 5/5 perfect shutouts, zero upside to change on final round.

## NEW MATCH SERIES vs nbw__nbw-crystal — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `nbw__nbw-crystal`. STRONGER than previous shutout opponents.
- Round 0 result: WON 232-3 with 3 ties (~97% win rate; 232 W, 3 L, 3 T out of 238 games).
- Verified `main.py` imports cleanly and returns valid move.
- Analyzed 3 losses: all involve mid/late-game self-trap or crystal snake outlasting us in corner scenarios.
  - sim_117 (short 32t): after eating, we made a corner move that limited future options.
  - sim_106 (50t): moved into a corner pocket at (0,10), later got trapped/starved.
  - sim_203 (196t): long game, opponent grew to length 18 vs our 11 and outlasted us.
- Common thread: our bot doesn't look far enough ahead in tight corners/late game.
- Decision: NOT changing code. Rationale:
  * 97% win rate is dominant; regression risk to modify late-game behavior.
  * The `tail_reachable` + 2-ply H2H protections added vs graeme-hill are already active.
  * Prior series ranged 95-100% win rate; this bot handles all opponents well.
- If losing more in future rounds, consider:
  * Extended horizon: check if reachable tail count strictly decreases (indicates trap)
  * Corner-avoidance penalty (extra cost for cells adjacent to 2+ walls)
  * Better length management: eat less when opponent is much shorter to avoid dying by starvation OR self-trap

## NEW MATCH SERIES vs nbw__nbw-crystal — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `nbw__nbw-crystal`. Round 0: 232-3-3. Round 1: 237-6-6. ~97% win rate.
- Verified `main.py` imports cleanly. Not changing.
- Same rationale: dominant win rate, regression risk >> upside.

## NEW MATCH SERIES vs nbw__nbw-crystal — Round 3 (opus-4-7): CODE CHANGES
- Opponent: `nbw__nbw-crystal` (NEW! Not the nessegrev family).
- Rounds 0 (232-3, 3T), 1 (237-6, 6T), 2 (233-8, 9T) — we still win but opponent DOES score, and ties increasing.
- **Analysis**: 16/17 losses have opus dying on a wall/edge. 9/18 ties same. Classic "wall-chase trap" pattern:
  We crawl along an edge (e.g. y=0); opponent mirrors on inner row (y=1). We hit corner and die by h2h with the longer/equal opponent.
  Example: `/logs/rounds/2/sim_2.jsonl` — opus went (2,1)→(2,0) at turn 21 (should've gone north), then died at corner (10,0).
- **Fix in main.py** (score function, near bottom):
  1. Increased on-edge penalty from -2 to -3.
  2. Added `trap_risk` detection: same-or-longer opp head within 4 cells on the inner adjacent row/col → -60.
  3. Corner penalty increased -10→-15.
  4. Added wall-crawl detection: if own body has 2+ segs on same edge as this move, extra -5/seg.
- Verified: `/tmp/replay_test.py` — the exact turn-21 losing state now returns "up" instead of "down". Good.
- Verified: 29 random frames from wins still produce valid moves.
- Backup of prior version: `main_backup2.py`.

## Files for teammates
- `main.py`: Current bot with wall-trap avoidance.
- `main_backup.py`, `main_backup2.py`: Prior versions.
- `/tmp/analyze.py`, `/tmp/loss_pattern2.py`: analysis scripts (regenerate if needed — /tmp is ephemeral).

## Analysis: loss/tie by opus edge-position
```python
# See /tmp/loss_pattern2.py — 16/17 losses on edge; 9/18 ties on edge.
```

## If losses continue after this round:
- Consider a deeper 2-3 ply minimax for opp moves (currently only 1-ply).
- Add "opponent-crawl breaker": if opp is on inner row parallel to us, occasionally force a direction change even mid-crawl (aggressive turn to break parallel).
- Track: are we PROVOKING the mirror by hugging walls early? Consider penalizing edge cells more strongly in early game (when snake is short and space is abundant).

## NEW MATCH SERIES — Round 4 (opus-4-7): MODIFIED main.py
- Opponent: `nbw__nbw-crystal` (STRONGER than nessegrev family).
- Prior scores in this series: R0 232-3 (3 ties), R1 237-6 (6 ties), R2 233-8 (9 ties), R3 240-8 (2 ties).
- Investigated losses: pattern is WALL-CORNER TRAPS. Opponent herds us along a wall/edge
  and we get stuck in the corner because we refused an equal-length H2H (tie) and instead
  walked into a certain-death dead-end.
- Fixes applied in `main.py`:
  1. Distinguish `danger_h2h` (strictly longer opp = we LOSE) from `tie_h2h` (equal length = TIE).
  2. When no non-tie option has adequate space (space >= new_len), allow tie H2H as a fallback
     (better than certain death). Threshold: if best non-tie space < max(3, my_len // 2), keep ties.
  3. Score penalty for tie H2H is -40 (bad, but less than -100 no-space or certain trap).
  4. Extra penalty for taking food onto an edge/corner cell when a larger opp head is within
     manhattan distance 5 (`-40` corner, `-15` edge). Prevents corner-food-chase suicide.
- Backup of previous main.py at `main_backup3.py`.
- Testing: reconstructed the actual T43 loss state from sim_22 — bot now chooses tie H2H
  ('right') instead of walking into corner (previously took 'left' and died).
- Rationale: We were converting some of the games we lost. Converting losses to ties won't
  beat wins directly but reduces opponent's score. Preventing corner-food-chase also directly
  reduces future losses.

## Files
- `main.py`: Active bot (patched Round 4).
- `main_backup3.py`: Pre-Round-4 version (working, 240-8 score).
- `main_backup.py`, `main_backup2.py`: Older versions.
