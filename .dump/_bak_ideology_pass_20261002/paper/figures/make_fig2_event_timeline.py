# -*- coding: utf-8 -*-
"""思想相关事件时间序列；图内不写标题。"""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"D:\2026\WB项目\明朝"
OUT = os.path.join(ROOT, "papers_pilot", "ideology", "paper", "figures")
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_ideology.json"), encoding="utf-8"))
plt.rcParams.update({"font.family": ["Noto Serif SC", "SimSun", "SimHei"], "font.size": 8,
                     "axes.unicode_minus": False, "pdf.fonttype": 42, "ps.fonttype": 42})
rows = S["ideology_events"]
colors = {"人物生平": "#444444", "政治斗争": "#9a9a9a"}
fig, ax = plt.subplots(figsize=(7.0, 2.55), dpi=150)
used = set()
for i, e in enumerate(rows):
    y = e["year"]; cat = e["category"]
    ax.vlines(y, 0, 1.0, color=colors[cat], linewidth=1.0)
    label = cat if cat not in used else None; used.add(cat)
    ax.scatter([y], [1.0], s=32, color=colors[cat], edgecolor="white", linewidth=0.5, label=label, zorder=3)
    short = e["name"].replace("王守仁", "").replace("天下", "")
    ax.text(y, 1.08 + 0.14 * (i % 2), short, rotation=35, ha="left", va="bottom", fontsize=6.5)
ax.axvspan(1508, 1528, color="#dddddd", alpha=0.35)
ax.set_xlim(1482, 1600); ax.set_ylim(0, 1.8)
ax.set_yticks([]); ax.set_xlabel("年份")
ax.legend(frameon=False, loc="upper left", ncol=2)
for side in ("top", "right", "left"): ax.spines[side].set_visible(False)
ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#cccccc")
fig.tight_layout()
pdf = os.path.join(OUT, "fig_ideology_2.pdf"); png = os.path.join(OUT, "fig_ideology_2.png")
fig.savefig(pdf, bbox_inches="tight"); fig.savefig(png, dpi=150, bbox_inches="tight"); plt.close(fig)
assert open(pdf, "rb").read(5) == b"%PDF-" and os.path.getsize(pdf) > 5000
assert os.path.getsize(png) > 5000
print("SELF-CHECK OK", pdf)
