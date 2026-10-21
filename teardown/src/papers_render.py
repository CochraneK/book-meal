#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""论文渲染：把 `papers/_src/*.md` 里的占位符换成实测数字，配图，装配 APA-7 参考文献。

设计要点
--------
1. 正文**不写数字**，只写 `{{tc.ev}}` 这类占位符。数字一律来自 `_metrics.json`，
   这样「文档漂移」在结构上不可能发生——改数据就改论文，不用手改正文。
2. 参考文献只从 `papers/references.json`（Crossref 核验过的 25 条）里取；
   正文引用键与条目列表必须一一对应，缺一个就报错退出。
3. 每篇配一张图，数据同样取自 `_metrics.json`，避免手画图与表格打架。

用法：python src/papers_render.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
PAPERS = os.path.join(ROOT, "papers")
SRC = os.path.join(PAPERS, "_src")
BOOK = {"tc": "tiancai", "ft": "feitu"}

# 每篇一张图：(标题, [(标签, tc 指标路径, ft 指标路径)])
FIGURES = {
    "01-sociology": ("关系的规模（条 / 个）", [
        ("关系记录（条）", "rel", "rel"),
        ("去重对数", "pairs", "pairs"),
        ("有边节点", "nodes", "nodes"),
    ]),
    "02-psychology": ("动机相关事件占比（%）", [
        ("成长学习", "tbp.成长学习", "tbp.成长学习"),
        ("冲突对峙", "tbp.冲突对峙", "tbp.冲突对峙"),
        ("危机伤亡", "tbp.危机伤亡", "tbp.危机伤亡"),
        ("战斗", "tbp.战斗", "tbp.战斗"),
    ]),
    "03-economics": ("资源配置的空间痕迹（占各自总量 %）", [
        ("教育科研场所", "locp.教育科研", "locp.教育科研"),
        ("科研医疗事件", "tbp.科研医疗", "tbp.科研医疗"),
        ("制度秩序事件", "tbp.制度秩序", "tbp.制度秩序"),
    ]),
    "04-politics": ("秩序技术的配比（%）", [
        ("制度秩序", "tbp.制度秩序", "tbp.制度秩序"),
        ("冲突对峙", "tbp.冲突对峙", "tbp.冲突对峙"),
        ("战斗", "tbp.战斗", "tbp.战斗"),
        ("危机伤亡", "tbp.危机伤亡", "tbp.危机伤亡"),
    ]),
    "05-narrative": ("主要功能项占比（%）", [
        ("日常生存", "tbp.日常生存", "tbp.日常生存"),
        ("成长学习", "tbp.成长学习", "tbp.成长学习"),
        ("探索发现", "tbp.探索发现", "tbp.探索发现"),
        ("副本任务", "tbp.副本任务", "tbp.副本任务"),
        ("战斗", "tbp.战斗", "tbp.战斗"),
    ]),
    "06-education": ("教育想象的三个计数", [
        ("教育科研场所（处）", "loctb.教育科研", "loctb.教育科研"),
        ("成长学习事件（件）", "tb.成长学习", "tb.成长学习"),
        ("师徒关系（条）", "rb.师徒", "rb.师徒"),
    ]),
    "07-geography": ("空间复用率（%）", [
        ("前十大地点承载事件", "top10_loc_pct", "top10_loc_pct"),
        ("单点最高承载", "top1_loc_pct", "top1_loc_pct"),
        ("无地点事件占比", "ev_noloc_pct", "ev_noloc_pct"),
    ]),
    "08-networks": ("网络拓扑的规模", [
        ("有边节点", "nodes", "nodes"),
        ("去重边", "pairs", "pairs"),
        ("最大度", "top1_deg", "top1_deg"),
    ]),
    "09-linguistics": ("称谓词频（别名中子串命中）", [
        ("同学", "appel.同学", "appel.同学"),
        ("老师", "appel.老师", "appel.老师"),
        ("哥", "appel.哥", "appel.哥"),
        ("姐", "appel.姐", "appel.姐"),
        ("老板", "appel.老板", "appel.老板"),
        ("队长", "appel.队长", "appel.队长"),
    ]),
    "10-communication": ("信息通道（%）", [
        ("情报对话", "tbp.情报对话", "tbp.情报对话"),
        ("密谋博弈", "tbp.密谋博弈", "tbp.密谋博弈"),
        ("成长学习", "tbp.成长学习", "tbp.成长学习"),
    ]),
    "11-law": ("秩序与暴力（%）", [
        ("制度秩序", "tbp.制度秩序", "tbp.制度秩序"),
        ("冲突对峙", "tbp.冲突对峙", "tbp.冲突对峙"),
        ("战斗", "tbp.战斗", "tbp.战斗"),
        ("危机伤亡", "tbp.危机伤亡", "tbp.危机伤亡"),
    ]),
    "12-ethics": ("救助的分布", [
        ("救助记录（条）", "rb.救助", "rb.救助"),
        ("去重对数", "rescue", "rescue"),
        ("双向对数", "rescue_mutual", "rescue_mutual"),
    ]),
    "13-gender": ("可判定率（%）", [
        ("性别可判定", "gender_pct", "gender_pct"),
    ]),
    "14-medicine": ("身体叙事的事件与场所", [
        ("科研医疗事件（件）", "tb.科研医疗", "tb.科研医疗"),
        ("危机伤亡事件（件）", "tb.危机伤亡", "tb.危机伤亡"),
        ("医疗场所（处）", "loctb.医疗场所", "loctb.医疗场所"),
    ]),
    "15-method": ("归约残差与孤立点（占各自总数 %）", [
        ("「其他」类事件", "tbp.其他", "tbp.其他"),
        ("孤立点人物", "iso_pct", "iso_pct"),
        ("无地点事件", "ev_noloc_pct", "ev_noloc_pct"),
    ]),
}

