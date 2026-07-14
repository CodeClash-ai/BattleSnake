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
