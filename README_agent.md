# Agent Notes (opus-4-8 BattleSnake)

## !!! CRITICAL LESSON (READ THIS FIRST) !!!
main.py MUST end with the launch block or the grader marks the bot INVALID
(scores 0). Local sims DON'T catch this. ALWAYS verify main.py ends with:
    if __name__ == "__main__":
        from server import run_server
        run_server({"info": info, "start": start, "move": move, "end": end})

## RESULTS SO FAR
- Round 0 (in /logs/rounds/0): WIN 20-0 vs `Nettogrof__nessegrev-julia`.
  Analyzed sims: 20 wins / 0 loss / 0 tie. All valid.
- Our bot survives; opponent self-destructs.

## CURRENT OPPONENT: `Nettogrof__nessegrev-julia`
Observed behavior (from /logs/rounds/0/sim_*.jsonl): NAIVE. Its snake runs
straight along an edge (e.g. top row y=9) moving right until it hits the wall
at x=10 (board width 11) and dies. No collision avoidance. Games end in ~3-13
turns because the opponent kills itself. We simply need to survive.
NOTE: earlier README mentioned pambrose SimpleSnake -- that was a DIFFERENT
opponent from a prior scenario. test/opponent.py is still the pambrose port
(also naive, also self-destructs) so match.sh remains a valid smoke test.

## VALIDATION CHECKLIST before submitting (do EVERY round)
1. `tail -4 main.py` shows the `if __name__ == "__main__"` block.
2. `python3 -c "import main"` succeeds.
3. `python3 -c "import ast; ast.parse(open('main.py').read())"` parses.
4. `bash test/match.sh 20` -> me=20 opp=0 (smoke test vs naive opp).
5. `python3 test/solo_test.py` (recreate below) -> SURVIVED 300 turns.

## Strategy in main.py (survival-first) -- WORKING, DON'T REGRESS
- Full collision avoidance (walls, bodies, self); tails free unless just ate.
- Head-to-head: avoid cells enemy head could enter unless strictly longer.
- Flood-fill space eval to avoid self-trapping (penalize space < my_len).
- Food: chase nearest when hungry (<60) or not clearly longer.
- Hunt enemy head when clearly longer (force winning h2h), keeping space first.
- try/except returns "up" fallback.
- Verified: survives 300-turn solo game without self-trapping, manages health.

## Test harness (test/)
- test/opponent.py = naive pambrose port (smoke test opponent).
- test/match.sh N = N local games (me :8000 vs opp :8001). Prints RESULTS line.
- main_original_backup.py = original naive main.py reference (has launch block).

## Solo survival test (recreate in /tmp, ephemeral)
Simulates our bot alone for 300 turns to prove it doesn't self-trap.
See git history / this README for the script if /tmp is wiped. It builds a
solo game_state, calls main.move, applies the move, checks wall/self collision
and health, expects "SURVIVED all 300 turns".

## Log analysis one-liner (win/loss over sim logs)
python3 -c "import json,glob
w=l=t=0
for f in glob.glob('/logs/rounds/0/sim_*.jsonl'):
    ls=open(f).readlines()
    if not ls: continue
    d=json.loads(ls[-1])
    if d.get('isDraw'): t+=1
    elif 'opus' in str(d.get('winnerName','')): w+=1
    else: l+=1
print('win',w,'loss',l,'tie',t)"

## Advice for future teammates
- Bot is winning comfortably vs a naive opponent. LOW RISK. Tip: don't touch
  the launch block, don't regress survival logic.
- If the opponent ever becomes smarter, current flood-fill + h2h + hunt is a
  solid base. Could add 2-ply lookahead, but keep survival logic intact and
  always re-run match.sh + solo test before submitting.


## ROUND 2 UPDATE (opus-4-8)
- Round 1 result: WIN, score 39-0 (39 completed games, all won; ~211 sim files
  were empty in the log dir -- harness artifacts, not losses). Opponent still
  self-destructs by turn ~9-13. Opponent runs with latency 500 (times out).
- Ruleset is ROYALE (foodSpawnChance 15, minimumFood 1, hazardDamagePerTurn 14,
  shrinkEveryNTurns 25). Hazards start appearing ~turn 25 but our games END by
  turn ~13, so hazards have never actually mattered yet. Added avoidance anyway
  for robustness in case a game runs long.
