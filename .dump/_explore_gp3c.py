# -*- coding: utf-8 -*-
import sys, json, collections, re, math
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

rels = md.relations()
kin = [r for r in rels if r.get("category") == "亲属"]

SENIOR = ["祖", "父", "母", "叔", "伯", "舅", "姑", "姨", "翁", "岳", "先祖"]
JUNIOR = ["子", "孙", "侄", "甥", "婿", "媳", "女"]
FLAT = ["兄弟", "兄妹", "姐弟", "姐妹", "夫妻", "妻", "亲家", "同母兄弟", "表兄弟", "堂兄弟"]

POWER = ["太子", "皇", "帝", "位", "篡", "夺", "监国", "藩", "谋叛", "政", "国", "继位", "传位", "立为"]

def cls(t):
    t = t or ""
    # 纵向判定：同时出现长辈词与晚辈词
    pos_s = [(t.find(w), w) for w in SENIOR if w in t]
    pos_j = [(t.find(w), w) for w in JUNIOR if w in t]
    pos_s = sorted([p for p in pos_s if p[0] >= 0])
    pos_j = sorted([p for p in pos_j if p[0] >= 0])
    if pos_s and pos_j:
        return ("down" if pos_s[0][0] < pos_j[0][0] else "up"), pos_s[0][1], pos_j[0][1]
    for f in FLAT:
        if f in t:
            return "flat", f, ""
    if pos_s:
        return "senior_only", pos_s[0][1], ""
    if pos_j:
        return "junior_only", "", pos_j[0][1]
    return "unknown", "", ""

cnt = collections.Counter()
rows = []
for r in kin:
    t = r.get("rel") or ""
    d, a, b = cls(t)
    pw = [w for w in POWER if w in t]
    cnt[d] += 1
    rows.append((r.get("from"), r.get("to"), t, d, a, b, pw))

print("亲属方向分布:", dict(cnt), "total", len(kin))
print("\n纵向带权力语汇的亲属关系：")
n_pw = 0
for row in rows:
    if row[3] in ("down", "up") and row[6]:
        n_pw += 1
        print("  ", row[0], "->", row[1], "|", row[2], "|", row[6])
print("n_pw", n_pw)

print("\n== 各类别里含权力语汇的亲属关系条数 ==")
bycat = collections.Counter()
for row in rows:
    if row[6]:
        bycat[row[3]] += 1
print(dict(bycat))

print("\n== 非亲属关系中的亲属语汇（家语入国）==")
KINW = ["父", "母", "子", "兄", "弟", "孙", "叔", "侄", "甥", "婿", "祖"]
tot_by_cat = collections.Counter(r.get("category") for r in rels)
hit_by_cat = collections.Counter()
examples = collections.defaultdict(list)
for r in rels:
    cat = r.get("category")
    if cat == "亲属":
        continue
    t = r.get("rel") or ""
    ws = [w for w in KINW if w in t]
    if ws:
        hit_by_cat[cat] += 1
        if len(examples[cat]) < 8:
            examples[cat].append((r.get("from"), r.get("to"), t))
for cat, n in hit_by_cat.most_common():
    print("%s: %d / %d = %.1f%%" % (cat, n, tot_by_cat[cat], 100.0 * n / tot_by_cat[cat]))
    for e in examples[cat]:
        print("     ", e)

print("\n== role 长幼标注 ==")
chars = md.characters()
pats = ["长子", "次子", "三子", "四子", "幼子", "太子", "皇子", "世子", "长孙", "嫡长", "嫡子", "庶子", "长兄", "仲", "伯"]
for p in pats:
    n = sum(1 for ch in chars if p in (ch.get("role") or ""))
    print(p, n)

print("\n== 亲属关系两端是否在角色里带君/帝/王 ==")
name_idx = md.name_index()
n_royal = 0
for r in kin:
    for e in (r.get("from"), r.get("to")):
        c = name_idx.get(e)
        role = (c or {}).get("role") or ""
        if any(w in role for w in ["皇帝", "帝", "王", "太子", "太祖", "宗"]):
            n_royal += 1
            break
print("royal-touching 亲属关系", n_royal, "/", len(kin))
