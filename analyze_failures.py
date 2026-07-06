import json
import os

def analyze_file(filepath):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
    
    # We find where gemini-3-5-flash disappeared
    for idx, turn in enumerate(turns):
        names = [s["name"] for s in turn["board"]["snakes"]]
        if "gemini-3-5-flash" not in names:
            # Died at this turn (idx). Let's see the previous turn.
            if idx > 0:
                prev = turns[idx-1]
                my_snake = next(s for s in prev["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
                opp_snake = next((s for s in prev["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
                
                print(f"--- FAILURE IN {os.path.basename(filepath)} at Turn {prev['turn']} ---")
                print(f"My head: {my_snake['head']}, length: {len(my_snake['body'])}, health: {my_snake['health']}")
                if opp_snake:
                    print(f"Opponent head: {opp_snake['head']}, length: {len(opp_snake['body'])}, health: {opp_snake['health']}")
                
                print("My body:", [(b['x'], b['y']) for b in my_snake['body']])
                if opp_snake:
                    print("Opponent body:", [(b['x'], b['y']) for b in opp_snake['body']])
                print("Food:", [(f['x'], f['y']) for f in prev['board']['food']])
            break

failures = ["sim_128.jsonl", "sim_131.jsonl", "sim_154.jsonl", "sim_195.jsonl", "sim_221.jsonl", "sim_223.jsonl", "sim_27.jsonl"]
for f in failures:
    analyze_file(os.path.join("/logs/rounds/0", f))
