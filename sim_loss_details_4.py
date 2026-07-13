import json

log_path = "/workspace/../logs/rounds/1/results.json"
with open(log_path, 'r') as f:
    data = json.load(f)
print(json.dumps(data, indent=2))
