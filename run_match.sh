#!/bin/bash
# Usage: ./run_match.sh <botA_main.py> <botB_main.py> <num_games>
BOTA=${1:-main.py}
BOTB=${2:-main_backup_v0.py}
N=${3:-50}
CLI=/workspace/battlesnake_cli
mkdir -p /tmp/botA /tmp/botB
cp /workspace/server.py /tmp/botA/server.py
cp /workspace/server.py /tmp/botB/server.py
cp "/workspace/$BOTA" /tmp/botA/main.py
cp "/workspace/$BOTB" /tmp/botB/main.py
PORT=8001 python3 /tmp/botA/main.py >/tmp/botA.log 2>&1 &
PA=$!
PORT=8002 python3 /tmp/botB/main.py >/tmp/botB.log 2>&1 &
PB=$!
sleep 2
winA=0; winB=0; draw=0
for i in $(seq 1 $N); do
  out=$($CLI play -W 11 -H 11 -n A -u http://localhost:8001 -n B -u http://localhost:8002 -r $i 2>&1 | tail -1)
  if echo "$out" | grep -q "A was the winner"; then winA=$((winA+1));
  elif echo "$out" | grep -q "B was the winner"; then winB=$((winB+1));
  else draw=$((draw+1)); fi
done
echo "A ($BOTA): $winA   B ($BOTB): $winB   draw: $draw"
kill $PA $PB 2>/dev/null