- CHANGE: main.py now reads board["hazards"] and applies a -60 score penalty to
  moving into a hazard cell (food tie-break can still override when starving).
  Verified: healthy snake avoids hazards; starving snake still chases safe food.
- CHANGE: test/match.sh now runs `-g royale` to match the real ruleset. Still
  20-0 / 15-0 vs the naive opponent. Solo test still SURVIVES 300 turns.
- Backups: main_pre_hazard_backup.py (before this change), main_original_backup.py.
- LOW RISK. Bot dominates. Don't touch the launch block.

## ROUND 3 UPDATE (opus-4-8)
- Opponent this round: `Nettogrof__nessegrev-java` (a JAVA variant, still NAIVE).
  From /logs/rounds/0/sim_1.jsonl: it runs straight UP the left edge (x=1) from
  spawn (1,1) until it hits the top wall at y=10 (height 11) and dies turn ~10.
  No collision avoidance -> self-destructs. We just survive.
- Result recorded in /logs/rounds/0/results.json: WIN 20-0 (opus-4-8).
- Ran full validation checklist -- ALL PASS:
  * tail main.py -> launch block present.
  * import + ast.parse OK.
  * bash test/match.sh 20 -> me=20 opp=0 tie=0 (royale, hazards on).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 9.
  * Extra edge tests: corner escape OK, hungry->food OK, avoids 2-cell
    self-trap pocket (chose open space via flood-fill). All correct.
- NO CODE CHANGE this round -- bot dominates, logic is solid, low risk.
  Did not touch launch block or survival logic (per prior guidance).

## ROUND 2 UPDATE #2 (opus-4-8, this session)
- Confirmed standing: Round 0 WIN 20-0, Round 1 WIN 37-0 (37 completed games,
  213 empty sim files = harness artifacts, 0 losses). Opponent
  `Nettogrof__nessegrev-java` still NAIVE, self-destructs by turn 5-13
  (avg ~8.6 turns). Ruleset name shows "standard" in round-1 sims but with
  royale hazard settings present (foodSpawnChance 15, hazardDamage 14,
  shrink 25) -- games end long before hazards matter.
- Ran FULL validation -- ALL PASS:
  * tail main.py -> launch block present.
  * import main + ast.parse OK.
  * bash test/match.sh 15 -> me=15 opp=0 tie=0.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 9.
  * Extra edge tests (inline): solo snake near wall -> valid move;
    equal-length h2h -> correctly avoids enemy-adjacent danger (goes left).
- NO CODE CHANGE. Bot dominates, logic is comprehensive & correct. Low risk.
  Did not touch launch block or survival logic (per prior guidance).

## ROUND 1 UPDATE (opus-4-8, csauve__bookworm opponent)
- CURRENT OPPONENT: `csauve__bookworm` (bookworm is a real strong snake, but in
  /logs/rounds/0 sims it TIMES OUT (latency 500) and self-destructs: runs straight
  into walls, dies by turn ~8-14). Result recorded: WIN 20-0.
- IMPORTANT RISK: if the grader's bookworm does NOT time out, it's genuinely strong.
  I mirror-tested main.py vs a copy of itself (see /tmp/smartrun.sh recreated below):
  new-me vs baseline = 21-19 (marginal edge). vs naive opp still 15-0.
