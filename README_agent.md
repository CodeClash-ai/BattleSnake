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

## Round 1 (this task, opus-4-8) — NEW OPPONENT `coreyja__amphibious-arthur`, FIXED CHRONIC SELF-COIL-WHILE-LONG
- **Opponent = `coreyja__amphibious-arthur`** (real bot, source in `opp_amphibious_arthur.py`).
  It seeks health~80 via recursive neighbor scoring; survives passively, stays SHORT (L6-23).
- **Round 0 result: won 228-21 +1 tie** (/logs/rounds/0/results.json). ~8% loss rate.
- **Loss analysis (all 21 losses, /tmp/analyze.py):** UNAMBIGUOUS — in EVERY loss WE were
  MUCH LONGER (L15-44!) with HIGH health (78-100) while the opponent stayed L6-23. We die by
  SELF-COILING / boxing ourselves in (deaths at corners (0,0),(10,10), edges). The opponent
  wins purely by outlasting us when we grow too big to manage our own body. Our chronic
  self-coil-while-long vector, amplified because we grow to EXTREME lengths (L30-44).
- **Changes (backup: main_r0_arthur_backup.py = git HEAD pre-change bot):**
  1. **STOP GROWING when clearly ahead:** new flag `clearly_ahead = not starving and
     my_len >= max_enemy_len+4 and my_len >= 10`. When set, food scoring AVOIDS food
     (-25 if landing on it, + small reward for distance). Extra length past a solid lead
     only increases self-coil risk vs this passive short opponent, so we keep the body short.
  2. **Length-adaptive deep-survival depth:** `deep_depth = min(20, max(8, my_len//2))`
     (was fixed 8). At L30-44 an 8-ply horizon can't see the coil; scaling depth lets the
     anti-coil sim detect traps that develop 10-20 turns out. Verified L40 decision = 0.1ms.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=15.95 (<500 limit); L40 board decision
  0.1ms. Built `vs_arthur.py` (loads opp_amphibious_arthur.py; alternates start). NOTE: vs_arthur
  runs SLOW because when we stop eating games run to the 500-turn timeout (both survive), so
  N>~20 exceeds the 30s command timeout — run in background: `nohup python3 vs_arthur.py
  main.py 40 > /tmp/out.txt 2>&1 &` then poll the file. Couldn't get the full A/B number before
  step limit; the changes are validated by design (directly target the confirmed loss vector),
  sim_test, fuzz, and timing.
- **Next teammate:** opponent = opp_amphibious_arthur.py (passive, stays short). Our ONLY loss
  vector is self-coil while LONG+healthy. If losses persist: (a) lower the clearly_ahead length
  threshold or make it stop eating even earlier, (b) consider a Hamiltonian-ish tail-follow when
  clearly ahead (cycle the board safely rather than coiling), (c) push deep_depth higher / add
  a periodic "unwind" toward open center when long. Test with `vs_arthur.py` (background, poll
  file). Keep sim_test + fuzz clean. main.py has all prior layers: time-aware flood fill,
  tail-reach BFS, 2-ply best/worst space, enemy-contested space, H2H follow-up, length-scaled
  edge/corner + edge-shadow, safety-aware food, CRITICAL starvation, Voronoi territory, deep
  self-survival sim (now length-adaptive), enemy-aware deep sim, and clearly_ahead food-avoid.

## Round 2 of 5 (this task, opus-4-8) — amphibious-arthur, STRENGTHENED ANTI-OVERGROWTH
- Opponent STILL `coreyja__amphibious-arthur` (passive, stays SHORT L6-23; opp_amphibious_arthur.py).
- Results: round 0 won 228-21+1T, round 1 won 227-23 (~9% loss). Round-0 clearly_ahead fix
  did NOT move the needle much (21 -> 23 losses).
- **Loss analysis (all 23 round-1 losses, inline script):** UNAMBIGUOUS & unchanged — in EVERY
  loss WE were LONGER (L11-38, mostly L20-32) with HIGH health (76-100), self-coiled into a
  corner/edge/pocket and boxed ourselves in. Deaths at T131-477, many at corners (0,0)/(10,10)/
  edges. The opponent (short L5-26) just outlasts us when we grow too big to manage our body.
  Our clearly_ahead food-avoid (-25) was TOO WEAK: we still grew to L20-38.
- **Change (backup: main_r1of5_arthur_r2_backup.py = git HEAD pre-change bot):**
  1. clearly_ahead triggers EARLIER: `my_len >= max_enemy_len+3 and my_len >= 8` (was +4, >=10).
     Stop growing sooner so we never reach the dangerous L20-38 range vs this short opponent.
  2. clearly_ahead food AVOIDANCE much stronger: landing on food -120 (was -25); reward
     keeping distance `min(d_after,6)*4.0` (was d_after*0.4). Makes not-eating dominant over
     the mild pull toward nearby food, so we actually stay short & manageable.
  Safety/space/H2H/tail-reach signals still dominate over food (space*10/unit, tail_reach
  +120/-200, H2H -1000), so this only removes GROWTH pressure — no suicidal food-refusal.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.0 (<500 limit). A/B vs real opp is
  SLOW (when we stop eating, games run to the 500-turn timeout — 30 games > 30s cmd timeout;
  use `nohup python3 vs_arthur.py main.py 30 > /tmp/out &` and poll). Crude capped-sim length
  test (opponent NOT accurately modeled): both bots ~L12-20 avg (sim food dynamics differ from
  real; the real losses are in T200-477 games this cap truncates). Fix validated by DESIGN
  (directly cuts the confirmed overgrowth->self-coil vector) + sim_test + fuzz + no-regression.
- **Next teammate:** opponent = opp_amphibious_arthur.py (passive, stays short). Our ONLY loss
  vector remains self-coil while LONG. If losses persist despite lower growth: (a) drop
  clearly_ahead threshold further (+2 / >=7), (b) implement a Hamiltonian-ish tail-follow when
  clearly ahead (cycle the board safely instead of coiling — this is the real fix and is still
  NOT implemented), (c) push deep_depth higher. Test with vs_arthur.py IN BACKGROUND (poll file)
  since games run long. main.py has all prior layers: time-aware flood fill, tail-reach BFS,
  2-ply best/worst space, enemy-contested space, H2H follow-up, length-scaled edge/corner +
  edge-shadow, safety-aware food, CRITICAL starvation, Voronoi territory, deep self-survival
  sim (length-adaptive), enemy-aware deep sim, clearly_ahead food-avoid (now much stronger).

## Round 1 of 5 (this task, opus-4-8) — NEW STRONG OPPONENT `OliverMKing__astar-snake`, STRENGTHENED ANTI-COIL
- **Opponent CHANGED to `OliverMKing__astar-snake` — a STRONG, REAL bot** (A* to food/tail,
  flood-fill dead-end avoidance, tail-chasing, danger prediction). Source saved to
  `opp_astar_snake.py` (git show origin/human/OliverMKing/astar-snake:main.py, 526 lines).
  NOT a wall-walker — plays LONG competitive games (median death turn 234). Test harness:
  `vs_astar.py` (loads opp_astar_snake.py; alternates start). NOTE: games run SLOW (both
  bots survive long + our deep-sim depth up to 20), so N>~16 exceeds the 30s command timeout;
  run in BACKGROUND: `nohup python3 vs_astar.py main.py 30 > /tmp/vsa.txt 2>&1 &` then poll.
- **Round 0 result: won 139-106, 5 ties** — CLOSE match (~56% win). This is our TOUGHEST
  opponent yet. Analysis tools: /tmp/losses3.py (death turn/len/location), /tmp/losses4.py
  (death cause), /tmp/lentime.py (max-len wins vs losses).
- **Loss analysis (all 106 losses):**
  - Death cause: **88/106 = BOXED IN** (boxed_wall+body 57, boxed_body 31), h2h 15, starve 3.
  - We were SHORTER at death 60/106, EQUAL 14, LONGER 32 (median len diff -1).
  - BUT max-length reached is ~SAME in wins (median 24) and losses (median 23) — so length is
    NOT the differentiator. **The problem is SPACE MANAGEMENT / SELF-COILING in long games**
    against an opponent that actively chases its tail and contests territory.
- **Change made (backup: main_r0_astar_backup.py = git HEAD pre-change bot):** strengthened
  the WORST-CASE 2-ply anti-coil penalty, since boxing-in is 88/106 of losses:
    - `(my_len - worst_next_space) * 12.0  ->  * 30.0`  (line ~545)
  This more strongly downranks moves whose TIGHTEST follow-up corridor is smaller than our
  body — the direct coil signal (a move that still reaches open board via one neighbor but
  funnels into a tight pocket via another). It was weak (12) relative to best_next_space (60).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0 vs naive; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=15.87 (<500 limit). A/B vs real astar was
  RUNNING at submit (slow); change validated by design (directly targets the 88/106 box-in loss
  vector) + sim_test + fuzz + no crash. A/B harness: /tmp/ab.py (NEW=main.py vs OLD=backup vs opp).
- **Next teammate:** opponent = `opp_astar_snake.py` (STRONG A*/tail-chaser, LONG games). This
  is a hard ~56% matchup and our #1 loss vector is SELF-COIL/BOX-IN in long games (88/106).
  IDEAS TO TRY (in priority order):
  1. **Run the A/B: `nohup python3 /tmp/ab.py 30 > /tmp/ab.txt &` (rebuild from README) or
     `nohup python3 vs_astar.py main.py 40 > /tmp/vsa.txt &`** to measure win-rate deltas —
     I couldn't finish it before the step limit. If worst_next_space*30 helps, push further
     (40-50) or also bump the deep-sim penalty weights (line ~568 `*45`, ~570 `*6`).
  2. **A real HAMILTONIAN-ish tail-follow when long+safe** is the canonical fix for self-coil
     and is STILL NOT IMPLEMENTED — this is likely the biggest available win. When we hold
     enough space, follow a cycle/tail rather than greedily maximizing food/space.
  3. Deeper/faster space sim (the deep-sim at depth 20 is slow but that's the horizon a coil
     needs). Consider caching or a smarter corridor detector.
  4. Reconsider `clearly_ahead` food-avoidance vs THIS opponent: astar keeps growing & tail-
     chasing; staying short may make us EASIER to trap. (But max-len is similar in wins/losses,
     so probably not the main lever.)
  Keep sim_test 40 + fuzz clean; verify decision time < 500ms (deep-sim ~16ms now, safe).

## Round 2 of 5 (this task, opus-4-8) — astar-snake, NO CODE CHANGE (weight tweak = noise)
- Opponent STILL `OliverMKing__astar-snake` (STRONG A*/tail-chaser). Results: round 0 won
  139-106+5T, round 1 won 139-101+10T (~57-58% real-match win; our TOUGHEST opponent).
- Re-confirmed loss analysis (round 1, 101 losses): shorter 53 / equal 23 / longer 25;
  median lendiff -1; median death turn 254 (LONG games); ~39% h2h-adjacent (25 of those
  while shorter, 8 equal). Dominant vector = SPACE MANAGEMENT / box-in in long games where
  we're often shorter — consistent with round-0's 88/106 boxed-in finding.
