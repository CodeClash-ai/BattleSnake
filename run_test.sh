#!/bin/bash
cd /workspace
N=${1:-20}
mkdir -p /tmp/opp && cp main_old_naive.py /tmp/opp/main.py && cp server.py /tmp/opp/
( cd /workspace && PORT=8000 python3 main.py >/tmp/me.log 2>&1 ) &
MEPID=$!
( cd /tmp/opp && PORT=8001 python3 main.py >/tmp/opp.log 2>&1 ) &
OPPID=$!
for i in $(seq 1 30); do
  curl -s http://127.0.0.1:8000 >/dev/null 2>&1 && curl -s http://127.0.0.1:8001 >/dev/null 2>&1 && break
  sleep 0.5
done
MEWIN=0; OPPWIN=0; TIE=0
for i in $(seq 1 $N); do
  OUT=$(./game/battlesnake play -W 11 -H 11 \
    --name me --url http://127.0.0.1:8000 \
    --name opp --url http://127.0.0.1:8001 \
    -g standard 2>&1 | tail -3)
  if echo "$OUT" | grep -qi "me.*is the winner\|Winner.*me"; then MEWIN=$((MEWIN+1));
  elif echo "$OUT" | grep -qi "opp.*is the winner\|Winner.*opp"; then OPPWIN=$((OPPWIN+1));
  else TIE=$((TIE+1)); fi
done
echo "RESULTS over $N games: me=$MEWIN opp=$OPPWIN tie=$TIE"
kill $MEPID $OPPID 2>/dev/null
pkill -f "PORT=8000" 2>/dev/null