- CHANGE this round (LOW RISK, defensive): in score_candidate, bumped space reward
  5.0->6.0, low-space penalty 40->60, and added a -300 penalty for entering a
  "tight pocket" (space < my_len//2 + 1). This prevents a smart opponent from
  trapping us in a near-fatal small region. Validated: solo SURVIVES 300 turns,
  15-0 vs naive, 21-19 vs old baseline (mirror).
- Backup of pre-round-1 code: main_round1_backup.py.
- Mirror-test harness: /tmp/smartrun.sh (ephemeral). Recreate: it launches main.py
  on :8000 and /tmp/smart_opp.py (copy of an old main.py) on :8001, plays N royale
  games, prints "SMART RESULTS: me=.. opp=.. tie=..".
- TODO for teammates: contested-food racing (only chase food we reach first) was
  TRIED and made it WORSE (13-16), so reverted. Better lever = space domination /
  cutting off the enemy when longer. Consider 2-ply h2h lookahead. Keep launch block!

## ROUND 2 UPDATE #3 (opus-4-8, THIS SESSION -- REAL FIGHT NOW)
- IMPORTANT: opponent `csauve__bookworm` is NO LONGER self-destructing this
  round. Round 1 result: WIN 25-1 but games now avg ~45 turns (real combat!).
  The ONE loss (/logs/rounds/1/sim_249.jsonl, 311 turns) was a SELF-TRAP: we
  crawled up the left wall coiling our own body until our head at (0,3) had
  zero valid moves. We were LONGER (22 vs 20) but boxed ourselves in.
- ROOT CAUSE: old flood-fill counted static space; inside a coil the tail
  retreats so raw space looked "ok" while the head was actually sealing itself
  into a shrinking pocket (space was already 7 << my_len 21 by turn 300).
- FIX #1: TIME-AWARE flood_fill. BFS now tracks distance d; a body cell is only
  an obstacle while occupied (clear_time = length - seg_index). Distinguishes a
  survivable coil (follow retreating tail) from a true trap.
- FIX #2 (the big one): TAIL-REACHABILITY heuristic in score_candidate. +200 if
  from the new head we can still reach our own tail (time-aware BFS via
  _can_reach), -200 if not. Classic anti-self-trap: if you can always chase your
  tail you can never seal yourself in. This makes the bot break OUT of wall-hug
  coils (verified: at the losing-game turn 298 it now goes RIGHT into open board
  instead of continuing down the wall to death).
- VALIDATION (all pass):
  * ast.parse + import main OK; launch block intact.
  * bash test/match.sh 15 -> me=15 opp=0 (naive smoke test).
  * python3 test/solo_test.py -> SURVIVED 300 turns.
  * MIRROR vs pre-change baseline (/tmp/mirror.sh, baseline=main_round2_v2_backup.py):
    batch1 11-9, batch2 14-6 => 25-15 over 40 games. Clear improvement, no regress.
- Backups: main_round2_v2_backup.py (pre-this-change), main_round1_backup.py, etc.
- ADVICE FOR NEXT TEAMMATE: bookworm is a genuinely strong snake now. Our edge is
  survival/anti-trap. Next lever: 2-ply lookahead on the enemy head, or better
  center-control. Keep tail-reachability + time-aware flood. NEVER touch the
  launch block. Re-run match.sh + solo_test + mirror before submitting.

## ROUND 1 UPDATE (opus-4-8, coreyja__improbable-irene opponent) -- THIS SESSION
- CURRENT OPPONENT: `coreyja__improbable-irene`. Result recorded in
  /logs/rounds/0/results.json: WIN 20-0 (opus-4-8).
- Behavior (from /logs/rounds/0/sim_*.jsonl, 20 non-empty of 250; rest are
  empty harness artifacts): opponent TIMES OUT every game -- latency ~500-501
  from turn 1 (timeout is 500). When it times out the CLI repeats its last move,
  so irene just walks STRAIGHT UP from spawn (5,1) -> (5,10) and dies on the top
  wall at turn ~10. Effectively naive/self-destructing, same pattern as the old
  bookworm-timeout scenario. We simply survive.
- RISK NOTE: coreyja snakes are genuinely strong IF they don't time out. Latency
  501 is 100% consistent across all sims, so timeout is reliable here. But if the
  grader ever lets it run, our survival/anti-trap logic is our edge.
- NO CODE CHANGE this round. Bot logic is comprehensive (time-aware flood-fill,
  tail-reachability anti-coil, h2h, hazard avoidance, food strategy) and winning.
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact (tail shows it).
  * bash test/match.sh 15 -> me=15 opp=0 (royale, hazards on).
  * standard-ruleset smoke test (inline) -> me=10 opp=0.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 9.
  * MIRROR vs main_round2_v2_backup.py (/tmp/mirror.sh) -> me=12 opp=8 (no regress).
- ADVICE: LOW RISK, bot dominates. Don't touch launch block or survival logic.
  If irene ever stops timing out, consider 2-ply h2h lookahead but keep
  tail-reachability + time-aware flood intact; always re-run all validations.

## ROUND 2 UPDATE (opus-4-8, coreyja__improbable-irene, THIS SESSION)
- Standing: Round 0 WIN 20-0, Round 1 WIN 20-0 vs `coreyja__improbable-irene`.
- Opponent behavior (verified /logs/rounds/1/sim_*.jsonl, 20 non-empty):
  latency 500-501 from turn 1 = TIMES OUT every game -> CLI repeats its last
  move, so irene walks STRAIGHT from spawn into a wall and dies turn ~9-10.
  Effectively naive/self-destructing. We simply survive. 20/20 wins.
- RISK: coreyja is a genuinely strong snake IF it ever runs. Latency 501 is
  100% consistent, so timeout is reliable here. Our survival/anti-trap logic
  (time-aware flood-fill + tail-reachability) is our edge if it ever runs.
- NO CODE CHANGE this round. Bot dominates; changing risks regression.
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact (tail shows it).
  * bash test/match.sh 15 -> me=15 opp=0 tie=0 (royale, hazards on).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 9.
  * Mirror vs main_round2_v2_backup.py & main_round1_backup.py -> all ties
    (deterministic symmetric coil draws; expected, no regression).
- ADVICE: LOW RISK, don't touch launch block or survival logic. If irene ever
  stops timing out, consider 2-ply h2h lookahead but keep tail-reachability +
  time-aware flood intact; always re-run all validations.

## ROUND 1 UPDATE (opus-4-8, graeme-hill__snakebot opponent) -- THIS SESSION
- CURRENT OPPONENT: `graeme-hill__snakebot`. Round 0 result recorded in
  /logs/rounds/0/results.json: WIN 95-0 (opus-4-8 score 95, graeme 0).
- IMPORTANT DIFFERENCE from prior opponents: graeme's bot ACTUALLY RUNS.
  Real latencies 100-129ms (NOT the 500ms timeout pattern of bookworm/irene).
  So it is genuinely making decisions -- but it still self-destructs against our
  survival-first strategy. It crawls along walls/edges and boxes itself in.
- Analysis of /logs/rounds/0 (95 non-empty of 250; rest empty harness artifacts):
  * 95 wins / 0 loss / 0 tie.
  * Game length avg 13.3 turns; most short (opp self-destructs by ~turn 7-16).
  * 3 real combat games: sim_153 (219 turns), sim_159 (115), sim_212 (94) --
    WE WON ALL. In sim_153 we grew to len 21 vs opp 19 and the opponent died.
    Confirms our bot out-survives/out-maneuvers a real running opponent.
- NO CODE CHANGE this round. Bot dominates (95-0) and even wins long combat
  games. Logic is mature (time-aware flood-fill, tail-reachability anti-trap,
  h2h avoid/hunt, hazard avoidance, food/center strategy). Changing risks regress.
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact (tail shows it).
  * bash test/match.sh 15 -> me=15 opp=0 tie=0 (royale, hazards on).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 9.
- ADVICE FOR NEXT TEAMMATE: graeme-hill RUNS (not a timeout bot), so if it ever
  improves it's a real threat -- but our survival/anti-trap edge beats it 95-0.
  If you want to push further, consider 2-ply h2h lookahead on the enemy head,
  but KEEP tail-reachability + time-aware flood intact and re-run all validations.
  NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, graeme-hill__snakebot, THIS SESSION)
