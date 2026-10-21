#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""论文体系校验（第五道闸）。

守六件事：
  ① 指标复算：11 篇里出现的核心指标由本文件**独立实现**再算一遍，必须与
     `papers/_metrics.json` 逐项相等（不复用 papers_prep 的代码，否则同一个 bug 会被
     两边同时"确认"）；
  ② 与学科视角对齐：与 `verify_perspectives.CANON` 共享的指标必须一致——两套文档
     说同一件事，不能各说各的；
  ③ 结构完整：摘要 / Abstract / 关键词 / Keywords / 五个编号小节 / 参考文献齐全；
  ④ 引用闭合：正文里的（Author, Year）必须在参考文献里找得到条目，反之亦然；
  ⑤ 数字纪律：正文里的百分比与三位以上整数，必须能在指标集合里找到来源，
     否则就是手写数字（漂移的起点）；
  ⑥ 文献可点：每条参考文献都必须带 DOI。

用法：python src/verify_papers.py（exit 0 = 全过）
"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
PAPERS = os.path.join(ROOT, "papers")
SRC = os.path.join(PAPERS, "_src")
sys.path.insert(0, BASE)

from core.books import load_data  # noqa: E402
import verify_perspectives as VP  # noqa: E402

BOOKS = {"tc": "tiancai", "ft": "feitu"}
SECTIONS = ["## 1.", "## 2.", "## 3.", "## 4.", "## 5."]
# 正文允许出现但不来自指标的数字（章节号、年份、类型总数等结构常量）
ALLOW_NUMBERS = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                 "16", "17", "108", "112", "218", "221", "439", "833", "2591", "2030", "1900"}
# 交叉校验：metrics 键 → CANON 键
CROSS = {
    "ev": "ev_total", "rel": "rel_total", "chars": "char_total",
    "pairs": "pairs", "nodes": "nodes", "iso": "iso", "iso_pct": "iso_pct",
    "comps": "comps", "max_comp": "max_comp", "max_comp_pct": "max_comp_pct",
    "deg1_pct": "deg1_pct", "alias_total": "alias_total", "alias_pct": "alias_pct",
    "q_picked": "q_picked", "q_attr": "q_attr", "q_pct": "q_pct",
    "info_n": "info", "info_pct": "info_pct", "rescue": "rescue_pairs",
    "gender_n": "gender_n", "gender_pct": "gender_pct",
}


def pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


