import json
import glob

# Analyze crashes in Round 1
sim_files = glob.glob("/logs/rounds/1/*.jsonl")

for path in sim_files:
    with open(path) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    if not lines:
        continue
    board_lines = [line for line in lines if "board" in line]
    if not board_lines:
        continue
    last_turn = board_lines[-1]
    alive_names = [s["name"] for s in last_turn["board"]["snakes"]]
    if "gemini-3-5-flash" not in alive_names:
        for idx in range(len(board_lines) - 1):
            curr_names = [s["name"] for s in board_lines[idx]["board"]["snakes"]]
            next_names = [s["name"] for s in board_lines[idx+1]["board"]["snakes"]]
            if "gemini-3-5-flash" in curr_names and "gemini-3-5-flash" not in next_names:
                gemini_snake = next(s for s in board_lines[idx]["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
                turn = board_lines[idx]["turn"]
                print(f"File {path.split('/')[-1]} Turn {turn} death: len={gemini_snake['length']} health={gemini_snake['health']} head={gemini_snake['head']}")
                # Print last 2 turns in detail
                for j in range(max(0, idx-1), min(idx+2, len(board_lines))):
                    t_data = board_lines[j]
                    print(f"  Turn {t_data['turn']}:")
                    for s in t_data["board"]["snakes"]:
                        print(f"    {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body']}")
                break
