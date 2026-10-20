# -*- coding: utf-8 -*-
"""Fig.3 —— 信息型机构（厂卫系）与其代理人（内廷宦官）在图谱中的结构位置对比。

三组分柱：平均关系度数 / 平均出场章节数 / 占攻讦关系端点的比重。
数据：.dump/_stats_info.json
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = ["Noto Serif SC", "SimSun", "SimHei"]
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["axes.unicode_minus"] = False

ROOT = r"D:\2026\WB项目\明朝"
PID = "info"
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_%s.json" % PID), encoding="utf-8"))
OUT = os.path.join(ROOT, "papers_pilot", PID, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

I = S["institutional_persons"]
groups = ["厂卫系", "内廷宦官", "全库基线"]
labels = ["平均关系度数", "平均出场章节数", "占攻讦端点比重（%）"]
keys = ["mean_degree", "mean_chapters", "endpoint_share"]
vals = {g: [I[g].get(k, 0.0) for k in keys] for g in groups}

x = np.arange(len(labels))
w = 0.26
fig, ax = plt.subplots(figsize=(7.0, 3.4), dpi=150)
cols = {"厂卫系": "#3b5f8a", "内廷宦官": "#a8673b", "全库基线": "#9a9a9a"}
for i, g in enumerate(groups):
    off = (i - 1) * w
    b = ax.bar(x + off, vals[g], width=w, color=cols[g], label="%s（%d 人）" % (g, I[g]["n"]))
    for r, v in zip(b, vals[g]):
        ax.text(r.get_x() + r.get_width() / 2, v + (0.12 if v < 10 else 0.5),
                "%.2f" % v, ha="center", fontsize=7.5)

ax.set_xticks(list(x))
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("数值", fontsize=9)
ax.legend(fontsize=8, frameon=False, loc="upper left")
ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_3.pdf" % PID)
png = os.path.join(OUT, "fig_%s_3.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000 and os.path.getsize(png) > 5000
print("WROTE", pdf, os.path.getsize(pdf), "B")
print("SELF-CHECK OK")
