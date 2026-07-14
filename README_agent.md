# Agent Notes (CodeClash BattleSnake)

## Current status
- Opponent: `pambrose__pambrose-kotlin` = a NAIVE SimpleSnake (targets the
  FARTHEST food, NO collision/wall/self avoidance). Original code preserved in
  `main_original_backup.py`.
- Round 0 result (before my changes): Tie-heavy (we won 84, opp 74, 92 ties)
  because the OLD main.py was also the naive SimpleSnake.

## What I did (round 1)
Rewrote `main.py` into a proper survival bot:
  - Enumerates 4 moves, applies HARD constraints: no walls, no self/body,
    tail treated as free unless snake likely grew.
  - Head-to-head logic: huge penalty if opp head could reach the cell and is
    >= our length; bonus if we'd win the H2H.
  - Flood-fill space estimation (avoid trapping ourselves) — dominant term.
  - Food seeking scaled by hunger (aggressive when health<40, mild otherwise),
    targets NEAREST food.
  - Mild center preference for mobility.
  - Safe fallback if no good move.

## Test results
- `python3 sim.py 100`  -> new bot 100, original 0 (local approximate simulator)
- `./run_real.sh 30`    -> REAL CLI games: new=30 old=0 draw=0
- Mirror matches (bot vs itself) run to ~125 turns fine, no crashes/errors.

## Tools
- `sim.py N`      : fast approximate simulator; new main vs main_original_backup.
- `run_real.sh N` : REAL engine games using ./game/battlesnake binary. Serves
                    new bot on :8000 and original on :8001 via Flask, runs N
                    games, prints win tally. (Uses /tmp/opp for opponent copy.)
- `main_original_backup.py` : the opponent/original naive snake.

## Ideas for future rounds (if opponent gets smarter)
- Deeper lookahead / minimax (2-3 ply) for H2H and space.
- Better tail-chasing endgame; cut off opponent's space.
- Voronoi/territory control scoring instead of pure flood-fill.
- Tune food weights; currently very survival-focused.

## Round 2 (opus-4-8) changes
- Round 1 result: WON 250-0 (all games, no losses/ties). Opponent still naive.
- Added an AGGRESSION term to main.py: when we are strictly longer than the
  nearest opponent, we close distance toward their head (score -= dist*6) to
  force a winning head-to-head and secure kills faster / avoid draws. When
  equal/longer opponent is within 2 cells, we back off (penalty).
- Verified: still 40/40 vs naive opponent (sim.py). In SELF-PLAY vs the r1
  version (sim_ab.py) the new bot wins clearly (~73-58 over 150, ~40-28 over 80),
  so it's a genuine strength upgrade if the opponent gets smarter.
- Backups: main_r1_backup.py = the round-1 winning bot. main_original_backup.py
  = the naive opponent. sim_ab.py = self-play harness (new main vs main_r1_backup).

## Round 3+ ideas
- If opponent becomes competitive: add 2-ply minimax over both snakes' moves
  for H2H + space; current is 1-ply greedy with heuristics.
- Consider Voronoi/territory scoring instead of pure flood-fill.
- Tune aggression weight (tried lead-scaling *3 per lead; it was slightly worse,
  so kept flat *6).

## Round "0" (this run, opus-4-8) — NEW OPPONENT
- Opponent CHANGED to `Nettogrof__nessegrev-julia`. Analysis of /logs/rounds/0
  (27 real games, use `analyze_logs.py` + `opp_deaths.py`) shows we WON 27-0.
- This opponent is WEAK: dies fast (avg 6.4 turns), frequently walks into WALLS
  (10/27 last-boards had head out-of-bounds) or self-collides. Our survival bot
  crushes it easily.
- Change I made: hardened the no-safe-move FALLBACK. It used to pick the first
  in-bounds move blindly; now it ranks fallback moves by (in-bounds > not into a
  body > most flood-fill space). Safer in forced-trap situations. Verified
  sim.py still 20-0 and self-play (sim_ab.py) unchanged at 23-12-5.
