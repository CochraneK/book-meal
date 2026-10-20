# -*- coding: utf-8 -*-
"""Fig.1 —— 政治攻讦 / 敌对冲突 在全书七部中的占比变化。

数据：.dump/_stats_info.json
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

ROOT = r"D:\2026\WB项目\明朝"
PID = "info"
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_%s.json" % PID), encoding="utf-8"))
OUT = os.path.join(ROOT, "papers_pilot", PID, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

parts = [str(k) for k in range(1, 8)]
abp = S["attack_by_part"]
sh_atk = [abp["政治攻讦"]["share_by_part"][p] for p in parts]
sh_foe = [abp["敌对冲突"]["share_by_part"][p] for p in parts]
n_atk = [abp["政治攻讦"]["by_part"][p] for p in parts]
n_foe = [abp["敌对冲突"]["by_part"][p] for p in parts]
den = [S["relations_by_part"][p] for p in parts]

x = range(1, 8)
fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=150)

ax.bar([i - 0.19 for i in x], sh_atk, width=0.38, color="#3b5f8a", label="政治攻讦")
ax.bar([i + 0.19 for i in x], sh_foe, width=0.38, color="#b0b0b0", label="敌对冲突")
ax.plot(list(x), sh_atk, color="#1f3a5c", marker="o", ms=4, lw=1.2)
ax.plot(list(x), sh_foe, color="#6a6a6a", marker="s", ms=4, lw=1.2, ls="--")

for i, (a, f) in enumerate(zip(sh_atk, sh_foe)):
    ax.text(i + 1 - 0.19, a + 0.6, "%.1f" % a, ha="center", fontsize=7.5, color="#1f3a5c")
    ax.text(i + 1 + 0.19, f + 0.6, "%.1f" % f, ha="center", fontsize=7.5, color="#6a6a6a")

ax.set_xticks(list(x))
ax.set_xticklabels(["第%d部\n(%d/%d)" % (i, n_atk[i - 1], den[i - 1]) for i in x], fontsize=8)
ax.set_xlabel("全书分部（括号内为该部攻讦关系数 / 该部关系总数）", fontsize=9)
ax.set_ylabel("占该部全部关系的比重（%）", fontsize=9)
ax.set_ylim(0, max(max(sh_atk), max(sh_foe)) * 1.28)
ax.legend(loc="upper left", fontsize=8, frameon=False)
ax.grid(axis="y", ls=":", lw=0.5, alpha=0.6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()

pdf = os.path.join(OUT, "fig_%s_1.pdf" % PID)
png = os.path.join(OUT, "fig_%s_1.png" % PID)
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, dpi=150, bbox_inches="tight")
assert open(pdf, "rb").read(5) == b"%PDF-"
assert os.path.getsize(pdf) > 5000 and os.path.getsize(png) > 5000
print("WROTE", pdf, os.path.getsize(pdf), "B")
print("SELF-CHECK OK")