- Standing: Round 0 WIN 95-0, Round 1 WIN 100-2 vs graeme-hill__snakebot.
  graeme RUNS (real ~100ms latency) -> genuine combat, avg ~17 turns.
- Analyzed the TWO round-1 LOSSES (both real combat, we self-trapped on walls):
  * sim_152 (96 turns): chased food (9,0) along the BOTTOM ROW; opp closed in
    from the right and we ran out of room on the wall -> boxed in corner.
  * sim_235 (138 turns): we were LONGER (13 vs 8) but COILED into the top-right
    and by turn ~133 our head at (7,2) had only ONE open cell -> sealed in.
    Root cause = gradual wall-hugging coil (trap set up over many earlier turns).
- CHANGES to main.py (defensive, low-risk):
  1. ESCAPE-COUNT in score_candidate: count safe neighbours of the new head
     (in-bounds, not body, not a cell an equal/longer enemy could take). 0
     escapes = -400 (dead-end), 1 escape = -40 (risky corridor). Directly
     targets the "one open cell" death.
  2. Mild EDGE penalty (-3, corner extra -5) ONLY when health>=40, to nudge
     toward the interior and off walls without blocking edge/corner FOOD when
     hungry (a stronger -8/-20 version STARVED the solo test -> reverted to -3/-5).
  3. Food tie-break restructured (still distance-first, space second) -- effectively
     the escape/edge penalties already filter dangerous cells before food sort.
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact (tail shows it).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 10 -> me=10 opp=0 (naive smoke test, royale).
  * MIRROR vs pre-change (main_round2_r2_backup.py, /tmp/mirror.sh) -> 10-10
    (deterministic, symmetric; no regression).
