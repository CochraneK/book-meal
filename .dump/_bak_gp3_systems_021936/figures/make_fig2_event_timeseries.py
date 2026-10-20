# -*- coding: utf-8 -*-
"""Fig.2 —— 事件时间序列（按十年聚合）与分期边界。

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

T = S["time_series"]
dec = T["decade"]
xs = [d["decade"] for d in dec]
ys = [d["n"] for d in dec]

fig, ax = plt.subplots(figsize=(7.0, 3.2), dpi=150)
ax.bar(xs, ys, width=9.0, color="#3b5f8a", edgecolor="#333333", linewidth=0.35)
# 分期分隔线（P1/P2 与 P2/P3 的边界）
for b, lab in ((1500, "P1|P2"), (1600, "P2|P3")):
    ax.axvline(b - 0.5, color="#c0504d", linestyle="--", linewidth=1.0)
    ax.text(b - 0.5, max(ys) * 0.95, " %s" % lab, fontsize=7.5, color="#c0504d")
# 峰值年份标注
for p in T["peak_years"][:5]:
    ax.annotate("%d" % p["year"], xy=(p["year"], 0), xytext=(p["year"], -0.13),
                textcoords=("data", "axes fraction"), ha="center", fontsize=7,
                color="#555555")
ax.set_xlabel("年代（按十年聚合）", fontsize=9)
ax.set_ylabel("事件数", fontsize=9)
ax.set_xlim(1320, 1660)
ax.set_ylim(0, max(ys) * 1.16)
ax.text(0.015, 0.93,
        "有年份事件 %d 件，覆盖 %d 个年份（%d–%d），空年 %d 个"
        % (T["n_events_with_year"], T["n_years"], T["year_min"], T["year_max"], T["gaps"]),
        transform=ax.transAxes, fontsize=8, va="top", color="#333333")
ax.text(0.015, 0.82,
        "年均 %.3f 件，标准差 %.3f，变异系数 %.3f，年度基尼 %.4f"
        % (T["mean_per_year"], T["sd_per_year"], T["cv"], T["gini_by_year"]),
        transform=ax.transAxes, fontsize=8, va="top", color="#333333")
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
