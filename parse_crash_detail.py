import json

with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

for line in lines[135:141]:
    data = json.loads(line)
    if "board" in data:
        print(f"--- Turn {data['turn']} ---")
        for s in data["board"]["snakes"]:
            print(f"  {s['name']}: head={s['head']}")
            print(f"    body={s['body']}")
