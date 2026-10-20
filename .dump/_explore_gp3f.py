# -*- coding: utf-8 -*-
import sys, collections, math
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

chars = md.characters()
rels = md.relations()
deg = md.degree_map()

# ---- 连通分量 ----
adj = collections.defaultdict(set)
nodes = set()
for r in rels:
    f, t = r.get("from"), r.get("to")
    if f and t:
        adj[f].add(t); adj[t].add(f); nodes.add(f); nodes.add(t)
names = set(c.get("name") for c in chars)
nodes |= set()
print("关系端点去重节点", len(nodes), "其中在人物表内的", len(nodes & names))

seen = set()
comps = []
for n in sorted(nodes):
    if n in seen:
        continue
    stack = [n]; comp = []
    seen.add(n)
    while stack:
        x = stack.pop(); comp.append(x)
        for y in adj[x]:
            if y not in seen:
                seen.add(y); stack.append(y)
    comps.append(comp)
comps.sort(key=len, reverse=True)
print("分量数", len(comps), "前 10 大小", [len(c) for c in comps[:10]])
giant = comps[0]
print("巨组件 %d 人，占有关系节点的 %.1f%%，占全部人物的 %.1f%%"
      % (len(giant), 100.0 * len(giant) / len(nodes), 100.0 * len(giant) / len(chars)))
print("巨组件外有关系的节点", len(nodes) - len(giant))
print("孤立分量(大小1)", sum(1 for c in comps if len(c) == 1))

# ---- 年事件数的离散度 ----
ey = md.events_by_year()
vals = sorted(ey.values())
n = len(vals); m = sum(vals) / n
sd = (sum((v - m) ** 2 for v in vals) / n) ** 0.5
print("\n年事件数 n=%d mean=%.3f sd=%.3f CV=%.3f" % (n, m, sd, sd / m))
print("年份跨度", min(ey), max(ey), "空年数", (max(ey) - min(ey) + 1) - n)

# ---- 卡方：期 × 类别 ----
evs = md.events()
CATS = ["政治斗争", "军事战争", "人事任免", "案件刑狱", "死亡身后", "外交边务",
        "宫廷变故", "人物生平", "制度科举", "民变起义", "天灾人祸"]
P = [("P1", 1368, 1499), ("P2", 1500, 1599), ("P3", 1600, 1662)]
tab = {}
for lab, lo, hi in P:
    sub = [e for e in evs if isinstance(e.get("year"), int) and lo <= e["year"] <= hi]
    c = collections.Counter(e.get("category") for e in sub)
    tab[lab] = (len(sub), [c.get(k, 0) for k in CATS])
rows = []
tot = sum(tab[l][0] for l, _, _ in P)
coltot = [sum(tab[l][1][j] for l, _, _ in P) for j in range(len(CATS))]
chi = 0.0
for l, _, _ in P:
    N, row = tab[l]
    for j in range(len(CATS)):
        e = N * coltot[j] / tot
        if e > 0:
            chi += (row[j] - e) ** 2 / e
df = (len(P) - 1) * (len(CATS) - 1)
print("\n卡方 chi2=%.2f df=%d (n=%d)" % (chi, df, tot))
# 正态近似的 p（df 大）
# 用 Wilson–Hilferty 近似
z = ((chi / df) ** (1.0 / 3) - (1 - 2.0 / (9 * df))) / ((2.0 / (9 * df)) ** 0.5)
from math import erf, sqrt
p = 1 - 0.5 * (1 + erf(z / sqrt(2)))
print("近似 p = %.3g" % p)

for l, _, _ in P:
    N, row = tab[l]
    print(l, "n=%d" % N, " ".join("%s=%.1f%%" % (CATS[j][:2], 100.0 * row[j] / N) for j in range(len(CATS)) if row[j]))

# ---- 关系 chapter 字段 ----
print("\n关系 chapter 分布 top10:", collections.Counter(r.get("chapter") for r in rels).most_common(6))

# ---- 亲属关系章节 ----
kin = [r for r in rels if r.get("category") == "亲属"]
print("亲属 chapter:", collections.Counter(r.get("chapter") for r in kin).most_common(5))
