# Strategy and Notes

Our bot (`gemini-3-5-flash`) controls a snake with state-of-the-art heuristics to outlast standard and custom opponents alike.

## Key Enhancements in Round 4 (This Round)
We analyzed past match logs and discovered that our snake was getting trapped inside pockets of its own body/coils. The previous implementation of the tail-reachability bonus (with a heavy weighting of 100,000) was overriding the flood fill score, driving the snake to enter dead-end corridors just because the tail was theoretically reachable.

To fix this and guarantee perfect end-game survival, we introduced:

1. **Time-Aware (Time-Predictive) Flood Fill**:
   - Instead of a static BFS, we implemented a BFS that keeps track of `step/time`.
   - Each grid cell occupied by any snake segment is tracked with the exact step at which it will be vacated (`length - index`).
   - The BFS only allows expanding into occupied cells if the current step of the path is greater than or equal to the cell's vacation step.
   - This naturally, elegantly, and perfectly handles:
     - Following our own tail (or the opponent's tail).
     - Coiling within tight spaces and corridors safely.
     - Accurately estimating pocket sizes relative to body length.

2. **Absolute Pocket Safeguard**:
   - If the time-aware reachable space is strictly less than our body length, we apply a massive penalty (`-10,000,000`) to guarantee the snake prioritizes exiting the pocket immediately.

3. **Voronoi Territory Partitioning & Head-to-Head Avoidance**:
   - Maintained territory control and avoided head-to-head collisions with larger/equal size opponent snakes.

These improvements prevent coiling-related pocket traps entirely while optimizing food search and territory control.
