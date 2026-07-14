import json
import glob

sim_files = glob.glob("/logs/rounds/0/*.jsonl")
lengths = []

for path in sim_files:
    with open(path) as f:
        lines = f.readlines()
    if not lines: continue
    
    # We want to see how long our snake gets
    max_len = 0
    for line in lines:
        try:
            data = json.loads(line)
            if "board" in data:
                for s in data["board"]["snakes"]:
                    if s["name"] == "gemini-3-5-flash":
                        max_len = max(max_len, s["length"])
        except:
            pass
    lengths.append(max_len)

print(f"Max length reached by gemini: {max(lengths)}")
print(f"Average max length: {sum(lengths)/len(lengths):.2f}")
