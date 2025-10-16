Hello teammate!

This is gemini-2.5-pro from round 1. I've made some initial improvements to our Battlesnake bot in `main.py`.

Here's a summary of the changes:
- Implemented basic collision avoidance:
    - Avoids moving out of bounds.
    - Avoids colliding with its own body.
    - Avoids colliding with other snakes.
- Implemented basic food-seeking behavior:
    - The snake will now move towards the closest food pellet.
    - If there's no food or no safe path to food, it will make a random safe move.

The code in `main.py` should be much more robust than the initial version.

For future rounds, here are some ideas for improvement:
- **More advanced pathfinding:** The current food-seeking logic is very simple. It only considers moves that directly reduce the Manhattan distance. A* or other pathfinding algorithms would be much more effective.
- **Flood fill algorithm:** To avoid getting trapped in tight spaces, we could implement a flood fill algorithm to determine the largest accessible area from each possible move.
- **Opponent prediction:** A more advanced bot could try to predict the moves of opponent snakes to either trap them or avoid being trapped.
- **Health management:** The bot currently always seeks food. It might be better to only seek food when its health is low and to be more aggressive or defensive otherwise.

Good luck in the next round!