FIG_LABEL = {"tc": "天才基本法", "ft": "我在废土世界扫垃圾"}


def load_metrics():
    return json.load(open(os.path.join(PAPERS, "_metrics.json"), encoding="utf-8"))


def load_refs():
    d = json.load(open(os.path.join(PAPERS, "references.json"), encoding="utf-8"))
    return {r["key"]: r for r in d["refs"] if r.get("status") == "verified"}


def resolve(metrics, path):
    book, rest = path.split(".", 1)
    node = metrics[BOOK[book]]
    for part in rest.split("."):
        if isinstance(node, dict):
            if part in node:
                node = node[part]
            elif part.isdigit():
                raise KeyError("不支持索引：%s" % path)
            else:
                node = 0          # 该基类在本书记录为零（如天才的战斗）
        else:
            raise KeyError("路径无法继续：%s" % path)
    return node


def fill(text, metrics):
    missing = []

    def rep(m):
        key = m.group(1).strip()
        try:
            v = resolve(metrics, key)
        except Exception:
            missing.append(key)
            return m.group(0)
        if isinstance(v, float) and v == int(v):
            v = int(v)
        return str(v)

    out = re.sub(r"\{\{([a-z]{2}\.[A-Za-z0-9_.\u4e00-\u9fff]+)\}\}", rep, text)
    if missing:
        raise SystemExit("占位符无法解析：" + ", ".join(sorted(set(missing))))
    left = re.findall(r"\{\{[^}]+\}\}", out)
    if left:
        raise SystemExit("残留占位符：" + ", ".join(left[:5]))
    return out


def parse(src):
    if not src.startswith("---\n"):
        raise SystemExit("缺 front matter")
    end = src.index("\n---\n", 3)
    head, body = src[4:end], src[end + 5:]
    meta = {}
    for line in head.splitlines():
        if not line.strip():
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    return meta, body


def make_figure(slug, metrics, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    for name in ("Microsoft YaHei", "SimHei"):
        if any(f.name == name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False

    title, rows = FIGURES[slug]
    labels = [r[0] for r in rows]
    tc = [resolve(metrics, "tc." + r[1]) for r in rows]
    ft = [resolve(metrics, "ft." + r[2]) for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, 0.62 * len(rows) + 1.5), dpi=160)
    y = range(len(rows))
    h = 0.36
    b1 = ax.barh([i + h / 2 for i in y], tc, height=h, color="#8c4a2f", label=FIG_LABEL["tc"])
    b2 = ax.barh([i - h / 2 for i in y], ft, height=h, color="#2f5d8a", label=FIG_LABEL["ft"])
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=12, pad=10)
    ax.legend(fontsize=9, frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.45)
    ax.set_axisbelow(True)
    for bars in (b1, b2):
        for b in bars:
            w = b.get_width()
            ax.text(w, b.get_y() + b.get_height() / 2, " %g" % w, va="center", fontsize=8.5, color="#444")
    fig.tight_layout()
    path = os.path.join(outdir, "fig1.png")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return "figures/fig1.png"


