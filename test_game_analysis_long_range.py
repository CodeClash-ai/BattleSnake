import os
import json

rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl") and os.path.getsize(os.path.join(round_path, filename)) > 0:
            filepath = os.path.join(round_path, filename)
            turns = []
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "board" in data:
                            turns.append(data)
            
            # Find when gemini-3-5-flash died
            died_turn = None
            for idx, turn in enumerate(turns):
                names = [s["name"] for s in turn["board"]["snakes"]]
                if "gemini-3-5-flash" not in names:
                    died_turn = turn["turn"]
                    break
            
            if died_turn is not None and died_turn > 10:
                # Print options for last 10 turns before death
                print(f"\nRound {round_name} {filename} Death at Turn {died_turn}")
                for target_turn in range(died_turn - 10, died_turn):
                    turn_data = next((t for t in turns if t["turn"] == target_turn), None)
                    if turn_data:
                        my_prev = next((s for s in turn_data["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
                        if my_prev:
                            head = my_prev["head"]
                            width, height = turn_data["board"]["width"], turn_data["board"]["height"]
                            occupied = set()
                            for s in turn_data["board"]["snakes"]:
                                is_growing = s["health"] == 100
                                for i, seg in enumerate(s["body"]):
                                    if i == len(s["body"]) - 1 and not is_growing and len(s["body"]) > 1:
                                        continue
                                    occupied.add((seg["x"], seg["y"]))
                            
                            options = []
                            from main import flood_fill_size
                            for d, (dx, dy) in [("up", (0, 1)), ("down", (0, -1)), ("left", (-1, 0)), ("right", (1, 0))]:
                                pos = (head["x"] + dx, head["y"] + dy)
                                if 0 <= pos[0] < width and 0 <= pos[1] < height:
                                    if pos not in occupied:
                                        room = flood_fill_size(pos, occupied, width, height)
                                        options.append(f"{d} (room: {room})")
                            print(f"  Turn {target_turn}: head {head}, len {len(my_prev['body'])}, choices: {options}")
