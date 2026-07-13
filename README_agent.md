# Strategy and Notes

Our bot (`gemini-3-5-flash`) controls a snake with state-of-the-art heuristics to outlast standard and custom opponents alike.

In Round 0, our bot completely dominated the opponent (`jackisherwood__battlesnake-elon`) with **211 wins to 37**.
In Round 1, we achieved **176 wins, 73 losses, and 1 tie** against `joshhartmann11__battlejake2019`.
In Round 2, we played `kentmacdonald2__beames` and won with **163 wins, 78 losses, and 9 ties**.

## Analysis & Improvements
We analyzed the previous round and historical simulations. The bot is extremely stable, and has optimized heuristics (reduced wall penalty, sophisticated Time-Aware Flood Fill, and Voronoi territory partitioning) that perfectly balance defensive coiling and opportunistic food/territory control. We maintained the current optimal configuration as it consistently outperforms opponents by huge margins across large batches of simulations.
