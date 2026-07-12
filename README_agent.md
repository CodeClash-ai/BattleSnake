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

## Round 1 (this task, opus-4-8) — CONFIRMED DOMINANT
- **Opponent CHANGED**: now `Nettogrof__nessegrev-julia` (NOT the pambrose one).
  - Behavior in /logs/rounds/0: it walks in a STRAIGHT LINE and hits a wall,
    dying within 2-13 turns every game. Another naive bot, zero collision avoidance.
- **Result of round 0 (previous submit): won 40-0** (40 games played, all wins, 0 draws).
  See /logs/rounds/0/results.json (opus-4-8: 40, opponent: 0).
- Verified our current `main.py` this round:
  - `python3 sim_test.py 200` => 200 wins / 0 losses / 0 draws vs naive.
  - Fuzz test `/tmp/fuzz.py` (5000 random boards): 0 crashes, 0 illegal, 0 out-of-bounds.
  - main.py vs main_r1_backup.py (200 alternating games): all draws (both survive to timeout;
    equal strength, so round-2 lookahead didn't regress survival).
- **Decision: NO code change to main.py.** We dominate a self-destructing opponent; the only
  realistic loss vector is a bug/regression in our own bot, so I kept it stable.
- If opponent ever gets smarter (check new /logs/rounds/N line-of-play), revisit the
  "Ideas for future rounds" section: minimax lookahead + aggression/cutoff when longer.

## Round 2 (this task, opus-4-8) — CONFIRMED DOMINANT, NO CHANGE
- Opponent this match: `Nettogrof__nessegrev-julia` (unchanged). Still the NAIVE bot:
  in /logs/rounds/1 it walks in a straight line (x=5, y=1->10) and dies at the wall on
  turn 10 every game. Zero collision avoidance.
- **Round 1 result: won 20-0** (see /logs/rounds/1/results.json: opus-4-8=20, opp=0.0).
- Verified our `main.py` this round:
  - syntax OK; `python3 sim_test.py 100` => 100 wins / 0 losses / 0 draws.
  - Fuzz 2000 random boards: 0 crashes, 0 illegal moves, max decision time 0.05ms.
  - Entry point `move()` returns dict `{"move": dir}`; server returns it directly. Correct.
- **Decision: NO code change.** We dominate a self-destructing opponent. Only realistic
  loss vector is a self-bug/regression, so kept main.py stable. If opponent ever changes
  (check new /logs/rounds/N line-of-play), see "Ideas for future rounds" above.

## Round (this task, opus-4-8) — DOMINANT, small safety improvement
- Opponent: `Nettogrof__nessegrev-java` (naive). In /logs/rounds/0 it walks a STRAIGHT
  LINE (x=5, y 1->10) into the top wall and dies on turn ~10-11 every game. Zero avoidance.
- **Round 0 result: won 40-0** (see /logs/rounds/0/results.json: opus-4-8=40, opp=0).
- Verified current main.py: syntax OK; sim_test 100 => 100/0/0 vs naive; fuzz 4000 boards
  => 0 crashes / 0 illegal; self-play avg survival ~135 turns.
- **Change made (low-risk downside protection only):** improved the emergency fallback in
  `_decide` (when ALL candidate moves collide). It used to return the first in-bounds move
  blindly; now it ranks in-bounds moves by (avoid equal/longer H2H loss) then flood-fill
  space. Only affects rare near-death states; no regression (new vs old ~even 48-41-61).
- Backup of pre-change bot: `main_r2_backup.py`.
- **Recommendation:** keep stable. Opponent self-destructs; only real loss vector is a
  self-bug. If opponent ever changes (check new /logs/rounds/N line-of-play), see the
  "Ideas for future rounds" section (deeper minimax, aggression/cutoff when longer).

## Round 2 of 5 (this task, opus-4-8) — DOMINANT, NO CODE CHANGE
- Opponent STILL `Nettogrof__nessegrev-java` (naive). Verified in /logs/rounds/1/sim_0:
  it walks a STRAIGHT LINE (x=1, y=5->10) into the TOP wall and dies on turn ~6. Zero
  collision avoidance, self-destructs every game.
- Results so far: round 0 won 40-0, round 1 won 33-0 (only 33 games actually played this
  round; the other 217 sim_*.jsonl files are EMPTY = games not run, NOT losses/draws).
- Verified current main.py this round:
  - syntax OK; `python3 sim_test.py 100` => 100 wins / 0 losses / 0 draws.
  - Fuzz `/tmp/fuzz.py` (3000 random boards, PYTHONPATH=/workspace): 0 crashes, 0 illegal,
    max decision time 0.04ms.
  - Entry point `move(game_state)` -> {"move": dir}; server.py `on_move` returns it directly.
- **Decision: NO code change.** We dominate a self-destructing opponent; the only realistic
  loss vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** first check /logs/rounds/N/sim_0.jsonl to see if opponent behavior
  changed. If still walking into walls -> just submit as-is. If it got smarter, see the
  "Ideas for future rounds" section (minimax lookahead, aggression/cutoff when longer).
  Re-run: `python3 sim_test.py 100` and `python3 fuzz_test.py (from /workspace)`.
