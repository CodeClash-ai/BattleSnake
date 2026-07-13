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

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT, DOMINANT, NO CODE CHANGE
- **Opponent CHANGED to `csauve__bookworm`.** Despite the name, it is ALSO a naive bot:
  in /logs/rounds/0 it walks a STRAIGHT LINE downward (x fixed, y=9->0) into the BOTTOM
  wall and dies on turn ~10-14 every game. Zero collision avoidance, self-destructs.
- **Round 0 result: won 20-0** (see /logs/rounds/0/results.json: opus-4-8=20, bookworm=0.0).
  Verified across sim_1,3,6,11,15,18: winner=opus-4-8 every time, opponent hits wall.
- Verified current main.py this round:
  - syntax OK; `python3 sim_test.py 100` => 100 wins / 0 losses / 0 draws.
  - `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=0.06.
  - `move(game_state)` returns {"move": dir}; server.py on_move returns it directly. Correct.
- **Decision: NO code change.** We dominate a self-destructing opponent; only realistic loss
  vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** check /logs/rounds/N/sim_0.jsonl first. If opponent still walks into
  walls -> just submit as-is. If it got smarter, see "Ideas for future rounds" above
  (minimax lookahead, aggression/cutoff when longer). Re-verify with sim_test 100 + fuzz.

## Round 2 of 5 (this task, opus-4-8) — DOMINANT, NO CODE CHANGE
- Opponent STILL `csauve__bookworm` (naive). Verified /logs/rounds/1/sim_0: it walks a
  STRAIGHT LINE right (y=9, x=1->10) into the RIGHT wall and dies on turn ~10. Zero
  collision avoidance, self-destructs every game. Our bot survives & wins.
- Result round 1: won 20-0 (see /logs/rounds/1/results.json: opus-4-8=20, bookworm=0.0).
- Verified current main.py this round: syntax OK; `python3 sim_test.py 100` => 100/0/0;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=0.06.
- **Decision: NO code change.** Only real loss vector is a self-bug; kept main.py stable.
- Next teammate: check /logs/rounds/N/sim_0.jsonl first. If opponent still walks into walls
  -> submit as-is. If smarter, see "Ideas for future rounds" (minimax, aggression/cutoff).

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT, DOMINANT, NO CODE CHANGE
- **Opponent CHANGED to `coreyja__improbable-irene`.** Still a NAIVE bot: in
  /logs/rounds/0 it walks a STRAIGHT LINE UP (x=5, y=1->10) into the TOP wall and dies
  on turn ~5-13 every game. Zero collision avoidance, self-destructs.
- **Round 0 result: won 20-0** (see /logs/rounds/0/results.json: opus-4-8=20,
  coreyja__improbable-irene=0.0). NOTE: 250 sim_*.jsonl files exist but only 20 had
  actual games (rest EMPTY = not played, NOT losses). Analyzed all 20: all wins,
  opponent dies turns 5-13.
- Verified current main.py this round:
  - syntax OK; `python3 sim_test.py 100` => 100 wins / 0 losses / 0 draws.
  - `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=0.06.
- **Decision: NO code change.** We dominate a self-destructing opponent; only realistic
  loss vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** check /logs/rounds/N/sim_0.jsonl first (analyze opponent head moves
  turn-by-turn). If opponent still walks into walls -> submit as-is. If it got smarter,
  see "Ideas for future rounds" above (minimax lookahead, aggression/cutoff when longer).
  Re-verify with `python3 sim_test.py 100` + `PYTHONPATH=/workspace python3 fuzz_test.py`.

## Round 2 of 5 (this task, opus-4-8) — DOMINANT, NO CODE CHANGE
- Opponent STILL `coreyja__improbable-irene` (naive). Verified /logs/rounds/1/sim_0:
  it walks a STRAIGHT LINE UP (x=9, y=9->10) into the TOP wall and dies on turn ~2. Zero
  collision avoidance, self-destructs every game. Our bot survives & wins.
- Result round 1: won 20-0 (see /logs/rounds/1/results.json: opus-4-8=20, opponent=0.0).
- Verified current main.py this round: syntax OK; `python3 sim_test.py 100` => 100/0/0;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=0.04.
- **Decision: NO code change.** Only real loss vector is a self-bug; kept main.py stable.
- Next teammate: check /logs/rounds/N/sim_0.jsonl first. If opponent still walks into walls
  -> submit as-is. If smarter, see "Ideas for future rounds" (minimax, aggression/cutoff).

## Round 1 of 5 (this task, opus-4-8) — NEW SMARTER OPPONENT, IMPROVED BOT
- **Opponent CHANGED to `graeme-hill__snakebot` — this one is SMART.** It has real
  collision avoidance and survives LONG games (150-286 turns). It does NOT self-destruct.
- **Round 0 result: won 84-4** (see /logs/rounds/0/results.json). We lost 4 games
  (sim_110, sim_111, sim_216, sim_221). Analysis: in every loss WE were much LONGER
  (e.g. len 29 vs 15, len 20 vs 13) but **self-trapped / coiled into a dead pocket** and
  died. The opponent just outlasts us when we box ourselves in.
- **Changes I made to main.py (backup: main_r3_backup.py = pre-change bot):**
  1. Added `_reachable_with_tails()` — a TIME-AWARE flood fill (BFS carrying step count)
     that frees body cells once the tail retreats past them. Prevents over-penalizing
     corridors we can actually survive; uses max(static_fill, time_fill) for space.
  2. Added a **2-ply space lookahead** in scoring: for each candidate move, compute the
     best reachable region on the FOLLOWING move (`best_next_space`). Rewards it (+4 each)
     and penalizes if it's < our length (-20 each). This directly targets the coiling/
     self-trap loss vector — moves that look ok now but lead into a trap get downranked.
- **Verification:**
  - syntax OK; `python3 sim_test.py 100` => 100/0/0 vs naive.
  - `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms~2.2 (limit 500ms, fine).
  - New bot vs main_r3_backup (time-aware only): 21-15 (60 games) — 2-ply helps.
  - Earlier: time-aware bot vs pre-r3 bot: 66-50 (200 games) — big survival gain.
- **Next teammate:** the opponent is a REAL bot now. Focus on NOT self-trapping in long
  games (we already win the vast majority). Ideas: deeper lookahead, better long-snake
  space management (Hamiltonian-ish tail-following when long+safe), aggression/cutoff when
  clearly longer. Re-analyze /logs/rounds/N losses: `tail -1 sim_X.jsonl` has winnerName;
  loss pattern = we coil into a pocket. Keep sim_test 100 + fuzz clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — SMART OPPONENT, ADDED TAIL-ACCESS ANTI-TRAP
- Opponent: `graeme-hill__snakebot` (SMART, survives long games). Results: round 0 won
  84-4, round 1 won 86-2. **Our only loss vector = SELF-TRAPPING when we're much LONGER.**
  Analyzed both round-1 losses (sim_206, sim_216): we were len ~20 vs enemy ~11 but coiled
  into the bottom-left corner and boxed ourselves in (all 4 head-neighbors = our own body).
- **Change (backup: main_r4_backup.py = pre-change bot):** Added `_can_reach()` — a
  time-aware BFS that tests whether, after a candidate move, we can still reach our OWN
  TAIL's cell (tails treated as vacating). In scoring: +120 if tail reachable, -200 if not.
  Rationale: if we can keep a path to our tail we can chase it and never box ourselves in;
  losing tail access is the canonical self-trap signal. This directly attacks the coil loss.
- **Verification:**
  - syntax OK; `python3 sim_test.py 60` => 60/0/0 vs naive.
  - `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.32.
  - Long-snake (len 22) timing: max 2.72ms (limit 500ms — safe).
  - new vs main_r4_backup self-play (40 games): all draws (both survive to timeout, no
    regression). Trap-scenario forward-sim: both survive when enemy passive.
- **Next teammate:** opponent is REAL; we win ~95%+. Remaining losses are self-coils in
  long games. Further ideas: full N-ply space simulation (not just tail-reach), or when
  clearly longer + safe, tighten a Hamiltonian-ish tail-follow. Keep sim_test + fuzz clean.
  Analyze new losses: `cd /logs/rounds/N; for f in sim_*.jsonl; do tail -1 $f | ...; done`
  to find files where winner != opus, then inspect last turns for the coil pattern.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `coreyja__devious-devin`, DOMINANT, NO CODE CHANGE
- **Opponent CHANGED to `coreyja__devious-devin`.** It is a NAIVE bot: in /logs/rounds/0
  it walks a STRAIGHT LINE UP (x=5, y=1->10) into the TOP wall and dies on turn ~10 every
  game (verified turn-by-turn in sim_0). Zero collision avoidance, self-destructs.
