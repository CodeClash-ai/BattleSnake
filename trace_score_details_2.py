import json
import sys
sys.path.append("/workspace")
from trace_score_details import analyze_scoring

# Let's see turn 51, 52, 53, 54, 55, 56, 57, 58
for t in range(50, 61):
    analyze_scoring("/logs/rounds/0/sim_128.jsonl", t)
