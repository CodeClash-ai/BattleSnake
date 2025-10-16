# Round 5 Summary

## What I Did
1. **Analyzed Round 4 Results**: Discovered that Round 4's "enhancements" caused win rate to drop from 99.7% to 34.0%
2. **Identified the Problems**:
   - Health-based food seeking (only chase when health < 70) caused starvation/poor positioning
   - "Smart" food selection (avoiding food opponents are closer to) overcomplicated decisions
   - Edge avoidance when healthy didn't help
3. **Reverted to Round 3**: Restored the 99.7% win rate strategy
4. **Updated Documentation**: Comprehensive README_agent.md with lessons learned
5. **Created Analysis Tools**: Scripts for analyzing game outcomes and individual games

## Key Insight
**Simple is better!** The Round 3 strategy of "always chase closest food + avoid collisions" achieved 99.7% win rate. Round 4's attempt to be "smarter" backfired spectacularly.

## Current Bot Strategy (Round 3 = Round 5)
1. Avoid walls, self-collision, opponent collisions
2. Avoid head-to-head with larger/equal snakes
3. Always move toward closest food when food exists
4. Random safe move when no food

## Expected Performance
Should return to ~99.7% win rate (997 wins, 0 losses, 2 ties out of 1000 games)

## Files Modified
- `main.py`: Reverted to Round 3 version
- `README_agent.md`: Updated with Round 4 post-mortem and Round 5 actions
- Created analysis scripts: `analyze_round4_deaths.py`, `find_losses.py`, `analyze_loss_game.py`

## Recommendation for Next Teammate
**DO NOT CHANGE THE STRATEGY!** 99.7% win rate is nearly perfect. If you must experiment:
- Test thoroughly first
- Make only ONE small change
- Revert immediately if win rate drops below 95%
