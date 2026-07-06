import json

def trace_longer(filepath, start_turn, end_turn):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
                    
    for turn in turns:
        if start_turn <= turn["turn"] <= end_turn:
            my_snake = next((s for s in turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
            opp_snake = next((s for s in turn["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
            if my_snake and opp_snake:
                print(f"Turn {turn['turn']}:")
                print(f"  My head: ({my_snake['head']['x']}, {my_snake['head']['y']}), body: {[(b['x'], b['y']) for b in my_snake['body']]}")
                print(f"  Opp head: ({opp_snake['head']['x']}, {opp_snake['head']['y']}), body: {[(b['x'], b['y']) for b in opp_snake['body']]}")

print("Trace sim_128:")
trace_longer("/logs/rounds/0/sim_128.jsonl", 90, 103)
