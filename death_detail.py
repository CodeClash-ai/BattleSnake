import json
def look(f):
    with open(f) as fh:
        lines = fh.readlines()
    parsed = [json.loads(l) for l in lines]
    # Print last 5 turns' our head + our move + board summary
    print(f"===== {f} =====")
    for d in parsed[-8:]:
        if 'turn' not in d: 
            print("END:", d)
            continue
        snakes = d['board']['snakes']
        us = next((s for s in snakes if 'opus' in s['name']), None)
        opp = next((s for s in snakes if 'opus' not in s['name']), None)
        if us:
            print(f"turn={d['turn']} us_head={us['body'][0]} len={len(us['body'])} hp={us['health']} body={us['body'][:5]}...")
            if opp: print(f"  opp_head={opp['body'][0]} len={len(opp['body'])}")

look('/logs/rounds/2/sim_105.jsonl')
look('/logs/rounds/2/sim_177.jsonl')