def recompute(book):
    """独立实现：与 papers_prep.metrics 不共享任何代码。"""
    d = load_data(book)
    chars, locs, evs, rels, chs = d["characters"], d["locations"], d["events"], d["relations"], d["chapters"]
    tb = Counter(e.get("type_base", "") for e in evs)
    lt = Counter(l.get("type_base", "") for l in locs)
    names = {l["name"] for l in locs}
    lc = Counter(e["location"] for e in evs if e.get("location") in names)

    pairs = set()
    for r in rels:
        if r["from"] != r["to"]:
            pairs.add(frozenset((r["from"], r["to"])))
    deg = Counter()
    for p in pairs:
        for who in p:
            deg[who] += 1
    # 连通分量：并查集（另一种实现，故意不用 BFS）
    parent = {n: n for n in deg}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in pairs:
        a, b = tuple(p)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comp = Counter(find(n) for n in deg)
    iso = sum(1 for c in chars if c["name"] not in deg)
    top = deg.most_common(1)[0] if deg else ("", 0)
    q = {}
    qp = os.path.join(ROOT, "data", book, "quotes.json")
    if os.path.exists(qp):
        q = json.load(open(qp, encoding="utf-8")).get("meta", {})
    res = {(r["from"], r["to"]) for r in rels if r.get("rel_base") == "救助"}
    mut = {x for x in res if (x[1], x[0]) in res}
    APPEL = ["同学", "老师", "叔", "哥", "姐", "老板", "队长", "阿姨", "主任", "医生"]

    return {
        "ch": len(chs), "ev": len(evs), "rel": len(rels), "chars": len(chars), "locs": len(locs),
        "pairs": len(pairs), "nodes": len(deg),
        "iso": iso, "iso_pct": pct(iso, len(chars)),
        "comps": len(comp), "max_comp": max(comp.values()) if comp else 0,
        "max_comp_pct": pct(max(comp.values()) if comp else 0, len(chars)),
        "deg1_pct": pct(sum(1 for v in deg.values() if v == 1), len(deg)),
        "top1_name": top[0], "top1_deg": top[1],
        "ev_loc": sum(lc.values()), "ev_noloc": len(evs) - sum(lc.values()),
        "ev_noloc_pct": pct(len(evs) - sum(lc.values()), len(evs)),
        "top1_loc": (lc.most_common(1)[0][0] if lc else ""),
        "top1_loc_n": (lc.most_common(1)[0][1] if lc else 0),
        "top1_loc_pct": pct(lc.most_common(1)[0][1] if lc else 0, len(evs)),
        "top10_loc_pct": pct(sum(v for _, v in lc.most_common(10)), len(evs)),
        "q_picked": q.get("picked", 0), "q_attr": q.get("attributed", 0),
        "q_pct": pct(q.get("attributed", 0), q.get("picked", 0)),
        "alias_total": sum(len(c.get("aliases") or []) for c in chars),
        "alias_pct": pct(sum(1 for c in chars if c.get("aliases")), len(chars)),
        "rescue": len(res), "rescue_mutual": len(mut) // 2,
        "info_n": tb.get("情报对话", 0) + tb.get("密谋博弈", 0),
        "info_pct": pct(tb.get("情报对话", 0) + tb.get("密谋博弈", 0), len(evs)),
        "gender_n": VP.recompute(book)["gender_n"],
        "gender_pct": VP.recompute(book)["gender_pct"],
        "tb": dict(tb), "rb": dict(Counter(r.get("rel_base", "") for r in rels)),
        "loctb": dict(lt),
        "tbp": {k: pct(v, len(evs)) for k, v in tb.items()},
        "locp": {k: pct(v, len(locs)) for k, v in lt.items()},
        "appel": {w: sum(1 for c in chars for a in (c.get("aliases") or []) if w in a) for w in APPEL},
        "kw": {
            "alzheimer": sum(1 for e in evs if "阿尔茨海默" in (e.get("name") or "")),
            "illness": sum(1 for e in evs if "病" in (e.get("name") or "")),
            "pollution": sum(1 for e in evs if "污染" in (e.get("name") or "")),
            "corpse": sum(1 for e in evs if "尸体" in (e.get("name") or "")),
        },
    }


