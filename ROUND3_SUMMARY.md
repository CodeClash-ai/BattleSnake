# Round 3 Summary

## Decision: Reverted to Round 1 Strategy

### Performance Comparison
- **Round 1**: 647 wins, 340 losses (64.7% win rate) - Simple strategy
- **Round 2**: 301 wins, 687 losses (30.1% win rate) - Flood fill strategy
- **Round 3**: Reverted to Round 1 (expecting ~65% win rate)

### Why Revert?
Round 2's flood fill implementation caused a **massive 34.6 percentage point drop** in win rate. This is a clear regression, not an improvement.

### What Was Wrong with Round 2?
The flood fill approach had several issues:
1. **Too conservative**: May have avoided good moves due to overly cautious space calculations
2. **Performance overhead**: BFS on every move for every safe direction
3. **Complexity bugs**: More complex code = more potential for bugs
4. **Over-optimization**: Trying to avoid dead ends may have made the bot too passive

### Current Strategy (Round 1)
Simple and effective:
- Avoid walls, self-collision, opponent bodies
- Avoid head-to-head collisions with larger/equal snakes
- Always move toward closest food
- Fast decision making with minimal computation

### Files Modified
- `main.py`: Reverted to Round 1 simple strategy
- `main_round2_failed.py`: Saved Round 2 version for reference
- `README_agent.md`: Updated with Round 3 notes and recommendations
- `ROUND3_SUMMARY.md`: This summary

### Recommendation
The simple strategy works well. Future improvements should:
1. Be tested thoroughly before deployment
2. Add ONE feature at a time
3. Focus on safe, incremental improvements
4. Avoid over-engineering

### Next Steps for Future Rounds
If teammates want to improve beyond 65% win rate:
- Smarter food selection (avoid food opponents are closer to)
- Health-based decisions (only seek food when health < 50)
- Simple neighbor counting (not full flood fill)
- Tail following when healthy

**Key Lesson**: Sometimes the simple solution is the best solution. Don't add complexity without proven benefits.
