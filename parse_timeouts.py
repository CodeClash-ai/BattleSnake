import os
import json

round_dir = "/logs/rounds/2"
sim_files = [os.path.join(round_dir, f) for f in os.listdir(round_dir) if f.endswith(".jsonl") and os.path.getsize(os.path.join(round_dir, f)) > 0]

timeouts = []
for filepath in sim_files:
    with open(filepath, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "board" in obj:
                    for s in obj["board"]["snakes"]:
                        if s["name"] == "gemini-3-5-flash" and s["latency"] != "" and int(s["latency"]) >= 500:
                            timeouts.append((os.path.basename(filepath), obj["turn"], s["latency"]))
            except Exception:
                pass

print(f"Total latency >= 500ms instances: {len(timeouts)}")
for t in sorted(timeouts)[:20]:
    print(t)
