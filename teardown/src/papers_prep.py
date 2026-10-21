#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""论文素材：从 data.json 现算论文要用的指标，供 14 篇论文的占位符替换。

为什么单独算一遍：论文里的数字必须能被 `verify_papers.py` 独立复算对上，
和 `perspectives_prep.py` 各写一份是**故意的**——两处口径若漂移，交叉比对会立刻暴露。
共享的指标（如去重关系对）还会与 `verify_perspectives.CANON` 逐项对齐。

输出 `papers/_metrics.json`。
"""
import json
import os
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
sys.path.insert(0, BASE)

from core.books import load_data  # noqa: E402

# 关键词计数：只数事件名，不读正文（口径写在论文 §2.3）
KEYWORDS = {
    "alzheimer": "阿尔茨海默",
    "illness": "病",
    "pollution": "污染",
    "corpse": "尸体",
    "exam": "考试",
}


def pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


def metrics(book):
    d = load_data(book)
    chars, locs, evs, rels, chs = d["characters"], d["locations"], d["events"], d["relations"], d["chapters"]
    n_chr, n_ev = len(chars), len(evs)
    tb = Counter(e.get("type_base", "") for e in evs)
    rb = Counter(r.get("rel_base", "") for r in rels)

    # 地点承载：只做精确匹配（别称不计，口径与 §7 地理学一致）
    loc_names = {l["name"] for l in locs}
    loc_cnt = Counter(e["location"] for e in evs if e.get("location") in loc_names)
    ev_loc = sum(loc_cnt.values())
    top10 = loc_cnt.most_common(10)
    top1_name, top1_n = (top10[0] if top10 else ("", 0))
    top10_n = sum(v for _, v in top10)

    # 关系拓扑：一律去重（无向对），原始条数并列
    pairs = set()
    for r in rels:
        a, b = r["from"], r["to"]
        if a != b:
            pairs.add(tuple(sorted((a, b))))
    deg = Counter()
    adj = {}
    for a, b in pairs:
        deg[a] += 1
        deg[b] += 1
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen, comps = set(), []
    for n in deg:
        if n in seen:
            continue
        stack, comp = [n], []
        seen.add(n)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    iso = sum(1 for c in chars if c["name"] not in deg)
    top1 = deg.most_common(1)[0] if deg else ("", 0)

    q = load_quotes(book)
    qm = q.get("meta", {})

    rescue = {(r["from"], r["to"]) for r in rels if r.get("rel_base") == "救助"}
    rescue_mutual = {p for p in rescue if (p[1], p[0]) in rescue}

    kw = {}
    for k, w in KEYWORDS.items():
        kw[k] = sum(1 for e in evs if w in (e.get("name") or ""))

    # 称谓词：在别名字符串里做子串计数（词表口径，非分词），只用于「哪种称谓更常见」
    APPEL = ["同学", "老师", "叔", "哥", "姐", "老板", "队长", "阿姨", "主任", "医生"]
    appel = {}
    for w in APPEL:
        appel[w] = sum(1 for c in chars for a in (c.get("aliases") or []) if w in a)
    info_n = tb.get("情报对话", 0) + tb.get("密谋博弈", 0)

    # 性别可判定率：只认角色描述里的显式线索，男女冲突时不判（与学科视角同口径）
    FW = ["女主角", "女主", "女队长", "女医生", "女异能者", "女学生", "女老板",
          "少女", "女孩", "母亲", "妻子", "姐姐", "妹妹", "女儿", "她"]
    MW = ["男主角", "男主", "男医生", "男学生", "少年", "男孩",
          "父亲", "丈夫", "哥哥", "弟弟", "儿子", "他"]
    g_n = 0
    for c in chars:
        r = c.get("role") or ""
        head = r.split("，")[0].split(",")[0]
        isf = any(w in head for w in FW) or any(w in r for w in ["之母", "之妻", "之女", "之姐", "之妹"])
        ism = any(w in head for w in MW) or any(w in r for w in ["之父", "之夫", "之子", "之兄", "之弟"])
        if (isf and not ism) or (ism and not isf):
            g_n += 1

    loctb = Counter(l.get("type_base", "") for l in locs)
    n_pairs = len(pairs)
    return {
        "title": d["meta"]["title"],
        "author": d["meta"]["author"],
        "ch": len(chs),
        "no_max": max(c["no"] for c in chs),
        "ev": n_ev,
        "rel": len(rels),
        "chars": len(chars),
        "locs": len(locs),
        "pairs": n_pairs,
        "nodes": len(deg),
        "avg_deg": round(2.0 * n_pairs / len(deg), 2) if deg else 0.0,
        "repeat_ratio": round(len(rels) / n_pairs, 2) if n_pairs else 0.0,
        "iso": iso,
        "iso_pct": pct(iso, n_chr),
        "comps": len(comps),
        "max_comp": len(comps[0]) if comps else 0,
        "max_comp_pct": pct(len(comps[0]) if comps else 0, n_chr),
        "deg1_pct": pct(sum(1 for v in deg.values() if v == 1), len(deg)),
        "top1_name": top1[0],
        "top1_deg": top1[1],
        "ev_loc": ev_loc,
        "ev_noloc": n_ev - ev_loc,
        "ev_noloc_pct": pct(n_ev - ev_loc, n_ev),
        "top1_loc": top1_name,
        "top1_loc_n": top1_n,
        "top1_loc_pct": pct(top1_n, n_ev),
        "top10_loc_n": top10_n,
        "top10_loc_pct": pct(top10_n, n_ev),
        "q_picked": qm.get("picked", 0),
        "q_attr": qm.get("attributed", 0),
        "q_pct": pct(qm.get("attributed", 0), qm.get("picked", 0)),
        "alias_total": sum(len(c.get("aliases") or []) for c in chars),
        "alias_pct": pct(sum(1 for c in chars if c.get("aliases")), n_chr),
        "rescue": len(rescue),
        "rescue_mutual": len(rescue_mutual) // 2,
        "ev_per_ch": round(n_ev / len(chs), 2),
        "rel_per_char": round(len(rels) / n_chr, 2),
        "gender_n": g_n,
        "gender_pct": pct(g_n, n_chr),
        "info_n": info_n,
        "info_pct": pct(info_n, n_ev),
        "appel": appel,
        "tb": {k: v for k, v in tb.items() if k},
        "tbp": {k: pct(v, n_ev) for k, v in tb.items() if k},
        "loctb": {k: v for k, v in loctb.items() if k},
        "locp": {k: pct(v, len(locs)) for k, v in loctb.items() if k},
        "rb": {k: v for k, v in rb.items() if k},
        "kw": kw,
    }


def load_quotes(book):
    p = os.path.join(ROOT, "data", book, "quotes.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


def main():
    out = {b: metrics(b) for b in ("tiancai", "feitu")}
    json.dump(out, open(os.path.join(ROOT, "papers", "_metrics.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for b, m in out.items():
        print("[%s] %s / %s" % (b, m["title"], m["author"]))
        print("    章 %d 事件 %d 关系 %d 人物 %d 地点 %d" % (m["ch"], m["ev"], m["rel"], m["chars"], m["locs"]))
        print("    去重对 %d 节点 %d 孤立 %.1f%% 分量 %d 最大 %d top1 %s=%d 度1 %.1f%%" % (
            m["pairs"], m["nodes"], m["iso_pct"], m["comps"], m["max_comp"], m["top1_name"], m["top1_deg"], m["deg1_pct"]))
        print("    地点承载 top1 %s %d(%.1f%%) top10 %.1f%% 无地点 %d" % (
            m["top1_loc"], m["top1_loc_n"], m["top1_loc_pct"], m["top10_loc_pct"], m["ev_noloc"]))
        print("    对白 %d/%d(%.1f%%) 别名 %d(%.1f%%) 救助对 %d 双向 %d 关键词 %s" % (
            m["q_attr"], m["q_picked"], m["q_pct"], m["alias_total"], m["alias_pct"],
            m["rescue"], m["rescue_mutual"], m["kw"]))
        print("    事件基类 %s" % m["tb"])
        print("    关系基类 %s" % m["rb"])


if __name__ == "__main__":
    main()