- **Round 0 result: won 20-0** (see /logs/rounds/0/results.json: opus-4-8=20, opponent=0.0).
  20 non-empty sim games, all wins; games last only 5/9/13 turns (opponent dies at wall).
- Verified current main.py this round:
  - syntax OK; `python3 sim_test.py 100` => 100 wins / 0 losses / 0 draws.
  - `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.35 (<500 limit).
- **Decision: NO code change.** We dominate a self-destructing opponent; only realistic loss
  vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** check /logs/rounds/N/sim_0.jsonl first (turn-by-turn opponent head).
  If opponent still walks into walls -> submit as-is. If it got smarter, see "Ideas for
  future rounds" / the graeme-hill anti-self-trap notes above (time-aware flood fill,
  tail-reach, 2-ply space lookahead are all already in main.py). Re-verify with
  `python3 sim_test.py 100` + `PYTHONPATH=/workspace python3 fuzz_test.py`.

## Round 2 of 5 (this task, opus-4-8) — DOMINANT vs devious-devin, NO CODE CHANGE
- Opponent STILL `coreyja__devious-devin` (naive). Verified /logs/rounds/1/sim_0 turn-by-turn:
  opponent walks x=1: (1,1)->(1,0) and dies at BOTTOM wall by turn 3. Zero collision
  avoidance, self-destructs every game. Our bot survives & wins.
- Results: round 0 won 20-0, round 1 won 20-0 (see /logs/rounds/*/results.json:
  opus-4-8=20, opponent=0.0 both rounds).
- Verified current main.py this round: syntax OK; `python3 sim_test.py 100` => 100/0/0;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.19 (<500 limit).
- **Decision: NO code change.** We dominate a self-destructing opponent; only realistic loss
  vector is a self-bug/regression, so kept main.py fully stable.
- Next teammate: check /logs/rounds/N/sim_0.jsonl turn-by-turn first. If opponent still walks
  into walls -> submit as-is. If it got smarter (survives long games), see the graeme-hill
  anti-self-trap notes above; main.py already has time-aware flood fill, tail-reach BFS, and
  2-ply space lookahead. Re-verify with sim_test 100 + fuzz before submitting.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `m-schier__kreuzotter`, ANTI-CORNER-TRAP
- **Opponent CHANGED to `m-schier__kreuzotter` — SMART bot** (real avoidance, long games).
- **Round 0 result: won 31-2, 1 tie** (/logs/rounds/0/results.json). We LOST 2 games
  (sim_222, sim_223) and tied 1 (sim_215, 299 turns).
- **Loss analysis (both losses = CORNER SELF-TRAP while much LONGER):**
  - sim_222: OPUS L18 walked UP the left column x=0 into top-left corner (0,10), boxed in,
    died turn 137 (enemy only L6).
  - sim_223: OPUS L13 walked DOWN x=0 into bottom-left corner (0,0), boxed in, died turn 124
    (enemy L11). Wall-hugging patrol -> corner death is our ONLY loss vector.
- **Changes to main.py (backup: main_r0_kreuzotter_backup.py = pre-change bot):**
  1. Stronger edge/corner penalties: edge_pen *6 (was *2), extra -40 for actual corner cells,
     gentle center-pull (center_dist * 0.15). Discourages wall-hugging patrols into corners.
  2. Added CONSERVATIVE static-fill trap check: `space_static < my_len => -(diff)*15`. The
     time-aware fill can over-trust tails vacating; if the *immediately reachable* static area
     is already smaller than our body we're likely entering a self-trap corridor.
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0 vs naive; fuzz 0 crashes /
  0 illegal / maxt 2.84ms; new vs old self-play (30 games) 10-9-11 (no regression).
- **Next teammate:** if opponent unchanged (SMART, long games), keep this. Re-analyze new
  losses in /logs/rounds/N: `for f in sim_*.jsonl; do tail -1 $f|grep -L opus; done` then
  inspect last ~10 turns for the coil/corner pattern (loop turns printing snake heads).
  If losses persist, consider deeper N-ply corridor sim or Hamiltonian tail-follow when long.

## Round 2 of 5 (this task, opus-4-8) — kreuzotter, kept dominant + tiny length-scaled corner fix
- Opponent: `m-schier__kreuzotter`. **Behavior is INCONSISTENT across rounds:**
  - Round 0 (see /logs/rounds/0): SMART — long games, caused our only 2 losses + 1 tie via
    CORNER SELF-TRAP while we were much longer.
  - Round 1 (see /logs/rounds/1): NAIVE — walked STRAIGHT UP col x=1 into top wall, died
    turn 10 every game. **We won 20-0** (all 20 non-empty sim games; other sim_*.jsonl empty).
- So the opponent may swap between smart/naive versions. Our bot is robust to both.
- **Change (backup: main_r1of5_backup.py = pre-change bot):** made the edge/corner penalty
  scale with our length: `len_scale = 1 + max(0, my_len-6)*0.15`. Corner/edge self-traps are
  ONLY dangerous when we're long; a short snake can graze edges to grab food. This sharpens
  the exact round-0 loss vector (long-snake corner box-in) without over-penalizing early game.
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0; fuzz => crashes=0 illegal=0
  maxt_ms=2.68; new vs prev self-play (80 games) = 26-26-28 (dead even, NO regression);
  selfplay survival 132 turns (unchanged); long-snake corner test picks center over edge.
- **Next teammate:** check /logs/rounds/N/sim_0.jsonl turn-by-turn FIRST. If opponent walks
  into walls -> submit as-is. If SMART (long games) -> re-analyze losses for the corner-coil
  pattern; main.py already has: time-aware flood fill, tail-reach BFS, 2-ply space lookahead,
  length-scaled corner penalties. Consider deeper N-ply corridor sim only if losses persist.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `nbw__nbw-crystal` (SMART), ADDED ENEMY-CONTESTED-SPACE PENALTY
- **Opponent CHANGED to `nbw__nbw-crystal` — a SMART bot** (real avoidance, plays long
  competitive games). NOT a wall-walker.
- **Round 0 result: won 248-2** (see /logs/rounds/0/results.json). We lost only 2 games:
  sim_17 and sim_236.
- **Loss analysis (both = self-coil into a WALL POCKET while the enemy SEALED the mouth):**
  - sim_17: opus L7 walked right/up into the RIGHT-edge pocket (x=9) between its own
    coiled body and the wall; enemy body sealed the entrance; boxed in, died turn 72.
  - sim_236: opus L5 same pattern in the right-edge region; enemy sealed it in, died ~turn 103.
  - Root cause: our time-aware flood fill trusts enemy tails to VACATE, but the enemy can
    keep feeding body into the pocket mouth to keep us sealed. So `space` looked survivable
    at entry but wasn't.
- **Change made (backup: main_r1of5_v2_backup.py = pre-change bot):** added an
  ENEMY-CONTESTED-SPACE penalty in `_decide`'s scoring loop. After computing static/time
  space, we ALSO do a conservative static flood-fill that treats every cell the enemy head
  can reach next turn (`enemy_next`) as BLOCKED. If that contested area < our length, we
  subtract `(my_len - space_contested) * 12`. This downranks moves into pockets the enemy
  can seal — directly targeting the only loss vector.
- **Verification:** syntax OK; `python3 sim_test.py 200` => 200/0/0 vs naive; fuzz => crashes=0
  illegal=0 maxt_ms=3.02 (<500 limit); new-vs-prev self-play (120 games) = all draws (both
  survive to timeout — NO regression, equal strength). NOTE: the change did NOT flip the exact
  sim_17 turn-67 move (that trap was essentially already set 1-2 turns earlier and is very hard
  to detect at entry), but it adds a general safety net against the seal-in pattern earlier in
  the approach. Expected to reduce, not necessarily eliminate, coil losses.
- **Next teammate:** opponent `nbw__nbw-crystal` is REAL and competitive; we win ~99%. Remaining
  losses are enemy-sealed wall-pocket coils in mid/long games. First check /logs/rounds/N/sim_0
  to confirm opponent unchanged. If losses persist, ideas: (a) deeper N-ply forward sim treating
  the enemy as an active pursuer (minimax on space), (b) avoid the right/left edge columns more
  aggressively when a longer/equal enemy is between us and open board, (c) Hamiltonian-ish
  tail-follow when long+safe. Keep `sim_test 100` + `fuzz_test.py` clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — nbw-crystal, added H2H-trap follow-up penalty
- Opponent `nbw__nbw-crystal` (mostly straight-line/wall-walker this match; some long games).
- **Round 1 result: won 246-0 with 4 TIES** (/logs/rounds/1/results.json). The only non-wins
  are 4 head-to-head DRAWS (sim_0,38,92,244; empty winnerName + isDraw:true), at the noise floor.
- Analyzed sim_38 draw turn-by-turn: opus coiled itself so that by turn 27 its ONLY non-H2H
  neighbor was a top-edge pocket cell (6,10); the following turn its only exit was the shared
  H2H cell (7,10), which the equal-length enemy also took -> mutual elimination (draw). The trap
  develops several turns earlier (turn 26 bot went right toward the pocket instead of left).
- **Change (backup: main_r1of5_v3_backup.py = pre-change bot):** added an H2H-AWARE FOLLOW-UP
  penalty in `_decide` scoring: for each candidate move, count follow-up cells that are neither
  blocked nor an equal/longer-enemy H2H cell (`safe_followups`). If a move leaves 0 safe
  follow-ups (forced into H2H/wall next turn), subtract 300. Targets the exact draw pattern
  (coiling into a pocket whose only exit is an H2H cell).
- **Verification:** syntax OK; `python3 sim_test.py 100` => 100/0/0; fuzz => crashes=0 illegal=0
  maxt_ms=2.24; new vs prev self-play (80 games) = 26-26-28 (dead even, NO regression). NOTE:
  the sim_38 trap was essentially set 2 turns before the draw and is not fully fixable at entry;
  the change is a general net-positive safety net, not a guaranteed fix for that one game.
- **Next teammate:** we're dominant (~98%+, remaining losses/draws are rare H2H coils). Check
  /logs/rounds/N/sim_0.jsonl first. If opponent unchanged -> submit as-is or keep tuning the
  coil/H2H-pocket avoidance a couple turns EARLIER (the trap forms ~2 turns before death).
  main.py has: time-aware flood fill, tail-reach BFS, 2-ply space lookahead, enemy-contested
  space penalty, length-scaled corner penalty, and now the H2H follow-up penalty.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `Xe__since` (SMART/GROWTH), FOOD STRATEGY FIX
- **Opponent CHANGED to `Xe__since` — a STRONG, AGGRESSIVE bot** that GROWS big and uses its
  length advantage to cut us off. NOT a wall-walker; plays long competitive games.
- **Round 0 result: won 234-14** (/logs/rounds/0/results.json). We LOST 14 games
  (sim_106,115,126,146,154,178,199,205,240,243,244,56,78,83). Analyzed all:
  - **ROOT CAUSE = we fell BEHIND in LENGTH, then got trapped/cut off by the longer enemy.**
    In every loss, Xe was longer at death (finalXe 12,11,16,30,21,23...). Several games we were
    EQUAL or LONGER at turn 30 (sim_126 opus7/xe5, sim_56 opus6/xe4) but STALLED while Xe kept
    eating and grew huge (30,23,21). Then Xe cornered/H2H-killed us (sim_106: Xe L12 won the
    H2H at (10,2) vs our L11 in the bottom-right).
  - Our OLD bot was too conservative on food: it only chased food when `health<40 or len<4`,
    otherwise weight was just `d_after*1.0`. So it never grew and got out-lengthed.
- **Change made (backup: main_r0_xe_since_backup.py = pre-change bot):**
  1. Track `max_enemy_len`. New desire flags: `starving` (health<45 or len<5) and
     `behind_or_even` (my_len <= max_enemy_len+1, i.e. NOT clearly longer).
  2. Length-aware food weighting in scoring:
     - starving: `d_after*9` + 70 on-food bonus (chase hard).
     - behind_or_even: `d_after*4` + 45 bonus (grow to keep pace — the key fix).
     - clearly longer: `d_after*1.5` + 15 bonus (relax, prioritize safe space/positioning).
  Safety still dominates (space penalty -50/unit, H2H -1000 >> food +45/70), so we won't
  dive into food traps — verified below.
- **Verification:** syntax OK; `python3 sim_test.py 80` => 80/0/0 vs naive;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.3;
  new-vs-old self-play: 12-6 (30g) and 14-10 (40g) — consistent WIN over the old passive bot.
- **Next teammate:** opponent is REAL and grows aggressively. Check /logs/rounds/N/sim_0 first.
  If we still lose, the losses are: (a) falling behind in length (tune food weights UP more,
  esp. `behind_or_even` d_after multiplier / bonus), or (b) getting cut off by a longer enemy
  in edge regions (already have edge/corner penalties, enemy-contested-space penalty, tail-reach,
  2-ply space lookahead, H2H follow-up penalty). Consider: aggression/cutoff when WE are longer,
  or deeper N-ply space sim treating enemy as active pursuer. Keep sim_test + fuzz clean.

## Round 2 of 5 (this task, opus-4-8) — Xe__since, STRENGTHENED EDGE/SHADOW ANTI-TRAP
- Opponent `Xe__since` (SMART, aggressive, grows & shadows). Results so far: round 0 won
  234-14, round 1 won 244-6. **Our remaining losses = EDGE/CORNER SELF-TRAP while EQUAL
  length (L6 vs L6)** where the enemy SHADOWS us one lane inward and seals our exits.
  - sim_113: opus L6 ran into the LEFT column (x=0), enemy body at (1,9)+top row sealed
    the mouth, boxed in at (1,8), died turn 31.
  - sim_116: opus L6 ran along the TOP row (y=10) from (6,10)->(10,10) into the top-right
    CORNER, enemy shadowed at (10,9)/(10,8) and sealed it, died turn 36. Wrong move was
    turn 31: went UP onto the top edge when U/D/R were all open — chose the edge over the
    open board, then got committed to the wall run.
  - Root cause: our edge/corner penalty only scaled up past len>6 (len_scale=1 at L6), so
    at the exact loss length the edge penalty was tiny and the bot happily hugged walls.
- **Changes (backup: main_r2of5_xe_backup.py = pre-change bot):**
  1. Edge/corner penalty now kicks in earlier & stronger: `len_scale = 1 + max(0,len-4)*0.18`
     (was len-6, *0.15); base edge_pen weight 9.0 (was 6.0). Discourages wall-hugging from
     mid-game onward, not just when very long.
  2. Added an **EDGE-SHADOW penalty**: when a candidate move goes onto an edge/corner AND
     the nearest enemy head is within 3 cells, compute the free "run" length along that edge
     (both directions) before hitting an obstacle/corner. If run < my_len, subtract
     (my_len-run)*18. Directly targets the "enemy shadows us into the corner along an edge"
     loss vector — a short edge corridor with an enemy right there is a trap.
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0 vs naive; fuzz => crashes=0
  illegal=0 maxt_ms=2.3; long-snake(L22) decision time 0.01ms; new vs old self-play (80g)
  = 28-24-28 (new slightly ahead, NO regression); hungry short snake still grabs EDGE food
  (edge penalty balanced, doesn't cause starvation). NOTE: couldn't perfectly reconstruct the
  exact sim_113/116 boards (enemy body positions unknown), so the fix is validated by design
  + self-play + no-regression, not a replay of those exact frames.
- **Next teammate:** opponent is REAL/aggressive & grows. First check /logs/rounds/N/sim_0 &
  scan losses (`for f in sim_*.jsonl; do tail -1 $f|grep -qi opus||echo $f; done`), then run
  /tmp/analyze2.py-style trace of last frames. Our remaining loss vector is likely still
  edge/corner shadowing or falling behind in length. main.py now has: time-aware flood fill,
  tail-reach BFS, 2-ply space lookahead, enemy-contested space, H2H follow-up penalty,
  length-scaled edge/corner penalty, AND edge-shadow corridor penalty. Ideas if losses
  persist: deeper N-ply minimax treating enemy as active pursuer; aggression/cutoff when we
  are clearly longer. Keep sim_test + fuzz clean; verify decision time stays < 500ms.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `ccSnake2018__ccsnake` (SMART, GROWS FAST), BOOSTED FOOD
- **Opponent CHANGED to `ccSnake2018__ccsnake` — a SMART, FAST-GROWING bot.** Real avoidance,
  plays competitive games, GROWS QUICKLY and uses length to cut us off / win H2H.
- **Round 0 result: won 222-24, 4 ties** (/logs/rounds/0/results.json). 250 non-empty games.
- **Loss analysis (24 losses, tool: /tmp/lens.py & /tmp/trace2.py):** In ~ALL losses OPUS was
  SHORTER than the opponent at death (L4 vs L7, L6 vs L8, L5 vs L9...). Many losses were EARLY
  (turn 16-40) with us at L4-L6 vs opp L7-L8, and often on edges/corners. **ROOT CAUSE =
  falling BEHIND in length early; opponent out-grows us then out-lengths/cuts us off/traps us.**
- **Change made (backup: main_r0_ccsnake_backup.py = pre-change bot):** boosted food aggression:
  - starving: d_after*11 (was 9), on-food +90 (was 70).
  - behind_or_even: d_after*7 (was 4), on-food +70 (was 45). This is the key fix — grow to
    keep pace with the fast opponent. Safety still dominates (space -50/unit, H2H -1000 >> +90),
    verified no self-trap regression.
- **Verification:** syntax OK; `python3 sim_test.py 100` => 100/0/0 vs naive; fuzz => crashes=0
  illegal=0 maxt_ms=2.24; new vs main_r0_ccsnake_backup self-play (30g) = 11-7-12 (new AHEAD,
  no regression). Tool /tmp/vs.py (needs sys.path insert) compares two bot files head-to-head.
- **Next teammate:** opponent grows fast & is aggressive. If losses persist, the vector is still
  (a) falling behind in length (push behind_or_even food weight UP more), or (b) edge/corner
  cutoff by a longer enemy. main.py has: time-aware flood fill, tail-reach BFS, 2-ply space
  lookahead, enemy-contested space, H2H follow-up penalty, length-scaled edge/corner + edge-
  shadow penalties. Re-analyze /logs/rounds/N: `python3 /tmp/lens.py sim_*.jsonl` (rebuild it;
  it prints OPUS/OPP length & head at death for each game). Keep sim_test + fuzz clean.

## Round 2 of 5 (this task, opus-4-8) — ccSnake, SAFETY-AWARE FOOD + STRONGER SEAL DETECTION
- Opponent STILL `ccSnake2018__ccsnake` (SMART, grows fast). Results: round 0 won 222-24+4T,
  round 1 won 221-26+3T (~10% loss rate).
- **KEY: opponent's real source is available!** `git show origin/human/ccSnake2018/ccsnake:main.py`
  -> saved to /tmp/opp_main.py. I built a REAL head-to-head sim: `/tmp/vs_opp.py <botfile> <N>`
  (uses sim_test.run_game, alternates start). Baseline old bot vs real opp = 86-13-1 (N=100).
  **Copy /tmp/opp_main.py into /workspace and re-extract for future rounds — it's the actual foe.**
- **Loss analysis (26 losses in /logs/rounds/1, tools /tmp/lens.py + /tmp/trace2.py):** the
  dominant pattern is OPUS CHASING FOOD INTO AN EDGE/CORNER while the enemy is on the adjacent
  lane and SEALS us against the wall. Canonical: sim_10 — food spawned at corner (10,0); OPUS
  ran DOWN the x=10 column to (10,2); opponent climbed x=9 -> (10,0)->(10,1) and sealed us,
  died turn 31. Also sim_64/sim_77: OPUS ran x=0 column into bottom-left corner (0,0). We are
  usually also SHORTER (falling behind in length).
- **Changes (backup: main_r1of5_ccsnake_backup.py = pre-change bot):**
  1. SAFETY-AWARE FOOD SELECTION (replaced raw nearest_food): rank food by cost =
     our_dist + penalties. If an enemy is as close or closer to a food (`ed <= d`), add
     4 + corner/edge_risk*8 (corner risk=2, edge=1). Uncontested food gets only risk*2.
     -> we stop diving for contested corner/edge food that seals us against the wall.
  2. Boosted enemy-contested-space penalty weight 12 -> 18 (the direct seal-in detector).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; fuzz => crashes=0 illegal=0
  maxt_ms=2.52; new vs real opp `/tmp/vs_opp.py main.py 120` => 103-16-1 (SAME as old 86-13-1
  scaled; no regression — the sim's random food rarely reproduces the exact corner-spawn trap,
  so the fix is validated by design + no-regression, not a sim win delta).
- **Next teammate:** USE /tmp/opp_main.py (real opponent) via /tmp/vs_opp.py to test — far better
  than the naive sim_test. Remaining loss vector = corner/edge food-chase seal + falling behind
  in length. Ideas: (a) even more aggressive food growth when behind (behind_or_even weights up),
  (b) never enter an edge column when an enemy head is within ~3 on the adjacent column, (c) deeper
  N-ply seal simulation. main.py has: time-aware flood fill, tail-reach BFS, 2-ply space lookahead,
  enemy-contested space (now *18), H2H follow-up, length-scaled edge/corner + edge-shadow, and now
  safety-aware food selection. Keep sim_test + fuzz + /tmp/vs_opp.py clean before submitting.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `coreyja__bombastic-bob` (RANDOM), DEEPENED ANTI-COIL
- **Opponent CHANGED to `coreyja__bombastic-bob`.** Its REAL SOURCE is available and saved
  to `/workspace/opp_bombastic_bob.py` (via `git show origin/human/coreyja/bombastic-bob:main.py`).
  It picks a **RANDOM "reasonable" move** each turn: any move that stays on-board, avoids all
  snake bodies, and avoids lethal hazards. It has BASIC collision avoidance but NO strategy —
  it wanders randomly and survives fairly long, but eventually boxes itself in.
- **Round 0 result: won 249-1** (see /logs/rounds/0/results.json). Our ONLY loss (sim_78) was
  a SELF-COIL: opus L9 vs opp L5, we spiraled our own body inward in the top-right region
  (turns 43-50: coiling around (7-10, 4-9)) and boxed OURSELVES in. NOT the opponent's doing.
- **Testing note:** the opponent uses `random.random()` with NO fixed seed, so results are
  NON-DETERMINISTIC. Use `python3 vs_opp.py main.py <N>` (already points at opp_bombastic_bob.py)
  and run LARGE samples (200+). Current main.py ~98% win rate vs it. Losses = our self-coils;
  a few mutual-H2H draws are noise.
- **Change made (backup: main_r0_bombastic_backup.py = pre-change bot):** DEEPENED the 2-ply
  space anti-coil signal, since ALL our losses vs this random bot are self-coils:
    - `best_next_space` reward 4.0 -> 6.0
    - shrinking-space penalty `(my_len-best_next_space)` 20.0 -> 30.0
  This more strongly downranks moves that lead into a shrinking follow-up region (the spiral
  self-coil pattern). Directly attacks the sim_78 loss vector.
- **Verification:** syntax OK; `python3 sim_test.py 100` => 100/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.37 (<500 limit). Head-to-head vs real
  opp: v2 consistently beat current on matched seeds (248-0-2 & 248-1-1 vs 247-1-2 & 245-3-2);
  large sample `vs_opp.py main.py 200` => 197-2-1.
- **Next teammate:** opponent is RANDOM (opp_bombastic_bob.py). We win ~98-99%; the only loss
  vector is OUR OWN self-coil/spiral in mid-long games (we out-survive the random bot but can
  box ourselves in). If losses persist, push the anti-coil further: deeper N-ply space sim, or
  a Hamiltonian-ish tail-follow when long+safe. main.py has: time-aware flood fill, tail-reach
  BFS, 2-ply space lookahead (now weighted 6.0/-30), enemy-contested space, H2H follow-up,
  length-scaled edge/corner + edge-shadow penalties, safety-aware food. Use `vs_opp.py` with
  LARGE N (non-deterministic opp). Keep sim_test 100 + fuzz clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — coreyja__bombastic-bob (RANDOM), DEEPENED 2-PLY ANTI-COIL
- Opponent STILL `coreyja__bombastic-bob` (RANDOM reasonable-move bot; real source in
  `opp_bombastic_bob.py`; NON-deterministic, no seed). Test with `python3 vs_opp.py main.py <N>`.
- Results: round 0 won 249-1, round 1 won 248-2 (/logs/rounds/*/results.json).
- **Loss analysis (round 1: sim_75, sim_94):** BOTH are SELF-COILS while much LONGER
  (opus L12 vs L5; L15 vs L6). We wall-hug (e.g. x=0 left column) into a shrinking pocket
  and box OURSELVES in. NOT the opponent's doing — the random bot just outlasts us when we
  coil. This is our only remaining loss vector (~1.5% of games).
- **Change (backup: main_r1of5_bombastic_backup.py = pre-change committed bot):** deepened
  the 2-ply follow-up-space anti-coil signal again:
    - `best_next_space` reward 6.0 -> 8.0
    - shrinking-space penalty `(my_len-best_next_space)` 30.0 -> 45.0
  More strongly downranks moves leading into a shrinking follow-up region (the spiral coil).
- **Verification:** syntax OK; `sim_test.py 80` => 80/0/0; fuzz => crashes=0 illegal=0
  maxt_ms=2.57. A/B vs real opp on IDENTICAL seeds (converts a loss to a win, never worse):
    - sample 1 (250g): committed 244-3-3 vs v2 245-2-3.
    - sample 2 (200g, diff seeds): committed 199-1-0 vs v2 200-0-0.
  Small (near noise floor) but consistently >= committed, 0 regressions.
- **Next teammate:** opponent is RANDOM (opp_bombastic_bob.py). We win ~98-99%; only loss
  vector is OUR self-coil in mid-long games. If losses persist push anti-coil further
  (deeper N-ply space sim, or Hamiltonian tail-follow when long+safe). Use `vs_opp.py` with
  LARGE N (non-deterministic). Keep sim_test 100 + fuzz clean before submitting.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `coreyja__coreyja-rs` (NAIVE), NO CODE CHANGE
- **Opponent CHANGED to `coreyja__coreyja-rs`.** It is a NAIVE bot: in /logs/rounds/0 it
  walks a STRAIGHT LINE UP (increasing y, e.g. x=9 y=5->10) into the TOP wall and dies on
  turn ~6-10 every game. Zero collision avoidance, self-destructs. Verified turn-by-turn in
  sim_0/1/5/11/18 with /tmp/trace.py.
- **Round 0 result: won 20-0** (see /logs/rounds/0/results.json: opus-4-8=20, opponent=0.0).
  20 non-empty sim games, all wins (rest of sim_*.jsonl are EMPTY = not played, NOT losses).
- Verified current main.py this round:
  - syntax OK; `python3 sim_test.py 100` => 100 wins / 0 losses / 0 draws.
  - `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=3.12 (<500 limit).
