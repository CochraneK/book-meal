# -*- coding: utf-8 -*-
"""
独立复核：多学科视角文档声称的关键数字（src/verify_perspectives.py）
====================================================================
不依赖 perspectives_prep.py，独立从 data/<book>/data.json 现算关键指标，
1) 与 KG_SPEC ④′ 同把尺子的 canonical 值比对（捕捉数据漂移 / 口径漂移）；
2) 确认该数字确实出现在 docs/perspectives_<book>.md（捕捉文档漂移）；
3) 阶段级核对（v2 新增，防「文档数字 vs 素材包」漂移——曾因手写文档时
   抄了旧版素材包，写出「密度 32–84 件/章」这种与现算差一个数量级的句子，
   canonical 全对而它全错，故补这道闸）：
   a. 覆盖：报告 payload 的每个阶段都必须以「阶段名（起–止）」出现在文档；
   b. 防虚构：文档里任何「阶段名（d–d）」的区间必须真实存在；
   c. 逐行 spot check：指定阶段的行必须包含指定的单元格值；
   d. 锚点数字必须在文档中；已证伪的旧值（黑名单）不得再出现。

退出码：全部一致 = 0；任一不一致 = 1。
用法：python src/verify_perspectives.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def recompute(book):
    data = load(os.path.join(BASE, "data", book, "data.json"))
    chars = data["characters"]
    locs = data["locations"]
    evs = data["events"]
    rels = data["relations"]
    n_rel = len(rels)
    n_ch = len(chars)
    n_ev = len(evs)
    n_loc = len(locs)
    rb = {}
    for r in rels:
        b = r.get("rel_base", "")
        rb[b] = rb.get(b, 0) + 1
    tb = {}
    for e in evs:
        b = e.get("type_base", "")
        tb[b] = tb.get(b, 0) + 1
    lb = {}
    for l in locs:
        b = l.get("type_base", "")
        lb[b] = lb.get(b, 0) + 1

    def pct(x, n):
        return round(100.0 * x / n, 1) if n else 0.0

    dom = rb.get("支配", 0) + rb.get("上下级", 0)
    prod = lb.get("生产处理", 0) + lb.get("商业服务", 0)
    cameo = sum(1 for c in chars if c.get("tier") == "cameo")
    me = tb.get("记忆情感", 0)
    cp = tb.get("副本任务", 0)
    inst = tb.get("制度秩序", 0)
    grow = tb.get("成长学习", 0)
    cmb = tb.get("战斗", 0) + tb.get("冲突对峙", 0)

    # ---- v3.10 新增八学科的可复算量（与 perspectives_prep 同算法，独立实现） ----
    # 关系边跨章重复计数严重，拓扑量一律先去重（否则 482 条边会被当成 482 次社交）
    pairs = set()
    for r in rels:
        a, b = r["from"], r["to"]
        if a != b:
            pairs.add(tuple(sorted((a, b))))
    deg = {}
    adj = {}
    for a, b in pairs:
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
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
    alias_total = sum(len(c.get("aliases") or []) for c in chars)
    alias_pct = pct(sum(1 for c in chars if c.get("aliases")), n_ch)
    q = load(os.path.join(BASE, "data", book, "quotes.json"), {})
    qm = q.get("meta", {})
    # quotes.json 是抽取出来的原文引语，受版权保护、不入版本控制。
    # 缺它时对白三项无从复算——必须记为 None 而不是 0：
    # 记 0 会与 canonical 的 171/156/91.2 对不上，在 CI 上表现为假漂移。
    HAS_QUOTES = bool(qm)
    info = tb.get("情报对话", 0) + tb.get("密谋博弈", 0)
    fight = tb.get("战斗", 0)
    conf = tb.get("冲突对峙", 0)
    # 性别代理判定（与 prep 同一词表；冲突不判）
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

    return {
        "rel_total": n_rel,
        "loc_total": n_loc,
        "char_total": n_ch,
        "ev_total": n_ev,
        "dom": dom, "dom_pct": pct(dom, n_rel),
        "cameo": cameo, "cameo_pct": pct(cameo, n_ch),
        "me": me, "me_pct": pct(me, n_ev),
        "cp": cp, "cp_pct": pct(cp, n_ev),
        "prod": prod, "prod_pct": pct(prod, n_loc),
        "inst": inst, "inst_pct": pct(inst, n_ev),
        "grow": grow, "grow_pct": pct(grow, n_ev),
        "dens": round(n_ev / n_loc_chapters(book, data), 2) if n_loc_chapters(book, data) else 0,
        "cmb": cmb, "cmb_pct": pct(cmb, n_ev),
        "pairs": len(pairs), "nodes": len(deg), "avg_deg": round(2.0 * len(pairs) / len(deg), 2) if deg else 0,
        "iso": iso, "iso_pct": pct(iso, n_ch),
        "comps": len(comps), "max_comp": len(comps[0]) if comps else 0,
        "max_comp_pct": pct(len(comps[0]) if comps else 0, n_ch),
        "top1": max(deg.values()) if deg else 0,
        "deg1_pct": pct(sum(1 for v in deg.values() if v == 1), len(deg)),
        "alias_total": alias_total, "alias_pct": alias_pct,
        "q_picked": qm.get("picked", 0), "q_attr": qm.get("attributed", 0),
        "q_pct": pct(qm.get("attributed", 0), qm.get("picked", 0)),
        # 供调用方判断这三个指标能否参与比对（缺 quotes.json 时为 False）
        "has_quotes": HAS_QUOTES,
        "info": info, "info_pct": pct(info, n_ev),
        "law_ratio": round(inst / (conf + fight), 2) if (conf + fight) else 0.0,
        "rescue_pairs": len({(r["from"], r["to"]) for r in rels if r.get("rel_base") == "救助"}),
        "gender_n": g_n, "gender_pct": pct(g_n, n_ch),
    }


def n_loc_chapters(book, data):
    # 事件密度分母 = 章数（沿用 perspectives_prep 的 len(data["chapters"])）
    return len(data.get("chapters", []))


# ---------- 阶段级核对（v2） ----------
def derive_payload_phases(book):
    """阶段派生（与报告 payload 同源同口径 —— 唯一真源 src/core.phases）。

    阶段是构建期现算的（不在 data.json 里），所以这里必须重跑同一套 derive，
    否则「文档说的阶段」和「报告里真实存在的阶段」会是两套。
    本函数此前从 generate_report 拷贝了一份 derive，现统一走 core。
    """
    sys.path.insert(0, os.path.join(BASE, "src"))
    from core.chapters import build_idx2no  # noqa: E402
    from core.phases import derive_phases, phases_to_no  # noqa: E402
    data = load(os.path.join(BASE, "data", book, "data.json"))
    raw = load(os.path.join(BASE, "data", book, "extract_raw.json"), [])
    return phases_to_no(derive_phases(book, data["chapters"], raw),
                        build_idx2no(data["chapters"]))


# 指定阶段的行必须包含这些单元格值（§5.1 张力曲线表 / §2.2 记忆情感表 / §3.1 副本任务表）
STAGE_ROW_SPOT = {
    "tiancai": [
        ("现实线（1–6）", ["6", "24", "4.00", "4", "1"]),
        ("现实线（58–72）", ["15", "61", "4.07", "7", "3"]),
        ("现实线（58–72）", ["6", "0.40"]),
        ("第2段（32–57）", ["5", "0.19"]),
        ("第6段（107–141）", ["35", "134", "3.83", "19", "13"]),
        ("芝士世界（高中线）（171–176）", ["6", "31", "5.17", "4", "11"]),
        ("芝士世界（高中线）（177–221）", ["45", "185", "4.11", "25", "21"]),
    ],
    "feitu": [
        ("第一卷·主线（38–43）", ["6", "26", "4.33", "2"]),
        ("第一卷·主线（181–194）", ["6"]),
        ("第一卷·主线（220–232）", ["13", "108", "8.31", "29"]),
        ("丧尸之城（259–271）", ["13", "108", "8.31", "25"]),
        ("永生药业基金会（195–219）", ["25", "159", "6.36", "26"]),
        ("永生药业基金会（195–219）", ["65"]),
        ("追杀人的房子（28–37）", ["24"]),
        ("霉菌之城（279–289）", ["11", "49", "4.45", "19"]),
        ("第二卷·主线（384–399）", ["4"]),
    ],
}

# 承载核心结论的锚点数字：改了阶段口径就会变的那些
ANCHORS = {
    "tiancai": ["421", "50.5%", "10.2%", "2.00", "5.17", "0.40", "0.38",
                "0.07", "107", "59.1%", "48.0%", "400", "5.9",
                "33.4%", "6.03", "67.8%", "91.2%", "阿尔茨海默"],
    "feitu": ["65.8%", "34.2%", "0.11", "0.06", "1.7", "8.31", "4.33",
              "4.45", "1369", "1209", "235", "202", "5.83", "5.99", "9.1%",
              "9.0%", "3.26", "51.9%", "40.0%", "141"],
}

# 已证伪的旧值（v1 文档抄旧素材包写错的黑名单）：再出现即 FAIL
STALE = {
    "tiancai": ["84.20", "32–84", "3–14", "19.7%", "差一个数量级", "密度高峰在第6段"],
    "feitu": ["98.57", "48–113", "第一卷·主线 41", "副本弧 4–8", "4–8 件/章"],
}


def stage_string_errors(book, doc, phases):
    """a. 覆盖 + b. 防虚构。"""
    errs = []
    for p in phases:
        pat = (re.escape(p["name"]) + r"[（(]\s*%d\s*[–—~～-]\s*%d\s*[）)]"
               % (p["s"], p["e"]))
        if not re.search(pat, doc):
            errs.append("文档缺少阶段字符串: %s（%d–%d）" % (p["name"], p["s"], p["e"]))
    for name in sorted({p["name"] for p in phases}):
        real = {(p["s"], p["e"]) for p in phases if p["name"] == name}
        for m in re.finditer(re.escape(name) + r"[（(]\s*(\d+)\s*[–—~～-]\s*(\d+)[）)]", doc):
            if (int(m.group(1)), int(m.group(2))) not in real:
                errs.append("文档出现虚构阶段区间: %s" % m.group(0))
    return errs


def row_spot_errors(book, doc):
    """c. 逐行 spot check：含该阶段名的行里，必须有一行单元格全中。"""
    errs = []
    for stage, cells in STAGE_ROW_SPOT[book]:
        ok = False
        for line in doc.splitlines():
            if stage in line:
                tail = line.split(stage, 1)[1].strip().strip("|")
                got = [c.strip() for c in tail.split("|")]
                if all(c in got for c in cells):
                    ok = True
                    break
        if not ok:
            errs.append("文档未找到含 %s 且单元格为 %s 的行" % (stage, cells))
    return errs


# KG_SPEC ④′ canonical 值（同把尺子）
CANON = {
    "tiancai": {
        "dom": 3, "dom_pct": 0.6, "cameo_pct": 50.7, "me": 29, "me_pct": 3.5,
        "cp": 1, "cp_pct": 0.1, "prod_pct": 12.9, "inst": 23, "inst_pct": 2.8,
        "grow": 131, "grow_pct": 15.7, "dens": 3.77, "cmb": 93, "cmb_pct": 11.2,
        "char_total": 140, "ev_total": 833, "rel_total": 482,
        # v3.10 八学科（去重拓扑 / 称谓 / 信息 / 秩序 / 伦理 / 性别覆盖）
        "pairs": 80, "nodes": 59, "iso": 82, "iso_pct": 58.6, "comps": 1,
        "max_comp": 59, "max_comp_pct": 42.1, "top1": 29,
        "alias_total": 166, "alias_pct": 40.0, "q_picked": 25, "q_attr": 10, "q_pct": 40.0,
        "info": 37, "info_pct": 4.4, "law_ratio": 0.25, "rescue_pairs": 8,
        "gender_n": 14, "gender_pct": 10.0,
    },
    "feitu": {
        "dom": 315, "dom_pct": 19.6, "cameo_pct": 54.6, "me": 38, "me_pct": 1.5,
        "cp": 373, "cp_pct": 14.4, "prod_pct": 7.2, "inst": 72, "inst_pct": 2.8,
        "grow": 7, "grow_pct": 0.3, "dens": 5.90, "cmb": 451, "cmb_pct": 17.4,
        "char_total": 379, "ev_total": 2591, "rel_total": 1606,
        # v3.10 八学科
        "pairs": 492, "nodes": 293, "iso": 119, "iso_pct": 31.4, "comps": 6,
        "max_comp": 283, "max_comp_pct": 74.7, "top1": 126,
        "alias_total": 479, "alias_pct": 53.0, "q_picked": 171, "q_attr": 156, "q_pct": 91.2,
        "info": 442, "info_pct": 17.1, "law_ratio": 0.16, "rescue_pairs": 52,
        "gender_n": 23, "gender_pct": 6.1,
    },
}


def main():
    ok = True
    for book in ("tiancai", "feitu"):
        got = recompute(book)
        canon = CANON[book]
        doc_path = os.path.join(BASE, "docs", "perspectives_%s.md" % book)
        doc = open(doc_path, encoding="utf-8").read() if os.path.exists(doc_path) else ""
        print("=" * 60)
        print("《%s》复核" % book)
        # 1) 与 canonical 比
        checks = [
            ("支配+上下级 边", got["dom"], canon["dom"]),
            ("支配+上下级 %", got["dom_pct"], canon["dom_pct"]),
            ("龙套 %", got["cameo_pct"], canon["cameo_pct"]),
            ("记忆情感 件", got["me"], canon["me"]),
            ("记忆情感 %", got["me_pct"], canon["me_pct"]),
            ("副本任务 件", got["cp"], canon["cp"]),
            ("副本任务 %", got["cp_pct"], canon["cp_pct"]),
            ("生产+商业 %", got["prod_pct"], canon["prod_pct"]),
            ("制度秩序 件", got["inst"], canon["inst"]),
            ("制度秩序 %", got["inst_pct"], canon["inst_pct"]),
            ("成长学习 件", got["grow"], canon["grow"]),
            ("成长学习 %", got["grow_pct"], canon["grow_pct"]),
            ("事件密度", got["dens"], canon["dens"]),
            ("冲突+战斗 件", got["cmb"], canon["cmb"]),
            ("冲突+战斗 %", got["cmb_pct"], canon["cmb_pct"]),
            ("人物总数", got["char_total"], canon["char_total"]),
            ("事件总数", got["ev_total"], canon["ev_total"]),
            ("关系总数", got["rel_total"], canon["rel_total"]),
            # v3.10 新增八学科
            ("去重关系对", got["pairs"], canon["pairs"]),
            ("有边节点", got["nodes"], canon["nodes"]),
            ("零关系人物", got["iso"], canon["iso"]),
            ("零关系 %", got["iso_pct"], canon["iso_pct"]),
            ("连通分量", got["comps"], canon["comps"]),
            ("最大分量", got["max_comp"], canon["max_comp"]),
            ("最大分量 %", got["max_comp_pct"], canon["max_comp_pct"]),
            ("度中心性 top1", got["top1"], canon["top1"]),
            ("别名总数", got["alias_total"], canon["alias_total"]),
            ("有别名 %", got["alias_pct"], canon["alias_pct"]),
            # 缺 quotes.json 时置 None，由下方的比对循环判为「跳过」而非「不一致」
            ("对白入选", got["q_picked"] if got["has_quotes"] else None, canon["q_picked"]),
            ("对白可归属", got["q_attr"] if got["has_quotes"] else None, canon["q_attr"]),
            ("对白归属 %", (got["q_pct"] if got["has_quotes"] else None), canon["q_pct"]),
            ("信息类事件", got["info"], canon["info"]),
            ("信息类 %", got["info_pct"], canon["info_pct"]),
            ("秩序/暴力比", got["law_ratio"], canon["law_ratio"]),
            ("救助去重对", got["rescue_pairs"], canon["rescue_pairs"]),
            ("性别可判定", got["gender_n"], canon["gender_n"]),
            ("性别可判定 %", got["gender_pct"], canon["gender_pct"]),
        ]
        for label, g, c in checks:
            if g is None:
                # 输入数据不在版本库里（原文引语），无从复算——跳过而非判失败。
                # 这样本地有数据时仍会真校验，CI 上也不会用假失败骗人。
                print("  [SKIP] %s: 依赖 data/%s/quotes.json（本地私有数据，不入库）"
                      % (label, book))
                continue
            same = (abs(g - c) < 0.05) if isinstance(g, float) else (g == c)
            flag = "OK " if same else "FAIL"
            if not same:
                ok = False
            print("  [%s] %s: 现算=%s canonical=%s" % (flag, label, g, c))
        # 2) 文档漂移：关键百分比字符串须出现在文档
        must_contain = [
            "%.1f%%" % got["dom_pct"],
            "%.1f%%" % got["cameo_pct"],
            "%.1f%%" % got["me_pct"],
            "%.1f%%" % got["cp_pct"],
            "%.1f%%" % got["prod_pct"],
            "%.1f%%" % got["inst_pct"],
            "%.1f%%" % got["grow_pct"],
            "%.1f%%" % got["cmb_pct"],
            str(got["me"]), str(got["cp"]), str(got["grow"]),
            str(got["dom"]), str(got["inst"]), str(got["cmb"]),
            # v3.10：八学科的关键数字必须出现在正文
            "%.1f%%" % got["iso_pct"],
            "%.1f%%" % got["max_comp_pct"],
            "%.1f%%" % got["alias_pct"],
            # 缺 quotes.json 时 q_pct 是 0.0，这个串多半不在文档里——
            # 那时是在惩罚「没有数据」，而不是抓住了文档漂移，故跳过。
        ] + (["%.1f%%" % got["q_pct"]] if got["has_quotes"] else []) + [
            "%.1f%%" % got["info_pct"],
            "%.2f" % got["law_ratio"],
            str(got["pairs"]), str(got["top1"]), str(got["rescue_pairs"]),
            "%d/%d 人（%.1f%%）" % (got["gender_n"], got["char_total"], got["gender_pct"]),
        ]
        for s in must_contain:
            # 文档里百分比多写作 "25.5%" 或 "(25.5%)"，用子串匹配
            if s not in doc:
                ok = False
                print("  [FAIL] 文档未包含关键数字: %s" % s)
        if not must_contain:
            pass
        # 额外：确认文档确实写了这两个总量
        if str(got["char_total"]) not in doc or str(got["ev_total"]) not in doc:
            ok = False
            print("  [FAIL] 文档未包含人物/事件总量")
        # 3) 阶段级核对（覆盖 / 防虚构 / 逐行 spot / 锚点 / 旧值黑名单）
        phases = derive_payload_phases(book)
        for e in stage_string_errors(book, doc, phases):
            ok = False
            print("  [FAIL] " + e)
        for e in row_spot_errors(book, doc):
            ok = False
            print("  [FAIL] " + e)
        for a in ANCHORS[book]:
            if a not in doc:
                ok = False
                print("  [FAIL] 文档缺少锚点数字: %s" % a)
        for s in STALE[book]:
            if s in doc:
                ok = False
                print("  [FAIL] 文档仍含已证伪的旧值: %s" % s)
        print("  阶段级核对：%d 个阶段字符串 / %d 行 spot / %d 锚点 / %d 旧值黑名单"
              % (len(phases), len(STAGE_ROW_SPOT[book]), len(ANCHORS[book]), len(STALE[book])))
    print("=" * 60)
    if ok:
        print("[OK] 全部一致：现算 == ④′ canonical == perspectives_*.md")
        return 0
    print("[FAIL] 存在不一致，见上。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
