# -*- coding: utf-8 -*-
"""Fig.2 —— 书内「公开渠道」与「隐秘渠道」信息机制词频对照（逐字命中，0 命中已弃用）。

数据：.dump/_stats_info.json
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Noto Serif SC", "SimSun", "SimHei"]
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["axes.unicode_minus"] = False

ROOT = r"D:\2026\WB项目\明朝"
PID = "info"
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_%s.json" % PID), encoding="utf-8"))
OUT = os.path.join(ROOT, "papers_pilot", PID, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

V = S["vocab_hits"]
rows = []
for w in V["公开渠道"]:
    rows.append((w["word"], w["n"], "#3b5f8a"))
for w in V["隐秘渠道"]:
    rows.append((w["word"], w["n"], "#a8673b"))
rows.sort(key=lambda r: r[1])

names = [r[0] for r in rows]
vals = [r[1] for r in rows]
cols = [r[2] for r in rows]

fig, ax = plt.subplots(figsize=(7.0, 4.4), dpi=150)
pos = range(len(names))
ax.barh(list(pos), vals, color=cols, height=0.68)
ax.set_yticks(list(pos))
ax.set_yticklabels(names, fontsize=9)
for i, v in enumerate(vals):
    ax.text(v + 2.5, i, "%d" % v, va="center", fontsize=8)
ax.set_xlabel("在原书全文中的逐字命中次数", fontsize=9)
ax.set_xlim(0, max(vals) * 1.18)

from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#3b5f8a", label="公开渠道（奏疏·弹劾·廷杖·诏狱）"),
                   Patch(color="#a8673b", label="隐秘渠道（厂卫·告密·谣言·黑名单）")],
          loc="lower right", fontsize=8, frameon=False)
ax.grid(axis="x", ls=":", lw=0.5, alpha=0.6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_2.pdf" % PID)
png = os.path.join(OUT, "fig_%s_2.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000 and os.path.getsize(png) > 5000
print("WROTE", pdf, os.path.getsize(pdf), "B")
print("SELF-CHECK OK")