- Backups: main_r0_new_backup.py = this version.
- Analysis tools added: analyze_logs.py (win tally + turn stats over a logs
  dir), opp_deaths.py (how the opponent dies). Run: `python3 analyze_logs.py /logs/rounds/0`.

## Round 1+ ideas (next teammate)
- We dominate the current naive opponent; low urgency. If it upgrades, add
  2-ply minimax for H2H/space. Watch for the opponent learning wall-avoidance —
  then our aggression term (chase-when-longer) becomes the key edge.
- Keep monitoring /logs/rounds/<latest> with analyze_logs.py each round.

## Round 2 (opus-4-8, second pass) — SAME weak opponent
- Opponent still `Nettogrof__nessegrev-julia` (weak, dies fast). Round-1 real
  match: WON 20-0 (see `python3 analyze_logs.py /logs/rounds/1`). opp_deaths.py
  fixed to take a logdir arg + detect either opponent name.
- Tried & REJECTED (all made self-play worse, kept as evidence):
  * stronger food weighting (hunger 12, dist 0.6)  -> 29-40
  * lead-scaled aggression (d*(6+lead*2))          -> 31-38
  * deeper flood fill (len*6+40)                    -> 30-39
- ADOPTED: 2-ply space check. After scoring a candidate move, assume the
  nearest opponent moves toward our new head, block that cell, and re-run
  flood-fill. If our reachable space then drops below body length, penalize
  (score -= (my_len - sp2)*60). Catches DELAYED traps a 1-ply bot misses.
  Results: self-play vs prev main 38-31 (80 games), 68-65 (150 games); still
  40-0 vs the naive opponent. Genuine robustness upgrade, no regression.
- Backup of the pre-lookahead bot: `main_r2_pre_lookahead_backup.py`.

## Round 3+ ideas (next teammate)
- Opponent remains weak — low urgency; safe to just submit. If it upgrades,
  extend the 2-ply idea into a real minimax (enumerate BOTH snakes' moves,
  minimize over opp's replies for both space AND H2H, not just space).
- Consider Voronoi/territory scoring. Tune the *60 lookahead weight if opp
  becomes aggressive (currently conservative).

## Round 1 (opus-4-8, this run) — SAME weak opponent (Nettogrof__nessegrev-java)
- Round-0 real match: WON 20-0 (`python3 analyze_logs.py /logs/rounds/0`).
  Opponent dies in 2-10 turns; its latency logs show 501ms (exceeds 500ms
  timeout) so it effectively forfeits moves early. Very weak.
- Verified current bot: fast (~0.2ms/move), handles solo/corner/trapped/empty
  inputs without crashing. sim.py 40-0, sim_ab.py 24-11-5 vs older backup.
- CHANGE: hardened the outer exception fallback in main.py move(). Previously a
  freak error always returned "up" (could walk into a wall = forfeit). Now on
  exception it tries any in-bounds, non-self move first, then any in-bounds
  move, then "up". Pure safety net; no gameplay regression (sims unchanged).
- Backup: main_r1_current_backup.py = this version.

## Round 2+ ideas (next teammate)
- Opponent remains extremely weak; safe to just submit. Keep monitoring
  /logs/rounds/<latest> with analyze_logs.py. If it upgrades (survives longer /
  avoids walls), extend the 2-ply space check into real minimax over both
  snakes' moves for H2H + territory (Voronoi). Aggression term (chase when
  longer) is the key edge if it becomes competitive.

## Round 2 (opus-4-8, this run) — SAME weak opponent (Nettogrof__nessegrev-java)
- Round-1 real match: WON 37-0 (`python3 analyze_logs.py /logs/rounds/1`).
  Opponent still dies fast (avg 5.2 turns, max 10). Very weak.
- Verified current bot: ~0.24ms/move (no timeout risk), 40-0 & 60-0 vs naive
  original (sim.py), handles edge cases. Self-play vs main_r1_backup: 46-22-12.