- **A/B tested a space-management weight boost** (space*10->12, worst_next_space penalty
  30->45) vs committed main.py, both vs real opp (sim harsher than real: ~40% vs 57%):
    - committed main.py: 8-9-3 (N=20)
    - variant:           8-10-2 (N=20)
  => IDENTICAL within noise (variant slightly worse). Weight tweaks are NOISE-FLOOR here,
  as prior teammates repeatedly found. **Decision: NO code change** — avoid regression risk
  on a bot that provably WINS the real match twice (139-101).
- NOTE: vs_astar.py games are SLOW (long games + deep-sim depth up to 20). N=20 ~90s; poll a
  background nohup file. Use `nohup python3 -u vs_astar.py <bot> 20 > /tmp/x.txt 2>&1 &`.
- **Next teammate — the ONLY likely real win is #2 from round-0 notes: a HAMILTONIAN-ish
  tail-follow when long+safe (cycle the board instead of greedily coiling).** This is the
  canonical fix for the box-in loss vector and is STILL NOT IMPLEMENTED. Scalar weight
  tweaks won't move the needle (proven twice now). If you attempt the Hamiltonian follow,
  gate it behind long+space-safe and A/B it carefully (background nohup, N>=30) before
  committing. main.py already has: time-aware flood fill, tail-reach BFS, 2-ply best/worst
  space, enemy-contested space, H2H follow-up, length-scaled edge/corner + edge-shadow,
  safety-aware food, CRITICAL starvation, Voronoi territory, deep self-survival sim
  (length-adaptive), enemy-aware deep sim, clearly_ahead food-avoid. Keep sim_test + fuzz clean.

## Round 1 (this task, opus-4-8) — NEW OPPONENT `nbw__nbw-ruby` (STRONG 2017 port), ADDED ANTI-WALL-HUG
- **Opponent = `nbw__nbw-ruby`** — faithful port of nbw's 2017 "Ereptile Disruption" bot
  (grid painter + tree/BFD path search, TREE_LEVELS=5). Real source saved to `opp_nbw_ruby.py`
  (git show origin/human/nbw/nbw-ruby:main.py, 633 lines). STRONG, real avoidance, GROWS LARGE
  (L17-35), plays LONG games. Test: `python3 vs_nbw.py main.py <N>` (created; N<=16 for 30s timeout).
- **Round 0 result: won 230-16 +4T** (~93.5%). Analyzed all 16 losses (/tmp/analyze2.py,
  /tmp/death.py, /tmp/death2.py): ALL are LONG games where OPUS died with HIGH health (86-97)
  by SELF-COILING / WALL-HUGGING into a corner/edge while a comparable-or-longer enemy (L15-35)
  SEALED the pocket. Canonical: sim_92 — at T127 head (3,0) OPUS had UP=(3,1) into the open board
  FREE but chose LEFT along the bottom edge into the corner (0,0), then up col x=0, and the L17
  enemy sealed it (T133). Enemy-assisted corner seal = our chronic loss vector.
- **Change (backup: main_r0_nbwruby_backup.py = git HEAD pre-change bot):** added an
  ANTI-WALL-HUG escape bonus after the center_dist nudge in `_decide`: when `my_len>=8` AND the
  CURRENT head is on an edge AND `max_enemy_len >= my_len-2` AND not critical, REWARD moving to
  an interior (non-edge) cell (+22*len_scale) and PENALIZE moving further into a corner
  (-30*len_scale). Rationale: penalizing edges alone is swamped by flood-fill `space*10` (which
  is similar along a wall); an explicit ESCAPE bonus tips the choice toward peeling off the wall
  BEFORE we get funneled into a corner and sealed.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=15.9 (<500 limit). vs_nbw 16 => 15-1
  (same as baseline). A/B new-vs-old on identical seeds (/tmp/ab.py, N=12): both 11-1 (NEUTRAL
  in sim — the sim's random food rarely reproduces the exact corner-seal frames, as prior
  teammates repeatedly found). Change is low-risk (fires only long+on-edge+enemy-near, only
  nudges scores) and directly targets the confirmed loss vector; validated by design + no
  regression. NOTE: on the exact sim_92 T127 frame the bot STILL picks left (flood-fill space
  for left >> the +69 escape bonus) — this one board is space-dominated; the change helps the
  broader class of wall-hug approaches, not that specific already-committed frame.
- **Next teammate:** opponent = opp_nbw_ruby.py (STRONG, grows large, long games). Our ONLY loss
  vector is corner/edge SELF-COIL/SEAL while long (86-97 hp, L13-35) — 16/16 round-0 losses.
  The canonical FIX (still NOT implemented, flagged for many rounds) is a **HAMILTONIAN-ish
  tail-follow when long+safe** (cycle the board instead of coiling). Scalar edge-weight tweaks
  are noise-floor (proven repeatedly). If attempting Hamiltonian: gate behind long+space-safe,
  A/B carefully. Alternatively consider raising `space` weight LESS along edges, or increasing
  the anti-wall-hug escape bonus (currently 22). main.py has: time-aware flood fill, tail-reach
  BFS, 2-ply best/worst space, enemy-contested space, H2H follow-up, length-scaled edge/corner +
  edge-shadow, safety-aware food, CRITICAL starvation, Voronoi territory, deep self-survival sim
  (length-adaptive), enemy-aware deep sim, clearly_ahead food-avoid, AND now anti-wall-hug escape.
  Test: `python3 vs_nbw.py main.py 16` + `python3 sim_test.py 40` + fuzz. Keep all clean.

## Round 2 of 5 (this task, opus-4-8) — nbw-ruby, ADDED TAIL-FOLLOW ANTI-COIL BIAS
- Opponent STILL `nbw__nbw-ruby` (STRONG 2017 port, grows large, long games; opp_nbw_ruby.py).
- Results: round 0 won 230-16+4T, round 1 won 223-23+4T (~9% loss).
- **Loss analysis (round 1, 23 losses, /tmp/death2.py + /tmp/board.py):** UNCHANGED, unambiguous
  chronic vector — in EVERY loss OPUS died LONG (L15-33) + HIGH health (85-100) by SELF-COILING
  into a tidy packed block and boxing itself in, while the opponent just outlasts us. Canonical:
  sim_33 T174 — OPUS L18 hp94 coiled its body into a 2-3-wide vertical column (x=3-5) with the
  head buried at (5,5), open board unused to the right/top. Flood-fill/space CANNOT distinguish a
  tidy self-coil from real freedom (both reach many cells at that instant).
- **Change (backup: main_prev_committed_backup.py = git HEAD pre-change bot):** implemented a
  TAIL-FOLLOW BIAS (the canonical fix flagged unimplemented for MANY rounds). Added `_bfs_dist()`
  (plain shortest-path BFS over free cells). In `_decide` scoring, when `my_len>=8 and not
  starving and not critical and tail_reach`: `score -= _bfs_dist(nxt, my_tail, new_blocked)*2.0`.
  Rewards keeping the head close (in path distance) to the tail -> body stays a LOOSE LOOP that
  chases its tail instead of packing into a dead block. Weight 2.0 is gentle so space (x10),
  H2H, food still dominate — it only breaks ties toward the un-coiled path.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.09 (<500 limit). RECONSTRUCTED sim_33:
  at T170 (head (4,6)) the NEW bot picks RIGHT (toward open board) where the OLD bot picked DOWN
  (into the coil) — the tail-follow bias correctly peels us off the coil earlier. A/B vs real opp
  on identical seeds (N=24): NEW 23-1, OLD 23-1 (the sim's random food rarely reproduces the exact
  late-game coil frames, as prior teammates found; no regression, and the frame test confirms the
  fix engages). Low-risk: fires only long+safe+not-hungry, only nudges scores.
- **Next teammate:** opponent = opp_nbw_ruby.py (STRONG, grows large). Our ONLY loss vector is the
  long+healthy self-coil. This round adds the tail-follow bias. If losses persist: (a) raise the
  tail-follow weight (2.0 -> 3-4) but A/B carefully to avoid it fighting the food pull, (b) make it
  length-scaled, (c) a full Hamiltonian cycle when very long+safe. Test: `python3 vs_nbw.py main.py
  16` (N<=16 for 30s timeout; games long + deep-sim). Keep sim_test 40 + fuzz clean. main.py has:
  time-aware flood fill, tail-reach BFS, 2-ply best/worst space, enemy-contested space, H2H
  follow-up, length-scaled edge/corner + edge-shadow, safety-aware food, CRITICAL starvation,
  Voronoi territory, deep self-survival sim (length-adaptive), enemy-aware deep sim, clearly_ahead
  food-avoid, anti-wall-hug escape, AND now the TAIL-FOLLOW anti-coil bias.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `coreyja__eremetic-eric` (COILING TAIL-CHASER), FIXED OVERGROWTH
- **Opponent = `coreyja__eremetic-eric`** — a "coiling" snake that chases its own tail
  (small food heuristic). Real source saved to `opp_eremetic_eric.py`
  (git show origin/human/coreyja/eremetic-eric:main.py, 356 lines). It stays SHORT (L7-16),
  survives LONG (400-856 turn games), and outlasts us. Test: `python3 vs_eremetic.py main.py <N>`
  (N<=8 for 30s cmd timeout; games are LONG — use nohup+poll for larger N).
- **Round 0 result: won 241-9** (/logs/rounds/0/results.json). Analyzed all 9 losses
  (`python3 analyze_losses.py sim_X.jsonl ...`): UNAMBIGUOUS chronic vector — in EVERY loss
  OPUS grew to **L49-96** (!) in 400-856 turn games and SELF-COILED / boxed itself in on the
  121-cell 11x11 board while the opponent stayed L7-16 and outlasted us. Extreme overgrowth.
- **ROOT CAUSE of the overgrowth:** the old `clearly_ahead` food-avoidance only penalized the
  single `nearest_food` cell (-120). Over hundreds of turns we incidentally wandered onto OTHER
  food cells and kept growing to absurd lengths. Threshold was also too high (+3/>=8).
- **Changes (backup: main_r0_eremetic_backup.py = git HEAD pre-change bot):**
  1. Added `food_set = set(food)`. In the `clearly_ahead` branch, HARD-penalize landing on
     **ANY** food cell (`nxt in food_set`) by **-400** (was -120 only for nearest_food). This
     stops all incidental growth, not just growth toward the nearest food.
  2. Lowered the `clearly_ahead` trigger: `my_len >= max_enemy_len + 2 and my_len >= 7`
     (was +3, >=8). Stop growing EARLIER vs this short opponent so we never reach the deadly
     L49-96 range. Safety/space (space*10/unit), H2H (-1000), tail-reach still dominate, so
     no suicidal food-refusal (verified sim_test 40/0/0, fuzz clean).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.24. A/B new vs old on IDENTICAL seeds:
  N=8 new 8-0-0 vs old 7-0-1; N=20 new 19-0-1 vs old 18-0-2 — consistent improvement (converts
  draws to wins), ZERO regressions.
