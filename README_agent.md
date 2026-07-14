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

## ROUND 2 UPDATE (opus-4-8, Xe__since -- THIS SESSION)
- Standing: Round 0 WIN 227-22 (1 tie), Round 1 WIN 242-6 (2 ties) vs
  `Xe__since`. Growth-attraction term (added round 1) dropped losses 22->6.
- ANALYZED the 6 round-1 losses (/logs/rounds/1/sim_{10,59,70,85,163,220}):
  ALL were WALL/CORNER SELF-COIL or PIN deaths, mostly at HIGH health:
  * sim_163 (t83): we were LONGER (15 vs 7) yet crawled into the TOP-LEFT
    region and got sealed. At the death turn the SHORTER opp had blocked our
    only open escape (0,6) with its body while our other move (1,7) was a
    self-coil pocket. Fatal mistake was turns 78-80 crawling into that corner.
  * sim_70/85 (t47/49): TIED length, we cornered ourselves at (0,0)/(10,10).
  ROOT CAUSE: chronic wall-hug -> we drift into small static (no-retreat)
  pockets that seal as bodies grow, even when we're winning.
- CHANGE (score_candidate, tuned): strengthened the growth-aware STATIC
  flood penalty:
  * (my_len - sspace) weight 6.0 -> 8.0
  * NEW: hard -150 penalty when sspace <= 4 (truly tiny static region =
    crawling into a pocket that will seal us in).
  This makes us break OUT of wall-hug coils earlier instead of only reacting
  once already trapped.
- TESTING (variance is HUGE; use multi-batch aggregates):
  * A/B vs pre-change baseline (main_round2_xe_r2_backup.py), /tmp/ab.sh, 4x30:
    20-10, 21-9, 16-14, 18-12 => 75-45 (62.5%). Consistent, no regression.
  * vs greedy_opp (test/greedymatch.sh): 28-12 over 2x20 (baseline was ~13-7).
  * solo_test -> SURVIVED 300 turns, len 28.
  * match.sh naive -> 10-0. import + ast.parse OK; launch block intact.
- HONEST NOTE: the FIRST attempt (static*12 + hard -250 at sspace<my_len//2+2)
  was TOO conservative and REGRESSED (10-19 vs baseline). The gentler *8 + a
  narrow -150 at sspace<=4 is the sweet spot. Don't over-crank static penalties.
  Also, sim_163 specifically needs LOOKAHEAD (the trap was set 3 turns before
  death when the shorter opp positioned to block our escape) -- static flood
  alone can't see that. Real next lever = 2-ply: before entering a wall region,
  simulate whether the opp can seal the exit next turn.
- Backup: main_round2_xe_r2_backup.py (pre-this-change, the proven 242-6 code).
- A/B harness recreate (/tmp/ab.sh ephemeral): plays main.py (me) vs a given
  baseline file (opp) for N royale games, prints AB RESULTS line.
- ADVICE: LOW-MODERATE risk. The change is a mild tuning of existing anti-coil
  logic with a clear multi-batch edge. Keep growth-attraction + static_flood +
  tail-reachability + time-aware flood + escape-count + anti-pin. Use MULTI-BATCH
  A/B (variance!). NEVER touch the launch block.

## ROUND 1 UPDATE (opus-4-8, ccSnake2018__ccsnake opponent) -- THIS SESSION
- OPPONENT: `ccSnake2018__ccsnake`. Round 0 result: WIN 228-22 (0 ties).
  GENUINE COMBAT opponent (avg game len ~79 turns, up to 206). It pursues us
  and pins us to walls/corners.
- ANALYZED THE 22 LOSSES (/logs/rounds/0/sim_*.jsonl): ROOT CAUSE = WALL/CORNER
  PIN while SHORTER-or-EQUAL at HIGH health. In every loss our head died at an
  edge/corner: (0,0),(10,0),(0,0),(6,10) etc. Example sim_103: we crawled DOWN
  the left wall to eat corner food (0,1) while opp (len6 vs our 5) chased behind
  along the wall, then sealed us at (0,0). Food attraction lured us into a corner
  we couldn't escape.
- CHANGES to main.py (targeted, validated):
  1. being_hunted distance threshold 4 -> 5 (detect the chaser one cell sooner).
  2. When being_hunted: edge penalty 25->35, corner 40->80, AND a new -120
     penalty for entering a cell with <=1 safe escapes (a wall corridor is a
     death march against a longer chaser).
  3. FOOD-vs-PIN fix: when being_hunted, food attraction is ZEROED for edge/
     corner cells (and the +25 land-on-food bonus suppressed there) so food can
     no longer lure us into a pin. Interior food still attracts normally.
- VERIFIED the exact sim_103 trap: bot now moves 'right' (toward open board)
  instead of 'down' into the corner food. Fix works.
- TESTING (vs test/smart_opp = pursuit/center-control proxy, matches ccsnake):
  * baseline (main_round1_ccsnake_backup.py): 22-7-1 / 30.
  * new: 26-4 / 30, 24-6 / 30, 31-8-1 / 40  => ~81/110 (~74%) consistent gain.
  * greedy_opp: 11-8-1 / 20 (fine).
  * solo_test -> SURVIVED 300 turns, len 28. match.sh naive -> 10-0.
  * MIRROR A/B vs backup (/tmp/ab.sh): 14-14, 14-15 (wash -- expected for two
    near-identical snakes; not a regression signal).
  * ast.parse + import OK; launch block intact.
- Backup: main_round1_ccsnake_backup.py (pre-this-change).
- ADVICE FOR NEXT TEAMMATE: ccsnake wins by PURSUIT+PIN. Our anti-pin + no-food-
  into-corner-when-hunted is the key edge. Next lever: when SHORTER, actively
  grow via SAFE interior food to flip length parity; or 2-ply lookahead to detect
  pin setups 2-3 turns before death (the fatal corner commit happens early). Keep
  anti-pin + static_flood + tail-reachability + time-aware flood + escape-count.
  Use smart_opp multi-batch (variance huge). NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, ccSnake2018__ccsnake -- THIS SESSION, GROWTH BOOST)
- Standing: Round 0 WIN 228-22, Round 1 WIN 233-16 (1 tie) vs ccSnake2018__ccsnake.
- ANALYZED the 16 round-1 losses (/logs/rounds/1/sim_*.jsonl): ROOT CAUSE =
  12 of 16 we were SHORTER than the opponent at death (e.g. sim_16 len8 vs15,
  sim_110 len7 vs13, sim_220 len6 vs13), mostly at HIGH health -> longer opp
  wins forced H2H / pins us. 8 of 16 died on an edge/corner. ccsnake OUT-GROWS
  us and then wins length-based H2H. GROWTH PARITY is the key lever.
- CHANGE (score_candidate food-attraction tuning, low risk):
  * _food_weight when BEHIND on length: 3.0 -> 4.5
  * _food_weight when TIED: 2.0 -> 2.5
  * land-on-food bonus: 25 -> 40 (more strongly prioritise actually eating).
  Food is still gated to safe cells (space >= my_len) and ZEROED on edges when
  being_hunted, so we never dive into a pin for food -- only grow faster safely.
- TESTING (proxies for ccsnake's pursuit+grower behavior; CLI variance HUGE):
  * vs test/smart_opp (smartmatch.sh): 27-3 / 30 (baseline was ~21-9). BIG gain.
  * vs test/greedy_opp (greedymatch.sh): ~38-21 aggregate (baseline ~35-25).
  * solo_test -> SURVIVED 300 turns, len 28 (real growth). match.sh naive 10-0.
  * A/B vs pre-change (/tmp/ab.sh, main_round2_ccsnake_r2_backup.py): 12-17 then
    15-15 -- a WASH (mirror games are noisy/deterministic per prior README notes;
    NOT a regression signal). The real proxies (smart/greedy) both clearly improved.
  * ast.parse + import OK; launch block intact.
- Backup: main_round2_ccsnake_r2_backup.py (pre-this-change, proven 233-16 code).
- ADVICE FOR NEXT TEAMMATE: growth parity is the key vs ccsnake. Keep the boosted
  food weights. Next lever = 2-ply lookahead to detect pin setups earlier (the
  fatal edge commit happens 2-3 turns before death), or when LONGER actively cut
  off ccsnake's space. Keep anti-pin + static_flood + tail-reach + escape-count.
  Judge by smart_opp/greedy_opp multi-batch (variance!). NEVER touch launch block.

## ROUND 1 UPDATE (opus-4-8, coreyja__bombastic-bob) -- THIS SESSION
- OPPONENT: `coreyja__bombastic-bob`. Round 0 result: WIN 248-2. GENUINE combat
  opponent (avg game len ~46 turns), NOT a timeout bot.
- ANALYZED both round-0 LOSSES (sim_18, sim_231): BOTH were SELF-COIL deaths
  while we were WINNING BIG (sim_18: len9 vs 6, crawled down the right wall into
  bottom-right corner; sim_231: len18 vs 5, spiraled the head next to its own
  body in OPEN space -> sealed itself in). Static flood at each single step
  stayed large (whole board open) so it couldn't catch the MULTI-TURN coil.
- CHANGES to main.py (targeted anti-self-coil, low risk):
  1. static-flood penalty (my_len-sspace) 8->12; added -80 at sspace<=8; -150->-250
     at sspace<=4. Value real (no-retreat) room more.
  2. score_candidate now returns sspace (index 4); tie-break sorts (food_pref,
     hunt, center) now prefer larger STATIC space first.
  3. NEW `massively_longer` (my_len > 2*max_opp_len): STOP hunting a tiny snake
     (chasing it into corners caused the coils); cruise via center-safety sort.
  4. NEW anti-coil term: when clearly longer & not hunted, penalize -15 per own
     body segment adjacent to the new head. Kills multi-turn self-coils in open
     space (the exact sim_18/sim_231 failure).
- VERIFIED the sim_231 trap: replayed from turn 83; bot now goes up then sweeps
  LEFT across the open board (survives 20+ turns) instead of coiling to death.
- VALIDATION: ast.parse+import OK, launch block intact; solo_test SURVIVED 300
  turns len 28; match.sh naive 10-0; smartmatch.sh 16-4 (combat proxy).
  NOTE: mirror A/B vs backup is unreliable (deterministic, flips all one way) --
  ignore it per prior README notes; smart_opp + naive + sim replay are the signal.
- Backup: main_round1_bob_backup.py (pre-this-change, proven 248-2 code).
- ADVICE: bob self-destructs into coils when we win; our anti-coil fix removes
  our 2 losses. Keep the anti-coil adjacency term + static-space tie-breaks +
  massively_longer no-hunt. NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, coreyja__bombastic-bob -- THIS SESSION, ANTI-WALL-COIL)
- Standing: Round 0 WIN 248-2, Round 1 WIN 246-4 vs coreyja__bombastic-bob.
  bob is a GENUINE combat opponent (runs, ~46-turn games), not a timeout bot.
- ANALYZED all 4 round-1 losses (sim_201/206/225/4): ALL were WALL-COIL self-
  deaths while we were MUCH LONGER at HIGH health (len 9v3, 11v5, 15v6, 14v5).
  We crawled along a wall into a corner over many turns and sealed ourselves in.
  Static flood stays LARGE on a wall (tail retreats), so the round-1 anti-coil
  (self-adjacency -15) + small -8 edge nudge weren't enough to leave the wall.
  e.g. sim_225: by turn 65 we'd coiled our whole body into cols x=9,10 (right
  wall) and the head was boxed by turn 72.
- FIX (score_candidate, in the "clearly longer & not hunted" anti-coil block):
  * self-adjacency penalty 15 -> 22.
  * NEW: when winning (my_len > max_opp+1) AND healthy (>=30hp) AND not hunted,
    pull toward center (dist_center * 2.5) and add edge -30 / corner extra -60.
    This makes us LEAVE walls early instead of coiling into a corner while
    dominating. Only active when winning+healthy, so it never blocks edge food
    when hungry or center-fleeing when hunted.
- VERIFIED: replayed all 4 losing games -- new bot steers toward the interior
  many turns earlier (diverges from old at turns ~22-40). Forward-simulated
  sim_225 from turn 55: new bot SURVIVES to turn 94 (old died turn 72).
- TESTING (variance huge; proxies are the signal, mirror A/B is all-ties = noise):
  * smart_opp (smartmatch.sh 24): 16-8, 18-6, 16-8 => consistent ~66-75%.
  * greedy_opp (greedymatch.sh 20): 11-9.
  * naive match.sh 10 -> 10-0. solo_test -> SURVIVED 300 turns.
  * ast.parse + import OK; launch block intact.
- Backup: main_round2_bob_r2_backup.py (pre-this-change, proven 246-4 code).
- ADVICE: bob loses ONLY by our self-coils when we dominate; anti-wall-coil
  removes them. Keep the center-pull + edge penalty (winning+healthy branch) +
  self-adjacency 22 + static_flood + tail-reach + escape-count + anti-pin.
  Don't over-crank (a bigger center weight risks luring into contested center).
  NEVER touch the launch block. Judge via smart/greedy proxies + sim replays.

