import os
import json

rounds_dir = "/logs/rounds"
counts = {"out_of_bounds": 0, "self_collision": 0, "body_collision": 0, "head_to_head": 0, "starvation": 0, "unknown": 0}

for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            turns = []
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "board" in data:
                            turns.append(data)
            
            # Find when we died
            for i, turn in enumerate(turns):
                names = [s["name"] for s in turn["board"]["snakes"]]
                if "gemini-3-5-flash" not in names:
                    prev_turn = turns[i-1] if i > 0 else None
                    if prev_turn:
                        my_prev = next((s for s in prev_turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
                        if my_prev:
                            head = my_prev["head"]
                            health = my_prev["health"]
                            if health <= 1:
                                counts["starvation"] += 1
                                break
                            
                            # Let's find if we moved or what was the next board state.
                            # In Battlesnake, the next turn has the updated heads. But since we are removed,
                            # we can look at the other snakes' bodies, or walls, or our own previous body to see if we collided.
                            # Where did we move?
                            # Usually, we can check which move our snake made, but let's just see if our head position was out of bounds
                            # or collided with something.
                            # Wait, in the turn where we are dead, is our name in any elimination list? No, the game log might not have it.
                            # But we can reconstruct our move by finding the cell that would be occupied or looking at standard rules.
                            pass
                    break
print(counts)
