import os
import json

log_dir = "/logs/rounds/2/"
h2h_losses = 0
starve_losses = 0
body_losses = 0
out_of_bounds = 0
total_analyzed = 0

for f_name in sorted(os.listdir(log_dir)):
    if not f_name.endswith('.jsonl'):
        continue
    with open(os.path.join(log_dir, f_name)) as f:
        lines = f.readlines()
    
    # Let's find the turn where we disappear
    us_last_seen = None
    turn_num = -1
    for line in lines:
        try:
            data = json.loads(line)
            if 'board' in data:
                snakes = data['board']['snakes']
                us_alive = any(s['name'] == 'gemini-3-5-flash' for s in snakes)
                if us_alive:
                    us_last_seen = data
                    turn_num = data['turn']
                else:
                    break
        except Exception:
            pass
            
    if us_last_seen is not None:
        total_analyzed += 1
        # Let's see what happened in the turn immediately after turn_num
        # Let's find the turn turn_num + 1
        next_turn_data = None
        for line in lines:
            try:
                data = json.loads(line)
                if 'board' in data and data['turn'] == turn_num + 1:
                    next_turn_data = data
                    break
            except Exception:
                pass
        
        us_s = [s for s in us_last_seen['board']['snakes'] if s['name'] == 'gemini-3-5-flash'][0]
        opp_s = [s for s in us_last_seen['board']['snakes'] if s['name'] != 'gemini-3-5-flash']
        
        # Check starvation
        if us_s['health'] <= 1:
            starve_losses += 1
            continue
            
        if next_turn_data:
            # Let's check if the opponent has won/is still alive
            opp_next = [s for s in next_turn_data['board']['snakes'] if s['name'] != 'gemini-3-5-flash']
            if opp_next:
                opp_head = opp_next[0]['head']
                # If opponent's next head matches any possible move we could make, and we had equal/less length:
                # We could have collided head-to-head.
                # Let's see if opponent's head at turn_num + 1 is adjacent to us_s['head']
                dist_heads = abs(opp_head['x'] - us_s['head']['x']) + abs(opp_head['y'] - us_s['head']['y'])
                if dist_heads <= 2:
                    h2h_losses += 1
                else:
                    body_losses += 1
            else:
                body_losses += 1

print(f"Total Analyzed: {total_analyzed}")
print(f"Starve Losses: {starve_losses}")
print(f"H2H Losses (est): {h2h_losses}")
print(f"Body/Wall/Other Losses: {body_losses}")
