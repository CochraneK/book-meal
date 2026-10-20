# -*- coding: utf-8 -*-
"""info 篇与其余各篇正文 4-gram Jaccard 自检（只读，不改任何论文文件）。"""
import os, sys
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
from cross_check_all import grams, jaccard, read, ROOT

PIDS = ["history", "psychology", "museum", "politics", "sociology", "anthropology",
        "systems", "economics", "geography", "law", "military", "narrative",
        "gender", "ideology", "diplomacy", "science", "art", "info", "synthesis",
        "narrative_silence"]

bodies = {}
for pid in PIDS:
    pdir = os.path.join(ROOT, "papers_pilot", pid, "paper", "sections")
    secs = sorted(f for f in os.listdir(pdir) if f.endswith(".tex")) if os.path.isdir(pdir) else []
    bodies[pid] = "".join(read(os.path.join(pdir, s)) for s in secs)

G = {p: grams(t) for p, t in bodies.items() if len(t) > 800}
out = ["info 正文汉字 %d" % len(bodies.get("info", ""))]
rows = []
for p in sorted(G):
    if p == "info":
        continue
    rows.append((jaccard(G["info"], G[p]), p))
rows.sort(reverse=True)
out.append("== info 与其他各篇的 4-gram Jaccard（降序）==")
for s, p in rows:
    out.append("  info <-> %-18s %.4f  %s" % (p, s, "OK" if s < 0.20 else "!! >=0.20"))
mx = rows[0][0] if rows else 0.0
out.append("最大值 %.4f（阈值 0.20）→ %s" % (mx, "PASS" if mx < 0.20 else "FAIL"))
open(os.path.join(ROOT, ".dump", "_jaccard_info.txt"), "w", encoding="utf-8").write("\n".join(out))
