import json, sys, glob, os

def analyze(round_dir, me="opus-4-8"):
    results = json.load(open(os.path.join(round_dir,"results.json")))
    print("Round", results.get("round_num"), "winner:", results.get("winner"), "scores:", results.get("scores"))
    for f in sorted(glob.glob(os.path.join(round_dir,"sim_*.jsonl"))):
        lines = [json.loads(l) for l in open(f) if l.strip()]
        # last game state line
        turns = [l for l in lines if "turn" in l and "board" in l]
        last = turns[-1]
        board = last["board"]
        snakes = {s["name"]:s for s in board["snakes"]}
        alive = list(snakes.keys())
        me_snake = None
        # find my final state across all turns
        my_len = 0
        for t in turns:
            for s in t["board"]["snakes"]:
                if s["name"]==me:
                    my_len = s["length"]
        won = me in alive and len(alive)==1
        # determine outcome
        n=os.path.basename(f)
        print(f"{n}: turns={last['turn']} alive={alive} my_final_len={my_len}")

if __name__=="__main__":
    d = sys.argv[1] if len(sys.argv)>1 else "/logs/rounds/0"
    analyze(d)
