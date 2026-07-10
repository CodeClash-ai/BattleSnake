#!/bin/bash
BOTA=$1; BOTB=$2; N=$3; CLI=/workspace/battlesnake_cli
rm -rf /tmp/botA /tmp/botB; mkdir -p /tmp/botA /tmp/botB
cp /workspace/server.py /tmp/botA/; cp /workspace/server.py /tmp/botB/
cp "$BOTA" /tmp/botA/main.py; cp "$BOTB" /tmp/botB/main.py
pkill -f "/tmp/botA/main.py" 2>/dev/null; pkill -f "/tmp/botB/main.py" 2>/dev/null
PORT=8001 python3 /tmp/botA/main.py >/tmp/botA.log 2>&1 & PA=$!
PORT=8002 python3 /tmp/botB/main.py >/tmp/botB.log 2>&1 & PB=$!
sleep 8; a=0;b=0;d=0
for i in $(seq 1 $N); do
  o=$($CLI play -W 11 -H 11 -n A -u http://localhost:8001 -n B -u http://localhost:8002 -r $i 2>&1 | tail -3)
  if echo "$o"|grep -q "A is the winner\|A was the winner"; then a=$((a+1));
  elif echo "$o"|grep -q "B is the winner\|B was the winner"; then b=$((b+1)); else d=$((d+1)); fi
done
echo "A=$a B=$b draw=$d"; kill $PA $PB 2>/dev/null
