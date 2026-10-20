import os, json
ROOT = r"D:\2026\WB项目\明朝"
out = []
p = os.path.join(ROOT, "papers_pilot", "info", "paper", "out")
for r, d, f in os.walk(p):
    for n in sorted(f):
        fp = os.path.join(r, n)
        out.append("%8d %s" % (os.path.getsize(fp), fp.replace("\\", "/")))
log = os.path.join(ROOT, ".dump", "_compile_info.log")
txt = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
out.append("--- compile log tail ---")
out.append("\n".join(txt.splitlines()[-60:]))
bbl = os.path.join(p, "main.bbl")
if os.path.exists(bbl):
    t = open(bbl, encoding="utf-8", errors="replace").read()
    out.append("--- BBL (%d lines) ---" % len(t.splitlines()))
    out.append("\n".join(t.splitlines()[:50]))
open(os.path.join(ROOT, ".dump", "_bblstate.txt"), "w", encoding="utf-8").write("\n".join(out))
