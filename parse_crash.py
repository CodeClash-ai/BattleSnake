import json
import glob

sim_files = glob.glob("/logs/rounds/0/*.jsonl")

for path in sim_files:
    with open(path) as f:
        lines = f.readlines()
    if not lines:
        continue
    label = path.split("/")[-1]
    
    # We want to inspect why gemini died. Let's find the turn where gemini had no moves or crashed, etc.
    # We can parse the log lines.
    for idx, line in enumerate(lines):
        try:
            data = json.loads(line)
        except Exception:
            continue
        if "board" not in data:
            continue
        turn = data.get("turn")
        snakes = data["board"].get("snakes", [])
        names = [s["name"] for s in snakes]
        
        # Check if gemini is in this turn, but gone in the next turn
        if "gemini-3-5-flash" in names:
            # Let's see if the next turn exists and does not contain gemini
            next_turn_has_gemini = False
            if idx + 1 < len(lines):
                try:
                    next_data = json.loads(lines[idx+1])
                    if "board" in next_data:
                        next_names = [s["name"] for s in next_data["board"].get("snakes", [])]
                        if "gemini-3-5-flash" in next_names:
                            next_turn_has_gemini = True
                except:
                    pass
            else:
                # Last line of the file, meaning gemini lived till the end or game ended
                next_turn_has_gemini = True
            
            if not next_turn_has_gemini:
                # Gemini died after this turn! Let's examine what happened.
                print(f"--- Gemini died after Turn {turn} in {label} ---")
                my_snake = [s for s in snakes if s["name"] == "gemini-3-5-flash"][0]
                opp_snakes = [s for s in snakes if s["name"] != "gemini-3-5-flash"]
                print(f"My head: {my_snake['head']}, length: {my_snake['length']}, health: {my_snake['health']}")
                print(f"My body: {my_snake['body']}")
                for os in opp_snakes:
                    print(f"Opponent {os['name']} head: {os['head']}, length: {os['length']}, health: {os['health']}")
                    print(f"Opponent body: {os['body']}")
                
                # Let's see what the actual next turn contains if it exists
                if idx + 1 < len(lines):
                    try:
                        next_data = json.loads(lines[idx+1])
                        print(f"Next turn {next_data.get('turn')} snakes:")
                        for s in next_data["board"].get("snakes", []):
                            print(f"  {s['name']} head: {s['head']}")
                    except Exception as e:
                        print("Could not parse next turn:", e)
                break