- HONEST NOTE: the two specific losses are LONG coils; escape-count catches
  dead-ends but not the multi-turn coil buildup at turns 117/133 (both versions
  still coil identically there). A real fix would need lookahead that avoids
  entering regions that will become sealed as our body grows -- a good TODO:
  before committing to a move, run flood_fill assuming our body GROWS (don't
  free the tail) to detect shrinking pockets earlier. Didn't have steps to do
  this safely this round. KEEP escape-count + tail-reachability + time-aware flood.
- Backup: main_round2_r2_backup.py (pre-this-change). NEVER touch launch block.

## ROUND 1 UPDATE (opus-4-8, coreyja__devious-devin opponent) -- THIS SESSION
- CURRENT OPPONENT: `coreyja__devious-devin`. Round 0 result in
  /logs/rounds/0/results.json: WIN 33-0 (opus-4-8 score 33, devin 0).
- Behavior (verified /logs/rounds/0/sim_*.jsonl, 33 non-empty of 251; rest are
  empty harness artifacts): devin TIMES OUT every game -- latency 500-501 from
  turn 1 (timeout is 500). CLI repeats its last move, so devin walks STRAIGHT UP
  the LEFT edge (x=1) from spawn (1,1) -> (1,10) and dies on the top wall at
  turn ~9-13. Effectively naive/self-destructing (same coreyja timeout pattern
  as irene). We simply survive. 33/33 wins, avg game len 9.2 turns.
- RISK: coreyja snakes are genuinely strong IF they run. Latency 500-501 is 100%
  consistent here so timeout is reliable. Our survival/anti-trap logic is the edge.
- NO CODE CHANGE this round. Bot dominates 33-0; changing risks regression.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * python3 -c "import main" + ast.parse OK.
  * bash test/match.sh 10 -> me=10 opp=0 tie=0 (royale, hazards on).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * Inline edge tests: corner (0,0) -> valid 'up'; hungry(h=20) near edge food
    at (0,5) -> correctly goes 'left'. Both correct.
- NOTE on mirror tests: current main.py vs old backups gives noisy split results
  (8-2 vs round2_v2, 4-6 vs round2_r2, 4-5 vs round1). These are DETERMINISTIC
  symmetric mirror games -- tiny scoring diffs (the round-2 edge/escape penalties)
  swing them; NOT representative of the real self-destructing opponent. Did not
  chase mirror wins as it would risk breaking proven survival logic.
- ADVICE: LOW RISK, bot dominates. Don't touch launch block or survival logic.
  If devin ever stops timing out, consider 2-ply h2h lookahead but keep
  tail-reachability + time-aware flood + escape-count intact; re-run all validations.

## ROUND 2 UPDATE (opus-4-8, coreyja__devious-devin) -- THIS SESSION
- Standing: Round 0 WIN 33-0, Round 1 WIN 20-0 vs `coreyja__devious-devin`.
- Opponent behavior (verified /logs/rounds/{0,1}/sim_*.jsonl): latency 500 from
  turn 1 = TIMES OUT every game. CLI repeats its last move so devin walks
  STRAIGHT UP the left edge from spawn and dies on the top wall by turn ~9-10.
  Effectively naive/self-destructing (standard coreyja timeout pattern).
  Round 0: 33 nonempty sims, 33-0-0, avglen 9.2. Round 1: 20 nonempty, 20-0-0,
  avglen 10.2. We simply survive.
- RISK: coreyja is genuinely strong IF it runs, but latency 500 is 100%
  consistent so timeout is reliable. Our survival/anti-trap logic is the edge.
- NO CODE CHANGE this round. Bot dominates; changing risks regression.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * python3 -c "import main" + ast.parse OK.
  * bash test/match.sh 10 -> me=10 opp=0 tie=0 (royale, hazards on).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * Inline edge tests: corner (0,0) -> valid 'up'; hungry(h=15) near edge food
    at (0,5) -> correctly goes 'left'. Both correct.
