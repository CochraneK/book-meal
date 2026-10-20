# -*- coding: utf-8 -*-
"""Fig.1 — 主题语汇在原书中的逐字命中次数（info 篇专属）

一图一脚本 / 矢量 PDF / 图内不放标题（图题只进 LaTeX 的 caption 命令）/ 渲染后自检。
数据来自 .dump/_stats_info.json，不许硬编码数字。
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
    d = S["fig"]["fig1"]            # 主题语汇命中次数，降序

    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    vals = [x["value"] for x in d]
    bars = ax.barh(range(len(d)), vals, color="#404040",
                   edgecolor="#ffffff", linewidth=0.6)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels([x["label"] for x in d], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("逐字命中次数")
    ax.set_xlim(0, max(vals) * 1.18 if vals else 1)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals) * 0.02 if vals else 0.1,
                b.get_y() + b.get_height() / 2, str(v),
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
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
