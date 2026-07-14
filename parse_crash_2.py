import json

with open("/logs/rounds/0/sim_10.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip()]

board_lines = [line for line in lines if "board" in line]
# Let us print specifically turn 169 and 170 to see what gemini chose or did.
# Wait, we can find the you object from the game frames.
for line in board_lines[-2:]:
    print("Turn:", line["turn"])
    print("  You:", line["you"]["name"], "head:", line["you"]["head"], "body len:", len(line["you"]["body"]))
    print("  You body:", line["you"]["body"])
    print("  Board snakes:")
    for s in line["board"]["snakes"]:
        print(f"    {s['name']}: head={s['head']} len={s['length']} body={s['body']}")
