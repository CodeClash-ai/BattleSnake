import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    data = json.loads(line)
    if "board" in data:
        you = data["you"]
        if you["name"] == "gemini-3-5-flash":
            print(f"Turn {data['turn']}: head {you['head']}")
        else:
            # Maybe we are not "you" in the log?
            # In Battlesnake server logs, "you" can be different depending on who requested the log or how it was saved.
            # But "board" contains all snakes!
            for s in data["board"]["snakes"]:
                if s["name"] == "gemini-3-5-flash":
                    print(f"Turn {data['turn']}: gemini head {s['head']}")
