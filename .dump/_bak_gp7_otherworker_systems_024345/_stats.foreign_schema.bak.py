# -*- coding: utf-8 -*-
"""systems 篇统计底稿 —— 崩塌的涌现：复杂网络中的明朝兴衰。

一条命令复算：
  python papers_pilot/systems/_stats.py

产出写入 .dump/_stats_systems.json，正文每个小数都来自这里。
数据纪律（见 _lib/mingdata.py 头注释）：
  1. relations[].from/to 是裸人物名，characters[] 无 id，一律按名字查；
  2. 地理坐标不按 falsy 判空；
  3. 截断桶改名（geN），不沿用被截断的键名。
"""
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_lib"))
import mingdata as md  # noqa: E402

PID = "systems"


def rou(x, n=4):
    return round(float(x), n)


# ---------------- 1. 语料规模 ----------------
corpus = {
    "persons": len(md.characters()),
    "events": len(md.events()),
    "relations": len(md.relations()),
    "locations": len(md.locations()),
    "chapters": len(md.timeline()),
}

# ---------------- 2. 度数分布 ----------------
deg = md.degree_map()
n_persons = corpus["persons"]
all_deg = [deg.get(c.get("name"), 0) for c in md.characters()]
n_linked = sum(1 for d in all_deg if d > 0)
n_isolated = n_persons - n_linked
hist = Counter(d for d in all_deg)
hist_le12 = [hist.get(i, 0) for i in range(0, 13)]
degree_ge13 = sum(v for k, v in hist.items() if k >= 13)

vals_sorted = sorted(all_deg)
total_deg = sum(vals_sorted)
top_share = {}
s = 0
for k in range(1, 101):
    s += vals_sorted[-k] if len(vals_sorted) >= k else 0
    top_share["top%d" % k] = rou(s / float(total_deg) * 100, 1)
top100_n = 0
if len(vals_sorted) >= 100:
    thr = vals_sorted[-100]
    top100_n = sum(1 for d in all_deg if d >= thr)

degree = {
    "n_persons": n_persons,
    "isolated": n_isolated,
    "isolated_pct": rou(n_isolated / float(n_persons) * 100, 1),
    "linked": n_linked,
    "linked_pct": rou(n_linked / float(n_persons) * 100, 1),
    "gini_all": rou(md.gini([float(d) for d in all_deg]), 4),
    "gini_linked": rou(md.gini([float(d) for d in all_deg if d > 0]), 4),
    "mean_all": rou(total_deg / float(n_persons), 3),
    "mean_linked": rou(total_deg / float(n_linked), 3),
    "max_degree": max(all_deg),
    "hist_le12": hist_le12,
    "hist_labels": [str(i) for i in range(0, 13)],
    "hist_ge13": degree_ge13,
    "hist_ge13_pct": rou(degree_ge13 / float(n_persons) * 100, 1),
    "top_share": top_share,
    "top100_n": top100_n,
    "top100_pct_of_persons": rou(top100_n / float(n_persons) * 100, 1),
}

# ---------------- 3. 幂律（Hill 估计 + α̂ 随 xmin 漂移） ----------------
tail_vals = [d for d in all_deg if d >= 2]


def hill_alpha(xs, xmin):
    sel = [x for x in xs if x >= xmin]
    if len(sel) < 5:
        return None, len(sel)
    sm = sum(math.log(x / float(xmin)) for x in sel)
    if sm <= 0:
        return None, len(sel)
    return 1.0 + len(sel) / sm, len(sel)


xmin_list = [2, 3, 5, 8, 10, 15]
fits = []
for xm in xmin_list:
    a, n = hill_alpha(tail_vals, xm)
    fits.append({"xmin": xm, "alpha": rou(a, 3), "n_tail": n})
alphas = [f["alpha"] for f in fits]
powerlaw = {
    "fits": fits,
    "alpha_min": min(alphas),
    "alpha_max": max(alphas),
    "alpha_drift": rou(max(alphas) - min(alphas), 3),
    "n_tail_at_xmin10": [f["n_tail"] for f in fits if f["xmin"] == 10][0],
    "xmin_at_max_alpha": fits[alphas.index(max(alphas))]["xmin"],
    "xmin_at_min_alpha": fits[alphas.index(min(alphas))]["xmin"],
    "verdict": "不主张幂律：α̂ 随 xmin 系统性漂移且尾样本过小",
}

