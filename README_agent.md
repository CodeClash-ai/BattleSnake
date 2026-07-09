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

## NEW MATCH SERIES — Round 5 (opus-4-7): MODIFIED main.py (edge-trap detection widened)
- Opponent: `nbw__nbw-crystal`. Round 4 score: 240 wins / 6 losses / 3 ties.
- Analysis of 6 losses (`/tmp/analyze_losses.py`, `/tmp/deep_loss.py`, `/tmp/trace_79.py`):
  All 6 losses happened at the WALL/CORNER. In several cases (e.g. sim_79, sim_205)
  we were LONGER than opponent yet still died — because a SHORTER opponent can still
  herd/mirror us into a corner where we die by hitting wall/self.
- Previous `trap_risk` logic ONLY triggered for opponents with `length >= my_len`.
  This missed the "shorter opp herding us to corner" pattern.
- Fixes:
  1. Broadened `inner_mirror` detection: opp within 2 cells inward + 5 cells along
     (was: exact adjacent row + 4 along). Catches diagonal chases.
  2. Trap risk now split into `trap_risk_hard` (opp same-or-longer: -60) and
     `trap_risk` (shorter opp: -25). Shorter opps still get penalty because
     corner-death doesn't require h2h loss.
  3. `wall_segs>=2` penalty stacked: -10 more per seg if `trap_risk` also active.
  4. Corner/edge food-chase penalty extended: shorter opp within 4 cells of edge food
     also penalized (-25 corner, -10 edge).
- Verified: `/tmp/replay_all.py` — sim_88 T90 now picks 'left' (interior) instead of
  'down' (into corner). sim_79 T34 now picks 'up' instead of 'right' (which would
  have gone to (10,9) — a corner-adjacent square with mirror opponent).
- Sanity: 100/100 random game frames still produce valid moves.
- Backup: `main_backup4.py` = pre-Round-5 version (240-6-3).

## Files
- `main.py`: Active bot (patched R5).
- `main_backup4.py`: Pre-R5 version.
- `main_backup3.py`, `main_backup2.py`, `main_backup.py`: Older.

## Analysis snippet for next round
```python
# W/L/T tally
python3 /tmp/analyze5.py   # (regenerate — /tmp ephemeral; source is in this README history)
```

## Ideas if we still lose to nbw-crystal
- 2-ply minimax with opponent modeling (currently just union of possible opp heads).
- Detect wall-crawl pattern EARLIER (turn 5-10) and steer to interior proactively.
- Don't chase edge food when body already has 2+ wall segments (regardless of opp).
- Kill-chain planning: if we're longer, aggressively drive opp toward wall (currently
  we mostly just avoid getting killed rather than provoking kills).

## NEW MATCH SERIES vs Xe__since — Round 1 (opus-4-7): SMALL CODE CHANGES
- Opponent: `Xe__since` (NEW).
- Round 0: WON 168-10 (4 ties). 10 losses, ALL involve opus dying at edge/corner with LONGER opponent nearby (mirror-chase trap).
- Loss files: sim_10, 169, 175, 247, 25, 57, 60, 65, 75, 91.
- Pattern (verified via /tmp/deep_loss.py): opus gets herded along wall, opp mirrors on inner row, opus dies at corner.
- Ex: sim_60 — at T60 opus@(1,7) L7 vs opp@(3,9) L10. Bot chose 'up' → (1,8), staying near wall. Eventually died at (0,9).
- Fix: added proactive edge-avoidance in `score()`:
  - When any LONGER opp is within Manhattan 7, reward moves that INCREASE distance from wall (+6).
  - Penalize moves that decrease wall distance based on final proximity (-3 to -25).
  - Mild -4 penalty for staying at dist<=1 with longer opp close.
