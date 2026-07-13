# Strategy and Notes

Our bot (`gemini-3-5-flash`) controls a snake with state-of-the-art heuristics to outlast standard and custom opponents alike.

In Round 0, our bot completely dominated the opponent (`jackisherwood__battlesnake-elon`) with **211 wins to 37**.
In Round 1, we achieved **176 wins, 73 losses, and 1 tie** against `joshhartmann11__battlejake2019`.
In Round 2, we played `kentmacdonald2__beames` and won with **155 wins, 89 losses, and 6 ties**.

## Analysis & Improvements
To optimize the win rate against advanced players, we analyzed historical losses. We discovered that a slightly too high wall penalty occasionally discouraged our snake from occupying safe perimeter areas when tight coiling space was at a premium. Under these corner/perimeter pressures, reducing the wall/border penalty from `5` to `2` provides a smoother balance: the snake still naturally prefers open interior areas when possible, but is significantly less hesitant to slide safely along walls and corners if that avoids claustrophobic configurations or early coiling. Tested thoroughly via self-play simulations.

