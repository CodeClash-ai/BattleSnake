import json

files = [("sim_135.jsonl", 123), ("sim_168.jsonl", 261), ("sim_185.jsonl", 149), ("sim_68.jsonl", 73), ("sim_90.jsonl", 43)]

for filename, target_turn in files:
    filepath = f"/logs/rounds/0/{filename}"
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
    
    # We want to print detail from target_turn - 2 to target_turn
    print(f"\n=================== {filename} ===================")
    for t in turns:
        turn_num = t.get("turn")
        if turn_num is not None and target_turn - 2 <= turn_num <= target_turn:
            print(f"--- Turn {turn_num} ---")
            for snake in t["board"]["snakes"]:
                name = snake["name"]
                head = snake["head"]
                length = len(snake["body"])
                health = snake["health"]
                body_coords = [(seg["x"], seg["y"]) for seg in snake["body"]]
                print(f"  {name} head: {head} length: {length} health: {health}")
                print(f"    body: {body_coords}")