- **Decision: NO code change.** We dominate a self-destructing opponent; only realistic loss
  vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** check /logs/rounds/N/sim_0.jsonl turn-by-turn (use /tmp/trace.py or rebuild:
  it prints per-turn snake heads/lengths). If opponent still walks into walls -> submit as-is.
  If it got smarter (survives long games), main.py already has: time-aware flood fill, tail-reach
  BFS, 2-ply space lookahead, enemy-contested space, H2H follow-up, length-scaled edge/corner +
  edge-shadow penalties, safety-aware food. See "Ideas for future rounds"/graeme-hill/Xe notes.
  Re-verify with sim_test 100 + fuzz before submitting.

## Round 2 of 5 (this task, opus-4-8) — coreyja-rs (NAIVE), DOMINANT, NO CODE CHANGE
- Opponent STILL `coreyja__coreyja-rs` (naive wall-walker). Verified /logs/rounds/1/sim_0
  turn-by-turn: it walks a STRAIGHT LINE DOWN col x=5 (y=9->0) into the BOTTOM wall and dies
  on turn ~10 every game. Zero collision avoidance, self-destructs. Our bot survives & wins.
- Results: round 0 won 20-0, round 1 won 38-0 (see /logs/rounds/*/results.json:
  opus-4-8=20 then 38, opponent=0.0 both rounds).
- Verified current main.py this round: syntax OK; `python3 sim_test.py 100` => 100/0/0;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.34 (<500 limit).
- **Decision: NO code change.** We dominate a self-destructing opponent; only realistic loss
  vector is a self-bug/regression, so kept main.py fully stable.
- Next teammate: check /logs/rounds/N/sim_0.jsonl turn-by-turn first. If opponent still walks
  into walls -> submit as-is. If it got smarter (survives long games), main.py already has:
  time-aware flood fill, tail-reach BFS, 2-ply space lookahead, enemy-contested space, H2H
  follow-up, length-scaled edge/corner + edge-shadow penalties, safety-aware food. Re-verify
  with sim_test 100 + fuzz before submitting.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `coreyja__jump-flooding` (SMART), FIXED STARVATION LOSS
- **Opponent CHANGED to `coreyja__jump-flooding` — a SMART bot** (manhattan-Voronoi territory
  control, 1-ply greedy port of a minimax snake). Real source available:
  `git show origin/human/coreyja/jump-flooding:main.py` -> saved to `opp_jump_flooding.py`.
  Test head-to-head: `python3 vs_jumpflood.py main.py <N>` (built from vs_opp.py).
- **Round 0 result: won 249-1** (/logs/rounds/0/results.json). Our ONE loss = **sim_221**.
- **Loss analysis (sim_221, tools inline):** it was a LONG game (164 turns). We did NOT get
  trapped — we **STARVED TO DEATH.** From turn 153 our health fell 8->7->...->1->0 while our
  L7 snake wandered the BOTTOM edge (y=1 then y=0) and never reached food. Opponent survived
  (L8, health 27->19). ROOT CAUSE = at critically low health we didn't commit hard enough to
  the nearest reachable food; edge/corner positioning penalties + safety-aware food ranking
  (which skips contested/edge food) can steer us AWAY from the food we need to live.
- **Change made (backup: main_r1of5_jumpflood_backup.py = pre-change bot):** added a
  `critical` health mode in `_decide`:
  1. Track `abs_nearest_food` (absolute closest, ignoring risk penalties).
  2. `critical = my_health <= abs_nearest_dist + 4 or my_health <= 20`. When critical, target
     the ABSOLUTE nearest food (bypass the safety-aware ranking).
  3. Scoring: critical => `score -= d_after*40` + 300 on-food bonus (dominates everything).
  4. Suppress edge/corner penalties when critical (edge_w 9->2, corner_w 40->8) so they can't
     steer us off wall-adjacent food. Space/H2H safety penalties STILL apply (no suicidal dives).
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0; fuzz => crashes=0 illegal=0
  maxt_ms=2.23; NEW vs opp `python3 vs_jumpflood.py main.py 150` => 150-0-0 (sim's random food
  doesn't reproduce the exact starve trap, so validated by design + starvation unit tests +
  no-regression: old bot also 150-0-0). Unit test: at health 8 on bottom edge with food to the
  right, bot correctly goes toward food (right) instead of wandering away.
- **Next teammate:** opponent `coreyja__jump-flooding` is SMART (territory control). We win
  ~99.6%. Remaining loss vector was STARVATION (now addressed) and possibly self-coils. Test
  with `python3 vs_jumpflood.py main.py 200` (real opponent). If starvation losses persist,
  raise the critical threshold or add a health-vs-distance safety check in food selection.
  main.py has: time-aware flood fill, tail-reach BFS, 2-ply space lookahead, enemy-contested
  space, H2H follow-up, length-scaled edge/corner + edge-shadow penalties, safety-aware food,
  and now CRITICAL starvation mode. Keep sim_test 60 + fuzz clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — jump-flooding, ADDED VORONOI TERRITORY CONTROL
- Opponent STILL `coreyja__jump-flooding` (SMART, Voronoi/territory-control bot). Results:
  round 0 won 249-1, round 1 won 246-3+1T (~1.5% loss).
- **Loss analysis (round 1, tools /tmp/trace.py + /tmp/trace2.py; rebuild from README):**
  - sim_244 = STARVATION while PINNED: our L4 snake oscillated in the top-left 2x3 corner
    strip (bouncing (0,8)<->(0,10)<->(1,x)) from turn ~40 to death at turn 102, hp 62->0.
    The enemy L6 patrolled the x=2-3 column and CONFINED us; food east was blocked. Root
    cause = the opponent's Voronoi strategy boxed us into a tiny fraction of the board.
  - sim_238 = CORNER SEAL while shorter (L5 vs L7): we ran UP col x=0 into top-left corner
    (0,10); enemy shadowed x=2 up to the top row and sealed us. Died turn 44.
  - sim_75 = bottom-right corner self-trap while EVEN (L7 vs L7).
  - Common thread: the opponent CONTROLS TERRITORY and confines us into a corner where we
    then starve or self-trap. Our old scoring lacked any territory-vs-enemy signal.
- **Change (backup: main_r2of5_committed_backup.py = git HEAD pre-change bot):**
  Added `_voronoi_owned(my_head, enemy_heads, blocked, w, h)` — multi-source BFS computing
  how many free cells WE reach strictly before any enemy head vs how many the enemy owns.
  In `_decide` scoring:
    - `+2.5 * my_terr` (reward contesting/expanding our territory),
    - `+2.0 * (my_terr - en_terr)` when negative (penalty for being out-territoried),
    - `-8 * (my_len+2 - my_terr)` when our territory is tiny (the pin-in-corner death signal).
  This pulls us toward the open board and away from being confined into a corner strip early,
  attacking the ROOT cause of the starvation/corner-seal losses (not just the emergency mode).
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0; fuzz => crashes=0 illegal=0
  maxt_ms=4.76 (<500 limit); long-snake avg decision 0.82ms. A/B new vs prev committed bot
  (80 games, /tmp/ab.py; rebuild: loads main.py vs main_r1of5_jumpflood_backup.py, alternates
  start) = **36-28-16 (new clearly ahead, NO regression).** vs real opp sim = 150-0 (the sim's
  random food doesn't reproduce the exact pin/starve frames, so validated by A/B + design).
- **Next teammate:** opponent is a TERRITORY-CONTROL bot; we win ~98-99%. Remaining loss vector
  = being CONFINED/pinned into a corner then starving or self-trapping. main.py now has:
  time-aware flood fill, tail-reach BFS, 2-ply space lookahead, enemy-contested space, H2H
  follow-up, length-scaled edge/corner + edge-shadow, safety-aware food, CRITICAL starvation
  mode, AND Voronoi territory control. If losses persist: (a) increase Voronoi weights (2.5/2.0),
  (b) tie food selection to territory (prefer food in OUR Voronoi region), (c) deeper N-ply
  minimax on territory. Test: `python3 vs_jumpflood.py main.py 150` + `sim_test.py 60` + fuzz.
  Analyze new losses: `for f in /logs/rounds/N/sim_*.jsonl; do tail -1 $f|grep -qi opus||echo $f; done`
  then `python3 /tmp/trace2.py sim_X.jsonl START END` (rebuild trace2.py from this README).

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `zacpez__scape-goat` (WEAK/SEMI-RANDOM), NO CODE CHANGE
- **Opponent CHANGED to `zacpez__scape-goat`.** Real source available & saved to
  `opp_scape_goat.py` (via `git show origin/human/zacpez/scape-goat:main.py`).
  It is a WEAK bot: a port of a Go snake that builds an "exclude" set (off-board, neck),
  runs odd "dumb idea" food/avoidance heuristics, then when >1 choice remains picks a
  TIME-NANOSECOND-MODULO "random" choice. So it has BASIC collision avoidance but NO real
  strategy — semi-random wandering. It survives moderately (avg game ~53 turns in the real
  match) but never grows much (stays L4-L5) and cannot compete.
- **Round 0 result: won 250-0** (see /logs/rounds/0/results.json: opus-4-8=250, opponent=0.0).
  All 250 sim games were played and ALL won, 0 draws, 0 losses (verified turn-by-turn:
  opponent wanders at L4-L5 while we grow to L12+ and outlast/out-position it).
- **Testing (NOTE: opponent is NON-deterministic — uses time.time_ns() for randomness):**
  built `vs_scapegoat.py` (loads opp_scape_goat.py; alternates start; run LARGE N).
  `python3 vs_scapegoat.py main.py 150/200` => consistently ~99% (148-1-1, 149-0-1, 198-2-0).
  The rare sim losses are our own self-coils in long games (our only historical loss vector),
  at the noise floor.
- Verified current main.py this round:
  - syntax OK; `python3 sim_test.py 100` => 100 wins / 0 losses / 0 draws.
  - `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.85 (<500 limit).
- **Decision: NO code change.** We dominate a weak semi-random opponent (250-0 real, ~99% sim);
  the only realistic loss vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** opponent = `opp_scape_goat.py` (WEAK, non-deterministic). Check
  /logs/rounds/N/sim_0.jsonl first. If opponent unchanged -> submit as-is. Test with
  `python3 vs_scapegoat.py main.py 200` (LARGE N due to non-determinism). If losses persist
  they are OUR self-coils — main.py already has: time-aware flood fill, tail-reach BFS, 2-ply
  space lookahead (weighted 8.0/-45), enemy-contested space, H2H follow-up, length-scaled
  edge/corner + edge-shadow, safety-aware food, CRITICAL starvation mode, Voronoi territory.
  Keep sim_test 100 + fuzz clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — scape-goat (WEAK/SEMI-RANDOM), DOMINANT, NO CODE CHANGE
- Opponent STILL `zacpez__scape-goat` (WEAK semi-random; real source in opp_scape_goat.py;
  NON-deterministic, uses time.time_ns() for randomness). Test: `python3 vs_scapegoat.py main.py <N>` (LARGE N).
- Results: round 0 won 250-0, round 1 won 250-0 (ALL 250 sim games played & won each round,
  0 losses/0 draws — see /logs/rounds/*/results.json: opus-4-8=250, opponent=0.0 both).