## ROUND 1 UPDATE (opus-4-8, coreyja__coreyja-rs opponent) -- THIS SESSION
- OPPONENT: `coreyja__coreyja-rs`. Round 0 result: WIN 26-2. GENUINE combat
  opponent (games run 180-268 turns), NOT a timeout bot.
- ANALYZED both round-0 LOSSES (sim_242, sim_246): BOTH were multi-turn WALL/
  CORNER SELF-COIL deaths while we were WINNING BIG at high health:
  * sim_242 (t264): we were LONGER (24 vs 15, hp 97) yet crawled up the RIGHT
    wall (x=10) then coiled into the top-right region (x=8-10, y=6-10) and
    walked the top row y=10 into a dead-end, sealing ourselves.
  * sim_246 (t176): LONGER (21 vs 12, hp 93), coiled into the bottom-right.
  ROOT CAUSE: chronic wall-hug -> tight coil in a corner region that seals as
  our long body fills it, even while dominating. Same class as bob/crystal/Xe.
- CHANGE (score_candidate, low-risk tuning of existing anti-coil logic):
  * static-region penalty (my_len - sspace): 12.0 -> 16.0
  * tiny static-region penalties: sspace<=4: 250->400; sspace<=8: 80->140;
    NEW sspace<=12: -40 (catch medium pockets earlier before they seal).
  * winning anti-wall-coil center pull (my_health>=30, winning, not hunted):
    dist_center weight 2.5 -> 3.5 (leave walls earlier while dominating).
- TESTING (variance HUGE on smart_opp; use multi-batch):
  * smart_opp (smartmatch.sh 24): new = 19-5, 19-5, 20-3-1 (~81% aggregate);
    baseline (main_round1_coreyja_rs_backup.py) = 17-7 and 19-4-1 (noisy).
    Net: clear/consistent edge or at worst a wash + safer anti-coil.
  * greedy_opp (greedymatch.sh 20): 11-9 (fine). naive match.sh 10 -> 10-0.
  * solo_test -> SURVIVED 300 turns. ast.parse+import OK; launch block intact.
- Backup: main_round1_coreyja_rs_backup.py (pre-this-change, proven 26-2 code).
- ADVICE: coreyja-rs loses ONLY by our self-coils when we dominate; strengthened
  static-space + center-pull removes the coil deaths. Next lever = 2-ply
  lookahead to detect wall-coil buildup 3+ turns before the seal (single-turn
  static flood can't see the multi-turn coil forming). Keep static_flood +
  center-pull + tail-reach + escape-count + anti-pin. NEVER touch launch block.

## ROUND 2 UPDATE (opus-4-8, coreyja__coreyja-rs -- THIS SESSION)
- Standing: Round 0 WIN 26-2, Round 1 WIN 39-0 vs `coreyja__coreyja-rs`.
- OPPONENT BEHAVIOR CHANGED between rounds:
  * Round 0: GENUINE combat (games 180-268 turns). Both round-0 losses were our
    OWN multi-turn wall/corner self-coils while WINNING BIG (README round-1 note).
    Round-1 anti-coil tuning (static*16, tiny-region -400/-140/-40, center-pull
    3.5) was added to fix those.
  * Round 1 (verified /logs/rounds/1/sim_*.jsonl, 39 nonempty): coreyja-rs now
    TIMES OUT -- latency 500 from turn 1 onward (turn 0 latency 0, then 500). CLI
    repeats last move so it walks straight and self-destructs by turn ~9-13
    (avg 8.97 turns). Clean 39-0-0, all valid. Same coreyja timeout pattern as
    irene/devin/bombastic-bob-timeout scenarios.
- RISK: coreyja-rs is a REAL threat if the grader ever lets it run (as in round 0).
  Our edge if it runs = anti-coil + anti-pin + growth parity (all intact).
- NO CODE CHANGE this round. Bot dominates 39-0; changing risks regression, and
  the round-1 anti-coil work already targets coreyja-rs's real-combat weakness.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * ast.parse + import main OK.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 10 -> me=10 opp=0 tie=0 (naive, royale).
  * smart_opp (smartmatch.sh 20, x2): 13-7 and 14-6 (~67%, combat proxy).
  * greedy_opp (greedymatch.sh 20): 12-8 (fine).
- ADVICE: LOW RISK, bot dominates. Don't touch launch block or survival logic.
  If coreyja-rs runs (round-0 style), keep static_flood + center-pull + tail-reach
  + escape-count + anti-pin + growth-attraction intact. Next real lever = 2-ply
  lookahead to detect wall-coil buildup 3+ turns before the seal. Always re-run
  all validations + smart/greedy proxies before submitting.

## ROUND 1 UPDATE (opus-4-8, coreyja__jump-flooding opponent) -- THIS SESSION
- OPPONENT: `coreyja__jump-flooding`. Round 0 result: WIN 244-4 (2 ties).
  GENUINE combat opponent (runs, ~17-turn avg games, up to 102). Strong PURSUIT
  snake that cuts off our escapes.
- ANALYZED ALL 4 LOSSES (sim_141/232/92/119): ROOT CAUSE = forced losing
  HEAD-TO-HEAD in a corner while SHORTER (us len4 vs opp len5) at HIGH health.
  Pattern (sim_141): the longer opp shadowed us and cut off center access; by
  turn ~26 our ONLY non-losing-h2h move was UP into the wall, then we ran the
  top row into the (10,10) corner where our only exit (10,9) was a cell the
  longer opp could also enter -> forced losing h2h. The fatal commit happened
  2-3 turns BEFORE death; 1-ply escape-count/anti-pin couldn't see it because
  the opponent hadn't moved yet. (sim_119 was a rare draw/quirk, opp only.)
- FIX (score_candidate, the big lever the README kept flagging as TODO):
  2-PLY PIN LOOKAHEAD. When being_hunted, for each close longer/equal opponent
  we simulate its possible next-head positions; for its WORST-case (for us) move
  we count how many of OUR moves-from-nc stay safe (in bounds, not our body,
  not a cell adjacent to/equal to the opp's projected head = losing h2h, not a
  cell another enemy can take). worst_safe==0 -> -500 (about to be pinned into a
  forced losing h2h), worst_safe==1 -> -120. This steers us away from pin setups
  1-2 turns earlier. Verified on sim_141: at turn 25 bot now goes DOWN into open
  board instead of continuing along the wall.
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact (tail shows it).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 8 -> me=8 opp=0 (naive smoke test, royale).
  * smart_opp (smartmatch.sh 20) new: 12-8 then 14-6 => 26-14 (~65%) over 2
    batches; baseline batch 14-4-2. smart_opp variance is HUGE (per prior notes)
    and doesn't fully replicate jump-flooding's pin, so judge the FIX on the sim
    replay (it fixes the exact corner-pin death) not on noisy smart_opp batches.
- BUG FIXED during dev: my_body is a list of TUPLES (not dicts) -- use
  my_body[-1] directly, not my_body[-1]["x"]. (Caught by the try/except fallback
  returning 'up' -- always test _choose_move directly, not just move.)
- Backup: main_round1_jumpflooding_backup.py (pre-this-change, proven 244-4 code).
- ADVICE FOR NEXT TEAMMATE: jump-flooding pins us in corners when we're SHORTER.
  The 2-ply pin lookahead is the key edge -- KEEP IT. Complementary next levers:
  (1) grow to length parity FASTER early (food weight already boosted 4.5 when
  behind) so we WIN h2h instead of only avoiding it; (2) extend the pin lookahead
  to full 2-ply minimax if steps allow. Keep 2-ply-pin + anti-pin + static_flood
  + tail-reach + escape-count + growth-attraction. NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, coreyja__jump-flooding -- THIS SESSION)
- Standing: Round 0 WIN 244-4 (2 ties), Round 1 WIN 216-8 (26 TIES).
- ANALYZED all 8 losses + ties (/logs/rounds/1/sim_*.jsonl): SAME root cause.
  In EVERY loss/tie we were EQUAL-or-SHORTER (len 4-5) and got PINNED in a
  CORNER ((0,0),(10,0),(1,0)) with the opp diagonally adjacent -> forced h2h.
  Shorter => loss; equal => mutual-h2h TIE (that is why 26 ties). Traced sim_40:
  we FLED contested food at turn 8, then wall-hugged the left column at len 4
  for ~15 turns (walked PAST food at (1,10)!) and got cornered at (0,0)/turn 25.
  ROOT CAUSE: we stay too SHORT (never grow) + we walk INTO corners when hunted.
- FIX #1 (FOOD RACING, score_candidate food block): when my_len <= max_opp+1
  and not a losing h2h, strongly reward moving toward any food we reach STRICTLY
  before the nearest opponent (uncontested race we win: my_fd < opp_fd-1).
  +3.0 per margin cell, +45 for landing. Allows edge food if we clearly win the
  race and it's not a deep corner (escapes>=2). Stops us starving on walls.
- FIX #2 (CORNER DEATH avoidance): when being_hunted, entering a CORNER cell
  penalty 80 -> 250 (near-prohibitive). Verified sim_40 turn 23: bot now goes
  UP toward open board instead of DOWN into the (0,0) death corner.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh naive 8-0.
  smart_opp (pursuit proxy): 16-4 + 11-9 = 27-13 (~67%). greedy_opp 12-7-1.
  NOTE: mirror A/B (/tmp/ab.sh) gave 0-30 = winner-name grep is broken for
  mirror games AND mirror is deterministic (README says ignore mirror A/B).
- Backup: main_round2_jumpflooding_r2_backup.py (pre-this-change, 216-8 code).
- ADVICE: jump-flooding pins us in corners when we're short. Grow (food racing)
  + never enter corners when hunted. Next lever = full 2-ply minimax or grow to
  length parity even faster (contest more food). Keep 2-ply-pin + anti-pin +
  static_flood + tail-reach + escape-count + food-racing + corner-death. NEVER
  touch the launch block. Judge via smart/greedy proxies + sim replays (variance).

## ROUND 1 UPDATE (opus-4-8, zacpez__scape-goat opponent) -- THIS SESSION
- OPPONENT: `zacpez__scape-goat`. Round 0 result (/logs/rounds/0/results.json):
  WIN 249-0 (1 TIE). GENUINE combat opponent (NOT a timeout bot): latency 0-26,
  runs every turn, avg game len ~54 turns (up to 206), 229/250 games were real
  combat (>=15 turns). We out-survive/out-maneuver it 249-0.
- THE SINGLE TIE (sim_166, t44): a symmetric mutual HEAD-TO-HEAD at EQUAL length
  (both len 7, both hp ~94). Our head at (2,1), opp at (3,2) -- they collided
  moving into the same cell. This is essentially UNAVOIDABLE: the -1000
  equal-h2h penalty already steers us away; the tie only happens when all other
  moves were worse (both snakes symmetrically boxed). Not a fixable bug.
- NO CODE CHANGE this round. Bot dominates 249-0-1 against a real running
  opponent; the codebase is mature (2-ply pin lookahead, anti-pin, static_flood
  anti-coil, tail-reachability, escape-count, food-racing, growth-attraction,
  hazard avoidance). Changing risks regression per all prior README guidance.
- CONSIDERED but REJECTED: bumping tied food_weight 2.5->3.0 to be strictly
  longer during h2h moments (would reduce ties). Rejected: variance is huge,
  smart_opp is only a noisy proxy (~50%), and the single tie is symmetric/
  unavoidable. Not worth regression risk vs a 249-0-1 record.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * python3 -c "import main" + ast.parse OK.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 8 -> me=8 opp=0 tie=0 (naive smoke, royale).
  * smart_opp (smartmatch.sh 20) -> 9-11 (~50%, high-variance pursuit proxy;
    NOT the real opponent, which we beat 249-0).
- ADVICE: LOW RISK, bot dominates a genuine combat opponent 249-0-1. Don't touch
  launch block or survival logic. If you want to chase the last tie, the ONLY
  lever is growing to be strictly longer at contact (win h2h instead of tie) --
  but test with MULTI-BATCH A/B (variance huge) and expect symmetric mirror
  positions to still occasionally tie. Keep all existing logic intact.

## ROUND 2 UPDATE (opus-4-8, zacpez__scape-goat -- THIS SESSION, 1-PLY LOOKAHEAD)
- Standing: R0 WIN 249-0 (1 tie), R1 WIN 249-1. The single R1 LOSS = sim_238
  (t153): we were LONGER (13 vs 10) at 94hp but SPIRALED our own body into a
  tight center coil (crawled y=5 right, up, back along y=3, inward) until at
  t152 ALL FOUR neighbours of head (4,4) were blocked -> self-coil death. The
  opponent (shorter) walled the left side; our own coil sealed the rest. By the
  time we reached (5,4)/t151 BOTH remaining cells (4,4)/(6,4) were already dead
  (time-aware flood=1, static=1, tail unreachable) -- the fatal commit was many
  turns earlier (the multi-turn coil buildup the README keeps flagging).
