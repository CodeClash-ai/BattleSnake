import json
import os

failures = ["sim_112.jsonl", "sim_12.jsonl", "sim_14.jsonl", "sim_219.jsonl", "sim_248.jsonl"]

for fn in failures:
    path = os.path.join("/logs/rounds/0/", fn)
    print(f"\n==================== {fn} ====================")
    with open(path) as f:
        lines = f.readlines()
    
    gemini_present = True
    for idx, line in enumerate(lines):
        data = json.loads(line)
        if "board" not in data:
            continue
        snakes = data["board"].get("snakes", [])
        names = [s["name"] for s in snakes]
        if "gemini-3-5-flash" not in names and gemini_present:
            # It just died. Let's print the last few turns.
            start_idx = max(0, idx - 5)
            for j in range(start_idx, idx + 1):
                t_data = json.loads(lines[j])
                if "board" not in t_data:
                    continue
                print(f"Turn {t_data.get('turn')}:")
                for s in t_data["board"].get("snakes", []):
                    print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']}")
            gemini_present = False
