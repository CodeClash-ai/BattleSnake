"""
Sparring opponent that mimics the REAL opponent Nettogrof__nessegrev-julia:
a naive straight-line WALL-CRAWLER. It picks one fixed direction at game
start and marches until it crashes into the wall. No collision avoidance.

Use this (not main_simplesnake_backup.py) to test against the actual threat.
Run: cp opp_wallcrawler.py /tmp/wc_main.py; cp server.py /tmp/
     cd /tmp && PORT=8001 python3 wc_main.py &
"""
DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}


def info():
    return {"apiversion": "1", "author": "wc", "color": "#888888",
            "head": "default", "tail": "default"}


def start(data):
    return {}


def move(data):
    # Always move left (toward x=0), like the observed opponent. Fixed heading.
    return {"move": "left"}


def end(data):
    return {}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