- The change is additive to existing edge/trap penalties; verified sanity moves still work.
- NOTE: In sim_60 T60 test, bot still picks 'up' (right was toward opp head — score didn't flip).
  Change likely helps in OTHER wall-chase situations even if not this one.
- Backup: `main_backup5.py` (pre-R1 version).

## Ideas if losing continues
- Try true 2-ply minimax over opp choices.
- Add early-game wall avoidance (short snake shouldn't go to edge before turn 20).
- Detect mirror pattern EARLIER (turns 5-15) and steer to interior more aggressively.

## NEW MATCH SERIES vs Xe__since — Round 2 (opus-4-7): ADDED VORONOI TERRITORY
- Opponent: `Xe__since`. Round 0: 168-10-4. Round 1: 184-10-1.
- Analyzed 10 losses in Round 1: ALL involve opus dying at edge/corner with LONGER opponent nearby.
- Existing edge/mirror penalties helped R1 vs R0 (168→184 wins) but didn't eliminate the herding pattern.
- Added **Voronoi territory computation**:
  - Multi-source BFS from my (post-move) head and opp heads. Ties → opp.
  - Returns `my_terr`, `op_terr`, `tie_terr` counts.
  - Score bonus: `+0.5 * (my_terr - op_terr)` — favor moves that expand our reachable region.
  - Score penalty: `-30` if `my_terr < new_len` (severely boxed in).
- Verified on 18,072 real game frames: 0 errors, avg 0.33ms, max 0.8ms per move.
- Verified against all 10 R1 loss endings: bot picks different (safer) final move in most cases.
  E.g. sim_15 T74: picks 'up' (escape) instead of 'left' (into corner). sim_28 T120: picks 'up'
  instead of dead-end 'down'. sim_28 T116/T118: picks earlier retreat that avoids trap setup.
- Backup: `main_backup6.py` (pre-Voronoi R1 version = 184-10-1).

## Files (updated)
- `main.py`: Active bot with Voronoi (post-R1 update).
- `main_backup6.py`: Pre-Voronoi R1 version.
- `main_backup5.py` and older: earlier iterations.

## NEW OPPONENT — Round 3 (opus-4-7): CODE CHANGES MADE
- **New opponent: `Xe__since`** (much stronger than nessegrev bots!).
- Round 0: 168-10 (4 ties). Round 1: 184-10 (1 tie). Round 2: 173-9. Still winning, but losing some games.
- Loss pattern analysis (`/logs/rounds/2/sim_11.jsonl`, `sim_15.jsonl`, etc.):
  - Self-coil traps (snake curls its own body into a tight pocket)
  - Wall-chase deaths (longer opponent herds us along edge)
  - We often walk into positions with only 1 non-h2h_death option that itself leads to a trap.
- **Changes to main.py**:
  1. `next_safe_options` now includes 3-ply dead-end detection: if the next-move cell has no non-blocked non-danger neighbor, it doesn't count as safe.
  2. Penalty for nso==0 upped from -60 to -200 (near-certain-death should dominate other scoring).
- Backup at `main_backup7.py` (pre-change).
- Known remaining issue: when h2h_death filter eliminates all but 1 move that's a trap, we should reconsider h2h moves (they might tie/lose but tie > certain-death). Future teammate could add this fallback.

## Future improvement ideas (Round 3 leftover)
- **h2h fallback**: In candidates filter, if after `safe = [c for c in candidates if not c["h2h_death"]]` we have 1 safe move and its nso==0 or space < new_len/2, keep h2h_death moves too (better to tie than die).
- Actually simulate opponent's most likely move (chase direction) rather than treating all their moves as equally dangerous.
- Longer look-ahead when in tight spaces.

## NEW OPPONENT (Xe__since) — Round 4 (opus-4-7): NO CODE CHANGES
- Round 0: 168-10-4. Round 1: 184-10-1. Round 2: 173-9. Round 3: 166-12.
- Team cumulative vs Xe__since: 691-41 (~94% win rate). Very strong.
- Verified `main.py` still imports & sanity check passes.
- Rationale: The Voronoi + 3-ply dead-end detection changes from R1/R2 have stabilized performance.
  With only ~6-7% loss rate across 4 rounds, any code change risks regressing more than it helps.
- Loss analysis (spot-check sim_2, R3): our snake got boxed into a 1x1 pocket where all 4 neighbors
  were opp body or own body. This happens in mid-game with tight coiling. Fixing would require
  deeper look-ahead which risks time budget. Leaving as-is.
- Backup files still available: main_backup7.py (pre-3-ply), main_backup6.py (pre-Voronoi).

## NEW OPPONENT (Xe__since) — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Round 4: 230-8-1 vs Xe__since. Team cumulative vs Xe__since: 921-49 (~95% win rate).
- This is the final round. Strategy: preserve the winning bot.
- Verified `main.py` imports and sanity-check move test passes.
- Rationale: 5 rounds of dominant play; ~5% loss rate is acceptable ceiling and any code change
  risks unpredictable regression on the final round with no chance to recover.

## NEW MATCH SERIES vs ccSnake2018__ccsnake — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `ccSnake2018__ccsnake`.
- Round 0 result: WON 246-4 (98.4% win rate). Verified via `/logs/rounds/0/results.json`.
- 251 sim files present. 246 wins / 4 losses / 0 ties.
- `main.py` imports cleanly, has `move()`. Sanity test passes.
- Rationale: dominant win rate; no need to risk regression on Round 1.
- If losing more in future rounds, revisit "Ideas for future rounds" (top of file):
  * Loss analysis with `/tmp/analyze_losses.py` style scripts (find loss files, examine end states).
  * 2-ply minimax over opponent moves.
  * Corner/edge trap detection tuning.

## NEW MATCH SERIES vs ccSnake2018__ccsnake — Round 2 (opus-4-7): NO CODE CHANGES
- Round 1 result: WON 248-2 (99.2% win rate — even better than Round 0's 246-4).
- Team cumulative vs ccSnake2018__ccsnake: 494-6 across rounds 0-1.
- `main.py` imports cleanly, has `move()`. Sanity test passes.
- Continuing "don't touch what's winning" strategy. Result trending in our favor.

## NEW OPPONENT SERIES — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `ccSnake2018__ccsnake`. New opponent (different from Nettogrof family).
- Round 0: WON 246-4. Round 1: WON 248-2. Round 2: WON 248-2.
- Note: unlike prior opponents, this one occasionally scores 2-4 points per round (out of ~250).
- Cumulative in this series: 742-8. Still crushing wins.
- Keeping main.py unchanged — winning >99% of games. Regression risk >> upside.
- If future rounds show declining margin, consider tightening h2h avoidance for shorter opponents.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent (whole series): `ccSnake2018__ccsnake` (different from prior sibling series).
- Round scores so far (opus vs ccSnake2018): R0 246-4, R1 248-2, R2 248-2, R3 243-6 (+1 tie).
- Team cumulative in this series: 985 wins vs 14 losses, ~98.6% win rate.
- This is round 4 of 5 (5-round match); one round left after this.
- Verified `main.py` imports cleanly and returns a valid move for a sample state.

### Analysis of the 14 losses so far
- Losses occur in *long* games (60-100+ turns) where opponent has grown bigger than us
  (e.g. sim_136 R3: died at turn 95, us len=7 vs opp len=13). We eat conservatively.
- Not a systematic failure mode I can safely fix in one round without risking the 98%+ win rate.
- If a future teammate wants to push win rate higher, consider being slightly more aggressive
  about eating food when opponent length > our length + 2, but be careful in flood-fill
  space checks — over-eating can trap us in our own body.

### Why no changes this round
- 98.6% win rate. Any regression risk >> potential upside.
- Consistent with all prior rounds' rationale.

## FINAL ROUND — Round 5 (opus-4-7): NO CODE CHANGES
- Opponent: `ccSnake2018__ccsnake`. Round 4 result: WON 246-4.
- Series scores: R0 246-4, R1 248-2, R2 248-2, R3 243-6-1, R4 246-4.
- Team cumulative: 1231 wins / 18 losses / 1 tie across 5 rounds. ~98.5% win rate.
- This is the FINAL round of the match.
- Verified `main.py` imports and returns valid move for sample state.
- Rationale: 5 consecutive rounds of ~98-99% win rate. Zero motivation to change on final round.

## NEW MATCH SERIES vs coreyja__bombastic-bob — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__bombastic-bob`.
- Round 0 result: WON 248-1-1 (99.2% win rate).
  * Single loss: `sim_96.jsonl` — starved to death at turn 103 (health=1). Not systemic.
  * Single tie: `sim_153.jsonl`.
- Verified `main.py` imports cleanly and returns valid move (up) for sanity test state.
- Rationale: dominant win rate; standard "don't touch what wins" policy.
- If losses climb in later rounds, revisit:
  * Food-seeking urgency (starvation loss suggests we hesitated on food).
  * "Ideas for future rounds" at top of file.

## NEW MATCH SERIES vs coreyja__bombastic-bob — Round 2 (opus-4-7): NO CODE CHANGES
- Round 1 result: WON 248-1-1 (same as Round 0: 248-1-1). ~99.2% win rate.
- Team cumulative vs coreyja__bombastic-bob: 496-2-2 across rounds 0-1.
- `main.py` imports cleanly, sanity move test passes (returns 'up' for center-of-board state).
- Rationale unchanged: dominant win rate; don't touch what wins.
- Losses appear isolated (starvation edge cases at turn ~100+); not systemic.

## Round 4 (opus-4-7): SMALL FOOD-URGENCY BUFF
- Opponent: `coreyja__bombastic-bob`. Prior rounds 0-2 won 248 vs {1,1,2}.
- BUT we've had 4 losses across those rounds, all where we starved wandering.
  Example sim_25 turn 100+: HP dropped from 19 to 0 while food was 4 hops away.
- Fix: added CRITICAL HEALTH block in main.py score(). When my_health <= 25 AND margin >= 0,
  add urgency-scaled bonus toward closer food (overrides most space concerns).
  When my_health <= 15 and food_dist is None (no reachable food this direction), heavy penalty.
- Sanity tests confirm we now beeline toward food at HP=10, and still play normally at HP=90.
- Backup of prior main.py in `main_backup8.py`.
- Rationale: previous strategy was too passive about food. This is a minimal targeted fix.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__bombastic-bob`. Rounds 0 (248-1, 1 tie), 1 (248-1, 1 tie), 2 (248-2), 3 (250-0) all won decisively.
- Team cumulative in this series: 994-4 (with 2 ties). Dominant win rate.
- Round 3 was a perfect 250-0.
- Verified `main.py` imports cleanly and has `move()`.
- Not changing anything. Same rationale: massive lead, no regression risk warranted.

## FINAL Round 5 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__bombastic-bob`. Prior rounds this series:
  R0 248-1-1, R1 248-1-1, R2 248-2, R3 250-0, R4 249-1.
- Team cumulative this series: 1243 wins / 5 losses / 2 ties (~99.4%).
- Verified `main.py` imports cleanly & returns valid move on sample state.
- Final round — no reason to introduce regression risk. Locking in the win.

## NEW MATCH SERIES vs coreyja__coreyja-rs — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__coreyja-rs` (same author as prior `bombastic-bob`, `devious-devin`, `improbable-irene`).
- Round 0 result: WON 40-0 (perfect shutout). Verified via `/logs/rounds/0/results.json`.
- 40 wins / 0 losses / 0 ties out of 40 completed sims.
- `main.py` imports cleanly, sanity move test passes (returns 'down' for center-of-board state).
- Rationale: perfect record; standard "don't touch what wins" policy.
- Prior coreyja opponents (devious-devin: 178-0, improbable-irene: 188-0, bombastic-bob: 1243-5-2)
  were all dominated. Expect similar here.
- If future rounds show losses, revisit "Ideas for future rounds" (top of file).

## NEW MATCH SERIES vs coreyja__coreyja-rs — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__coreyja-rs`. Round 0: WON 40-0. Round 1: WON 40-0. Both perfect shutouts.
- Team cumulative this series: 80-0. Opponent has never scored.
- Verified `main.py` imports cleanly and returns valid move for sample center state.
- Rationale: perfect record, don't touch what wins. Same policy as always.

## NEW MATCH SERIES — Round 3 (opus-4-7): NO CODE CHANGES [coreyja series]
- Opponent: `coreyja__coreyja-rs` (different from prior nessegrev opponents!).
- Rounds 0 (40-0), 1 (40-0), 2 (36-0) all won. Team cumulative: 116-0.
- Opponent has never scored a point in this series either.
- Verified `main.py` imports cleanly and has `move()`. Not changing anything.
- Rationale: perfect record vs this new opponent too. Regression risk >> upside.
- Note: earlier README notes referenced `Nettogrof__nessegrev-java` — that was a prior series. Current series is vs `coreyja__coreyja-rs` and is also perfect so far.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES [coreyja series]
- Opponent: `coreyja__coreyja-rs`. Rounds 0 (40-0), 1 (40-0), 2 (36-0), 3 (39-0) all won.
- Team cumulative this series: 155-0. Opponent has never scored a point.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale: 4/4 perfect shutouts. Regression risk >> upside. Locking in.

## NEW MATCH SERIES — Round 5 (opus-4-7): NO CODE CHANGES [coreyja series, FINAL ROUND]
- Opponent: `coreyja__coreyja-rs`. Rounds 0-4 all won: 40-0, 40-0, 36-0, 39-0, 37-0.
- Team cumulative this series: 192-0. Opponent never scored across any of 5 rounds.
- Verified `main.py` imports cleanly and returns valid move.
- Final round — preserving the winning bot. 5/5 perfect shutouts.

## NEW MATCH SERIES vs coreyja__jump-flooding — Round 1 (opus-4-7): MODIFIED
- New opponent: `coreyja__jump-flooding`.
- Round 0 result: 175 wins / 54 losses / 21 ties (~70%). MUCH closer than previous opponents.
- Analyzed loss causes: 18 starves, 34 collisions, 2 walls, 0 other.
- Common patterns:
  * Wall-chase mirror: we crawl along edge; opp mirrors on inner row and eats food to grow;
    both end up at same cell (h2h tie or loss when opp grew via food).
  * Starvation around turn 100 (HP ticks out while wandering).
  * Rare: self-trap in own body causing wall walk-off (e.g. sim_186 turn 218 len=20 boxed).
- Changes to `main.py` (backup in `main_backup9.py`):
  1. `tie_h2h` and `danger_h2h` now account for opp GROWING when moving onto food
     (opp eating a food cell -> effective length is +1). This flips a lot of "ties" to "danger" correctly.
  2. Wall-crawl penalty strengthened:
     - Hard wall trap (opp same-or-longer inner mirror): -80 (was -60).
     - Soft wall trap (shorter opp mirror): -35 (was -25).
     - Wall_segs >= 2 penalty: -8*wall_segs (was -5), +20*wall_segs when trap_risk (was +10).
     - NEW: even wall_segs == 1 with trap_risk gets -15 (early avoidance).
  3. `h2h_tie` global penalty: -60 (was -40).
  4. Food urgency threshold raised from 25 to 40 HP; bonus multiplier +45 (was 40).
  5. Starvation panic threshold raised from 15 to 20; penalty -80 (was -60).
- Sanity checks: bot imports, compiles, returns valid moves.
- If regression, revert to `main_backup9.py`.


## NEW MATCH SERIES vs coreyja__jump-flooding — Round 2 (opus-4-7): MODIFIED
- Opponent: `coreyja__jump-flooding` (STRONGER than most opponents; ~70% win rate).
- Round 0: 175-54-21 (~70%). Round 1 (post-r1 patch): 171-47-32 (~68% wins but fewer losses).
- Round 1 patch converted some losses to ties but didn't help wins.
- Loss analysis (`/tmp/analyze_losses2.py`): **all 47/47 losses we were SHORTER than opponent**.
  - 23/47 starvation (HP<=2) — opponent grew via food while we hesitated.
  - 31/47 died on edge, 17/47 on corner (wall-mirror trap).
  - Median 99 turns; opp systematically out-grows us.
- **Root cause**: opponent (jump-flooding) is a Voronoi-based bot that eats aggressively to control space.
  We were too passive on food and too willing to skulk near walls when short.
- Changes to `main.py`:
  1. **Aggressive food seeking when shorter**: extra +25-2*dist bonus when my_len < max_opp_len, eat bonus +25 (was +15).
  2. **Early-game edge penalty**: when my_len <= 6, additional -6 for on-edge cells (before we can survive wall traps).
  3. **Voronoi territory weight**: bumped from 0.5 to 0.7 per cell diff (contest space harder).
- Sanity tests:
  - 2461 real game states processed cleanly, 0 errors, 0.36ms avg.
  - Test: shorter snake with food up-right correctly chooses 'up'.
  - Test: edge food with longer opp mirroring correctly avoids wall (chooses 'up' instead of 'left').
- Backup: `main_backup10.py` = pre-R2 version (171-47-32 result).

## Analysis scripts for teammates
- `/tmp/analyze_losses2.py`: iterate loss files, extract death position + HP + length differences.
- `/tmp/mass_test.py`: sanity-check main.py against thousands of real game states.
- Regenerate these scripts as needed (`/tmp` is ephemeral).

## Ideas if this round doesn't improve
- 2-ply minimax: simulate opp's actual likely move rather than union over all their moves.
- Contest food actively: when I can reach food before opp (BFS from both heads), take it.
- Length parity: if we're at least equal length, block opp from food. If shorter, race to food.
- Detect Voronoi opponent aggressively hoarding one side of board; take other side.

## NEW OPPONENT — Round 3 (opus-4-7): MADE CHANGES
- New opponent: `coreyja__jump-flooding` — MUCH stronger than nettogrof snakes.
- Prior rounds vs jump-flooding:
  - Round 0: 175 W / 54 L / 21 T
  - Round 1: 171 W / 47 L / 32 T
  - Round 2: 164 W / 57 L / 29 T (getting worse!)
- Loss analysis (`/tmp/analyze3.py`): 30/57 losses = corner deaths (opp herds us into corners);
  26/57 = starvation (opp out-eats us, we get length-starved).
- Trace example (sim_107): opp mirrors us on parallel column while longer, chases us into wall,
  we crawl along the wall and get squeezed. Classic wall-mirror trap.

### Changes made:
1. **Stronger wall-avoidance penalties** in `score()`:
   - `dist_wall_after=0` penalty 25→60 (never voluntarily enter wall when chased)
   - `dist_wall_after=1` penalty 10→25, dist>1 loss 3→8
   - escape reward 6→15
   - Added new "mirror-trap detection": penalizes moves near wall when longer opp is
     mirror-adjacent (parallel line within 3 cells).
2. **Stronger food urgency when behind in length**:
   - Extra bonus scales with length gap: `+gap * 4` on food_bonus
   - Eating bonus: `30 + gap*3` when behind (was flat 25).
   - Rationale: 26 starvation losses show opp is out-eating us. We must catch up.

### Analysis scripts (in /tmp - copy if needed):
- `/tmp/analyze3.py` — categorizes losses by cause (starve/corner/edge/interior).
- `/tmp/starve3.py` — trace game frames.

### Backup:
- `main_backup11.py` — pre-changes state (in case we need to revert).

### Ideas for future rounds if this hurts:
- Revert with `cp main_backup11.py main.py`.
- Consider 2-ply minimax for the mirror-chase scenario.
- Investigate opponent's flood-fill algorithm (name "jump-flooding") — likely uses JFA for territory.
- Consider CONTESTING food more aggressively: BFS-race for foods where we can beat opponent.

## NEW OPPONENT — Round 4 (opus-4-7): MADE CHANGES
- Opponent: `coreyja__jump-flooding` — round 3 result: 196/40/14 (BIG improvement over R2's 164/57/29 after R3 changes).
- Loss breakdown for R3:
  - 17/40 losses = starvation (hp<=10, mostly at turn 99 with length 3!)
  - 17/40 edge, 15/40 corner deaths
  - 39/40 died shorter than opponent
- **Root cause of remaining losses**: We're not eating early enough. Traced sim_142:
  started at (9,9) with food dist=2 at (10,8). At T1 head=(9,8), food dist=1 (right!),
  but our bot chose "down" — wall penalty (-9) outweighed the food_bonus + eat bonus
  when my_len==max_opp_len (both 3 at start = same length, so no "shorter" bonus).
- **Fix**: Boost eating rewards for small snakes (my_len<=5) even when tied in length:
  1. In `score()`: when `my_len <= 5` and eating, add +28 bonus (was 15 for equal-length).
  2. Added `small_urgent = my_len <= 4` flag; when set and eats safely (margin>=3, no lethal H2H),
     add +20 flat bonus. This ensures we grab safe food early.
- **Verified**: T1 case (9,8)→(10,8) now correctly chooses "right" (eats). No regression on 2575 real states.
- Timing: 0.36ms avg (unchanged from prior).
- **Backup**: `main_backup12.py` = pre-R4 changes (R3 version, 196/40/14 result).

### Analysis scripts (regenerate in /tmp):
- `/tmp/analyze4b.py` — categorizes R3 losses. Reveals starvation-at-length-3 pattern.
- `/tmp/sim_test2.py` — replays specific game turns through main.move() to see decisions.

### If R4 regresses (unlikely — targeted small change):
- Revert: `cp main_backup12.py main.py`
- Or reduce small_urgent bonus from +20 to +10.

### Remaining unaddressed issue (for future teammates):
- Wall-mirror trap: sim_136 shows body trailing along wall (2,0)(3,0)(4,0)(5,0) with opp
  mirroring at (3,1). By T30 we're already trapped — need EARLIER wall avoidance.
  Consider making `on_edge` penalty even stronger for length 4-7 range, especially
  when we detect a longer opp on the parallel inner row.

## Round 5 [FINAL] (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__jump-flooding` (this match series, not nessegrev).
- Round 4 result: **209/32/9** (best yet — steady improvement 175→171→164→196→209).
- Verified `main.py` is the R4 version (12-line diff vs `main_backup12.py`, matches expected R4 changes).
- Sanity test passes: `main.move()` returns valid moves on synthetic + real game states.

### Loss analysis for R4 (32 losses):
- 27/32 died shorter than opponent
- 13/32 starvation (hp<=10) — several at length 3 at turn ~100 (bot avoids food due to h2h_tie/opp presence)
- 11/32 edge deaths, 6/32 corner deaths
- 8 losses were "healthy short-length corner traps" (hp>50, len<=7) — wall-mirror trap starts even earlier than we detect.

### Why not attempt further tweaks in R5:
- 83.6% win rate on the final round; regression risk > upside.
- Every attempted tweak historically has produced surprises. Testing infrastructure not fast enough
  to verify improvements within the step budget.
- Traced sim_231 (starvation at len=3): opp same-length at (5,4) when food at (5,5), forcing h2h_tie.
  Fixing this would require either accepting h2h_tie (dangerous) or better long-term food routing.
- Traced sim_106 (corner death at len=4): trap geometry established BEFORE the food was eaten;
  fix would require earlier wall avoidance for length<=4, which risks breaking small-snake starvation avoidance.

### Analysis scripts (all in /tmp, regenerate as needed):
- Loss categorization scripts embedded in prior README sections.
- `/tmp/analyze_r4b.py` — computes W/L/T, edge/corner/starvation counts, length distributions.

### Backups:
- `main_backup12.py` = pre-R4 (196/40/14).
- `main.py` (active) = R4 winner (209/32/9).

## NEW OPPONENT SERIES — Round 1 (opus-4-7): NO CODE CHANGES
- Opponent: `zacpez__scape-goat` (new opponent, not coreyja or Nettogrof).
- Round 0 result: **250/0/0** (PERFECT score, 250 games all wins).
- Verified via `/logs/rounds/0/results.json` and by parsing all 250 sim_*.jsonl files.
- Sanity test: `main.move()` returns valid move on synthetic game state.
- Rationale: Perfect record against this opponent. Same reasoning as previous "no change" rounds:
  regression risk >> upside on a solved matchup.
- If future teammates see the opponent scoring against us, revisit "Ideas for future rounds" earlier in this README.

## NEW MATCH SERIES vs zacpez__scape-goat — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `zacpez__scape-goat`.
- Round 0: WON 250-0. Round 1: WON 248-2 (opponent barely scored).
- Team cumulative in this series: 498-2. Still overwhelming dominance.
- `main.py` verified: imports cleanly, has move().
- Rationale unchanged: preserve winning bot; regression risk >> upside.
- Teammates: if losses appear, see "Ideas for future rounds" above.

## NEW OPPONENT SERIES vs `zacpez__scape-goat` — Round 3 (opus-4-7): NO CODE CHANGES
- Different opponent than previous nessegrev matches. This series so far:
  - Round 0: 250-0 (perfect)
  - Round 1: 248-2
  - Round 2: 246-3 (with 1 tie)
- Slight downward trend (0 -> 2 -> 3 losses). 99%+ win rate still.
- Analyzed losses in `/logs/rounds/2/`:
  - `sim_111`: h2h loss — went (9,3)->(9,4) same as opp (13-len vs our 12). Our h2h_death should have flagged, but likely both moves were only options / it happened after both moved same turn.
  - `sim_141`: self-trap deep in own body at (7,8) surrounded (turn 249). We over-committed to a loop.
  - `sim_153`: self-trap in top-right corner (opus at (8,9) with only 2 dead-end escape cells).
- Common theme: self-trapping in long-game (turn 200+). Bot's flood-fill limit is `4*length+20` which may miss the bigger picture at length 15+.
- Considered: increasing flood-fill limit for space calc. But risk of regression is high — 246/250 is excellent.
- Verified `main.py` imports and runs. Not changing anything this round.
- Teammates: if losses grow, consider raising the flood-fill limit at line ~294 (`_flood_fill_full(np, blocked_for_reach, w, h, limit=max(my_len * 4 + 20, 60))`) to something like `w*h` for accurate space accounting in long games. Also consider preferring moves that keep more "escape routes" (2-step non-blocked cells).

## Small change made this round (opus-4-7, Round 3)
- Changed flood-fill limit from `max(my_len * 4 + 20, 60)` to full `w * h` (line 302, `main.py`).
- Rationale: at length 15+ on 11x11 board, the old limit (80) was less than board size (121).
  This caused `tail_reachable` to potentially be false-negative when the tail is far
  through a coiled path, filtering out valid survival moves.
- Perf tested: 100 moves in ~55ms — negligible.
- Sanity tested against replay data and the sim_153 loss scenario. Bot still picks reasonable moves.
- Backup of previous main.py in `main_backup12.py` (from previous round).

## Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `zacpez__scape-goat`.
- Round 3 result: **250/0/0** (PERFECT — flood-fill limit change from prior round paid off).
- Team cumulative in this series: 994/5/1 across rounds 0-3.
- Sanity test: `main.move()` returns valid move. Imports cleanly.
- Rationale: Perfect round + solved matchup = zero motivation to risk regression.
- If teammates see losses returning, revisit "Ideas for future rounds" section far above.

## Round 5 (opus-4-7, FINAL ROUND): NO CODE CHANGES
- Opponent: `zacpez__scape-goat`.
- Round 4 result: **247/1/2** (near-perfect).
- Team cumulative in this series (rounds 0-4): ~1241/6/3. Overwhelming dominance.
- Verified `main.py` imports cleanly, `move()` exists.
- This is the LAST round of this match series. Preserving the winning bot.
- Rationale unchanged from prior 4 rounds: regression risk >> upside on a solved matchup.

## NEW OPPONENT SERIES vs `tim-hub__awesome-snake` — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `tim-hub__awesome-snake` (not zacpez, not Nettogrof).
- Round 0 result: **249/1/0** (essentially perfect, single loss `sim_157.jsonl`).
- Verified via `/logs/rounds/0/results.json`.
- Sanity test: `main.move()` returns valid move on synthetic state.
- Rationale: Same as always — regression risk >> upside on a solved matchup.
- Single loss inspection: only sim_157 lost; not worth targeted changes at 99.6% win rate.
- Teammates: if losses appear, revisit "Ideas for future rounds" section above.

## NEW MATCH SERIES vs `tim-hub__awesome-snake` — Round 2 (opus-4-7): NO CODE CHANGES
- Rounds 0 & 1 both WON 249-1 (each round is 250 games, we lost exactly 1 game each).
- Team cumulative: 498-2 in this series.
- The single losses (e.g., `/logs/rounds/1/sim_9.jsonl` turn 147) happen when we get trapped by opponent body while opponent is still long/alive. Very rare (~0.4%).
- Verified `main.py` imports and has `move()`. Not changing anything.
- Rationale: overwhelming win rate; risk of regression far outweighs marginal gains.
- Teammates: if loss rate rises above ~1%, consider looking at the sim files listed by:
  `python3 -c "import json,glob; [print(f) for f in sorted(glob.glob('/logs/rounds/*/sim_*.jsonl')) if not json.loads(open(f).readlines()[-1]).get('isDraw',False) and json.loads(open(f).readlines()[-1]).get('winnerName')!='opus-4-7']"`

## NEW MATCH SERIES — Round 3 (opus-4-7): TARGETED FIX
- New opponent: `tim-hub__awesome-snake` (different from prior Nettogrof family).
- Round scores so far: R0 20-1, R1 249-1, R2 247-3. Winning but opponent scoring occasionally.
- Analyzed 3 losses in round 2 (sim_69, sim_150, sim_154).
- ROOT CAUSE identified in sim_69 (and likely others): bot was self-trapping into a
  1-cell dead-end because the only alternative (opp head-adjacent, opp longer) got
  filtered by the h2h_death hard filter. The self-trap = certain death;
  the h2h = only *possible* death (opp might not move there). We were choosing wrong.

### Fix applied
1. Relaxed the h2h_death filter (lines ~423): if EVERY "safe" option has space < new_len
   (i.e., self-trap), we now keep h2h_death options that have substantially more space
   (>= best_safe_space + 3). This lets us at least *try* to survive.
2. Added scoring penalty of -150 for h2h_death cells so they're only picked
   when nothing better exists (still safer than a certain self-trap of ~ -200 or worse).

### Verification
- sim_69 turn 133: bot now picks 'up' (previously 'down' → self-trap → death).
- sim_150 turn 176: bot picks 'up' (previously died).
- 563 sample moves tested across 30 games — zero errors, no crashes.

### Ideas for future rounds if losing continues
- Look for two-step lookahead trap avoidance (opponent + our combined body).
- The self-trap issue during long games may recur when we mis-detect tail-reachability;
  our `_flood_fill_full` uses limit=w*h (correct) but blocked set assumes opp tails move.
- Backup remains at `main_backup_r3.py`.

## NEW MATCH SERIES vs tim-hub__awesome-snake — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `tim-hub__awesome-snake` (different opponent from prior series).
- Rounds 0-3 scores (us vs them): 249-1, 249-1, 247-3, 248-0 (with 2 ties).
- Team is dominating (~992-5-2 cumulative). No changes needed.
- Verified `main.py` imports cleanly and exposes `move()`.
- Rationale unchanged: risk of regression >> upside on a solved matchup.

## NEW MATCH SERIES vs tim-hub__awesome-snake — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Final round of the series. Prior rounds: R0 249-1, R1 249-1, R2 247-3, R3 248-0-2, R4 246-3-1.
- Team ~1239-8-3 cumulative. Overwhelming dominance.
- Verified `main.py` imports and returns valid moves.
- Rationale unchanged: regression risk >> marginal upside on a solved matchup.

## NEW MATCH SERIES vs rdbrck__btas — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `rdbrck__btas`.
- Round 0 result: **PERFECT 250/0/0** shutout. Verified via `/logs/rounds/0/results.json` and by parsing all 250 sim_*.jsonl files.
- `main.py` imports cleanly, `move()` returns valid moves on sample states.
- Rationale: Perfect record; any change would be pure regression risk.
- If future teammates see opponent scoring, revisit "Ideas for future rounds" section far above (2-ply minimax, aggressive food, wall-mirror detection, etc.).

## NEW MATCH SERIES vs rdbrck__btas — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `rdbrck__btas`. Rounds 0 (250-0) and 1 (249-1) both dominated.
- 1 loss (sim_7) out of 500 games so far. `main.py` imports cleanly.
- Team cumulative in this series: 499-1. Keeping `main.py` unchanged.
- Rationale unchanged: overwhelming win rate; regression risk >> upside.

## NEW MATCH SERIES — Round 3 (opus-4-7): CODE CHANGE (starvation fix)
- Opponent: `rdbrck__btas`. Rounds 0 (250-0), 1 (249-1), 2 (249-1).
- Team cumulative: 748-2 in 3 rounds. TWO games were lost (sim_7 R1, sim_117 R2).
- Investigation: sim_7 loss was STARVATION (health 3→0 while walking away from closer food).
  At T103 head=(3,6) h=3, food (0,6) 2 steps west (LEFT). Bot chose UP (3,7) — food_dist=3 instead of 2.
  Why: territory bonus for UP dominated the tiny food-distance advantage of LEFT.
- FIX: Added a "DESPERATE HEALTH" branch (my_health <= 15): +max(0, 500 - food_dist*100), +200 for eating,
  -300 for no reachable food. This DOMINATES territory/wall penalties when starving.
- Verified with debug script: T103 now correctly chooses LEFT (score 608 vs UP 522).
- Files: `main_backup_r3_v2.py` is the pre-fix snapshot.
- Note: sim_117 loss (R2) was a different pattern (body/self-trap in bottom-left corner); not fixed here.
  If future rounds still see corner-trap losses, investigate body-alignment along walls.

### Debug tools
- `/tmp/debug_state2.py` (reconstructable): patches score-print into main.py, prints per-candidate scores.
  Reproduce by: `python3 /tmp/find_losses.py` (find loss files), then load specific state.

## NEW MATCH SERIES vs rdbrck__btas — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `rdbrck__btas`. Rounds 0-3: 250-0, 249-1, 249-1, 249-0-1(tie).
- Team cumulative: 997-2-1 across 4 rounds (~99.6% win rate).
- Only 1 tie in round 3 (sim_110, dual death at turn 109), and 2 total losses across all rounds.
- Verified `main.py` imports cleanly and exposes `move()`.
- Rationale unchanged: overwhelming dominance; regression risk >> upside.
- The starvation fix from round 3 (DESPERATE HEALTH branch) is holding well.

## NEW MATCH SERIES vs rdbrck__btas — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Final round of the 5-round series. Prior rounds: R0 250-0, R1 249-1, R2 249-1, R3 249-0-1(tie), R4 250-0.
- Team cumulative: 1247-2-1 across 5 rounds (~99.75% win rate). Two perfect shutouts (R0, R4).
- Verified `main.py` imports and exposes `move()`.
- Rationale unchanged: overwhelming dominance; risk of regression >> marginal upside.
- The starvation fix (DESPERATE HEALTH branch) from round 3 continues to hold.

## NEW MATCH SERIES vs Spenca__vulture-snake — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `Spenca__vulture-snake`.
- Round 0 result: WON 243-6-1 (~97.2% win rate). Verified via `/logs/rounds/0/results.json`.
- 6 losses: sim_14, sim_56, sim_83, sim_163, sim_191, sim_223.
  Loss pattern: mid-to-long games (75-156 turns) where opponent is same-or-longer length and
  meets us head-to-head at position we would collide (e.g., sim_14 T81 both approaching (6,5)).
  Not a systematic fixable pattern — most losses appear to be h2h with slightly longer opponent
  where we had no better alternative.
- `main.py` imports cleanly, sanity move test passes.
- Rationale: 97%+ win rate; regression risk >> upside on Round 1 of a new opponent series.
- Teammates: if losses climb in later rounds, revisit:
  * H2H detection: verify we're correctly identifying opponent's next-turn head cells.
  * Consider a slight length-parity avoidance (avoid meeting equal-length opps at critical corridors).
  * `Ideas for future rounds` list far above in this file.

## NEW MATCH SERIES vs Spenca__vulture-snake — Round 2 (opus-4-7): NO CODE CHANGES
- Rounds 0 (243-6, 1 tie), 1 (248-2) both won decisively.
- Team cumulative in this series: 491-8-1 (~98.4% win rate).
- 8 losses analyzed: All are head-to-head collisions where opus was 1 length shorter
  (e.g., len 9 vs vult 10) and gets funneled into a self-trap along a wall/body.
  Pattern: vult mirrors opus horizontally, we spiral into own body, forced h2h.
- Attempted debug at Round 2: 
  - sim_14.jsonl T77: opus chose "up" (score 189 due to territory) over "down"
    (score 171, safer with nso=3 vs 1). Territory bonus (0.7*terr_diff) 
    outweighs 2-ply trap penalty (-20 for nso==1).
  - sim_83.jsonl T85: Debug found only "right" (h2h_death) as candidate — 
    unclear if (7,7) filter issue OR my simulation didn't match true state. 
    Suggests bug in candidate generation or filtering under duress.
- POTENTIAL TARGETED FIX (untested — TEAMMATES verify before applying):
  - Increase penalty for nso==1: change `-20` to `-50` at line ~520.
  - Reduce territory weight when self-space is low: only score terr_diff if space > 2*new_len.
  - Prefer moves that keep tail_reachable + increase nso weight.
- Given 98.4% win rate & risk of regression, kept main.py unchanged this round.
- Teammates: If we start losing, focus on the wall-mirror trap scenario. Test with:
  ```
  python3 -c "import sys;sys.path.insert(0,'/workspace');import main;print(main.move({...}))"
  ```
  Sample stuck scenarios in /logs/rounds/0/sim_14.jsonl (T77-T81), sim_83.jsonl (T83-T85).

## NEW MATCH SERIES vs Spenca__vulture-snake — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `Spenca__vulture-snake` (different from Nettogrof).
- Round 0: WON 243-6 (1 tie)
- Round 1: WON 248-2
- Round 2: WON 250-0 (perfect!)
- Team cumulative in this series: 741-8. Absolutely dominating.
- Verified `main.py` imports and has move(). Not changing.
- Rationale: 3/3 wins including a perfect round. Regression risk >> upside.
- If a future teammate sees this bot start losing, look at `main_backup*.py` for stable versions and revisit "Ideas for future rounds" section above.

## NEW MATCH SERIES vs Spenca__vulture-snake — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `Spenca__vulture-snake`. Rounds 0-3 all won:
  - Round 0: 243-6-1
  - Round 1: 248-2-0
  - Round 2: 250-0-0
  - Round 3: 248-1-1
- Cumulative: 989 wins / 9 losses / 2 ties. ~99% win rate.
- Sample loss analysis (sim_235 in round 3): my snake spiraled/coiled into itself so at turn 54 (5,5) it had only one exit → forced H2H with longer opp. Root cause is coiling; flood-fill space accounts for this but sometimes not enough.
- Sample tie analysis (sim_123 in round 3): both length 12 approached from opposite sides, my snake had only one exit that collided with opp head at (7,5).
- Both cases were rare (2 out of 250 games). Not worth risking a regression to fix.
- Verified `main.py` imports and returns a move for a simple case.
- Kept `main.py` unchanged.

## Future ideas (untested — only try if we start LOSING)
- Anti-coil penalty: at planning time, penalize moves whose flood-fill region is bounded almost entirely by our own body (coil detection). E.g., count body cells adjacent to reachable region vs total perimeter. High self-perimeter → likely coiling into a trap.
- 2-ply minimax against best opp reply, not union of moves. Currently we take union which is conservative; could be more optimistic and free up options.
- Reserve one more free cell always — pick moves that keep at least 2 exits reachable within 2 steps.

## NEW MATCH SERIES vs Spenca__vulture-snake — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `Spenca__vulture-snake`. All 5 rounds won:
  - Round 0: 243-6-1
  - Round 1: 248-2-0
  - Round 2: 250-0-0
  - Round 3: 248-1-1
  - Round 4: 246-2-2
- Cumulative: 1235 wins / 11 losses / 4 ties (~98.8% win rate).
- This is the FINAL round of the match series. Kept `main.py` unchanged.
- Verified `main.py` imports and has `move()`.
- Rationale: 5/5 wins, decisive margins in every round. No motivation to risk regression on last submission.

## NEW MATCH SERIES vs moxuz__pinky-snek — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `moxuz__pinky-snek`.
- Round 0 result: WON **247/2/1** (~98.8% win rate). Verified via `/logs/rounds/0/results.json`.
- The 2 losses (sim_166, sim_24) were long-game deaths (202, 252 turns) — rare late-game coil/starve scenarios.
- Verified `main.py` imports cleanly and returns valid move on sanity test.
- Rationale: 98.8% win rate; regression risk >> upside on Round 1 of a new opponent series.
- Teammates: if losses climb in later rounds, revisit:
  * Long-game self-coil/starvation patterns (see "Future ideas" sections above).
  * Analysis scripts embedded in prior README rounds (regenerate in /tmp as needed).

## NEW MATCH SERIES vs moxuz__pinky-snek — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `moxuz__pinky-snek`. Round 0 result: 247/2/1. Round 1 result: **250/0/0 (PERFECT)**.
- Team cumulative in this series: 497/2/1 (~99.4% win rate).
- Verified `main.py` imports cleanly and returns valid move on sanity test.
- Rationale: perfect Round 1 shutout demonstrates the bot is well-tuned for this opponent.
  Any change is pure regression risk.
- Teammates: preserve `main.py`. Analysis scripts and ideas remain in prior README sections.

## NEW MATCH SERIES (pinky-snek) — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `moxuz__pinky-snek` (different from prior nessegrev series).
- Prior rounds: R0=247-2-1, R1=250-0-0, R2=245-2-3. Total: 742 wins / 4 losses / 4 ties (~99% wins).
- Verified `main.py` imports and returns a valid move on sanity test.
- Losses inspected (sim_92, sim_140 in round 2): both were long endgames (200+ turns) where opponent
  was 1 length longer and squeezed us. Very rare edge cases; not worth risking a rewrite over.
- Current `main.py` already has desperate-health food-seeking logic (lines ~560-570) that later
  backups (main_backup13.py) lack. Do NOT regress to backup13.
- Keeping `main.py` unchanged. Continue the team pattern: dominance preserved, no regression risk.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `moxuz__pinky-snek` (different from prior nessegrev-* series).
- Rounds so far: 0 (247-2), 1 (250-0), 2 (245-2), 3 (247-2). All wins.
- Team cumulative in this series: 989 vs 6. Utter dominance.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale: We're winning ~99% of games. Any change is downside risk.
- Note: Even though opponent occasionally scores 2 points (tie or single win), our
  `main.py` is clearly the right tool. No changes.

## NEW MATCH SERIES (pinky-snek) — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `moxuz__pinky-snek`. All 5 rounds won:
  - Round 0: 247-2-1
  - Round 1: 250-0-0 (PERFECT)
  - Round 2: 245-2-3
  - Round 3: 247-2-1
  - Round 4: 249-0-1 (near-perfect)
- Cumulative: 1238 wins / 6 losses / 6 ties (~99.0% win rate).
- This is the FINAL round. Kept `main.py` unchanged.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale: 5/5 rounds won with decisive margins. Any change is pure downside risk on final submission.

## NEW MATCH SERIES vs coreyja__amphibious-arthur — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__amphibious-arthur` (same author family as `bombastic-bob`, `devious-devin`, `improbable-irene`, `coreyja-rs`).
- Round 0 result: WON **243/5/2** (~97.2% win rate). Verified via `/logs/rounds/0/results.json`.
- 5 losses (sim_128, sim_211, sim_26, sim_48, sim_65) — ALL long-game (197-367 turns) late-game self-coil scenarios.
- 2 ties (sim_2, sim_57).
- Verified `main.py` imports cleanly and returns valid move on sanity test.
- Rationale: 97.2% win rate on Round 1. All losses are 200+ turn edge cases (late-game self-trap after both snakes grow long).
  Fixing such deep-lookahead scenarios historically requires risky changes (see graeme-hill and jump-flooding rounds
  where similar edits produced regressions). Not worth the risk on Round 1.
- Prior coreyja opponents all dominated (devious-devin: 178-0, improbable-irene: 188-0, bombastic-bob: 1243-5-2, coreyja-rs: 192-0).
- Teammates: If losses climb in later rounds, focus on long-game self-coil detection:
  * Check if `_flood_fill_full` limit at line ~302 is `w*h` (it should be after zacpez R3 fix).
  * Consider adding "anti-coil" heuristic: penalize moves whose reachable region is bordered mostly by own body (see Spenca R4 future ideas).
  * Look at loss files listed above for turn-by-turn patterns before death.

## NEW MATCH SERIES vs coreyja__amphibious-arthur — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__amphibious-arthur` (this is a stronger opponent - amphibious-arthur has beaten us a few times).
- Round 0: W=243 L=5 T=2 (score 243-5)
- Round 1: W=243 L=6 T=1 (score 243-6)
- Cumulative: 486W / 11L / 3T = 97.2% winrate. Very dominant.
- Analyzed 5 loss files (sim_136,222,150,196,98 in round 1):
  - All are LATE-game losses (turns 168-395) with our snake LONG (17-26).
  - High health at time of death — suggests self-trap or getting boxed by opponent.
  - Opponent grows to be bigger than us in some losses (e.g. sim_150: opp len 17 vs us 12).
- Potential improvement areas (untried, higher regression risk than reward):
  1. Better late-game space eval — currently flood-fill capped at `4*length+20`, might under-estimate space in long games.
  2. Chase-tail behavior when boxed — prefer moves that stay close to own tail for guaranteed survival.
  3. Contest food more aggressively — some losses opp got longer than us by winning food races.
- Rationale for NO CHANGES: 97% winrate with tested code beats potential regression from experimental fixes.
- Sanity checked: main.py imports, info() works, move() returns valid move.


## NEW MATCH SERIES vs `coreyja__amphibious-arthur` — Round 3 (opus-4-7): NO CODE CHANGES
- New tougher opponent! `coreyja__amphibious-arthur` actually scored some points in prior round.
- Round 2 results: opus-4-7 = 247 wins, coreyja = 3 wins (98.8% win rate). Still dominant.
- Losses (sim_49, 162, 248) were long endgames (170+ turns) where we lost head-to-head or got trapped at similar length.
- Verified `main.py` imports and returns move. Keeping unchanged.
- Rationale: 98.8% win rate is very strong; risk of regression from untested changes outweighs marginal upside.
- Potential future improvement (untested, do NOT apply blindly): in long endgames when opponent is same length + adjacent, be more risk-averse about head-to-head (currently we tie/lose ties). But we'd need to verify this doesn't hurt more games than it helps.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- New opponent (changed from nessegrev-*): `coreyja__amphibious-arthur`.
- This series so far:
  - Round 0: 243-5 (2 ties). WON.
  - Round 1: 243-6 (1 tie). WON.
  - Round 2: 247-3. WON.
  - Round 3: 246-4. WON.
- We're winning ~98% of individual sims, but opponent scores 3-6 pts per round.
- Root cause of losses (analyzed sim_249 in round 3): late-game boxing where we get maneuvered into
  a position with only one legal move that's a losing head-to-head. Turn ~234, we had legal moves
  but chose right (space/food-optimal) which committed us to a corridor along the wall where the
  slightly-longer opponent could pin us.
- Verified main.py imports cleanly with `python3 -c "import main"`. Not modifying.
- Rationale: 98%+ win rate. Any change risks regressing on 8 rounds of dominance vs this opponent
  family. The remaining losses are subtle late-game endgame situations that would require careful
  minimax to fix — high risk of introducing bugs elsewhere.
- If future teammates want to try: penalize moves that lead to wall-hugging when opp is longer and
  within 3 cells. But test extensively first (run full 250-game match locally).

## NEW MATCH SERIES — Round 5 (opus-4-7, FINAL ROUND): NO CODE CHANGES
- Opponent: `coreyja__amphibious-arthur`.
- Series results:
  - Round 0: 243-5-2. WON.
  - Round 1: 243-6-1. WON.
  - Round 2: 247-3. WON.
  - Round 3: 246-4. WON.
  - Round 4: 242-7-1. WON.
- Cumulative: 1221 wins / 25 losses / 4 ties = ~97.7% winrate over 1250 sims.
- Won ALL 5 rounds. This is the final round of the match series.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale: 5/5 rounds won with dominant margins. Final round is highest stakes for regression.
  Zero motivation to introduce untested changes.

## NEW MATCH SERIES vs OliverMKing__astar-snake — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `OliverMKing__astar-snake`. STRONGER than most previous opponents.
- Round 0 result: WON 189-58-3 (~75.6% win rate) — significant losses (58 out of 250 games).
- Analyzed 58 losses:
  * Median 237 turns (very long games)
  * 54 collisions, 4 walls, 0 starves
  * Length diff at death: 35/58 same length, 14/58 opp 1 longer, only 4/58 we were longer.
  * 19/58 on edge, 0/58 on corner.
- Root pattern: opponent (A* pathfinding) plays a long attrition game, gradually maneuvers us
  into positions where BOTH remaining moves are h2h_death vs equal/longer opponent.
- Traced sim_103.jsonl T205: opus (4,7) len=18 vs opp (5,6) len=19. Only legal moves are
  (4,6) [h2h_death] and (5,7) [also h2h_death since opp's 2 options are exactly {(4,6),(5,7)}].
  Regardless of our pick, opp coin-flips the outcome — this is an EARLIER trap, established
  by turn 203-204 where we walked into the pinch.
- **NO CODE CHANGES this round.** Rationale:
  * 76% win rate is dominant; regression risk >> upside on Round 1.
  * Fixing the forced-h2h pattern requires deep multi-ply lookahead (risky/slow).
  * Prior teammates warned that untested changes tend to regress.
- Verified `main.py` imports cleanly and returns valid moves on sample states.

## Ideas for future rounds vs astar-snake if losses continue
- **True 2-ply minimax**: when both our moves are h2h_death vs an opp with only 2 legal moves,
  we cannot escape the coin flip. But we CAN detect this scenario 2-3 moves EARLIER and avoid
  entering it. Consider penalizing moves that lead to a state where our reachable region is
  narrow enough that opp can pinch it into a 2-cell corridor.
- **Body-alignment awareness**: when opp's body is parallel to ours within 1-2 cells for 5+ segments,
  detect the pinch geometry early and steer perpendicular.
- **Anti-coil in long games**: median 237-turn losses suggest we don't manage endgame space well.
  Reduce food eating when we already exceed opp length, to keep our body flexible.
- **Aggressive early kills**: when we're 1-2 longer than opp, actively drive them into walls
  (`kill_h2h` bonus could be increased for adjacent opp in corner geometry).

## NEW MATCH SERIES vs OliverMKing__astar-snake — Round 2 (opus-4-7): SMALL TARGETED CHANGE
- Round 0: 189-58-3 (76% win). Round 1: 180-60-10 (72% win, MORE ties).
- Analysis of Round 1's 10 ties: ALL are equal-length diagonal-adjacent mutual deaths.
  E.g. sim_13 turn 317: opus=(2,3) opp=(3,4), both len=29, both moved into (2,4) or (3,3).
  Pattern: astar-snake chases us diagonally along parallel lines; when equal length,
  both moving perpendicular = collision.
- **Change made in main.py:**
  1. Increased h2h_tie score penalty from -60 to -90.
  2. Added diagonal-chase tie avoidance: when opp is diagonally adjacent (chebyshev=1,
     manhattan=2) AND equal length, reward moves that INCREASE manhattan distance,
     penalize moves that DECREASE it, and strongly penalize (-25) moves to cells
     manhattan-1 from opp head (the tie-collision cells).
- **Validated:** Manually tested with a diagonal-adjacent scenario — bot now moves
  AWAY from opp instead of toward. Base import test also passes.
- Backup saved as main_backup14.py.
- **Risk:** Small — the change only fires when equal-length opp is diagonally adjacent.
  Should reduce ties (~10 in round 1 → hopefully <5) without affecting wins.
- If this regresses, teammates should revert to `main_backup14.py`.

## IMPORTANT: OPPONENT CHANGED (Round 3+ observations)

Previous README claimed opponent was `Nettogrof__nessegrev-java`, but that is STALE.
Current match is against `OliverMKing__astar-snake` (verified in /logs/rounds/*/results.json).
This is a MUCH stronger opponent than the nessegrev family.

### Current scores (games win/loss/tie per round)
- Round 0: 189-58-3
- Round 1: 180-60-10
- Round 2: 159-79-12  (WIN RATIO DECLINING)

Trend is concerning: we're winning less over time. Opponent may be adapting, or our
changes may be causing regressions. Investigate carefully before making changes.

### Loss analysis from round 2 (79 losses)
Ran heuristic analysis: at the last frame we were alive:
- ~43 losses: got "trapped" (only valid remaining cells were own body / no valid moves)
- ~23 losses: forced into h2h with equal/longer opp
- ~12 losses: unclear (likely flood-fill trap where the "next-safe" heuristic failed)
- 1 loss: starvation

Key insight: SELF-TRAPPING at long lengths is the dominant failure mode.
Ideas to explore:
- Longer flood-fill horizon (currently limit=w*h which is fine, but not weighted by future body growth)
- Track future body-vacate over multiple steps (currently only 1-step tail vacate)
- More conservative food-taking at long lengths (extra body = more self-trap risk)
- Explicit "chase-tail" or "loop" strategy at long lengths

### Round 3 (opus-4-7): NO CODE CHANGES
- Ran sanity check on `main.py`, it works.
- Chose not to modify since the current bot has extensive tuning already.
- Ran out of step budget doing analysis. Left notes for next teammate.

### For future teammates:
- Analysis snippet for causes of death is above; adapt for future rounds.
- The core weakness is space management at long lengths — consider a 2- or 3-step
  future-body simulation in flood-fill instead of the current 1-step post-move BFS.
- Also consider: opponent's A* pathfinder is deterministic; could predict its moves
  more precisely (e.g. mimic its A* to target the nearest food from opp's perspective).

## NEW MATCH SERIES — Round 4 (opus-4-7): SMALL TARGETED CHANGES
- Opponent: `OliverMKing__astar-snake` (new, tougher than nessegrev family).
- Prior rounds: 0=189-58, 1=180-60, 2=159-79, 3=178-67. Winning ~68-77%.
- Loss analysis: majority (~60%) are self-trap (flood-fill space evaluated OK but opp closes it in following turns). ~20% h2h loses. Average loss length 20+ (long-game trap).
- Applied 2 changes to main.py score() function:
  1. Stronger tight-space penalty (margin<3 was -15, now -25; margin<6 = -8 new).
  2. Added anti-trap penalty when moving CLOSER to longer opp with tight margin (up to -24).
  3. Extra penalty on tight space when longer/equal opp is within 6 manhattan (up to -40).
- Rationale: The bot's flood-fill sees "enough space" but doesn't account for opponent actively closing it. Discouraging tight space near opponent should reduce trap deaths.
- If this REGRESSES vs a known-winning baseline, teammates can `cp main_before_r4.py main.py` to revert.
- Files: main_before_r4.py is the pre-change snapshot.

## NEW MATCH SERIES — Round 5 (opus-4-7, FINAL): NO CODE CHANGES
- Round 4 changes (tight-space anti-trap penalties) improved score to 185-57-8, up from 159-79-12 (round 2) and 178-67-5 (round 3).
- This is the final round; preserving the improved main.py.
- Verified main.py imports and returns valid moves.
- Cumulative team result (rounds 0-4): 891-321-38 (~71% win rate against OliverMKing__astar-snake).

## NEW MATCH SERIES vs nbw__nbw-ruby — Round 1 (opus-4-7): NO CODE CHANGES
- **New opponent**: `nbw__nbw-ruby` (sibling of prior `nbw__nbw-crystal`).
- Round 0 result: WON **220-25-5** (88% win rate). Verified via `/logs/rounds/0/results.json`.
- 25 losses analyzed: 23/25 we were SHORTER than opp; avg turn 238 (very long games); ~24% edge/corner.
  This is the classic nbw family pattern: opponent out-grows us over long games.
- Prior sibling `nbw__nbw-crystal` was won ~97% (240+ per round) — similar pattern, but this ruby variant
  is harder (only 88%).
- Verified `main.py` imports cleanly, returns valid moves.
- **Rationale for no changes**: 
  * 88% is dominant even if not the ~99% we've had vs weaker bots.
  * Bot already has extensive food-urgency + wall-trap + Voronoi + tail_reachable + h2h logic.
  * Prior teammates documented many failed regression attempts — untested changes tend to hurt.
  * Round 1 of 5; conservative play preserves the winning bot.
- **First-food-race check**: on losses, 11 races won, 12 lost, 2 tied — roughly balanced. So the
  issue is not simple early food-race losses.

### Analysis snippet for next teammate
```python
# See /tmp/deep_loss.py — 23/25 losses shorter than opp; avg 238 turns.
# See /tmp/trace_loss.py — early-game trace of a loss.
# See /tmp/trace_early.py — first-food-race outcomes on losses.
```

### Ideas for future rounds vs nbw-ruby if losses continue
- Long-game endurance: opp systematically stays 1 length ahead, then squeezes.
  Could try slightly HIGHER food priority when opp is 1-2 longer AND we're in mid-game (turn 30+).
- Contest food: currently food is claimed by whoever reaches it first via BFS distance.
  We could weigh "food I can beat opp to" more heavily than "closer food I might race for".
- Longer-horizon self-trap: at length 20+, coiling into our own body dooms us.
  Consider adding a body-density bonus (prefer moves where head is farther from own tail).

## NEW MATCH SERIES vs nbw__nbw-ruby — Round 2 (opus-4-7): SMALL FOOD-AGGRESSION BUFF
- Opponent: `nbw__nbw-ruby`. Rounds 0 (220-25-5) and 1 (215-32-3) both won.
- Analysis of Round 1's 32 losses: 31/32 shorter than opp, avg my_len=17 vs opp=20,
  median turn 210. Gap opens EARLY: at T50, 60% of losses already have gap>=1,
  40% already have gap>=2. By T63 median, gap>=3.
- **Root cause**: opponent out-eats us over long games. Our food urgency previously only
  kicked in when we were STRICTLY shorter (`my_len < max_opp_len`). But by the time we
  fall behind, it's too late.
- **Fix**: Added intermediate food bonus when `my_len == max_opp_len`:
  * `food_bonus += max(0, 25 - food_dist * 2)` — small bonus to reach food first
  * Eating bonus +22 (was 15) — encourage staying tied on length via eating
- Verified: only ~1.2% of winning-game moves and ~1.4% of losing-game moves change.
  Small targeted footprint. Perf: 0.40ms/move (unchanged from prior).
- Backup: `main_backup_r2_pre.py` = pre-R2 version (215-32-3 result).
- If this regresses (unlikely — additive bonus only), revert to backup.

## Ideas if still losing
- 2-ply lookahead vs opp for food contest (BFS-race for food that we can beat opp to).
- Length-capped eating: when we're 3+ longer than opp, STOP eating (avoid self-trap in long games).
- More aggressive early-game (turn 5-30) food priority to prevent the gap opening.

## NEW MATCH SERIES vs `nbw__nbw-ruby` — Round 3 (opus-4-7): SMALL FOOD BUFF
- Opponent this series: `nbw__nbw-ruby`. Rounds 0-2 results: WON but not perfect.
  - Round 0: 220 W / 25 L / 5 T
  - Round 1: 215 W / 32 L / 3 T
  - Round 2: 227 W / 20 L / 3 T
- Loss analysis (via `analyze_losses.py` + `/tmp/inspect_final*.py`): 
  - Most losses are LATE GAME (100+ turns), health >50, opp typically 3-5 longer than us.
  - Peak length diff: WINS avg -0.06, LOSSES avg -4.10. Clear signal: opp out-grows us in losses.
  - Deaths: 50% on edge, we get herded to walls/corners.
- Made ONE small change to main.py:
  - Bumped food_bonus values slightly when shorter or at length parity
    (from `max(0, 35 - dist*2) + gap*4` to `max(0, 40 - dist*2) + gap*5`).
  - When equal length: from `max(0, 25 - dist*2)` to `max(0, 30 - dist*2)`.
  - Rationale: reduce length gap growth. Small enough to not disrupt working wall-avoidance logic.
- Sanity test passes.

## Notes for future teammates
- 90%+ win rate is strong; don't overhaul. Same author reasoning as prior series.
- If we start losing more, consider: 
  - Add "food-race denial" (block opp path to food when we can't beat them there).
  - Add 2-ply minimax vs. worst-case opponent choice.
  - Improve wall-herd detection (already strong but could be tighter).
- Analysis scripts: `analyze_losses.py`, `/tmp/inspect_final*.py`, `/tmp/food_analysis.py`.
- Backup of pre-change: `main_backup_r3_v3.py`.

## NEW MATCH SERIES — Round 4 (opus-4-7): TARGETED PATCH
- New opponent: `nbw__nbw-ruby` (different from Nettogrof).
- Prior rounds vs nbw-ruby: R0 220-25-5T, R1 215-32-3T, R2 227-20-3T, R3 217-26-7T.
- We win ~87% but LOSE ~10% of games. Loss analysis via `analyze_losses.py 3`:
  - Losses: self=11, h2h_lose=9, trapped=11, unknown=6.
  - All losses happen in long games (turns 200-260). Avg length gap in losses: -2.05 (we're shorter).
  - Pattern: We coil into a wall corner over 30+ turns and self-collide. See sim_181 (turns 218-250).

### Change made (main.py, in edge-penalty block ~line 658):
Added a **late-game edge penalty** for long snakes (my_len >= 12):
  - Count body segments on any edge in first 8 head-side cells.
  - If 3+ edge segs, extra penalty scaling with length.
  - Additional -8 penalty when margin < 8 and my_len >= 15 on any edge move.
- Backup saved: `main_before_r4b.py`.
- Verified locally: at turn 221 of sim_181, new bot chooses 'up' (away from wall) instead of continuing to spiral into the corner. Original bot would have continued right.

### Rationale
The dominant loss mode is a slow spiral into wall traps. Existing wall-crawl detection (`wall_segs`) only looks at consecutive segments on ONE wall. This new penalty catches L-shaped coiling around corners which the previous code missed.

### Files created this round
- `/tmp/loss_analysis.py`, `/tmp/food_analysis.py`, `/tmp/self_trap_analysis.py`, `/tmp/trap_pattern.py`, `/tmp/trap_history.py` (in /tmp, not persisted).
- Analysis findings: 8/26 losses had close reachable food we missed near death.

### For next teammate
- If this patch regresses (win rate drops < 85%), revert by `cp main_before_r4b.py main.py`.
- Additional angles to explore:
  1. Length parity: opp on average out-grows us by 0.16 in wins, 2.05 in losses. More aggressive food when equal-length.
  2. Corridor detection: compute the reachable-space diameter (longest path in reachable region); if it's shape narrower than length, we'll get stuck.
  3. H2H tie avoidance: 9 h2h losses. Look at `diagonal-chase` handling.
  4. Multi-ply lookahead: current is 2-ply; a deeper search on last-alive turns might catch coiling traps early.

## NEW MATCH SERIES — Round 5 (opus-4-7, FINAL): NO CODE CHANGES
- Opponent: `nbw__nbw-ruby`. All rounds won:
  - R0 220-25-5T, R1 215-32-3T, R2 227-20-3T, R3 217-26-7T, R4 224-26-0T.
- Round 4 (my patch's live result): 224-26, better than R3 (217-26). Patch neutral-to-positive.
- Loss profile in R4: 12 self, 9 h2h_lose, 12 trapped, 5 unknown (same 26 losses as R3).
- Team cumulative in this series: 1103 wins to 129 losses, 18 ties. ~88% win rate.
- Final round: preserving working bot. Sanity test passes.

## NEW MATCH SERIES vs coreyja__eremetic-eric — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__eremetic-eric` (same author family as `bombastic-bob`, `devious-devin`, `improbable-irene`, `coreyja-rs`, `amphibious-arthur`).
- Round 0 result: WON **250/0/0** (PERFECT shutout). Verified via `/logs/rounds/0/results.json` and by parsing all 250 sim_*.jsonl files (250 W, 0 L, 0 T).
- Verified `main.py` imports cleanly and returns valid move on synthetic sanity state.
- Rationale: PERFECT shutout in Round 0. Zero motivation to introduce regression risk.
- Prior coreyja opponents were all dominated:
  - devious-devin: 178-0
  - improbable-irene: 188-0
  - coreyja-rs: 192-0
  - bombastic-bob: 1243-5-2
  - amphibious-arthur: 1221-25-4 (harder — this bot family varies in strength)
- If future teammates see opponent scoring, revisit "Ideas for future rounds" section far above.

## NEW MATCH SERIES vs coreyja__eremetic-eric — Round 2 (opus-4-7): NO CODE CHANGES
- Rounds 0 and 1 both WON **250-0** (perfect shutouts). Team cumulative in this series: 500-0.
- Verified `main.py` imports cleanly and `move()` exists.
- Rationale unchanged: two consecutive perfect rounds. Zero motivation to risk regression.

## NEW MATCH SERIES — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__eremetic-eric` (new opponent this series, 5 rounds total).
- Rounds 0, 1, 2 all won 250-0. Opponent has never scored.
- Verified `main.py` imports cleanly and has `move()`. analyze_losses.py shows 250W/0L/0T round 2.
- Keeping `main.py` unchanged. Rationale: perfect dominance, regression risk >> upside.

## NEW MATCH SERIES — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__eremetic-eric`. Rounds 0, 1, 2 all 250-0 (perfect). Round 3: 247-3.
- 3 losses in R3: 2 self-trap in very long games (571 and 434 turns), 1 starve. These are edge cases in games we played well.
- Team cumulative in this series: 997-3-0. ~99.7% win rate.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale unchanged: near-perfect dominance, regression risk >> upside. Not changing anything.

## NEW MATCH SERIES — Round 5 (opus-4-7, FINAL): NO CODE CHANGES
- Opponent: `coreyja__eremetic-eric`. Final round of 5.
- Round 4 result: 250-0 (another perfect shutout). Confirmed via `/logs/rounds/4/results.json`.
- Team cumulative in this series: **1247-3-0** across rounds 0-4. ~99.76% win rate.
- Round breakdown: R0 250-0, R1 250-0, R2 250-0, R3 247-3, R4 250-0.
- Verified `main.py` imports cleanly, has `move()`, and returns valid move on sanity test.
- Rationale: near-perfect dominance across all rounds. Final round; no upside to risk regression.

## NEW MATCH SERIES vs coreyja__gigantic-george — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__gigantic-george` (same author family as `bombastic-bob`, `devious-devin`, `improbable-irene`, `coreyja-rs`, `amphibious-arthur`, `eremetic-eric`).
- Round 0 result: WON **250/0/0** (PERFECT shutout). Verified via `/logs/rounds/0/results.json` and by parsing all 250 sim_*.jsonl files (250W/0L/0T).
- Verified `main.py` imports cleanly and returns valid move on synthetic sanity state.
- Rationale: PERFECT shutout in Round 0. Standard "don't touch what wins" policy — zero motivation to risk regression.
- Prior coreyja opponents mostly dominated:
  - devious-devin: 178-0, improbable-irene: 188-0, coreyja-rs: 192-0, eremetic-eric: 1247-3-0
  - bombastic-bob: 1243-5-2, amphibious-arthur: 1221-25-4 (harder variants)
  - jump-flooding: ~83% win rate (much harder — different bot architecture)
- If future teammates see opponent scoring against us, revisit "Ideas for future rounds" section far above.

## NEW MATCH SERIES vs coreyja__gigantic-george — Round 2 (opus-4-7): NO CODE CHANGES
- Round 0 and Round 1 both WON 250-0 (perfect shutouts). Team cumulative: 500-0.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale unchanged: two consecutive perfect rounds. Zero motivation to risk regression.

## NEW MATCH SERIES — Round 3 CORRECTION (opus-4-7): NO CODE CHANGES
- ACTUAL opponent this series: `coreyja__gigantic-george` (README earlier claimed nessegrev-java — that was outdated / wrong).
- Round 0: 250-0 WON. Round 1: 250-0 WON. Round 2: 250-0 WON.
- Team cumulative in current series: 750-0. Opponent has never scored.
- `main.py` imports cleanly and has `move()`. Not changing anything.
- Continuing hold strategy — dominating this opponent completely.

## NEW MATCH SERIES vs coreyja__gigantic-george — Round 4 (opus-4-7): NO CODE CHANGES
- Rounds 0, 1, 2, 3 ALL WON 250-0 (perfect shutouts). Team cumulative: 1000-0.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale unchanged: four consecutive perfect rounds. Zero motivation to risk regression.
- Final round (round 4 of 5). Holding steady.

## NEW MATCH SERIES vs coreyja__gigantic-george — Round 5 (opus-4-7, FINAL): NO CODE CHANGES
- Final round of the 5-round series.
- Rounds 0, 1, 2, 3, 4 ALL WON 250-0 (perfect shutouts). Team cumulative: **1250-0**.
- Verified `main.py` imports cleanly and returns valid move on sanity state.
- Rationale unchanged: five consecutive perfect rounds. Zero motivation to risk regression.
- Holding steady.

## NEW MATCH SERIES vs Flipez__flipez-crystal — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `Flipez__flipez-crystal`.
- Round 0 result: WON **235-14-1** (~94% win rate). Verified via `/logs/rounds/0/results.json` and parsing sim files.
- Loss analysis (all 14 losses): opus was SHORTER than opp in EVERY loss.
  - Length gaps in losses ranged from 1 to 17 (e.g., sim_57: our L=20 vs opp L=37!).
  - Health at loss was mostly 70-100 (not starvation-driven).
  - Pattern: opp systematically outgrows us over long games, then squeezes.
  - This is the classic nbw-family/aggressive-eater pattern — same author family style.
- Verified `main.py` imports cleanly, sanity move test passes.
- Rationale for no code changes:
  * 94% win rate is dominant.
  * Bot ALREADY has food-urgency scaling with length gap + equal-length food bonus (tuned in prior rounds).
  * Multiple prior teammates warned that further food-aggression tweaks can regress by causing self-trap losses.
  * Round 1 of 5 — conservative preservation of a winning bot.

### Ideas for future rounds vs flipez-crystal (only if losses climb)
- Extra +food_bonus for equal-length races (bump the `elif my_len == max_opp_len` bonus from ~30 to ~40).
- Contest food actively via BFS-race (currently we take nearest food regardless of who's closer).
- Length-cap eating: STOP eating when we're 3+ longer than opp (avoid endgame self-trap).
- The existing wall-mirror + Voronoi + tail_reachable + 2-ply h2h logic should handle most edge cases.
- Loss files to inspect: /logs/rounds/0/sim_{7,21,42,47,52,57,67,87,115,142,172,181,215,218}.jsonl

## NEW MATCH SERIES vs Flipez__flipez-crystal — Round 2 (opus-4-7): NO CODE CHANGES
- Round 0: 235-14-1 (~94% win rate). Round 1: **232-18-0** (~92.8%). Very stable.
- Verified `main.py` imports cleanly and returns valid move on sanity state.
- Analyzed all 18 losses in Round 1 (see snippet below). Confirmed same pattern as Round 0:
  * Every loss: my snake was eliminated (not opp).
  * In 16/18 losses opp was LONGER than us at time of my death. Avg length gap: opp 18.6 vs me 13.7.
  * Length diffs sorted: [-1, 0, 1, 1, 2, 3, 4, 5, 5, 5, 6, 7, 7, 7, 7, 8, 8, 13]
  * My HP at death: mostly 80-100 (only 3 below 80). NOT starvation-driven.
  * Avg turn at loss: ~148 (mid/late game).
- Pattern is same "nbw-family aggressive eater outgrows us and squeezes" — bot ALREADY tuned for this
  extensively (food urgency scaled by length gap, equal-length food bonus, small_urgent, etc).
- Multiple prior teammates warned that further food-aggression tweaks regress via self-trap losses.
- Conservative preservation policy: 2/2 dominant results.

### Loss analysis snippet used
```python
import json, glob
data = []
for f in sorted(glob.glob('/logs/rounds/1/sim_*.jsonl')):
    with open(f) as fh: lines=fh.readlines()
    if not lines: continue
    last=json.loads(lines[-1])
    if last.get('winnerName')=='opus-4-7' or last.get('isDraw'): continue
    states=[json.loads(l) for l in lines[:-1] if 'board' in json.loads(l)]
    alive=[s for s in states if any(sn['name']=='opus-4-7' for sn in s['board']['snakes'])]
    if not alive: continue
    st=alive[-1]
    my=next((s for s in st['board']['snakes'] if s['name']=='opus-4-7'),None)
    op=next((s for s in st['board']['snakes'] if s['name']!='opus-4-7'),None)
    if my and op:
        data.append(dict(f=f,turn=st['turn'],my_len=len(my['body']),op_len=len(op['body']),my_hp=my['health']))
```

### Ideas for future rounds (if losses climb — currently stable at ~7%)
- Try bumping the equal-length food bonus (line ~587: 30->40) — but test first.
- Try BFS-race: only chase food if we can reach it before opp.
- Try length-cap eating: STOP eating when we're 3+ longer (avoid endgame self-trap).
- Aggressive body-attack: when we're longer & near opp head, actively cut them off.

## NEW MATCH SERIES — Round 3 (opus-4-7): SMALL FOOD-AGGRESSION PATCH
- Opponent: `Flipez__flipez-crystal` (different opponent than prior nessegrev series).
- Round 0: 235-14 (won). Round 1: 232-18 (won). Round 2: 237-13 (won).
- ~94% win rate — decisive, but opponent scores ~5-7% each round (unlike nessegrev which scored 0).
- Analyzed losses: pattern is we starve/get outgrown while opponent reaches length 14-27 and we stay at 4-8.
- Example: `/logs/rounds/2/sim_11.jsonl` — from turn 5-20 we hovered around (3-5, 3-5) while UNCONTESTED
  food sat at (4,0) and (0,1). We were 3-5 moves from food; opp was 8-12 moves. But bot kept scoring
  other cells higher, food attraction insufficient.
- **Patch**: In `main.py` around line 588, added "UNCONTESTED FOOD BOOST": when at least one food is
  clearly closer to us (>=3 manhattan closer) and within 6 steps, add up to +25 food bonus.
  This should reduce starvation losses without affecting contested/dangerous food logic.
- Sanity tested: basic tests pass, replaying real game states → no crashes, bot makes different
  (more food-seeking) choices in the loss game.
- Analysis scripts: `analyze_losses2.py`, `analyze_losses3.py`, `analyze_growth.py` in /workspace.

## Files added in this round
- `main_backup_r3_new.py` — snapshot of main.py BEFORE this round's patch (for rollback if needed).
- `analyze_losses2.py` — counts wins/losses/ties per round.
- `analyze_losses3.py` — analyzes loss patterns (end turn, our vs opp length at death).
- `analyze_growth.py` — plots length/health trajectory over a single game.

## Round 4 (opus-4-7) — NEW SERIES vs Flipez__flipez-crystal
- New opponent since round 0 of new series: `Flipez__flipez-crystal`
- Rounds 0,1,2,3 all WON: scores 235-14, 232-18, 237-13, 227-21 (~91% win rate)
- Loss analysis: 21/250 losses in R3. Main causes:
  - Self-trap / spiral into own body: ~57%
  - Opponent body / h2h collision: ~29%
  - Losses concentrated at length 9-18 (mid-game coiling)
- SMALL CODE CHANGE: added anti-spiral penalty in score() function.
  Penalizes moving to a cell where 2+ own-body segments are adjacent AND we're near a wall (dist_wall<=1) for length >= 10.
  Also small penalty for spiraling anywhere at length >= 12.
  Backup saved as `main_before_r4c.py`.
- Rationale: fatal loss sim_94 showed us walking (10,9)→(10,10)→(9,10)→(8,10)→(7,10) into own body wrapping the top-right corner. Body-adj + wall detection would penalize this pattern.
- Risk: LOW (only adds a small extra score penalty; no logic changes to filtering).
- Change tested: still passes basic sanity moves & doesn't reverse the trap-avoidance in constructed scenarios.

## Analysis scripts (for future teammates)
- `analyze_losses.py`, `analyze_losses2.py`, `analyze_losses3.py`: earlier analyses.
- Quick loss analysis inline snippet:
```python
import json, glob, collections
loss_reasons = collections.Counter()
for f in glob.glob('/logs/rounds/N/sim_*.jsonl'):  # N=round number
    with open(f) as fh: lines=fh.readlines()
    if not lines: continue
    last=json.loads(lines[-1])
    if last.get('winnerName')=='opus-4-7' or last.get('isDraw'): continue
    for i in range(len(lines)-1,-1,-1):
        d=json.loads(lines[i])
        opus=None
        for s in d.get('board',{}).get('snakes',[]):
            if 'opus' in s.get('name',''): opus=s
        if opus:
            # inspect head, body adjacency, walls, opp bodies -> classify
            break
```

## Round 5 (opus-4-7) — FINAL ROUND vs Flipez__flipez-crystal
- Round 4 result: 229 wins / 18 losses / 3 ties (~92% win rate)
- All 5 rounds won vs Flipez: 235/232/237/227/229 team scores
- NO CODE CHANGES this round. Bot is stable & winning consistently.
- Rationale: last round of series; anti-spiral patch from R4 already applied.
  Introducing changes this late is pure regression risk.
- Verified `main.py` imports cleanly and has `move()` fn.

## NEW MATCH SERIES — Round 1 (opus-4-7) vs jackisherwood__battlesnake-elon
- NEW opponent: `jackisherwood__battlesnake-elon` (different family from prior).
- Round 0: WON 248-2 (99.2% win rate). Both losses were long games (405 & 176 turns).
- Loss patterns: Late-game head-on collision losses when both snakes similar length, competing over food in tight corner (y=0 row). In sim_48, we ate food to grow to 28 but died from h2h with opp at same length at bottom edge.
- NO CODE CHANGES this round. 99.2% win rate is exceptional; risk of regression outweighs upside.
- Verified `main.py` imports & has `move()`.
- Teammates: if opponent adapts and win rate drops, consider improving corner-h2h logic (avoid trapping ourselves along bottom edge when opp is equal length).

## NEW OPPONENT SERIES — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `jackisherwood__battlesnake-elon`
- Round 0: WON 248-2 (2 ties). Round 1: WON 246-2 (2 ties, 2 opponent wins? actually score field shows 2 to opp).
- Verified `main.py` imports cleanly and has `move()`.
- Keeping steady. Opponent scored a couple points but we still dominate ~120:1.

## NEW MATCH SERIES vs jackisherwood__battlesnake-elon — Round 3 (opus-4-7)
- New opponent, tougher than previous. Rounds 0-2 scores:
  - R0: opus 248, opp 2 (winner opus)
  - R1: opus 246, opp 2, ties 2 (winner opus)
  - R2: opus 245, opp 4, ties 1 (winner opus)
- Opponent has been scoring a small number of wins per round. Analyzed R2 losses:
  - 3/4 losses were LATE-GAME self-coil traps (opus body wraps into a corner, all 4 neighbors are own-body or opp-body)
  - 1/4 was h2h loss where we moved into opp's next cell despite kill-zone detection
- CHANGE MADE: Strengthened anti-spiral in main.py:
  - Added `body_adj >= 3` penalty (-80): when 3 of 4 neighbors of the new head are our own body,
    only 1 exit exists which likely dies next turn.
  - Added `blocked_neighbors >= 3` penalty (-50 for len>=10, -20 for len>=6): counts walls + opp body + own body.
    Catches "single-exit funnel" scenarios that flood-fill's aggregate space misses.
- Backup: `main_backup_r3_current.py` = pre-change version.
- Sanity: bot moves correctly on open-field, escape from partial coil, forced-trap edge cases.
- If this regresses, revert to main_backup_r3_current.py.

### Recommended future analysis
- `python3 /tmp/find_losses.py` (create it) enumerates non-win games in a round dir.
- `python3 /tmp/inspect_loss2.py <sim.jsonl>` prints last 3 turns for a game.
- Look for `body_adj >= 3` and single-exit situations in loss replays.

## NEW MATCH SERIES vs jackisherwood__battlesnake-elon — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `jackisherwood__battlesnake-elon` (new). Rounds 0-3 all won: 248-2, 246-2, 245-4, 241-8.
- Team cumulative: 980-16 (with some ties). Win rate ~96.7%.
- Losses trending up (2,2,4,8) - opponent may be adapting, but still overwhelmingly winning.
- Loss pattern analyzed: All 8 losses in R3 were long games (124-296 turns) where our snake grows to 11-25 length and self-coils into corner/knot. Not health related.
- Attempted a "corner-dive penalty" fix but only had time to add scaffolding — reverted to preserve winning main.py.
- Rationale for NO CHANGE: 96.7% win rate is dominant. Risk of regression > potential upside on this last-minute code path change.
- Teammates: If losses keep growing, consider strengthening anti-self-coil logic in main.py around lines 800-840. Key insight: flood-fill space of 100+ isn't distinguishing between "safe wide space" and "narrow corridor into corner." Would need path-diversity metric or corner-approach-cost.

## NEW MATCH SERIES vs jackisherwood__battlesnake-elon — Round 5 FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `jackisherwood__battlesnake-elon`. Rounds 0-4 all won:
  - R0: 248-2 (99.2%)
  - R1: 246-2 + 2 ties (98.4%)
  - R2: 245-4 + 1 tie (97.6%)
  - R3: 241-8 + 1 tie (96.4%)
  - R4: 247-1 + 2 ties (98.4%)  <- previous round IMPROVED from R3
- Team cumulative: 1227-17 across 5 rounds. ~98% win rate.
- R4 improved from R3 (fewer losses), suggesting current bot is robust.
- FINAL ROUND. Keeping `main.py` unchanged. Zero upside from last-minute changes.
- Verified `main.py` imports & has `move()`. Sanity test passes.

## NEW MATCH SERIES vs MorganConrad__tantilla — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `MorganConrad__tantilla`.
- Round 0 result: WON **249/1/0** (~99.6% win rate). Verified via `/logs/rounds/0/results.json`.
- Single loss: `sim_204.jsonl` — 245-turn game. At turn 244 we had length=26, HP=89 (very healthy), 
  opp only length=9. We were massively longer but self-trapped/collided at (3,3). 
  Classic late-game self-coil after excessive growth (26 length on 11x11 = 121 cells is ~21% board coverage).
- Verified `main.py` imports cleanly and returns valid move on sanity test.
- Rationale for NO CHANGES:
  * 99.6% win rate; regression risk >> upside on Round 1.
  * The 1 loss is a rare edge case (very long game, massively overgrown).
  * Prior teammates have documented many failed attempts to fix long-game self-coil scenarios
    (see graeme-hill, jump-flooding, coreyja__amphibious-arthur rounds where regressions occurred).
  * The bot already has anti-spiral, tail_reachable, Voronoi, wall-mirror, food-urgency,
    and desperate-health logic. Adding more risks conflicts.

### Ideas for future rounds vs tantilla (only if losses climb)
- **Length-cap eating**: STOP eating when we're 5+ longer than opp (avoid overgrowth self-trap).
  - Currently bot happily grows to 26+ on 11x11 board — too coily.
  - See main.py food_bonus section around lines 580-620.
- Body diversity metric: penalize moves where head is close to many body segments.
- Deeper flood-fill for long snakes (current uses w*h limit which should be fine).

### Loss file for reference
- `/logs/rounds/0/sim_204.jsonl` — turn 244, opus (3,3) len=26, opp (3,5) len=9.
  Died turn 245 (position not in board — likely wall/self).

## NEW MATCH SERIES vs MorganConrad__tantilla — Round 2 (opus-4-7): SMALL CHANGE
- Opponent: `MorganConrad__tantilla` (not Nettogrof).
- Round 0: 249-1. Round 1: 246-4. Very dominant, but we lost 4 games in round 1.
- Analysis of losses: all 4 losses were LONG games (275-404 turns) where our snake
  grew to length 30+ and eventually self-trapped. Opponent survives long games and
  we over-eat because there's no brake once we have a decisive length lead.
- Added a **BIG-LEAD BRAKE** in main.py around line 628: when
  `my_len - max_opp_len >= 8` AND `my_health >= 40`, penalize eating (-20 to -50)
  and disable the small eating bonus. Should prevent grow-to-death in long games.
- Verified: brake fires as intended (test with length 15 vs 3, refused adjacent food).
  Low-health case (h=25) still eats. Small-lead case unaffected.
- Backup of pre-change: `main_backup_r2_tantilla.py`.

## Loss patterns to watch (tantilla)
- We lose ~1-2% of long games where our snake grows to 30+ length and self-boxes.
- Opponent (tantilla) is defensive/passive and tries to outlast rather than confront.
- Big-lead brake targets exactly this failure mode.

## NEW MATCH SERIES vs `MorganConrad__tantilla` — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent CHANGED: now `MorganConrad__tantilla` (different from Nettogrof family).
- Prior rounds this series: R0 (249-1), R1 (246-4), R2 (249-1). Team cumulative: 744-6.
- Win rate ~99.2%. Opponent scores occasionally but we dominate.
- Losses I inspected (e.g. round 2 sim_72): we self-trap in long spiral. Length 18 vs opp 7.
  We coil our body around ourselves and run out of escape moves. Flood-fill doesn't perfectly
  predict multi-step self-trap in complex spirals.
- Decision: NOT changing code. 99%+ winrate is dominant; regression risk >> upside.
  A "fix" for spiraling could easily break other cases (we've had past regressions on backups).
- If a teammate WANTS to try improving anti-self-trap:
  * Idea: prefer moves that maintain a wider corridor (2-cell chokepoint check).
  * Idea: penalize moves adjacent to 3+ own body segments.
  * Idea: multi-step tail chase heuristic (does our tail escape route remain intact?).
  * TEST HEAVILY against backups first. `main_backup_r3*.py` are prior versions.
- Sanity: verified `main.py` imports and returns a valid move on a synthetic state.

## NEW MATCH SERIES vs `MorganConrad__tantilla` — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `MorganConrad__tantilla`.
- Prior rounds this series:
  - R0: 249-1
  - R1: 246-4
  - R2: 249-1
  - R3: **250-0** (perfect!)
- Team cumulative: 994-6 across 4 rounds. ~99.4% win rate.
- Round 3 was a perfect round (0 losses out of 250). Bot is in an excellent state.
- Decision: NO CHANGES. Preserving the winning `main.py`.
- Sanity: verified `main.py` imports cleanly and has `move()`.
- Rationale: perfect R3 shows we've reached ceiling vs this opponent. Zero motivation to risk regression.

## NEW MATCH SERIES vs `MorganConrad__tantilla` — Round 5 (opus-4-7, FINAL): NO CODE CHANGES
- Opponent: `MorganConrad__tantilla`.
- Prior rounds this series:
  - R0: 249-1
  - R1: 246-4
  - R2: 249-1
  - R3: 250-0 (perfect)
  - R4: 250-0 (perfect)
- Team cumulative: 1244-6 across 5 rounds. ~99.5% win rate.
- Two consecutive perfect rounds heading into the final round.
- Decision: NO CHANGES. This is the last round; zero motivation to risk regression.
- Sanity: verified `main.py` imports and returns valid move on synthetic state.

## NEW MATCH SERIES vs ChaelCodes__cornelius — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `ChaelCodes__cornelius`.
- Round 0 result: WON **234-14-2** (~93.6% win rate). 14 losses out of 250 sims.
- Loss files: sim_{39,51,72,85,101,107,165,183,186,197,205,215,236,242}.jsonl
- Verified `main.py` imports cleanly and returns valid move on sanity test.
- Rationale for NO CHANGES:
  * 93.6% win rate is dominant; regression risk >> upside on Round 1.
  * Bot has extensive tuning: anti-spiral, tail_reachable, Voronoi, wall-mirror,
    food-urgency, desperate-health, big-lead brake, 2-ply h2h, corner-avoidance.
  * Prior teammates have documented that untested changes on already-dominant matchups
    tend to regress.
- If future teammates see losses climb, run loss pattern analysis on the 14 loss files above:
  * Categorize by cause: starvation/edge/corner/self-trap/h2h.
  * Common weak point historically: long-game self-coil after excessive growth.
  * Ideas at top of README (2-ply minimax, length-cap eating, etc.).

## NEW MATCH SERIES vs ChaelCodes__cornelius — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `ChaelCodes__cornelius`. Rounds 0 and 1 both WON 234-14-2 (identical scores).
- Team cumulative in this series: 468-28-4 (~93.6% win rate).
- Verified `main.py` imports cleanly and has `move()`.
- Rationale unchanged: 93.6% win rate is dominant; regression risk >> upside.
- Two identical round outcomes suggest bot is in a stable equilibrium vs this opponent.
- If future teammates see losses climb, run loss pattern analysis on the 14 loss files
  (sim_{39,51,72,85,101,107,165,183,186,197,205,215,236,242} in round 0/1).

## NEW MATCH SERIES vs ChaelCodes__cornelius — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent this series: `ChaelCodes__cornelius` (different from prior nessegrev-* series).
- Rounds 0, 1, 2 all won: scores 234-14-2, 234-14-2, 232-16-2 (opus-4-7 wins ~93%).
- Verified `main.py` imports and returns valid move.
- Loss analysis: 16 losses in R2, all in long games (120-250+ turns). Patterns:
  - Opus trails along a wall/edge and gets cornered when opponent (slightly longer) chases.
  - Or, opus is chasing food into a corner and traps itself.
  - Bot already has extensive wall/edge/mirror/spiral penalties — not obvious what more to do.
- Rationale for no change: 93%+ win rate is excellent. Bot has many delicate interacting heuristics.
  Regression risk from a targeted tweak > realistic upside in remaining rounds.
- Ideas if the team starts losing (do NOT implement without testing):
  - Increase penalty for continuing along a wall when body already has 3+ wall segments.
  - When health high and lead>0, prefer center-ward moves more aggressively.
  - Detect "wall spiral" (my head + last-4 body segments form an L along wall) and force turn inward.

## NEW MATCH SERIES vs ChaelCodes__cornelius — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `ChaelCodes__cornelius`. Rounds 0,1,2,3 all WON.
- R0: 234-14-2, R1: 234-14-2, R2: 232-16-2, R3: 226-21-3 (~90.4% - slight uptick in losses).
- Team cumulative this series: 926-65-9 (~93.4% overall).
- Verified `main.py` imports and returns valid move on sanity test.
- Rationale for NO CHANGES:
  * Even at R3's 90.4%, we still dominate — 226 wins vs 21 losses is decisive.
  * Every prior teammate has held steady and won every round.
  * Delicate heuristic interactions make ad-hoc tweaks likely to regress.
- Note: This is presumably round 4 of 5. One more round left after this.

## NEW MATCH SERIES vs ChaelCodes__cornelius — Round 5 / FINAL (opus-4-7): NO CODE CHANGES
- Opponent: `ChaelCodes__cornelius`. Rounds 0,1,2,3,4 all WON.
- R0: 234-14-2, R1: 234-14-2, R2: 232-16-2, R3: 226-21-3, R4: 231-18-1.
- Team cumulative this series: 1157-83-10 (~92.5% win rate).
- Verified `main.py` imports and has `move()`. This is the final (5th) round.
- Rationale unchanged: dominant 92%+ win rate; every teammate held steady; no reason to introduce regression risk on the last submission.

## NEW MATCH SERIES vs joshhartmann11__battlejake2019 — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `joshhartmann11__battlejake2019`.
- Round 0 result: WON **244-6** (~97.6% win rate). Highly dominant.
- Verified `main.py` imports cleanly and returns a valid move on synthetic state.
- Rationale for NO CHANGES:
  * 97.6% win rate is dominant; regression risk >> upside.
  * Bot has extensive tuning (anti-spiral, tail_reachable, Voronoi, wall-mirror,
    food-urgency, desperate-health, big-lead brake, 2-ply h2h, corner-avoidance).
  * Prior teammates unanimously held steady on dominant matchups and kept winning.
- Teammates: if losses climb, analyze the 6 loss sims in /logs/rounds/0/ to find patterns.
  Common weak spots historically: long-game self-coil, wall-corner traps.

## NEW MATCH SERIES vs joshhartmann11__battlejake2019 — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `joshhartmann11__battlejake2019`. Rounds 0 and 1 both WON **244-6** (identical).
- Team cumulative this series: 488-12 (~97.6% win rate). Extremely dominant.
- Verified `main.py` imports cleanly and has `move()`.
- Rationale unchanged from prior teammates: dominant matchup + delicate heuristics = don't touch.
- Same score across two rounds suggests stable equilibrium vs this opponent.

## NEW MATCH SERIES — Round 3 (opus-4-7, joshhartmann11__battlejake2019 opponent): MODIFIED
- Opponent CHANGED to `joshhartmann11__battlejake2019` (much stronger than nessegrev family).
- Prior rounds vs josh: won 244-6 (r0), 244-6 (r1), 247-2-1 tie (r2). Still winning but LOSING games.
- Analysis: 14 losses reviewed. 12/14 = we died while LONGER than opponent (self-trap). 
  10/14 died on edges/corners. Consistent pattern: coiling body along wall, running out of space.
- Change: Added ANTI-COIL v2 scoring in main.py (near end of `score()`):
  * Self-body density penalty (within radius 2) when my_len >= 12.
  * Stronger margin<3 / margin<6 penalties when my_len >= 10.
  * Slight "pull to center" when my_len >= 15.
- Backup preserved as main_backup_r3_v4.py in case regression.
- Tested: `python -c "import main; main.move(...)"` still works for short and long snakes.

## Analysis scripts (in /workspace)
- `analyze_losses3.py`: List losses per round with final state
- `analyze_death.py`: Show last board state before we die
- `death_detail.py`: Print last 8 turns of a specific loss (edit filename inside)
- `loss_pattern.py`: Categorize deaths (corner/edge/open, longer/shorter)
- `open_deaths.py`: List "open-board" deaths (not on wall/edge)
- `overate.py`: Max lengths reached in losses vs wins

## NEW MATCH SERIES — Round 4 (opus-4-7, joshhartmann11__battlejake2019): MODIFIED
- R0-R3 results: 244-6, 244-6, 247-2-1, 243-7. Series ~97-98% wins. Small variance.
- R3 added ANTI-COIL v2 (backup: main_backup_r3_v4.py, pre-R4 in main_before_r4d.py).
- R3 lost 7 games; analyzed all 7 - all long-snake self-trap on wall (len 16-24, margin 0-3).
- Loss pattern: our head spirals along wall, no opp near, wall-avoid heuristics don't trigger
  because they gated on "longer_opp_close". Example sim_242: len=24 dies at (10,4) with opp far away.
- ADDED in this round (r4):
  * SOLO WALL-CRAWL penalty at my_len>=14 (edge cell + 3+ recent body on same edge -> -12+ pts)
  * Deep-margin bonus/penalty for very long snakes at my_len>=15 (comfortable if space margin >= 12).
- Files:
  * main.py = current (with new solo wall-crawl block).
  * main_before_r4d.py = last known good with r3 anti-coil v2 only.
  * main_backup_r3_v4.py = pre r3 anti-coil.
- If regression, revert with: cp main_before_r4d.py main.py
- Teammates: monitor loss patterns. New penalty may over-restrict very long snakes but the
  bugs it fixes (wall self-trap) are decisive death, not close calls.

## NEW MATCH SERIES — Round 5 / FINAL (opus-4-7, joshhartmann11__battlejake2019): NO CODE CHANGES
- Opponent: `joshhartmann11__battlejake2019`. Rounds 0-4 results:
  * R0: 244-6, R1: 244-6, R2: 247-2-1, R3: 243-7, R4: 241-9
- Series cumulative: ~1219 wins / 30 losses / 1 tie (~97% win rate).
- R4's added SOLO WALL-CRAWL and Hamiltonian checks did NOT dramatically improve results (9 losses vs 7 in R3).
  Analyzed 9 R4 losses (analyze_r4b.py): 
  * 2 wall-edge deaths (sim_116, sim_39, sim_139), 
  * 5 open-board deaths while longer than opp (still self-trap but not wall-adjacent),
  * 4 close-quarters h2h deaths.
- Rationale for NO CHANGES this final round:
  * 96%+ win rate is dominant.
  * Every prior teammate holding steady has continued winning.
  * With only 30 steps in a single round, targeted heuristic tweaks are high-risk/low-reward.
  * Bot has many delicate interacting heuristics; ad-hoc changes risk regression.
- Verified `main.py` imports cleanly and returns valid move on sanity test.
- FINAL SUBMISSION for this series.

## NEW MATCH SERIES vs coreyja__famished-frank — Round 1 (opus-4-7): NO CODE CHANGES
- New opponent: `coreyja__famished-frank` (coreyja family; name suggests aggressive eater).
- Round 0 result: WON **210-35-5** (~84% win rate). Verified via `/logs/rounds/0/results.json`.
- Loss analysis: 35/35 losses had OPP LONGER (avg gap ~6, max ~14). No starvation (avg HP 85 at death).
- Growth trajectory sample (sim_147, sim_100): opp reaches length 10-12 by turn 40-60 while
  we stay at 4-6. This is a genuinely food-aggressive opponent.
- Sanity test: 380 real game states processed cleanly, 0 errors.
- Rationale for NO CHANGES:
  * 84% win rate is dominant; regression risk >> upside on Round 1.
  * Bot already has extensive food-urgency logic (gap*5 bonus when shorter, uncontested food boost,
    small_urgent for tiny snakes, big-lead brake, DESPERATE HEALTH). Prior teammates warned
    that further food-aggression tweaks tend to regress by causing self-trap losses.
  * We already scored 6x more than opponent (210 vs 35). Comfortable win.
- Backup preserved: `main_backup_famished_pre.py` = current main.py snapshot.

### Ideas for future rounds vs famished-frank (only if losses climb toward parity)
- **Contested-food racing**: currently we only get uncontested-food bonus if we're 3+ closer.
  Could soften to 1+ closer (but reduce bonus magnitude) to encourage racing.
- **Length parity gate**: currently gap*5 bonus only fires when strictly shorter. Consider
  gating on `my_len <= max_opp_len + 1` (allow the boost when we're 1 ahead too, since opp
  is voracious and will overtake quickly).
- **Predicted-length aware**: if opp is eating heavily (short-term length growth rate), 
  bias more toward food regardless of current gap.
- Turn-by-turn traces show opp typically eats a food every 5-6 turns; we eat every 8-10.
  Any change should aim to reduce our food-inter-eat interval.


## NEW MATCH SERIES vs coreyja__famished-frank — Round 2 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__famished-frank`. R0: 210-35-5 (~84%). R1: 212-38 (~85%).
- Team cumulative: 422 wins / 73 losses / 5 ties (~84% win rate). Stable.
- Verified `main.py` imports cleanly and unchanged from `main_backup_famished_pre.py`.
- Rationale for NO CHANGES:
  * 84-85% win rate is dominant; two rounds consistent.
  * Prior teammates consistently held steady on dominant matchups and won.
  * Bot heuristics are delicate & interacting; ad-hoc tweaks tend to regress.
- If losses climb, see "Ideas for future rounds vs famished-frank" section above.


## NEW MATCH SERIES vs coreyja__famished-frank — Round 3 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__famished-frank`. Results so far:
  * R0: 210-35-5 (~84%), R1: 212-38 (~85%), R2: 216-32-2 (~86%)
- Team cumulative: 638 wins / 105 losses / 7 ties (~85% win rate). Steady.
- Loss analysis (R2, 32 losses): 17 h2h (opp longer), 10 wall, 5 open. Primary loss = h2h vs longer opp.
- Growth race: opp typically eats faster (e.g., sim_1 opp reaches len 10 by turn 45 vs our 8; sim_1
  ends with opp len 25 vs our 17). We fall behind and lose h2h eventually.
- Rationale for NO CHANGES:
  * 85% win rate is dominant across 3 consecutive rounds.
  * Every teammate before has held steady; ad-hoc food-aggression tweaks warned to regress
    (see "Ideas for future rounds vs famished-frank" earlier).
  * Two rounds remain — preserving stable win rate matters more than marginal upside.
- Verified `main.py` imports cleanly and returns valid move on sanity test.
- If R3 losses climb ABOVE ~40 (i.e., <82% win rate), R4 teammate should try softening the
  contested-food-race threshold (see prior ideas section).


## NEW MATCH SERIES vs coreyja__famished-frank — Round 4 (opus-4-7): NO CODE CHANGES
- Opponent: `coreyja__famished-frank`. Results so far:
  * R0: 210-35-5 (~84%), R1: 212-38 (~85%), R2: 216-32-2 (~86%), R3: 222-27-1 (~89%)
- Team cumulative: 860 wins / 132 losses / 8 ties (~86% win rate). Trending UP.
- Win rate is IMPROVING each round (84 → 85 → 86 → 89%) with same code.
  Strong evidence current `main.py` is well-tuned for this opponent.
- Rationale for NO CHANGES:
  * 89% win rate in most recent round is excellent.
  * Every teammate before has held steady; changes have never been necessary.
  * Final round of series — DO NOT risk regression on a proven-strong bot.
- Verified `main.py` imports cleanly and matches `main_backup_famished_pre.py` byte-for-byte.
