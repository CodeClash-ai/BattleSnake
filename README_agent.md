# Battlesnake Bot - Gemini Improved Version

## Strategy and Design Details

In this round, we dramatically improved the bot's survivability by building a highly intelligent, robust rule-based logic to replace the original naive/buggy strategy.

### Key Features Implemented:
1. **Obstacle Collision Avoidance**: Avoids running into walls, its own body, or opponent bodies.
2. **Head-to-Head Collision Avoidance**: Identifies cells adjacent to the opponent's head. It will dynamically avoid these spaces unless our snake is strictly longer than the opponent, minimizing the risk of getting eliminated by head-on collisions.
3. **Dead End & Trap Prevention (Flood Fill / BFS)**: Conducts a real-time BFS from each prospective move to count the reachable area. It ranks moves with sufficient breathing room (reachable area >= current body length) equally, completely avoiding tight pockets where the snake could get trapped.
4. **Closest Food Targeting**: Uses Manhattan distance to navigate towards the closest piece of food (prioritized behind survivability constraints) rather than the original bug/quirk of going to the farthest food.
5. **Fallback Cascade**: Clean tiered fallback logic (`smart_moves` -> `non_colliding_moves` -> `safe_moves` -> default "up") to ensure we always return a valid legal move even in worst-case scenarios.

### Local Testing:
We have verified the improvements by running local simulation matches against ourselves and we consistently survived way longer, easily winning due to superior pathfinding and trap avoidance.
