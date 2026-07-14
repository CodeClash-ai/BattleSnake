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
