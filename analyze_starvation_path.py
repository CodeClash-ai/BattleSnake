import json

# Let's inspect sim_141.jsonl turns 140 to 155 to see what our health was and why we did not eat food.
with open("/logs/rounds/0/sim_141.jsonl", "r") as f:
    lines = f.readlines()

for turn in range(130, 156):
    data = json.loads(lines[turn])
    you = data["you"]
    print(f"Turn {turn}: Head: ({you['head']['x']},{you['head']['y']}), Len: {you['length']}, Health: {you['health']}, Food: {data['board']['food']}")
