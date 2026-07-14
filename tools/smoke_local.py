#!/usr/bin/env python3
import subprocess, time, sys, os, signal, re
style=sys.argv[1] if len(sys.argv)>1 else 'food'
n=int(sys.argv[2]) if len(sys.argv)>2 else 10
port1=8010; port2=8011
env=os.environ.copy(); env['PORT']=str(port1)
p1=subprocess.Popen([sys.executable,'main.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
p2=subprocess.Popen([sys.executable,'tools/simple_opponent.py',style,str(port2)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
wins=loss=draw=0
try:
 for seed in range(1,n+1):
  cmd=['./game/battlesnake','play','-W','11','-H','11','--name','gpt-5-5','--url',f'http://localhost:{port1}','--name',f'simple-{style}','--url',f'http://localhost:{port2}','--seed',str(seed)]
  out=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10).stdout
  if 'gpt-5-5 was the winner' in out: wins+=1
  elif f'simple-{style} was the winner' in out: loss+=1
  else: draw+=1
 print(style, 'wins', wins, 'loss', loss, 'draw', draw)
finally:
 for p in (p1,p2):
  p.terminate()
 try:
  p1.wait(timeout=1); p2.wait(timeout=1)
 except subprocess.TimeoutExpired:
  p1.kill(); p2.kill()
