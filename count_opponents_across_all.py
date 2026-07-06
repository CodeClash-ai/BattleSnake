import os
import json

rounds_dir = "/logs/rounds"
opps = set()

for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "board" in data:
                            for s in data["board"]["snakes"]:
                                if s["name"] != "gemini-3-5-flash":
                                    opps.add(s["name"])

print(opps)
