"""Local recreation of observed Nettogrof__nessegrev-java behavior.

Round logs show this opponent always returns {"move": "up"}, regardless of
food, walls, or bodies.  This is useful as a smoke-test opponent alongside
simple_opponent.py.
"""


def info():
    return {"apiversion": "1", "author": "up-opp", "color": "#4444ff"}


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    return {"move": "up"}


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
