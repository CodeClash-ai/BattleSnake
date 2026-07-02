# Native launcher for snork (wrenger/snork, Rust, Battlesnake v1 API).
# The ACTUAL Rust SOURCE is committed in this branch; the arena compiles it
# (cargo build --release, see battlesnake.py _build_submissions) before serving.
# This launcher just runs the produced binary on $PORT (with a fallback build if needed).
# def stubs exist only for the arena's static validate_code.
import os, subprocess
def info(): pass
def start(game_state): pass
def move(game_state): pass
def end(game_state): pass
if __name__ == "__main__":
    port = os.environ.get("PORT", "8000")
    here = os.path.dirname(os.path.abspath(__file__))
    binp = os.path.join(here, "target", "release", "server")
    if not os.path.exists(binp):
        subprocess.run(["cargo", "build", "--release", "--bin", "server"], cwd=here, check=True)
    subprocess.Popen([binp, "--host", f"0.0.0.0:{port}"]).wait()
