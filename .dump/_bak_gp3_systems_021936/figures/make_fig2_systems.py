# -*- coding: utf-8 -*-
"""Fig.2 — 主题子网络与全图基线的关系类别构成（systems 篇专属）

分组条形：主题子网络 vs 全图基线 的关系类别构成（占比 %）。
一图一脚本 / 矢量 PDF / 图内不写标题 / 渲染后自检。
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STATS = r"D:\2026\WB项目\明朝\.dump\_stats_systems.json"

plt.rcParams.update({
    "font.family": ["Noto Serif SC", "SimSun"],
    "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "figure.dpi": 150, "pdf.fonttype": 42, "ps.fonttype": 42,
})


def main():
    S = json.load(open(STATS, encoding="utf-8"))
    d = S["fig"]["fig2"]            # {"cat", "subset_pct", "baseline_pct"}

    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    x = range(len(d))
    a = [r["subset_pct"] for r in d]
    b = [r["baseline_pct"] for r in d]
    ax.bar([i - 0.19 for i in x], a, width=0.38, label="主题子网络",
           color="#404040", edgecolor="#ffffff", linewidth=0.5)
    ax.bar([i + 0.19 for i in x], b, width=0.38, label="全图基线",
           color="#bdbdbd", edgecolor="#ffffff", linewidth=0.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels([r["cat"] for r in d], fontsize=6.5, rotation=30,
                       ha="right", rotation_mode="anchor")
    ax.set_ylabel("占比 \\%")
    ax.set_ylim(0, max(max(a) or 1, max(b) or 1) * 1.22)
    ax.legend(loc="upper right", fontsize=7, frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(width=0.7)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#cccccc")
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.8)
    fig.tight_layout()

    pdf = os.path.join(HERE, "fig_systems_2.pdf")
    png = os.path.join(HERE, "fig_systems_2.png")
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
