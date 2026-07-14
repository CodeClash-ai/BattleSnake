#!/bin/bash
N=${1:-20}
cd /workspace
env PORT=8000 python -u -c "
from server import run_server
import main
run_server({'info':main.info,'start':main.start,'move':main.move,'end':main.end})
" >/tmp/me.log 2>&1 &
ME_PID=$!
env PORT=8001 python -u -c "
import sys; sys.path.insert(0,'test')
import opponent
from server import run_server
run_server({'info':opponent.info,'start':opponent.start,'move':opponent.move,'end':opponent.end})
" >/tmp/opp.log 2>&1 &
OPP_PID=$!
sleep 4
me=0; opp=0; tie=0
for i in $(seq 1 $N); do
  out=$(./game/battlesnake play -W 11 -H 11 --name me --url http://127.0.0.1:8000 --name opp --url http://127.0.0.1:8001 -g standard 2>&1)
  w=$(echo "$out" | grep -iE 'winner|draw' | tail -1)
  if echo "$w" | grep -qi 'me was the winner'; then me=$((me+1));
  elif echo "$w" | grep -qi 'opp was the winner'; then opp=$((opp+1));
  else tie=$((tie+1)); fi
done
echo "RESULTS: me=$me opp=$opp tie=$tie (of $N)"
kill $ME_PID $OPP_PID 2>/dev/null
