import os
def move(state):
    return {"move":"up"}
if __name__=="__main__":
    from server import run_server
    run_server({"info":lambda: {"apiversion":"1"},"move":move})
