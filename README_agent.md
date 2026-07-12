# Strategy and Notes

Our opponent is `pambrose__pambrose-kotlin`, which uses the `SimpleSnake` logic.
SimpleSnake has some critical weaknesses:
1. It has NO collision avoidance or out-of-bounds avoidance at all.
2. It has a bug where it targets the FARTHEST food instead of the nearest.
3. It has a rigid deterministic movement style.

We replaced the original port of SimpleSnake in `main.py` with an optimized and highly robust agent:
- **Collision Avoidance**: Avoids walls, self body, and opponent's body segments.
- **Head-to-Head Evaluation**: Detects squares that larger or equal-length opponents can reach next turn and actively avoids them unless there are no other options.
- **Flood Fill Analysis**: Uses a Breadth-First Search (BFS) flood-fill algorithm to estimate free space for every potential move, preventing itself from getting trapped in dead-ends or coils.
- **Pathing / Target Acquisition**: Targets the *nearest* food when food is present (correcting the farthest-food bug) and targets the board center when no food exists, while weighting the target-directedness against space availability.

This ensures our snake survives long-term while the opponent frequently collides or traps itself.
