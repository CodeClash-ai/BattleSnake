# Round 14 Summary - Critical Bug Fix

## Problem Identified
Round 13 dropped to 48.2% win rate (from 62% in Round 11). Analysis revealed a critical bug in head-to-head collision avoidance logic.

## Root Cause
The bot was marking moves as UNSAFE if they were adjacent to larger/equal opponent heads, even when those moves were the only safe option. This caused the bot to default to unsafe moves and die immediately.

## Solution Implemented
Changed collision avoidance to use a two-tier system:
1. UNSAFE moves: Actually dangerous (walls, bodies, out of bounds)
2. RISKY moves: Adjacent to larger opponents (prefer to avoid, but acceptable if necessary)

## Testing
Created test case from actual game failure (sim_1.jsonl, turn 41):
- Before fix: Chose down (unsafe) and died
- After fix: Chose left (risky but safe) and survived

## Expected Outcome
Win rate should return to 60%+ range, matching Round 11 performance.

## Files Modified
- main.py: Implemented risky move logic
- README_agent.md: Documented bug and fix
- Created test scripts for validation
