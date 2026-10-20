# -*- coding: utf-8 -*-
"""Fig.2 —— 事件时间序列（十年桶），标注三个分期边界。

数据从 .dump/_stats_systems.json 的 time_series.decades 读；图内不写标题（图题只进 \\caption）。
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

T = S["time_series"]
dec = T["decades"]
xs = [float(d["label"].rstrip("s")) for d in dec]
ys = [float(d["value"]) for d in dec]

fig, ax = plt.subplots(figsize=(7.0, 3.0), dpi=150)
ax.bar(xs, ys, width=8.0, color="#3b5f8a", edgecolor="#333333", linewidth=0.3)
ax.axvline(1368.0, color="#c0504d", linestyle="--", linewidth=1.0)
ax.axvline(1500.0, color="#7f7f7f", linestyle=":", linewidth=1.0)
ax.axvline(1600.0, color="#7f7f7f", linestyle=":", linewidth=1.0)
ax.set_xlabel("十年桶（起始年）", fontsize=9)
ax.set_ylabel("事件数", fontsize=9)
ax.set_ylim(0, max(ys) * 1.16)
ax.set_xticks([d for d in xs if d % 20 == 0 or d in (1390.0, 1590.0, 1630.0)])
ax.tick_params(axis="both", labelsize=8)
# 数据标注（非标题）：三个最高的十年与单年峰值
for x, y in zip(xs, ys):
    if y >= 60:
        ax.text(x, y + max(ys) * 0.02, str(int(y)), ha="center", fontsize=7.5)
ax.text(0.985, 0.96,
        "单年峰值：%d 年 %d 件；年均 %.3f 件，变异系数 %.2f"
        % (T["peak_years"][0]["year"], T["peak_years"][0]["n"],
           T["mean_per_year"], T["cv"]),
        transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color="#333333")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_2.pdf" % PID)
png = os.path.join(OUT, "fig_%s_2.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
print("WROTE", pdf, os.path.getsize(pdf), "B |", png, os.path.getsize(png), "B")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000
print("SELF-CHECK OK")
