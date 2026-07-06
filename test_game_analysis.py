import json

def analyze_turn(filepath, target_turn):
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if data.get("turn") == target_turn:
                    return data
    return None

data = analyze_turn("/logs/rounds/1/sim_246.jsonl", 120)
print(json.dumps(data, indent=2))