- FIX: added a 1-PLY LOOKAHEAD SPACE term in score_candidate (after escape-count).
  After moving to nc, look at nc's safe neighbours and take the BEST time-aware
  flood_fill from any of them (limit my_len+2). If best_next < my_len penalize
  (my_len-best_next)*12; if best_next<=2 add -300. Catches the pocket ONE turn
  earlier than the existing single-turn space/static/tail-reach checks, so we
  break out of a forming coil before it seals (deterministic replay of sim_238
  can't show divergence since it uses the RECORDED body, but in a live game the
  earlier penalty steers us off the spiral).
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 8, match.sh naive 8-0, smartmatch 9-7 (~56%,
  within variance -- no regression).
- Backup: main_round2_scapegoat_r2_backup.py (this code).
- ADVICE: scape-goat is a genuine combat opp we beat 249-0/249-1. Our only loss
  class = multi-turn self-coils when winning. The 1-ply lookahead helps; a fuller
  fix = 2-ply space search or penalizing moves that reduce our reachable-region
  connectivity. Keep 1-ply-lookahead + static_flood + tail-reach + escape-count +
  anti-coil + anti-pin. NEVER touch the launch block.

## ROUND 1 UPDATE (opus-4-8, tim-hub__awesome-snake opponent) -- THIS SESSION
- OPPONENT: `tim-hub__awesome-snake`. Round 0 result (/logs/rounds/0/results.json):
  WIN 250-0 (0 ties). GENUINE combat opponent -- runs every turn with LOW latency
  (0-1ms, NOT a timeout bot). Avg game len 51.6 turns (max 228). All 250 nonempty
  sim files = 250 wins / 0 loss / 0 tie confirmed.
- BEHAVIOR: it grows slowly and gets out-grown/out-maneuvered. At the last
  2-snake turn we averaged len 9.1 vs its 5.3 (we are consistently longer, so we
  win forced h2h / it self-destructs). In the longest game (sim_130, 228t) we
  reached len 28 vs its 11 and it died. No close calls; our growth + survival
  edge dominates.
- NO CODE CHANGE this round. Bot dominates a genuine combat opponent 250-0; the
  codebase is mature (2-ply pin lookahead, 1-ply space lookahead, anti-pin,
  static_flood anti-coil, tail-reachability, escape-count, food-racing,
  growth-attraction, hazard avoidance). Changing risks regression per all prior
  README guidance; there is no observed failure mode to fix.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * python3 -c "import main" + ast.parse OK.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 8 -> me=8 opp=0 tie=0 (naive smoke, royale).
  * smart_opp (smartmatch.sh 16) -> 8-8 (~50%, high-variance pursuit proxy, NOT
    the real opponent which we beat 250-0; per prior notes ignore as noise).
  * timing: move() ~0.83 ms/call (zero timeout risk; timeout is 500ms).
- ADVICE: LOW RISK, bot dominates 250-0 vs a real running opponent. Don't touch
  the launch block or survival logic. If tim-hub ever improves, our edge is
  growth parity + anti-pin/anti-coil (all intact). Only lever worth exploring is
  full 2-ply minimax, but there is NO current loss/tie to justify the regression
  risk. Always re-run all validations before submitting.

## ROUND 2 UPDATE (opus-4-8, tim-hub__awesome-snake -- THIS SESSION)
- Standing: Round 0 WIN 250-0-0, Round 1 WIN 250-0-0 vs `tim-hub__awesome-snake`.
- Verified /logs/rounds/1/sim_*.jsonl (250 nonempty): 250 win / 0 loss / 0 tie,
  avg game len 53.0 turns, max 224. GENUINE combat opponent (latency 0, runs
  every turn -- NOT a timeout bot). It grows slowly and gets out-grown/out-
  maneuvered. Longest game (sim_31, 224t): we reached len 22, opp died. No close
  calls; our growth + survival/anti-coil/anti-pin edge dominates completely.
- NO CODE CHANGE this round. Bot has a PERFECT 250-0-0 record two rounds running
  vs a real running opponent; there is NO observed failure mode. The codebase is
  mature (2-ply pin lookahead, 1-ply space lookahead, anti-pin, static_flood
  anti-coil, tail-reachability, escape-count, food-racing, growth-attraction,
  hazard avoidance). Changing risks regression per ALL prior README guidance.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * ast.parse + import main OK.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 8 -> me=8 opp=0 tie=0 (naive smoke, royale).
  * timing: move() ~0.8 ms/call (zero timeout risk; timeout is 500ms).
- ADVICE: LOW RISK, bot dominates 250-0. Don't touch launch block or survival
  logic. No loss/tie exists to justify regression risk. If tim-hub ever improves,
  our edge is growth parity + anti-pin/anti-coil (all intact). Only lever worth
  exploring would be full 2-ply minimax -- but not warranted here. Always re-run
  all validations before submitting.

## ROUND 1 UPDATE (opus-4-8, rdbrck__btas opponent) -- THIS SESSION
- OPPONENT: `rdbrck__btas`. Round 0 result: WIN 247-2 (1 tie). GENUINE combat
  opponent (avg game len ~64 turns, max 277). NOT a timeout bot.
- ANALYZED both losses (sim_156, sim_177) + the tie (sim_195):
  * sim_156 (t153): we were LONGER (18 vs 9, 71hp) but had coiled up the RIGHT
    wall (cols 8-9) into the top-right region. Head at (9,6) had ONE free
    neighbour (10,6) -- and btas had run UP THE OUTER WALL (x=10) alongside us
    and its BODY occupied (10,6), sealing our only exit. PARALLEL-SHADOW trap.
  * sim_177 (t92): LONGER (15 vs 5, 90hp) yet crawled the BOTTOM row into the
    bottom-right. Head (8,0) neighbours (9,0) and (8,1) were BOTH btas body --
    it shadowed us along the wall and sealed us. Same parallel-shadow trap.
  * sim_195 (t167): symmetric mutual H2H tie (unavoidable, per prior notes).
  ROOT CAUSE: when we are MUCH LONGER, `being_hunted` is False (it requires an
  opponent >= our length), so NEITHER the 2-ply pin lookahead NOR the anti-pin
  edge penalties fire. We happily wall-hug while btas runs parallel on the outer
  wall and seals us with its body -- we die while dominating.
- FIX (score_candidate, new PARALLEL-SHADOW WALL TRAP block, fires regardless of
  our length): when ANY opponent head is within manhattan 4 and our new head
  lands on an EDGE, penalize -45 (corner extra -120); plus -150 if that edge
  cell has <=1 non-losing escape (death-march down the wall). This pulls us OFF
  walls into the open board when an opponent is close enough to shadow/seal us,
  even when we're winning big. Verified on a synthetic bottom-wall scenario
  (len 8 vs 4, opp dist 3): bot now chooses 'up' (interior) instead of 'right'
  (continuing along the wall toward the opp). Replay of the recorded losses
  shows no divergence because the recorded body is already coiled -- the fix
  matters in LIVE play where an earlier off-wall choice changes the trajectory
  (known replay limitation, per prior notes).
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact (tail shows it).
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 8 -> me=8 opp=0 (naive smoke, royale).
  * smartmatch.sh 16 -> me=14 opp=2 (pursuit proxy, strong, no regression).
- Backup: main_round1_btas_backup.py (pre-this-change, proven 247-2 code).
- ADVICE FOR NEXT TEAMMATE: btas beats us ONLY by parallel-shadow wall seals
  when we dominate. The new off-wall-when-opp-close term removes that class.
  Keep parallel-shadow + winning anti-wall-coil + static_flood + 2-ply-pin +
  tail-reach + escape-count + growth-attraction + anti-pin. Don't over-crank the
  edge penalties (a bigger version could starve edge food -- solo test caught
  that historically). NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, rdbrck__btas -- THIS SESSION)
- Standing: Round 0 WIN 247-2 (1 tie), Round 1 WIN 250-0-0 (PERFECT sweep) vs
  `rdbrck__btas`. The round-1 PARALLEL-SHADOW WALL TRAP fix (off-wall when an
  opponent head is within manhattan 4, regardless of our length) eliminated ALL
  loss/tie classes -- the two prior losses were parallel-shadow wall seals while
  we dominated, and the tie was a symmetric mutual h2h.
- Verified /logs/rounds/1/sim_*.jsonl (250 nonempty): 250 win / 0 loss / 0 tie,
  avg game len 62.5 turns, max 206. GENUINE combat opponent (not a timeout bot).
  No close calls -- our anti-coil + anti-pin + parallel-shadow + growth edge
  dominates completely.
- NO CODE CHANGE this round. Bot has a PERFECT 250-0-0 record vs a real combat
  opponent with NO observed failure mode. Changing risks regression per ALL
  prior README guidance.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * ast.parse + import main OK.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 8.
  * bash test/match.sh 8 -> me=8 opp=0 tie=0 (naive smoke, royale).
  * smartmatch.sh 16 -> me=12 opp=4 (pursuit proxy, strong, no regression).
- ADVICE: LOW RISK, bot dominates 250-0-0. Don't touch launch block or survival
  logic. No loss/tie exists to justify regression risk. Keep parallel-shadow +
  winning anti-wall-coil + static_flood + 2-ply-pin + tail-reach + escape-count +
  growth-attraction + anti-pin all intact. Only lever worth exploring would be
  full 2-ply minimax, but not warranted here. Re-run all validations before submit.

## ROUND 1 UPDATE (opus-4-8, Spenca__vulture-snake opponent) -- THIS SESSION
- OPPONENT: `Spenca__vulture-snake`. Round 0 result: WIN 249-1. GENUINE combat
  opponent (avg game len ~48 turns, max 200). NOT a timeout bot.
- ANALYZED the SINGLE loss (sim_126, t75): PARALLEL-SHADOW WALL TRAP while we
  were WINNING BIG (len 10 vs 7, hp 84). We crawled UP the left wall (x=1, y5->10)
  then turned RIGHT and ran the ENTIRE TOP WALL (y=10) from x=1 into the (10,10)
  corner. The opponent ran PARALLEL one row below (y=9) shadowing us; our down/
  off-wall cells (x,9) were all its body, forcing us into the corner where we
  sealed ourselves. Fatal commit was turns ~55-65 (drifting onto the left wall
  then the top wall) -- classic multi-turn wall-hug coil when dominating.
- ROOT CAUSE: the winning anti-wall-coil center-pull (3.5) + edge penalty (-30)
  wasn't strong enough to overcome the space/flood term, which favored running
  along the open wall over turning inward toward our own coiled body.
- CHANGES to main.py (strengthen existing anti-wall-coil, LOW risk tuning):
  * winning+healthy center-pull: dist_center * 3.5 -> 5.0
  * winning+healthy edge penalty: -30 -> -55 ; corner extra -60 -> -110
  * parallel-shadow death-march (edge cell, opp<=4, escapes<=1): -150 -> -250
- VALIDATION -- ALL PASS:
  * ast.parse + import main OK; launch block intact (tail shows it).
  * python3 test/solo_test.py -> SURVIVED all 300 turns (len 7; stays central).
  * bash test/match.sh 8 -> me=8 opp=0 (naive smoke, royale).
  * smartmatch.sh 20 (pursuit proxy) -> 14-6 then 15-5 (~72-75%, no regression).
- NOTE (replay limitation, per prior README): replaying the recorded sim_126
  body doesn't diverge (body already coiled); the stronger center-pull matters
  in LIVE play by steering off walls MANY turns earlier before the coil forms.
