import json
import os

failures = ["sim_112.jsonl", "sim_12.jsonl", "sim_14.jsonl", "sim_219.jsonl", "sim_248.jsonl"]

for fn in failures:
    path = os.path.join("/logs/rounds/0/", fn)
    print(f"\n==================== {fn} ====================")
    with open(path) as f:
        lines = f.readlines()
    
    # We want to see the move decision that led to death.
    # The last turn gemini is alive is the one before it disappears.
    gemini_idx = -1
    for idx, line in enumerate(lines):
        data = json.loads(line)
        if "board" not in data:
            continue
        snakes = data["board"].get("snakes", [])
        names = [s["name"] for s in snakes]
        if "gemini-3-5-flash" in names:
            gemini_idx = idx

    if gemini_idx != -1:
        # Print state at gemini_idx (the last turn it was alive and had to make a decision)
        t_data = json.loads(lines[gemini_idx])
        print(f"Turn {t_data.get('turn')} state:")
        for s in t_data["board"].get("snakes", []):
            if s["name"] == "gemini-3-5-flash":
                print(f"  gemini head: {s['head']}")
                print(f"  gemini body: {s['body']}")
            else:
                print(f"  {s['name']} head: {s['head']}")
                print(f"  {s['name']} body: {s['body']}")
