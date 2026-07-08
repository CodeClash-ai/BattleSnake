# Agent Notes — CodeClash BattleSnake

## ⚠️ CORRECTION vs old notes (READ THIS)
Older notes in git history claimed the opponent was "pambrose-kotlin SimpleSnake".
That is WRONG for THIS match. Verified from /logs/rounds/0/:

- **Actual opponent name: `Nettogrof__nessegrev-julia`**
- The opponent **TIMES OUT every move** (latency reported ~500–505 ms, timeout is
  500 ms). When a snake times out, the engine repeats its previous move
  direction. So the opponent effectively **walks in a straight line** from its
  spawn and **dies by hitting a wall** in ~3–11 turns.
- Confirmed: round 0 we won **38/38 games**, avg game length ~6 turns,
  score 38 vs 0. Every opponent death was a wall collision after moving straight.

## Current status: WINNING 100%
`main.py` is a robust survival bot (wall/body/tail-aware obstacles, per-move
flood-fill for space, tail-reachability safety, obstacle-aware BFS food distance,
health-scaled food urgency, H2H avoidance/seeking, mild aggression when longer).
- Move latency ~0.3 ms (timeout 500 ms) — we NEVER time out. This is the crucial
  edge: the opponent times out and dies; we don't.
- Verified this round: main.py vs straight-line opponent stand-in
  (`opp_straight.py`) = **50-0 as A, 30-0 as B**. Never loses/draws.

## Strategy decision this round
Kept main.py unchanged. We already win every game against an opponent that
self-destructs by turn ~10. The ONLY way to lose is if WE die first, which the
survival bot + fast latency prevents. Changing a 100%-winning bot only risks
regression.

## Testing tools (IMPORTANT: sandbox quirks)
- Background server processes do NOT persist between separate bash commands
  (each command is a fresh subshell). You must start servers AND run the CLI
  **within a single bash command / script**.
- `opp_straight.py` = stand-in for the real opponent (always moves "up", i.e.
  straight line into a wall). NOTE: any test bot MUST include the
  `if __name__ == "__main__": from server import run_server; run_server(...)`
  bootstrap or its flask server won't start (port refused).
- Working test script (self-contained, one command):
  `bash /tmp/rm2.sh <botA.py> <botB.py> <N>`  (recreate below if missing)
  ```bash
  cat > /tmp/rm2.sh <<'SH'
  #!/bin/bash
  BOTA=$1; BOTB=$2; N=$3; CLI=/workspace/battlesnake_cli
  mkdir -p /tmp/botA /tmp/botB
  cp /workspace/server.py /tmp/botA/; cp /workspace/server.py /tmp/botB/
  cp "/workspace/$BOTA" /tmp/botA/main.py; cp "/workspace/$BOTB" /tmp/botB/main.py
  PORT=8001 python3 /tmp/botA/main.py >/tmp/botA.log 2>&1 & PA=$!
  PORT=8002 python3 /tmp/botB/main.py >/tmp/botB.log 2>&1 & PB=$!
  sleep 2; a=0;b=0;d=0
  for i in $(seq 1 $N); do
    o=$($CLI play -W 11 -H 11 -n A -u http://localhost:8001 -n B -u http://localhost:8002 -r $i 2>&1 | tail -1)
    if echo "$o"|grep -q "A was the winner"; then a=$((a+1));
    elif echo "$o"|grep -q "B was the winner"; then b=$((b+1)); else d=$((d+1)); fi
  done
  echo "A=$a B=$b draw=$d"; kill $PA $PB 2>/dev/null
  SH
  ```
- Build CLI if missing: `cd game && go build -o /workspace/battlesnake_cli ./cli/battlesnake`
- NOTE: the shipped `run_match.sh` gives false "draw" results if the test
  opponent lacks the run_server bootstrap. Use /tmp/rm2.sh and check its logs.

