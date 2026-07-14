import json
import os
import glob

def analyze():
    print("--- Battlesnake Game Logs Analysis ---")
    results_path = "/logs/rounds/0/results.json"
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            data = json.load(f)
            print(f"Round Number: {data.get('round_num')}")
            print(f"Winner: {data.get('winner')}")
            print("Scores:")
            for player, score in data.get("scores", {}).items():
                print(f"  - {player}: {score}")
            print("\nPlayer Stats:")
            for player, stats in data.get("player_stats", {}).items():
                print(f"  - {player}: Valid submit={stats.get('valid_submit')}, Score={stats.get('score')}")
    else:
        print("No results.json file found.")

    sims = glob.glob("/logs/rounds/0/sim_*.jsonl")
    non_empty_sims = [s for s in sims if os.path.getsize(s) > 0]
    print(f"\nTotal simulation files found: {len(sims)}")
    print(f"Non-empty simulation files: {len(non_empty_sims)}")
    
    if non_empty_sims:
        durations = []
        for sim in non_empty_sims:
            with open(sim, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    try:
                        end_data = json.loads(last_line)
                        if "turn" in end_data:
                            durations.append(end_data["turn"])
                        elif "game" in end_data and "turn" in end_data:
                            durations.append(end_data["turn"])
                        else:
                            # Try to find game duration by counting lines
                            durations.append(len(lines) - 2)
                    except Exception:
                        durations.append(len(lines) - 2)
        if durations:
            print(f"Average Match Duration: {sum(durations)/len(durations):.2f} turns")
            print(f"Max Match Duration: {max(durations)} turns")
            print(f"Min Match Duration: {min(durations)} turns")

if __name__ == "__main__":
    analyze()
