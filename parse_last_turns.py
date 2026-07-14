import json

paths = [
    ("/logs/rounds/0/sim_104.jsonl", "sim_104"),
    ("/logs/rounds/0/sim_42.jsonl", "sim_42"),
    ("/logs/rounds/1/sim_122.jsonl", "sim_122"),
    ("/logs/rounds/1/sim_198.jsonl", "sim_198"),
    ("/logs/rounds/1/sim_26.jsonl", "sim_26")
]

for path, label in paths:
    print(f"\n==================== {label} ====================")
    with open(path) as f:
        lines = f.readlines()
    
    # We want to trace gemini-3-5-flash leading up to its death.
    # Let's find where gemini-3-5-flash is no longer present.
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
                    print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body']}")
            gemini_present = False