- **Next teammate:** opponent = opp_eremetic_eric.py (COILING tail-chaser, stays short, long
  games). Our ONLY loss vector remains overgrowth->self-coil. If losses persist: (a) lower
  clearly_ahead threshold further (+1 / >=6), (b) cap max length harder, (c) the canonical
  Hamiltonian tail-follow when long+safe (still not implemented). Test: `python3 vs_eremetic.py
  main.py 8` (or nohup for larger N — games run 400-800 turns). Keep sim_test 40 + fuzz clean.
  main.py has all prior layers + now HARD any-food avoidance when clearly ahead.

## Round 2 of 5 (this task, opus-4-8) — eremetic-eric, LENGTH-SCALED TAIL-FOLLOW + FIXED ANTI-WALL-HUG GATE
- Opponent STILL `coreyja__eremetic-eric` (coiling tail-chaser, stays SHORT L9-16, survives
  400-670 turn games; opp_eremetic_eric.py). Results: round 0 won 241-9, round 1 won 247-3.
- **Loss analysis (round 1: sim_18, sim_231, sim_233; tool analyze_losses.py):** ALL three are
  the SAME chronic vector — OPUS grew to **L19/L53/L72** with HP pinned at 100 the whole game,
  then ran along an EDGE into a CORNER ((7,0)/(10,0)) and self-coiled (only 1 free neighbor each
  step until 0). KEY: the /logs sim floods the board with FOOD (~53 food on 121 cells by turn
  420!), so our -400 "avoid food when clearly_ahead" penalty CANNOT stop growth (food is
  unavoidable — every neighbor is food). The opponent stays short by tightly following its OWN
  tail (coiling) and only eating when its loop calc says it must.
- **Two changes (backup: main_r1of5_eremetic_r2_backup.py = git HEAD pre-change bot):**
  1. **LENGTH-SCALED TAIL-FOLLOW** (line ~585): tail-follow bias weight was fixed 2.0; now
     `tf_w = 2.0 + (my_len-15)*0.6` for my_len>=15 (strong at L50+). Makes a long snake coil
     in a COMPACT loop chasing its tail (like the opponent) instead of running edges into corners.
  2. **FIXED ANTI-WALL-HUG GATE** (line ~783): the escape-off-edge bonus was gated on
     `max_enemy_len >= my_len-2`, so when we're MUCH longer (L53 vs L10) it NEVER fired — exactly
     our loss case! Removed the enemy gate: now fires whenever `my_len>=8 and currently_on_edge
     and not critical` (self-coil is length-driven, not enemy-driven). Rewards peeling off the
     wall into open board (+22*len_scale), penalizes heading into a corner (-30*len_scale).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.08. Frame tests on sim_231: at T420
  (L21 on top edge) NEW picks DOWN (into interior) vs OLD RIGHT (along edge) — peels off. A/B vs
  real opp on same seeds: NEW 21-0-3 & 27-0-3, OLD 22-0-2 & 28-0-2 (IDENTICAL within noise, NO
  regression). The sim's random food doesn't reproduce the exact corner-coil frames (as prior
  teammates repeatedly found), so validated by design (targets confirmed vector) + frame tests +
  no-regression. NOTE: by the death FRAME (T548) we were already forced (only 1 free neighbor);
  the trap forms 5-10 turns earlier — the two changes attack that EARLIER commit + keep us shorter.
- **Next teammate:** opponent = opp_eremetic_eric.py (coiling tail-chaser, stays short). Our ONLY
  loss vector is overgrowth (L50-72 on a food-flooded board) -> self-coil into a corner. If losses
  persist: (a) raise tail-follow scale further, (b) a TRUE Hamiltonian cycle when very long+safe
  (still the canonical unimplemented fix), (c) even harder edge/corner avoidance for L20+. Test:
  `python3 vs_eremetic.py main.py 24` IN BACKGROUND (`nohup ... &`, poll file — games run 400-800
  turns, N>~24 exceeds the 30s cmd timeout). Keep sim_test 40 + fuzz clean. main.py has all prior
  layers + now length-scaled tail-follow and enemy-independent anti-wall-hug escape.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `coreyja__gigantic-george`, ANTI-OVERGROWTH
- **Opponent = `coreyja__gigantic-george`** — delegates to EremeticEric (coiling tail-chaser)
  + a Hamiltonian board-fill step. Real source saved to `opp_gigantic_george.py`
  (git show origin/human/coreyja/gigantic-george:main.py). Stays SHORT (L9-15), keeps its
  health at ~2 (only eats when forced), loops tightly around its own tail, survives 500-800+
  turn games. Test: `python3 vs_gigantic.py main.py <N>` (built; N small — games run long).
- **Round 0 result: won 246-4** (/logs/rounds/0/results.json). Analyzed all 4 losses
  (`python3 analyze_losses.py sim_148 sim_184 sim_72 sim_95`): UNAMBIGUOUS chronic vector —
  OPUS grew to **L32/L94/L88/L68** in 498-813 turn games and SELF-COILED / boxed itself in on
  the 121-cell board while the opponent stayed L9-15 and outlasted us. Extreme overgrowth.
- **ROOT CAUSE:** the real engine ACCUMULATES food (verified sim_184: food count climbs 3->38
  by turn 500, ~16-38 pieces sitting on the board). Once we're long, avoiding food is nearly
  impossible (every neighbor is often food), so we keep growing to L86+ and then can't manage
  our body. NOTE: `sim_test.py` does NOT reproduce this (it maintains only min-1 food, caps 500
  turns) — so A/B in the sim can't reproduce the trap (both bots survive to the 500 cap = draws).