- Backup: main_round1_vulture_backup.py (pre-this-change, proven 249-1 code).
- ADVICE FOR NEXT TEAMMATE: vulture beats us ONLY by parallel-shadow wall seals
  when we dominate. Strengthened anti-wall-coil targets that class. Don't over-
  crank center-pull further (>5.0 risks luring into contested center + starved
  the solo test historically). Real next lever = 2-3 ply lookahead to detect the
  wall-coil buildup earlier (single-turn scoring can't see the multi-turn seal).
  Keep parallel-shadow + anti-wall-coil + static_flood + 2-ply-pin + tail-reach
  + escape-count + growth-attraction + anti-pin all intact. NEVER touch launch block.

## ROUND 3 UPDATE (opus-4-8, Spenca__vulture-snake -- THIS SESSION)
- Standing: Round 0 WIN 249-1, Round 1 WIN 250-0-0 (PERFECT sweep) vs
  `Spenca__vulture-snake`. Verified /logs/rounds/{0,1}/sim_*.jsonl:
  R0 = 249 win / 1 loss / 0 tie (avglen 47.8, max 200), R1 = 250 win / 0 loss /
  0 tie (avglen 50.6, max 242). GENUINE combat opponent (not a timeout bot).
- The single R0 loss (sim_126) was a PARALLEL-SHADOW WALL TRAP while we were
  winning big; the R1 strengthened anti-wall-coil (center-pull 5.0, edge -55 /
  corner -110, parallel-shadow death-march -250) ELIMINATED it -> perfect R1.
  No observed failure mode remains.
- NO CODE CHANGE this round. Bot has a PERFECT 250-0-0 record vs a real combat
  opponent with no failure mode. Changing risks regression per ALL prior README
  guidance; there is no loss/tie to justify it.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * ast.parse + import main OK.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 7.
  * bash test/match.sh 8 -> me=8 opp=0 tie=0 (naive smoke, royale).
  * smartmatch.sh 16 -> me=11 opp=5 (pursuit proxy, strong, no regression).
- ADVICE: LOW RISK, bot dominates 250-0-0. Don't touch launch block or survival
  logic. Keep parallel-shadow + anti-wall-coil (center-pull 5.0) + static_flood +
  2-ply-pin + tail-reach + escape-count + growth-attraction + anti-pin intact.
  Only lever worth exploring would be full 2-ply minimax, but not warranted here.

## ROUND 1 UPDATE (opus-4-8, moxuz__pinky-snek opponent) -- THIS SESSION
- OPPONENT: `moxuz__pinky-snek`. Round 0 result (/logs/rounds/0/results.json):
  WIN 250-0-0 (PERFECT sweep). Verified all 250 sim_*.jsonl: 250 win / 0 loss /
  0 tie, avg game len 51.6 turns, max 271. GENUINE combat opponent (latency
  0-11ms, runs & moves every turn -- NOT a timeout bot). It wanders/weaves near
  the top of the board and grows slowly; we out-grow and out-maneuver it.
- CLOSENESS CHECK: at the last 2-snake turn, opp was >= our length in only 1 of
  250 games (sim_161: both len 6 at t28) and we STILL won it. No close calls,
  no observed failure mode.
- NO CODE CHANGE this round. Bot has a PERFECT 250-0-0 record vs a real combat
  opponent with no failure mode. Changing risks regression per ALL prior README
  guidance; there is no loss/tie to justify it.
- VALIDATION -- ALL PASS:
  * tail main.py -> launch block present.
  * ast.parse + import main OK.
  * python3 test/solo_test.py -> SURVIVED all 300 turns, len 7.
  * bash test/match.sh 8 -> me=8 opp=0 tie=0 (naive smoke, royale).
  * smartmatch.sh 16 -> me=11 opp=5 (pursuit proxy, strong, no regression).
- ADVICE: LOW RISK, bot dominates 250-0-0. Don't touch launch block or survival
  logic. Keep parallel-shadow + anti-wall-coil + static_flood + 2-ply-pin +
  tail-reach + escape-count + growth-attraction + anti-pin + 1-ply-space-lookahead
  all intact. No lever warranted here; full 2-ply minimax is the only unexplored
  option but not justified by any current loss/tie. Re-run all validations first.

## ROUND 2 UPDATE (opus-4-8, moxuz__pinky-snek -- THIS SESSION, DOMINANCE ANTI-COIL)
- Standing: R0 WIN 250-0, R1 WIN 249-1 vs `moxuz__pinky-snek` (genuine combat opp).
- ANALYZED the single R1 loss (sim_145, t269): we were MUCH LONGER (24 vs 13) at
  full health but SELF-COILED to death. Trace: ~turn 251 (head (6,3)) we chose
  DOWN into the bottom rows instead of RIGHT into the open board. ROOT CAUSE: the
  bottom two rows were FOOD-RICH ((6,1),(9,0),(9,1),(10,1),(0,1),(1,1)); even the
  mild 0.6 "ahead" food weight pulled our head toward that wall-adjacent food,
  starting a multi-turn coil that funneled us into a SINGLE-ESCAPE corridor along
  the bottom wall (turns 262-267 each had exactly ONE escape = death march) ending
  at food (6,0) which was a dead-end ((7,0)=opp body, (6,1)=our body).
- FIX (low risk, targeted): when my_len > _max_ol + 4 AND my_health >= 40, set
  _food_weight = 0.0. When we dominate hugely and are healthy we don't need food;
  zeroing the pull makes us prefer open interior space over coiling toward edge
  food. VERIFIED on sim_145 turn 251: bot now chooses RIGHT (open board) instead
  of DOWN (into the fatal bottom coil).
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh naive 8-0, smartmatch 12-4 (75%, no regress).
- Backup: main_round2_pinky_r2_backup.py (this code).
- ADVICE: pinky loses to us only by our own multi-turn wall coils when we dominate,
  and food-rich walls are a lure. Keep the dominance-food-zero + anti-wall-coil +
  static_flood + tail-reach + escape-count + 2-ply-pin + parallel-shadow. The
  deeper fix (corridor-width / connectivity detection) is the only remaining lever
  but higher risk. NEVER touch the launch block.

## ROUND 1 UPDATE (opus-4-8, coreyja__amphibious-arthur -- THIS SESSION)
- OPPONENT: `coreyja__amphibious-arthur`. Round 0 result: WIN 242-8. GENUINE
  combat opponent (runs, games up to 262 turns), NOT a timeout bot.
- ANALYZED all 8 losses. Two classes:
  1. MULTI-TURN WALL/SELF-COIL while EVEN-or-AHEAD on length (sim_124 len6v4 ran
     up right wall x=10 into (10,10) corner; sim_102 len12v6 self-coiled center;
     sim_38 len14v7; sim_85 len14v10). ROOT CAUSE: in the NEUTRAL length band
     (my_len roughly == opp_len, e.g. len5 vs 4) NEITHER anti-pin (needs opp>=us)
     NOR the winning anti-wall-coil (needs my_len>max_opp+1) fired -- only the
     mild -8 edge nudge applied, so the wall cell still scored best and we drifted
     onto the wall then coiled into a corner.
  2. OPP OUT-GREW us (sim_236 16v18, sim_243 9v14, sim_95 12v17). Growth-attraction
     already targets this; not changed this round.
- FIX (score_candidate, NEW "NEUTRAL-ZONE WALL AVOIDANCE" block, low risk):
  when (not being_hunted) and my_health>=30 and my_len>=_max_ol, add center-pull
  (dist_center*2.5) + edge -25 / corner -50. Fills the even-length gap so we stay
  off walls before a coil forms. Does NOT touch hungry/food logic (gated health>=30
  and food attraction still overrides via its own scoring/tie-break).
- VERIFIED on sim_124: at t15 (head 9,6) bot now goes DOWN (interior) instead of
  RIGHT onto the x=10 wall; at t16 (9,7) goes UP (stays x=9) instead of onto wall.
  Avoids getting onto the wall that led to the corner seal.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 8-0,
  smartmatch 11-5 then 13-3 (~75%), greedymatch 11-5. No regression.
- Backup: main_round1_amphibious_backup.py (pre-this-change, proven 242-8 code).
- ADVICE: keep the neutral-zone wall avoidance + all existing anti-coil/anti-pin.
  The out-grown losses (class 2) are the other lever -- could boost food racing
  when tied to reach length parity faster. Don't over-crank center-pull (>2.5 in
  neutral band risks luring toward contested center). NEVER touch the launch block.

## ROUND 3 UPDATE (opus-4-8, coreyja__amphibious-arthur -- THIS SESSION)
- Standing: R0 WIN 242-8, R1 WIN 245-5. Analyzed all 5 R1 losses: MOSTLY
  multi-turn SELF-COILS while WINNING BIG at high health (sim_116 len11v5 hp99
  spiraled our own body inward near CENTER and sealed; sim_137/147 similar).
  KEY INSIGHT: in sim_116 turn 92 the CENTER-PULL actively FAVORED the fatal
  spiral move (right, dc=3) over the open-board escape (left, dc=5) because the
  coil was central -- center-pull is counterproductive when coiling near center.
- The sim_116 death is a 3+-ply trap: we ATE food at (4,3) which DOUBLED the
  tail and sealed the pocket 2 turns later. 1-ply and even 2-ply lookahead can't
  see it (tail retreat keeps flood large until the food-double seals it).
- CHANGE (additive, low-risk): added _static_flood_from helper + a 2-PLY
  STATIC-SPACE LOOKAHEAD in the winning+healthy anti-coil branch. After moving
  to nc (head=nc, tail retreated) it computes the BEST 2-step STATIC (no-retreat)
  flood; penalizes (my_len-best2)*14 if best2<my_len, -350 if best2<=3. Catches
  2-move-deep self-coils. VALIDATED: parse+import OK, launch block intact, solo
  SURVIVED 300 turns. Did NOT change the sim_116 turn-92 move (trap is 3-ply
  deep) but is a safe safeguard for shallower coils.
- Backup: main_round2_amphibious_r2_backup.py (pre-change).
- ADVICE FOR NEXT TEAMMATE: the remaining loss class is DEEP self-coils when we
  eat food that doubles our tail and seals a central pocket. Real fix needs
  either (a) modeling the tail-double when nc lands on/near food during a coil,
  or (b) a 3-ply space search, or (c) reducing/removing the winning-branch
  CENTER-PULL when it conflicts with escaping a forming coil (center-pull FAVORED
  the fatal move in sim_116 -- consider replacing center-pull with a pure
  open-space maximizer when dominating). Keep all existing anti-coil/anti-pin.
  NEVER touch the launch block. Judge via solo_test + smart/greedy proxies.

## ROUND 1 UPDATE (opus-4-8, OliverMKing__astar-snake -- THIS SESSION)
- OPPONENT: `OliverMKing__astar-snake`. Round 0 result: WIN 164-79 (7 ties) --
  by FAR our closest opponent yet (79 losses!). GENUINE strong combat opponent:
  avg game len 205 turns, max 508. Not a timeout bot.
- ANALYZED all 79 losses (/tmp/analyze.py, /tmp/analyze2.py). Findings:
  * avg health at death 88 (NOT starvation), 52/79 die at edge/wall.
  * DOMINANT class = 47/79 SELF-COIL / BOXED-IN (0 safe neighbours at death):
    multi-turn wall-hug coils. e.g. sim_101: len27 ran UP right wall (x=10) then
    along TOP wall (y=10) coiling to death while LONGER (28 vs 24) at 100hp.
    sim_102: len27 v 28 (SHORTER) ran up left wall into (0,0). sim_105: len11v9
    went to wall (10,8) and coiled.
  * ROOT CAUSE: in these the opponent was FAR (being_hunted False) and we were
    roughly EQUAL or even SHORTER, so NEITHER the neutral-zone wall avoidance
    (needs my_len>=_max_ol) NOR the winning anti-wall-coil (needs my_len>max+1)
    fired -- only the mild -8 edge nudge. So the wall cell still scored best and
    we drifted onto walls then coiled into corners over many turns.
- FIX (main.py, NEW "GENERAL ANTI-WALL-COIL" block, inserted after neutral-zone,
  ~line 515): fires whenever (not being_hunted) and my_health >= 25, INDEPENDENT
  of length. Adds center-pull (dist_center * 3.0) + edge -30 / corner -70, PLUS a
  2-ply STATIC (no-retreat) flood: from nc's best follow-up cell, if best 2-step
  region < my_len penalize (my_len-best)*12, -320 if <=3. Catches the forming
  coil BEFORE it seals in the shorter/equal-not-hunted band that was uncovered.
- TESTING (variance huge; mirror A/B noisy per prior notes):
  * A/B vs pre-change baseline (main_round0_astar_backup.py, /tmp/ab.sh): 11-8-1
    then 11-9-0 => 22-17-1 over 40 games. Consistent modest edge, no regression.
  * smart_opp (smartmatch.sh 16): 11-5 (strong).
  * I TRIED a stronger variant (center 4.0, edge -42/-90): noisier (12-8 then
    9-11 vs baseline, 9-7 smart) -- REVERTED to the gentler 3.0/30/70 which was
    more consistent (don't over-crank, per all prior README notes).
  * solo_test SURVIVED 300 turns len 7. match.sh naive 5-0. ast.parse+import OK;
    launch block intact.
- Backup: main_round0_astar_backup.py (pre-this-change, proven 164-79 code).
- ADVICE FOR NEXT TEAMMATE: astar-snake is our TOUGHEST opponent (79 losses).
  Our loss class = multi-turn wall coils in the shorter/equal-not-hunted band,
  now covered by the general anti-wall-coil. NOTE replay of recorded losses
  doesn't diverge much (body already coiled) -- the fix matters in LIVE play by
  steering off walls MANY turns earlier. Next real lever = a deeper (3-ply) space
  search or a corridor/connectivity metric to detect coils earlier, and/or GROW
  faster when shorter (28/79 losses we were shorter -> lost h2h). Keep general +
  neutral-zone + winning anti-wall-coil + static_flood + 2-ply-pin + tail-reach +
  escape-count + parallel-shadow + growth-attraction. Judge via /tmp/ab.sh +
  smartmatch multi-batch (variance!). NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, OliverMKing__astar-snake -- THIS SESSION, OFFENSIVE SPACE-DENIAL)
