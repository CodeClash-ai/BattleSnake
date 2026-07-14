import os
import json

rounds_dir = "/logs/rounds"
for r in sorted(os.listdir(rounds_dir)):
    r_path = os.path.join(rounds_dir, r)
    if not os.path.isdir(r_path):
        continue
    sim_files = [f for f in os.listdir(r_path) if f.startswith("sim_") and f.endswith(".jsonl")]
    for sf in sorted(sim_files):
        path = os.path.join(r_path, sf)
        if os.path.getsize(path) == 0:
            continue
        with open(path) as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            data = json.loads(line)
            if "board" in data:
                snakes = data["board"].get("snakes", [])
                for s in snakes:
                    if s["name"] == "gemini-3-5-flash":
                        lat = s.get("latency")
                        if lat is not None:
                            try:
                                val = int(lat)
                                if val >= 200:
                                    print(f"OUR BOT Round {r} file {sf} turn {data['turn']}: latency is {lat}")
                            except ValueError:
                                pass
