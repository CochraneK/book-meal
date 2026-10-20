# -*- coding: utf-8 -*-
"""Fig.2 —— 关系记录里可辨识的「信息型动作」动词在各关系类别中的条数。

一图一脚本 / 矢量 PDF / 图内不放标题（图题只进 LaTeX 的 caption）/ 渲染后自检。
数据全部来自 .dump/_stats_info.json，不许硬编码数字。
"""
import json, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STATS = r"D:\2026\WB项目\明朝\.dump\_stats_info.json"

plt.rcParams.update({
    "font.family": ["Noto Serif SC", "SimSun"],
    "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "figure.dpi": 150, "pdf.fonttype": 42, "ps.fonttype": 42,
})

CATS = ["政治攻讦", "敌对冲突", "君臣从属"]
COLORS = {"政治攻讦": "#2b4258", "敌对冲突": "#7f4f2a", "君臣从属": "#7f95ad"}


def main():
    S = json.load(open(STATS, encoding="utf-8"))
    act = S["action_verbs_in_rel"]

    verb_set = []
    for c in CATS:
        for k, v in act[c].items():
            if not k.startswith("_") and v > 0:
                verb_set.append(k)
    verbs = [v for v in verb_set if v not in ("_n", "_any", "_any_pct")]

    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    x = range(len(verbs))
    width = 0.26
    for i, c in enumerate(CATS):
        vals = [act[c].get(v, 0) for v in verbs]
        ax.bar([p + i * width for p in x], vals, width=width,
               color=COLORS[c], label=c)
    ax.set_xticks(list(x))
    ax.set_xticklabels(verbs, fontsize=7)
    ax.set_ylabel("关系条数", fontsize=8)
    ax.set_ylim(0, max(max(act[c].get(v, 0) for v in verbs) for c in CATS) * 1.25)
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(width=0.7)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#cccccc")
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.8)
    fig.tight_layout()

    pdf = os.path.join(HERE, "fig_info_2.pdf")
    png = os.path.join(HERE, "fig_info_2.png")
    fig.savefig(pdf, format="pdf", bbox_inches="tight")
    fig.savefig(png, format="png", dpi=150)
    plt.close(fig)

    ok = True
    blob = open(pdf, "rb").read()
    if not blob.startswith(b"%PDF") or len(blob) < 4000:
        print("SELFCHECK FAIL: pdf"); ok = False
    if os.path.getsize(png) < 8000:
        print("SELFCHECK FAIL: png"); ok = False
    print("SELFCHECK {} | {} {} B / {} B".format(
        "OK" if ok else "FAILED", pdf, os.path.getsize(pdf), os.path.getsize(png)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