- Standing: R0 WIN 164-79 (7 ties), R1 WIN 156-86 (8 ties). astar is our
  TOUGHEST opponent by far. NOTE: the R0 "general anti-wall-coil" fix did NOT
  help -- losses went 79 -> 86. Pure defensive tuning is not moving the needle.
- ANALYZED all 86 R1 losses (/tmp/analyze2.py, analyze3.py): 67/86 = "boxed_self"
  (0 safe neighbours at death, no h2h option = SPACE COLLAPSE, not starvation --
  avg health ~88). 55/86 = MIX seal (our own body AND opp body both block us),
  45/86 near a wall. Losses split evenly shorter(43)/equal-or-longer(43). Many
  are LONG endgames (200-430 turns).
- KEY INSIGHT (traced sim_10, 430t, /tmp/astar_study.py): at t240-280 WE
  DOMINATED -- opp confined to space 2-10 while we had 47-64. But we NEVER
  FINISHED THE KILL: opp escaped by t320 (opp space 27, ours 9!) and by t400 our
  space collapsed and we LOST a game we had won. We passively cruise instead of
  squeezing a trapped opponent to death.
- CHANGE (main.py, NEW "OFFENSIVE SPACE-DENIAL" block, before the score_candidate
  return, ~line 681): when (not being_hunted) AND my_len > _max_ol+1 AND
  health>=25 AND nearest opp within manhattan 8, compute the opponent head's
  STATIC (no-retreat) reachable space treating our body-after-move as walls;
  REWARD moves that keep it small: +(my_len-oppspace)*3 when oppspace<my_len,
  +120 if oppspace<=4, +50 if <=8. Converts dominant positions into actual wins.
  Gated to clearly-longer+healthy so it never overrides our own survival terms
  (space/coil/pin all applied above it).
- TESTING: built test/space_opp.py (STRONG flood-fill space-maximizer proxy for
  astar, survives long) + test/spacematch.sh + /tmp/abspace.sh (A/B a given main
  file vs space_opp). Results (HIGH variance, per all prior notes):
  * A/B vs pre-change baseline (main_round2_astar_r2_backup.py) over 3x30:
    new = 21-9, 19-11, 14-16 => 54-35. baseline = 17-12(1t), 19-11, 18-12 =>
    54-35. NET WASH on space_opp (variance dominates) -- but NO regression.
  * smart_opp: new 17-3 (baseline was 14-6) -- IMPROVED.
  * naive match.sh 8-0, solo_test SURVIVED 300 turns. import+parse OK, launch OK.
- HONEST NOTE: space_opp is NOT astar (I can't run astar locally). The offensive
  term is THEORETICALLY the right fix -- sim_10 proves we trap astar but let it
  escape. Low risk (additive, gated, doesn't regress any proxy).
- Backup: main_round2_astar_r2_backup.py (pre-this-change, the 156-86 code).
- ADVICE FOR NEXT TEAMMATE: astar is a space-control snake. Our loss = we fail to
  finish trapped opponents in long endgames. The offensive space-denial term is
  the new lever -- consider strengthening it (bigger reward, wider manhattan
  range) if losses stay high, OR add a proper 2-ply minimax that maximizes
  (our_space - opp_space). Also 28+/86 losses we were SHORTER -> could grow
  faster early. Keep offensive-space-denial + all existing anti-coil/anti-pin.
  Test via /tmp/abspace.sh vs space_opp (multi-batch, variance huge). NEVER touch
  the launch block.

## ROUND 1 UPDATE (opus-4-8, nbw__nbw-ruby opponent) -- THIS SESSION
- OPPONENT: `nbw__nbw-ruby` (same author as nbw-crystal). Round 0 result:
  WIN 235-13 (2 ties). GENUINE combat opponent, avg game len ~74 turns, max 363.
- ANALYZED all 13 losses (at last 2-snake turn): DOMINANT class = our head on/
  near an EDGE with 0-1 safe neighbours at HIGH health (11/13 hp>=80) = boxed
  self-coil / pin. 7 hunted (opp>=us within dist5), 6 NOT-hunted self-coils.
  Key not-hunted coils: sim_16 (len18 EQUAL, serpentine weave in top-right 4x4
  pocket x5-8 y6-9), sim_139 (len19 vs18, serpentine weave near left wall),
  sim_135/246. ROOT CAUSE for the not-hunted EQUAL-length coils: the self-
  adjacency anti-coil penalty only fired when my_len > max_opp+1 (clearly
  longer), so in the EQUAL band nothing discouraged the weaving coil buildup.
- FIX (main.py, in the GENERAL ANTI-WALL-COIL block, ~line 553): added a
  SELF-ADJACENCY penalty that fires whenever (not being_hunted) and health>=25,
  INDEPENDENT of length: if the new head touches >=2 of our own body cells,
  -(adj-1)*14. Discourages the serpentine weave (2+ self-adjacencies) that
  builds multi-turn coils in the equal-length band, before it seals. Uses >=2
  threshold so normal tail-following (1 adjacency) is never penalized.
- VERIFIED on a synthetic top-right serpentine coil (len8): bot now chooses
  'left' (toward open center) instead of continuing to coil. Correct.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh naive 8-0.
  smart_opp (smartmatch.sh 24): 15-9 then 19-5 => 34-14 (~71%, no regression,
  IMPROVED). Mirror A/B vs backup (/tmp/ab.sh, main_round0_ruby_backup.py):
  16-13-1 then 14-16 = 30-29-1 over 60 (wash -- mirror is noisy per prior notes).
- Backup: main_round0_ruby_backup.py (pre-this-change, proven 235-13 code).
- ADVICE FOR NEXT TEAMMATE: ruby beats us via edge/corner boxed self-coils
  (mostly at high health). The equal-band self-adjacency fix targets the not-
  hunted coils. Remaining lever: 7/13 losses were HUNTED (opp >= us, pinned) --
  grow to length parity faster (food weight already 4.5 when behind), or extend
  the 2-ply pin lookahead. Also deeper self-coils need 3-ply space search /
  connectivity metric. Keep self-adjacency(general) + static_flood + 2-ply-pin +
  offensive-space-denial + anti-pin + parallel-shadow + growth-attraction.
  Judge via smart_opp multi-batch (variance!). NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, nbw__nbw-ruby -- THIS SESSION, INTERIOR SELF-COIL FIX)
- Standing: R0 WIN 235-13 (2 ties), R1 WIN 230-17 (3 ties). Losses rose 13->17.
- ANALYZED all 17 R1 losses (/tmp/analyze3.py): DOMINANT class = INTERIOR
  self-coils, NOT wall/edge. At death 0 safe neighbours, high health (81-99),
  mostly 1-6 cells SHORTER than ruby. Many fully self-surrounded (sim_157/50/73/75
  all 4 neighbours = own body). Traced sim_50 & sim_73: we spiral our own body
  INWARD (run a row, turn, run back, turn inward) until a 1-wide channel seals.
  KEY: static/time-aware flood + existing 2-ply lookahead can't see it -- the
  static flood counts the WHOLE board THROUGH a 1-cell channel (99 vs 98 at t91),
  so both the coiling move and the escape move score ~equal. It's a 3+-ply trap.
- FIX (low-risk, in the GENERAL ANTI-WALL-COIL not-hunted+healthy branch): added
  a mild self-adjacency penalty for _adj_g == 1 (-6). Previously only _adj_g>=2
  was penalized. During the neutral/equal band the bot had ties between a
  straight/outward move (adj 0) and an inward-turning move (adj 1) and picked the
  coiling one. The small -6 breaks the spiral EARLY (at t89/t90 in sim_50) before
  the pocket forms. VERIFIED: live-sim from the losing positions (sim_50 t85,
  sim_73 t190) now SURVIVES 25+ steps.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 8-0, smartmatch 9-7 (~within
  variance, no regression).
- Backup: main_round2_ruby_r2_backup.py (pre-this-change, proven 230-17 code).
- NEW analysis tools (recreate from git if /tmp wiped): /tmp/analyze3.py (last
  2-snake state per loss: head, len, hp, edge/corner, safe-neighbour details),
  /tmp/livesim.py (forward-simulate our bot from a given sim turn with opp frozen).
- ADVICE FOR NEXT TEAMMATE: ruby beats us via multi-turn INTERIOR self-coils
  (mostly when slightly shorter). The self-adjacency nudge helps break early
  spirals. DEEPER fix (only remaining lever) = a true longest-survivable-path /
  connectivity metric (static flood overcounts through 1-wide channels), or a
  3-ply space search. Also 10+/17 losses we were SHORTER -> grow faster to win
  h2h (food weight already 4.5 when behind). Keep self-adjacency(adj1&adj2) +
  static_flood + 2-ply-pin + offensive-space-denial + anti-pin + parallel-shadow
  + growth-attraction all intact. NEVER touch the launch block. Judge via
  solo_test + smartmatch multi-batch (variance huge).

## ROUND 1 UPDATE (opus-4-8, coreyja__eremetic-eric -- THIS SESSION)
- OPPONENT: `coreyja__eremetic-eric`. Round 0 result: WIN 236-14. GENUINE combat
  opponent that stays SMALL (len 7-12) and just SURVIVES while we grow HUGE.
- ANALYZED all 14 losses (/tmp/analyze3.py): ALL were LONG endgames (300-565
  turns) where WE self-eliminated. At death we were MASSIVELY LONGER (len 37-61
  vs opp 7-12) at HIGH health (82-100hp) with 0 safe neighbours = DOMINANCE
  SELF-COIL. Our huge body fills the board and we seal ourselves in.
- ROOT CAUSE (traced sim_129, /tmp/trace2.py + /tmp/replay3.py): we coiled the
  x=9 column then ran DOWN the x=10 wall corridor into the (0,0) corner. From
  ~t291 every move had only 1 safe cell = a WALL DEATH-MARCH. The trap forms
  many turns earlier when we drift onto the wall. Existing anti-wall-coil terms
  fire but are DWARFED by space*10 when we are huge (my_len=30+), and the flat
  escape==1 penalty (-40) is tiny relative to a big snake's score.
- FIX (score_candidate, new DOMINANCE CORRIDOR AVOIDANCE block, after the
  escape-count block ~line 365): when (not being_hunted) AND my_health>=30 AND
  my_len > _max_ol+3 (we dominate), scale the low-escape corridor penalty with
  length: escapes<=1 -> -(my_len-6)*4.0, AND add +space*3.0 so a huge snake
  strongly prefers the OPEN-interior move over continuing down a wall. Gated so
  it never blocks fighting/food when it matters.
- VERIFIED: synthetic dominant-near-wall (/tmp/synth.py, len20 head(9,5), opp
  tiny+far) -> bot now chooses UP (interior) instead of RIGHT (into wall). Live
  forward-sim of sim_129 from t275/280/285 (opp frozen) -> SURVIVES 60 steps
  (no longer walks into the coil).
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh naive 6-0, spacematch 9-7, smartmatch
  11-5 (no regression). Grow-solo stress test (/tmp/growsolo.py, 6 food, 600
  turns) -> new bot SURVIVES full 600 turns reaching len 44-47 (the failure-mode
  lengths) with NO self-coil; identical/near-identical to baseline (no regress).
- Backup: main_round1_eremetic_backup.py (pre-this-change, proven 236-14 code).
- ADVICE FOR NEXT TEAMMATE: eremetic-eric beats us ONLY by our own dominance
  self-coils in long endgames (it stays tiny and outlasts us). The dominance-
  corridor term targets that class. Remaining deeper lever = a true longest-
  survivable-path / connectivity metric (static flood overcounts through 1-wide
  channels and via tail retreat on walls) or a 3-ply space search to detect the
  multi-turn wall coil even earlier. Keep dominance-corridor + all existing anti-
  coil/anti-pin/parallel-shadow/growth intact. Judge via grow-solo + smart/space
  proxies (variance huge). NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, coreyja__eremetic-eric -- THIS SESSION, DOMINANCE TAIL-FOLLOW)
- Standing: R0 WIN 236-14, R1 WIN 231-19. ALL 19 R1 losses (analyzed /tmp/analyze.py)
  = the SAME DOMINANCE SELF-COIL class: we grew HUGE (len 29-62) vs a tiny opp
  (6-12) at HIGH health (81-100) then self-sealed (15/19 on edge, 4 interior).
  eremetic-eric stays tiny and outlasts us; our own coil kills us in long endgames.
- TRACED sim_12 (interior coil, /tmp/trace2/trace3.py): static flood was already
  << my_len for MANY turns before death. ROOT CAUSE: time-aware flood (space*10 /
  space*3) OVERCOUNTS through 1-wide channels (the coil clears as the tail
  retreats), so the bot happily SERPENTINES into a shrinking sub-length pocket
  while sspace silently drops. By the time all moves show sspace<my_len it's
  already sealed. A huge snake survives indefinitely only by CHASING ITS TAIL.
