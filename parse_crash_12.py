import json

path = "/logs/rounds/0/sim_12.jsonl"
with open(path) as f:
    for line in f:
        try:
            d = json.loads(line)
            # Find last few turns
            print(f"Turn {d.get('turn')}:")
            for s in d["board"]["snakes"]:
                print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']}")
        except:
            pass
