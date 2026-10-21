# -*- coding: utf-8 -*-
"""
多学科视角分析 · 现算素材包（KG_SPEC.md ④ / ④′）
=============================================
为每本书从 data/<book>/data.json 现算各学科问题所需的**细分**数字，
输出 docs/_persp_<book>.md 素材包，供人工撰写解读。

纪律（继承 KG_SPEC.md ⑥）：
- 每个结论必须能指到「节点/边 + 数量 + 占比」，写完能回 data.json 复算；
- 口径严格沿用 graph_spec.py：支配+上下级 = rel_base 的支配+上下级，
  生产+商业 = 地点 type_base 的「生产处理」+「商业服务」；
- 不另起口径，和 ④′ 汇总表同把尺子。

用法：python src/perspectives_prep.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 共享核心：阶段划分与章号换算的唯一真源。
# 本文件此前自带一份 derive_phases 拷贝（与 generate_report.py 写法还不同，
# 如 TC_TIME_HINTS 末项一个是「小时候→童年线」的死项、一个是「童年→童年线」），
# 是 v3.3 学科文档数字漂移的根因；现统一收敛到 src/core。
from core.books import BASE, load  # noqa: E402
from core.chapters import build_idx2no, build_key2no  # noqa: E402
from core.phases import derive_phases, phases_to_no, phase_key  # noqa: E402


def derive(book, data):
    """派生阶段并转成书中真实章号（no 口径）。唯一真源 = core.phases。"""
    raw = load(os.path.join(BASE, "data", book, "extract_raw.json"), [])
    return phases_to_no(derive_phases(book, data["chapters"], raw),
                        build_idx2no(data["chapters"]))


def pct(x, n):
    return "%.1f%%" % (100.0 * x / n) if n else "0%"


def main():
    for book in ("tiancai", "feitu"):
        data = load(os.path.join(BASE, "data", book, "data.json"))
        chars, locs, evs, rels = (data["characters"], data["locations"],
                                  data["events"], data["relations"])
        key2no = build_key2no(data["chapters"])
        idx2no = build_idx2no(data["chapters"])
        phases = derive(book, data)
        # 把章号区间烤进阶段名，保证阶段名唯一（天才多段同名会撞），供 ev_stage/聚合用。
        # 唯一键格式统一由 core.phases.phase_key 定义（「名（起–止）」），前端链接也认这个格式。
        for p in phases:
            p["name"] = phase_key(p)

        # 事件 → 主阶段（first_no 口径：事件所有章的最小 no 落到的阶段）
        stage_of = {}
        for p in phases:
            for no in range(p["s"], p["e"] + 1):
                stage_of[no] = p["name"]
        def ev_stage(e):
            nos = sorted({key2no[k] for k in (e.get("chapters") or []) if k in key2no})
            if not nos:
                return None
            return stage_of.get(nos[0])
        # 关系边 → 涉及章的 no 集合
        def rel_nos(r):
            return sorted({key2no[k] for k in (r.get("chapters") or []) if k in key2no})

        out = []
        W = out.append
        W("# 多学科视角素材包 · 《%s》\n" % book)
        W("> 全部数字由 src/perspectives_prep.py 从 data.json 现算；括号百分比分母为对应总数。\n")

        # 0. 与 KG_SPEC ④′ 同把尺子的自检（确认口径没漂）
        W("## 0 口径自检（应等于 KG_SPEC ④′ 同格数字）\n")
        tb = {}   # 事件 type_base
        for e in evs:
            tb[e.get("type_base", "")] = tb.get(e.get("type_base", ""), 0) + 1
        rb = {}   # 关系 rel_base
        for r in rels:
            rb[r.get("rel_base", "")] = rb.get(r.get("rel_base", ""), 0) + 1
        lb = {}   # 地点 type_base
        for l in locs:
            lb[l.get("type_base", "")] = lb.get(l.get("type_base", ""), 0) + 1
        tr = {}   # 人物 tier
        for c in chars:
            tr[c.get("tier", "")] = tr.get(c.get("tier", ""), 0) + 1
        dom = rb.get("支配", 0) + rb.get("上下级", 0)
        prod = lb.get("生产处理", 0) + lb.get("商业服务", 0)
        selfcheck = [
            ("支配+上下级 边", "%d 条（%s）" % (dom, pct(dom, len(rels)))),
            ("龙套人物占比", "%s（%d/%d）" % (pct(tr.get("cameo", 0), len(chars)),
                                             tr.get("cameo", 0), len(chars))),
            ("记忆情感事件", "%d 件（%s）" % (tb.get("记忆情感", 0), pct(tb.get("记忆情感", 0), len(evs)))),
            ("副本任务事件", "%d 件（%s）" % (tb.get("副本任务", 0), pct(tb.get("副本任务", 0), len(evs)))),
            ("生产+商业场所", "%d 处（%s）" % (prod, pct(prod, len(locs)))),
            ("制度秩序事件", "%d 件（%s）" % (tb.get("制度秩序", 0), pct(tb.get("制度秩序", 0), len(evs)))),
            ("成长学习事件", "%d 件（%s）" % (tb.get("成长学习", 0), pct(tb.get("成长学习", 0), len(evs)))),
            ("事件密度", "%.2f 件/章" % (len(evs) / len(data["chapters"]))),
            ("冲突+战斗", "%d 件（%s）" % (tb.get("战斗", 0) + tb.get("冲突对峙", 0),
                                           pct(tb.get("战斗", 0) + tb.get("冲突对峙", 0), len(evs)))),
        ]
        W("| 指标 | 现算值 | 对应学科 |\n|---|---|---|")
        for k, v in selfcheck:
            W("| %s | %s | — |" % (k, v))
        W("")

        # 1. 社会学：关系结构 + 权力 + 分层
        W("## 1 社会学\n")
        W("### 1.1 关系基类全分布（%d 条边）\n" % len(rels))
        W("| 关系基类 | 条数 | 占比 | |\n|---|---|---|---|")
        for k, v in sorted(rb.items(), key=lambda x: -x[1]):
            W("| %s | %d | %s |" % (k, v, pct(v, len(rels))))
        W("")
        W("### 1.2 权力/支配结构（支配 + 上下级，共 %d 条）\n" % dom)
        if book == "feitu":
            # 谁支配谁 / 谁是上级：按 (from→to) 聚合，支配与上下级分开统计
            pair_dom = {}
            up_dom = {}
            pair_sup = {}
            up_sup = {}
            for r in rels:
                base = r.get("rel_base")
                if base == "支配":
                    pair_dom[(r["from"], r["to"])] = pair_dom.get((r["from"], r["to"]), 0) + 1
                    up_dom[r["from"]] = up_dom.get(r["from"], 0) + 1
                elif base == "上下级":
                    pair_sup[(r["from"], r["to"])] = pair_sup.get((r["from"], r["to"]), 0) + 1
                    up_sup[r["from"]] = up_sup.get(r["from"], 0) + 1
            dom_top = "、".join("%s×%d" % (k, v) for k, v in
                               sorted(up_dom.items(), key=lambda x: -x[1])[:8]) if rb.get("支配", 0) else "（无）"
            sup_top = "、".join("%s×%d" % (k, v) for k, v in
                               sorted(up_sup.items(), key=lambda x: -x[1])[:8]) if rb.get("上下级", 0) else "（无）"
            W("- 支配关系 %d 条（支配方 top）：%s" % (rb.get("支配", 0), dom_top))
            W("- 上下级关系 %d 条（上级方 top）：%s" % (rb.get("上下级", 0), sup_top))
        else:
            W("- 天才基本法只有上下级 %d 条、支配 0 条；**第一大类关系是师徒 %d 条（%s）**。" % (
                rb.get("上下级", 0), rb.get("师徒", 0), pct(rb.get("师徒", 0), len(rels))))
            # 师徒 top 双方
            pair = {}
            for r in rels:
                if r.get("rel_base") == "师徒":
                    pair[(r["from"], r["to"])] = pair.get((r["from"], r["to"]), 0) + 1
            W("  师徒关系 top 双方：%s" % "、".join(
                "%s→%s×%d" % (a, b, v) for (a, b), v in
                sorted(pair.items(), key=lambda x: -x[1])[:6]))
        W("")
        W("### 1.3 分层 vs 流动（人物 tier 分布）\n")
        W("| 层级 | 人数 | 占比 | 人均关系边数（派生） |")
        W("|---|---|---|---|")
        # 人物-事件参与边 + 人物关系边 数（派生：participants 反推 + relations 端点）
        rel_count = {}
        for r in rels:
            rel_count[r["from"]] = rel_count.get(r["from"], 0) + 1
            rel_count[r["to"]] = rel_count.get(r["to"], 0) + 1
        part_count = {}
        for e in evs:
            for p in (e.get("participants") or []):
                part_count[p] = part_count.get(p, 0) + 1
        for tier in ("core", "major", "minor", "cameo"):
            grp = [c for c in chars if c.get("tier") == tier]
            if not grp:
                continue
            avg_rel = sum(rel_count.get(c["name"], 0) + part_count.get(c["name"], 0)
                          for c in grp) / len(grp)
            W("| %s | %d | %s | %.1f |" % (tier, len(grp),
                                           pct(len(grp), len(chars)), avg_rel))
        W("")

        # 2. 心理学：记忆情感事件阶段分布
        W("## 2 心理学（记忆情感事件）\n")
        me = [e for e in evs if e.get("type_base") == "记忆情感"]
        W("- 记忆情感事件共 **%d 件（%s）**；按主阶段分布：\n" % (
            len(me), pct(len(me), len(evs))))
        by_stage = {}
        for e in me:
            s = ev_stage(e)
            by_stage[s] = by_stage.get(s, 0) + 1
        W("| 阶段 | 记忆情感事件数 |")
        W("|---|---|")
        for s in [p["name"] for p in phases]:
            if by_stage.get(s):
                W("| %s | %d |" % (s, by_stage[s]))
        W("")
        # 主角参与的情感事件
        protag = "林朝夕" if book == "tiancai" else "祝宁"
        pm = [e for e in me if protag in (e.get("participants") or [])]
        W("- 主角 %s 参与的记忆情感事件 **%d 件**（占其全部记忆情感事件的 %s）。\n" % (
            protag, len(pm), pct(len(pm), len(me)) if me else "0%"))
        W("")

        # 3. 经济学（废土为主）
        W("## 3 经济学\n")
        if book == "feitu":
            W("- 副本任务事件 **%d 件（%s）**；按副本弧（阶段）分布 top：\n" % (
                tb.get("副本任务", 0), pct(tb.get("副本任务", 0), len(evs))))
            by_arc = {}
            for e in evs:
                if e.get("type_base") == "副本任务":
                    s = ev_stage(e)
                    by_arc[s] = by_arc.get(s, 0) + 1
            W("| 副本弧 | 副本任务事件数 |")
            W("|---|---|")
            for s, v in sorted(by_arc.items(), key=lambda x: -x[1])[:12]:
                W("| %s | %d |" % (s, v))
            W("")
            W("- 交易关系 **%d 条**；生产+商业场所 **%d 处（%s）**。" % (
                rb.get("交易", 0), prod, pct(prod, len(locs))))
        else:
            W("- 天才基本法几乎没有副本任务（%d 件），成长学习 %d 件（%s）——经济系统稀疏，\
这是个以智力成长而非任务-收益为骨架的故事。\n" % (
                tb.get("副本任务", 0), tb.get("成长学习", 0), pct(tb.get("成长学习", 0), len(evs))))
        W("")

        # 4. 政治学
        W("## 4 政治学（制度秩序 × 上下级）\n")
        inst = [e for e in evs if e.get("type_base") == "制度秩序"]
        inst_nos = set()
        for e in inst:
            inst_nos |= {key2no[k] for k in (e.get("chapters") or []) if k in key2no}
        up_nos = set()
        for r in rels:
                if r.get("rel_base") == "上下级":
                    up_nos |= set(rel_nos(r))
        co = inst_nos & up_nos
        W("- 制度秩序事件 **%d 件**；上下级关系 **%d 条**。" % (len(inst), rb.get("上下级", 0)))
        W("- 两者章节共现 **%d 章**（制度秩序事件出现的章里，%s 同时有上下级关系）。\n" % (
            len(co), pct(len(co), len(inst_nos)) if inst_nos else "0%"))
        W("")

        # 5. 叙事学：每阶段事件密度与类型构成（张力曲线）
        W("## 5 叙事学（张力曲线）\n")
        W("| 阶段 | 章数 | 事件数 | 密度(件/章) | 主要类型构成（top3） |")
        W("|---|---|---|---|---|")
        for p in phases:
            ph_evs = [e for e in evs if ev_stage(e) == p["name"]]
            ch_n = p["e"] - p["s"] + 1
            dens = len(ph_evs) / ch_n if ch_n else 0
            sub = {}
            for e in ph_evs:
                sub[e.get("type_base", "")] = sub.get(e.get("type_base", ""), 0) + 1
            top3 = "、".join("%s %d" % (k, v) for k, v in
                             sorted(sub.items(), key=lambda x: -x[1])[:3])
            W("| %s | %d | %d | %.2f | %s |" % (
                p["name"], ch_n, len(ph_evs), dens, top3))
        W("")

        # 6. 教育学（天才）
        W("## 6 教育学（成长学习弧）\n")
        gl = [e for e in evs if e.get("type_base") == "成长学习"]
        W("- 成长学习事件 **%d 件（%s）**" % (len(gl), pct(len(gl), len(evs))))
        if book == "tiancai":
            by_stage = {}
            for e in gl:
                s = ev_stage(e)
                by_stage[s] = by_stage.get(s, 0) + 1
            W("；按主阶段分布：\n")
            W("| 阶段 | 成长学习事件数 |")
            W("|---|---|")
            for s in [p["name"] for p in phases]:
                if by_stage.get(s):
                    W("| %s | %d |" % (s, by_stage[s]))
        else:
            W("——废土只有 %d 件，说明这不是一部关于「成长」的小说，祝宁的弧光是「活下去/弑神」而非「习得」。\n" % len(gl))
        W("")

        # 7. 地理学：空间结构（地点类型 / 承载事件 / 跨阶段 / 坐标状态）
        W("## 7 地理学（空间结构）\n")
        W("### 7.1 地点类型分布（%d 处）\n" % len(locs))
        W("| 地点基类 | 处数 | 占比 |\n|---|---|---|")
        for k, v in sorted(lb.items(), key=lambda x: -x[1]):
            W("| %s | %d | %s |" % (k, v, pct(v, len(locs))))
        W("")
        # 地点承载事件：events[].location 与地点名精确匹配（不做模糊，宁可少算）
        loc_names = {l["name"] for l in locs}
        ev_by_loc = {}
        no_loc = 0
        for e in evs:
            ln = e.get("location") or ""
            if not ln:
                no_loc += 1
                continue
            if ln in loc_names:
                ev_by_loc[ln] = ev_by_loc.get(ln, 0) + 1
        top_loc = sorted(ev_by_loc.items(), key=lambda x: -x[1])[:10]
        W("### 7.2 地点承载事件 top10（location 精确匹配，共 %d 件有地点、%d 件无地点）\n"
          % (len(evs) - no_loc, no_loc))
        W("| 地点 | 事件数 | 占全部事件 |\n|---|---|---|")
        for k, v in top_loc:
            W("| %s | %d | %s |" % (k, v, pct(v, len(evs))))
        top10_share = sum(v for _, v in top_loc)
        W("")
        W("- top10 地点合计承载 **%d 件（%s）**，空间集中度可据此判断。" % (
            top10_share, pct(top10_share, len(evs))))
        W("")
        # 跨阶段地点：地点出现的事件落在多少个不同阶段
        loc_stages = {}
        for e in evs:
            ln = e.get("location") or ""
            if ln not in loc_names:
                continue
            s = ev_stage(e)
            if s:
                loc_stages.setdefault(ln, set()).add(s)
        W("### 7.3 跨阶段地点 top10（同一地点出现在多少个阶段）\n")
        W("| 地点 | 阶段数 |\n|---|---|")
        for k, v in sorted(loc_stages.items(), key=lambda x: -len(x[1]))[:10]:
            W("| %s | %d |" % (k, len(v)))
        W("")
        # 坐标状态（geo_annotations）
        geo = load(os.path.join(BASE, "data", book, "geo_annotations.json"), {})
        st = {}
        for v in (geo.values() if isinstance(geo, dict) else []):
            if isinstance(v, dict):
                key = v.get("status") or v.get("kind") or "未标"
                st[key] = st.get(key, 0) + 1
        W("- 坐标标注状态：%s\n" % ("、".join("%s %d" % (k, v) for k, v in
                                              sorted(st.items(), key=lambda x: -x[1])) or "（无文件）"))

        # 8. 网络科学：关系图拓扑
        # 必须先说清一个数据事实：关系表里同一对人物会被跨章重复记多条
        # （天才 482 条边只覆盖 253 个唯一对，党爱萍→某人对重复 50 次）。
        # 直接拿「边数」算度会把重复计数当成社交广度，所以这里同时给两套：
        # 原始边（数据原样）/ 去重无向对（拓扑真实形状），表格一律用去重口径。
        W("## 8 网络科学（关系图拓扑）\n")
        deg = {}
        adj = {}
        for r in rels:
            a, b = r["from"], r["to"]
            if a == b:
                continue
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
        pairs_u = set()
        deg_u = {}
        for r in rels:
            a, b = r["from"], r["to"]
            if a == b:
                continue
            pairs_u.add(tuple(sorted((a, b))))
            deg_u[a] = deg_u.get(a, 0) + 1
            deg_u[b] = deg_u.get(b, 0) + 1
        # 去重后按对重算：一对算 1
        deg_d = {}
        for a, b in pairs_u:
            deg_d[a] = deg_d.get(a, 0) + 1
            deg_d[b] = deg_d.get(b, 0) + 1
        nodes = sorted(deg_d)
        raw_edges = len(rels)
        edges = len(pairs_u)
        avg_deg = (2.0 * edges / len(nodes)) if nodes else 0
        char_names = {c["name"] for c in chars}
        iso = [c["name"] for c in chars if c["name"] not in deg_d]
        W("- 原始关系边 **%d 条**，去重（无向对）后 **%d 对**，平均每对 **%.2f 条**"
          "——同对被跨章重复计数是抽取的既有现象，下面所有度数一律用**去重口径**。" % (
              raw_edges, edges, (raw_edges / edges) if edges else 0))
        W("- 关系图：节点 **%d**、去重边 **%d**、平均度 **%.2f**；**%d/%d 人物（%s）零关系边**（孤立点）。" % (
            len(nodes), edges, avg_deg, len(iso), len(chars), pct(len(iso), len(chars))))
        # 连通分量（BFS）
        seen = set()
        comps = []
        for n in nodes:
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
        W("- 连通分量 **%d** 个，最大分量 **%d 节点（占有人物 %s）**。" % (
            len(comps), len(comps[0]) if comps else 0,
            pct(len(comps[0]) if comps else 0, len(chars))))
        W("")
        W("### 8.1 度中心性 top10（去重口径）\n")
        W("| 人物 | 关系度（去重） | 原始条数 |\n|---|---|---|")
        for k, v in sorted(deg_d.items(), key=lambda x: -x[1])[:10]:
            W("| %s | %d | %d |" % (k, v, deg.get(k, 0)))
        W("")
        degs = sorted(deg_d.values())
        d1 = sum(1 for v in degs if v == 1)
        W("- 度=1 的节点 **%d 个（占有边节点的 %s）**——长尾程度。" % (
            d1, pct(d1, len(nodes))))
        # 分层的平均关系度
        W("")
        W("| 层级 | 人数 | 平均关系度 |\n|---|---|---|")
        for tier in ("core", "major", "minor", "cameo"):
            grp = [c for c in chars if c.get("tier") == tier]
            if not grp:
                continue
            W("| %s | %d | %.2f |" % (tier, len(grp),
                                      sum(deg_d.get(c["name"], 0) for c in grp) / len(grp)))
        W("")

        # 9. 语言学：称谓系统与话语
        W("## 9 语言学（称谓与话语）\n")
        al = [c for c in chars if c.get("aliases")]
        al_total = sum(len(c.get("aliases") or []) for c in chars)
        W("- 别名总数 **%d**，人均 **%.2f**；**%d/%d 人（%s）至少有一个别名**。" % (
            al_total, al_total / len(chars) if chars else 0, len(al), len(chars),
            pct(len(al), len(chars))))
        W("")
        W("### 9.1 别名最多 top8（一人多名的程度）\n")
        W("| 人物 | 别名数 | 例 |\n|---|---|---|")
        for c in sorted(chars, key=lambda x: -len(x.get("aliases") or []))[:8]:
            W("| %s | %d | %s |" % (c["name"], len(c.get("aliases") or []),
                                    "、".join((c.get("aliases") or [])[:5])))
        W("")
        # 称谓后缀：从别名里数亲属/敬称词，反映称谓系统（精确匹配词表，不做分词）
        HONOR = ["哥", "姐", "叔", "姨", "爷", "奶", "老师", "师父", "师傅", "同学",
                 "先生", "小姐", "老板", "队长", "教授", "医生"]
        hon = {}
        for c in chars:
            for a in (c.get("aliases") or []):
                for h in HONOR:
                    if h in a:
                        hon[h] = hon.get(h, 0) + 1
        W("### 9.2 称谓词在别名中的出现次数（词表命中，非分词）\n")
        W("| 称谓 | 次数 |\n|---|---|")
        for k, v in sorted(hon.items(), key=lambda x: -x[1]):
            W("| %s | %d |" % (k, v))
        W("")
        q = load(os.path.join(BASE, "data", book, "quotes.json"), {})
        qm = q.get("meta", {})
        W("- 对白候选 **%s** 句，入选 **%s** 条；其中能归属到说话人 **%s** 条（%s），"
          "涉及 **%s** 位说话人。" % (
              qm.get("dialogue_lines", "?"), qm.get("picked", "?"), qm.get("attributed", "?"),
              pct(qm.get("attributed", 0), qm.get("picked", 0) or 1), qm.get("speakers", "?")))
        W("- 叙述/独白候选 %s 句，入选 %s 条。" % (
            qm.get("narr_candidates", "?"), qm.get("narr_picked", "?")))
        W("")

        # 10. 传播学：信息获取 vs 信息交换
        W("## 10 传播学（信息结构）\n")
        info_n = tb.get("情报对话", 0)
        plot_n = tb.get("密谋博弈", 0)
        exp_n = tb.get("探索发现", 0)
        W("- 情报对话 **%d 件（%s）**、密谋博弈 **%d 件（%s）**、探索发现 **%d 件（%s）**。" % (
            info_n, pct(info_n, len(evs)), plot_n, pct(plot_n, len(evs)),
            exp_n, pct(exp_n, len(evs))))
        W("- 信息类合计（情报对话+密谋博弈）**%d 件（%s）**；探索发现代表「靠行动获取信息」。\n" % (
            info_n + plot_n, pct(info_n + plot_n, len(evs))))
        by_stage_info = {}
        for e in evs:
            if e.get("type_base") in ("情报对话", "密谋博弈"):
                s = ev_stage(e)
                by_stage_info[s] = by_stage_info.get(s, 0) + 1
        W("| 阶段 | 信息类事件数 |\n|---|---|")
        for s, v in sorted(by_stage_info.items(), key=lambda x: -x[1])[:10]:
            W("| %s | %d |" % (s, v))
        W("")
        # 参与者规模：信息交换是小圈还是大会
        def avg_part(types):
            xs = [len(e.get("participants") or []) for e in evs
                  if e.get("type_base") in types]
            return sum(xs) / len(xs) if xs else 0
        W("- 平均参与者：情报对话 **%.2f 人**，密谋博弈 **%.2f 人**，日常生存 **%.2f 人**"
          "（对比可知信息事件是密室还是广场）。\n" % (
              avg_part(("情报对话",)), avg_part(("密谋博弈",)), avg_part(("日常生存",))))

        # 11. 法学·秩序
        W("## 11 法学·秩序（规则与暴力）\n")
        inst_n = tb.get("制度秩序", 0)
        conf_n = tb.get("冲突对峙", 0)
        fight_n = tb.get("战斗", 0)
        W("- 制度秩序 **%d 件（%s）**、冲突对峙 **%d 件（%s）**、战斗 **%d 件（%s）**。" % (
            inst_n, pct(inst_n, len(evs)), conf_n, pct(conf_n, len(evs)),
            fight_n, pct(fight_n, len(evs))))
        W("- 敌对关系 **%d 条（%s）**。秩序事件 / 暴力事件（冲突对峙+战斗）= **%.2f**。" % (
            rb.get("敌对", 0), pct(rb.get("敌对", 0), len(rels)),
            (inst_n / (conf_n + fight_n)) if (conf_n + fight_n) else 0))
        W("")
        by_stage_inst = {}
        for e in evs:
            if e.get("type_base") == "制度秩序":
                s = ev_stage(e)
                by_stage_inst[s] = by_stage_inst.get(s, 0) + 1
        W("| 阶段 | 制度秩序事件数 |\n|---|---|")
        for s, v in sorted(by_stage_inst.items(), key=lambda x: -x[1])[:10]:
            W("| %s | %d |" % (s, v))
        W("")

        # 12. 伦理学：救助、牺牲、背叛
        W("## 12 伦理学（救助·牺牲·背叛）\n")
        help_n = rb.get("救助", 0)
        W("- 救助关系 **%d 条（%s）**、敌对 **%d 条（%s）**、合作 **%d 条（%s）**。" % (
            help_n, pct(help_n, len(rels)), rb.get("敌对", 0), pct(rb.get("敌对", 0), len(rels)),
            rb.get("合作", 0), pct(rb.get("合作", 0), len(rels))))
        # 双向救助：A→B 且 B→A
        pairs = {(r["from"], r["to"]) for r in rels if r.get("rel_base") == "救助"}
        mutual = {p for p in pairs if (p[1], p[0]) in pairs}
        n_mutual = len(mutual) // 2
        W("- 救助关系去重后 **%d 个有向对**（原始 %d 条，同对平均 %.1f 条）："
          "**双向 %d 对**、单向 **%d 对**。" % (
              len(pairs), help_n, (help_n / len(pairs)) if pairs else 0,
              n_mutual, len(pairs) - n_mutual * 2))
        # 谁救谁 top
        give = {}
        for r in rels:
            if r.get("rel_base") == "救助":
                give[r["from"]] = give.get(r["from"], 0) + 1
        W("- 施救方 top8：%s\n" % "、".join(
            "%s×%d" % (k, v) for k, v in sorted(give.items(), key=lambda x: -x[1])[:8]))
        crisis_n = tb.get("危机伤亡", 0)
        rescue_n = tb.get("撤离救援", 0)
        W("- 危机伤亡事件 **%d 件（%s）**、撤离救援 **%d 件（%s）**、密谋博弈 **%d 件（%s）**"
          "（后者是「算计/背叛」的结构位）。\n" % (
              crisis_n, pct(crisis_n, len(evs)), rescue_n, pct(rescue_n, len(evs)),
              plot_n, pct(plot_n, len(evs))))
        # 主角的施救/被救
        pg = "林朝夕" if book == "tiancai" else "祝宁"
        pg_give = sum(1 for r in rels if r.get("rel_base") == "救助" and r["from"] == pg)
        pg_take = sum(1 for r in rels if r.get("rel_base") == "救助" and r["to"] == pg)
        W("- 主角 %s：施救 **%d 次**、被救 **%d 次**。\n" % (pg, pg_give, pg_take))

        # 13. 性别研究（严格词表，覆盖率必须披露）
        W("## 13 性别研究（词表判定，覆盖有限）\n")
        F_WORDS = ["女主角", "女主", "女队长", "女医生", "女异能者", "女学生", "女老板",
                   "少女", "女孩", "母亲", "妻子", "姐姐", "妹妹", "女儿", "她"]
        M_WORDS = ["男主角", "男主", "男医生", "男学生", "少年", "男孩",
                   "父亲", "丈夫", "哥哥", "弟弟", "儿子", "他"]
        fem, male, unk = [], [], []
        for c in chars:
            r = c.get("role") or ""
            head = r.split("，")[0].split(",")[0]
            is_f = any(w in head for w in F_WORDS) or any(
                w in r for w in ["之母", "之妻", "之女", "之姐", "之妹"])
            is_m = any(w in head for w in M_WORDS) or any(
                w in r for w in ["之父", "之夫", "之子", "之兄", "之弟"])
            if is_f and not is_m:
                fem.append(c)
            elif is_m and not is_f:
                male.append(c)
            else:
                unk.append(c)
        W("- 可判定 **%d/%d 人（%s）**：女 %d / 男 %d；其余 %d 人（%s）**不判**"
          "（role 里没有性别线索，或男女线索同时出现）。" % (
              len(fem) + len(male), len(chars), pct(len(fem) + len(male), len(chars)),
              len(fem), len(male), len(unk), pct(len(unk), len(chars))))
        W("")
        W("| 组 | 人数 | 核心+主要 | 平均关系度 | 平均出场章数 |\n|---|---|---|---|---|")
        for label, grp in (("女", fem), ("男", male)):
            if not grp:
                continue
            core_major = sum(1 for c in grp if c.get("tier") in ("core", "major"))
            W("| %s | %d | %d | %.2f | %.1f |" % (
                label, len(grp), core_major,
                sum(deg_d.get(c["name"], 0) for c in grp) / len(grp),
                sum(len(c.get("chapters") or []) for c in grp) / len(grp)))
        W("")
        W("- 说明：这是**称谓/亲属词的代理判定**，不是作者设定；`她/他` 在 role 里指代可能不是本人，"
          "所以只在首分句里取，且男女线索冲突时不判。结论只能用于「样本内对比」，不可外推。\n")

        # 14. 医学·身体
        W("## 14 医学·身体（疾病、创伤、身体改造）\n")
        med_ev = tb.get("科研医疗", 0)
        W("- 科研医疗事件 **%d 件（%s）**、危机伤亡 **%d 件（%s）**、医疗场所 **%d 处（%s）**。" % (
            med_ev, pct(med_ev, len(evs)), crisis_n, pct(crisis_n, len(evs)),
            lb.get("医疗场所", 0), pct(lb.get("医疗场所", 0), len(locs))))
        # 身体关键词（明确披露为关键词口径，不做语义判断）
        BODY_KW = ["感染", "污染", "尸体", "异化", "变异", "实验体", "手术", "移植",
                   "伤口", "残疾", "病", "癌", "阿尔茨海默", "精神值"]
        kw = {}
        for e in evs:
            nm = e.get("name") or ""
            for k in BODY_KW:
                if k in nm:
                    kw[k] = kw.get(k, 0) + 1
        W("- 事件名命中身体关键词：%s（关键词口径，只数事件名，不读正文）。\n" % (
            "、".join("%s %d" % (k, v) for k, v in sorted(kw.items(), key=lambda x: -x[1]))
            or "（无命中）"))

        # 15. 缺口声明（沿用 KG_SPEC ⑤）
        W("## 15 口径与缺口声明（沿用 KG_SPEC ⑤）\n")
        W("- 事件 year 字段 %d/%d 为空，时间一律用书中章号 no 与阶段轴，不用公元纪年。" % (
            sum(1 for e in evs if not e.get("year")), len(evs)))
        W("- participants 含群体称谓（全班/各校代表），派生边计数时已按非人物实体排除。")
        W("- 关系基类仍有「其他」残差（天才 %d 条 / 废土 %d 条），分析时单独说明。" % (
            rb.get("其他关系", 0), rb.get("其他关系", 0)))
        if book == "tiancai":
            W("- 源文本 57 对重复章节（防盗章伪影），对白/事件计数可能重复计入；比例类指标已留意。")

        txt = "\n".join(out)
        out_path = os.path.join(BASE, "docs", "_persp_%s.md" % book)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(txt)
        print("[done] %s → %s（%d 字）" % (book, out_path, len(txt)))


if __name__ == "__main__":
    main()