- ADVICE: LOW RISK, don't touch launch block or survival logic. If devin ever
  stops timing out, the known weakness is multi-turn wall-hug coils (see round-2
  graeme notes); a real fix needs lookahead assuming our body GROWS to detect
  shrinking pockets earlier. Keep escape-count + tail-reachability + time-aware
  flood intact; re-run all validations before submitting.

## ROUND 1 UPDATE (opus-4-8, m-schier__kreuzotter opponent) -- THIS SESSION
- CURRENT OPPONENT: `m-schier__kreuzotter`. Round 0 result in
  /logs/rounds/0/results.json: WIN 20-0 (opus-4-8 score 20, kreuzotter 0).
- Behavior (verified /logs/rounds/0/sim_*.jsonl, 20 nonempty of 250; rest empty
  harness artifacts): kreuzotter TIMES OUT every game -- latency 500-501 from
  turn 1 (timeout is 500). CLI repeats its last move, so it walks STRAIGHT into
  a wall from spawn and dies by turn ~5-13 (avg game len 8.25). Same reliable
  timeout/self-destruct pattern as prior coreyja/bookworm/irene/devin opponents.
  We simply survive. 20/20 wins.
  NOTE: sim log format this round = per-line JSON with {game,turn,board,you}
  wrapper (board.snakes[].body/latency). Last line = {winnerName,isDraw}.
- RISK: kreuzotter (m-schier) may be a genuinely capable snake IF it ever runs,
  but latency 500 is 100% consistent so timeout is reliable here. Our survival/
  anti-trap logic is the edge if it ever runs.
- NO CODE CHANGE this round. Bot dominates 20-0; changing risks regression.
- Our move() is ~0.0013 ms/call -> zero timeout risk on our side.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * ast.parse + import main OK.
  * bash test/match.sh 12 -> me=12 opp=0 tie=0 (royale, hazards on).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * timing test: move() avg ~0.0013 ms (no timeout risk).
- ADVICE: LOW RISK, don't touch launch block or survival logic. If kreuzotter
  ever stops timing out, known weakness is multi-turn wall-hug coils; a real fix
  needs lookahead assuming our body GROWS to detect shrinking pockets earlier.
  Keep escape-count + tail-reachability + time-aware flood intact; re-run all
  validations before submitting.

## ROUND 2 UPDATE (opus-4-8, m-schier__kreuzotter -- REAL COMBAT NOW)
- IMPORTANT: kreuzotter is NO LONGER timing out. Round 1 result: WIN 24-2 but
  real combat (avg ~18 turns, up from ~8). It is a genuine PURSUIT + center-
  control snake: it tails our head one cell behind and pins us to walls/corners.
- Analyzed the TWO round-1 losses:
  * sim_244 (t64): opp chased directly behind us; we ran a path into the TOP-LEFT
    corner while SHORTER (len4 vs5) and got boxed in.
  * sim_247 (t196): long game, we were LONGER early but hugged the RIGHT wall
    (cols 9-10) letting opp control center; we got cornered on the BOTTOM row and
    forced into a losing head-to-head (our only move was into a cell the longer
    opp could also take).
- CHANGE (low-risk tuning of existing score_candidate):
  * space weight 6.0 -> 8.0
  * low-space penalty 60 -> 80 per missing cell
  * healthy-edge penalty 3 -> 6, corner extra 5 -> 10
  Rationale: push us off walls/corners and value open room more, to resist the
  pursuit/pin strategy. NOT a structural change -- proven survival logic intact.
- TESTING: added test/smart_opp.py (flood-fill + PURSUIT + center-control snake
  that mimics kreuzotter) and test/smartmatch.sh. Also /tmp/cmp.sh (ephemeral,
  recreate: runs a chosen main file vs smart_opp for N royale games).
  NOTE: the battlesnake CLI is HIGHLY non-deterministic (food spawn) -- single
  batches swing wildly (baseline ranged 21-18 to 31-9). Paired A/B over 2x40
  games: tuned=52/80 (65%), baseline=46/80 (58%). Consistent modest edge for
  the tuned version, no regression.
- I TRIED a Voronoi/contested-territory term (count cells we reach before opp)
  weighted into the score -- it made things WORSE (10-30 vs smart_opp) because it
  lured us toward contested cells near the opp. REVERTED. Don't re-add naively.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh 10-0 (naive), smart_opp paired edge.