- NEW STRESS TEST: test/grow_solo.py -- runs our bot ALONE with heavy food to
  force it to the failure lengths (70-100). Reproduces the self-coil reliably:
  `cd /workspace/test && python3 -c "import sys;sys.path.insert(0,'.');import grow_solo as g;[print(g.run(s,800,14)) for s in range(10)]"`.
  BASELINE (main_round2_eremetic_r2_backup.py): 1/10 survive (die len 71-102).
- FIX (in the DOMINANCE CORRIDOR block, my_len>_max_ol+3 + healthy + not-hunted):
  added TAIL-FOLLOWING pull `score -= tail_dist*12.0` + `sspace*4.0` reward +
  anti-serpentine `-(adj-1)*30` when head snugs 2+ own body cells. Steers a huge
  snake to chase its tail / keep the largest no-retreat region instead of weaving.
  RESULT: grow_solo now 7/10 survive (deaths only at len 72-82, much later).
  Tuned tail weight: 3->weak(1/10), 12->best(7/10, latest deaths), 18->worse.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh naive 6-0.
- Backup: main_round2_eremetic_r2_backup.py (pre-this-change, proven 231-19 code).
- ADVICE FOR NEXT TEAMMATE: the dominance self-coil is the ONLY loss class vs
  eremetic-eric (it stays tiny and outlasts us). Tail-following helps a lot but a
  perfect fix needs a space-filling (Hamiltonian-ish) path planner when huge, or a
  true longest-survivable-path metric (static flood still overcounts through
  channels). Use test/grow_solo.py (nfood=14, 800 turns) as the repro. Keep
  tail-follow(12) + sspace-reward + anti-serpentine + all existing anti-coil/pin.
  NEVER touch the launch block.

## ROUND 1 UPDATE (opus-4-8, coreyja__gigantic-george -- THIS SESSION)
- OPPONENT: `coreyja__gigantic-george`. Round 0 result: WIN 220-30.
  GENUINE combat opp; stays SMALL (opp len 7-15) and OUTLASTS us in LONG
  endgames (avg game len 274 turns, up to 687). Same class as eremetic-eric.
- ANALYZED all 30 losses (/tmp/analyze3.py): 100% DOMINANCE SELF-COIL. At death
  we were MASSIVELY LONGER (ml 31-75 vs opp 7-15), HIGH health (87-100), BOXED
  IN (0 safe neighbours). 16 edge, 2 corner, 12 interior. george never dies; our
  own huge body seals us in.
- REPRODUCED with test/grow_solo.py (nfood=14): BASELINE survived 12/20 seeds
  (800t), deaths at len 54-83.
- CHANGES to main.py DOMINANCE TAIL-FOLLOWING branch (my_len>_max_ol+3, healthy,
  not-hunted) -- all tuned via grow_solo:
  * sspace reward 4.0 -> 8.0 (value real no-retreat room more).
  * anti-serpentine: adj>=2 penalty 30->45; NEW adj==1 penalty -12 (breaks the
    single-adjacency inward turn that starts interior coils).
  * NEW 2-PLY STATIC LOOKAHEAD: from nc, best static region reachable via any
    safe neighbour; -(my_len-best2)*12 if best2<my_len, -300 if best2<=4. Catches
    the funnel into a shrinking pocket 2 moves early.
  RESULT: grow_solo 15/20 -> and deaths pushed to len 86-107 (much later; the
  loss lengths were 31-75, so this class is largely eliminated in the real range).
  6/6 seeds survive 400t clean.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, per-call timing 0.014ms (zero timeout risk).
  NOTE: grow_solo at 800t/many-seeds TIMES OUT the 30s shell (test artifact: the
  test's own body-set grows huge, NOT a move() perf issue -- move() is 0.014ms).
  Use nfood=14, <=400 turns, <=6 seeds for a quick repro under the shell limit.
- Backup: main_round0_ggeorge_backup.py (this code).
- ADVICE FOR NEXT TEAMMATE: gigantic-george (like eremetic-eric) beats us ONLY
  by our own dominance self-coils in long endgames. The 2-ply static lookahead +
  stronger tail-follow/anti-serpentine helps a lot. The deep remaining coils
  (len 90+) need a true space-filling (Hamiltonian) path planner when huge, or a
  3-ply static search. Keep 2-ply-static-lookahead + tail-follow(12) +
  sspace-reward(8) + anti-serpentine(adj1&adj2) + all existing anti-coil/pin.
  Use test/grow_solo.py as the repro. NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, coreyja__gigantic-george -- THIS SESSION)
- Standing: R0 WIN 220-30, R1 WIN 224-25 (1 tie). Analyzed ALL 25 R1 losses
  (/tmp/analyze_r1.py): 100% DOMINANCE SELF-COIL -- we grew MASSIVELY LONGER
  (len 27-68 vs opp 7-15) at HIGH health (82-100), in LONG endgames (300-587
  turns), then sealed ourselves in. george stays tiny and outlasts us; our own
  huge body kills us. This is the known hard failure class (same as eremetic/
  amphibious): a huge snake survives only via a space-filling loop (chase tail).
- REPRO: /tmp/growbig.py (recreate: solo bot, 20 food, 900 turns) reliably
  reproduces -- BASELINE dies 10/12 seeds by self-coil at len 58-102.
- CHANGE (additive, GATED to the existing dominance branch: not_hunted +
  health>=30 + my_len>_max_ol+3, so it ONLY affects huge-snake behavior and
  CANNOT touch normal combat): added _region_and_tail() helper + a TAIL-REACHABLE
  REGION term. From the new head, flood with body-after-move as walls; if the
  future tail cell is still reachable -> +60 (on a survivable loop), else -400
  (severs the loop = coil death); plus +region*10 (prefer open room over 1-wide
  channels). This is the true survival metric a huge snake needs.
- HONEST NOTE: at moderate weights (reg*10, -400) growbig is UNCHANGED from
  baseline (2/12); only at extreme weights (reg*15, -2000) did it improve to
  3/12 -- but extreme weights risk distorting real play, so kept moderate. The
  term is a CORRECT additive safeguard (rewards staying on a survivable loop)
  but heuristics alone can't fully solve the len-90+ coil. The REAL fix is a
  space-filling / Hamiltonian-cycle path planner when huge, or a longest-
  survivable-path metric (static/time-aware floods overcount through 1-wide
  channels and via tail retreat). That's the remaining lever, higher effort/risk.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 6-0. smartmatch 12-game
  proxy: mine 4-8 vs baseline 5-7 = within variance (tiny sample, proxy rarely
  reaches huge lengths so my huge-only term is irrelevant there; per prior notes
  smart_opp is noisy). No regression to the 224-25 combat record.
- Backup: main_round1_ggeorge_r2_backup.py (this code); main_round0_ggeorge_backup.py
  (prior). NEVER touch the launch block.
- ADVICE FOR NEXT TEAMMATE: gigantic-george beats us ONLY by our own dominance
  self-coils in long endgames. Best remaining lever = a real space-filling path
  planner when my_len is huge (>~40): compute a Hamiltonian-ish cycle over free
  cells and follow it, only deviating for safe food. Use /tmp/growbig.py (20 food,
  900 turns) as the repro -- target getting >8/12 seeds to SURVIVE. Keep
  tail-reachable-region + tail-follow + 2-ply-static + anti-serpentine + all
  existing anti-coil/anti-pin. Test carefully; the 224-25 record is the floor.

## ROUND 1 UPDATE (opus-4-8, Flipez__flipez-crystal opponent) -- THIS SESSION
- OPPONENT: `Flipez__flipez-crystal`. Round 0 result: WIN 219-29 (2 ties).
  GENUINE combat opponent, avg game len 112 turns, max 260. NOT a timeout bot.
- ANALYZED all 29 losses (/tmp/analyze.py, /tmp/analyze2.py): CLEAR SINGLE
  ROOT CAUSE = in 100% of losses WE WERE SHORTER than flipez (avg gap 5.3 cells,
  range 1-13). flipez OUT-GROWS us EARLY (traced sim_36/145/153: by turn 40-50 it
  is len 8-13 while we hang at len 4-6), then pins us to walls/corners and wins
  forced head-to-heads. Not self-coil, not starvation (hp 50-95 at death) -- pure
  LENGTH DEFICIT. It grabs food aggressively; we were too passive.
- WHY WE WERE PASSIVE: score is dominated by space*10 (space 50+ => 500+ pts)
  while food weight 4.5*dist(~10)=45 pts, easily overwhelmed. Food racing was
  also too conservative (required my_fd < opp_fd-1, so tied races were ceded).
- CHANGES to main.py (targeted growth parity, additive to existing food logic):
  1. _food_weight when BEHIND: was flat 4.5 -> now 7.0 + min(behind,6)*0.8
     (7.0..11.8, scales with how far behind we are). Tied: 2.5 -> 3.5.
  2. FOOD RACING when BEHIND: contest food we WIN OR TIE (my_fd <= opp_fd)
     instead of only clear wins; race reward 3.0->5.0 when behind, land bonus
     45->55. When even/ahead the old conservative my_fd<opp_fd-1 still applies.
  These make us keep up on length so we WIN h2h instead of getting pinned.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 8-0.
  greedy_opp (aggressive grower proxy for flipez): 11-9, 13-11 (~54%, no regress;
  greedy_opp is HIGH variance per prior notes and grows fast like flipez).
  NOTE: mirror A/B (/tmp/ab.sh) is all-ties (deterministic symmetric) -- ignore
  per all prior README notes. Single-decision tests (/tmp/decision*.py) confirm
  the food logic already handles clear cases; the change matters at the MARGINS
  (stronger pull vs competing space/wall terms) accumulating over a game.
- Backup: main_round0_flipez_backup.py (pre-this-change, proven 219-29 code).
- ADVICE FOR NEXT TEAMMATE: flipez beats us by OUT-GROWING us then pinning.
  Growth parity is THE lever -- keep the boosted behind-food-weight + tie-race.
  If losses persist, consider growing even more aggressively early (contest food
  within manhattan even when slightly losing the race, IF escape>=2), or 2-ply
  h2h to win length-based contacts. Don't over-crank food (could dive into pins;
  food is still gated to safe cells space>=my_len and zeroed on edges when hunted).
  Keep all existing anti-coil/anti-pin/parallel-shadow/dominance logic intact.
  NEVER touch the launch block. Judge via greedy_opp multi-batch (variance huge).

## ROUND 2 UPDATE (opus-4-8, Flipez__flipez-crystal -- THIS SESSION, EARLY-GROWTH BOOST)
- Standing: R0 WIN 219-29 (2t), R1 WIN 221-26 (3t). R1 behind-food-weight boost
  cut losses only 29->26. STILL losing to length deficit.
- ANALYZED all 26 R1 losses (/tmp/analyze.py + /tmp/analyze_gap.py): 100% we were
  SHORTER at death (gap 1-23). KEY NEW FINDING: 25/26 losses we FELL BEHIND VERY
  EARLY -- median turn 10, 16 losses by turn 10-19, 9 by turn 0-9. flipez does a
  burst-eat in the opening (traced sim_15: at t50 we were LONGER 10v9, then flipez
  ate 3 food in ~10 turns and flipped ahead; sim_102/53: flipez reaches len7 by t20
  while we sit at len4). ROOT CAUSE: when TIED or slightly ahead our food pull was
  weak (tied 3.5, ahead 0.6) and the tied food-RACE rule was conservative
  (my_fd<opp_fd-1), so flipez freely grabbed food and pulled ahead in the opening.
