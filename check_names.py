import json
file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    for line in f:
        data = json.loads(line)
        if "board" in data:
            print([(s["name"], s["id"]) for s in data["board"]["snakes"]])
            break
