import sys, re
sys.stdout.reconfigure(encoding="utf-8")
p = r"d:\2026\WB项目\明朝\papers_pilot\_lib\mingdata.py"
t = open(p, encoding="utf-8").read()
for m in re.finditer(r"^def\s+(\w+)\s*\(([^)]*)\)", t, re.M):
    print("def", m.group(1) + "(" + m.group(2) + ")")
print("---- DEFS/CLASSES ----")
for m in re.finditer(r"^(class|def)\s+(\w+)", t, re.M):
    print(m.group(1), m.group(2))
