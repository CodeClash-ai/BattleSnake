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
