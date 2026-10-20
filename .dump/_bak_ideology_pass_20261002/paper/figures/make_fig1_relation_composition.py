# -*- coding: utf-8 -*-
"""思想组与权力参照组的显式关系构成；图内不写标题。"""
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

def values(key):
    d = S["groups"][key]
    return [d["teacher_peer_pct"], d["power_relation_pct"],
            round(100.0 - d["teacher_peer_pct"] - d["power_relation_pct"], 1)]

labels = ["思想相关组\n(n=90)", "权力参照组\n(n=77)"]
rows = [values("thought_explicit"), values("power_explicit")]
colors = ["#222222", "#777777", "#c8c8c8"]
names = ["师生同门", "权力关系", "其他"]
fig, ax = plt.subplots(figsize=(3.5, 2.45), dpi=150)
left = [0, 0]
for j, name in enumerate(names):
    vals = [r[j] for r in rows]
    bars = ax.barh(range(2), vals, left=left, color=colors[j], edgecolor="white", label=name)
    for i, (b, v) in enumerate(zip(bars, vals)):
        if v >= 8:
            ax.text(left[i] + v / 2, b.get_y() + b.get_height() / 2, f"{v:.1f}%",
                    ha="center", va="center", color="white" if j < 2 else "black", fontsize=7)
    left = [left[i] + vals[i] for i in range(2)]
ax.set_yticks(range(2)); ax.set_yticklabels(labels)
ax.set_xlim(0, 100); ax.set_xlabel("显式关系构成（%）")
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.20), fontsize=7)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#cccccc"); ax.set_axisbelow(True)
fig.tight_layout()
pdf = os.path.join(OUT, "fig_ideology_1.pdf"); png = os.path.join(OUT, "fig_ideology_1.png")
fig.savefig(pdf, bbox_inches="tight"); fig.savefig(png, dpi=150, bbox_inches="tight"); plt.close(fig)
assert open(pdf, "rb").read(5) == b"%PDF-" and os.path.getsize(pdf) > 5000
assert os.path.getsize(png) > 5000
print("SELF-CHECK OK", pdf)
