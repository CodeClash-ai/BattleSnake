# Native launcher for bobby-witt (tphummel/bobby-witt, Node.js, v1 API).
# Runs the ACTUAL original JS via its local.js runner (http server on $PORT). Zero npm deps.
# def stubs exist only for the arena's static validate_code.
import os, subprocess
def info(): pass
def start(game_state): pass
def move(game_state): pass
def end(game_state): pass
if __name__ == "__main__":
    subprocess.Popen(["node", "local.js"], cwd=os.path.dirname(os.path.abspath(__file__))).wait()
