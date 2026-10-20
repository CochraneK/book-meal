# -*- coding: utf-8 -*-
"""Fig.1 —— 书内信息载体词的逐字命中（公开渠道 / 隐秘渠道 / 弃用（0 命中））。

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


def main():
    S = json.load(open(STATS, encoding="utf-8"))
    vocab = S["vocab_hits"]

    groups = ["公开渠道", "隐秘渠道"]
    words, vals, cols = [], [], []
    colormap = {"公开渠道": "#2b4258", "隐秘渠道": "#7f4f2a", "弃用（0 命中）": "#b8c4d0"}
    for g in groups:
        for d in sorted(vocab[g], key=lambda x: -x["n"]):
            words.append(d["word"])
            vals.append(d["n"])
            cols.append(colormap[g])
    for d in vocab["弃用（0 命中）"]:
        words.append(d["word"])
        vals.append(d["n"])
        cols.append(colormap["弃用（0 命中）"])

    fig, ax = plt.subplots(figsize=(3.5, 4.6))
    y = range(len(words))
    bars = ax.barh(list(y), vals, color=cols, height=0.62)
    ax.set_yticks(list(y))
    ax.set_yticklabels(words, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("逐字命中次数（原书）", fontsize=8)
    mx = max(vals) if vals else 1
    ax.set_xlim(0, mx * 1.25)
    for b, v in zip(bars, vals):
        ax.text(v + mx * 0.02, b.get_y() + b.get_height() / 2, str(v),
                va="center", fontsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(width=0.7)
    ax.set_axisbelow(True)
    ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#cccccc")
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.8)
    fig.tight_layout()

    pdf = os.path.join(HERE, "fig_info_1.pdf")
    png = os.path.join(HERE, "fig_info_1.png")
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
