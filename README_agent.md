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

## Round 2 Strategy & Updates

1. **Strategic Food Avoidance**:
   - When we are already significantly larger than the opponent, growing further only makes navigation harder, limits space, and leads to accidental trapping.
   - We introduced a conditional hunger mechanism: if our length is already at least 2 greater than the opponent's max length AND our health is safe (above 35), we disable aggressive food targeting.

2. **Tail Following and Coiling Target**:
   - When we are not hungry, we target our own tail (`you["body"][-1]`) instead of food. This aligns our pathing with our own movement, allowing safe tail-following and coiling patterns, significantly improving longevity.

3. **Fallback Move Selection**:
   - If no strictly obstacle-free squares exist (e.g., when completely cornered or surrounded), we fall back to choosing a move within bounds instead of defaulting to `"up"`. This gives the snake a chance to walk into segments that are about to be vacated on the exact turn.