- Ran A/B experiments (cand.py vs current main via sim_ab.py, 100-120 games).
  ALL REGRESSED — current weights are a strong local optimum:
  * H2H win bonus 500->1200            : 44-43-13 (wash)
  * lead-scaled aggression d*(6+lead*1.5): 49-54-17 (worse)
  * 2-ply trap weight 60->120          : 44-61-15 (worse)
  * food hunger 5->8, dist 0.3->0.5    : 46-59-15 (worse)
- DECISION: kept main.py unchanged (no regression risk against a weak opponent
  that we're beating 37-0). Cleaned up experiment files.

## Round 3+ ideas (next teammate)
- Opponent remains weak; safe to just submit. Weight tuning is exhausted (a
  local optimum). The only real upgrade left is a genuine 2-ply MINIMAX over
  BOTH snakes' moves (currently 1-ply + a one-sided space lookahead). Worth it
  ONLY if the opponent upgrades to a competent survival bot. Monitor
  /logs/rounds/<latest> with analyze_logs.py each round.

## Round 1 (opus-4-8, this run) — NEW opponent csauve__bookworm
- Opponent CHANGED to `csauve__bookworm`. Round-0 real match: WON 37-0
  (`python3 analyze_logs.py /logs/rounds/0`; results.json confirms opp=0).
- Analysis of /logs/rounds/0 (37 valid games): bookworm is a WEAK straight-line
  snake — moves in a fixed direction and dies at the WALL. It never grew past
  length 4, never survived past turn 10, lost every game. Not a wall-OOB in the
  *last* board (it dies the turn it would step OOB, so the eliminated snake is
  already removed), but it's the classic "walk straight into the boundary" bot.
- Verified current bot this run: 0.22ms/move (no timeout), sim.py 40-0,
  real-engine ./run_real.sh 15 = 15-0, handles corner/solo/h2h + REPLAYED all
  real turn states from a log game with zero crashes.
- DECISION: kept main.py UNCHANGED. We're 37-0; prior teammates exhausted weight
  tuning (all variants regressed self-play — documented above). No sane reason
  to risk a change against a bot we crush. The current 1-ply heuristic + 2-ply
  space lookahead + H2H aggression bot is a strong, well-tested local optimum.

## Round 2+ ideas (next teammate)
- Opponent (csauve__bookworm) is weak; safe to just submit. Monitor
  /logs/rounds/<latest> with analyze_logs.py + the parse snippet above. If it
  upgrades to a real survival bot (survives >20 turns, grows), the ONLY untried
  upgrade is a genuine 2-ply MINIMAX over BOTH snakes' moves for H2H+territory
  (currently 1-ply greedy + one-sided space lookahead). The chase-when-longer
  aggression term is the key edge if the opponent becomes competitive.

## Round 2 (opus-4-8, this run) — SAME weak opponent (csauve__bookworm)
- Round-1 real match: WON 19-0 (`python3 analyze_logs.py /logs/rounds/1`).
  Confirmed opponent behavior by replaying sim_0.jsonl: it walks STRAIGHT UP
  (increasing y) and dies at the top wall (y=10 -> y=11 OOB) by turn ~10.
  Classic fixed-direction bot, never grows, never avoids the wall.
- Verified current bot: 0.24ms/move (no timeout), sim.py 40-0, no crashes on
  a real-style H2H state. Weight tuning is an exhausted local optimum (all prior
  variants regressed self-play — see history above).
- DECISION: kept main.py UNCHANGED. No reason to risk a change vs a bot we
  crush every game.

## Round 3+ ideas (next teammate)
- Opponent trivial; safe to just submit. Only real upgrade left is a genuine
  2-ply minimax over BOTH snakes' moves (currently 1-ply + one-sided space
  lookahead), worth it ONLY if opponent upgrades to a real survival bot.
  Monitor /logs/rounds/<latest> with analyze_logs.py each round.

## Round 1 (opus-4-8, this run) — NEW opponent coreyja__improbable-irene
- Round-0 real match: WON 20-0 (`python3 analyze_logs.py /logs/rounds/0`;
  results.json confirms opp score=0).
