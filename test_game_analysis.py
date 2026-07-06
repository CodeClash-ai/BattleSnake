import json

with open("test_game.json") as f:
    lines = f.readlines()

for line in lines:
    try:
        data = json.loads(line)
        if "turn" in data and data["turn"] in [54, 55]:
            print("Turn:", data["turn"], "You ID:", data["you"]["id"])
            for s in data["board"]["snakes"]:
                print("  Name:", s["name"], "ID:", s["id"], "Head:", s["head"])
                print("  Body:", s["body"])
    except Exception as e:
        pass
