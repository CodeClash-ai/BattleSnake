import os
import json

round_dir = "/logs/rounds/2"
sim_files = [os.path.join(round_dir, f) for f in os.listdir(round_dir) if f.endswith(".jsonl") and os.path.getsize(os.path.join(round_dir, f)) > 0]

turns_with_timeouts = {}
for filepath in sim_files:
    with open(filepath, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "board" in obj:
                    for s in obj["board"]["snakes"]:
                        if s["name"] == "gemini-3-5-flash" and s["latency"] != "":
                            latency = int(s["latency"])
                            if latency >= 500:
                                turns_with_timeouts[obj["turn"]] = turns_with_timeouts.get(obj["turn"], 0) + 1
            except Exception:
                pass

print("Turns with high latency/timeouts:")
for turn, count in sorted(turns_with_timeouts.items()):
    print(f"Turn {turn}: {count} times")
