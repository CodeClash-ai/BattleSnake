import json
with open("/workspace/test_main_new.py", "w") as f_out:
    pass # Let's first inspect sim_121.jsonl's exact last turn.
with open("/logs/rounds/1/sim_121.jsonl") as f:
    lines = f.readlines()
print("Total lines:", len(lines))
for line in lines[-3:]:
    data = json.loads(line)
    if "board" in data:
        print("Turn:", data.get("turn"))
        for s in data["board"].get("snakes", []):
            print(f"  {s['name']}: head=({s['head']['x']},{s['head']['y']})")
    else:
        print(data.keys())
