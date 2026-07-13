import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# Port/copy of TheApX__hungry opponent for local evaluation.
from collections import deque
MATRIX_SNAKE_BODY = 10 ** 18
MATRIX_UNINITIALIZED = 10 ** 18 - 1
_DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, 1), "down": (0, -1)}
_MOVE_ORDER = ["left", "right", "up", "down"]

def info():
    return {"apiversion":"1","author":"TheApX","color":"#2e8244","head":"smart-caterpillar","tail":"rattle"}
def start(game_state): return None
def end(game_state): return None
class MoveComparator:
    def __init__(self, board, you):
        self.width=int(board['width']); self.height=int(board['height']); self.snakes=board.get('snakes',[]) or []; self.food=board.get('food',[]) or []; self.you=you
        head=you['body'][0]; self.head=(int(head['x']),int(head['y'])); self.length=int(you.get('length',len(you['body'])))
        self.move_points={m:(self.head[0]+dx,self.head[1]+dy) for m,(dx,dy) in _DIRS.items()}
        self.neck=None
        if len(you['body'])>=2:
            n=you['body'][1]; self.neck=(int(n['x']),int(n['y']))
        self._init_board_matrix()
    def _idx(self,x,y): return y*self.width+x
    def _steps(self,p): return self.matrix[self._idx(p[0],p[1])]
    def _is_out_of_bounds(self,p):
        x,y=p; return x<0 or y<0 or x>=self.width or y>=self.height
    def _init_board_matrix(self):
        self.matrix=[MATRIX_UNINITIALIZED]*(self.width*self.height); self._mark_snake_bodies(); self._compute_steps_from_food()
    def _mark_snake_bodies(self):
        for snake in self.snakes:
            body=snake.get('body',[]) or []
            for seg in body[:-1]:
                x,y=int(seg['x']),int(seg['y'])
                if 0<=x<self.width and 0<=y<self.height: self.matrix[self._idx(x,y)]=MATRIX_SNAKE_BODY
    def _compute_steps_from_food(self):
        bfs=deque()
        for f in self.food:
            fx,fy=int(f['x']),int(f['y'])
            if 0<=fx<self.width and 0<=fy<self.height:
                self.matrix[self._idx(fx,fy)]=0; bfs.append((fx,fy))
        while bfs:
            cx,cy=bfs.popleft(); cur=self.matrix[self._idx(cx,cy)]
            for dx,dy in ((-1,0),(1,0),(0,1),(0,-1)):
                nx,ny=cx+dx,cy+dy
                if self._is_out_of_bounds((nx,ny)): continue
                v=self.matrix[self._idx(nx,ny)]
                if v==MATRIX_SNAKE_BODY or v!=MATRIX_UNINITIALIZED: continue
                self.matrix[self._idx(nx,ny)]=cur+1; bfs.append((nx,ny))
    def is_better(self,move,best):
        if move is None: return False
        if best is None: return True
        mp=self.move_points[move]; bp=self.move_points[best]
        if self.length>=2 and self.neck is not None:
            if mp==self.neck: return False
            if bp==self.neck: return True
        if self._is_out_of_bounds(mp): return False
        if self._is_out_of_bounds(bp): return True
        ms=self._steps(mp); bs=self._steps(bp)
        if ms==MATRIX_SNAKE_BODY: return False
        if bs==MATRIX_SNAKE_BODY: return True
        if ms==MATRIX_UNINITIALIZED and bs!=MATRIX_UNINITIALIZED: return False
        if ms!=MATRIX_UNINITIALIZED and bs==MATRIX_UNINITIALIZED: return True
        if ms!=MATRIX_UNINITIALIZED and bs!=MATRIX_UNINITIALIZED:
            if ms<bs: return True
            if ms>bs: return False
        return False

def _fallback_move(game_state):
    try:
        board=game_state['board']; you=game_state['you']; w=int(board['width']); h=int(board['height']); head=you['body'][0]; hx,hy=int(head['x']),int(head['y'])
        blocked=set()
        for snake in board.get('snakes',[]) or []:
            for seg in (snake.get('body',[]) or [])[:-1]: blocked.add((int(seg['x']),int(seg['y'])))
        for m in _MOVE_ORDER:
            dx,dy=_DIRS[m]; nx,ny=hx+dx,hy+dy
            if 0<=nx<w and 0<=ny<h and (nx,ny) not in blocked: return m
    except Exception: pass
    return 'up'

def move(game_state):
    try:
        comp=MoveComparator(game_state['board'],game_state['you']); best=None
        for m in _MOVE_ORDER:
            if comp.is_better(m,best): best=m
        return {'move': best or _fallback_move(game_state)}
    except Exception: return {'move': _fallback_move(game_state)}
if __name__=='__main__':
    from server import run_server
    run_server({'info':info,'start':start,'move':move,'end':end})
