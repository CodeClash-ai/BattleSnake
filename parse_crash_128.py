import json

path = "/logs/rounds/0/sim_128.jsonl"
with open(path) as f:
    for line in f:
        try:
            d = json.loads(line)
            if d.get('turn', 0) >= 84:
                print(f"Turn {d.get('turn')}:")
                for s in d["board"]["snakes"]:
                    print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body']}")
        except:
            pass
