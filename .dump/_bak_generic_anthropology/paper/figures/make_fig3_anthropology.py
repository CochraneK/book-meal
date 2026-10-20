# -*- coding: utf-8 -*-
"""Fig.3 — 主题事件的时间分布（anthropology 篇专属）

一图一脚本 / 矢量 PDF / 图内不写标题 / 渲染后自检。
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STATS = r"D:\2026\WB项目\明朝\.dump\_stats_anthropology.json"

plt.rcParams.update({
    "font.family": ["Noto Serif SC", "SimSun"],
    "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "figure.dpi": 150, "pdf.fonttype": 42, "ps.fonttype": 42,
})


def main():
    S = json.load(open(STATS, encoding="utf-8"))
    d = S["fig"]["fig3"]            # 主题事件的年份分布
    xlabel, ylabel = "年份", "事件数"
    if not d:
        # 回退口径：该篇没有带年份的主题事件时，改用锚点人物的出场章节数。
        # 这条回退是 2026-10-01 补的：原先无数据时直接返 False，
        # 留下 9 篇的空图；锚点表每篇都有，故回退恒定有数据。
        d = [{"label": a["name"], "value": a.get("chapters", 0)}
             for a in S.get("anchors", [])]
        xlabel, ylabel = "锚点人物", "出场章节数"
        if not d:
            print("SELFCHECK FAILED: 图 3 回退后仍无数据"); return False

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.bar(range(len(d)), [x["value"] for x in d], width=0.7,
           color="#707070", edgecolor="#ffffff", linewidth=0.5)
    ax.set_xticks(range(len(d)))
    ax.set_xticklabels([x["label"] for x in d], fontsize=6.2, rotation=90)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(x["value"] for x in d) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(width=0.7)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#cccccc")
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.8)
    fig.tight_layout()

    pdf = os.path.join(HERE, "fig_anthropology_3.pdf")
    png = os.path.join(HERE, "fig_anthropology_3.png")
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
