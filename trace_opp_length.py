import json

def trace_lengths(filepath):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
                    
    for turn in turns:
        my_snake = next((s for s in turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
        opp_snake = next((s for s in turn["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
        if my_snake and opp_snake:
            if abs(len(my_snake["body"]) - len(opp_snake["body"])) > 2:
                # Let's see at what turn we got significantly outgrown
                print(f"Turn {turn['turn']}: My len {len(my_snake['body'])}, Opp len {len(opp_snake['body'])}")
                break

print("Length difference check:")
trace_lengths("/logs/rounds/0/sim_128.jsonl")
