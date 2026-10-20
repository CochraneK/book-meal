# -*- coding: utf-8 -*-
"""Fig.2 —— 亲属关系的代际跨度分布 + 纵向关系的方向不对称。

数据从 .dump/_stats_anthropology.json 读；图内不写标题。
"""
import json, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Noto Serif SC", "SimSun", "SimHei"]
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["axes.unicode_minus"] = False

PID = "anthropology"
ROOT = r"D:\2026\WB项目\明朝"
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_%s.json" % PID), encoding="utf-8"))
OUT = os.path.join(ROOT, "papers_pilot", PID, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

K = S["kinship"]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.2), dpi=150)

# --- 左：代际跨度 ---
sp = K["span_counts"]
labels = ["0 代（同辈）", "1 代", "2 代"]
vals = [sp.get("0", 0), sp.get("1", 0), sp.get("2", 0)]
pcts = [K["span_pct"].get("0", 0.0), K["span_pct"].get("1", 0.0), K["span_pct"].get("2", 0.0)]
b = ax1.bar(range(3), vals, color=["#7f7f7f", "#3b5f8a", "#c0504d"],
            width=0.6, edgecolor="#333333", linewidth=0.4)
ax1.set_xticks(range(3))
ax1.set_xticklabels(labels, fontsize=8.5)
ax1.set_ylabel("亲属关系条数", fontsize=9)
for i, (v, p) in enumerate(zip(vals, pcts)):
    ax1.text(i, v + 1.4, "%d\n%.1f%%" % (v, p), ha="center", fontsize=8)
ax1.set_ylim(0, max(vals) * 1.30)

# --- 右：纵向关系的方向不对称 ---
down = K["direction_counts"].get("down", 0)
up = K["direction_counts"].get("up", 0)
ax2.bar([0], [down], color="#3b5f8a", width=0.5, edgecolor="#333333", linewidth=0.4)
ax2.bar([1], [up], color="#c0504d", width=0.5, edgecolor="#333333", linewidth=0.4)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(["长辈→晚辈", "晚辈→长辈"], fontsize=8.5)
ax2.set_ylabel("纵向关系条数", fontsize=9)
ax2.text(0, down + 1.5, str(down), ha="center", fontsize=9)
ax2.text(1, up + 1.5, str(up), ha="center", fontsize=9)
ax2.set_ylim(0, max(down, up) * 1.30)
ax2.text(0.97, 0.90, "下行 : 上行 = %.1f : 1" % K["down_up_ratio"],
         transform=ax2.transAxes, ha="right", fontsize=8, color="#333333")
ax2.text(0.97, 0.76, "纵向跨度均值 %.3f 代（n=%d）"
         % (K["span_mean_vertical"], K["span_n_vertical"]),
         transform=ax2.transAxes, ha="right", fontsize=8, color="#333333")

for a in (ax1, ax2):
    a.spines["top"].set_visible(False)
    a.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_2.pdf" % PID)
png = os.path.join(OUT, "fig_%s_2.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
print("WROTE", pdf, os.path.getsize(pdf), "B |", png, os.path.getsize(png), "B")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000
print("SELF-CHECK OK")
