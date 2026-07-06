import json
filepath = "/logs/rounds/1/sim_219.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            t = json.loads(line)
            turn_num = t.get("turn")
            if turn_num is not None and 30 <= turn_num <= 36:
                my_snake = next(s for s in t["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
                opp_snake = next(s for s in t["board"]["snakes"] if s["name"] == "graeme-hill_snakebot")
                print(f"Turn {turn_num}: My head {my_snake['head']}, Opp head {opp_snake['head']}, Opp len {len(opp_snake['body'])}, My len {len(my_snake['body'])}")