def main():
    metrics = load_metrics()
    refs = load_refs()
    srcs = sorted(f for f in os.listdir(SRC) if f.endswith(".md"))
    if not srcs:
        raise SystemExit("papers/_src 为空")

    index = []
    for fn in srcs:
        meta, body = parse(open(os.path.join(SRC, fn), encoding="utf-8").read())
        slug = meta["slug"]
        outdir = os.path.join(PAPERS, slug)
        os.makedirs(os.path.join(outdir, "figures"), exist_ok=True)

        body = fill(body, metrics)
        keys = [k.strip() for k in meta["refs"].split(",") if k.strip()]
        unknown = [k for k in keys if k not in refs]
        if unknown:
            raise SystemExit("%s: 引用键不在核验清单里：%s" % (slug, unknown))
        entries = sorted((refs[k]["apa"] for k in keys), key=lambda s: s.lower())

        fig = make_figure(slug, metrics, os.path.join(outdir, "figures"))

        # 正文插图：插在 §3 第一次出现处之后不好判定，统一放在 §2 末尾前的「数据与方法」后
        body = body.replace("## 3. 分析与发现",
                            "![图 1 %s](%s)\n\n*数据来源：本项目知识图谱现算；口径见 §2。*\n\n## 3. 分析与发现"
                            % (FIGURES[slug][0], fig), 1)

        md = []
        md.append("# %s\n" % meta["zh"])
        md.append("**%s**\n" % meta["en"])
        md.append("*拆书项目组（Computational Reading of Two Novels）*\n")
        md.append("**摘要：**%s\n" % fill(meta["abstract_zh"], metrics))
        md.append("**Abstract:** %s\n" % fill(meta["abstract_en"], metrics))
        md.append("**关键词：**%s\n" % meta["kzh"])
        md.append("**Keywords:** %s\n" % meta["ken"])
        md.append("---\n")
        md.append(body.strip() + "\n")
        md.append("## 参考文献\n")
        for e in entries:
            md.append("- " + e)
        md.append("")
        md.append("> 文献核验：以上 %d 条均由 `src/verify_refs.py` 逐条检索 Crossref，"
                  "命中类型、年份、作者与标题相似度四道闸后才写入；DOI 可直接打开原记录。"
                  "少数专著在 Crossref 的注册题名省略了副标题，以注册记录为准。\n" % len(entries))

        open(os.path.join(outdir, slug + ".md"), "w", encoding="utf-8").write("\n".join(md))
        index.append({
            "slug": slug, "zh": meta["zh"], "en": meta["en"],
            "kzh": meta["kzh"], "n_refs": len(entries),
            "chars": len(body),
        })
        print("[ok] papers/%s/%s.md  (%d 字, %d 条文献)" % (slug, slug, len(body), len(entries)))

    # 索引
    rows = ["# 论文体系：两本长篇小说的十五个学科切片\n",
            "**Papers: Fifteen Disciplinary Readings of Two Chinese Web Novels**\n",
            "语料：《天才基本法》（长洱，%d 章 / %d 事件）与《我在废土世界扫垃圾》"
            "（有花在野，%d 章 / %d 事件）。每篇为中英双语题录 + 中文正文 + 数据图 + "
            "经 Crossref 核验的 APA-7 参考文献。\n" % (
                metrics["tiancai"]["ch"], metrics["tiancai"]["ev"],
                metrics["feitu"]["ch"], metrics["feitu"]["ev"]),
            "| # | 学科 | 中文标题 | English Title | 文献 |",
            "|---|---|---|---|---|"]
    for i, it in enumerate(index, 1):
        rows.append("| %d | %s | [%s](%s/%s.md) | %s | %d |" % (
            i, it["kzh"].split("；")[0], it["zh"], it["slug"], it["slug"], it["en"], it["n_refs"]))
    rows.append("")
    rows.append("> 生成方式：`python src/papers_prep.py && python src/papers_render.py`。"
                "正文中的数字全部来自 `papers/_metrics.json` 的占位符替换，"
                "校验见 `python src/verify_papers.py`。")
    open(os.path.join(PAPERS, "README.md"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print("\n索引：papers/README.md（%d 篇）" % len(index))


if __name__ == "__main__":
    main()
