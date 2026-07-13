import subprocess
import json
import time

def run_single_game():
    cmd = [
        "/workspace/game/battlesnake", "play",
        "-W", "11", "-H", "11",
        "-n", "gemini-3-5-flash", "-u", "http://localhost:8000",
        "-n", "ChaelCodes__cornelius", "-u", "http://localhost:8001",
        "-o", "test_game_output.json"
    ]
    # We need server processes running!
    # Let's see if we can launch them in the background, run the command, and kill them.
    # But since it's just a verification run, we can write a quick python script to test.
    pass
