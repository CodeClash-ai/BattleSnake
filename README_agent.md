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
