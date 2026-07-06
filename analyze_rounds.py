import os
import json

def analyze():
    rounds_dir = "/logs/rounds"
    if not os.path.exists(rounds_dir):
        print("No rounds directory found.")
        return
        
    for round_name in sorted(os.listdir(rounds_dir)):
        round_path = os.path.join(rounds_dir, round_name)
        if not os.path.isdir(round_path):
            continue
        results_file = os.path.join(round_path, "results.json")
        if os.path.exists(results_file):
            with open(results_file) as f:
                data = json.load(f)
                print(f"Round {round_name}: Winner = {data.get('winner')}, Scores = {data.get('scores')}")

if __name__ == "__main__":
    analyze()
