import os, glob
out = []
cands = []
for r, d, f in os.walk("papers_pilot/info/paper"):
    for n in f:
        if n == "main.blg" or (n.endswith(".bbl") and "out" in r):
            cands.append(os.path.join(r, n))
out.append("CANDIDATES: %s" % cands)
for c in cands:
    if c.endswith(".blg"):
        t = open(c, encoding="utf-8", errors="replace").read()
        out.append("=== %s ===" % c)
        out.append(t[-4000:])
bbls = [c for c in cands if c.endswith(".bbl")]
for c in bbls:
    t = open(c, encoding="utf-8", errors="replace").read()
    lines = t.splitlines()
    out.append("=== BBL %s (%d lines) ===" % (c, len(lines)))
    out.append("\n".join(lines[:40]))
open(".dump/_blg.txt", "w", encoding="utf-8").write("\n".join(out))
