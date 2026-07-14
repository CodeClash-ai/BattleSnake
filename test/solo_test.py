# Test our bot's survival alone (opponent absent / already dead) over many turns.
import sys
sys.path.insert(0, '/workspace')
import main

W=H=11
import random
random.seed(42)

def make_state(body, health, food, length):
    return {
        "board": {"width":W,"height":H,
                  "food":[{"x":f[0],"y":f[1]} for f in food],
                  "snakes":[{"id":"me","length":length,"health":health,
                             "body":[{"x":b[0],"y":b[1]} for b in body]}]},
        "you":{"id":"me","length":length,"health":health,
               "body":[{"x":b[0],"y":b[1]} for b in body]},
    }

# simulate solo survival
body=[(5,5),(5,4),(5,3)]
health=100
length=3
food=[(2,2)]
DIRS=main.DIRS
alive=0
for turn in range(300):
    st=make_state(body,health,food,length)
    mv=main.move(st)["move"]
    dx,dy=DIRS[mv]
    nh=(body[0][0]+dx, body[0][1]+dy)
    # check collision
    if not (0<=nh[0]<W and 0<=nh[1]<H) or nh in body[:-1]:
        print("DIED turn",turn,"len",length,"move",mv,"head",body[0],"->",nh)
        break
    ate = nh in food
    body=[nh]+body
    if ate:
        food=[(random.randint(0,W-1),random.randint(0,H-1))]
        length+=1
        health=100
    else:
        body=body[:-1]
        health-=1
    if health<=0:
        print("STARVED turn",turn); break
    alive=turn
else:
    print("SURVIVED all 300 turns, len",length)