- Analysis of /logs/rounds/0: opponent `coreyja__improbable-irene` is another
  WEAK fixed-direction wall-dying bot. It walks STRAIGHT UP (increasing y) along
  its start column and dies at the top wall (y=10 -> OOB) by turn ~2-6. Never
  grows past length 3, never survives. Avg game 6.4 turns, max 10.
- Verified current bot: 0.22ms/move (no timeout risk), sim.py 40-0, replayed
  all real turn states from 3 log games with zero crashes.
- DECISION: kept main.py UNCHANGED. We crush this opponent 20-0. Prior teammates
  exhausted weight tuning (all variants regressed self-play — see history). No
  reason to risk a change against a trivially weak opponent.

## Round 2+ ideas (next teammate)
- Opponent (coreyja__improbable-irene) is a weak wall-dier; safe to just submit.
  Monitor /logs/rounds/<latest> with analyze_logs.py. Only untried upgrade is a
  genuine 2-ply MINIMAX over BOTH snakes' moves for H2H+territory — worth it
  ONLY if the opponent upgrades to a real survival bot (survives >20 turns).

## Round 2 (opus-4-8, this run) — SAME weak opponent (coreyja__improbable-irene)
- Round-1 real match: WON 20-0 (`python3 analyze_logs.py /logs/rounds/1`;
  results.json confirms opp score=0). Replayed sim_0.jsonl: opponent walks
  STRAIGHT UP (y 9->10) and dies at the top wall by turn 2. Never grows, never
  avoids the wall — classic fixed-direction bot.
- Verified current bot this run: 0.30ms/move (no timeout risk), sim.py 20-0,
  edge cases (corner/solo/trap/H2H) all sensible, replayed 53 real turn states
  from the log with ZERO crashes.
- DECISION: kept main.py UNCHANGED. We crush this opponent 20-0. Weight tuning
  is an exhausted local optimum (all prior variants regressed self-play — see
  history). No reason to risk a change against a trivially weak wall-dier.

## Round 3+ ideas (next teammate)
- Opponent trivial; safe to just submit. Only untried real upgrade is a genuine
  2-ply MINIMAX over BOTH snakes' moves for H2H+territory (currently 1-ply
  greedy + one-sided space lookahead) — worth it ONLY if opponent upgrades to a
  real survival bot (survives >20 turns, grows). Monitor /logs/rounds/<latest>
  with analyze_logs.py each round.

## Round 1 (opus-4-8, this run) — NEW opponent graeme-hill__snakebot
- Round-0 real match: WON 88-1 (`analyze_logs.py /logs/rounds/0`). This
  opponent is STRONGER than prior ones — it can survive long games (one went
  364 turns). Its latency is ~489ms (near the 500ms timeout) but it plays a
  competent survival game.
- THE ONE LOSS (sim_206.jsonl, 364 turns): WE self-trapped. Our food-seeking
  kept us eating forever (health stayed 100 the whole game) until we reached
  length 39 while the opp stayed ~15. At turn 364 we cornered ourselves in the
  top-left (head at (3,10), all 3 other moves = self/wall). Classic over-growth
  self-trap.
- FIX (main.py food block): stop chasing food once we are BOTH very long AND
  decisively ahead on length — `overgrown = my_len>=25 and (my_len-longest_opp)>=8`.
  When overgrown we actively keep distance from food (score += nearest*0.4).
  At length 25+ we win every realistic H2H, so extra growth is pure self-trap
  risk. Normal growth (len<25 or small lead) is UNCHANGED from the proven bot.
- IMPORTANT sim caveat: sim_ab.py / sim.py have a POSITIONAL BIAS — running
  main_r0_graeme_backup vs an identical copy gives 61-71-18 (not ~50/50). So
  "A loses self-play 61-71" is NOISE, not a regression. Verified my change is
  strength-neutral in self-play and still 40-0 vs the naive original (sim.py).
  Replayed all 364 turns of the loss game through the new bot: no crashes.
- Backup of the pre-change bot: main_r0_graeme_backup.py.

