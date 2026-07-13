"""Local copy of coreyja__bombastic-bob: random reasonable move."""
import random
MOVES=[("up",(0,1)),("down",(0,-1)),("left",(-1,0)),("right",(1,0))]
def info(): return {"apiversion":"1","author":"coreyja","color":"#AA66CC","head":"trans-rights-scarf","tail":"default"}
def start(game_state): pass
def end(game_state): pass
def move(game_state):
    try: return {"move":_choose(game_state)}
    except Exception: return {"move":"right"}
def _choose(game_state):
    board=game_state["board"]; width=board["width"]; height=board["height"]
    me=game_state["you"]; hx,hy=me["head"]["x"],me["head"]["y"]
    body_cells={(seg["x"],seg["y"]) for s in board["snakes"] for seg in s["body"]}
    hazard_cells={(hh["x"],hh["y"]) for hh in board.get("hazards",[])}
    hazard_damage=game_state.get("game",{}).get("ruleset",{}).get("settings",{}).get("hazardDamagePerTurn",15)
    reasonable=[]
    for name,(dx,dy) in MOVES:
        nx,ny=hx+dx,hy+dy
        if not (nx<0 or nx>=width or ny<0 or ny>=height or (nx,ny) in body_cells or ((nx,ny) in hazard_cells and hazard_damage>=me["health"])):
            reasonable.append(name)
    if reasonable: return random.choice(reasonable)
    neck=me["body"][1] if len(me["body"])>1 else None
    fallback=[]
    for name,(dx,dy) in MOVES:
        nx,ny=hx+dx,hy+dy
        if neck is not None and nx==neck["x"] and ny==neck["y"]: continue
        fallback.append(name)
    return random.choice(fallback) if fallback else "right"
if __name__=="__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from server import run_server
    run_server({"info":info,"start":start,"move":move,"end":end})