## Analysis tool
- `/tmp/analyze.py` and `/tmp/deaths.py` parse /logs/rounds/0/*.jsonl to compute
  win counts, game lengths, opponent latency, and per-turn head positions.
  (Recreate from git history if lost; they showed opp latency ~502ms & straight
  line death.)

## Backups
- main_backup_v0.py = original SimpleSnake port (baseline).
- main_backup_v1/v2/v3.py = earlier iterations of the survival bot.

## TODO for next teammate (only if opponent CHANGES)
- If the opponent stops timing out / starts surviving & maneuvering, add 2-ply
  minimax on contested cells. H2H / space / aggression logic is already sound.
- Always test BOTH position orders (A and B) before submitting — there is a
  player-A position bias in self-play.
- Do NOT regress: `bash /tmp/rm2.sh main.py opp_straight.py 50` must stay 50-0.

## Round 2 update (opus-4-8_r2)
- Verified round 1 result: **opus-4-8 34, opponent 0** (from /logs/rounds/1/results.json).
  Parsed 250 sim files: opus wins 34, opp wins 0, draws 0 (rest had no final winner line).
- Opponent STILL `Nettogrof__nessegrev-julia`, still times out & dies (avg game ~2 turns).
- Regression tests PASS: `main.py` vs `opp_straight.py` = 30-0 as A AND 0-30 (we're B) -> we win 30/30 both orders.
- Worst-case latency test (full 11x11 board, two 30-long snakes): **0.017 ms** avg (timeout 500ms).
- `move()` wraps all logic in try/except with fast `_safe_fallback`. Cannot crash into a timeout.
- DECISION: kept main.py unchanged. 100% win rate + can't-lose latency edge. No regression risk taken.

## Round 3 update (opus-4-8_r3)
- Verified round 2 result: **opus-4-8 38, opponent 0** (/logs/rounds/2/results.json).
  All 3 rounds so far won: 38, 34, 38 vs 0.
- Opponent STILL `Nettogrof__nessegrev-julia`. Round 2 latency avg **379ms**, max 502ms
  (times out at 500 -> repeats prev move -> straight into wall). Our latency avg 0.4ms max 5ms.
  Avg game length ~0.8 turns (dies almost instantly).
- Regression tests PASS: main.py vs opp_straight.py = 30-0 as A AND 0-30 (we are B).
- Worst-case latency test (two 25-long snakes, dense board, 8 food): **0.094 ms** avg move.
- DECISION: kept main.py unchanged. 100% win rate maintained via latency edge + survival bot.
  No regression risk taken. Next teammate: only change if opponent stops timing out.

## Round 4 update (opus-4-8_r4)
- Verified round 3 result: **opus-4-8 38, opponent 0** (/logs/rounds/3/results.json).
  All 4 rounds won: 38, 34, 38, 38 vs 0.
- Opponent STILL `Nettogrof__nessegrev-julia`. Round 3 latency avg **390.5ms**, max 504ms
  (>500ms timeout -> repeats prev move -> straight into wall). Our latency avg **0.9ms**, max 12ms.
  Avg game length ~0.72 turns (dies almost instantly).
- Regression tests PASS: main.py vs opp_straight.py = 30-0 as A AND 0-30 (we are B).
- main.py compiles clean (ast.parse OK).
- DECISION: kept main.py unchanged. 100% win rate maintained via latency edge + survival bot.
  No regression risk taken. Next teammate: only change if opponent stops timing out.

## Round 5 update (opus-4-8_r5) — FINAL ROUND
- Verified round 4 result: **opus-4-8 35, opponent 0** (/logs/rounds/4/results.json).
  All 5 rounds won: 38, 34, 38, 35 vs 0 (plus this round).
- Opponent STILL `Nettogrof__nessegrev-julia`. Round 4 latency avg **425.5ms**, max **507ms**
  (>500ms timeout -> engine repeats prev move -> snake walks straight into wall).
  Our latency avg **0.91ms**, max 14ms. Avg game length ~1.1 turns (dies almost instantly).
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B** (we win both orders).
- Worst-case latency test (two 30-long snakes, dense 11x11 board, 10 food): **0.017 ms** avg, 0.039ms max.
- main.py compiles clean; move() wrapped in try/except with self-guarded _safe_fallback (cannot crash->timeout).
- DECISION: kept main.py unchanged. 100% win rate maintained via latency edge + robust survival bot.
  No regression risk taken. This was the final round.

## Round 1 update (opus-4-8 — CURRENT MATCH, fresh /logs)
- NOTE: The prior "Round 2-5" notes above were carried over from a PREVIOUS
  match/game setup. THIS match's /logs only has round 0 so far.
- Verified round 0 result: **opus-4-8 40, opponent 0** (/logs/rounds/0/results.json).
- **Actual opponent name here: `Nettogrof__nessegrev-java`** (note: -java, NOT -julia).
  Same behavior: it TIMES OUT on most moves (avg latency **387ms**, max **510ms**,
  137/190 moves >=490ms -> engine repeats prev move -> snake walks straight into wall).
  Our latency avg **1.06ms**, max 10ms. Avg game length **1.24 turns** (dies almost instantly).
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B** (win both orders).
- Worst-case latency (two 30-long snakes, dense 11x11, 10 food): **0.017ms** avg, 0.038ms max.
- move() wrapped in try/except + self-guarded _safe_fallback -> cannot crash into a timeout.
- DECISION: kept main.py unchanged. 100% win rate maintained via latency edge + robust survival bot.
  No regression risk taken. Next teammate: only change if opponent stops timing out & starts maneuvering.

## Round 2 update (opus-4-8_r2 — CURRENT MATCH)
- Verified results: round 0 **40-0**, round 1 **36-0** (opus-4-8 vs Nettogrof__nessegrev-java). 2/2 rounds won.
- Opponent STILL times out: round 1 latency avg **405.4ms**, max **505ms**, **159/207 moves >=490ms**
  -> engine repeats prev move -> snake walks straight into wall. Avg game length **1.26 turns** (max 13).
  Our latency avg **1.2ms**, max 18ms.
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B** (win both orders).
- Worst-case latency (two 30-long snakes, dense 11x11, 10 food): **0.015ms** avg, 0.031ms max (timeout 500ms).
- main.py parses clean (ast.parse OK); move() wrapped in try/except + _safe_fallback -> cannot crash into timeout.
- DECISION: kept main.py unchanged. 100% win rate via latency edge + robust survival bot. No regression risk taken.
  Next teammate: only change if opponent stops timing out & starts maneuvering.

## Round 3 update (opus-4-8_r3 — CURRENT MATCH)
- Verified results so far: round 0 **40-0**, round 1 **36-0**, round 2 **36-0**
  (opus-4-8 vs Nettogrof__nessegrev-java). 3/3 rounds won.
- Opponent STILL times out: round 2 latency avg **409.4ms**, max **504ms**,
  **163/206 moves >=490ms** -> engine repeats prev move -> snake walks straight
  into wall. Avg game length **0.82 turns** (dies almost instantly).
  Our latency avg **0.71ms**, max 15ms.
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B** (win both orders).
- Worst-case latency (two 28-long snakes, dense 11x11, 10 food): **0.016ms** avg, 0.036ms max (timeout 500ms).
- main.py parses clean (ast.parse OK); move() wrapped in try/except + _safe_fallback -> cannot crash into timeout.
- DECISION: kept main.py unchanged. 100% win rate via latency edge + robust survival bot. No regression risk taken.
  Next teammate: only change if opponent stops timing out & starts maneuvering.

## Round 4 update (opus-4-8_r4 — CURRENT MATCH)
- Verified results so far: round 0 **40-0**, round 1 **36-0**, round 2 **36-0**, round 3 **37-0**
  (opus-4-8 vs Nettogrof__nessegrev-java). 4/4 rounds won.
- Opponent STILL times out: round 3 latency avg **438.6ms**, max **502ms**, **37/43 sampled moves >=490ms**
  -> engine repeats prev move -> snake walks straight into wall. Avg game length **1.204 turns**, max 13.
  Our latency avg **0.42ms**, max 2ms.
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B** (win both orders).
- Worst-case latency (two 30-long snakes, dense 11x11, 5 food): **0.016ms** avg, 0.049ms max (timeout 500ms).
- main.py parses clean (ast.parse OK); move() wrapped in try/except + _safe_fallback -> cannot crash into timeout.
- DECISION: kept main.py unchanged. 100% win rate via latency edge + robust survival bot. No regression risk taken.
  Next teammate: only change if opponent stops timing out & starts maneuvering.

## Round 5 update (opus-4-8_r5 — CURRENT MATCH, FINAL ROUND)
- Verified results so far: round 0 **40-0**, round 1 **36-0**, round 2 **36-0**,
  round 3 **37-0**, round 4 **40-0** (opus-4-8 vs Nettogrof__nessegrev-java). 5/5 won.
- Opponent STILL `Nettogrof__nessegrev-java` and STILL times out: round 4 sampled
  latency avg **311ms**, max **502ms**, 13/22 sampled moves >=490ms
  -> engine repeats prev move -> snake walks straight into wall.
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B** (win both orders).
- Worst-case latency (two 30-long snakes, dense 11x11, 10 food, 200 moves): **0.017ms** avg, 0.098ms max (timeout 500ms).
- main.py parses clean (ast.parse OK); move() wrapped in try/except + _safe_fallback -> cannot crash into timeout.
- DECISION: kept main.py unchanged. 100% win rate via latency edge + robust survival bot. No regression risk taken.

## Round 1 update (opus-4-8 — NEW MATCH vs csauve__bookworm)
- ⚠️ NEW OPPONENT this match: **`csauve__bookworm`** (NOT Nettogrof/-java/-julia).
  Same weakness though: it TIMES OUT most moves.
- Verified round 0 result: **opus-4-8 40, opponent 0** (/logs/rounds/0/results.json).
  40 unique games (250 sim files, most empty/dupes), ALL won by us.
- Opponent latency avg **400.8ms**, max **504ms**, **163/209 moves >=490ms (78%)**
  -> engine repeats prev move -> walks straight into a wall. Confirmed final states
  show opp dying at edges (y=10, x=0) with latency ~501-502ms.
  Avg game length **5.2 turns**, max 10. Our latency avg **0.85ms**, max 7ms.
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B**.
- Worst-case latency (two 30-long snakes, dense 11x11, 10 food, 200 moves):
  **0.013ms avg, 0.026ms max** (timeout 500ms) — cannot time out.
- Sanity: main.py vs main_backup_v3 ~ even (8-12); vs self ~ even (9-11, B-bias).
  Confirms main.py is a competent survival bot that plays close vs equals.
- main.py parses clean; move() wrapped in try/except + self-guarded _safe_fallback.
- DECISION: kept main.py unchanged. 100% win rate via latency edge + robust survival
  bot. No regression risk taken. Next teammate: only change if csauve__bookworm
  stops timing out & starts maneuvering (then consider 2-ply minimax on contested cells).

## Round 2 update (opus-4-8_r2 — CURRENT MATCH vs csauve__bookworm)
- Verified results so far: round 0 **40-0**, round 1 **40-0** (opus-4-8 vs csauve__bookworm). 2/2 won.
- Opponent STILL `csauve__bookworm` and STILL times out: round 1 latency avg **416.0ms**,
  max **505ms**, **198/249 moves >=490ms (80%)** -> engine repeats prev move -> walks
  straight into a wall. Avg game length **6.22 turns**, max 11. Our latency avg **0.6ms**, max 11ms.
- Regression tests PASS: main.py vs opp_straight.py = **30-0 as A AND 0-30 as B** (win both orders).
- Worst-case latency (two 30-long snakes, dense 11x11, 10 food, 200 moves): **0.0157ms** avg,
  0.0925ms max (timeout 500ms) — cannot time out.
- main.py parses clean (ast.parse OK); move() wrapped in try/except + self-guarded _safe_fallback
  -> cannot crash into a timeout.
- DECISION: kept main.py unchanged. 100% win rate via latency edge + robust survival bot. No
  regression risk taken. Next teammate: only change if csauve__bookworm stops timing out & starts
  maneuvering (then consider 2-ply minimax on contested cells).

## Round 3 update (opus-4-8_r3 — CURRENT MATCH vs csauve__bookworm) — IMPORTANT CHANGE
- ⚠️ **OPPONENT STOPPED TIMING OUT.** Round 2 result: **opus-4-8 29, csauve__bookworm 4**
  (we LOST 4 games — first losses this match). Round 0/1 were 40-0/40-0 when opp timed out.
- Round 2 stats (via /tmp/analyze2.py): opp latency avg **355ms**, only **179/939 moves >=490ms (19%)**
  (was ~80% before). Avg game length jumped to **28 turns** (max 298) — the opponent now
  actively plays and maneuvers. The latency-edge free wins are GONE; we must out-play it.
- **Root cause of our 4 losses = SELF-TRAP.** In every loss (e.g. game 4b56be19), our snake
  coiled itself into a pocket where all 4 neighbors were our own body (flood space -> 0).
  The old bot's tail-reachability check was insufficient; it let us walk into shrinking corridors.

- **FIX (main.py v5, backup = main_backup_v4.py):**
  * Survival filter now requires `tail_reachable OR space >= my_len+1` (not just tail loop).
  * Added explicit trap penalty: `-(my_len+2 - space)*6` when space < my_len+2.
  * Bonus for the max-space move (+8) to prefer open board over corridors.
  * Slightly stronger H2H win bonus (30) and aggression only when space >= my_len+2.
  * Safe-fallback now picks the move with MOST flood-fill space (was first-legal).
- **Results (30-game self-play, /tmp/rm2.sh):**
  * v5 vs v4 (old main): **24-15 as A, 23-17 as B** (~60% both orders). Clear improvement.
  * v5 vs v3: 30-25 total. v5 vs opp_straight.py: **15-0 both orders** (no regression).
  * Worst-case latency (two 30-long snakes, dense board): **0.016ms avg, 0.032ms max** (timeout 500).
- **Tuning tried & REJECTED** (all made it worse or wash vs v5):
  * More aggression (edist*3.5, H2H+40): 11-19 LOSS. Aggression HURTS — keep it mild (edist*2.0).
  * Stronger trap penalty (*9, my_len+3): 11-18 LOSS (over-cautious).
  * space weight 4.0 vs 3.0: wash. less aggression (edist*1.0): wash.
- **DECISION: submitted v5.** It directly fixes the self-trap losses and beats old main both orders.
- **TODO next teammate:** opponent is now a competent survival bot. Biggest remaining edge would be
  a proper 2-ply minimax on contested cells / a multi-step body-advance flood-fill (simulate our
  body occupying the corridor over N future turns, not just tail-vacates-once). Re-run
  /tmp/analyze2.py on the NEW round's /logs to see if we still self-trap or lose to H2H.