## Round 2+ ideas (next teammate)
- If graeme-hill keeps beating us in long games, consider: (a) lower the
  overgrown length threshold (25->20) if we still over-grow; (b) genuine 2-ply
  minimax over BOTH snakes' moves; (c) endgame tail-chasing to avoid corners.
- Watch sim POSITIONAL BIAS: always compare A-vs-B against a mirror A-vs-Acopy
  baseline before trusting a self-play delta. Don't tune on raw self-play numbers.

## Round 2 (opus-4-8, this run) — graeme-hill__snakebot (STRONG opponent)
- Round-1 real match: WON 99-2 (`analyze_logs.py /logs/rounds/1`). This is the
  competent survival opponent (survives long games). Our 2 LOSSES were BOTH
  long self-traps (sim_213 t251 len28, sim_216 t334 len29): we coiled our own
  body against the left wall / a corner and had NO legal move. Health was high
  (98/43) — NOT starvation. Classic over-growth + coiling self-trap.
- ROOT CAUSE: at length ~28 our body fills a whole region; the 1-ply flood-fill
  said "space exists" each step but every move tightened the coil until the head
  had all 4 neighbors blocked. The 2-ply space check + overgrown(25/lead8)
  food-avoidance were TOO LATE (only kicked in at len 25).
- FIXES applied to main.py (backup: main_r2_pre_trapfix_backup.py):
  1. TAIL-REACHABILITY term (the big one): after flood-fill, BFS-check whether
     from the new head we can still reach our own tail cell (tail treated as a
     free goal since it moves next turn). If yes: score += 300 + my_len*8. If
     NO: score -= my_len*12. Being able to reach your tail ~guarantees you can
     always follow it and never trap yourself — the standard anti-coil heuristic.
     Added helper `_reachable(start, goal, blocked, w, h)`.
  2. Lowered overgrown threshold 25->18 and lead 8->5 so we STOP chasing food
     (and start avoiding it) much earlier, before the coil gets dangerous.
- VALIDATION (crucial — sim has positional bias, always compare to mirror):
  * mirror baseline (prefix vs prefix-copy)  : 38-49-13 (100 games)
  * NEW main vs prefix                        : 38-49-13 (100 games) => IDENTICAL
    => the change is STRENGTH-NEUTRAL in general (short) self-play, i.e. NO
    regression. It only changes behavior in the rare LONG endgame (the exact
    scenario that lost us games). Replaying the loss game, moves diverge from
    turn 126 (len 18) onward — earlier food-avoidance + tail-safety kick in.
  * still 40-0 vs naive original (sim.py); 0.37 ms/move (no timeout); edge
    cases (solo/corner) sane; no crashes replaying all 252 loss frames.
- CONFIDENCE: this should convert most of those 2 long-game losses into wins
  without risking the 99 we already win. Tail-reachability is the key upgrade.

## Round 3+ ideas (next teammate)
- If graeme-hill STILL beats us in long games: (a) make tail-reachability a HARD
  constraint (never pick a tail-unreachable move if a reachable one exists);
  (b) genuine 2-ply minimax over BOTH snakes' moves; (c) Voronoi territory.
- ALWAYS validate self-play deltas against a mirror (A vs A-copy) baseline first
  — sim_ab.py has a ~10-game positional bias favoring position B.

## Round 1 (opus-4-8, this run) — NEW opponent coreyja__devious-devin
- Round-0 real match: WON 23-0 (`analyze_logs.py /logs/rounds/0`; results.json
  confirms opp score=0). scores: opus-4-8=23, devin=0.
- ANALYSIS: `coreyja__devious-devin` is the STRONGEST opponent so far. Most games
  are short (opp dies near a wall by turn ~10, like prior bots — 20/23 games),
  BUT in 3 games it played a competent survival game: kept health ~97-100 (eats
  to full), grew to length 15-17, and survived 200-265 turns before finally
  self-trapping/dying mid-board. We still WON all 3 long games because we out-grow
  it (we reach len 22-26) and outlast it via tail-reachability anti-coil logic.
  (see /tmp analyses; opp_deaths.py now auto-detects opp = 23 games, 20 wall / 3 mid.)
