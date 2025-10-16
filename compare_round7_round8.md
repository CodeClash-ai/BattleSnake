# Comparison: Round 7 vs Round 8 Strategy

## Round 7 (Simple Strategy - 39.8% win rate)
**Algorithm:**
1. Mark safe moves (avoid walls, self, opponents, head-to-head)
2. If food exists: move toward closest food (Manhattan distance)
3. If no food: random safe move

**Strengths:**
- Fast execution
- Simple and deterministic
- Worked perfectly in Rounds 5-6 (100% win rate)

**Weaknesses:**
- No space awareness
- Gets trapped in corners/dead ends
- Opponent adapted to exploit this in Round 7

**Example Failure:**
- Game 1: Length 14 vs 6, trapped at turn 83
- We were longer but died from self-collision in corner

## Round 8 (Space-Aware Strategy - TBD)
**Algorithm:**
1. Mark safe moves (same as Round 7)
2. Calculate reachable space for each safe move (flood fill, depth 20)
3. Filter out moves with insufficient space (< length/2 or < 5)
4. If food exists: move toward food, use space as tiebreaker
5. If no food: move to position with most space

**Strengths:**
- Prevents getting trapped
- Still aggressive toward food
- Adapts space requirement to snake length
- Fast (depth-limited flood fill)

**Potential Weaknesses:**
- Slightly slower than Round 7 (flood fill overhead)
- May be too cautious in some situations
- Untested against adapted opponent

**Key Parameters:**
- Max flood fill depth: 20
- Min space threshold: max(length/2, 5)
- Scoring: -distance + (space * 0.01)

## Expected Outcome
- If opponent still uses space control: Should improve significantly
- If opponent reverted to simple: Should still be competitive
- Target: >60% win rate (better than Round 7's 39.8%)

## Fallback Plan
If Round 8 loses badly:
1. Check if flood fill is too slow
2. Try adjusting parameters (depth, threshold)
3. Consider reverting to Round 7 simple strategy
4. Analyze new opponent patterns
