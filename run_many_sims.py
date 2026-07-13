import subprocess
import time
import re

server_process = subprocess.Popen(["python3", "main.py"])
time.sleep(1)

our_wins = 0
opp_wins = 0

try:
    for i in range(20):
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
        else:
            if "gemini-3-5-flash" in res.stderr and "opponent" not in res.stderr:
                our_wins += 1
            elif "opponent" in res.stderr and "gemini-3-5-flash" not in res.stderr:
                opp_wins += 1
            else:
                print("Unknown match result:")
                print(res.stderr)
finally:
    server_process.terminate()

print(f"Our wins: {our_wins}, Opponent wins: {opp_wins}")
