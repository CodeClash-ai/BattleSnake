import json

filepath = "/logs/rounds/1/sim_210.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for t in turns:
    turn_num = t.get("turn")
    if turn_num == 228:
        my_snake = None
        for s in t["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
                break
        print("My Snake head:", my_snake["head"])
        print("Body:", my_snake["body"])
        print("Food:", t["board"]["food"])
