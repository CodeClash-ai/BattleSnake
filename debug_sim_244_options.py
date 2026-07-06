import json

filepath = "/logs/rounds/1/sim_244.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 65:
                # Let's print out what the board state looks like and run our move function manually
                game_state = {
                    "game": {"id": "test"},
                    "turn": 65,
                    "board": data["board"],
                    "you": [s for s in data["board"]["snakes"] if s["name"] == "gemini-3-5-flash"][0]
                }
                
                from main import move
                res = move(game_state)
                print("Calculated move on Turn 65:", res)
