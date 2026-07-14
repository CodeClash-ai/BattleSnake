import json
import glob

sim_files = glob.glob("/logs/rounds/0/*.jsonl")

reasons = {}

for path in sim_files:
    with open(path) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    if not lines:
        continue
    board_lines = [line for line in lines if "board" in line]
    if not board_lines:
        continue
    # Let's see who is alive on the last Turn and who is not.
    last_turn = board_lines[-1]
    alive_names = [s["name"] for s in last_turn["board"]["snakes"]]
    if "gemini-3-5-flash" not in alive_names:
        # Gemini died! Let's find why.
        # Find the frame where gemini is still in the board but absent in the next.
        for idx in range(len(board_lines) - 1):
            curr_names = [s["name"] for s in board_lines[idx]["board"]["snakes"]]
            next_names = [s["name"] for s in board_lines[idx+1]["board"]["snakes"]]
            if "gemini-3-5-flash" in curr_names and "gemini-3-5-flash" not in next_names:
                # Gemini died on the transition to next turn. Let's find its snake data in curr
                gemini_snake = next(s for s in board_lines[idx]["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
                # Look at turn index
                turn = board_lines[idx]["turn"]
                print(f"File {path.split('/')[-1]} Turn {turn} death: len={gemini_snake['length']} health={gemini_snake['health']} head={gemini_snake['head']}")
                break
