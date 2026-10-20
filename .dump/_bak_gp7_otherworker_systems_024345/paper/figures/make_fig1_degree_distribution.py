# -*- coding: utf-8 -*-
"""Fig.1 —— 度数直方图（0--12 逐度 + >=13 汇总桶）+ 集中度两条基线。

数据从 .dump/_stats_systems.json 的 degree.* 读；图内不写标题（图题只进 \\caption）。
注意：>=13 桶必须改名（图里写作 >=13），不得沿用被截断的键名。
"""
import json, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Noto Serif SC", "SimSun", "SimHei"]
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["axes.unicode_minus"] = False

PID = "systems"
ROOT = r"D:\2026\WB项目\明朝"
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_%s.json" % PID), encoding="utf-8"))
OUT = os.path.join(ROOT, "papers_pilot", PID, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

D = S["degree"]
hist = D["hist_le12"]
labels = [str(i) for i in range(13)] + ["$\\ge$13"]
vals = hist + [D["hist_ge13"]]
COLORS = ["#3b5f8a"] * 6 + ["#8f9bb3"] * 7 + ["#c0504d"]

fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.0, 3.0), dpi=150)

ax0.bar(list(range(len(vals))), vals, color=COLORS, width=0.68,
        edgecolor="#333333", linewidth=0.4)
ax0.set_xticks(list(range(len(vals))))
ax0.set_xticklabels(labels, fontsize=8)
ax0.set_xlabel("度数", fontsize=9)
ax0.set_ylabel("人数", fontsize=9)
ax0.set_ylim(0, max(vals) * 1.22)
ax0.tick_params(axis="y", labelsize=8)
for i, v in enumerate(vals):
    if v >= 40:
        ax0.text(i, v + max(vals) * 0.02, str(v), ha="center", fontsize=7.5)
ax0.text(0.985, 0.96,
         "0 度（孤立）%d 人；最大 %d" % (D["isolated"], D["max_degree"]),
         transform=ax0.transAxes, ha="right", va="top", fontsize=7.5, color="#333333")
ax0.spines["top"].set_visible(False)
ax0.spines["right"].set_visible(False)

ks = [1, 5, 10, 20, 50, 100]
ys = [D["top_share"]["top%d" % k] for k in ks]
ax1.plot(ks, ys, marker="o", color="#3b5f8a", linewidth=1.2, markersize=4)
ax1.set_xscale("log")
ax1.set_xticks(ks)
ax1.set_xticklabels([str(k) for k in ks], fontsize=8)
ax1.set_xlabel("度数排序前 k 位（对数轴）", fontsize=9)
ax1.set_ylabel("占全部度数和（%）", fontsize=9)
ax1.set_ylim(0, max(ys) * 1.25)
ax1.tick_params(axis="both", labelsize=8)
for k, y in zip(ks, ys):
    ax1.annotate("%.1f" % y, (k, y), textcoords="offset points", xytext=(0, 5),
                 ha="center", fontsize=7.5)
ax1.axhline(D["top_share"]["top100"], color="#c0504d", linestyle=":", linewidth=0.8)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

fig.tight_layout()
pdf = os.path.join(OUT, "fig_%s_1.pdf" % PID)
png = os.path.join(OUT, "fig_%s_1.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
print("WROTE", pdf, os.path.getsize(pdf), "B |", png, os.path.getsize(png), "B")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000
print("SELF-CHECK OK")
