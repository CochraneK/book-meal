# -*- coding: utf-8 -*-
"""Fig.3 —— 三期事件类别构成的迁移（1368–1499 / 1500–1599 / 1600–1662）。

左：六个关键类别在三个时期的占比折线；右：战争/政治之比的变化。
数据从 .dump/_stats_systems.json 读；图内不写标题。
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
shift = P["shift"]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.3), dpi=150,
                               gridspec_kw={"width_ratios": [1.6, 1]})

KEYS = ["军事战争", "政治斗争", "制度科举", "民变起义", "案件刑狱", "人事任免"]
COLORS = {"军事战争": "#c0504d", "政治斗争": "#3b5f8a", "制度科举": "#4f8a4f",
          "民变起义": "#c98a2e", "案件刑狱": "#8064a2", "人事任免": "#7f7f7f"}
xs = [0, 1, 2]
XT = ["P1\n1368–1499", "P2\n1500–1599", "P3\n1600–1662"]
for k in KEYS:
    ax1.plot(xs, [shift[k]["P1"], shift[k]["P2"], shift[k]["P3"]],
             "o-", color=COLORS[k], linewidth=1.4, markersize=4, label=k)
    for i, x in enumerate(xs):
        ax1.annotate("%.1f" % [shift[k]["P1"], shift[k]["P2"], shift[k]["P3"]][i],
                     (x, [shift[k]["P1"], shift[k]["P2"], shift[k]["P3"]][i]),
                     textcoords="offset points", xytext=(0, 4), ha="center", fontsize=6.8)
ax1.set_xticks(xs)
ax1.set_xticklabels(XT, fontsize=8)
ax1.set_ylabel("占该期事件数的比例（%）", fontsize=9)
ax1.set_ylim(-1, 46)
ax1.legend(fontsize=7, ncol=3, frameon=False, loc="upper left")
ax1.text(0.99, 0.02, "卡方 %.2f，df %d，Cramér's V %.3f"
         % (P["chi2"], P["chi2_df"], P["cramers_v"]),
         transform=ax1.transAxes, ha="right", fontsize=7.5, color="#333333")

# --- 右：战争 / 政治 之比 ---
w = P["war_over_politics"]
names = ["军事战争 / 政治斗争"]
ax2.bar(range(3), [w["P1"], w["P2"], w["P3"]],
        color=["#9bb0c6", "#7f9dc0", "#c0504d"], width=0.55,
        edgecolor="#333333", linewidth=0.4)
ax2.set_xticks(range(3))
ax2.set_xticklabels(["P1", "P2", "P3"], fontsize=8.5)
ax2.set_ylabel("事件条数之比", fontsize=9)
ax2.axhline(1.0, color="#333333", linestyle=":", linewidth=0.9)
for i, k in enumerate(["P1", "P2", "P3"]):
    ax2.text(i, w[k] + 0.05, "%.3f" % w[k], ha="center", fontsize=8)
ax2.set_ylim(0, max(w.values()) * 1.25)
ax2.text(0.03, 0.95, "P3 战争条数反超政治", transform=ax2.transAxes,
         fontsize=7.5, va="top", color="#333333")

for a in (ax1, ax2):
    a.spines["top"].set_visible(False)
    a.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_3.pdf" % PID)
png = os.path.join(OUT, "fig_%s_3.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
print("WROTE", pdf, os.path.getsize(pdf), "B |", png, os.path.getsize(png), "B")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000
print("SELF-CHECK OK")
