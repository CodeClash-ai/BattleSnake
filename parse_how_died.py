import json, os

round_dir = "/logs/rounds/1"
sim_files = [os.path.join(round_dir, f) for f in os.listdir(round_dir) if f.endswith(".jsonl")]

for filepath in sim_files:
    with open(filepath, "r") as f:
        lines = f.readlines()
        if not lines:
            continue
        last_turn_data = None
        for line in reversed(lines):
            try:
                obj = json.loads(line)
                if "board" in obj:
                    last_turn_data = obj
                    break
            except Exception:
                pass
        if last_turn_data:
            snakes = last_turn_data["board"]["snakes"]
            alive_names = [s["name"] for s in snakes]
            if "nbw__nbw-ruby" in alive_names and "gemini-3-5-flash" not in alive_names:
                # Find the turn where we died
                all_turns = []
                for line in lines:
                    try:
                        obj = json.loads(line)
                        if "board" in obj:
                            all_turns.append(obj)
                    except:
                        pass
                for idx in range(len(all_turns) - 1):
                    t_curr = all_turns[idx]
                    t_next = all_turns[idx+1]
                    my_curr = [s for s in t_curr["board"]["snakes"] if s["name"] == "gemini-3-5-flash"]
                    my_next = [s for s in t_next["board"]["snakes"] if s["name"] == "gemini-3-5-flash"]
                    if my_curr and not my_next:
                        print(f"File {os.path.basename(filepath)} died at Turn {t_curr['turn']} -> {t_next['turn']}")
                        print(f"  My head at {t_curr['turn']}: {my_curr[0]['head']}")
                        print(f"  Opp head at {t_curr['turn']}: {[s['head'] for s in t_curr['board']['snakes'] if s['name'] != 'gemini-3-5-flash'][0]}")
                        # Let's print my body segments to see if we crashed into ourself or opponent or wall
                        print(f"  My body segments: {my_curr[0]['body']}")
                        opp_body = [s['body'] for s in t_curr['board']['snakes'] if s['name'] != 'gemini-3-5-flash'][0]
                        print(f"  Opp body segments: {opp_body}")
                        print(f"  Food: {t_curr['board']['food']}")
                        break
