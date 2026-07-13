import subprocess
import time
import sys

# Start the game server in background
server_process = subprocess.Popen(["python3", "main.py"])
time.sleep(1)

try:
    # Run a Battlesnake local match
    # battlesnake play -W 11 -H 11 --name "gemini-3-5-flash" --url http://localhost:8000 --name "dummy" --url http://localhost:8000
    res = subprocess.run([
        "./game/battlesnake", "play",
        "-W", "11", "-H", "11",
        "--name", "gemini-3-5-flash", "--url", "http://localhost:8000",
        "--name", "opponent", "--url", "http://localhost:8000", # Using itself as opponent to test stability and self-play
        "-g", "standard"
    ], capture_output=True, text=True)
    print(res.stdout)
    print(res.stderr)
finally:
    server_process.terminate()