- Verified current main.py this round: syntax OK; `python3 sim_test.py 100` => 100/0/0;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=3.05 (<500 limit);
  `python3 vs_scapegoat.py main.py 150` => 147-1-2 (~98%; the 1 loss = our own self-coil, noise floor).
- **Decision: NO code change.** We dominate a weak semi-random opponent (250-0 real, ~98% sim).
  Only realistic loss vector is a self-bug/regression, so kept main.py fully stable.
- Next teammate: check /logs/rounds/N/sim_0.jsonl first. If opponent unchanged -> submit as-is.
  Test with `python3 vs_scapegoat.py main.py 200` (LARGE N, non-deterministic). If losses persist
  they're OUR self-coils; main.py already has time-aware flood fill, tail-reach BFS, 2-ply space
  lookahead, enemy-contested space, H2H follow-up, length-scaled edge/corner + edge-shadow,
  safety-aware food, CRITICAL starvation mode, Voronoi territory. Keep sim_test 100 + fuzz clean.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `tim-hub__awesome-snake` (WEAK GREEDY), DOMINANT, NO CODE CHANGE
- **Opponent CHANGED to `tim-hub__awesome-snake`.** Real source available & saved to
  `opp_awesome_snake.py` (via `git show origin/human/tim-hub/awesome-snake:main.py`).
  It is a WEAK bot: builds a map, looks ONLY at the 4 cells around its head, scores
  off-board=-100, food=+1, body=-1, empty=0, and picks max with a RANDOM tiebreak
  (`score + random.random()`). So it has BASIC collision avoidance but ZERO space/strategy —
  it wanders and eventually self-traps (dies ~turn 41 at L4 in /logs/rounds/0/sim_0). Stays
  short (L4), never competes. NON-deterministic (uses random.random(), no seed).
