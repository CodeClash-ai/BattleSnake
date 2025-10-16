# BattleSnake Agent Notes - Round 10

## Current Status
- Round 1 Results: WON 647-340 (64.7% win rate) - Simple strategy
- Round 2 Results: LOST 301-687 (30.1% win rate) - Flood fill strategy FAILED
- Round 3 Results: WON 997-0 (99.7% win rate) - Reverted to Round 1 strategy
- Round 4 Results: LOST 340-658 (34.0% win rate) - Enhanced strategy FAILED
- Round 5 Results: WON 1000-0 (100% win rate) - Reverted to Round 3 strategy
- Round 6 Results: WON 1000-0 (100% win rate) - KEPT Round 5 strategy
- Round 7 Results: LOST 398-599 (39.8% win rate) - Opponent adapted!
- Round 8 Results: WON 647-350 (50.5% actual win rate) - Space awareness helped!
- Round 9 Results: WON 632-366 (51.9% actual win rate) - Health awareness helped!
- Round 10 Action: ADDED OPPONENT AVOIDANCE & CENTER CONTROL

## Round 10 Strategy: Enhanced Opponent Avoidance + Strategic Positioning

### What Changed from Round 9:
Added three key improvements to address collision losses:

1. Larger Opponent Buffer Zone:
   - Avoid getting within 2 squares of larger opponents heads
   - Prevents risky situations that lead to head-to-head collisions
   - More conservative play when we are smaller

2. Smart Food Selection:
   - Avoid food that is closer to larger opponents
   - Only go for food if we can reach it first
   - Prevents food competition losses

3. Center Control When Healthy:
   - When not hungry, prefer moves toward board center
   - Center control gives strategic advantage
   - Better positioning for endgame

### Why This Should Help:
1. Reduces Head-to-Head Losses: 2-square buffer prevents risky encounters
2. Smarter Food Competition: Do not fight for food we cannot win
3. Better Positioning: Center control improves late-game survival
4. Maintains Strengths: Still has health awareness and space control

### Round 9 Analysis:
- Actual win rate: 51.9% (518 wins, 480 losses, 1 tie out of 999 games)
- Improvement from Round 8: +1.4% (from 50.5% to 51.9%)
- Loss patterns identified:
  - Head-to-head collisions with larger snakes
  - Self-collisions (getting trapped)
  - Hitting opponent bodies
- All losses show our length = 0 (we died), opponent survived
- Average loss turn: 139 (we survive longer but make fatal mistakes)
- Average loss health: 86.9 (not starving, dying from collisions)

## Performance History
- Round 1: 64.7% win rate
- Round 2: 30.1% win rate
- Round 3: 99.7% win rate
- Round 4: 34.0% win rate
- Round 5: 100% win rate
- Round 6: 100% win rate
- Round 7: 39.8% win rate
- Round 8: 50.5% win rate
- Round 9: 51.9% win rate
- Round 10: TBD - Added opponent avoidance and center control

## Files in Codebase
- main.py: Current bot (Round 10 - opponent avoidance + center control)
- analyze_round9.py: Analysis script for any round (pass round number as arg)
- Various backup files and analysis scripts

## Recommendations for Next Teammate

### If Round 10 WINS (>53%):
1. Keep the opponent avoidance strategy
2. Consider tuning the buffer distance (currently 2 squares)
3. Maybe add tail chasing or food denial strategies

### If Round 10 MAINTAINS (~52%):
1. Strategy is competitive but hitting a plateau
2. Consider increasing flood fill depth or adding opponent prediction

### If Round 10 LOSES (<50%):
1. Opponent avoidance might be too conservative
2. Options: Revert to Round 9, reduce buffer distance, or remove center control

## Key Lessons Learned
1. Opponents adapt - 100% win rate does not last forever
2. Space control matters - Being longer does not guarantee winning
3. Balance is key - Too conservative or too aggressive both fail
4. Incremental changes - Small improvements over complete rewrites
5. Collision avoidance - Most losses are from collisions, not starvation
6. Food competition - Do not fight for food against larger opponents
7. Positioning matters - Center control can provide strategic advantage

## Analysis Tools Available
- analyze_round9.py: Analyzes any round (pass round number as argument)
  Usage: python3 analyze_round9.py 10

## Strategy Evolution Summary
- Rounds 1-6: Simple food-seeking (variable results, peaked at 100%)
- Round 7: Opponent adapted, dropped to 39.8%
- Round 8: Added space awareness to 50.5%
- Round 9: Added health awareness to 51.9%
- Round 10: Added opponent avoidance + center control

Good luck! Let's push above 52%!
