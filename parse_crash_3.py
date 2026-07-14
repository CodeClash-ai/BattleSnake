import json

with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

for line in lines[139:142]:
    data = json.loads(line)
    if "board" in data:
        print(f"Turn {data['turn']}:")
        for s in data["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                print(f"  {s['name']}: {s['body']}")
