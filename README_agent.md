# Agent Notes (opus-4-8 BattleSnake)

## !!! CRITICAL LESSON FROM ROUND 1 (READ THIS) !!!
Round 1 scored **0 vs 250 (LOSS)** even though local sims showed 40-0 wins.
Reason: `main.py` was MISSING the `if __name__ == "__main__"` block that starts
the flask server. The grader flags this as INVALID:
  "main.py must keep its `if __name__ == \"__main__\"` block that starts the
   server, or the bot fails to launch."
=> Local sims (test/match.sh) DON'T catch this because they start the server
   manually via `run_server(...)`. ALWAYS verify main.py ends with:
     if __name__ == "__main__":
         from server import run_server
         run_server({"info": info, "start": start, "move": move, "end": end})

## Round 2 fix (current)
Re-added the launch block to main.py. Verified:
- `python -c "import main"` OK, handlers present.
- `python -c "import ast; ast.parse(open('main.py').read())"` OK.
- `bash test/match.sh 20` => me=20 opp=0 tie=0.
The strategy code (survival-first + flood-fill + h2h) is unchanged and strong.

## VALIDATION CHECKLIST before submitting (do EVERY round)
1. `tail -6 main.py` shows the `if __name__ == "__main__"` block.
2. `python -c "import main"` succeeds (no import errors).
3. `bash test/match.sh 20` wins comfortably.

## Opponent
`pambrose__pambrose-kotlin` = naive SimpleSnake: chases FARTHEST food,
x-dominates-y, NO collision avoidance -> self-destructs. Copy in test/opponent.py.

## Strategy in main.py (survival-first)
- Full collision avoidance (walls, bodies, self); tails treated free unless ate.
- Head-to-head: avoid cells enemy head could enter unless strictly longer.
- Flood-fill space eval to avoid self-trapping.
- Food: chase nearest when hungry (<60) or not clearly longer; else favor space+center.
- try/except returns "up" fallback.

## Test harness (test/)
- test/opponent.py = naive opponent strategy.
- test/match.sh N = N local games (me :8000 vs opp :8001) via game/battlesnake.
  Prints "RESULTS: me=X opp=Y tie=Z". Winner string: "NAME was the winner."
- main_original_backup.py = original naive main.py (HAS the launch block, ref).

## Ideas for future teammates
- Opponent is static/naive; current bot dominates. Low risk.
- DON'T remove the launch block. Verify it every time (see checklist).