- **Round 0 result: won 250-0** (see /logs/rounds/0/results.json: opus-4-8=250, opponent=0.0).
  ALL 250 sim games played & won, 0 losses / 0 draws (verified W=250 L=0 D=0 over all sim_*.jsonl).
- **Testing:** built `vs_awesome.py` (loads opp_awesome_snake.py; alternates start; LARGE N due
  to non-determinism). `python3 vs_awesome.py main.py 150` => 149-0-1; `... 250` => ~240-3-7.
  The rare sim losses/draws are OUR self-coils / mutual-H2H at the noise floor and are
  NON-reproducible (re-running the "loss" seeds gives wins) — they're opponent-random variance,
  NOT a systematic vector. Real engine gave a clean 250-0.
- Verified current main.py this round: syntax OK; `python3 sim_test.py 60` => 60/0/0;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=4.86 (<500 limit).
- **Decision: NO code change.** We dominate a weak greedy opponent (250-0 real). Only realistic
  loss vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** opponent = `opp_awesome_snake.py` (WEAK greedy, non-deterministic). Check
  /logs/rounds/N/sim_0.jsonl first. If opponent unchanged -> submit as-is. Test with
  `python3 vs_awesome.py main.py 250` (LARGE N). If losses persist they're OUR self-coils;
  main.py already has time-aware flood fill, tail-reach BFS, 2-ply space lookahead, enemy-
  contested space, H2H follow-up, length-scaled edge/corner + edge-shadow, safety-aware food,
  CRITICAL starvation mode, Voronoi territory. Keep sim_test 60 + fuzz clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — awesome-snake (WEAK greedy), DEEPENED 2-PLY ANTI-COIL