# ---------------- 4. 连通性 ----------------
adj = defaultdict(set)
for r in md.relations():
    f, t = r.get("from"), r.get("to")
    if f and t:
        adj[f].add(t)
        adj[t].add(f)
nodes_with_edges = len(adj)
seen = set()
comps = []
for n0 in adj:
    if n0 in seen:
        continue
    stack, cur = [n0], []
    seen.add(n0)
    while stack:
        u = stack.pop()
        cur.append(u)
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    comps.append(len(cur))
comps.sort(reverse=True)
giant = comps[0] if comps else 0
connectivity = {
    "nodes_with_edges": nodes_with_edges,
    "components": len(comps),
    "giant_size": giant,
    "giant_pct_of_nodes": rou(giant / float(nodes_with_edges) * 100, 1),
    "giant_pct_of_persons": rou(giant / float(n_persons) * 100, 1),
    "outside_giant_with_edges": nodes_with_edges - giant,
    "component_sizes_top": comps[:12],
}

# ---------------- 5. 事件时间序列 ----------------
eby = md.events_by_year()
years = sorted(eby)
vals = [eby[y] for y in years]
n_events_yearly = sum(vals)
mean_y = n_events_yearly / float(len(years))
sd_y = math.sqrt(sum((v - mean_y) ** 2 for v in vals) / float(len(vals)))
peak_years = sorted(eby, key=lambda y: (-eby[y], y))[:10]
dec = defaultdict(int)
for y in years:
    dec[(y // 10) * 10] += eby[y]
dec_list = sorted(dec)
time_series = {
    "n_events_with_year": n_events_yearly,
    "n_events_total": corpus["events"],
    "n_years": len(years),
    "year_min": years[0] if years else None,
    "year_max": years[-1] if years else None,
    "mean_per_year": rou(mean_y, 3),
    "sd_per_year": rou(sd_y, 3),
    "cv": rou(sd_y / mean_y, 3) if mean_y else 0.0,
    "gini_by_year": rou(md.gini([float(v) for v in vals]), 4),
    "peak_years": [{"year": y, "n": eby[y]} for y in peak_years],
    "decades": [{"label": "%ds" % d, "value": dec[d]} for d in dec_list],
    "empty_years": (years[0] - 1300 - len(years)) if years else 0,
}

# ---------------- 6. 时期切分与类别迁移 ----------------
PERIODS = [("P1", 1368, 1499), ("P2", 1500, 1599), ("P3", 1600, 1662)]
cats_all = [e["name"] for e in md.event_categories()]
tab = defaultdict(lambda: defaultdict(int))
per_n = {}
for (pn, y0, y1) in PERIODS:
    c = Counter(e.get("category") or "未分类" for e in md.events()
                if isinstance(e.get("year"), int) and y0 <= e["year"] <= y1)
    per_n[pn] = sum(c.values())
    for kk, v in c.items():
        tab[pn][kk] = v
rows = []
for c in cats_all:
    row = {"cat": c}
    for (pn, _, _) in PERIODS:
        n = tab[pn].get(c, 0)
        t = per_n[pn] or 1
        row[pn] = n
        row[pn + "_pct"] = rou(n / float(t) * 100, 1)
    rows.append(row)
used_cats = [r["cat"] for r in rows if any(r[pn] for (pn, _, _) in PERIODS)]
# 期望频数取「类别 × 时期」两向边际的乘积（非条件占比）
cat_tot = {}
for r in rows:
    cat_tot[r["cat"]] = sum(r[pn] for (pn, _, _) in PERIODS)
n_total = sum(per_n.values())
chi2 = 0.0
for c in used_cats:
    row = [r for r in rows if r["cat"] == c][0]
    for (pn, _, _) in PERIODS:
        obs = row[pn]
        exp = cat_tot[c] / float(n_total) * per_n[pn]
        chi2 += (obs - exp) ** 2 / exp if exp else 0.0
dfree = (len(PERIODS) - 1) * (len(used_cats) - 1)


def chi2_sf(x, k):
    t = math.exp(-x / 2.0)
    s = t
    for j in range(1, k):
        t = t * (x / 2.0) / j
        s += t
    return s


pval = chi2_sf(chi2, dfree // 2) if dfree % 2 == 0 else 0.0
v_cramer = math.sqrt(chi2 / float(n_total * (min(len(PERIODS), len(used_cats)) - 1)))
shift = []
for c in ["军事战争", "政治斗争", "民生经济", "社会变动"]:
    hit = [r for r in rows if r["cat"] == c]
    if not hit:
        continue
    r = hit[0]
    shift.append({"cat": c,
                  "P1": r.get("P1_pct"), "P2": r.get("P2_pct"), "P3": r.get("P3_pct")})
periods = {
    "periods": [{"label": "%s %d-%d" % (pn, y0, y1), "n_events": per_n[pn],
                 "y0": y0, "y1": y1} for (pn, y0, y1) in PERIODS],
    "table": rows, "used_cats": used_cats, "n_total": n_total,
    "chi2": rou(chi2, 2), "df": dfree,
    "p": ("<1e-6" if pval < 1e-6 else "%.3g" % pval),
    "cramers_v": rou(v_cramer, 3),
    "shift": shift,
}

# ---------------- 7. 每期参与人物 ----------------
per_nodes = {}
for (pn, y0, y1) in PERIODS:
    s = set()
    for e in md.events():
        if isinstance(e.get("year"), int) and y0 <= e["year"] <= y1:
            for nm in (e.get("participants") or []):
                if nm:
                    s.add(nm)
    per_nodes[pn] = len(s)
participants = {"per_period": per_nodes}

# ---------------- 8. 原书证据（逐字命中，0 命中即弃） ----------------
book_evidence = []
for ph in ["苟延残喘的骆驼，只等生命中那最后一根稻草",
           "上天给元朝的最后一根稻草终于压了下来",
           "史云：明朝亡于党争。我云：党争，起于此时。",
           "一片亡国之象",
           "让我们看看现在的大明王朝的五个关键词",
           "明朝亡于党争",
           "大厦将倾，独木难支"]:
    book_evidence.append({"phrase": ph, "hits": md.hit_text(ph)})

# ---------------- 9. 图用数据 ----------------
out = {
    "pid": PID,
    "title_cn": "崩塌的涌现：复杂网络中的明朝兴衰",
    "corpus": corpus,
    "degree": degree,
    "powerlaw": powerlaw,
    "connectivity": connectivity,
    "time_series": time_series,
    "periods": periods,
    "participants": participants,
    "book_evidence": book_evidence,
    "fig": {
        "fig1": [{"label": str(i), "value": degree["hist_le12"][i]} for i in range(13)],
        "fig2": time_series["decades"],
        "fig3": shift,
    },
}

md.write_stats(PID, out)
print("WROTE .dump/_stats_%s.json" % PID)
print("  gini_all", degree["gini_all"], " gini_linked", degree["gini_linked"],
      " isolated", degree["isolated"], degree["isolated_pct"])
print("  mean_all", degree["mean_all"], " mean_linked", degree["mean_linked"],
      " max", degree["max_degree"])
print("  components", connectivity["components"], " giant", connectivity["giant_size"])
print("  alpha fits:", [(f["xmin"], f["alpha"], f["n_tail"]) for f in fits])
print("  n_events_with_year", n_events_yearly, " n_years", len(years),
      " cv", time_series["cv"], " gini_by_year", time_series["gini_by_year"])
print("  chi2", periods["chi2"], "df", dfree, "V", periods["cramers_v"], "p", periods["p"])
print("  per_period persons", participants["per_period"])
print("  shift", [(x["cat"], x["P1"], x["P2"], x["P3"]) for x in shift])
print("  book_evidence:", [(b["hits"], b["phrase"][:12]) for b in book_evidence])
