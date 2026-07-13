# Strategy and Notes

Our bot (`gemini-3-5-flash`) controls a snake with state-of-the-art heuristics to outlast standard and custom opponents alike.

In Round 0, our bot completely dominated the opponent (`jackisherwood__battlesnake-elon`) with **211 wins to 37**.

## Key Improvements
1. **Time-Aware Flood Fill Implementation**:
   - Instead of standard static BFS/Flood-Fill, we track time-aware occupation steps.
   - Each grid cell occupied by any snake segment is tracked with the exact step at which it will be vacated (`length - index`).
   - The BFS only expands into cells once they are vacated, meaning our snake can perfectly follow its own tail, follow opponent tails, and accurately navigate winding paths without underestimating space.

2. **Absolute Pocket Safeguard**:
   - If the time-aware reachable space is strictly less than our body length, we apply a massive penalty (`-10,000,000`) to guarantee the snake exits immediately.

3. **Voronoi Territory Partitioning & Head-to-Head Avoidance**:
   - Maintained territory control and avoided head-to-head collisions with larger/equal size opponent snakes.
