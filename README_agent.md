# Agent Notes (opus-4-8 team)

## TL;DR
- Game: BattleSnake standard, 11x11, 2 snakes, ~250 sim games per match. **Score = games won.**
- Opponent (`pambrose__pambrose-kotlin`) is the NAIVE SimpleSnake port with **NO collision
  avoidance** — it walks into walls/itself and dies within ~4-5 turns.
- Round 0 (before my edit) we tied it because OUR bot was also the same naive port
  (83 vs 88, 79 double-KOs — essentially a coin flip).
- **I (round 1) replaced `main.py` with a real strategy bot.** Local sim: 300/300 wins vs naive.

## Current bot strategy (`main.py`)
1. Enumerate the 4 moves; drop out-of-bounds and moves into snake bodies.
   - Tail modeling: a tail cell is treated as free next turn unless the snake just ate
     (last two body cells coincide).
2. Head-to-head handling:
   - Avoid cells an equal/longer enemy head can also reach (deadly).
   - Bonus for cells where a strictly shorter enemy head could go (we'd win the H2H).
3. Score remaining moves:
   - `+10 * flood_fill_space` (survival is #1 priority).
   - Heavy penalty if reachable space < our length (avoid getting boxed).
   - Food incentive scaled by hunger (health<40 or length<4 => seek food hard).
   - Small wall/edge penalty for mobility.
4. Robust fallbacks: if no safe move, pick any in-bounds move; on any exception return "up".
   Never crashes, never returns illegal.

## Files
- `main.py` — the active bot (improved).
- `main_naive_backup.py` — original naive port == the opponent's strategy. Use as sparring.
- `sim_test.py` — lightweight local match simulator (standard rules, 11x11, 2 snakes).
  Run: `python3 sim_test.py [num_games]`. Alternates start positions to be fair.
  NOTE: it's an approximation of the Go engine, good for RELATIVE comparison, not exact.

## How to verify changes
```
python3 -c "import ast; ast.parse(open('main.py').read())"   # syntax
python3 sim_test.py 300                                        # vs naive (should be ~all wins)
```
Also self-play survival: run `run_game(me,me,seed)` in sim_test — avg ~110 turns (healthy).

## Ideas for future rounds (if opponent gets smarter)
- Add 1-2 ply minimax / lookahead for enemy moves.
- Better trap detection: check if a move leads into a dead-end corridor via longer flood-fill.
- Aggression: when clearly longer, cut off / body-block the enemy to force collisions.
- Tune food weights; currently conservative (space > food).
- The opponent picks the FARTHEST food & has no avoidance, so it self-destructs fast; keep
  our bot alive and it wins by default. Don't over-engineer aggression vs this opponent.

## Round 2 update (opus-4-8)
- Round 1 result confirmed: **250-0** vs opponent (all 250 sim games won, 0 draws).
  Opponent still the naive port; dies in ~5-14 turns every game (verified in /logs/rounds/1).
- Added **1-ply lookahead safety**: `_future_safe_moves()` penalizes moving into a cell
  with 0 escape options (-500, guaranteed death next turn) or only 1 escape (-40).
  This reduces our (already tiny) risk of self-trapping — the only realistic way we could
  lose to a fast-dying opponent.
- Verified: still **400/400** vs naive; self-play avg survival improved 108 -> 135 turns;
  0 crashes / 0 illegal moves over 3000 fuzzed random states.
- Backups: `main_r1_backup.py` (round-1 bot), `main_naive_backup.py` (opponent's strategy).
- **Recommendation for round 3+:** we are dominating; don't risk regressions. Only change
  the bot if the opponent's strategy visibly changes in a new /logs/rounds/N. If it does,
  consider the "Ideas for future rounds" section above (deeper minimax, aggression).
