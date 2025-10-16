#!/usr/bin/env python3
"""
Analysis script for BattleSnake game logs.
Usage: python3 analyze_games.py <round_number>
"""

import json
import sys
import os
from collections import defaultdict

def analyze_round(round_num):
    """Analyze all games in a specific round."""
    round_dir = f"/logs/rounds/{round_num}"
    
    if not os.path.exists(round_dir):
        print(f"Round {round_num} directory not found at {round_dir}")
        return
    
    # Read results summary
    results_file = os.path.join(round_dir, "results.json")
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            results = json.load(f)
        print(f"\n=== Round {round_num} Summary ===")
        print(f"Winner: {results['winner']}")
        print(f"Scores: {results['scores']}")
        print()
    
    # Analyze individual games
    wins = 0
    losses = 0
    ties = 0
    total_turns_won = []
    total_turns_lost = []
    death_reasons = defaultdict(int)
    
    sim_files = sorted([f for f in os.listdir(round_dir) if f.startswith('sim_') and f.endswith('.jsonl')])
    
    for sim_file in sim_files:
        filepath = os.path.join(round_dir, sim_file)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        if len(lines) < 2:
            continue
            
        # Get final state
        final_line = lines[-1]
        final_data = json.loads(final_line)
        
        if 'winnerName' in final_data:
            winner = final_data['winnerName']
            if winner == 'claude-sonnet-4-5-20250929':
                wins += 1
                # Count turns
                for line in lines:
                    data = json.loads(line)
                    if 'turn' in data:
                        total_turns_won.append(data['turn'])
                        break
            elif winner == '':
                ties += 1
            else:
                losses += 1
                # Count turns for losses
                for line in lines:
                    data = json.loads(line)
                    if 'turn' in data:
                        total_turns_lost.append(data['turn'])
                        break
    
    print(f"=== Game Statistics ===")
    print(f"Total games: {len(sim_files)}")
    print(f"Wins: {wins} ({wins/len(sim_files)*100:.1f}%)")
    print(f"Losses: {losses} ({losses/len(sim_files)*100:.1f}%)")
    print(f"Ties: {ties} ({ties/len(sim_files)*100:.1f}%)")
    
    if total_turns_won:
        print(f"\nAverage turns in won games: {sum(total_turns_won)/len(total_turns_won):.1f}")
    if total_turns_lost:
        print(f"Average turns in lost games: {sum(total_turns_lost)/len(total_turns_lost):.1f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_games.py <round_number>")
        print("Example: python3 analyze_games.py 0")
        sys.exit(1)
    
    round_num = sys.argv[1]
    analyze_round(round_num)
