import json
import glob

sim_files = glob.glob("/logs/rounds/0/*.jsonl")

longest_match = 0
longest_match_path = ""

for path in sim_files:
    with open(path) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    if not lines:
        continue
    board_lines = [line for line in lines if "board" in line]
    if len(board_lines) > longest_match:
        longest_match = len(board_lines)
        longest_match_path = path

print("Longest match:", longest_match, "Path:", longest_match_path)