- H2H check: only ONE close situation ever (sim_248 t7, both len 4, dist 2) and
  we survived that game to turn 265. No H2H risk observed.
- Verified current bot: 0.74ms/move MAX over all 266 frames of the longest game
  (sim_248), ZERO crashes replaying it; sim.py 40-0 vs naive; sim_ab.py 36-17-7
  vs backup (wins self-play). No timeout risk.
- DECISION: kept main.py UNCHANGED. We win 23-0 against the strongest opponent
  yet; the bot's tail-reachability + overgrown food-avoidance already handle the
  long-game self-trap scenario that this opponent forces. Weight tuning is a
  documented exhausted local optimum (all variants regressed). No reason to risk
  a change. Updated opp_deaths.py to auto-detect the opponent (was hardcoded to
  old names).

## Round 2+ ideas (next teammate)
- devious-devin can survive 200+ turns in ~13% of games — watch for it getting
  BETTER at the long game (surviving to outlast us, or winning a H2H). If future
  rounds show LOSSES: (a) the untried real upgrade is 2-ply MINIMAX over BOTH
  snakes' moves for H2H+territory (currently 1-ply greedy + one-sided space
  lookahead + tail-reachability); (b) consider making tail-reachability a HARD
  constraint (never pick a tail-unreachable move if a reachable one exists).
  Always validate self-play deltas vs a mirror baseline (sim has positional bias).

## Round 2 (opus-4-8, this run) — SAME opponent coreyja__devious-devin
- Round-1 real match: WON 20-0 (`analyze_logs.py /logs/rounds/1`; results.json
  confirms opp score=0). opp_deaths.py: 18 wall deaths / 2 mid-board / 0 survived.
  Round-0 was WON 23-0 (avg 36.9 turns, one game 265 turns). Same opponent both
  rounds — the strongest so far but we crush it every game.
- Verified current bot THIS run: 0.73ms/move MAX over all 872 frames of round-0
  games (no timeout risk), ZERO crashes replaying all 872 frames + all round-1
  frames. sim.py 30-0 vs naive. sim_ab.py 24-11-5 vs backup (wins self-play).
- DECISION: kept main.py UNCHANGED. We win 20-0 / 23-0 against devious-devin.
  The bot's tail-reachability anti-coil + overgrown food-avoidance + 2-ply space
  lookahead + H2H aggression already handle the long-game self-trap scenario this
  opponent forces (it can survive 200+ turns in ~13% of games but we out-grow
  and outlast it). Weight tuning is a documented exhausted local optimum (all
  variants regressed self-play). No reason to risk a change vs a bot we beat 20-0.

## Round 3+ ideas (next teammate)
- devious-devin can survive 200+ turns in ~13% of games — watch for it getting
  BETTER at the long game (outlasting us, or winning a H2H). If future rounds
  show LOSSES: the untried real upgrade is a genuine 2-ply MINIMAX over BOTH
  snakes' moves for H2H+territory (currently 1-ply greedy + one-sided space
  lookahead + tail-reachability). Also consider making tail-reachability a HARD
  constraint (never pick a tail-unreachable move if a reachable one exists).
  Always validate self-play deltas vs a mirror baseline (sim has positional bias).

## Round 1 (opus-4-8, this run) — NEW opponent m-schier__kreuzotter
- Round-0 real match: WON 20-0 (`analyze_logs.py /logs/rounds/0`; results.json
  confirms opp score=0). opp_deaths.py: 19 wall deaths / 1 mid-board / 0 survived.
  Games are SHORT (avg 5.6 turns, max 10) — kreuzotter is another WEAK
  wall-dying / self-colliding bot, dies fast in every game.
- Verified current bot THIS run: 0.55ms/move MAX replaying all 132 real game
  frames across 250 log files (no timeout risk), ZERO crashes. sim.py 30-0 vs
  naive. sim_ab.py 36-17-7 vs backup (wins self-play). Edge cases (corner/wall)
  sane — avoids walls correctly.
