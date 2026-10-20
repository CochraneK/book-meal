# -*- coding: utf-8 -*-
"""Fig.3 —— 家语与国语的双向渗透：
  左：亲属关系（185 条）里带国家/权力语汇的比例；
  右：各类非亲属关系里带亲属语汇的比例（宽口径 / 严格口径对照）。

数据从 .dump/_stats_anthropology.json 读；图内不写标题。
"""
import json, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

plt.rcParams["font.family"] = ["Noto Serif SC", "SimSun", "SimHei"]
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["axes.unicode_minus"] = False

PID = "anthropology"
ROOT = r"D:\2026\WB项目\明朝"
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_%s.json" % PID), encoding="utf-8"))
OUT = os.path.join(ROOT, "papers_pilot", PID, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

V = S["state_kin_vocab"]
K = S["kinship"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.4), dpi=150,
                               gridspec_kw={"width_ratios": [1, 1.55]})

# --- 左：亲属类里国家语汇的占比（单柱占比条） ---
pw = K["power_lexicon_pct"]
ax1.bar([0], [pw], width=0.45, color="#c0504d", edgecolor="#333333", linewidth=0.4)
ax1.bar([0], [100 - pw], bottom=[pw], width=0.45, color="#e8e8e8",
        edgecolor="#333333", linewidth=0.4)
ax1.set_xticks([0])
ax1.set_xticklabels(["亲属关系\n（n=%d）" % K["n"]], fontsize=8.5)
ax1.set_ylabel("占比（%）", fontsize=9)
ax1.set_ylim(0, 100)
ax1.text(0, pw / 2.0, "含国家/权力语汇\n%d 条 = %.1f%%"
         % (K["power_lexicon_n"], pw), ha="center", fontsize=8, color="white")
ax1.text(0, pw + (100 - pw) / 2.0, "其余 %d 条" % (K["n"] - K["power_lexicon_n"]),
         ha="center", fontsize=8)

# --- 右：各类非亲属关系里亲属语汇的占比 ---
rows = [c for c in V["by_category"] if c["n"] >= 60]
rows.sort(key=lambda c: -c["pct"])
names = [c["category"] for c in rows]
wide = [c["pct"] for c in rows]
strict = [c["pct_strict"] for c in rows]
y = list(range(len(names)))[::-1]
h = 0.36
ax2.barh([yy + h / 2 for yy in y], wide, height=h, color="#3b5f8a",
         edgecolor="#333333", linewidth=0.4)
ax2.barh([yy - h / 2 for yy in y], strict, height=h, color="#9bb0c6",
         edgecolor="#333333", linewidth=0.4)
ax2.set_yticks(y)
ax2.set_yticklabels(names, fontsize=8.5)
ax2.set_xlabel("含亲属语汇的关系占比（%）", fontsize=9)
for i, (w, s) in enumerate(zip(wide, strict)):
    ax2.text(w + 0.25, y[i] + h / 2, "%.1f" % w, va="center", fontsize=7.5)
    ax2.text(s + 0.25, y[i] - h / 2, "%.1f" % s, va="center", fontsize=7.5)
ax2.set_xlim(0, max(wide) * 1.42)
ax2.legend(handles=[Patch(facecolor="#3b5f8a", edgecolor="#333333", label="宽口径（含太子/皇子等职称化词）"),
                    Patch(facecolor="#9bb0c6", edgecolor="#333333", label="严格口径（仅纯亲属词）")],
           fontsize=7, loc="lower right", frameon=False)

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
