import json

path = "/logs/rounds/0/sim_101.jsonl"
with open(path) as f:
    lines = f.readlines()

for line in lines:
    try:
        d = json.loads(line)
        if d.get("turn") == 58:
            for s in d["board"]["snakes"]:
                if s["name"] == "gemini-3-5-flash":
                    print("Turn 58 Gemini head:", s["head"])
                    print("Turn 58 Gemini tail:", s["body"][-1])
                    print("Turn 58 Gemini length:", s["length"])
    except:
        pass