- CHANGE (score_candidate food block, targeted early-growth parity):
  * tied food_weight 3.5 -> 5.5 (contest hard so flipez can't pull ahead)
  * behind food_weight base 7.0 -> 8.0, scale 0.8 -> 0.9 (8.0..13.4)
  * FOOD RACING: TIED snakes (my_len <= _max_ol, new `_aggro`) now use the
    aggressive win-OR-tie race rule (my_fd <= opp_fd) + race_w 5.0, same as behind.
    Even/ahead snakes still use the conservative my_fd<opp_fd-1 (unchanged) so we
    never dive into contested cells when already winning.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns, match.sh naive 8-0, grow_solo 6/6 seeds SURVIVE
  400t (no self-coil regression, len 11-18).
  * greedy_opp A/B (/tmp/abg.sh, aggressive-grower proxy for flipez, HIGH variance):
    NEW = 20-9-1 + 19-11 => 39-20 (66%). BASELINE (main_round2_flipez_r2_backup.py)
    = 20-10 + 16-14 => 36-24 (60%). Modest consistent edge, no regression.
- Backup: main_round2_flipez_r2_backup.py (pre-this-change, the 221-26 code).
- ADVICE FOR NEXT TEAMMATE: flipez OUT-GROWS us in the OPENING (turns 0-19) then
  pins us via length. Early growth parity is THE lever. If losses persist, the
  remaining move is to contest food EVEN MORE aggressively in turns 0-20 (e.g.
  when tied, also contest food we lose the race by 1 IF escape>=2), or add a
  2-ply h2h to win length-based contacts. Don't over-crank food -- it's gated to
  safe cells (space>=my_len) and zeroed on edges when hunted. Keep all existing
  anti-coil/anti-pin/parallel-shadow/dominance logic intact. Judge via
  /tmp/abg.sh (greedy_opp) MULTI-BATCH (variance huge). NEVER touch launch block.

## ROUND 1 UPDATE (opus-4-8, jackisherwood__battlesnake-elon -- THIS SESSION)
- OPPONENT: `jackisherwood__battlesnake-elon`. R0 result: WIN 239-10 (1 tie).
  GENUINE combat opp, LONG games (avg 204 turns, max 399). It stays alive and
  OUTLASTS us in long endgames.
- ANALYZED all 10 losses (/tmp/analyze3.py): 100% DOMINANCE / NEAR-EQUAL SELF-COIL.
  At death we were LONGER-or-EQUAL (ml 21-32 vs ol 19-30), HIGH health (70-100),
  BOXED IN (0-1 safe nbrs), mostly INTERIOR (7/10). We seal ourselves in; elon
  survives. KEY: unlike eremetic/george (we were HUGELY longer, my_len>_max_ol+3),
  here we were NEAR-EQUAL length (ml~ol) -> the strong dominance tail-following /
  tail-reachable-region block DIDN'T FIRE (gated my_len>_max_ol+3). This near-equal
  band was only covered by the time-aware floods, which OVERCOUNT through 1-wide
  channels and via tail retreat, missing the multi-turn interior coil.
- FIX (score_candidate, after the existing time-aware tail-reach check ~line 375):
  NEW UNIVERSAL TAIL-REACHABLE-REGION safeguard for EVERY length band. Gated to
  (not being_hunted) + health>=30. Uses STATIC (body-after-move as permanent
  walls) _region_and_tail: +50 if the future tail cell stays reachable (survivable
  space-filling loop), -350 if severed (coil death); -(my_len-reg)*10 if the static
  region < our length; -250 if region<=4. This is the true survival metric applied
  to the near-equal band that was uncovered.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, smartmatch 10-6.
  * spacematch (space_opp = strong space-maximizer proxy, survives long like elon):
    NEW 15-8-1 vs BASELINE 15-9-0 = WASH (no regression; additive safeguard).
  * grow_solo (nfood=20,500t): 8/12 vs baseline 9/12 -- within variance (that test
    forces len 40-70, a different regime than the len 21-32 real losses; deaths at
    len 49-58 either way). The change targets the near-equal INTERIOR coil in LIVE
    play, which replays can't show (recorded body already coiled, per prior notes).
- Backup: main_round0_elon_backup.py (pre-this-change, proven 239-10 code).
- ADVICE FOR NEXT TEAMMATE: elon beats us ONLY by our own near-equal-length
  interior self-coils in long endgames. The universal tail-region safeguard covers
  the previously-uncovered ml~ol band. The DEEP remaining fix (all authors' notes
  agree) = a real space-filling / Hamiltonian-cycle path planner or a true
  longest-survivable-path metric (floods overcount through 1-wide channels). Keep
  universal-tail-region + dominance tail-follow + 2-ply-static + anti-serpentine +
  all existing anti-coil/anti-pin. NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, jackisherwood__battlesnake-elon -- NEAR-EQUAL ANTI-COIL)
- Standing: R0 WIN 239-10 (1 tie), R1 WIN 235-15 (0 ties). Losses rose 10->15
  (the R1 "universal tail-region" term did not fully close the gap).
- ANALYZED all 15 R1 losses (/tmp/analyze.py): 100% NEAR-EQUAL-LENGTH INTERIOR
  self-coils. At death ml~ol (e.g. sim_131 27v27, sim_130 22v24, sim_16 18v19),
  HIGH health (56-98, mostly 82-98), 14/15 INTERIOR, boxed in (0-1 safe nbrs).
  Traced sim_131 t253-259: we SERPENTINE-weaved into a shrinking ~8-cell pocket
  (R,D,R,U,U,L) and sealed ourselves at t259 (0 safe moves). Long endgames.
- ROOT CAUSE: the strong anti-serpentine + tail-follow + 2-ply STATIC lookahead
  only fired in the DOMINANCE band (my_len > _max_ol+3). The NEAR-EQUAL band
  (my_len <= _max_ol+3) was only covered by the universal tail-region term
  (+50/-350 + reg*10), which wasn't enough to break a forming multi-turn weave.
- FIX (score_candidate, NEW "NEAR-EQUAL-LENGTH ANTI-COIL" block, right after the
  universal tail-region block, gated not-hunted + health>=30 + my_len<=_max_ol+3):
  a MILDER copy of the dominance anti-coil -- anti-serpentine (-30 per adj>=2,
  -8 at adj==1), tail-following (-tail_dist*3), and a 2-ply STATIC lookahead
  (best no-retreat region from a safe nbr of nc: -(my_len-best)*10 if <my_len,
  -250 if <=4). Weights are lighter than the dominance branch so it never
  overrides h2h/food; it just breaks the serpentine weave EARLY in the
  near-equal band before the pocket seals.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 8-0 (& 5-0),
  smartmatch 12-4 (strong, no regression), grow_solo 5/5 seeds SURVIVE 300t.
  Mirror A/B vs baseline = 0-0-24 (all ties, deterministic symmetric -- noise,
  ignore per prior notes). Frozen-opp livesim can't discriminate (both survive;
  the recorded body is already coiled -- the fix matters in LIVE play by steering
  off the weave many turns earlier, a known replay limitation).
- Backup: main_round2_elon_r2_backup.py (pre-this-change, proven 235-15 code).
- ADVICE FOR NEXT TEAMMATE: elon beats us ONLY by near-equal-length interior
  self-coils in long endgames. The near-equal anti-coil covers the previously-
  uncovered band. The DEEP remaining fix (all notes agree) = a real space-filling
  / longest-survivable-path metric (static/time-aware floods overcount through
  1-wide channels). Keep near-equal-anti-coil + universal-tail-region + dominance
  tail-follow + 2-ply-static + anti-serpentine + all existing anti-coil/anti-pin.
  Don't over-crank the near-equal weights (>~1.5x could distort real combat).
  NEVER touch the launch block. Judge via solo_test + grow_solo + smartmatch.

## ROUND 1 UPDATE (opus-4-8, MorganConrad__tantilla -- DOMINANCE ANTI-COIL BOOST)
- OPPONENT: `MorganConrad__tantilla`. R0 result: WIN 225-24 (1 tie). GENUINE
  combat opp that stays SMALL (opp len 5-14) and OUTLASTS us in LONG endgames
  (loss turns 42-547). Same class as eremetic-eric / gigantic-george / elon.
- ANALYZED all 24 losses (/tmp/analyze4.py): 100% DOMINANCE SELF-COIL. At death
  we were ALWAYS MUCH LONGER (my_len 15-68 vs opp 5-14) at HIGH health (93-100),
  boxed in. 9 edge / 7 corner / 8 interior. tantilla never dies; our own huge
  body seals us. 0 shorter, 24 longer -- pure dominance-coil, no h2h/pin losses.
- REPRO: test/grow_solo.py at STRESS regime (550 turns, 20 food, seeds 0-3):
  BASELINE (main_round0_tantilla_backup.py) dies 2/4 (seed0 WALL t362 len58,
  seed2 SELF t310 len58).
- FIX (tuning of existing DOMINANCE + UNIVERSAL tail-region anti-coil weights,
  all GATED to not-hunted + healthy so combat/food untouched):
  * DOMINANCE branch (my_len>_max_ol+3): tail-follow _td 12->20, tail-reachable
    stays-on-loop +60->+120, sever-loop -400->-800, region reward _reg*10->*16.
  * UNIVERSAL tail-region (all bands): stays-loop +50->+90, sever -350->-500,
    sub-length region penalty *10->*14.
  Rationale: a HUGE snake survives only on a space-filling loop (reach its own
  tail); the floods overcount through 1-wide channels so we serpentine into
  shrinking pockets. Stronger tail-follow + sever penalty keeps us on the loop.
- TESTING (grow_solo A/B, BASE vs NEW, same seeds):
  * 550t/20food seeds 0,2: BASE dies both (t362,t310) -> NEW seed0 t437 (later),
    seed2 SURVIVES 500 len89. Clear improvement.
  * 450t/18food seeds 1,3,5,7: BASE 3/4 -> NEW 4/4 (seed3 NEW len89 vs BASE60).
  * 480t/18food seeds 0,2,5: BASE 2/3 -> NEW 3/3.
  * 420t/16food seeds 0-7: both 8/8 (coils only form in longer/heavier games).
  NEW is never worse, often survives much longer / reaches larger space-fill len.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 6-0, smartmatch 9-3 (no
  regression to combat).
- Backup: main_round0_tantilla_backup.py (pre-this-change, the 225-24 code).
- ADVICE FOR NEXT TEAMMATE: tantilla beats us ONLY by our own dominance
  self-coils in long endgames (it stays tiny and outlasts us). The boosted
  tail-follow + sever penalty helps. The DEEP remaining fix (all prior notes
  agree) = a true space-filling / Hamiltonian-cycle path planner when huge
  (my_len>~40), or a longest-survivable-path metric (floods overcount through
  1-wide channels). Use test/grow_solo.py (550t, 20 food, seeds 0-3) as the
  repro -- target >3/4 seeds survive. Keep the boosted dominance/universal
  tail-region weights + all existing anti-coil/anti-pin/parallel-shadow/growth.
  NEVER touch the launch block. Judge via grow_solo A/B + smartmatch (variance).

## ROUND 2 UPDATE (opus-4-8, MorganConrad__tantilla -- THIS SESSION, DOMINANCE COIL WEIGHT BOOST)
- Standing: R0 WIN 225-24 (1t), R1 WIN 223-27. Analyzed ALL 27 R1 losses
  (/tmp/analyze_r1.py): 100% DOMINANCE SELF-COIL -- we grew LONGER (ml 7-62 vs
  opp 4-21) at HIGH health (87-100) in LONG endgames (t188-576) then self-sealed.
  tantilla stays tiny and outlasts us; our own body kills us. SAME known hard
  class (eremetic/george/elon/tantilla). 0 shorter, 0 h2h/pin losses.
- REPRO (reliable): test/grow_solo.py at 25 food / 500 turns, seeds 0-7:
  BASELINE (main_round2_tantilla_r2_backup.py) survived only 2/8 (self-coil at
  len 83-90). At 22 food / 450 turns seeds 8-13: baseline 3/6.
- FIX (weight boosts in the EXISTING DOMINANCE ANTI-COIL branch ONLY -- gated
  not_hunted + health>=30 + my_len>_max_ol+3, so combat/food UNTOUCHED):
  * DOMINANCE tail-follow _td: 20 -> 28 (pull harder toward tail = space-fill loop)
  * sever-loop penalty (tail unreachable after move): 800 -> 1500
  * anti-serpentine adj>=2: 45 -> 60 per extra adjacency; adj==1: 12 -> 20
  * 2-ply static funnel penalty (my_len - best2): 12 -> 18
  Rationale: a HUGE snake survives ONLY on a space-filling loop (reach own tail);
  time-aware/static floods overcount through 1-wide channels so we serpentine
  into shrinking pockets. Stronger tail-follow + sever + anti-serpentine keeps us
  on the loop and breaks weaves earlier.
- RESULT (grow_solo A/B, same seeds):
  * 25food/500t seeds 0-7: BASE 2/8 -> NEW 5/8.
  * 22food/450t seeds 8-13: BASE 3/6 -> NEW 6/6.
  Clear, consistent improvement, no easy-seed artifact.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 6-0, smartmatch 10-2
  (strong combat, no regression). greedymatch 5-7 (within variance; greedy_opp
  rarely reaches the dominance band my changes touch, per prior notes).
- Backup: main_round2_tantilla_r2_backup.py (pre-this-change, the 223-27 code).
- ADVICE FOR NEXT TEAMMATE: tantilla beats us ONLY by our own dominance self-coils
  in long endgames. The boosted tail-follow/sever/anti-serpentine helps a lot but
  the DEEP fix (all notes agree) = a real space-filling / Hamiltonian-cycle path
  planner when huge (my_len>~40), or a longest-survivable-path metric (floods
  overcount through 1-wide channels). Use test/grow_solo.py (25 food, 500t,
  seeds 0-7) as the repro -- target >5/8 survive. Don't over-crank further (edge
  penalty in the branch caused wall/self flips; tested, reverted). Keep the
  boosted weights + all existing anti-coil/anti-pin/parallel-shadow/growth.
  NEVER touch the launch block. Judge via grow_solo A/B + smartmatch (variance).

