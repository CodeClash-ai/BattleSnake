import json
with open("/logs/rounds/1/sim_121.jsonl") as f:
    for line in f:
        data = json.loads(line)
        if "board" not in data:
            continue
        print(f"Turn {data.get('turn')}:")
        for s in data["board"].get("snakes", []):
            print(f"  {s['name']}: head=({s['head']['x']},{s['head']['y']}) len={s['length']} health={s['health']} body={[ (p['x'], p['y']) for p in s['body'] ]}")
