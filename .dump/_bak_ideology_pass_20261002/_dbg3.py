# -*- coding: utf-8 -*-
import os, time
ROOT = r"D:\2026\WB项目\明朝"
lines = []
for root, dirs, files in os.walk(ROOT):
    if ".git" in root or "__pycache__" in root:
        continue
    for fn in files:
        if "_stats_" in fn or fn.endswith(".log"):
            p = os.path.join(root, fn)
            lines.append("%s | %s bytes | %s" % (p, os.path.getsize(p), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p)))))
with open(os.path.join(os.path.dirname(__file__), "_dbg3.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(lines)))
