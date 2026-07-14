import json
import glob

# Search for loss/draw logs in Round 0
sim_files = glob.glob("/logs/rounds/0/*.jsonl")

for path in sim_files:
    with open(path) as f:
        lines = f.readlines()
    if not lines:
        continue
    # Check if we won or lost. We look at the last state
    last_state = json.loads(lines[-1])
    if "board" not in last_state:
        continue
    snakes = last_state["board"].get("snakes", [])
    alive_names = [s["name"] for s in snakes]
    if "gemini-3-5-flash" not in alive_names:
        label = path.split("/")[-1]
        print(f"\n==================== {label} ====================")
        gemini_present = True
        for idx, line in enumerate(lines):
            data = json.loads(line)
            if "board" not in data:
                continue
            names = [s["name"] for s in data["board"].get("snakes", [])]
            if "gemini-3-5-flash" not in names and gemini_present:
                # It just died. Let's print the last few turns.
                start_idx = max(0, idx - 4)
                for j in range(start_idx, min(idx + 2, len(lines))):
                    t_data = json.loads(lines[j])
                    if "board" not in t_data:
                        continue
                    print(f"Turn {t_data.get('turn')}:")
                    for s in t_data["board"].get("snakes", []):
                        print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']}")
                gemini_present = False
