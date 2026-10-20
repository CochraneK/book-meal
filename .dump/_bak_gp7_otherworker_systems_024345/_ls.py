# -*- coding: utf-8 -*-
import os, time, json, shutil

ROOT = r"D:\2026\WB项目\明朝"
outp = os.path.join(ROOT, "papers_pilot", "systems", "_ls.txt")
out = open(outp, "w", encoding="utf-8")


def w(s=""):
    out.write(s + "\n")


SRC = os.path.join(ROOT, ".dump", "_stats_systems.json")
BAK = os.path.join(ROOT, "papers_pilot", "systems_bak_20261002_022347", "_stats_systems.json")

# 1) 先把外来底稿与外来生成器另存，不删
foreign = os.path.join(ROOT, ".dump", "_bak_systems_foreign_schema_20261002.json")
shutil.copy2(SRC, foreign)
w("foreign stats -> %s" % os.path.relpath(foreign, ROOT))

j = json.load(open(foreign, encoding="utf-8"))
w("foreign keys: %s" % list(j.keys()))

# 2) 用我自己的备份恢复标准 schema
shutil.copy2(BAK, SRC)
w("restored standard schema -> %s" % os.path.relpath(SRC, ROOT))
j2 = json.load(open(SRC, encoding="utf-8"))
w("live keys: %s" % list(j2.keys()))

# 3) 打印恢复后的关键段
w("\n=== subset ===")
w(json.dumps(j2.get("subset"), ensure_ascii=False)[:1500])
w("\n=== baseline ===")
w(json.dumps(j2.get("baseline"), ensure_ascii=False)[:1500])
w("\n=== vocab ===")
w(json.dumps(j2.get("vocab"), ensure_ascii=False)[:800])
w("\n=== anchors ===")
w(json.dumps(j2.get("anchors"), ensure_ascii=False)[:800])
w("\n=== events ===")
w(json.dumps(j2.get("events"), ensure_ascii=False)[:600])
out.close()
print("ok")
