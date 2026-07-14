#!/bin/bash
# Serve new bot on 8000, original on 8001, run N real CLI games.
cd /workspace
mkdir -p /tmp/opp
cp main_original_backup.py /tmp/opp/main.py
cp server.py /tmp/opp/server.py
PORT=8000 python3 main.py >/tmp/a.log 2>&1 &
A=$!
cd /tmp/opp && PORT=8001 python3 main.py >/tmp/b.log 2>&1 &
B=$!
cd /workspace
sleep 3
NEW=0; OLD=0; DRAW=0
N=${1:-10}
for i in $(seq 1 $N); do
  OUT=$(./game/battlesnake play -W 11 -H 11 \
    -n new -u http://127.0.0.1:8000 \
    -n old -u http://127.0.0.1:8001 \
    -g standard -r $((i*13+3)) 2>&1 | tail -3)
  if echo "$OUT" | grep -qi "new was the winner"; then NEW=$((NEW+1));
  elif echo "$OUT" | grep -qi "old was the winner"; then OLD=$((OLD+1));
  else DRAW=$((DRAW+1)); fi
done
echo "REAL GAMES: new=$NEW old=$OLD draw=$DRAW (n=$N)"
kill $A $B 2>/dev/null
