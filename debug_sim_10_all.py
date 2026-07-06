import json

with open("/logs/rounds/2/sim_10.jsonl") as f:
    for line in f:
        data = json.loads(line)
        if "turn" in data and data["turn"] is not None:
            turn = data["turn"]
            snakes = {s["name"]: s for s in data["board"]["snakes"]}
            if "gemini-3-5-flash" in snakes and "nbw_nbw-crystal" in snakes:
                g = snakes["gemini-3-5-flash"]
                c = snakes["nbw_nbw-crystal"]
                print(f"Turn {turn}:")
                print(f"  Gemini: Head {g['head']}, Length {g['length']}, Body {g['body']}")
                print(f"  Crystal: Head {c['head']}, Length {c['length']}, Body {c['body']}")
