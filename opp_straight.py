import os
def move(gs): return {"move":"up"}
if __name__=="__main__":
    from server import run_server
    run_server({"info":lambda:{"apiversion":"1"},"move":move,"start":lambda g:None,"end":lambda g:None})
