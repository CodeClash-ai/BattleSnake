import json

path = "/logs/rounds/0/sim_101.jsonl"
with open(path) as f:
    lines = f.readlines()

for line in lines:
    try:
        d = json.loads(line)
        turn = d["turn"]
        board = d["board"]
        width, height = board["width"], board["height"]
        my_snake = None
        for s in board["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
                break
        if not my_snake:
            continue
            
        head = (my_snake["head"]["x"], my_snake["head"]["y"])
        my_tail = (my_snake["body"][-1]["x"], my_snake["body"][-1]["y"])
        
        obstacle_positions = set()
        for s in board["snakes"]:
            body_segs = s["body"]
            is_growing = (s["health"] == 100)
            active_body = body_segs if is_growing else body_segs[:-1]
            for seg in active_body:
                obstacle_positions.add((seg["x"], seg["y"]))
                
        possible_moves = {
            "up": (head[0], head[1] + 1),
            "down": (head[0], head[1] - 1),
            "left": (head[0] - 1, head[1]),
            "right": (head[0] + 1, head[1])
        }
        
        safe_moves = {}
        for d_name, pos in possible_moves.items():
            if 0 <= pos[0] < width and 0 <= pos[1] < height:
                if pos not in obstacle_positions:
                    safe_moves[d_name] = pos
                    
        def analyze_move(start_pos):
            queue = [start_pos]
            visited = {start_pos}
            count = 0
            can_reach_tail = False
            while queue:
                curr = queue.pop(0)
                count += 1
                if curr == my_tail:
                    can_reach_tail = True
                if count > 120:
                    if can_reach_tail:
                        break
                for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
                    nx, ny = curr[0] + dx, curr[1] + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if (nx, ny) == my_tail or ((nx, ny) not in obstacle_positions and (nx, ny) not in visited):
                            visited.add((nx, ny))
                            queue.append((nx, ny))
            return count, can_reach_tail

        has_any_reach_tail = False
        for d_name, pos in safe_moves.items():
            _, can_reach = analyze_move(pos)
            if can_reach:
                has_any_reach_tail = True
        
        if not has_any_reach_tail and turn > 50:
            print(f"Turn {turn}: Tail is not reachable from ANY move!")
            break
    except Exception as e:
        print(e)
