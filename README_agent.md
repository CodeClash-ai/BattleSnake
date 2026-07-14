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
