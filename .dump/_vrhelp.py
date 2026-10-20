import sys, io, os
sys.stdout.reconfigure(encoding="utf-8")
p = r"d:\2026\WB项目\明朝\papers_pilot\_lib\verify_refs.py"
src = open(p, encoding="utf-8").read().splitlines()
for i, l in enumerate(src[:60], 1):
    print(i, l)
print("....")
for i, l in enumerate(src, 1):
    if "argv" in l or "json.dump" in l or "OUT" in l or "out" in l.lower() and ("json" in l or "md" in l):
        print(i, l)
