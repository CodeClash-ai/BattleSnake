#!/usr/bin/env python3
import json
import os
import sys

def analyze_game(game_file):
    """Analyze a single game file."""
    with open(game_file, 'r') as f:
        lines = f.readlines()
    
    if len(lines) < 3:
        return None
    
    # Last line is result, second-to-last is final game state
    result_line = json.loads(lines[-1])
    last_state = json.loads(lines[-2])
    
    # Determine outcome from result
    our_id = last_state['you']['id']
    
    if result_line.get('isDraw', False):
        outcome = 'TIE'
    elif result_line.get('winnerId') == our_id:
        outcome = 'WIN'
    else:
        outcome = 'LOSS'
    
    # Find our snake and opponent in final state
    our_snake = None
    opponent_snake = None
    
    for snake in last_state['board']['snakes']:
        if snake['id'] == our_id:
            our_snake = snake
        else:
            opponent_snake = snake
    
    return {
        'file': game_file,
        'outcome': outcome,
        'turn': last_state['turn'],
        'our_length': len(our_snake['body']) if our_snake else 0,
        'opp_length': len(opponent_snake['body']) if opponent_snake else 0,
        'our_health': our_snake['health'] if our_snake else 0,
        'opp_health': opponent_snake['health'] if opponent_snake else 0
    }

def main():
    round_num = sys.argv[1] if len(sys.argv) > 1 else '9'
    round_dir = f'/logs/rounds/{round_num}'
    
    results = []
    game_files = [f for f in os.listdir(round_dir) if f.startswith('sim_') and f.endswith('.jsonl')]
    
    for game_file in sorted(game_files, key=lambda x: int(x.split('_')[1].split('.')[0])):
        result = analyze_game(os.path.join(round_dir, game_file))
        if result:
            results.append(result)
    
    # Count outcomes
    wins = sum(1 for r in results if r['outcome'] == 'WIN')
    losses = sum(1 for r in results if r['outcome'] == 'LOSS')
    ties = sum(1 for r in results if r['outcome'] == 'TIE')
    
    print(f"Round {round_num} Results:")
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Ties: {ties}")
    print(f"  Total: {len(results)}")
    print(f"  Win Rate: {wins/len(results)*100:.1f}%")
    print()
    
    # Analyze losses
    print("Loss Analysis:")
    loss_games = [r for r in results if r['outcome'] == 'LOSS']
    
    if loss_games:
        print(f"  Total Losses: {len(loss_games)}")
        
        # Check if we were longer when we lost
        longer_losses = [r for r in loss_games if r['our_length'] > r['opp_length']]
        print(f"  Losses when we were LONGER: {len(longer_losses)}")
        
        # Show some examples
        print("\n  Sample losses:")
        for i, loss in enumerate(loss_games[:10]):
            print(f"    {os.path.basename(loss['file'])}: Turn {loss['turn']}, Our length: {loss['our_length']}, Opp length: {loss['opp_length']}")
    
    print()
    
    # Analyze wins
    print("Win Analysis:")
    win_games = [r for r in results if r['outcome'] == 'WIN']
    if win_games:
        avg_win_turn = sum(r['turn'] for r in win_games) / len(win_games)
        avg_win_length = sum(r['our_length'] for r in win_games) / len(win_games)
        print(f"  Average win turn: {avg_win_turn:.1f}")
        print(f"  Average win length: {avg_win_length:.1f}")

if __name__ == '__main__':
    main()
