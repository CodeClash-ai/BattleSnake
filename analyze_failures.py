import json

filepath = "/logs/rounds/1/sim_246.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

print("Total turns:", len(turns))
# turn 120 is index 120 (since we start at turn 0)
for idx in range(118, 122):
    if idx < len(turns):
        t = turns[idx]
        print(f"Turn {t.get('turn')}:")
        if "board" in t:
            for s in t["board"]["snakes"]:
                print(f"  {s['name']}: head={s['head']}, health={s['health']}, body_len={len(s['body'])}")

print("\nDetail of Turn 120 and 121:")
t120 = turns[121] # index 121 corresponds to turn 120
print("Turn 120 snakes:")
for s in t120["board"]["snakes"]:
    print(s["name"], s["body"])

t121 = turns[122] # index 122 corresponds to turn 121 / or winner line
print("Line 122 keys:", t121.keys())
if "board" in t121:
    print("Turn 121 snakes:")
    for s in t121["board"]["snakes"]:
        print(s["name"], s["body"])
else:
    print(t121)
