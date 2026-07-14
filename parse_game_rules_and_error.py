import json

with open("/logs/rounds/2/sim_0.jsonl", "r") as f:
    lines = f.readlines()

# Let's search for "error", "invalid", "shout", "timeout" or any final stdout/stderr
for line in lines[-20:]:
    try:
        obj = json.loads(line)
        if "error" in obj or "rules" in obj or "winner" in obj or "stdout" in obj or "stderr" in obj:
            print(line.strip()[:200])
    except Exception:
        print(line.strip()[:200])
