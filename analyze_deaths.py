import json

with open("/logs/rounds/0/sim_0.jsonl", "r") as f:
    lines = f.readlines()

print("GAME SIM 0 DEATH DETAILS:")
# let's look at last few turns
for i in range(-5, 0):
    turn_data = json.loads(lines[i])
    if "board" in turn_data:
        turn = turn_data.get("turn")
        snakes = turn_data["board"]["snakes"]
        you = turn_data.get("you")
        print(f"Turn {turn}:")
        print(f"  Snakes left: {len(snakes)}")
        for s in snakes:
            print(f"    {s['name']}: head={s['head']}, len={s['length']}, health={s['health']}")
        if you:
            print(f"    US: head={you['head']}, len={you['length']}, health={you['health']}")
            # let's print us body
            print(f"    US body: {you['body']}")
    else:
        print(f"End state: {turn_data}")

# Let's print our moves on Turn 206
print("\nTurn 206 detailed snakes:")
turn_data = json.loads(lines[-3])
print(json.dumps(turn_data["board"], indent=2))
