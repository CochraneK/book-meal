# -*- coding: utf-8 -*-
"""Fig.1 —— 人物关系网络的度分布与集中度。

左：度直方图（0–12 真实分箱 + ≥13 汇总桶，不沿用被截断的键名）；
右：Top-k 人数所占的度数份额（累计曲线）。
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

D = S["degree"]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.3), dpi=150)

# --- 左：度直方图 ---
hist = D["hist_le12"]
ks = sorted(int(k) for k in hist.keys())
labels = [str(k) for k in ks] + ["≥13"]
vals = [hist[str(k)] for k in ks] + [D["degree_ge13"]]
colors = ["#c0504d"] + ["#3b5f8a"] * (len(ks) - 1) + ["#7f7f7f"]
ax1.bar(range(len(labels)), vals, color=colors, width=0.66,
        edgecolor="#333333", linewidth=0.35)
ax1.set_xticks(range(len(labels)))
ax1.set_xticklabels(labels, fontsize=7.8)
ax1.set_xlabel("无向关系度数", fontsize=9)
ax1.set_ylabel("人数", fontsize=9)
ax1.set_yscale("log")
ax1.set_ylim(0.8, max(vals) * 2.2)
ax1.text(0.03, 0.95, "孤立点 %d 人（%.1f%%）" % (D["isolated"], D["isolated_pct"]),
         transform=ax1.transAxes, fontsize=8, va="top", color="#333333")
ax1.text(0.03, 0.83, "基尼 %.4f（全部）/ %.4f（度>0）" % (D["gini_all"], D["gini_linked"]),
         transform=ax1.transAxes, fontsize=8, va="top", color="#333333")
ax1.text(0.03, 0.71, "最大度 %d，均值 %.3f" % (D["max_degree"], D["mean_all"]),
         transform=ax1.transAxes, fontsize=8, va="top", color="#333333")

# --- 右：Top-k 度数份额累计 ---
ts = D["top_share"]
ks2 = [1, 5, 10, 20, 50, 100]
vs = [ts["top%d" % k] for k in ks2]
ax2.plot(range(len(ks2)), vs, "o-", color="#3b5f8a", linewidth=1.4, markersize=4)
ax2.set_xticks(range(len(ks2)))
ax2.set_xticklabels(["Top%d" % k for k in ks2], fontsize=8)
ax2.set_xlabel("按度数降序取前 k 人（共 %d 人）" % D["n_persons"], fontsize=9)
ax2.set_ylabel("占全部关系端点数的份额（%）", fontsize=9)
ax2.set_ylim(0, 72)
for i, v in enumerate(vs):
    ax2.text(i, v + 2.2, "%.1f" % v, ha="center", fontsize=7.8)
ax2.text(0.04, 0.90, "Top100（占人物 %.1f%%）持有 %.1f%% 的度数"
         % (D["top100_pct_of_persons"], ts["top100"]),
         transform=ax2.transAxes, fontsize=8, va="top", color="#333333")

for a in (ax1, ax2):
    a.spines["top"].set_visible(False)
    a.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_1.pdf" % PID)
png = os.path.join(OUT, "fig_%s_1.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
print("WROTE", pdf, os.path.getsize(pdf), "B |", png, os.path.getsize(png), "B")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000
print("SELF-CHECK OK")
