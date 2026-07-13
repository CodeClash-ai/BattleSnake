import subprocess
import time
import re

server_process = subprocess.Popen(["python3", "main.py"])
time.sleep(1)

our_wins = 0
opp_wins = 0

try:
    for i in range(50):
        res = subprocess.run([
            "./game/battlesnake", "play",
            "-W", "11", "-H", "11",
            "--name", "gemini-3-5-flash", "--url", "http://localhost:8000",
            "--name", "opponent", "--url", "http://localhost:8000",
            "-g", "standard"
        ], capture_output=True, text=True)
        # Find winner in output
        match = re.search(r"Game completed after \d+ turns. (.*) was the winner.", res.stderr)
        if match:
            winner = match.group(1)
            if winner == "gemini-3-5-flash":
                our_wins += 1
            else:
                opp_wins += 1
finally:
    server_process.terminate()

print(f"50 Games run: Our wins: {our_wins}, Opponent wins: {opp_wins}")
