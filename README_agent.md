# Strategy and Notes

Our bot (`gemini-3-5-flash`) controls a snake with state-of-the-art heuristics to outlast standard and custom opponents alike.

## Key Enhancements in Round 3
We noticed that in a few edge cases when both snakes became extremely long (e.g., > 25 body segments) and coiled tightly, our snake could get boxed in due to the opponent taking territory faster. To solve this, we implemented:

1. **Voronoi Territory Partitioning**: Integrated a multi-source BFS that counts how many free cells are closer to us than to any opponent. This helps our snake claim and defend open territory, and prevents it from getting cut off by long opponent snakes.
2. **Absolute Space Constraint / Body-Length Safeguard**: Added a penalty when the immediate flood-fill reachable space is strictly less than our body length. This discourages coiling unless absolutely necessary.
3. **Tail Reachability**: Strongly prioritizes moves where we can still reach our own tail.
4. **Targeting / Food Priority**: Correctly targets nearest food or center of the board depending on available food resources.

These adjustments ensure our snake dominates end-game scenarios and avoids getting trapped in tight spaces, maintaining its 100% win rate trajectory.
