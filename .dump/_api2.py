import sys, inspect, re
sys.stdout.reconfigure(encoding="utf-8")
p = r"d:\2026\WB项目\明朝\papers_pilot\_lib\mingdata.py"
t = open(p, encoding="utf-8").read()
i = t.index("def degree_map")
print(t[i-1200:i+900])
print("\n\n=========== events_by_year ===========")
j = t.index("def events_by_year")
print(t[j:j+700])
