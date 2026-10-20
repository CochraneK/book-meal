# -*- coding: utf-8 -*-
"""Fig.1 —— 亲属关系的方向分布（长辈→晚辈 / 晚辈→长辈 / 平辈 / 单侧标记 / 未定）。

数据一律从 .dump/_stats_anthropology.json 读；图内不写标题（图题只进 \\caption）。
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
LABEL = {"down": "长辈→晚辈", "up": "晚辈→长辈", "flat": "平辈（兄弟/夫妻/姻亲）",
         "senior_only": "仅长辈词", "junior_only": "仅晚辈词", "unknown": "未定"}
ORDER = ["down", "up", "flat", "senior_only", "junior_only", "unknown"]
names = [LABEL[d] for d in ORDER]
vals = [K["direction_counts"].get(d, 0) for d in ORDER]
pcts = [K["direction_pct"].get(d, 0.0) for d in ORDER]
COLORS = ["#3b5f8a", "#c0504d", "#7f7f7f", "#9bb0c6", "#c9b79a", "#d9d9d9"]

fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=150)
y = list(range(len(names)))[::-1]
bars = ax.barh(y, vals, color=COLORS, height=0.68, edgecolor="#333333", linewidth=0.4)
ax.set_yticks(y)
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel("亲属关系条数（共 %d 条）" % K["n"], fontsize=10)
for i, (v, p) in enumerate(zip(vals, pcts)):
    ax.text(v + 1.2, y[i], "%d（%.1f%%）" % (v, p), va="center", fontsize=8.5)
ax.set_xlim(0, max(vals) * 1.28)
# 数据标注（非标题）：纵向合计与下行占纵向的比例
ax.text(0.985, 0.06,
        "纵向合计 %d 条（%.1f%%），其中下行占 %.1f%%"
        % (K["vertical_n"], K["vertical_pct"], K["down_share_of_vertical"]),
        transform=ax.transAxes, ha="right", fontsize=8, color="#333333")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_1.pdf" % PID)
png = os.path.join(OUT, "fig_%s_1.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
print("WROTE", pdf, os.path.getsize(pdf), "B |", png, os.path.getsize(png), "B")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000
print("SELF-CHECK OK")
