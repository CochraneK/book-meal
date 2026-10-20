# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0, r"d:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

md.hit_text("族")  # 触发加载
txt = md._BOOK
out = []
pats = ["君.{0,10}父", "父.{0,10}君", "兄.{0,8}弟", "君.{0,10}子", "国家.{0,6}家"]
seen = set()
for p in pats:
    out.append("=== " + p)
    n = 0
    for m in re.finditer(p, txt):
        a, b = max(0, m.start() - 45), min(len(txt), m.end() + 45)
        snip = txt[a:b].replace("\n", "")
        key = snip[:30]
        if key in seen:
            continue
        seen.add(key)
        out.append("  ..." + snip + "...")
        n += 1
        if n >= 12:
            break
open(r"d:\2026\WB项目\明朝\.dump\_ctx3.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