- Backup: main_round2_pursuit_backup.py (pre-tuning).
- ADVICE: kreuzotter is a REAL threat now. Best next lever = 2-ply lookahead
  (simulate opp's best pursuit response, avoid moves that let it seal us next
  turn) OR smarter cornering (when SHORTER, keep to open center; when LONGER,
  cut off its access to open space). Test carefully -- variance is huge, use 2x40
  paired batches. NEVER touch the launch block.

## ROUND 1 UPDATE (opus-4-8, nbw__nbw-crystal opponent) -- THIS SESSION
- CURRENT OPPONENT: `nbw__nbw-crystal`. Round 0 result: WIN 214-24 (12 ties).
  This is a GENUINE COMBAT opponent (NOT a timeout/self-destruct bot). Avg game
  len 61 turns, up to 371. It grows steadily, controls center, and pins us.
- ANALYZED THE 24 LOSSES (/logs/rounds/0/sim_*.jsonl -- note: 'you' field is
  CRYSTAL's perspective; our snake is the OTHER one in board.snakes):
  * sim_157/110: we were SHORTER and got boxed against the LEFT WALL/corner.
  * sim_0 (253t) & sim_13: we were LONGER (17 vs 13!) yet COILED into the
    bottom-right / top-left corner up a wall and sealed ourselves in.
  ROOT CAUSE: chronic WALL-HUGGING -> multi-turn coil traps, even when winning.
- CHANGES to main.py (tuned, validated):
  1. space weight 8->10, low-space penalty 80->100 (value open room more).
  2. edge penalty 6->8, corner extra 10->16, and applied at health>=25 (was 40)
     so we stay off walls more consistently (food logic still reaches edge food).
  3. NEW growth-aware STATIC flood-fill (`static_flood`): treats ALL current
     body cells as permanent walls (no tail retreat). Penalty
     -(my_len - sspace)*6 when that region < our length. Detects pockets that
     SEAL us in as bodies grow -- the exact multi-turn coil death above. This is
     the fix the previous README kept flagging as a needed TODO.
- TESTING (test/smartmatch.sh vs test/smart_opp, a center-control+pursuit proxy
  for crystal): baseline was 10-10. After changes, aggregate across 3x24 batches
  = 45-27 (62.5%). AB vs old backup = 13-11. Naive smoke test 8-0. Solo SURVIVES
  300 turns. NOTE: CLI variance is HUGE (single batches swung 12-12 to 17-7);
  judge on multi-batch aggregate, not one run.
- I first tried heavier weights (static*12, edge 12/25) -> one batch went 7-17
  (over-avoidance). Dialed back to the gentler values above for consistency.
- Backup: main_round1_crystal_backup.py (pre-this-change).
- ADVICE FOR NEXT TEAMMATE: crystal is a REAL threat. Our edge is anti-coil +
  space. Next lever: 2-ply lookahead (simulate crystal's pursuit response), or
  when LONGER actively CUT OFF crystal's space (offensive flood-fill) instead of
  just avoiding our own traps. Keep static_flood + tail-reachability + time-aware
  flood + escape-count. Test with 3+ batches of smartmatch.sh (variance!). NEVER
  touch the launch block.

## ROUND 2 UPDATE (opus-4-8, nbw__nbw-crystal -- THIS SESSION, ANTI-PIN FIX)
- Standing: Round 0 WIN 214-24 (12 ties), Round 1 WIN 218-24 (8 ties) vs
  `nbw__nbw-crystal`. Real combat opponent, avg game len ~59 turns.
- ANALYZED the 24 round-1 losses: MOST were HEAD-TO-HEAD / PIN deaths at HIGH
  health (82-97%), NOT starvation or self-coil. Pattern (e.g. sim_0 t27, sim_151,
  sim_194, sim_103, sim_238): we were SHORTER, a longer opp pursued us, and we
  FLED toward a wall/corner, letting the longer snake cut us off and win a
  forced head-to-head. The fatal mistake happened EARLIER (turns 21-22 we dove
  into the corner) -- by the time both our only moves were losing h2h cells we
  were already doomed.
- FIX (score_candidate): new ANTI-PIN term. Compute `being_hunted` =
  (nearest opponent length >= my_len) AND (nearest opp within manhattan 4).
  When being_hunted: penalize distance-to-center (*4.0) and add a strong edge
  (-25) / corner (-40) penalty. This pulls us toward open center and off walls
  when a longer snake is chasing, so we keep escape routes and can't be pinned.
  Applied regardless of health, but food tie-break still lets a STARVING snake
  reach edge food (verified: health 15 + hunted -> still goes to edge food).
- TUNING (A/B vs test/smart_opp, /tmp/ab.sh, 40-game batches, HIGH variance):
  * center*4 (chosen): 29-11, 23-17, 27-13 => ~50-62% consistently.
  * OLD baseline (main_round2_crystal_r2_backup.py): 21-19, 22-17 => ~53%.
  * center*6 -> 16-23 (over-avoidance, lured into contested center). REJECTED.
  * center*2.5 -> 25-15 then 17-23 (inconsistent). REJECTED, center*4 better.
  Net: clear, consistent improvement over baseline, no regression.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh naive 10-0.
- Backup: main_round2_crystal_r2_backup.py (pre-anti-pin).
- A/B harness: /tmp/ab.sh (ephemeral) runs a given main file vs smart_opp for N
  royale games. Recreate from git history / this note if /tmp wiped.
- ADVICE: crystal wins by PURSUIT+PIN when we're shorter. Anti-pin helps a lot.
  Next lever: when SHORTER, actively grow (eat safe food) to flip length so we
  win h2h; or 2-ply lookahead to detect pin setups earlier. Keep anti-pin +
  static_flood + tail-reachability + time-aware flood + escape-count. Use
  MULTI-BATCH aggregates (variance is huge). NEVER touch the launch block.

## ROUND 1 UPDATE (opus-4-8, Xe__since opponent) -- THIS SESSION
- OPPONENT: `Xe__since`. Round 0 result: WIN 227-22 (1 tie). GENUINE COMBAT
  opponent (avg game len 123 turns). Grows steadily and pins us via H2H.
- ANALYZED THE 22 LOSSES (/logs/rounds/0/sim_*.jsonl): ROOT CAUSE = Xe
  OUT-GROWS us. In every loss we were 3-5 cells SHORTER (e.g. sim_128 turn 60:
  us len 9 vs Xe 13; sim_5: 6 vs 7 by turn 40). Being shorter -> Xe wins forced
  head-to-heads / pins us to walls. Our old bot only chased food when
  health<60, so we grew too slowly and stayed permanently behind on length.
- FIX (main.py): added an active FOOD-ATTRACTION term to score_candidate,
  weighted by growth-need (_food_weight): 4.0 when starving(<35hp), 3.0 when
  BEHIND on length, 2.0 when TIED, 0.6 when ahead. Applied only when the cell is
  safe (space >= my_len) so we never dive into a trap for food. Also +25 for
  landing on food. This keeps us at length parity so we win/avoid H2Hs.
- TUNING: first tried food_weight 8/6/3/1 -> TOO aggressive, lured us into
  contested cells, LOST vs greedy_opp (10-12). Dialed back to 4/3/2/0.6.
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact.
  * solo_test -> SURVIVED 300 turns, len 28 (was ~8; confirms real growth now).
  * match.sh naive -> 10-0.
  * A/B vs proven baseline (main_round0_xe_backup.py) via /tmp/ab.sh:
    batch1 20-8 (2 tie), batch2 22-8 => 42-16 (72%). CLEAR, consistent win.
- NEW TEST TOOLS: test/greedy_opp.py (food-greedy variant of smart_opp, mimics
  Xe's aggressive growth) + test/greedymatch.sh. NOTE: greedy_opp batches are
  HIGH variance (single 24-game batches swung 16-8 to 10-14); the reliable
  signal was the direct A/B vs baseline. /tmp/ab.sh = A vs baseline (ephemeral,
  recreate from git/this note): plays main.py vs main_round0_xe_backup.py.
- Backup: main_round0_xe_backup.py (proven 227-22 pre-growth code).
- ADVICE FOR NEXT TEAMMATE: growth parity is the key lever vs Xe. Keep the
  food-attraction term. If losing more, consider: when clearly LONGER, actively
  CUT OFF Xe's space (offensive flood-fill), or 2-ply H2H lookahead. Keep
  static_flood + tail-reachability + time-aware flood + escape-count + anti-pin.
  Judge changes by A/B vs baseline (variance!). NEVER touch the launch block.
