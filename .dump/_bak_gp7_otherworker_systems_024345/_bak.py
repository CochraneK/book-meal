# -*- coding: utf-8 -*-
"""跑 prep 前先备份本 pid 活目录（team-lead 硬纪律：动任何文件前先快照）。"""
import json
import os
import shutil
import time

ROOT = r"D:\2026\WB项目\明朝"
SRC = os.path.join(ROOT, "papers_pilot", "systems")
DST = os.path.join(ROOT, "papers_pilot", "systems_bak_" + time.strftime("%Y%m%d_%H%M%S"))
os.makedirs(DST, exist_ok=True)
if os.path.isdir(SRC):
    shutil.copytree(SRC, os.path.join(DST, "papers_pilot"), dirs_exist_ok=True)
sp = os.path.join(ROOT, ".dump", "_stats_systems.json")
if os.path.exists(sp):
    shutil.copy2(sp, os.path.join(DST, "_stats_systems.json"))
files = []
for r, d, fs in os.walk(DST):
    for f in fs:
        files.append(os.path.relpath(os.path.join(r, f), DST))
with open(os.path.join(DST, "_manifest.json"), "w", encoding="utf-8") as f:
    json.dump({"src": SRC, "dst": DST, "files": sorted(files)}, f, ensure_ascii=False, indent=2)