- **Changes (backup: main_r0_gigantic_backup.py = git HEAD pre-change bot):**
  1. Lowered `clearly_ahead` length threshold `my_len >= 7 -> >= 6` (line 415) so we STOP
     growing EARLIER vs this short opponent (the +2-over-enemy part is unchanged). Earlier we
     invoke the HARD any-food avoidance (-400 on any food cell) -> stay shorter longer.
  2. Raised deep-self-survival `deep_depth` cap `20 -> 24` (line 616). At L60-90 the coil
     develops 20+ turns out; a 20-ply horizon can't see it. 24 gives more foresight while
     staying time-safe (L40 loose-loop board = 5.9ms; fuzz maxt 16ms; per-move limit ~500ms).
     (Tried 28 but backed off to 24 for compute margin since A/B self-play couldn't validate.)
- **Verification:** syntax OK; `python3 sim_test.py 30/40` => 30/0/0 & 40/0/0; `PYTHONPATH=
  /workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.0 (<500 limit);
  `python3 vs_gigantic.py main.py 10` => 8-0-2 (draws = 500-turn timeouts, sim doesn't flood
  food so overgrowth trap not reproduced). A/B new-vs-backup self-play TIMES OUT in this env
  (games run to the 500-turn cap + deep_depth=24 is slow at high length) = no regression signal
  available; changes validated by DESIGN (directly cut the confirmed overgrowth->self-coil
  vector) + sim_test + fuzz + timing.
- **Next teammate:** opponent = opp_gigantic_george.py (coiling tail-chaser + Hamiltonian fill;
  stays short, food-floods the board over long games). Our ONLY loss vector is overgrowth
  (L32-94!) -> self-coil. If losses persist: (a) lower clearly_ahead further (>=5 / even +1),
  (b) the canonical Hamiltonian tail-follow when long+safe is STILL the real unimplemented fix
  (cycle the board tightly like the opponent instead of coiling), (c) push deep_depth higher
  IF timing allows (watch the 500ms per-move limit; L40 loose = ~6ms at depth 24). Analyze new
  losses with `analyze_losses.py`. Keep sim_test + fuzz clean. main.py has all prior layers:
  time-aware flood fill, tail-reach BFS, 2-ply best/worst space, enemy-contested space, H2H
  follow-up, length-scaled edge/corner + edge-shadow, safety-aware food, CRITICAL starvation,
  Voronoi territory, deep self-survival sim (depth now 24), enemy-aware deep sim, clearly_ahead
  HARD any-food avoid (now triggers at L6), anti-wall-hug escape, length-scaled tail-follow.

## Round 2 of 5 (this task, opus-4-8) — gigantic-george, DOMINANT-TAIL-FOLLOW AT EXTREME LENGTH
- Opponent STILL `coreyja__gigantic-george` (coiling tail-chaser + Hamiltonian fill; stays
  SHORT L9-15, keeps hp~2, survives 500-800 turn games; opp_gigantic_george.py).
- Results: round 0 won 246-4, round 1 won 249-1 (prev teammate's anti-overgrowth cut 4->1 loss).
- **Loss analysis (round 1, ONLY loss = sim_121, 767 turns, analyze_losses.py):** SAME chronic
  vector — OPUS grew to **L91** on the 121-cell board while OPP stayed L14, then self-coiled.
  Traced growth: the real engine FLOODS food (3 -> 38 pieces on the board by turn ~600), so once
  we're L23+ EVERY neighbor is often food and the -400 "avoid food when clearly_ahead" penalty
  CANNOT stop growth (all moves get -400, no discrimination). By the death frames (T753-763) the
  board was 105/121 full and the head had 0-1 free neighbors every turn — a pure Hamiltonian
  survival situation. The trap is set ~40 turns earlier by burying the head away from the tail.
- **Change (backup: main_r1of5_gigantic_r2_backup.py = git HEAD pre-change bot):** made the
  TAIL-FOLLOW bias DOMINANT at extreme length. Previously tf_w maxed ~gently (2.0+(len-15)*0.6).
  Added: `if my_len>=30: tf_w = max(tf_w, 12.0 + (my_len-30)*1.2)`. At L91 tf_w ~85/unit-dist,
  strongly rewarding keeping the head close (path-distance) to the tail -> the body stays a TIGHT
  LOOP that hugs its own tail (Hamiltonian-ish cycle, like the opponent) instead of coiling into
  a dead pocket. This is the canonical fix for the overgrowth->self-coil vector, gated to only
  fire when long+safe+not-hungry (my_len>=8, not starving, not critical, tail_reach).
- **Verification:** syntax OK; `python3 sim_test.py 60` => 60/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.15 (<500 limit). Max decision time over
  the actual sim_121 game frames = 11.7ms (safe). FRAME REPLAY of sim_121: new bot changes 2 of
  302 long-snake decisions (T483 L33 left->right, T503 L43 up->right) — steering toward the
  tail-follow path at exactly the length range where the coil forms; minimal change = low
  regression risk. Self-play new-vs-old N=6 = 2-2-2 (dead even, no regression). NOTE: the sim
  does NOT reproduce the food-flooding (maintains min-1 food, 500-turn cap), so A/B in the sim
  can't reproduce the trap (both survive to timeout = draws) — validated by design (targets the
  confirmed L91 overgrowth vector) + frame replay + sim_test + fuzz + timing + no-regression.
- **Next teammate:** opponent = opp_gigantic_george.py (coiling + Hamiltonian, food-floods the
  board over long games). Our ONLY loss vector is overgrowth (L86-91!) -> self-coil on a nearly
  full board. If losses persist: (a) raise the extreme-length tail-follow scale further (12.0 /
  1.2), (b) a TRUE Hamiltonian cycle when very long+safe is STILL the ideal unimplemented fix
  (perfectly fill the board like the opponent), (c) push deep_depth higher IF timing allows.
  Analyze new losses with `analyze_losses.py <sim.jsonl>`. Test vs real opp: `vs_gigantic.py`
  (sim won't reproduce the trap; both survive to 500-cap). Keep sim_test + fuzz clean. main.py
  has all prior layers + now DOMINANT tail-follow at L30+.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `Flipez__flipez-crystal`, NO CODE CHANGE (reverted)
- **Opponent = `Flipez__flipez-crystal`** — a MODERATE 2018 port. Real source saved to
  `opp_flipez_crystal.py` (git show origin/human/Flipez/flipez-crystal:main.py, 188 lines).
  Strategy: 4 head neighbors; a cell is "free" if in-bounds, not on any snake body, and not
  the predicted-next cell of an enemy whose length >= mine (enemy predicted to move toward its
  OWN nearest food). Target = nearest food, UNLESS an enemy is closer -> target board CENTER.
  Picks the free neighbor closest (euclidean) to the target. Has basic H2H/collision avoidance
  and food-seeking but NO space management. GROWS LARGE (L8-29) and cuts us off.
- **Round 0 result: won 223-22 +5T** (~89%). Test harness: `python3 vs_flipez.py main.py <N>`
  (created; sim is HARSHER than real, ~75% at committed bot).
- **Loss analysis (all 22 losses, analyze_losses.py + /tmp/death.py):** DIFFERENT from our
  chronic self-coil vector — here in nearly EVERY loss WE were SHORTER (OPUS L7-21 vs OPP
  L8-29). The opponent OUT-GROWS us, then funnels us into a spot where our ONLY free move is a
  cell the LONGER enemy can also reach = H2H LOSS (sim_114: OPUS L7 @(7,9) only free=up, OPP
  L10 @(8,10) takes (7,10); sim_201 same pattern). Loss vector = falling behind in LENGTH +
  getting cut off / H2H-killed by the longer snake.
- **Experiments tried (all REVERTED — net noise/risk):**
  1. Raise `behind_or_even` threshold +1->+2 and `clearly_ahead` +2->+3 (grow longer vs a
     big-growing foe). A/B on identical seeds was INCONSISTENT: batch1 (seed 13n+3) NEW 22-0
     vs OLD 20-2 (+2); batch2 (29n+101) even; batch3 (17n+555) NEW 12-9 vs OLD 17-5 (-5!).
  2. Also boosting behind food weight 7->8 / bonus 70->80: same seed-dependent noise.
  => The changes are NOISE-FLOOR and one seed batch showed a real regression, so NOT worth the
  risk on a bot that WON the real match 223-22 (89%). **Reverted to committed main.py.**
- Verified committed main.py: syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=
  /workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.
- **Decision: NO code change.** Kept the proven 89% bot stable.
- **Next teammate:** opponent = opp_flipez_crystal.py (moderate, grows large, cuts us off in
  H2H when we're shorter). Our loss vector THIS matchup = falling behind in LENGTH -> forced
  into an H2H-loss cell by the longer enemy. IDEAS if you want to push win rate: (a) a
  DETERMINISTIC growth edge — since the opponent AVOIDS cells WE can reach when we're >= its
  length, being reliably LONGER makes it yield; but naive food-weight boosts regressed on some
  seeds (dive into contested food). Try a SMARTER growth: only eat UNCONTESTED food (enemy
  farther) to grow safely without walking into H2H traps. (b) Exploit its predictability: it
  predicts WE go to our nearest food — you could feint. (c) Better anti-funnel: detect when our
  free-move count is collapsing to 1 near a longer enemy and steer away EARLIER (2-3 turns before
  the forced-H2H frame). A/B ANY change across MULTIPLE seed batches (13n+3, 29n+101, 17n+555)
  — single-batch results are misleading (proven above). main.py has all prior layers. Test:
  `python3 vs_flipez.py main.py 20` + `sim_test.py 40` + fuzz. Backup: main_r0_flipez_backup.py.

## Round 2 of 5 (this task, opus-4-8) — flipez-crystal, RE-CONFIRMED NO CODE CHANGE (tweaks = noise/regressive)
- Opponent STILL `Flipez__flipez-crystal` (moderate 2018 port, grows large L8-24, cuts us off;
  opp_flipez_crystal.py). Results: round 0 won 223-22+5T, round 1 won 223-23+4T (~89% real).
- **Loss analysis (all 23 round-1 losses, analyze_losses.py):** UNAMBIGUOUS & unchanged from
  round 0 — in EVERY loss OPUS was SHORTER at death (OPUS L5-L15 vs OPP L6-L24). We fall
  BEHIND in length, then get funneled/cut off/H2H-killed by the longer snake. NOT our usual
  self-coil vector; here the opponent OUT-GROWS us.
- **Experiments A/B'd on IDENTICAL seeds across 3 batches (7n+1, 29n+101, 17n+555), N=20 each,
  vs real opp (sim ~78%, harsher than real 89%):**
  1. variant: clearly_ahead +2/>=6 -> +4/>=12 AND behind_or_even +1 -> +3 (grow to a bigger
     lead before relaxing). NEW 16/17/14 vs OLD 15/17/15 = DEAD EVEN (net 47-47).
  2. variant2: when behind/even+healthy, chase the ABSOLUTE nearest food (raw distance) instead
     of the safety-ranked food (win the growth race). NEW 15/16/15 vs OLD 15/17/15 = even/slightly
     worse.
  3. variant3: variant1 + behind food weight 7->9. NEW 14 vs OLD 15 on batch1 = REGRESSED.
  => All food/threshold tweaks are NOISE-FLOOR or slightly regressive here, EXACTLY as the two
  prior flipez teammates found. Scalar tuning does not move the needle vs this opponent.
- Verified committed main.py: syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=
  /workspace python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.33.
- **Decision: NO code change.** Kept the proven ~89% bot stable; every tweak tested was noise
  or a regression, and regression risk on a winning bot isn't worth it.
- **Next teammate — the ONLY promising unexplored lever:** AGGRESSIVE CUTOFF WHEN WE ARE
  LONGER. The opponent's `is_free_point` treats a cell as blocked ONLY if an enemy whose
  `length >= mine` can reach it (it YIELDS to a longer snake, predicting the longer snake moves
  toward its own nearest food). So when WE are strictly longer, Flipez actively avoids cells we
  can reach — we can BODY-BLOCK / cut off its space and force it to trap itself. This is a
  STRUCTURAL exploit (not a scalar tweak) and is the only thing likely to beat the ~89% ceiling.
  Implementation sketch: when my_len > max_enemy_len, add an AGGRESSION term that rewards moves
  reducing the enemy's Voronoi/reachable territory (we already have `_voronoi_owned`), or that
  position our body between the enemy head and the open board / its nearest food. A/B carefully
  across MULTIPLE seed batches (7n+1, 29n+101, 17n+555) — single-batch is misleading (proven).
  Tools: `python3 vs_flipez.py main.py 20`, `python3 vs_flipez2.py <bot> <N> <mult> <off>`,
  `/tmp/ab.py <N> <mult> <off>` (rebuild: loads a variant vs main.py vs opp on identical seeds).
  main.py has all prior layers. Backup available: main_r0_flipez_backup.py.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `jackisherwood__battlesnake-elon`, STRONGER MID-LENGTH TAIL-FOLLOW
- **Opponent = `jackisherwood__battlesnake-elon`** — a REAL 2019 JS port (smorts/floodFill).
  Source saved to `opp_elon.py`. It is a TAIL-CHASER: scared state (enemy<=3) -> collision_avoider;
  hungry -> food_seeker; else -> tail_chaser (keeps a compact loop following its own tail). Has
  threshold flood-fill (len+5) dead-end avoidance. STRONG: grows large (L20-40) and survives VERY
  long games (median death turn 337). NOT a wall-walker.
- **Round 0 result: won 190-53 +7T** (~76%, our TOUGHEST-ish matchup). Test: `python3 vs_elon.py
  main.py <N>` (games run LONG ~2s each; use nohup+poll, N<=30 for 30s cmd timeout).
- **Loss analysis (all 53 losses):** LONG games (median turn 337), OPUS median L24 vs OPP L27.
  33/53 shorter, 4 equal, 16 longer. Dominant vector = SELF-COIL while large in long games.
  Traced sim_157 (we were LONGER L24 vs L22): at T346 head (4,4) we went LEFT into a shrinking
  corridor (free neighbors 3->3->2->1->1->0) and boxed ourselves in at T351. Classic mid-length
  self-coil. Our tail-follow bias at L24 was only tf_w=7.4 (2.0+9*0.6), too weak vs space*10.
- **Change (backup: main_r0_elon_backup.py = git HEAD pre-change bot):** strengthened the
  tail-follow bias in the L15-30 band where elon losses cluster (median L24):
    - `tf_w = 2.0 + (my_len-15)*0.6`  ->  `* 1.1` (at L24: 7.4 -> 11.9; at L30: 11 -> 18.5).
  The L30+ dominant tail-follow (12.0+(len-30)*1.2) is unchanged. Gated behind long+safe+
  not-hungry+tail_reach so it never overrides survival/food priorities — only makes a large
  snake coil in a COMPACT tail-following loop instead of burying its head into a dead pocket.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.14 (<500 limit). A/B vs real opp
  (/tmp/ab_elon.py, identical seeds, N=30): NEW W=18 L=5 D=7 (OLD run didn't finish before step
  limit — games are slow). NOTE: the sim's random food/dynamics rarely reproduce the exact
  long-game coil frames (as prior teammates repeatedly found), so validated by DESIGN (directly
  targets the confirmed mid-length self-coil vector) + sim_test + fuzz + no crash. Low risk:
  only nudges the tail-follow score in the L15-30 band.
- **Next teammate:** opponent = opp_elon.py (STRONG tail-chaser, grows large, long games). Our
  loss vector = self-coil while large (L15-30) in long games; often we're SHORTER (33/53) so the
  opponent also out-lasts us. Ideas if losses persist: (a) tune the L15-30 tail-follow further
  (1.1 -> 1.5) but A/B carefully across seed batches, (b) the canonical TRUE Hamiltonian cycle
  when long+safe is STILL the ideal unimplemented fix, (c) since 33/53 losses we're shorter,
  consider growing more aggressively mid-game to not get out-lasted. Test: `nohup python3 -u
  vs_elon.py main.py 30 > /tmp/x.txt &` (poll — games are slow). Keep sim_test 40 + fuzz clean.

## Round 2 of 5 (this task, opus-4-8) — elon, OPPONENT-ADAPTIVE GROWTH (stop out-lasting ourselves short)
- Opponent STILL `jackisherwood__battlesnake-elon` (STRONG tail-chaser, grows LARGE L30-43,
  long games; opp_elon.py). Results: round 0 won 190-53 (76%), round 1 won 205-41 (~83%,
  prev teammate's mid-length tail-follow boost helped).
- **Loss analysis (all 41 round-1 losses, analyze_losses.py):** DECISIVE SHIFT from our
  chronic self-coil vector — **33/45 losses OPUS was SHORTER at death** (OPUS L20-30 vs OPP
  L30-43); 7 equal, only 5 longer. Long games (turn 173-494). ROOT CAUSE = elon OUT-GROWS us
  and out-lasts us; the bigger snake controls territory and cuts us off.
- **WHY we were shorter:** the old `clearly_ahead` food-avoidance triggered at just
  `my_len >= max_enemy_len + 2` (designed for SHORT opponents eremetic/gigantic/arthur to
  avoid overgrowth self-coil). But vs a LARGE-GROWING opponent, at a mere +2 lead we STOPPED
  eating, elon kept eating, passed us, and then WE became the shorter snake that gets out-lasted.
- **Change (backup: main_r1of5_elon_r2_backup.py = git HEAD pre-change bot):** made growth
  OPPONENT-ADAPTIVE:
  1. `clearly_ahead` now requires EITHER (+2 lead AND enemy is short, max_enemy_len<=16) OR
     (+6 absolute lead). Vs elon (L30) we no longer shut off growth at +2 — we keep pace and
     only relax at a big +6 lead. Vs short opponents (<=16) behavior is UNCHANGED (still +2).
  2. `behind_or_even` pace band widened vs large enemies: `_pace_margin = 4 if
     max_enemy_len>=20 else 1`. So vs elon we chase food aggressively (d_after*7, +70 on-food)
     up to a +4 lead, keeping pace; vs short opponents the +1 band is unchanged.
  Net effect: vs elon we grow to STAY COMPETITIVE (attacks the 33/45 shorter-at-death vector);
  vs all short opponents (eremetic/gigantic/arthur) the overgrowth->self-coil protection is
  fully preserved (verified by unit-test logic table).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.3 (<500 limit). Unit-test logic table
  confirms: elon L32/L30 -> keep growing (behind_or_even=True, clearly_ahead=False); elon
  L36/L30 -> clearly_ahead=True (relax); eremetic L14/L12 -> clearly_ahead=True (unchanged);
  eremetic L30/L12 -> clearly_ahead=True (overgrowth guard intact). A/B vs real opp
  (/tmp/ab_elon.py, identical seeds) was RUNNING at step limit — elon games are SLOW (both
  survive long), N=16 exceeds the 30s cmd timeout even in background. Validated by DESIGN
  (directly targets the confirmed shorter-at-death vector) + sim_test + fuzz + logic table +
  full backward-compat with short-opponent guards.
- **Next teammate:** opponent = opp_elon.py (STRONG tail-chaser, grows large). If losses persist
  and we're STILL shorter, push _pace_margin higher (4->6) or the behind food weight (7->8-9),
  but A/B carefully — elon games run long so use `nohup python3 -u /tmp/ab_elon.py N &` and poll
  /tmp/ab*.txt (rebuild: loads main.py NEW vs main_r1of5_elon_r2_backup.py OLD, both vs opp_elon,
  identical seeds). If we're LONGER when losing, it's back to the self-coil vector -> the
  canonical TRUE Hamiltonian tail-follow when long+safe is STILL the ideal unimplemented fix.
  main.py has all prior layers + now opponent-adaptive growth (keep pace vs large-growers,
  avoid overgrowth vs short opponents).

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `MorganConrad__tantilla` (COMPACT TAIL-CHASER), ANTI-OVERGROWTH + TAIL-FOLLOW
- **Opponent = `MorganConrad__tantilla`** — a JS->Python port that `chaseYourTail` (keeps a
  COMPACT loop following its own tail), eats only when hungry (health<20 closest food, <40
  tail-chase). Basic collision + H2H avoidance. Stays SHORT (L7-22), survives LONG (300-600+
  turn games) and OUTLASTS us. Real source saved to `opp_tantilla.py`. Test: `python3
  vs_tantilla.py main.py <N>` (created; sim does NOT flood food like the real engine, so it
  can't reproduce the loss trap — both survive to timeout).
- **Round 0 result: won 234-16** (~93.6%). Analyzed all 16 losses (`analyze_losses.py`):
  UNAMBIGUOUS chronic self-coil vector — in EVERY loss OPUS was MUCH LONGER (L13-52!) than the
  opponent (L7-22) in LONG games (turn 287-613) and SELF-COILED / boxed itself in. The real
  engine FLOODS food (14+ pieces on the 121-cell board by turn 180) so once we're long, food is
  nearly unavoidable and we grow to L44-52, then can't manage our body.
- **Changes (backup: main_r0_tantilla_backup.py = git HEAD pre-change bot):**
  1. Anti-overgrowth `_enemy_small` threshold `<=16 -> <=22` and big-lead `+6 -> +5` (lines
     ~427-431). Vs Tantilla (stays L7-22) this shuts off growth at just +2 lead across its whole
     length range (was only <=16). Vs LARGE-growers (elon L30-43) `_enemy_small` stays false so
     we still keep pace (verified logic table: elon L32/L30 keeps growing; tantilla L24/L22 stops).
  2. Mid-length tail-follow bias L15-30 band `*1.1 -> *1.4` (line ~613) — tantilla losses cluster
     L15-31; a stronger tail-follow keeps a COMPACT loop instead of coiling into a dead pocket.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.2 (<500 limit). Frame tests: the bot
  correctly AVOIDS food when clearly_ahead (validated on sim_212 T200). NOTE: the changes are
  NEUTRAL on the actual loss death-frames (0 moves changed) because by the last ~30 turns of a
  coil the snake is already committed AND the board is already flooded (food unavoidable) — the
  trap forms EARLIER. vs_tantilla sim = 11-0-1 (same as backup, no regression). Validated by
  DESIGN (targets the confirmed overgrowth->self-coil vector) + sim_test + fuzz + no-regression.
- **Next teammate:** opponent = opp_tantilla.py (COMPACT tail-chaser, stays short, food-floods
  the board over long games). Our ONLY loss vector is overgrowth (L44-52) -> self-coil on a
  nearly-full board. The REAL unimplemented fix (flagged for MANY rounds) is a TRUE HAMILTONIAN
  CYCLE when long+safe — cycle the board tightly like the opponent instead of coiling. Scalar
  tweaks (food weights, tail-follow scale) are NOISE-FLOOR and don't reproduce in the sim (which
  doesn't flood food). If you attempt the Hamiltonian follow: gate behind long+space-safe, A/B
  carefully (but note sim can't validate the trap — use frame-replay of /logs losses instead).
  main.py has all prior layers + now `_enemy_small<=22` anti-overgrowth and stronger L15-30
  tail-follow. Analyze losses: `python3 analyze_losses.py <sim.jsonl>`.

## Round 2 of 5 (this task, opus-4-8) — tantilla, ADDED CLEARLY-AHEAD ANTI-CORNER-APPROACH
- Opponent STILL `MorganConrad__tantilla` (COMPACT tail-chaser, stays SHORT, food-floods board
  over long games; opp_tantilla.py). Results: round 0 won 234-16, round 1 won 233-17.
- **Loss analysis (round 1, analyze_losses.py):** SAME chronic overgrowth->self-coil vector.
  TRACED sim_54 turn-by-turn (the key insight this round): at T262 OPUS L11 hp100 (clearly
  ahead vs OPP L8) was on the TOP edge at (6,10) and ran RIGHT along y=10 eating flooded food
  ((6,10)->(7,10)->(8,10)->(9,10)->(10,10)) STRAIGHT INTO the top-right CORNER, then boxed
  itself in (L17, T273, 0 free neighbors). The existing anti-wall-hug escape bonus (+22) and
  corner penalty were SWAMPED by flood-fill space*10 (running right keeps ~90 open cells), so
  the bot happily ran the edge into the corner. Note: bfs-dist-to-tail actually PREFERRED right
  here (tail circled back), so tail-follow bias did NOT help this case.
- **Change (backup: main_r1of5_tantilla_r2_backup.py = git HEAD pre-change bot):**
  1. Added an ANTI-CORNER-APPROACH penalty in the `long_on_edge` block: when a candidate move
     STAYS on an edge (not peeling off, not yet the corner) AND takes us CLOSER to the nearest
     corner along that edge, subtract approach_w*len_scale (14 normally, **55 when clearly_ahead**).
     Directly attacks the "run along edge into corner while ahead" self-coil (sim_54).
  2. Strengthened the peel-off/corner weights WHEN clearly_ahead: peel-off-edge bonus 22->60,
     corner-cell penalty 30->80 (both *len_scale). We should NOT be hugging walls / eating edge
     food when already ahead — it only funnels us into a corner.
  All gated behind `long_on_edge` = my_len>=8 + currently_on_edge + not critical, so CRITICAL
  (starving) mode fully suppresses it (verified: starving snake on edge still eats toward
  edge/corner food -> goes right).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.12. FRAME REPLAY sim_54: NEW bot now
  peels DOWN off the top edge at T263/T264 (was running right into the corner) — fix engages.
  sim_108 T604 (L52 @corner (10,0)) NEW picks UP (away from corner). Starving-edge-food unit
  test: still eats (critical suppresses penalty). A/B new-vs-backup on identical seeds (N=10)
  = 8-0-2 vs 9-0-1 (noise; the sim does NOT reproduce the food-flooding trap so both mostly
  win/draw — validated by DESIGN + frame replay + no-regression, as all prior tantilla/eremetic/
  gigantic teammates found the sim can't reproduce the overgrowth trap).
- **Next teammate:** opponent = opp_tantilla.py (COMPACT tail-chaser, stays short, food-floods
  board). Our ONLY loss vector remains overgrowth (L17-52) -> self-coil, now attacked at the
  EDGE-APPROACH stage (peel off before the corner). Interior coils (L33-50 buried head, e.g.
  sim_127/sim_44) are still unaddressed — the canonical TRUE HAMILTONIAN CYCLE when long+safe
  is STILL the ideal unimplemented fix (cycle the board tightly instead of coiling). Scalar
  food/tail-follow tweaks are noise-floor and don't reproduce in the sim. main.py has all prior
  layers + now clearly-ahead anti-corner-approach + stronger clearly-ahead peel-off.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `ChaelCodes__cornelius` (FOOD-GREEDY, GROWS LARGE), KEEP-PACE GROWTH
- **Opponent = `ChaelCodes__cornelius`** — a 1-PLY GREEDY bot (Rust port). Source saved to
  `opp_cornelius.py` (git show origin/human/ChaelCodes/cornelius:main.py, 172 lines). Scoring per
  head-neighbor: base 100 interior / 60 on x==0 or y==0 edges (NOT the max edges!); +75 food;
  -80 if equal/longer enemy head adjacent; +50 if flood-fill space>=len else -(80-space); +75
  incidental if food. Picks argmax of the 4 moves. **NO lookahead.** It is STRONGLY food-attracted
  and GROWS LARGE (L28-41). Test: `python3 vs_cornelius.py main.py <N>` (games long; N<=14 for 30s
  cmd timeout, or nohup+poll). NOTE: sim_test/vs_cornelius do NOT flood food like the real engine,
  so they can't reproduce the growth-race loss vector (we win ~15-0 in sim).
- **Round 0 result: won 177-73** (~71%, one of our CLOSER matchups). Analyzed all 73 losses
  (`python3 analyze_cornelius.py`): DECISIVE — **55/73 losses OPUS was SHORTER at death** (OPUS
  L20-33 vs OPP L24-41); 5 equal, only 13 longer. LONG games (median turn 323). ROOT CAUSE =
  Cornelius OUT-GROWS us (it's food-greedy, +75) and out-lasts/out-positions us as the bigger
  snake. This is the OPPOSITE of our chronic self-coil vector — vs Cornelius we stop growing too
  early and get out-lengthed.
- **Changes (backup: main_r0_cornelius_backup.py = git HEAD pre-change bot):**
  1. `_pace_margin` for large-growing enemies (max_enemy_len>=20): 4 -> **6** (keep chasing food
     to a bigger lead before relaxing, so a food-greedy L41 opponent doesn't pass us).
  2. Added `truly_behind = my_len < max_enemy_len and max_enemy_len >= 12` flag. New food-scoring
     branch (between starving and behind_or_even): chase HARD (d_after*9, +85 on-food).
  3. When truly_behind (and not critical), target the ABSOLUTE nearest food (bypass safety-ranked
     food selection) to win the growth race. Safety/space/H2H penalties still dominate scoring
     (space*10/unit, H2H -1000) so no suicidal dives.
  All changes fire ONLY when we're strictly shorter than a >=L12 enemy, so they DON'T affect
  short-opponent overgrowth guards (eremetic/gigantic/arthur/tantilla: those enemies stay short,
  truly_behind stays false once we lead, clearly_ahead unchanged).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace python3
  fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.1 (<500 limit); `vs_cornelius.py main.py 14`
  => 13-0-1 (no regression; sim can't reproduce the food-flood growth race so validated by DESIGN
  — directly targets the confirmed 55/73 shorter-at-death vector — + sim_test + fuzz + no crash).
- **Next teammate:** opponent = opp_cornelius.py (FOOD-GREEDY, grows L28-41, no lookahead). Our
  loss vector = being SHORTER (out-grown). If losses persist and we're still shorter, push
  _pace_margin higher (6->8) or truly_behind food weight (9->11). EXPLOIT: Cornelius has NO
  lookahead and is superstitious of x==0/y==0 edges (base 60 there) — we could bait it toward
  those low-edges or cut it off when we're longer (it avoids cells an equal/longer enemy head is
  adjacent to, -80). If we're LONGER when losing, it's the self-coil vector (tail-follow etc all
  present). Analyze: `python3 analyze_cornelius.py`. main.py has all prior layers + keep-pace growth.

## Round 2 of 5 (this task, opus-4-8) — cornelius, WIDENED KEEP-PACE GROWTH BAND
- Opponent STILL `ChaelCodes__cornelius` (FOOD-GREEDY 1-ply greedy, grows L28-41, no lookahead;
  opp_cornelius.py). Results: round 0 won 177-73, round 1 won 193-55+2T (prev teammate's
  keep-pace growth cut losses 73->55 — GROWTH IS THE LEVER vs this opponent).
- **Loss analysis (round 1, 57 losses, analyze_cornelius.py + /tmp/deathcause.py):** UNCHANGED
  dominant vector — **38/57 losses OPUS was SHORTER at death** (median opusL~22 vs oppL~24;
  6 equal, 13 longer). Death cause: boxed 22, wall/corner 17, H2H 18. The 18 H2H losses are
  DIRECTLY caused by being shorter (we lose every H2H when shorter). Cornelius (food-greedy)
  OUT-GROWS us and out-lasts / H2H-kills us as the bigger snake. Losses are close in length
  (only -2 median), so a modest growth boost should flip many.
- **Change (backup: main_r1of5_cornelius_r2_backup.py = git HEAD pre-change bot):** widened the
  keep-pace growth band so we don't fall behind cornelius:
    - `_pace_margin = 8 if max_enemy_len>=20 else (6 if max_enemy_len>=12 else 1)`
      (was `6 if >=20 else 1`). Now vs a large grower we keep eating to a +8 lead (was +6), and
      vs a mid-length enemy (L12-19, the growth-race window) we keep pace to +6 (was +1 — we
      used to stop eating too early mid-game and let cornelius pass us).
  Logic table verified: whenever we're behind/near cornelius (L24-41) we eat HARD (truly_behind)
  or keep pace (behind_or_even); clearly_ahead only fires at a genuinely big lead (behind_or_even
  is checked BEFORE clearly_ahead in the elif chain, so it wins when both true). `_enemy_small`
  left at 22 (unchanged) to NOT regress the tantilla anti-overgrowth guard.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=15.98. Logic table confirms keep-pace at
  all cornelius-relevant lengths. A/B vs real opp in sim: NEW 10-0 = OLD 10-0 (NO regression;
  the sim does NOT flood food like the real engine over 300+ turn games, so it CANNOT reproduce
  the growth-race trap — both bots win in sim regardless, as every prior cornelius/tantilla/
  eremetic/gigantic teammate found). Validated by DESIGN (directly targets the confirmed 38/57
  shorter-at-death vector) + sim_test + fuzz + logic table + no-regression.
- **Next teammate:** opponent = opp_cornelius.py (FOOD-GREEDY, grows L28-41, no lookahead). Our
  loss vector = being SHORTER (out-grown) -> boxed/H2H-killed by the bigger snake. If losses
  persist and we're STILL shorter, push _pace_margin higher (8->10) or truly_behind food weight
  (9->11). NOTE: the sim CANNOT validate growth changes (doesn't food-flood) — validate by design
  + analyze_cornelius.py on new /logs. If we start losing while LONGER, back off growth (self-coil
  vector) — the canonical TRUE Hamiltonian tail-follow when long+safe is STILL the ideal
  unimplemented fix. EXPLOIT idea (untried): cornelius has NO lookahead and is superstitious of
  x==0/y==0 edges (base 60 vs 100); it avoids cells an equal/longer enemy head is adjacent to
  (-80) — when LONGER we could body-block/cut it off. main.py has all prior layers + now the
  widened keep-pace growth band.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `joshhartmann11__battlejake2019`, LENGTH-SCALED ENEMY-REACH ANTI-SEAL
- **Opponent = `joshhartmann11__battlejake2019`** — a 2019 BattleSnake port (y-flip to v1 API).
  Real source saved to `opp_battlejake.py` (git show origin/human/joshhartmann11/battlejake2019:main.py,
  556 lines). Food-seeking by HUNGRY/STARVING thresholds; stays SHORTER than us and outlasts us.
  Test: `python3 vs_battlejake.py main.py <N>` (created; games run LONG, N<=12 for 30s cmd timeout;
  use nohup+poll for larger N). A/B harness: `/tmp/ab_bj.py <N>` (NEW=main.py vs OLD=backup vs opp,
  identical seeds).
- **Round 0 result: won 226-24** (~90%). Analyzed all 24 losses (`analyze_losses.py`): the CHRONIC
  self-coil vector — **20/24 losses OPUS was LONGER** (L11-29 vs OPP L9-21), ~18/24 die on an
  EDGE/CORNER, HIGH health (90+). We coil our body into a bottom/right/corner pocket while the
  SHORTER opponent slowly walls off our escape to the open board = ENEMY-ASSISTED SEAL.
  Traced sim_101: L18 hp95 ran down into the bottom-left, coiled, got funneled right along y=1
  into corner (10,0) while OPP L13 body occupied y=2-3 blocking the top escape. Died T151.
- **Change (backup: main_r0_battlejake_backup.py = git HEAD pre-change bot):** made the
  ENEMY-AWARE DEEP SURVIVAL horizon LENGTH-SCALED (was fixed 4-step enemy reach + depth-8):
    - `e_steps = min(9, 4 + max(0,(my_len-12))//3)` (4 at L12, up to ~7-8 when long)
    - `e_depth = min(14, 8 + max(0,(my_len-12))//3)`
  The enemy walls off our escape over ~10 turns; a fixed 4-step reach + depth-8 can't see the
  seal when we're long. Scaling both with length gives more foresight to detect the enemy-assisted
  seal earlier and steer toward the open board.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace python3
  fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.13 (<500 limit); L22 edge board decision 2.25ms
  (safe). A/B vs real opp on IDENTICAL seeds (N=16, /tmp/ab_bj.py): NEW 12-1-3 vs OLD 13-3-0 —
  **losses dropped 3->1** (converted to draws/wins), win count even within noise, ZERO regression.
- **Next teammate:** opponent = opp_battlejake.py (2019 port, stays short, outlasts us). Our ONLY
  loss vector is the LONG+healthy self-coil into an edge/corner pocket that the shorter enemy
  seals. If losses persist: (a) raise e_steps/e_depth caps further (watch timing, L22=2.25ms so
  room), (b) the canonical TRUE Hamiltonian tail-follow when long+safe is STILL the ideal
  unimplemented fix (cycle the board tightly instead of coiling). Analyze new losses:
  `cd /logs/rounds/N && python3 /workspace/analyze_losses.py sim_*.jsonl | grep -vi ...` (find
  non-opus winners first). main.py has all prior layers + now length-scaled enemy-reach anti-seal.

## Round 2 of 5 (this task, opus-4-8) — battlejake2019, TESTED EDGE-SHADOW FIX, REVERTED (regressed)
- Opponent STILL `joshhartmann11__battlejake2019` (2019 port, stays SHORTER, outlasts us;
  opp_battlejake.py). Results: round 0 won 226-24, round 1 won 236-13 (~94.8%).
- **Loss analysis (round 1, 13 losses, analyze_losses.py):** 12/13 OPUS was LONGER (L12-35 vs
  L11-33), ~11/13 on EDGE/CORNER, high health — the CHRONIC long+healthy self-coil / enemy-
  assisted seal vector. ONE exception: sim_129, an EARLY L4 loss at turn 18 — OPUS ran along
  the TOP edge (y=10) toward the right corner while a LONGER OPP shadowed one lane inward (y=9)
  heading to the SAME corner, sealing the wall corridor -> forced H2H at the corner. The wrong
  decision was T13 (head (3,10)): bot went RIGHT (into the shadow, toward corner) instead of
  LEFT (away, open board). The edge-shadow penalty didn't fire because the "run" toward the
  corner was long (~6 cells) so `run < my_len` was False.
- **Tried (backup: main_r1of5_battlejake_r2_backup.py = committed bot):** added a PARALLEL-
  SHADOW-INTO-CORNER penalty: when moving ALONG an edge toward a corner with a >=our-length
  enemy on the adjacent inward lane, close, and paralleling us toward that corner, penalize.
  - At -220 / edist<=4 it FIXED sim_129 T13 (picks left) BUT A/B vs real opp on identical seeds
    (N=20, /tmp/ab_bj2.py) REGRESSED: NEW 9-4-7 vs OLD 15-1-4. Too aggressive — it steered the
    bot into worse positions when the shadow wasn't actually a trap.
  - Tightening to -120 / edist<=2 / room<=my_len+1 made it safe but then it NO LONGER catches
    sim_129 (edist=3 at the key frame). No net benefit.
- **Decision: REVERTED to committed main.py.** The proven ~95% bot is better than a change that
  regressed in A/B. sim_129 is a single early-game edge-shadow-H2H (1/13 losses); the fix for it
  costs more than it gains. Verified reverted bot: syntax OK; sim_test 40 => 40/0/0; fuzz =>
  crashes=0 illegal=0 maxt_ms=16.2.
- **Next teammate:** opponent = opp_battlejake.py. Our dominant loss vector is STILL the long+
  healthy self-coil into an edge/corner pocket that the shorter enemy seals (12/13). Scalar/
  positional tweaks keep proving NOISE-FLOOR or regressive (as ~all prior teammates found). The
  ONLY likely real win is the canonical TRUE HAMILTONIAN tail-follow when long+safe (cycle the
  board tightly instead of coiling) — STILL unimplemented after many rounds. If you attempt it:
  gate behind long+space-safe, A/B carefully across MULTIPLE seed batches (`/tmp/ab_bj2.py N`
  compares main.py NEW vs main_r1of5_battlejake_r2_backup.py OLD, both vs opp, identical seeds;
  games run LONG so use nohup+poll, N~20 takes ~2min). Do NOT ship anything that A/B-regresses
  vs the committed bot — we win ~95% and regression risk isn't worth marginal single-game fixes.
  main.py has all prior layers (time-aware flood fill, tail-reach BFS, 2-ply best/worst space,
  enemy-contested space, H2H follow-up, length-scaled edge/corner + edge-shadow, safety-aware
  food, CRITICAL starvation, Voronoi, deep self-survival sim, enemy-aware deep sim length-scaled,
  clearly_ahead food-avoid, tail-follow anti-coil).

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `coreyja__famished-frank` (STRONG A*-GROWER), NO CODE CHANGE
- **Opponent = `coreyja__famished-frank`** — a Rust A*-based port. Real source saved to
  `opp_famished_frank.py` (git show origin/human/coreyja/famished-frank:main.py, 231 lines).
  Strategy: A* (Dijkstra) to the NEAREST food while `len < target_length` where
  `target_length = height*2 + width = 33`. Once L33 it patrols the 4 CORNERS. It blocks only
  current snake BODY cells — **it has NO head-to-head avoidance and no space/flood management.**
  It is a STRONG, AGGRESSIVE GROWER (reaches L15-33) that out-lengths us. Test harness:
  `python3 vs_famished.py main.py <N> [seedoff]` (created; games run LONG, N<=14 for the 30s
  cmd timeout, or `nohup ... &` + poll for larger N). sim is HARSHER than real (~67% sim vs 82% real).
- **Round 0 result: won 204-44 +2T** (~82%). Analyzed all 46 losses (`analyze_losses.py`):
  **41/46 losses OPUS was SHORTER at death** (OPUS L11-25 vs OPP L15-33); 2 equal, 3 longer.
  LONG games (turn 49-266). ROOT CAUSE = famished OUT-GROWS us (aggressive A*-to-food to L33)
  and out-lasts / cuts us off / H2H-kills us as the bigger snake. This is the growth-race loss
  vector (same as cornelius/elon), NOT our chronic self-coil vector.
- **Experiments A/B'd vs real opp (background nohup, identical seeds):**
  1. variant (`_pace_margin` 8/6->12/8 AND truly_behind food d_after*9->11, +85->100):
     NEW 10-6 vs OLD 12-4 (N=16) — **REGRESSED.** Over-aggressive food chasing walks into traps.
  2. variant2 (`_pace_margin` 8/6->10/7 only, no food-weight change): NEW 13-7 vs OLD 13-7
     (N=20) — EXACTLY NEUTRAL (noise-floor).
  => Growth boosts either regress (food-weight) or are noise (pace-margin), consistent with what
  ~all prior growth-opponent teammates (cornelius/elon/flipez) found. Scalar tweaks don't move
  the needle and carry regression risk.
- **Decision: NO code change.** Kept the proven ~82% bot stable. Verified: syntax OK;
  `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0
  illegal=0 maxt_ms=16.09; `vs_famished.py main.py 24 99` => 16-7-1 (~67% sim, matches baseline).
- **Next teammate — POTENTIAL UNEXPLORED LEVER (structural, not scalar):** famished-frank has
  **ZERO head-to-head avoidance** and walks A*-predictably toward its nearest food. When we are
  EQUAL or LONGER we already get +200 for H2H-win cells (we exploit this). The real problem is
  being SHORTER. Ideas: (a) SMARTER growth — since naive food-weight boosts regress (we dive into
  contested/trap food), try growing only on UNCONTESTED food (we're strictly closer) via a
  DEDICATED early-game growth push (first ~40 turns) that A/B-validates on MULTIPLE seed batches;
  (b) since famished is PREDICTABLE (A* to nearest food, no H2H), you can PREDICT its path and
  bait it into an H2H-loss cell / cut it off from food when we're near-equal length; (c) the
  canonical TRUE Hamiltonian tail-follow when long+safe (still unimplemented) for the 3 longer
  losses. A/B ANY change across MULTIPLE seed batches (change the seed offset arg) — single-batch
  is misleading (proven repeatedly). Use `nohup python3 -u vs_famished.py <bot> <N> <off> &` + poll.
  main.py has all prior layers (time-aware flood fill, tail-reach BFS, 2-ply best/worst space,
  enemy-contested space, H2H follow-up, length-scaled edge/corner + edge-shadow, safety-aware
  food, CRITICAL starvation, Voronoi, deep self-survival sim, enemy-aware deep sim length-scaled,
  clearly_ahead food-avoid, tail-follow anti-coil, opponent-adaptive keep-pace growth).

## Round 2 of 5 (this task, opus-4-8) — famished-frank, RE-CONFIRMED NO CODE CHANGE (growth tweaks = noise/regressive)
- Opponent STILL `coreyja__famished-frank` (STRONG A*-to-nearest-food grower, target_length=33,
  ZERO H2H avoidance, no space mgmt; opp_famished_frank.py). Results: round 0 won 204-44+2T,
  round 1 won 190-57+3T (~76.8%).
- **Loss analysis (round 1, ALL 57 losses, /tmp/losscount.py + /tmp/opplen.py):** UNAMBIGUOUS &
  unchanged — in **57/57 losses OPUS was SHORTER at death** (0 equal, 0 longer). Opponent final
  lengths mostly L12-30 (still GROWING, below its L33 patrol cap) — the growth race is lost
  MID-GAME. famished out-grows us via pure efficient A*-to-food and out-lasts/cuts us off as the
  bigger snake. Pure growth-race vector (same as cornelius/elon/flipez), NOT self-coil.
- **Experiments A/B'd vs real opp on IDENTICAL seeds (/tmp/ab_ff.py NEW=main.py vs OLD=committed):**
  1. truly_behind trigger max_enemy_len>=12 -> >=8 (chase food earlier mid-game): batch1(off1)
     NEW 9-2-1 vs OLD 10-1-1; consistently slightly WORSE. Reverted.
  2. truly_behind food weights d_after*9->12, +85->100 (chase harder): batch1 NEW 9-2-1 vs OLD
     10-1-1; batch2(off101) NEW 7-5-0 vs OLD 8-4-0. Consistently slightly WORSE. Reverted.
  - Sanity: committed-vs-committed A/B swings 1 game (8-4 vs 7-5) = pure noise floor.
  => Growth/food tweaks are NOISE-FLOOR or slightly regressive, EXACTLY as the round-0/1 famished
  teammate AND all prior growth-opponent teammates (cornelius/elon/flipez) found. The sim
  MAINTAINS min-1 food (does NOT flood food like the real engine over long games), so it CANNOT
  reproduce the mid-game growth race — aggressive food-chasing in the sim just walks into traps
  (hence the small regressions). No reliable way to validate a growth boost in this env.
- **Decision: NO code change.** Kept the proven ~77-82% bot stable; every tweak tested was noise
  or regressive, and regression risk on a winning bot isn't worth it. Verified: syntax OK;
  `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace python3 fuzz_test.py` => crashes=0
  illegal=0 maxt_ms=16.11; main.py byte-identical to committed.
- **Next teammate — the ONLY promising UNEXPLORED lever is STRUCTURAL, not scalar:** famished-frank
  has **ZERO H2H avoidance** and walks A*-PREDICTABLY toward its NEAREST food (its A* path filter
  blocks only current body cells, not head danger/space). Two structural ideas (both need careful
  multi-seed A/B — but note the sim can't reproduce the real growth race, so validate by DESIGN +
  frame-replay of /logs losses, NOT sim win-rate):
  1. **PREDICT + INTERCEPT its food:** compute famished's A* next step (we have opp_famished_frank.py
     — could import its `_a_prime_next_direction`) and, when we're near-equal length, either grab the
     contested food FIRST (we're closer) or set up an H2H-win cell on its predicted path (we already
     give +200 for H2H-win cells; steer TOWARD its predicted head cell when we're strictly longer).
  2. **SAFE early growth push:** the race is lost mid-game (opp L12-30 while growing). A dedicated
     first-~40-turn growth mode that eats ONLY strictly-uncontested food (we're strictly closer,
     ed>d) to build a lead WITHOUT walking into contested-food traps (which caused the sim
     regressions above). Gate it to only fire early + uncontested so it can't self-trap.
  A/B ANY change across MULTIPLE seed batches (`python3 /tmp/ab_ff.py <N> <off>`, offs 1/101/555;
  games run LONG so N<=12 fits the 30s cmd timeout, or nohup+poll). Do NOT ship anything that
  A/B-regresses vs committed. main.py has all prior layers (time-aware flood fill, tail-reach BFS,
  2-ply best/worst space, enemy-contested space, H2H follow-up, length-scaled edge/corner +
  edge-shadow, safety-aware food, CRITICAL starvation, Voronoi, deep self-survival sim, enemy-aware
  deep sim length-scaled, clearly_ahead food-avoid, tail-follow anti-coil, opponent-adaptive
  keep-pace growth). Backup: main_r0_famished... none created (no change); use git HEAD.

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `kentmacdonald2__beames` (A* GROWER, NO H2H/SPACE), NO CODE CHANGE
- **Opponent = `kentmacdonald2__beames`** — a 2017 Advanced-division A* port. Real source saved
  to `opp_beames.py` (git show origin/human/kentmacdonald2/beames:main.py, 209 lines). Strategy:
  rank food by squared-Euclidean dist to head, A* (squared-euclid heuristic, count>499 bailout)
  to NEAREST food, quirky second-food fallback, then desperation = first safe neighbor in fixed
  order up/down/left/right. `_if_safe` = on-board AND not in ANY snake body cell. **CRITICAL
  WEAKNESSES: ZERO head-to-head avoidance, ZERO space/flood management, blocks ALL body cells
  (incl. tails).** It's an AGGRESSIVE nearest-food grower (reaches L20-34) that OUT-GROWS us.
  Test harness: `python3 vs_beames.py main.py <N> [seedoff]` (created; N<=14 for 30s cmd timeout).
- **Round 0 result: won 188-59 +3T** (~75%). Analyzed all 59 losses (/tmp/beames_analysis.py —
  rebuild: counts shorter/equal/longer at death across /logs/rounds/0/sim_*.jsonl):
  **58/59 losses OPUS was SHORTER at death** (0 equal, 1 longer). Beames out-grows us via
  aggressive nearest-food A* and out-lasts/H2H-kills us as the bigger snake. ~1/3 of losses are
  NEAR-EQUAL length (L4v5, L5v6, L7v8, L11v12, L18v19) = growth-race + forced-H2H at edges;
  the rest are pure growth-race blowouts (L14v24, L19v34). This is the SAME growth-race vector
  as cornelius/elon/famished, NOT our chronic self-coil vector.
- **Experiments A/B'd vs real opp on IDENTICAL seeds (/tmp/ab_beames.py NEW=main.py mod vs
  OLD=committed, alternates start):** boosted truly_behind food weight d_after*9->12 / +85->105
  AND behind_or_even *7->9 / +70->90. Batch1(off1): NEW (8,3,1) vs OLD (8,3,1). Batch2(off101):
  NEW (9,3,0) vs OLD (9,3,0). => BYTE-IDENTICAL results = pure NOISE-FLOOR, exactly as every
  prior growth-opponent teammate (cornelius/elon/flipez/famished) found. The sim spawns food at
  15%/turn (does NOT flood like the real engine over long games), so it CANNOT reproduce the
  mid-game growth race — growth tweaks don't move the sim needle. Reverted.
- **Verified the H2H-race loss is ALREADY handled:** reconstructed sim_2 T17 (OPUS L4 @(7,10)
  top edge, OPP L5 @(8,9), both racing food @(9,10)) in /tmp/test_t17.py — the CURRENT bot picks
  DOWN (peels off the edge, away from the H2H-loss cell (8,10)), NOT right into the trap. So the
  near-equal H2H-race losses are largely already avoided by the safety-aware food ranking +
  edge/corner penalties; the historical losses were slightly different frames / earlier commits.
- **Decision: NO code change.** Kept the proven ~75% bot stable. Growth tweaks are noise/
  regression-risk (proven), the sim can't validate them, and the addressable H2H-race pattern is
  already handled. Verified: syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace
  python3 fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.13; main.py byte-identical to committed.
- **Next teammate — the ONLY promising UNEXPLORED lever is STRUCTURAL (beames is fully
  DETERMINISTIC + has ZERO H2H/space awareness):**
  1. **PREDICT + EXPLOIT:** import opp_beames.py's `_decide`/`_search` to predict beames' EXACT
     next move (it always A*'s to nearest food). When we're EQUAL or LONGER, steer TOWARD its
     predicted head cell to force an H2H-win (we already give +200 for h2h_win cells; make the
     enemy_next model use beames' PREDICTED single cell, not all 4 neighbors, so we can
     aggressively contest it). When SHORTER, use the prediction to grab the contested food FIRST
     if we're strictly closer, or dodge its predicted cell.
  2. **CUT IT OFF when longer:** beames has no space management and blocks all body cells (incl.
     tails) — so when we're longer we can body-block it into a dead-end / shrink its Voronoi
     (we already have `_voronoi_owned`). It cannot escape a seal it can't foresee.
  3. **SAFE early growth:** the race is lost because we start/stay behind. A dedicated first-~40-
     turn growth mode eating ONLY strictly-uncontested food (ed>d) could build a lead without the
     contested-food traps that make naive food boosts regress. Gate to early+uncontested.
  A/B ANY change across MULTIPLE seed batches (`python3 /tmp/ab_beames.py <N> <off>`, offs 1/101/
  555; N<=14 for the 30s cmd timeout). Do NOT ship anything that A/B-regresses vs committed — we
  win ~75% and the sim can't validate growth-race changes (validate structural exploits by DESIGN
  + frame-replay of /logs losses + no-regression). main.py has all prior layers (time-aware flood
  fill, tail-reach BFS, 2-ply best/worst space, enemy-contested space, H2H follow-up, length-
  scaled edge/corner + edge-shadow, safety-aware food, CRITICAL starvation, Voronoi, deep
  self-survival sim, enemy-aware deep sim length-scaled, clearly_ahead food-avoid, tail-follow
  anti-coil, opponent-adaptive keep-pace growth). Tools: vs_beames.py, /tmp/ab_beames.py,
  /tmp/beames_analysis.py, /tmp/test_t17.py (rebuild from this note if /tmp cleared).

## Round 2 of 5 (this task, opus-4-8) — beames, EARLY-GAME ANTI-CORNER-FOOD (low-risk)
- Opponent STILL `kentmacdonald2__beames` (A* nearest-food grower, ZERO H2H/space awareness;
  opp_beames.py). Results: round 0 won 188-59+3T, round 1 won 181-63+6T (~74%).
- **Loss analysis (round 1, 63 losses, analyze_beames.py -> /tmp/ab1.py):** 61/63 OPUS SHORTER
  at death; by turn 30 we're avg L5.8 vs opp L7.6 (already behind in 44/57). TRACED sim_165
  (L4v5, died T18): the ONLY food was in the bottom-right corner (9,0); our L4 snake chased it
  along the bottom edge into the corner and got trapped by the closer/longer opponent. Early-game
  corner-food death, NOT overgrowth.
- **Changes (backup: main_r2of5_beames_backup.py = git HEAD pre-change bot):**
  1. Lowered `long_on_edge` threshold 8 -> 5 (short snakes also get anti-wall-hug/corner-approach).
  2. Added EARLY-GAME ANTI-CORNER penalty: moving ONTO an edge cell within 2 of a corner, when
     an enemy head is within 4, subtracts (3-d_corner)*12 (gated: not critical/starving).
  3. Added `corner_food_trap` flag: when the chosen food is edge/corner-risk (>=1) AND contested
     (enemy as close/closer) AND we're not longer -> DAMPEN food pull (truly_behind d_after*9->2,
     behind_or_even *7->1.5, no on-food bonus). Steers us off contested corner food to open board.
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace fuzz`
  => crashes=0 illegal=0 maxt_ms=16.16. A/B vs real opp (/tmp/ab_beames.py, offs 1/101/555, N~12)
  = IDENTICAL to committed (noise floor; sim can't reproduce the corner-food-flood trap, as all
  prior beames/growth teammates found). NOTE: on the exact sim_165 frames the bot STILL runs into
  the corner (trap already committed by T14, space/flood favors it) — the change is a general
  low-risk safety net for the EARLIER approach, validated by design + sim_test + fuzz + no-regression.
- **Next teammate:** opponent = opp_beames.py (deterministic A* grower, ZERO H2H/space). Our loss
  vector = being SHORTER + early corner-food death. Scalar growth tweaks are NOISE (proven many
  rounds). The unexplored STRUCTURAL lever: PREDICT beames' exact next move (import opp_beames.py)
  and force H2H-wins when equal/longer, or grab contested food FIRST when strictly closer. main.py
  has all prior layers + now early-game anti-corner-food damping. A/B ANY change multi-seed vs real
  opp; do NOT ship regressions (we win ~74%).

## Round 1 of 5 (this task, opus-4-8) — NEW OPPONENT `TheApX__hungry`, ADDED DETERMINISTIC-H2H INTERCEPT EXPLOIT
- **Opponent = `TheApX__hungry`** ("The Very Hungry Caterpillar", C++ port). Source saved to
  `opp_hungry.py`. Strategy: multi-source BFS from all food -> distance-to-nearest-food for every
  cell; picks the head-neighbor with the smallest food-distance (order L,R,U,D). Blocks body cells
  (tails enterable). **DETERMINISTIC. ZERO head-to-head avoidance. ZERO space/flood management.**
  Food-greedy GROWER (reaches L16-33). Test: `python3 vs_hungry.py main.py <N> [off]` (sim harsher,
  ~58% vs 82% real). A/B: `python3 /tmp/ab_hungry.py <N> <off>` (NEW=/tmp/new_main vs OLD=/tmp/old_main).
- **Round 0 result: won 204-43 +3T** (~82%). Loss analysis (/tmp/wins.py): **45/46 losses OPUS was
  SHORTER at death** (OPUS L8-19 vs OPP L12-33). Same growth-race vector as cornelius/elon/famished/
  beames — the food-greedy opponent out-grows us and out-lasts / cuts us off / H2H-kills us.
- **Change made (backup: main_r0_hungry_backup.py = git HEAD pre-change bot):** exploited the
  opponent's DETERMINISM + ZERO H2H avoidance. Added `predicted_enemy_cell`: import opp_hungry and
  call its `move()` from the opponent's perspective to get its EXACT next head cell. In scoring,
  when we're STRICTLY LONGER (my_len > max_enemy_len, not critical/starving): +260 if our candidate
  cell IS the predicted enemy cell (guaranteed H2H win — it won't dodge), +40 if adjacent (intercept
  setup). This forces H2H kills when ahead, since it never yields. Fully gated: does NOTHING when
  we're shorter/equal (h2h_loss -1000 guard still protects us — verified we go UP not into the H2H
  loss when L3 vs L5).
- **Verification:** syntax OK; `python3 sim_test.py 40` => 40/0/0; `PYTHONPATH=/workspace python3
  fuzz_test.py` => crashes=0 illegal=0 maxt_ms=16.28. UNIT TESTS (/tmp/test_pred*.py): when L5 vs L3
  with food between, opponent moves left to food cell and WE correctly move RIGHT to intercept for a
  guaranteed H2H win; when L3 vs L5 we correctly AVOID the H2H-loss cell (go up). A/B vs real opp on
  3 seed batches (off 1/101/555, N=12): NEW == OLD exactly (7-4-1, 12-0-0, 7-3-2) — NO regression;
  the sim rarely reproduces the intercept scenario (games resolve fast / sim doesn't food-flood),
  so the exploit is validated by DESIGN + unit tests + no-regression (as all prior growth-opponent
  teammates found the sim can't validate these changes).
- **Next teammate:** opponent = opp_hungry.py (DETERMINISTIC food-greedy grower, ZERO H2H/space).
  Our loss vector = being SHORTER (out-grown). This round adds the deterministic H2H intercept
  exploit (fires only when longer). If losses persist and we're STILL shorter, the remaining lever
  is SAFE early growth (the sim can't validate scalar growth tweaks — proven noise-floor for
  cornelius/elon/famished/beames — but this opponent is deterministic so you can also PREDICT +
  grab contested food FIRST when strictly closer using predicted_enemy_cell). Consider extending the
  intercept: when we're longer, actively CUT OFF its food path (body-block) using the prediction +
  Voronoi. main.py has all prior layers + now the deterministic-opponent H2H intercept. A/B multi-seed
  via /tmp/ab_hungry.py; do NOT ship regressions (we win ~82%).
