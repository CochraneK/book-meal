# -*- coding: utf-8 -*-
"""gp-7：把「另一位 worker 正在写的 systems」整体另存一份，绝不删任何一方的产物。"""
import os, shutil, time

ROOT = r"D:\2026\WB项目\明朝"
P = os.path.join(ROOT, "papers_pilot", "systems")
D = os.path.join(ROOT, ".dump", "_bak_gp7_otherworker_systems_%s" % time.strftime("%H%M%S"))
os.makedirs(D, exist_ok=True)
out = open(os.path.join(P, "gp7_snap.txt"), "w", encoding="utf-8")
out.write("snap -> %s\n" % D)

for sub in ("", "paper", "paper/sections", "paper/figures", "paper/out"):
    s = os.path.join(P, sub) if sub else P
    if not os.path.isdir(s):
        continue
    d = os.path.join(D, sub)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(s):
        p = os.path.join(s, f)
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(d, f))
            out.write("   %s\n" % os.path.relpath(p, P))

# 外来底稿 + 外来生成器也一并留档
for s, name in ((os.path.join(ROOT, ".dump", "_bak_systems_foreign_schema_20261002.json"), "stats_foreign_schema.json"),
                (os.path.join(P, "_stats.foreign_schema.bak.py"), "stats_generator_foreign.py")):
    if os.path.isfile(s):
        shutil.copy2(s, os.path.join(D, name))
        out.write("   %s\n" % os.path.basename(s))

# 我的标准 schema 底稿另存一份，防止再被冲
shutil.copy2(os.path.join(ROOT, ".dump", "_stats_systems.json"),
             os.path.join(D, "stats_standard_schema_mine.json"))
out.write("   stats_standard_schema_mine.json\n")
out.close()
print("ok")
