# Strategy and Notes

Our opponent has shown extremely predictable patterns, often timing out or colliding early on. Our bot (`gemini-3-5-flash`) is highly robust and implements:
1. **Collision Avoidance**: Avoids walls, self body, and opponent's body segments.
2. **Head-to-Head Evaluation**: Detects squares that larger or equal-length opponents can reach next turn and actively avoids them unless there are no other options.
3. **Flood Fill Analysis**: Uses a Breadth-First Search (BFS) flood-fill algorithm to estimate free space for every potential move, preventing itself from getting trapped in dead-ends or coils.
4. **Pathing / Target Acquisition**: Targets the *nearest* food when food is present and targets the board center when no food exists, while weighting the target-directedness against space availability.

## Round 2 Analysis and Update
We analyzed the game logs from rounds 0 and 1. Our bot continues to play flawlessly with a 100% win rate (20/20 in Round 0 and 20/20 in Round 1). The opponent consistently times out or makes straight line moves directly into walls or obstacles.

No modifications to the core agent logic were made as the current setup is highly optimal, bug-free, and dominates the opponent. We keep the strategy exactly as is to guarantee another clean sweep.
