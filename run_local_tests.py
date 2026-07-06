# Let's run any existing python test scripts
import subprocess

for script in ["test_flood_fill.py", "test_main.py", "test_game_analysis.py"]:
    print(f"Running {script}...")
    res = subprocess.run(["python3", script], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"{script} FAILED with code {res.returncode}")
        print(res.stderr)
