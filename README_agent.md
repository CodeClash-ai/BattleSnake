# Strategy and Notes

Our bot (`gemini-3-5-flash`) controls a snake with state-of-the-art heuristics to outlast standard and custom opponents alike.

## Analysis & Improvements
In Round 3, we successfully optimized several components of the bot:
1. **Time-Aware Flood Fill**: A highly precise BFS that simulates step-by-step movement of both snakes' bodies, naturally handling coiling, tail-chasing, and pocket sizing.
2. **Voronoi Territory Partitioning**: Counts cells strictly closer to us than any opponent head. We increased its weight from 20 to 150 to emphasize strong territory control.
3. **Optimized Food / Hunger Heuristics**: Our snake now dynamically balances survival and growth. Specifically:
   - We target closest food aggressively if we are within 3 steps of it, or if our length is not at least 2 segments larger than the longest opponent, or if our health drops below 40.
   - Otherwise, we target our own tail to coil defensively.
4. **Enhanced Wall Avoidance**: We increased wall/corner penalties to keep our snake operating in open territory where it cannot easily be pinned.
