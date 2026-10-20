# -*- coding: utf-8 -*-
import sys, json, collections, re
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

rels = md.relations()
kin = [r for r in rels if r.get("category") == "亲属"]
print("亲属 n=", len(kin))
c = collections.Counter(r.get("rel", "") for r in kin)
for k, v in c.most_common(60):
    print(v, k)

print("\n=== role 里的继承/长幼标记 ===")
chars = md.characters()
pats = ["长子", "次子", "三子", "四子", "太子", "长孙", "嫡", "庶", "兄", "弟", "子", "孙", "侄", "继承", "继位", "世子"]
for p in pats:
    n = sum(1 for ch in chars if p in (ch.get("role") or ""))
    print(p, n)

print("\n=== 亲属 rel 文本里出现哪些亲属词 ===")
kpats = ["父", "子", "兄", "弟", "孙", "叔", "侄", "祖", "母", "妻", "甥", "婿", "兄弟", "外戚", "皇子", "公主"]
allrel = collections.Counter()
for r in rels:
    t = r.get("rel") or ""
    for p in kpats:
        if p in t:
            allrel[(r.get("category"), p)] += 1
for k, v in sorted(allrel.items(), key=lambda kv: -kv[1]):
    print(v, k)

print("\n=== 君臣从属 rel 文本样本 ===")
jc = [r for r in rels if r.get("category") == "君臣从属"]
for r in jc[:30]:
    print(r.get("rel"))

print("\n=== 君臣从属里含亲属词的 ===")
n = 0
for r in jc:
    t = r.get("rel") or ""
    if any(p in t for p in ["父", "子", "兄", "弟", "孙", "叔", "侄", "祖"]):
        n += 1
        if n <= 20:
            print("  ", r.get("from"), "->", r.get("to"), "|", t)
print("total", n, "/", len(jc))
