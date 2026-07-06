# Agent Notes & Strategy

I have drastically improved the Battlesnake bot strategy by implementing basic safety checks:
1. **Collision Avoidance:** The snake now avoids self-collisions, wall collisions, and collisions with other snakes by maintaining a set of occupied cells.
2. **Nearest Food Targeting:** Instead of chasing the *farthest* food (which was a preserved quirk of the SimpleSnake baseline), our snake now targets the **closest** food item using Manhattan distance.
3. **Safe Move Optimization:** Among all available collision-free moves, the snake chooses the one that minimizes the Manhattan distance to the target (closest food or center).

This should result in a significantly higher win rate and fewer draws/losses due to self-elimination.
