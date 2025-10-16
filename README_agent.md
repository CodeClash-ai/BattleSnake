# BattleSnake Agent Notes - Round 11

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
- Round 10 Results: LOST 505-490 (50.6% win rate) - Opponent avoidance TOO CONSERVATIVE
- Round 11 Action: REVERTED TO ROUND 9 (51.9% win rate strategy)

## Round 11 Strategy: Revert to Round 9 (Health-Aware Space Control)

### Why Revert?
Round 10's changes DECREASED win rate from 51.9% to 50.6% (-1.3%)

Round 10 added three features that hurt performance:
1. **2-square buffer from larger opponents** - TOO CONSERVATIVE
   - Marked moves as UNSAFE, reducing options
   - Trapped us in corners and bad positions
   - Better to risk proximity than guarantee bad positioning

2. **Smart food selection** - Possibly too cautious
   - Avoided food closer to larger opponents
   - May have caused starvation in some games

3. **Center control when healthy** - Unclear benefit
   - Moved toward center when not hungry
   - May have led to unnecessary confrontations

### Current Strategy (Round 9 - Restored):
1. **Space Awareness**: Use flood fill to avoid trapped positions
2. **Health Awareness**: Prioritize food when health < 30, urgent when < 15
3. **Head-to-Head Avoidance**: Only avoid direct collisions with larger/equal snakes
4. **Body Collision Avoidance**: Standard collision detection
5. **Balanced Scoring**: Weight space and food distance appropriately

### Key Features:
- Flood fill with max_depth=20 to count reachable spaces
- Minimum space threshold: max(my_length // 2, 5)
- Health thresholds: hungry < 30, very_hungry < 15
- Food priority scaling: very_hungry (10x), hungry (2x), normal (1x)
- Space bonus: 0.01 per reachable square

## Performance History
- Round 1: 64.7% win rate
- Round 2: 30.1% win rate
- Round 3: 99.7% win rate
- Round 4: 34.0% win rate
- Round 5: 100% win rate
- Round 6: 100% win rate
- Round 7: 39.8% win rate
- Round 8: 50.5% win rate
- Round 9: 51.9% win rate ← CURRENT STRATEGY
- Round 10: 50.6% win rate (reverted)
- Round 11: TBD - Reverted to Round 9

## Files in Codebase
- main.py: Current bot (Round 9 strategy - health-aware space control)
- main_round9_health_aware.py: Backup of Round 9 (51.9% win rate)
- main_round10.py: Backup of Round 10 (50.6% win rate - too conservative)
- analyze_round9.py: Analysis script for any round (pass round number as arg)
- Various other backup files

## Recommendations for Next Teammate

### If Round 11 MAINTAINS (~52%):
1. Round 9 strategy is solid and consistent
2. Consider SMALL tweaks:
   - Adjust health thresholds (currently 30/15)
   - Tune flood fill depth (currently 20)
   - Adjust space/food weighting
3. DO NOT add aggressive opponent avoidance (Round 10 proved it fails)

### If Round 11 IMPROVES (>52%):
1. Keep this strategy!
2. Maybe add subtle improvements:
   - Tail chasing when safe
   - Better endgame strategy
   - Opponent movement prediction

### If Round 11 DECLINES (<51%):
1. Opponent may have adapted again
2. Options:
   - Try Round 8 strategy (50.5% but different approach)
   - Experiment with food priority thresholds
   - Consider more aggressive play

## Key Lessons Learned
1. **Conservative != Better**: Round 10's 2-square buffer was too restrictive
2. **Marking moves UNSAFE is dangerous**: Reduces options, can trap us
3. **Incremental changes work best**: Round 9's small improvement over Round 8 was good
4. **Revert when performance drops**: Don't be afraid to go back to what works
5. **Space control matters**: Being able to move freely is critical
6. **Health awareness helps**: Knowing when to prioritize food is important
7. **Direct collision avoidance only**: Only avoid head-to-head when we'd lose

## Analysis Tools Available
- analyze_round9.py: Analyzes any round (pass round number as argument)
  Usage: python3 analyze_round9.py 11

## Strategy Evolution Summary
- Rounds 1-6: Simple food-seeking (variable results, peaked at 100%)
- Round 7: Opponent adapted, dropped to 39.8%
- Round 8: Added space awareness → 50.5%
- Round 9: Added health awareness → 51.9% ← CURRENT
- Round 10: Added opponent avoidance → 50.6% (FAILED, reverted)
- Round 11: Reverted to Round 9 strategy

## What NOT to Do (Learned from Round 10)
1. Do NOT add large buffer zones around opponents
2. Do NOT mark moves as UNSAFE based on proximity alone
3. Do NOT over-optimize food selection (can cause starvation)
4. Do NOT add center control without clear benefit
5. Do NOT make multiple changes at once (hard to debug)

Good luck! Round 9 strategy is solid - small tweaks only!
