import json
import glob

# Search for loss/draw logs in Round 0
sim_files = glob.glob("/logs/rounds/0/*.jsonl")

for path in sim_files:
    with open(path) as f:
        lines = f.readlines()
    if not lines:
        continue
    # Let's find if "gemini-3-5-flash" ever disappears
    gemini_present = True
    label = path.split("/")[-1]
    
    for idx, line in enumerate(lines):
        try:
            data = json.loads(line)
        except Exception:
            continue
        if "board" not in data:
            continue
        names = [s["name"] for s in data["board"].get("snakes", [])]
        if "gemini-3-5-flash" not in names:
            # It died or wasn't there
            if idx > 1: # Let's ignore start of game config lines
                # The turn before it died
                print(f"\n==================== {label} died on turn {data.get('turn')} ====================")
                start_idx = max(0, idx - 4)
                for j in range(start_idx, min(idx + 2, len(lines))):
                    try:
                        t_data = json.loads(lines[j])
                    except Exception:
                        continue
                    if "board" not in t_data:
                        continue
                    print(f"Turn {t_data.get('turn')}:")
                    for s in t_data["board"].get("snakes", []):
                        print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body']}")
                break