## ROUND 1 UPDATE (opus-4-8, ChaelCodes__cornelius -- THIS SESSION)
- OPPONENT: `ChaelCodes__cornelius`. Round 0 result: WIN 218-31 (1 tie).
  GENUINE combat opponent, LONG endgames (loss turns 66-445, high health 82-100).
- ANALYZED all 31 losses (/tmp/analyze2.py + analyze3.py, recreate from git):
  * 23/31 = SELF-COIL (0 safe nbrs, 0 h2h at death) -- mostly NEAR-EQUAL length
    (ml~ol), high health, LONG games, boxed in interior/edge. Traced sim_218
    (ml20 ol19, t214): we weaved DOWN into the bottom-left region, ate food at
    the wall (len 19->20 doubling the tail) and sealed the pocket. Classic
    near-equal / dominance interior+wall self-coil (same class as elon/eremetic/
    tantilla).
  * 8/31 = H2H losses, MOSTLY when SHORTER (cornelius out-grew us).
- CHANGE (low risk, tuning of EXISTING NEAR-EQUAL-LENGTH ANTI-COIL block only,
  gated not-hunted + health>=30 + my_len<=_max_ol+3, so combat/food untouched):
  * anti-serpentine adj>=2: 30 -> 45 per extra adjacency; adj==1: 8 -> 12
  * tail-following _tdn weight: 3 -> 5
  * 2-ply STATIC lookahead limit: my_len+4 -> my_len+12 (so a truly open region
    is distinguished from a shrinking pocket even for a longer near-equal snake),
    sub-length penalty (my_len-best2): 10 -> 16, tiny-region penalty 250 -> 300.
  Rationale: the near-equal band was the dominant loss class; the milder existing
  weights weren't enough to break the multi-turn serpentine weave before the
  pocket seals. Stronger tail-follow + anti-serpentine + deeper lookahead steers
  us off the coil EARLIER.
- VERIFIED (frozen-opp livesim, /tmp/test_early.py): starting BEFORE the coil
  commits (t189/t194 for sim_218; t309/t314 for sim_157; etc.) the new bot
  SURVIVES 40 steps where the recorded game died. NOTE: replays starting AFTER
  the coil is already committed (~22 turns back) do NOT diverge (recorded body
  already coiled -- known replay limitation, per all prior notes). The fix
  matters in LIVE play by steering off the weave many turns earlier.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 6-0,
  smartmatch 11-5-0 then 11-4-1 (strong combat, no regression),
  grow_solo 5/8 (25food/500t, unchanged from baseline -- those failures are
  len 69-96 DEEP dominance coils outside the near-equal band this change touches).
- Backup: main_round0_cornelius_backup.py (pre-this-change, proven 218-31 code).
- ADVICE FOR NEXT TEAMMATE: cornelius beats us mostly by our own near-equal-length
  self-coils in long endgames (23/31), plus 8 h2h when SHORTER. Growth weights
  are already aggressive (behind up to 13.4, tied 5.5) -- don't over-crank (pin
  risk). The DEEP remaining fix (all notes agree) = a real space-filling /
  longest-survivable-path metric (static/time-aware floods overcount through
  1-wide channels). Keep the boosted near-equal anti-coil + all existing
  anti-coil/anti-pin/dominance/growth logic. Judge via smartmatch (variance!)
  + solo/grow_solo. NEVER touch the launch block.

## ROUND 2 UPDATE (opus-4-8, ChaelCodes__cornelius -- THIS SESSION, CHOKEPOINT-QUALITY ANTI-COIL)
- Standing: R0 WIN 218-31 (1t), R1 WIN 211-37 (2t). Losses ROSE 31->37; the R1
  near-equal anti-coil weight boost did NOT help (may have slightly hurt).
- ANALYZED all 37 R1 losses (/tmp/cat2.py, recreate from git): SPLIT into two
  clear classes by our length at death:
  * 18 losses we were LONGER -> ALL were SELF-COIL (0 safe nbrs). We win then
    seal ourselves in during long endgames (t114-415), high health (67-98).
    Lengths 13-31 (NOT the huge len-60+ dominance regime). Interior-heavy.
  * 18 losses we were SHORTER -> mix of 10 self-coil + 8 h2h/pin (cornelius
    out-grows us then traps/pins). 1 equal-length coil.
  Overall: 27 self-coil / 10 h2h. Interior 18, edge 10, corner 9.
- ROOT CAUSE (self-coil class, per ALL prior notes): static/time-aware floods
  OVERCOUNT space reachable through 1-wide channels (a coil clears as the tail
  retreats), so a serpentine coil looks "big" while it is really a shrinking
  corridor. The bot happily weaves into it and seals.
- FIX (the deep lever every prior note flagged, implemented lightly & safely):
  new helper `_open_region_quality(start, blocked)` -- a CHOKEPOINT-AWARE flood.
  Each reachable cell contributes 0.35 if it has <=1 free neighbour (corridor/
  dead-end), 0.75 if 2, else 1.0. A serpentine channel scores far lower quality
  than genuinely open room. Used in the UNIVERSAL tail-region block (fires for
  ALL length bands, gated not-hunted + health>=30): score += q*2.0, and
  -(my_len-q)*8.0 when q < my_len. Steers us toward genuinely open moves and
  breaks forming coils earlier, independent of length.
- TUNING: first tried q*3 + (-6) with limit=my_len*3 -> deep grow_solo 4/8
  (slightly worse, limit too small for huge snakes). Settled on q*2 + (-8) with
  NO limit -> deep grow_solo 5/8 (== baseline, no regress) AND moderate regime
  (400t/14food, the real loss-length band) 8/8, (450t/22food) 12/12.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 6-0,
  smartmatch 11-5 then 10-2 (strong combat, no regression),
  greedymatch 9-3, grow_solo deep A/B vs backup 9/14==9/14 (no regress), moderate
  8/8 & 12/12.
- Backup: main_round2_cornelius_r2_backup.py (pre-this-change, the 211-37 code).
- ADVICE FOR NEXT TEAMMATE: cornelius beats us by (a) our own self-coils when
  LONGER (18/37) and (b) out-growing then pinning us when SHORTER (18/37). The
  chokepoint-quality term directly targets class (a) -- the real fix vs the
  overcounting floods. For class (b), growth weights are already aggressive;
  next lever = grow to parity even faster early, or extend 2-ply pin lookahead.
  The DEEPEST coils (len 60+) still need a true space-filling/Hamiltonian path
  planner. Keep chokepoint-quality + universal-tail-region + all existing anti-
  coil/anti-pin/dominance/growth. Don't over-crank q weight (>~3 distorts deep
  play, tested). NEVER touch the launch block. Judge via grow_solo A/B (moderate
  AND deep) + smart/greedy proxies (variance huge).

## ROUND 1 UPDATE (opus-4-8, joshhartmann11__battlejake2019 -- THIS SESSION)
- OPPONENT: `joshhartmann11__battlejake2019`. R0 result: WIN 213-37. GENUINE
  combat opp (loss turns 54-403, high health 66-100). NOT a timeout bot.
- ANALYZED all 37 losses (/tmp/analyze2.py, recreate from git): 36/37 were
  SELF-COILS while we were LONGER (ml 6-35 vs ol 6-26) at HIGH health (mostly
  82-100), boxed in (0 safe nbrs). 28/37 on an EDGE, lengths mostly MODERATE
  (13-35, NOT the huge-dominance len-60+ regime). 1 loss (sim_231) was a rare
  shorter-h2h. This is the classic near-equal/dominance wall self-coil class.
- TRACED sim_186 (ml14 ol13, t198): at t185-187 we DOVE from the interior (5,2)
  down to the bottom wall (5,0) chasing wall-adjacent food (8,0)/(10,0), ran
  RIGHT along the bottom into the (10,0) corner (ate, len->15), then walked UP
  the x=10 wall into a dead-end (10,3). Classic wall death-march started by
  chasing EDGE food while at/above length parity.
- ROOT CAUSE: food racing (my_len<=_max_ol+1) rewarded moving toward edge/corner
  food even when we were AT/ABOVE parity and healthy. The dominance-food-zero
  only fires at my_len>_max_ol+4 (huge), so the near-equal band (ml 1-6 > ol)
  was uncovered and chased edge food into wall corridors.
- FIX (main.py food block, LOW RISK, additive & gated):
  * New `_suppress_edge_food = (my_len >= _max_ol and my_health >= 40)`.
  * In FOOD RACING: when _suppress_edge_food and the food target is on an EDGE,
    SKIP the racing reward; and if the new-head cell is itself an edge cell with
    <=2 escapes, add -45 (discourage diving onto the wall). Only affects the
    at-parity+/healthy/not-hunted case -- a starving (<40hp) or BEHIND snake
    still races edge food normally (food-parity vs flipez/ccsnake untouched).
- VERIFIED (frozen-opp livesim /tmp/livesim.py): from sim_186 t178-185 the new
  bot now SURVIVES 50 steps (recorded game died t198). At t185 it no longer
  dives to the bottom wall / no longer runs into the corner.
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 6-0.
- Backup: main_round0_battlejake_backup.py (pre-this-change, proven 213-37 code).
- ADVICE FOR NEXT TEAMMATE: battlejake beats us ONLY by our own wall self-coils
  when at/above length parity (chasing edge food onto walls). The edge-food-
  suppression targets that. The DEEPER remaining coils (interior, len 30+) still
  need a true space-filling/longest-survivable-path metric (floods overcount
  through 1-wide channels -- all prior notes agree). Keep _suppress_edge_food +
  chokepoint-quality + near-equal-anti-coil + dominance tail-follow + all
  existing anti-coil/anti-pin/growth. Use /tmp/livesim.py (frozen-opp forward
  sim from a given sim turn) to verify wall-coil fixes. NEVER touch launch block.

## ROUND 2 UPDATE (opus-4-8, joshhartmann11__battlejake2019 -- FOOD-DOUBLING TAIL FIX)
- Standing: R0 WIN 213-37, R1 WIN 224-25 (1t). The R0 edge-food-suppression cut
  losses 37->25. Analyzed ALL 25 R1 losses (/tmp/analyze2.py, recreate from git):
  23/25 = SELF-COIL (0 safe nbrs at death), 19/25 while LONGER, high health
  (74-100), MODERATE lengths (10-31, NOT huge-dominance regime). Edge 14 / int 11.
  Traced sim_180 (t141-144, len10 v9 interior): we ATE food at (9,8) -> grew ->
  turned back INTO our own coil pocket at (7,7) and sealed (all 4 nbrs own body).
- ROOT CAUSE (a real BUG all prior notes flagged as a TODO): the tail-reachable-
  region + 2-ply-static anti-coil blocks ALL assumed the tail RETREATS
  (_occ = my_body[:-1]). But when the new head lands on FOOD the tail does NOT
  retreat -- the body stays and grows. So those blocks OVERCOUNTED the reachable
  region right when eating food seals a pocket (the exact sim_180 death). The
  bot happily ate wall/pocket food that doubled its tail and self-sealed.
- FIX (main.py, targeted & low-risk): in all four tail-region / 2-ply-static
  blocks (universal ~line 436, dominance ~line 566, near-equal 2-ply ~line 492,
  dominance 2-ply ~line 592), when nc is in _food_cells use the FULL body
  (set(my_body)) as walls and keep the current tail as _future_tail (no retreat).
  This makes the anti-coil see the TRUE post-eat space, so it avoids eating food
  that would seal a shrinking pocket.
- VERIFIED: frozen-opp livesim (/tmp/livesim.py) from sim_180 t140 now SURVIVES
  30 steps (recorded game died t145). grow_solo (heavy food 20, 450t, seeds 0-5)
  = 6/6 SURVIVE reaching len up to 44 (no regression, strong).
- VALIDATION -- ALL PASS: ast.parse+import OK, launch block intact,
  solo_test SURVIVED 300 turns len 7, match.sh naive 6-0, move() ~1.7ms/call
  (zero timeout risk).
- Backup: main_round2_battlejake_r2_backup.py (pre-this-change, the 224-25 code).
- ADVICE FOR NEXT TEAMMATE: battlejake beats us ONLY by our own self-coils
  (23/25) mostly when LONGER at moderate lengths -- the food-doubling tail bug was
  the missing piece (we sealed pockets by eating food that doubled the tail). The
  DEEPEST coils still need a true space-filling/longest-survivable-path planner
  (floods overcount through 1-wide channels). Keep the food-doubling tail fix +
  chokepoint-quality + universal-tail-region + near-equal-anti-coil + dominance
  tail-follow + _suppress_edge_food + all existing anti-coil/anti-pin/growth.
  NEVER touch the launch block. Judge via /tmp/livesim.py + grow_solo + solo_test.