def flat_numbers(obj, acc):
    if isinstance(obj, dict):
        for v in obj.values():
            flat_numbers(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            flat_numbers(v, acc)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        acc.add(str(obj))
        if isinstance(obj, float):
            acc.add(("%.1f" % obj))
            if obj == int(obj):
                acc.add(str(int(obj)))
    elif isinstance(obj, str):
        acc.add(obj)
    return acc


def check_metrics(metrics, errs):
    for tag, book in BOOKS.items():
        fresh = recompute(book)
        for k, v in fresh.items():
            got = metrics[book].get(k)
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if got.get(kk) != vv:
                        errs.append("[①] %s.%s.%s 漂移：metrics=%s 复算=%s" % (tag, k, kk, got.get(kk), vv))
            else:
                if got != v:
                    errs.append("[①] %s.%s 漂移：metrics=%s 复算=%s" % (tag, k, got, v))
        # ② 与学科视角文档对齐
        canon = VP.CANON.get(book, {})
        for mk, ck in CROSS.items():
            if ck in canon and metrics[book].get(mk) != canon[ck]:
                errs.append("[②] %s.%s=%s 与 perspectives canonical %s=%s 不一致"
                            % (tag, mk, metrics[book].get(mk), ck, canon[ck]))


def key_name(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def check_paper(slug, path, metrics, refs, errs):
    text = open(path, encoding="utf-8").read()
    for block in ("**摘要：**", "**Abstract:**", "**关键词：**", "**Keywords:**", "## 参考文献"):
        if block not in text:
            errs.append("[③] %s 缺 %s" % (slug, block))
    for sec in SECTIONS:
        if sec not in text:
            errs.append("[③] %s 缺小节 %s" % (slug, sec))
    if "{{" in text:
        errs.append("[③] %s 有未替换占位符" % slug)

    body, _, reflist = text.partition("## 参考文献")
    # ⑥ DOI
    entries = [l.strip("- ").strip() for l in reflist.splitlines() if l.startswith("- ")]
    if not entries:
        errs.append("[⑥] %s 参考文献为空" % slug)
    for e in entries:
        if "https://doi.org/" not in e:
            errs.append("[⑥] %s 条目缺 DOI：%s" % (slug, e[:60]))
    # ④ 引用闭合
    cited = set()
    for m in re.finditer(r"（([A-Z][A-Za-zÀ-ÿ'’\-]+)(?: & [A-Z][A-Za-zÀ-ÿ'’\-]+)?, (\d{4})）", body):
        cited.add((key_name(m.group(1)), m.group(2)))
    if not cited:
        errs.append("[④] %s 正文没有任何 (Author, Year) 引用" % slug)
    have = set()
    for e in entries:
        en = key_name(e)
        m = re.match(r"([a-z'’\-]+),", en)
        y = re.search(r"\((\d{4})\)", en)
        if m and y:
            have.add((key_name(m.group(1)), y.group(1)))
    for c in sorted(cited - have):
        errs.append("[④] %s 引用 %s, %s 在参考文献里找不到" % ((slug,) + c))
    for h in sorted(have - cited):
        errs.append("[④] %s 参考文献 %s, %s 未被正文引用" % ((slug,) + h))
    # ⑤ 数字纪律
    allowed = set()
    for tag in BOOKS:
        flat_numbers(metrics[BOOKS[tag]], allowed)
    allowed |= ALLOW_NUMBERS
    allowed |= {str(i) for i in range(0, 16)}
    for m in re.finditer(r"(\d+(?:\.\d+)?)%", body):
        if m.group(1) not in allowed:
            errs.append("[⑤] %s 正文出现无法复算的百分比：%s%%" % (slug, m.group(1)))
    for m in re.finditer(r"(?<![\d.])(\d{3,})(?![\d.])", body):
        if m.group(1) not in allowed and not (1900 <= int(m.group(1)) <= 2030):
            errs.append("[⑤] %s 正文出现无法复算的数字：%s" % (slug, m.group(1)))


def main():
    metrics = json.load(open(os.path.join(PAPERS, "_metrics.json"), encoding="utf-8"))
    refs = {r["key"]: r for r in json.load(open(os.path.join(PAPERS, "references.json"),
                                                encoding="utf-8"))["refs"]}
    errs = []
    check_metrics(metrics, errs)

    srcs = sorted(f for f in os.listdir(SRC) if f.endswith(".md"))
    if len(srcs) != 15:
        errs.append("[③] 论文数 %d，预期 15" % len(srcs))
    for fn in srcs:
        slug = fn[:-3]
        path = os.path.join(PAPERS, slug, slug + ".md")
        if not os.path.exists(path):
            errs.append("[③] 缺产物 papers/%s/%s.md" % (slug, slug))
            continue
        check_paper(slug, path, metrics, refs, errs)
        fig = os.path.join(PAPERS, slug, "figures", "fig1.png")
        if not os.path.exists(fig):
            errs.append("[③] %s 缺图 figures/fig1.png" % slug)

    ok = sum(1 for r in refs.values() if r.get("status") == "verified")
    print("=" * 60)
    print("论文校验：%d 篇 / 文献池 %d 条（verified %d）" % (len(srcs), len(refs), ok))
    if errs:
        print("发现问题 %d 处：" % len(errs))
        for e in errs[:40]:
            print("  - " + e)
        return 1
    print("[OK] ① 指标复算一致 ② 与学科视角 canonical 对齐 ③ 结构完整")
    print("    ④ 引用闭合 ⑤ 数字可溯源 ⑥ 文献全部带 DOI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
