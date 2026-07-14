# Agent Notes (opus-4-8 BattleSnake)

## !!! CRITICAL LESSON FROM ROUND 1 (READ THIS) !!!
Round 1 scored **0 vs 250 (LOSS)** even though local sims showed wins.
Reason: `main.py` was MISSING the `if __name__ == "__main__"` block that starts
the flask server. Grader flags this INVALID:
  "main.py must keep its `if __name__ == \"__main__\"` block that starts the
   server, or the bot fails to launch."
=> Local sims (test/match.sh) DON'T catch this (they start server manually).
   ALWAYS verify main.py ends with:
     if __name__ == "__main__":
         from server import run_server
         run_server({"info": info, "start": start, "move": move, "end": end})

## RESULTS SO FAR
- Round 1: LOSS 0-250 (missing launch block bug, now fixed).
- Round 2: WIN 250-0 (250/250 sims won). Launch block restored.
- Round 3: kept winning strategy, added a small "hunt when clearly longer"
  tiebreaker. Local match.sh 30 => me=30 opp=0 tie=0. Games end in ~2-7 turns
  because opponent self-destructs (no collision avoidance).

## VALIDATION CHECKLIST before submitting (do EVERY round)
1. `tail -4 main.py` shows the `if __name__ == "__main__"` block.
2. `python -c "import main"` succeeds (no import errors).
3. `python -c "import ast; ast.parse(open('main.py').read())"` parses.
4. `bash test/match.sh 20` wins comfortably.

## Opponent
`pambrose__pambrose-kotlin` = naive SimpleSnake: chases FARTHEST food,
x-dominates-y, NO collision avoidance -> self-destructs almost immediately.
Copy in test/opponent.py. Our bot just needs to survive & it wins fast.

## Strategy in main.py (survival-first)
- Full collision avoidance (walls, bodies, self); tails free unless just ate.
- Head-to-head: avoid cells enemy head could enter unless strictly longer.
- Flood-fill space eval to avoid self-trapping (penalize space < my_len).
- Food: chase nearest when hungry (<60) or not clearly longer.
- NEW (r3): when clearly longer than every opponent and not chasing food,
  keep space priority but move toward enemy head to force winning h2h.
- try/except returns "up" fallback.

## Test harness (test/)
- test/opponent.py = naive opponent strategy.
- test/match.sh N = N local games (me :8000 vs opp :8001) via game/battlesnake.
  Prints "RESULTS: me=X opp=Y tie=Z".
- main_original_backup.py = original naive main.py (HAS launch block, ref).
- /tmp is ephemeral; backups there won't persist across rounds.

## Log analysis one-liner (win/loss over sim logs)
python3 -c "import json,glob; w=l=t=0
[ (lambda d: (globals().update()) ) for _ in []]"  # see below
# Simpler: each /logs/rounds/N/sim_*.jsonl last line has winnerName / isDraw.
# Count with: for f in sims: last=json.loads(open(f).readlines()[-1]);
#   isDraw -> tie; winnerName=='opus-4-8' -> win; else loss.

## Ideas for future teammates
- Opponent is static/naive; bot dominates. Low risk. DON'T touch launch block.
- If opponent ever changes to be smarter, current flood-fill + h2h + hunt is a
  reasonable base. Could add 2-ply lookahead if needed, but keep it simple &
  never regress the survival logic.
