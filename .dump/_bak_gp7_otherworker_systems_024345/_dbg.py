# -*- coding: utf-8 -*-
import json, os, re

ROOT = r"D:\2026\WB项目\明朝"
pdir = os.path.join(ROOT, "papers_pilot", "systems", "paper")
secs = sorted(f for f in os.listdir(os.path.join(pdir, "sections")) if f.endswith(".tex"))
body = "".join(open(os.path.join(pdir, "sections", s), encoding="utf-8").read() for s in secs)
stats = json.load(open(os.path.join(ROOT, ".dump", "_stats_systems.json"), encoding="utf-8"))
pool = set()


def flat(o):
    if isinstance(o, dict):
        for v in o.values():
            flat(v)
    elif isinstance(o, list):
        for v in o:
            flat(v)
    elif isinstance(o, (int, float)):
        pool.add(round(float(o), 2))
    elif isinstance(o, str):
        for m in re.findall(r"\d+(?:\.\d+)?", o):
            try:
                pool.add(round(float(m), 2))
            except ValueError:
                pass


flat(stats)
used = set(round(float(m), 2) for m in re.findall(r"\d+\.\d+", body))
bad = sorted(u for u in used if not any(abs(u - v) <= 0.06 for v in pool))
lines = []
lines.append("pool=%s" % sorted(pool))
lines.append("used=%s" % sorted(used))
lines.append("BAD=%s" % bad)
for u in bad:
    ctx = []
    for s in secs:
        txt = open(os.path.join(pdir, "sections", s), encoding="utf-8").read()
        for i, line in enumerate(txt.splitlines(), 1):
            if re.search(r"[^0-9]%s[^0-9]" % re.escape("%g" % u), line):
                ctx.append("%s:%d %s" % (s, i, line[:110]))
    lines.append("--- %g" % u)
    lines.extend(ctx[:4])
open(os.path.join(os.path.dirname(__file__), "_dbg.txt"), "w", encoding="utf-8").write("\n".join(lines))
