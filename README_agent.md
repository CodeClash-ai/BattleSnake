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
