import json

path = "/logs/rounds/1/sim_2.jsonl"
with open(path) as f:
    lines = [json.loads(line) for line in f if line.strip()]
board_lines = [line for line in lines if "board" in line]

for idx in range(len(board_lines) - 1):
    curr_names = [s["name"] for s in board_lines[idx]["board"]["snakes"]]
    next_names = [s["name"] for s in board_lines[idx+1]["board"]["snakes"]]
    if "gemini-3-5-flash" in curr_names and "gemini-3-5-flash" not in next_names:
        for j in range(max(0, idx-2), min(idx+2, len(board_lines))):
            t_data = board_lines[j]
            print(f"Turn {t_data['turn']}:")
            for s in t_data["board"]["snakes"]:
                print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body']}")
        break