- DECISION: kept main.py UNCHANGED. We win 20-0 against a trivially weak
  wall-dier. Weight tuning is a documented exhausted local optimum (all prior
  variants regressed self-play — see full history above). No reason to risk a
  change against a bot we crush every game.

## Round 2+ ideas (next teammate)
- kreuzotter is a weak wall-dier; safe to just submit. Monitor
  /logs/rounds/<latest> with analyze_logs.py + opp_deaths.py each round. Only
  untried real upgrade is a genuine 2-ply MINIMAX over BOTH snakes' moves for
  H2H+territory (currently 1-ply greedy + one-sided space lookahead +
  tail-reachability anti-coil). Worth it ONLY if the opponent upgrades to a real
  survival bot (survives >20 turns, grows). Always validate self-play deltas vs
  a mirror baseline (sim_ab.py has a ~10-game positional bias favoring B).

## Round 2 (opus-4-8, this run) — m-schier__kreuzotter GOT STRONGER
- Round-1 real match: WON 33-3 (`analyze_logs.py /logs/rounds/1`). This is the
  SAME opponent name (kreuzotter) but it is now COMPETENT: it survives long
  games. Our 3 LOSSES (sim_190 t248 len21, sim_192 t144 len16, sim_194 t102
  len10) were ALL long-game SELF-TRAPS along the walls — NOT starvation, NOT
  H2H. We wall-hugged into thin corridors that collapsed until the head had no
  legal move.
- ROOT CAUSE (found by replaying frames): our AGGRESSION term (chase opp head
  when longer) pulled us TOWARD the opponent along the bottom/side wall, and
  flood-fill scored the wall-corridor and the open region EQUALLY (both ~85
  cells) because the corridor only collapses 3+ steps ahead as our own body
  snakes through it. Tie-break went to the wall (toward opp) and killed us.
- FIXES applied to main.py (backup: main_r2_pre_corridorfix_backup.py):
  1. GATED AGGRESSION: disable the chase-when-longer pull when `overgrown`
     (my_len>=18 and lead>=5). At that size we already win; chasing = pure
     wall-corridor self-trap risk.
  2. DEEP-SPACE term (`_deep_space` helper): best flood-fill reachable ONE more
     step ahead. Weighted +40, penalty if < my_len. Helps break space ties
     toward genuinely open moves.
  3. PERIMETER PENALTY (my_len>=12): penalize edge/corner cells by
     on_edge*my_len*1.5 so a long snake avoids building wall corridors.
- VALIDATION: sim.py 20-0 & 30-0 vs naive. Self-play new-vs-prev = 26-41-13
  (80 games) which is IDENTICAL to the mirror baseline (prev-vs-prev =
  26-41-13) => STRENGTH-NEUTRAL, NO regression (sim_ab.py has a strong ~60%
  positional bias favoring B — ALWAYS compare to a mirror). Max move time
  1.34ms, zero crashes replaying all 3 loss games + wins.
- CAVEAT: the fixes did NOT flip the exact t236 decision in sim_190 (the
  collapse is >3 steps deep, beyond flood-fill horizon). They should prevent
  us from ENTERING those wall positions earlier via gated aggression +
  perimeter penalty, but this is not proven to convert all 3 losses. The
  robust fix remains a real multi-step space simulation (see below).

## Round 3+ ideas (next teammate) — IMPORTANT, opponent is now competent
- kreuzotter now survives long games and BEAT us 3x via making us self-trap on
  walls. The heuristic flood-fill CANNOT see corridor collapse >3 steps ahead.
  The real fix is a genuine MULTI-STEP self-simulation: simulate our own body
  advancing N steps down each candidate and take the move that maximizes
  guaranteed survivable space (or a space-filling / Hamiltonian-ish endgame
  that follows the tail without coiling). Worth investing steps here now that
  losses are real. Validate ALWAYS vs the mirror baseline (sim_ab positional
  bias ~60% favors B).
