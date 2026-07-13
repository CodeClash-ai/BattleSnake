import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""Local port of xtagon/nagini for prediction/eval (copied from origin/human/xtagon/nagini)."""
DIRECTIONS = ["up", "down", "left", "right"]

def step(coord, direction):
    x, y = coord["x"], coord["y"]
    if direction == "up": return {"x": x, "y": y + 1}
    if direction == "down": return {"x": x, "y": y - 1}
    if direction == "left": return {"x": x - 1, "y": y}
    if direction == "right": return {"x": x + 1, "y": y}
    return {"x": x, "y": y}

def head_of(snake): return snake["body"][0]
def step_snake(snake, direction): return step(head_of(snake), direction)
def out_of_bounds(board, target): return target["y"] < 0 or target["x"] < 0 or target["y"] >= board["height"] or target["x"] >= board["width"]
def coords_equal(a,b): return a["x"]==b["x"] and a["y"]==b["y"]
def manhattan_distance(a,b): return abs(a["x"]-b["x"])+abs(a["y"]-b["y"])
def adjacent(a,b): return (a["x"]==b["x"] and abs(a["y"]-b["y"] )==1) or (a["y"]==b["y"] and abs(a["x"]-b["x"] )==1)

def check_collision(you, target, other_snake):
    you_are_other = (you["id"] == other_snake["id"] and you["body"] == other_snake["body"])
    body = other_snake["body"]
    last = body[-1]
    second_last = body[-2] if len(body) >= 2 else None
    solid_parts=[]
    for part in body:
        is_free_tail = coords_equal(part,last) and (second_last is None or not coords_equal(part,second_last))
        if not is_free_tail: solid_parts.append(part)
    direct_impact = any(coords_equal(p,target) for p in solid_parts)
    other_head=body[0]
    possible_head_to_head = (not you_are_other) and adjacent(other_head,target)
    if direct_impact: outcome="lose"; prob=1.0
    elif possible_head_to_head:
        prob=1.0/3.0
        if len(other_snake["body"]) == len(you["body"]): outcome="draw"
        elif len(other_snake["body"]) < len(you["body"]): outcome="win"
        else: outcome="lose"
    else: outcome="free"; prob=0.0
    return {"outcome": outcome, "value": {"win":1.0,"draw":-0.5,"free":0.0,"lose":-1.0}[outcome]*prob, "probability": prob}

def value_of_collision_with_snake(board,you,target):
    collisions=[check_collision(you,target,s) for s in board["snakes"]]
    collisions=[c for c in collisions if c["outcome"]!="free"]
    if collisions:
        worst=min(collisions,key=lambda c:c["value"]); avg=sum(c["value"] for c in collisions)/len(collisions)
        return worst["value"] if worst["value"] <= 0 else avg
    return 0.0

def probability_of_eating_food(board,target):
    if not board.get("food"): return 0.0
    nearest=min(manhattan_distance(f,target) for f in board["food"])
    return 1.0 if nearest == 0 else 1.0/nearest

def value_of_move(world,direction):
    you=world["you"]; board=world["board"]; target=step_snake(you,direction)
    col=-1.0 if out_of_bounds(board,target) else value_of_collision_with_snake(board,you,target)
    return {"collision_avoidance": col, "food_seeking": probability_of_eating_food(board,target)}

def sort_solutions_by_value(solutions):
    s=sorted(solutions,key=lambda x:x["value"]["food_seeking"])
    s=sorted(s,key=lambda x:x["value"]["collision_avoidance"])
    s.reverse(); return s

def solve(world,max_depth=0,depth=0):
    sols=sort_solutions_by_value([{"direction":d,"value":value_of_move(world,d)} for d in DIRECTIONS])
    return sols[0]["direction"] if sols else None

def move(game_state):
    try:
        mv=solve({"board": game_state["board"], "turn": game_state.get("turn",0), "you": game_state["you"]}, 0)
        return {"move": mv if mv in DIRECTIONS else "up"}
    except Exception:
        return {"move":"up"}

def info():
    return {"apiversion":"1","author":"xtagon","color":"#6b46c1","head":"default","tail":"default"}
def start(game_state): return None
def end(game_state): return None

if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
