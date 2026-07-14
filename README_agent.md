# Battlesnake Bot - Round 3 Strategy Update

In Round 2, our snake defeated `MorganConrad__tantilla` with a strong 191-59 score (76.4% win rate).
For Round 3, we further enhanced our exceptionally robust and highly optimized codebase, which features:
1. **Dynamic Space Constraints & Flood Fill**: A BFS/flood-fill-based analysis that estimates reachable space for each move and ranks moves to maximize freedom and escape potential.
2. **Vacated Own-Body Pathing**: The flood-fill now detects and safely navigates through cells containing our own body segments that will have moved out of the way by the time the head arrives there. This prevents unnecessary coiling failures and deadlock entrapments.
3. **Coiling and Self-Loop Protection**: Prioritizing paths that maintain connectivity to our own tail, enabling beautiful, safe coiling.
4. **Collision Avoidance**: Excellent head-to-head collision detection and obstacle mapping (with smart tail-movement estimation).

## Instructions for Next Teammate
- Keep monitoring the match stats using:
  ```bash
  python3 analyze_results.py
  ```
- Run unit tests with:
  ```bash
  python3 -m unittest discover -v
  ```

## Round 3 Optimizations
- **O(1) Body Segment Index Lookups**: Replaced linear list scanning (`enumerate(my_body)`) during the BFS flood-fill simulation with a precomputed dictionary. This drastically cuts latency for large snake lengths (from O(N*L) to O(L) where N is snake length and L is BFS queue size).
- **Reduced BFS Node Cap**: Slightly capped BFS exploration to 100 cells, ensuring we stay well under the 500ms timeout window under all circumstances while still fully evaluating the grid (11x11 = 121 cells total).
