import json

with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

for turn_num in [135, 136, 137, 138, 139]:
    data = json.loads(lines[turn_num + 1]) # Index line offset
    board = data["board"]
    for s in board["snakes"]:
        if s["name"] == "gemini-3-5-flash":
            head = (s["head"]["x"], s["head"]["y"])
            body = [(seg["x"], seg["y"]) for seg in s["body"]]
            print(f"Turn {turn_num}: Head={head}")
            for d, pos in [("up", (head[0], head[1]+1)), ("down", (head[0], head[1]-1)), ("left", (head[0]-1, head[1])), ("right", (head[0]+1, head[1]))]:
                in_body = pos in body
                print(f"  {d}: {pos} in_body={in_body}")
