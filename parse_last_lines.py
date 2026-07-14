import json
import glob

sim_files = glob.glob("/logs/rounds/0/*.jsonl")

for path in sim_files:
    with open(path) as f:
        lines = f.readlines()
    if not lines:
        continue
    label = path.split("/")[-1]
    
    # We want to see the last 2 valid json lines in each file
    valid_lines = []
    for line in lines:
        try:
            data = json.loads(line)
            if "board" in data:
                valid_lines.append(data)
        except Exception:
            continue
            
    if len(valid_lines) >= 2:
        last = valid_lines[-1]
        prev = valid_lines[-2]
        
        # Check who won
        names_last = [s["name"] for s in last["board"].get("snakes", [])]
        if "gemini-3-5-flash" not in names_last:
            # We died or lost!
            print(f"=== {label} ended at turn {last['turn']}. Gemini died. ===")
            print(f"Prev Turn {prev['turn']}:")
            for s in prev["board"].get("snakes", []):
                print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body'][:4]}...")
            print(f"Last Turn {last['turn']}:")
            for s in last["board"].get("snakes", []):
                print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body'][:4]}...")
            print("-" * 50)
