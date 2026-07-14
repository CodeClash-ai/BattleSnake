# Battlesnake Bot - Round 1 Strategy and Improvement Notes

We reviewed Round 0 game logs and improved the survivability of our bot against `OliverMKing__astar-snake`.

## Match Performance Summary
- **Round 0 Score**: 123 wins vs 124 losses (approx 50% win rate) against an A*-based snake opponent.
- **Latency & Reliability**: Exceptionally fast response time (~0-1ms), absolute zero timeouts or crashes.

## Code Base & Strategy Improvements
1. **Dynamic Obstacle / Tail Recognition**:
   - In standard Battlesnake, the tail of a snake moves out of the way on the next turn, unless the snake consumed food in the previous turn (health = 100).
   - Our previous version treated all tail segments as permanent obstacles, leading to conservative, suboptimal moves in tight corridors.
   - We updated `main.py` to identify if a snake is growing (using `health == 100` as a proxy). If a snake is not growing, we exclude its tail segment from the list of immediate obstacles since it will move out of the way on the next tick. This allows our bot to seamlessly follow opponent tails or its own tail in tightly packed boards.

2. **Upgraded Trap Avoidance & Flood-Fill Depth**:
   - Increased the BFS/flood-fill cap from `30` to `45` to search deeper, giving much safer path choices on larger boards with long body segments.
   - Increased the minimum space-needed target check to `20` to better navigate mid-to-late game scenarios where the snake body grows quite large.

All unit tests pass correctly.

## Instructions for Next Teammate
- Keep monitoring the match stats using:
  ```bash
  python analyze_results.py
  ```
- Run unit tests with:
  ```bash
  python -m unittest discover -v
  ```

# Round 2 Strategy and Precision Upgrades
1. **Dynamic Flood Fill Deeper Limit (45 -> 60)**:
   - Raised flood-fill count limits to 60 cells to provide higher-precision path choices and avoid large, complex late-game dead ends.
2. **Optimized Minimum Space Check Target (20 -> 30)**:
   - Tuned minimum safe space check to dynamically scale up to `30` cells (clamped to body length). This ensures large snakes correctly prioritize maximizing area to wind out of complex tail traps instead of food-chasing prematurely.
