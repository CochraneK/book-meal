# -*- coding: utf-8 -*-
import sys, collections, math, json
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

chars = md.characters()
rels = md.relations()
evs = md.events()
deg = md.degree_map()

names = set()
for c in chars:
    if c.get("name"):
        names.add(c["name"])
    for a in (c.get("aliases") or []):
        names.add(str(a))
NMS = sorted(names, key=len, reverse=True)

print("== 度分布 ==")
dvals = [deg.get(c.get("name"), 0) for c in chars]
n0 = sum(1 for d in dvals if d == 0)
print("人物", len(chars), "孤立点(度0)", n0, "占比 %.1f%%" % (100.0 * n0 / len(chars)))
print("度数>0 的", len(dvals) - n0)
print("gini(全部)", md.gini(dvals))
print("gini(度>0)", md.gini([d for d in dvals if d > 0]))
print("max", max(dvals), "mean %.3f" % (sum(dvals) / len(dvals)))
print("mean(>0) %.3f" % (sum(d for d in dvals if d > 0) / (len(dvals) - n0)))
hist = collections.Counter(dvals)
for k in sorted(hist)[:20]:
    print("  deg", k, "->", hist[k], "人")
print("  deg>=13:", sum(v for k, v in hist.items() if k >= 13))
top = deg.most_common(15)
print("top15", top)

print("\n== 累积：Top-k 占全部度数和 ==")
tot = sum(dvals)
srt = sorted(dvals, reverse=True)
for k in (1, 5, 10, 20, 50, 100):
    print("  top%d 度数占比 %.1f%%" % (k, 100.0 * sum(srt[:k]) / tot))

print("\n== 幂律尾试探（Hill / log-log 回归，度>=xmin）==")
def hill(xmin):
    tail = [d for d in dvals if d >= xmin]
    if len(tail) < 5:
        return None
    xs = [math.log(d) for d in tail]
    ys = [math.log(1.0 * i / len(tail)) for i in range(len(tail), 0, -1)]
    # 用 rank 回归：log(P(X>=x)) ~ -(a-1) log x
    # 简化：CCDF 对 x 的对数线性拟合
    xs2 = sorted(tail, reverse=True)
    pts = [(math.log(x), math.log((i + 1.0) / len(tail))) for i, x in enumerate(xs2)]
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((a - mx) * (b - my) for a, b in pts)
    den = sum((a - mx) ** 2 for a, b in pts)
    slope = num / den if den else 0
    return {"xmin": xmin, "n": n, "alpha": round(1 - slope, 3)}
for xm in (2, 3, 5, 8, 10, 15):
    print("  ", hill(xm))

print("\n== 事件年份分布 ==")
ey = md.events_by_year()
print("有年份事件", sum(ey.values()), "年份数", len(ey), "范围", min(ey), max(ey))
dec = collections.Counter()
for y, n in ey.items():
    dec[(y // 10) * 10] += n
for d in sorted(dec):
    print("  ", d, dec[d], "#" * (dec[d] // 2))

print("\n== 分期事件类别 ==")
PERIODS = [(1368, 1499, "P1 1368-1499"), (1500, 1599, "P2 1500-1599"), (1600, 1662, "P3 1600-1662")]
for lo, hi, lab in PERIODS:
    sub = [e for e in evs if e.get("year") and isinstance(e.get("year"), int) and lo <= e["year"] <= hi]
    c = collections.Counter(e.get("category") for e in sub)
    print(lab, "n=", len(sub))
    for k, v in c.most_common():
        print("    %-10s %4d  %.1f%%" % (k, v, 100.0 * v / len(sub)))

print("\n== 事件总数/类别 ==")
for x in md.event_categories():
    print("   ", x)

print("\n== 每年事件数的集中度 ==")
yrs = sorted(ey)
vals = [ey[y] for y in yrs]
print("gini(按年)", md.gini(vals))
print("峰值年份", sorted(ey.items(), key=lambda kv: -kv[1])[:10])
