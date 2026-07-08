# Agent Notes (CodeClash Battlesnake)

## Current status (after round 1 edits by opus-4-8)
The opponent is **pambrose SimpleSnake** (naive Kotlin port): NO collision
avoidance, walks straight toward the FARTHEST food. It self-eliminates in a
handful of turns very often.

Round 0 baseline (both bots were the naive port) was essentially a coin flip:
WINS=84 LOSSES=81 TIES=85 out of 250. See /logs/rounds/0/.

### What I changed
Rewrote `main.py` into a real survival bot:
  - Never moves into walls / bodies (treats vacating tails as passable).
  - Flood-fill space evaluation per candidate move (avoids trapping itself).
  - Head-to-head: heavily avoids ties/losses; rewards kills vs shorter snakes.
  - Food seeking, weighted higher when health < 35.
Backup of the old naive bot: `main_v0_backup.py`.

### Results after change (local tests vs naive opponent)
**90 wins, 0 losses, 0 ties** over 90 games. Self-play survives 130+ turns.
Move computation ~0.1 microseconds — zero timeout risk.

## Testing tools (in /workspace)
- `naive_opponent.py`  — the pambrose SimpleSnake, as a runnable server (for tests).
- `run_matches.sh N`   — runs N matches (main.py vs naive_opponent.py) via the
  bundled `game/battlesnake` CLI, prints W/L/T. Usage: `./run_matches.sh 60`.
- `game/battlesnake`   — prebuilt Battlesnake CLI (Go rules engine).

Start a server manually: `PORT=8001 python3 main.py`

## Ideas for future rounds (if opponent gets smarter)
- Add opponent move prediction / minimax lookahead (currently 1-ply heuristic).
- Longest-path / tail-chasing when space is tight.
- Aggressively cut off the opponent's flood-fill area when we are longer.
- Tune food weights; avoid over-eating (growing longer = easier to trap self).
