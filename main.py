# Native launcher for hettie (ChaelCodes/HettieCodes, Ruby/Sinatra, v1 API).
# Runs the ACTUAL original Sinatra app via rackup on $PORT. def stubs are only for the
# arena's static validate_code.
import os, subprocess
def info(): pass
def start(game_state): pass
def move(game_state): pass
def end(game_state): pass
if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    port = os.environ.get("PORT", "8000")
    subprocess.run(["bundle", "install", "--quiet"], cwd=here)
    subprocess.Popen(["bundle", "exec", "rackup", "-p", port, "-o", "0.0.0.0"], cwd=here).wait()
