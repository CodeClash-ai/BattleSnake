import json

path = "/logs/rounds/0/sim_139.jsonl"
with open(path) as f:
    lines = f.readlines()

for line in lines:
    try:
        d = json.loads(line)
        if d.get("turn") == 184:
            for s in d["board"]["snakes"]:
                if s["name"] == "gemini-3-5-flash":
                    print("Turn 184 Gemini head:", s["head"])
                    print("Turn 184 Gemini body:", s["body"])
    except:
        pass