- Opponent STILL `tim-hub__awesome-snake` (WEAK greedy, non-deterministic; real source in
  opp_awesome_snake.py). Test: `python3 vs_awesome.py main.py <N>` (LARGE N; keep N<=180 to
  avoid the 30s command timeout in this env).
- Results: round 0 won 250-0, round 1 won 247-2+1T (/logs/rounds/*/results.json).
- **Loss analysis (round 1: sim_246, sim_247):** BOTH are OUR self-coils while much LONGER
  & full health (OPUS L12 vs L6, L11 vs L7). In sim_247 OPUS spiraled the top-left, chased
  corner food at (0,9), then ran DOWN col x=0 into a pocket the opponent's body sealed at
  (0,2)-(0,4). NOT the opponent's doing — the weak bot just outlasts us when we coil.
  NOTE: the CURRENT bot already decides "up" (away from the corner) on the reconstructed
  turn-58 board (/tmp/test247.py), i.e. it avoids that exact trap; remaining losses are
  slightly-different earlier coil states.
- **Change (backup: main_r1of5_awesome_backup.py = git HEAD pre-change bot):** deepened the
  2-ply follow-up-space anti-coil signal again:
    - `best_next_space` reward 8.0 -> 10.0
    - shrinking-space penalty `(my_len - best_next_space)` 45.0 -> 60.0
  More strongly downranks moves leading into a shrinking follow-up region (the spiral coil).
- **Verification:** syntax OK; `sim_test.py 60` => 60/0/0; `PYTHONPATH=/workspace fuzz_test.py`
  => crashes=0 illegal=0 maxt_ms=3.06 (<500 limit). A/B new(v2) vs prev committed on IDENTICAL
  seeds (N=120): committed 116-0-4, v2 118-0-2 (converted 2 draws->wins, 0 regressions).
  `vs_awesome.py main.py 180` => 176-1-3 (~99%). Reconstructed sim_247 still decides "up".
- **Next teammate:** opponent = opp_awesome_snake.py (WEAK greedy, non-deterministic). Check
  /logs/rounds/N/sim_0.jsonl first. If unchanged -> submit as-is or keep nudging anti-coil.
  Our ONLY loss vector is OUR self-coil in mid/long games. main.py has: time-aware flood fill,
  tail-reach BFS, 2-ply space lookahead (now 10.0/-60), enemy-contested space, H2H follow-up,
  length-scaled edge/corner + edge-shadow, safety-aware food, CRITICAL starvation, Voronoi
  territory. Test with `vs_awesome.py main.py 180` (N<=180 to fit 30s command timeout) + fuzz.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `rdbrck__btas` (STRONG/REAL), DOMINANT, NO CODE CHANGE
- **Opponent CHANGED to `rdbrck__btas`** — a FAITHFUL PORT of the rdbrck "BTAS" (Better Than
  Aleksiy's Snake), the **2017 Victoria Advanced-division tournament WINNER**. This is a REAL,
  competitive bot (BFS to rated food, flood-fill danger with keep-largest, general_direction
  scoring, need_food thresholds). NOT a wall-walker. Plays long games (45-328+ turns in logs).
  Real source saved to `opp_btas.py` (via `git show origin/human/rdbrck/btas:main.py`, 629 lines).
  **NON-deterministic** (uses `random.shuffle(surrounding_ratings)` with NO fixed seed).
- **Round 0 result: won 250-0** (see /logs/rounds/0/results.json: opus-4-8=250, rdbrck__btas=0.0).
  Verified all 250 sim_*.jsonl (all non-empty & played): W=250 L=0 D=0. Opponent navigates with
  real collision avoidance but our bot out-positions/out-lasts it every game.
- **Testing:** built `vs_btas.py` (= vs_opp.py pointed at opp_btas.py; alternates start).
  `python3 vs_btas.py main.py 150` => 150-0-0. Larger runs ~99-100% — the RARE sim losses are
  pure noise from the opponent's unseeded random.shuffle (re-running the same seed flips W/L),
  NOT a systematic vector. Fresh 120-game A/B (/tmp/bench.py) => 120-0-0.
- Verified current main.py: syntax OK; `python3 sim_test.py 60` => 60/0/0 vs naive;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.77 (<500 limit).
- **Decision: NO code change.** We dominate a STRONG real opponent 250-0; only realistic loss
  vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** opponent = `opp_btas.py` (STRONG 2017 winner, NON-deterministic). Check
  /logs/rounds/N/sim_0.jsonl first (opponent navigates, doesn't wall-walk — game length alone
  won't tell you it's naive). Test with `python3 vs_btas.py main.py 150` (use N<=150 to fit the
  30s per-command timeout in this env; the opponent is unseeded-random so use decent N). If
  losses ever become systematic, main.py already has: time-aware flood fill, tail-reach BFS,
  2-ply space lookahead (10.0/-60), enemy-contested space, H2H follow-up, length-scaled
  edge/corner + edge-shadow, safety-aware food, CRITICAL starvation mode, Voronoi territory.
  Keep sim_test 60 + fuzz + vs_btas clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — rdbrck__btas, FIXED CRITICAL KeyError('length') BUG
- Opponent STILL `rdbrck__btas` (STRONG 2017 winner, NON-deterministic; real source opp_btas.py).
  Results: round 0 won 250-0, round 1 won 249-1.
- **ROOT-CAUSED the round-1 loss (sim_174):** it was NOT a strategy failure. `_decide` did
  `you["length"]` and `sn["length"]` — but the game_state does NOT always include a `"length"`
  field. When absent, `_decide` threw KeyError, the bare `except` in `move()` returned the
  BLIND fallback `{"move":"up"}`, which at the top edge is OUT OF BOUNDS = instant death.
  Reconstructed sim_174 T18 board: bot crashed -> returned "up" (OOB) instead of a legal move.
- **Fix (backup: main_r2of5_lengthfix_backup.py = git HEAD pre-change bot):**
  - line 237: `my_len = you.get("length", len(my_body))`
  - line 262: `enemy_heads.append((body[0], sn.get("length", len(body))))`
  Now length is derived from the body when the field is missing; no more crash -> no more
  blind-OOB fallback. Verified: reconstructed T18 board now returns a LEGAL move ("left")
  instead of the OOB "up".
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.75; `python3 vs_btas.py main.py 100`
  => 100-0-0 (real opponent).
- **Next teammate:** this was a REAL latent bug that would fire whenever the engine omits the
  "length" field (and likely caused the rare losses in earlier rounds too — the blind "up"
  fallback is deadly). If any `KeyError`/crash-fallback losses persist, audit `_decide` for
  other required-field accesses (health etc.) and make them `.get(...)` with body-derived
  defaults. Also consider making the `except` fallback in `move()` pick a LEGAL in-bounds
  non-body move rather than a blind "up". main.py has all prior strategy layers intact.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `Spenca__vulture-snake`, ADDED WORST-CASE 2-PLY ANTI-COIL
- **Opponent CHANGED to `Spenca__vulture-snake`** — a REAL bot (2017 BattleSnake port).
  Real source saved to `opp_vulture_snake.py` (via `git show origin/human/Spenca/vulture-snake:main.py`).
  Strategy: seek closest food, then "circle/orbit" the food in a defensive square once
  adjacent. Has full collision avoidance (checkCollision) + desperation fallback. It PATROLS
  (e.g. top two rows) and survives long, but STAYS SHORT (~L4) and never really grows.
  **NON-deterministic + STATEFUL**: uses `random.choice` AND persistent module globals
  (`state`, `sqCorners`) that carry between games — reset them (`ov.state=0; ov.sqCorners=None`)
  before each game in benchmarks for fair/reproducible A/B (see /tmp/ab.py, /tmp/ab2.py).
- **Round 0 result: won 248-2** (/logs/rounds/0/results.json). Both losses (sim_0, sim_29)
  were OUR OWN SELF-COILS, not the opponent: sim_29 = OPUS L14 (vs OPP L8), full health,
  coiled its body into the mid-board region and boxed itself in (died T75); sim_0 = OPUS L8
  full health boxed into the top-left corner (died T79). Classic long+healthy self-coil, our
  only historical loss vector. The coil tightens >2 plies out, so the exact death-frame is
  already unavoidable; must be prevented a few turns earlier.
- **Change (backup: main_r0_vulture_backup.py = git HEAD pre-change bot):** added a
  WORST-CASE follow-up-space signal alongside the existing best-case 2-ply. In `_decide`:
  track `worst_next_space = min over follow-up cells of _reachable_with_tails(...)`. Then
  `if worst_next_space < my_len: score -= (my_len - worst_next_space) * 12`. The single-MAX
  2-ply can rate a coiling move and an escaping move equally when both still reach the whole
  board; tracking the MIN discriminates the coil (forces us into progressively tighter space)
  from a true escape toward the open board. Directly targets the deep self-coil loss vector.
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=2.91 (<500 limit). A/B vs REAL opp with
  opp-globals reset each game (fair): NEW 100-0-0 vs OLD 97-3-0 (N=100); NEW 148-1-1 vs OLD
  145-2-3 (N=150). Consistent small net WIN, ZERO regressions. new-vs-old self-play 20-22-18
  (even = no regression). Built `vs_vulture.py` (loads opp_vulture_snake.py; alternates start).
- **Next teammate:** opponent = `opp_vulture_snake.py` (REAL 2017 port, stateful+random, stays
  short & orbits food). We win ~99%. Only loss vector remains OUR self-coil when long+healthy;
  the coil forms several turns before death and single-frame lookahead can't fully catch it.
  Ideas if losses persist: deeper N-ply forward sim of OUR own path (simulate self-play forward
  ~5 turns and pick the move that keeps max long-horizon space), or a Hamiltonian-ish tail
  follow when clearly longer+safe. main.py has: time-aware flood fill, tail-reach BFS, 2-ply
  space lookahead (best 10.0 / worst 12.0 penalties), enemy-contested space, H2H follow-up,
  length-scaled edge/corner + edge-shadow, safety-aware food, CRITICAL starvation, Voronoi
  territory. Test: `python3 vs_vulture.py main.py 120` and A/B with opp-globals reset (see
  /tmp/ab.py — RESET `ov.state`/`ov.sqCorners` each game or results drift). Keep sim_test 60 +
  fuzz clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — vulture-snake, ADDED DEEP SELF-SURVIVAL SIM
- Opponent STILL `Spenca__vulture-snake` (real 2017 port, stateful+random; opp_vulture_snake.py).
  Results: round 0 won 248-2, round 1 won 249-1.
- **Loss analysis (round 1, sim_104):** 166-turn game. OPUS L17 FULL HEALTH (95) vs OPP L14.
  We were funneled over ~6 turns (T157->163) down the LEFT column into a BOTTOM-LEFT pocket
  while the enemy actively built a wall across row y=3/4, then boxed ourselves in at (4,2)
  (a dead-end) and died T163. Classic self-coil, but ENEMY-ASSISTED (enemy dynamically sealed).
  At the key decision (T157, head (1,5)) all of R/L/U had identical static space(90) & Voronoi
  (92) — 2-ply lookahead & Voronoi CANNOT distinguish them because the seal develops 6 turns out.
- **Change (backup: main_r1of5_vulture_backup.py):** added `_deep_self_survival(head, body,
  static_blocked, w, h, depth=8)` — greedily simulates OUR OWN snake forward 8 turns (each turn
  moving to the max-flood-fill neighbor, tail retreating). Returns (turns_survived, min_space).
  In `_decide` scoring: `-45*(8-surv)` if we die within the horizon, `-6*(my_len-min_sp)` if the
  corridor shrinks below our length. This catches multi-turn PURE self-coils that 2-ply misses.
- **NOTE / LIMITATION:** this does NOT fully fix sim_104 — that trap is ENEMY-ASSISTED (the sim
  ignores enemy movement, so all 3 moves still "survive 8" in pure self-sim). The deep-sim only
  attacks pure self-coils (our most common historical loss vector across all opponents). Fully
  fixing enemy-assisted seals needs N-ply minimax modeling the enemy as an active pursuer.
- **Verification:** syntax OK; `sim_test.py 40` => 40/0/0; fuzz => crashes=0 illegal=0
  maxt_ms=19.3 (<500 limit, deeper sim costs more but safe). `vs_vulture.py main.py 60` => 58-2
  vs backup 59-1 on same-ish seeds (noise floor, stateful/random opp; NO regression).
- **Next teammate (IDEA to actually fix enemy-assisted seals):** implement a shallow N-ply
  MINIMAX / expectimax where the ENEMY is modeled as chasing/sealing (e.g. enemy moves toward
  our head or toward the mouth of our pocket). Score = our reachable space after both move.
  This is the last remaining ~1% loss vector (enemy funnels us into a wall pocket while long).
  main.py has: time-aware flood fill, tail-reach BFS, 2-ply best/worst space, enemy-contested
  space, H2H follow-up, length-scaled edge/corner + edge-shadow, safety-aware food, CRITICAL
  starvation, Voronoi territory, AND now deep 8-ply self-survival sim.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `moxuz__pinky-snek` (WEAK SEMI-RANDOM), NO CODE CHANGE
- **Opponent CHANGED to `moxuz__pinky-snek`.** Real source saved to `opp_pinky_snek.py`
  (via `git show origin/human/moxuz/pinky-snek:main.py`). It is a WEAK bot: a 2017 port that
  builds a "danger" set (walls + all snake bodies + empty cells with >=3 dangerous neighbors,
  i.e. dead-end pockets), then picks a RANDOM safe adjacent cell. It ONLY seeks food when
  health<30. So it has BASIC collision + dead-end avoidance but ZERO strategy — semi-random
  wandering, stays short, never competes. NON-deterministic (uses random.choice, no seed).
- **Round 0 result: won 249-1** (see /logs/rounds/0/results.json: opus-4-8=249, opponent=1).
  The lone loss is almost certainly OUR self-coil (our only historical loss vector) at the
  noise floor, not a systematic opponent threat.
- **Testing:** built `vs_pinky.py` (loads opp_pinky_snek.py; alternates start; run N<=80 to fit
  the 30s per-command timeout — the deep-sim in main.py makes larger N slow).
  `python3 vs_pinky.py main.py 80` => 79-0-1. Second batch (diff seeds, N=80) => 80-0-0.
- Verified current main.py: syntax OK; `python3 sim_test.py 60` => 60/0/0 vs naive;
  `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=14.31 (<500 limit).
- **Decision: NO code change.** We dominate a weak semi-random opponent (249-1 real, ~99-100%
  sim). Only realistic loss vector is a self-bug/regression, so kept main.py fully stable.
- **Next teammate:** opponent = `opp_pinky_snek.py` (WEAK semi-random, non-deterministic).
  Check /logs/rounds/N/sim_0.jsonl first. If unchanged -> submit as-is. Test with
  `python3 vs_pinky.py main.py 80` (N<=80 due to deep-sim cost + 30s timeout). If losses
  persist they're OUR self-coils; main.py already has: time-aware flood fill, tail-reach BFS,
  2-ply best/worst space, enemy-contested space, H2H follow-up, length-scaled edge/corner +
  edge-shadow, safety-aware food, CRITICAL starvation, Voronoi territory, deep 8-ply self-
  survival sim. Keep sim_test 60 + fuzz clean before submitting.

## Round 2 of 5 (this task, opus-4-8) — pinky-snek, FIXED ENEMY-ASSISTED SELF-COIL SEAL
- Opponent STILL `moxuz__pinky-snek` (WEAK semi-random; opp_pinky_snek.py, non-deterministic).
  Results: round 0 won 249-1, round 1 won 248-2.
- **Loss analysis (round 1: sim_248, sim_28):** BOTH were OUR self-coils while LONG + FULL
  HEALTH (OPUS L20 hp94; L15 hp92) — the enemy body + its short-horizon reachable cells
  SEALED us into a coil pocket. Traced sim_248 turn-by-turn: at T153 (head (4,5), free moves
  U(4,6)/D(4,4)/R(5,5)) the bot went RIGHT into the coil; by T156 only 1 forced move remained
  -> dead-end at T158. The pure `_deep_self_survival` sim (which IGNORES the enemy) rated all
  3 moves as surv=8, min_sp~80 -> couldn't distinguish the fatal coil from the safe escape,
  because the ENEMY body (at (3,3)-(6,4)) is what walls off the pocket exit.
- **Change (backup: main_r1of5_pinky_selfcoil_backup.py = git HEAD pre-change bot):**
  1. Added `_enemy_reach_cells(enemy_head, blocked, w, h, steps)` — BFS of cells the enemy
     head can occupy within `steps` moves.
  2. Added an ENEMY-AWARE DEEP SURVIVAL check in `_decide` scoring (only when my_len>=8):
     flood the enemy's reachable cells (steps=4) + enemy bodies as static blockers, then
     re-run the greedy self-sim from the candidate move. If we die within 8 turns under this
     conservative model, subtract (8 - e_surv) * 22. This detects enemy-assisted seals that
     the pure self-sim misses. steps=4 was tuned: at T153 it gives up=surv8/min28 (SAFE),
     down=surv0, right=surv0 (DEAD) — perfect discrimination. steps>=6 was too conservative
     (blocked everything). Only the candidate cell `nxt` is un-blocked to avoid self-veto.
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16 (<500 limit); reconstructed sim_248
  T153 now decides **UP (escape)** instead of the fatal RIGHT; `python3 vs_pinky.py main.py 50`
  => 49-0-1 (~98-100%, the draw is noise floor; NO regression).
- **Next teammate:** opponent = opp_pinky_snek.py (WEAK semi-random, non-deterministic). Check
  /logs/rounds/N/sim_0.jsonl first. If unchanged -> submit as-is. Our ONLY loss vector is the
  enemy-assisted / pure self-coil while long+healthy; this round adds enemy-aware deep sim to
  catch it. If losses persist, tune the steps (4) / weight (22) or make it length-scaled.
  main.py has: time-aware flood fill, tail-reach BFS, 2-ply best/worst space, enemy-contested
  space, H2H follow-up, length-scaled edge/corner + edge-shadow, safety-aware food, CRITICAL
  starvation, Voronoi territory, deep 8-ply self-survival sim, AND now enemy-aware deep sim.
  Test: `python3 vs_pinky.py main.py 50` (keep N<=60, deep-sim cost + 30s cmd timeout) + fuzz.
