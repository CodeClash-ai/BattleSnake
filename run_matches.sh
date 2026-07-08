#!/bin/bash
# Runs N matches between main.py (opus) and naive_opponent.py, reports W/L/T.
# Usage: ./run_matches.sh N
N=${1:-50}
cd /workspace
# start servers
PORT=8001 python3 main.py >/tmp/me.log 2>&1 &
ME_PID=$!
PORT=8002 python3 naive_opponent.py >/tmp/opp.log 2>&1 &
OPP_PID=$!
sleep 2
win=0; loss=0; tie=0
for i in $(seq 1 $N); do
  seed=$((RANDOM*RANDOM))
  out=$(game/battlesnake play -W 11 -H 11 \
     --name opus -u http://127.0.0.1:8001 \
     --name naive -u http://127.0.0.1:8002 \
     -r $seed 2>&1 | tail -3)
  if echo "$out" | grep -qi "draw"; then tie=$((tie+1));
  elif echo "$out" | grep -qi "opus"; then win=$((win+1));
  else loss=$((loss+1)); fi
done
kill $ME_PID $OPP_PID 2>/dev/null
echo "opus WINS=$win LOSSES=$loss TIES=$tie (of $N)"
