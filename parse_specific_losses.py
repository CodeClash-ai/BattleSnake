import json

# Let's inspect sim_119.jsonl, sim_128.jsonl, sim_135.jsonl, sim_15.jsonl, sim_171.jsonl
files = ["sim_119.jsonl", "sim_128.jsonl", "sim_135.jsonl", "sim_15.jsonl", "sim_171.jsonl"]

for fname in files:
    path = f"/logs/rounds/0/{fname}"
    with open(path) as f:
        lines = f.readlines()
    print(f"\n==================== {fname} ====================")
    # Print last 3 turns
    valid = []
    for line in lines:
        try:
            d = json.loads(line)
            if "board" in d:
                valid.append(d)
        except:
            continue
    for turn_data in valid[-3:]:
        print(f"Turn {turn_data['turn']}:")
        for s in turn_data["board"]["snakes"]:
            print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body']}")
