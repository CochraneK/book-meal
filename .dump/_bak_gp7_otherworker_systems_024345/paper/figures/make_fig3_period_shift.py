# -*- coding: utf-8 -*-
"""Fig.3 —— 三期事件类别构成的迁移 + 卡方/效应量。

数据从 .dump/_stats_systems.json 的 periods.shift / periods.chi2 / periods.cramers_v 读。
图内不写标题（图题只进 \\caption）。
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

P = S["periods"]
sh = P["shift"]
order = ["P1", "P2", "P3"]
xs = [1, 2, 3]
COLORS = ["#3b5f8a", "#c0504d", "#7f7f7f", "#9bb0c6"]

fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.0, 3.0), dpi=150)

for i, row in enumerate(sh):
    ys = [float(row[p]) for p in order]
    ax0.plot(xs, ys, marker="o", linewidth=1.2, markersize=4, color=COLORS[i])
    for x, y in zip(xs, ys):
        ax0.annotate("%.1f" % y, (x, y), textcoords="offset points", xytext=(0, 5),
                     ha="center", fontsize=7, color=COLORS[i])
ax0.set_xticks(xs)
ax0.set_xticklabels(["P1\n1368--1499", "P2\n1500--1599", "P3\n1600--1662"], fontsize=8)
ax0.set_ylabel("事件类别占比（%）", fontsize=9)
ax0.set_ylim(0, max([float(r[p]) for r in sh for p in order]) * 1.30)
ax0.tick_params(axis="y", labelsize=8)
ax0.text(0.03, 0.04,
         "军事战争 28.9 / 21.8 / 40.9\n政治斗争 33.9 / 40.8 / 21.5",
         transform=ax0.transAxes, ha="left", va="bottom", fontsize=7.5, color="#333333")
ax0.spines["top"].set_visible(False)
ax0.spines["right"].set_visible(False)

ratio = []
for k, p in enumerate(order):
    m = [r for r in sh if r["cat"] == "军事战争"][0][p]
    pol = [r for r in sh if r["cat"] == "政治斗争"][0][p]
    if pol:
        ratio.append(float(m) / float(pol) * 100.0)
ax1.plot(xs[:len(ratio)], ratio, marker="s", color="#3b5f8a", linewidth=1.2, markersize=4)
for x, y in zip(xs[:len(ratio)], ratio):
    ax1.annotate("%.0f" % y, (x, y), textcoords="offset points", xytext=(0, 5),
                 ha="center", fontsize=7.5)
ax1.set_xticks(xs[:len(ratio)])
ax1.set_xticklabels(["P1", "P2", "P3"], fontsize=8)
ax1.set_ylabel("军事战争 / 政治斗争（%）", fontsize=9)
ax1.tick_params(axis="y", labelsize=8)
ax1.text(0.985, 0.04,
         "$\\chi^2$ = %s, df = %d, V = %.3f" % (P["chi2"], P["df"], P["cramers_v"]),
         transform=ax1.transAxes, ha="right", va="bottom", fontsize=7.5, color="#333333")
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

fig.tight_layout()
pdf = os.path.join(OUT, "fig_%s_3.pdf" % PID)
png = os.path.join(OUT, "fig_%s_3.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
print("WROTE", pdf, os.path.getsize(pdf), "B |", png, os.path.getsize(png), "B")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000
print("SELF-CHECK OK")
