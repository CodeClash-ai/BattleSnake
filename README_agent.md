# Agent Notes (opus-4-8 team) — BattleSnake

## TL;DR
- Game: standard BattleSnake, 11x11, 2 snakes (us vs `pambrose__pambrose-kotlin`).
- Opponent is the naive **SimpleSnake**: NO collision avoidance, walks toward the
  FARTHEST food (or center). It kills itself fast (usually within ~4-12 turns by
  hitting a wall). Beating it just requires surviving longer.
- Our `main.py` was rewritten (round 1) from the identical naive port into a real
  survival bot. Local result vs the naive opponent: **30-0-0** over 30 games.

## Current strategy (main.py)
Per turn, for each of 4 candidate moves:
  1. Discard immediately-lethal moves (out of bounds / into a snake body).
     Tails are treated as free unless that snake just ate (grew).
  2. Score survivors by:
     - `space*10` from a flood-fill of reachable free cells (avoid self-trapping).
       Big penalty (-500) if reachable space < our length.
     - Head-to-head: +60 if we're strictly longer than an enemy that can reach the
       square (kill chance); -1000 if we'd lose/tie (avoid).
     - Food: move closer to nearest food, weight scales with hunger (100-health);
       urgent bias when health < 30; +40 for landing on food.
  3. Pick best; fall back to any legal move; else "up".

Coordinate system is y-up (up = y+1).

## Testing harness (how to reproduce)
```bash
# backup of the original naive bot:
cp main_naive_backup.py /tmp/opp/main.py   # opponent == naive SimpleSnake
cp server.py /tmp/opp/server.py
cd /workspace && PORT=8000 python3 main.py >/tmp/me.log 2>&1 &
cd /tmp/opp && PORT=8001 python3 main.py >/tmp/opp.log 2>&1 &
# then loop games:
./game/battlesnake play -W 11 -H 11 --name me --url http://localhost:8000 \
    --name opp --url http://localhost:8001 -g standard 2>&1 | grep "Game completed"
```
Solo survival test: `./game/battlesnake play -W 11 -H 11 --name me --url http://localhost:8000 -g solo`
(We survive ~300-480 turns solo — no self-trapping.)

## Log analysis
- Round results: `/logs/rounds/N/results.json` (winner + per-snake scores over ~250 sims).
- Per-game replays: `/logs/rounds/N/sim_*.jsonl` (line 1 = ruleset, then per-turn boards).
- Round 0 (naive vs naive): opp 89 / tie 79 / us 82 — basically a coin flip.
  Our rewrite should push this heavily in our favor.

## Ideas for future rounds (if opponent changes / to squeeze more)
- Add 2-ply minimax on the opponent head to force H2H kills reliably.
- Tune food aggression: eating grows us, which helps win H2H and constrictor-style
  play, but too much food-chasing can trap us. Current weights favor survival.
- If opponent becomes non-naive, the flood-fill + H2H logic already generalizes.

## Round 2 update (opus-4-8)
- Round 1 result was **250-0** (dominant win). Local retest vs naive: 60-0-0.
- Kept the winning survival+space+H2H strategy intact.
- Tweak: increased H2H kill bonus 60 -> 120 (main.py line ~155). Purely makes us
  more willing to move into a square a *strictly shorter* enemy could enter
  (guaranteed kill). Cannot cause us to enter losing/tie H2H (still -1000).
- NOTE on testing: starting flask servers in one bash call and running MANY
  battlesnake games in a *separate* call works; but chaining server-start +
  a long game loop in ONE command tends to time out (returncode 143). Start
  servers first (their own command), wait, then run games in later commands.
  Winner string in CLI output: "<name> was the winner." / "It was a tie."

## Round 3 update (opus-4-8)
- IMPORTANT: Opponent CHANGED. It is now **Nettogrof__nessegrev-julia**, NOT the
  pambrose naive bot. New opponent is ALSO naive/self-destructing: it walks in a
  straight line (up a column) and hits the wall, dying by turn ~2-11. See
  /logs/rounds/0 replays (sim_13 walks up column x=1 into the wall).
- Round 0 result: **20-0 win** (we survive every game; opponent always self-kills).
- Change made this round: added a MILD center bias (weight 0.3) after the food
  block in main.py — keeps us off walls, preserves escape routes, breaks ties
  toward safer squares. Retested vs naive proxy: 15-0, no regression.
  Solo survival still ~345-400 turns (no self-trapping).
- Strategy unchanged otherwise: space flood-fill (king), H2H avoid ties/losses,
  food by hunger. This dominates both known naive opponents.
- If opponent ever becomes non-trivial: the flood-fill + H2H already generalizes;
  consider 2-ply minimax on enemy head. But current opponent needs nothing more.

## Round 2 update #2 (opus-4-8) — CURRENT
- Confirmed opponent is still Nettogrof__nessegrev-julia (naive: walks straight
  UP a column, dies at wall ~turn 11). Rounds 0 & 1 both won 20-0.
- Since opponent self-destructs fast, games become effectively SOLO SURVIVAL for
  us — so long-game self-trap avoidance is what actually matters.
- Change: added TAIL-REACHABILITY heuristic to flood-fill (_flood_fill now
  returns (count, reached_target); reward +150 if our own tail is reachable =
  we can tail-chase forever = guaranteed not trapped). See main.py.
- Results: vs naive still 20-0-0. Solo survival improved (was ~280 turns; now
  276/342/495 across 3 runs). Head-to-head vs prior version (main_r2_backup.py)
  = 10-10 (equal in combat, strictly better at not self-trapping).
- Backups: main_r2_backup.py (pre-tail-heuristic), main_naive_backup.py (naive).
- Testing gotcha CONFIRMED: start each flask server in ITS OWN command with
  `nohup env PORT=xxxx python3 main.py >log 2>&1 & disown`, sleep 4, then run
  games in later commands. Chaining server-start + game-loop in one command
  times out (rc 143).
