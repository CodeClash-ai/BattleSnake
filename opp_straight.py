def info(): return {"apiversion":"1","author":"opp","color":"#FFAAAA","head":"shac-gamer","tail":"shac-coffee"}
def start(gs): return None
def end(gs): return None
def move(gs): return {"move":"up"}
if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
