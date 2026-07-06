import json

filepath = "/logs/rounds/1/sim_244.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 61:
                print("YOU dict keys:", data["you"].keys())
                print("YOU identity info:", data["you"]["id"], data["you"]["name"])
