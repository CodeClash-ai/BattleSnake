import json

def trace(filepath, target_turn):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
                    
    # Find target_turn
    for idx, turn in enumerate(turns):
        if turn["turn"] == target_turn:
            # Let's print our positions and opponent positions starting from 5 turns before
            start_idx = max(0, idx - 8)
            for i in range(start_idx, idx + 1):
                t = turns[i]
                my_snake = next((s for s in t["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
                opp_snake = next((s for s in t["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
                if my_snake and opp_snake:
                    print(f"Turn {t['turn']}:")
                    print(f"  My head: ({my_snake['head']['x']}, {my_snake['head']['y']}), health: {my_snake['health']}, body: {[(b['x'], b['y']) for b in my_snake['body']]}")
                    print(f"  Opp head: ({opp_snake['head']['x']}, {opp_snake['head']['y']}), health: {opp_snake['health']}, body: {[(b['x'], b['y']) for b in opp_snake['body']]}")

print("Trace sim_128:")
trace("/logs/rounds/0/sim_128.jsonl", 110)
