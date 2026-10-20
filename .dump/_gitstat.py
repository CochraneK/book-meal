# -*- coding: utf-8 -*-
"""统计 papers_pilot 首次入库的范围，避免把不该进的东西带进去。"""
import collections, io, os

cands = [
    r"D:\2026\WB项目\明朝\papers_pilot\.dump\_git_status.txt",
    r"D:\2026\WB项目\明朝\.dump\_git_status.txt",
]
p = next((c for c in cands if os.path.exists(c)), None)
if not p:
    found = []
    for root, dirs, files in os.walk(r"D:\2026\WB项目\明朝\papers_pilot"):
        if "_git_status.txt" in files:
            found.append(os.path.join(root, "_git_status.txt"))
    print("找不到 _git_status.txt，找到：", found[:5])
    raise SystemExit(1)

L = [l for l in io.open(p, encoding="utf-8", errors="replace").read().splitlines() if len(l) > 3]
print("staged 条目数 =", len(L))
print("状态前缀:", dict(collections.Counter(l[:2] for l in L)))
g = collections.Counter()
for l in L:
    q = l[3:].strip()
    top = q.split("/")[0] if "/" in q else "(根文件)"
    g[top] += 1
print("顶层分组（前 16）：")
for k, v in g.most_common(16):
    print("   %-38s %d" % (k, v))
print("总计", sum(g.values()))
print("pdf 入库 =", sum(1 for l in L if l.endswith(".pdf")))
print("pyc 入库 =", sum(1 for l in L if l.endswith(".pyc")))
print("tex 入库 =", sum(1 for l in L if l.endswith(".tex")))
print("bak/quarantine 目录掩盖到的条目 =",
      sum(1 for l in L if "bak" in l.lower() or "quarantine" in l.lower()))
