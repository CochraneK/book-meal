# -*- coding: utf-8 -*-
"""
KG 规格说明生成器
================
输入：data/<book>/data.json（+ quotes.json）
输出：docs/KG_SPEC.md

为什么要有这个文件
------------------
后面要做「多学科视角分析」，最大的风险是**空谈**：写一段社会学解读，
却说不清结论出自图里的哪条边。这个文件先把家底摊开：

  ① 有哪些节点类型、哪些边类型，各多少条，示例长什么样；
  ② 每条边/每个字段**能不能用**（覆盖率、脏数据比例）；
  ③ 按学科列出「可以问什么问题 → 需要查什么 → 现在数据够不够」。

纪律：所有数字都从 data.json 现算，不手写。手写的数字会过期
（前面已经栽过一次：体检工具统计归约前字段，报了 43% 的过期警报）。
"""
import json
import os
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = ["tiancai", "feitu"]
TIER_CN = {"core": "核心", "major": "主要", "minor": "次要", "cameo": "龙套"}

# 学科 → (要问的问题, 需要的图查询, 数据支持度怎么算)
DISCIPLINES = [
    ("社会学", "废土里「支配/豢养」型关系占多少？谁在支配谁？",
     "关系边按 rel_base 分组，取 top 双方"),
    ("社会学", "人群是分层还是流动的？龙套占比多少？",
     "人物节点按 tier 分布 + 每人关系边数"),
    ("心理学", "主角的心理负担有多重？情感/记忆类事件集中在哪些阶段？",
     "事件节点按 type_base=记忆情感 筛，再按阶段分段"),
    ("经济学", "副本是「任务-收益」结构吗？生产/商业场所的比例？",
     "事件 type_base=副本任务 计数 + 地点 type_base 分布"),
    ("政治学", "秩序是谁定的？制度类事件与「上下级」边是否同步出现？",
     "事件 type_base=制度秩序 × 关系 rel_base=上下级 的章节共现"),
    ("叙事学", "张力曲线怎么走？每阶段的事件密度与类型构成？",
     "事件按阶段分段，统计数量与 type_base 构成"),
    ("教育学", "（天才基本法）成长/学习类事件如何随主线推进？",
     "事件 type_base=成长学习 按章节序号分布"),
]


def load(book):
    d = json.load(open(os.path.join(BASE, "data", book, "data.json"), encoding="utf-8"))
    # 坑：geo_status / zone **不在 data.json 里**，在 geo_annotations.json。
    # 第一版直接从 location 对象读，256 个地点全显示成 pending ——
    # 「没匹配到就静默用默认值」的又一例。必须显式换数据源。
    geo_path = os.path.join(BASE, "data", book, "geo_annotations.json")
    geo = json.load(open(geo_path, encoding="utf-8")) if os.path.exists(geo_path) else {}
    zpath = os.path.join(BASE, "data", book, "geo_zones.json")
    zlabel = {}
    if os.path.exists(zpath):
        zlabel = {z["key"]: z["label"]
                  for z in json.load(open(zpath, encoding="utf-8"))}
    return d, geo, zlabel


def pct(a, b):
    return f"{a / max(1, b) * 100:.1f}%"


def dist_lines(counter, total, top=None):
    out = []
    for k, v in counter.most_common(top):
        out.append(f"| {k} | {v} | {pct(v, total)} |")
    return out


def spec_book(book):
    d, geo, zlabel = load(book)
    m = d["meta"]
    ch_n = m["chapters"]
    chars, locs, evs, rels, others = (d["characters"], d["locations"], d["events"],
                                      d["relations"], d["other_events"])
    L = []
    A = L.append

    A(f"## {m['title']}（`{book}`）")
    A("")
    A(f"{m['author']} · {ch_n} 章 · {m['chars'] / 10000:.1f} 万字 · "
      f"{'架空世界' if m['kind'] == 'fictional_world' else '现实背景'} · "
      f"源：{m['source']}")
    A("")

    # ---------- ① 图规格总表 ----------
    part_edges = sum(len(e.get("participants", [])) for e in evs)
    at_edges = sum(1 for e in evs if (e.get("location") or "").strip())
    A("### ① 图规格总表")
    A("")
    A("| 类型 | 名称 | 数量 | 说明 |")
    A("|---|---|---|---|")
    A(f"| 节点 | 人物 | {len(chars)} | 有别名/阵营/分层/出场章 |")
    A(f"| 节点 | 地点 | {len(locs)} | 有类型基类/地理三态/分区 |")
    A(f"| 节点 | 事件 | {len(evs)} | 有功能基类/参与者/地点/章 |")
    A(f"| 边 | 人物—人物 关系 | {len(rels)} | rel_base 归约为有限基类 |")
    A(f"| 边 | 人物—事件 参与（派生） | {part_edges} | 由事件 participants 反推 |")
    A(f"| 边 | 事件—地点 发生在（派生） | {at_edges} | 由事件 location 反推 |")
    A(f"| 文本 | 同章上下文事件 | {len(others)} | **只有 text+chapters，无法当节点** |")
    A("")
    A(f"可查询的边合计 **{len(rels) + part_edges + at_edges}** 条"
      f"（其中派生边 {pct(part_edges + at_edges, len(rels) + part_edges + at_edges)}）。")
    A("")

    # ---------- ② 节点明细 ----------
    A("### ② 节点明细")
    A("")
    tc = Counter(p.get("tier") or "cameo" for p in chars)
    A(f"**人物** {len(chars)} 个 · 分层：" +
      " / ".join(f"{TIER_CN.get(k, k)} {v}" for k, v in tc.most_common()) +
      f" · 别名总数 {sum(len(p.get('aliases', [])) for p in chars)}")
    A("")
    fm = Counter(p.get("faction_main") or "（未标注）" for p in chars)
    A("| 主阵营 Top 8 | 人数 | 占比 |")
    A("|---|---|---|")
    L.extend(dist_lines(fm, len(chars), 8))
    A("")

    gs = Counter(geo.get(l["name"], {}).get("geo_status") or "pending" for l in locs)
    zs = Counter(zlabel.get(geo.get(l["name"], {}).get("zone"),
                      geo.get(l["name"], {}).get("zone") or "未分区") for l in locs)
    A(f"**地点** {len(locs)} 个 · 地理三态：" +
      " / ".join(f"{k} {v}" for k, v in gs.most_common()))
    A("")
    A("| 分区 | 地点数 | 占比 |")
    A("|---|---|---|")
    L.extend(dist_lines(zs, len(locs), 8))
    A("")
    A("| 地点功能基类 Top 8 | 数量 | 占比 |")
    A("|---|---|---|")
    L.extend(dist_lines(Counter(l.get("type_base") or "其他场所" for l in locs), len(locs), 8))
    A("")

    no_year = sum(1 for e in evs if not (e.get("year") or "").strip())
    A(f"**事件** {len(evs)} 件 · 年份缺失 {no_year}（{pct(no_year, len(evs))}）"
      f"→ **year 字段不可用，时间只能靠 chapters + time_hint**")
    A("")
    A("| 事件功能基类 Top 10 | 数量 | 占比 |")
    A("|---|---|---|")
    L.extend(dist_lines(Counter(e.get("type_base") or "其他" for e in evs), len(evs), 10))
    A("")

    # ---------- ③ 边明细 ----------
    A("### ③ 边明细（含可用性）")
    A("")
    rb = Counter(r.get("rel_base") or "其他关系" for r in rels)
    A(f"**人物—人物关系** {len(rels)} 条，归约到 {len(rb)} 个基类：")
    A("")
    A("| 关系基类 | 条数 | 占比 | 示例 |")
    A("|---|---|---|---|")
    for k, v in rb.most_common():
        pool = [r for r in rels if (r.get("rel_base") or "其他关系") == k]
        # 示例优先挑 rel 原文里就写着这个基类的（「师徒」配「师徒」），
        # 否则读者会看到「师徒 | 党爱萍 —其他（生活老师照护）→ 林朝夕」这种对不上的行
        ex = next((r for r in pool if k in (r.get("rel") or "")), None) or (pool[0] if pool else None)
        sample = "—"
        if ex:
            note = f"（{ex['rel_note']}）" if ex.get("rel_note") else ""
            sample = f"{ex['from']} —{ex['rel']}{note}→ {ex['to']}"
        A(f"| {k} | {v} | {pct(v, len(rels))} | {sample} |")
    A("")

    # 参与边可用性：participants 里有多少不在人物表
    names = {p["name"] for p in chars}
    bad_part = Counter()
    for e in evs:
        for p in e.get("participants", []):
            if p not in names:
                bad_part[p] += 1
    A(f"**人物—事件 参与边** {part_edges} 条。参与者不在人物表的有 "
      f"{sum(bad_part.values())} 处、{len(bad_part)} 个取值（例：" +
      "、".join(list(bad_part)[:5]) + "）—— 这些是群体称谓（全班/各校代表），"
      "查询时要按「非人物实体」排除。")
    A("")
    empty_loc = len(evs) - at_edges
    A(f"**事件—地点 发生在边** {at_edges} 条；{empty_loc} 件事件没写地点"
      f"（{pct(empty_loc, len(evs))}），做地理聚合时分子分母要说清。")
    A("")
    A(f"**同章上下文事件** {len(others)} 条：只有正文摘录和章节，没有参与者/地点字段，"
      "**不能作为节点查询**，只能做全文检索式引用。")
    A("")

    # ---------- ④ 可问的问题 ----------
    A("### ④ 按学科可问的问题")
    A("")
    A("下表是**通用问题清单**；每本书的实测值见文末汇总表（那里的数字是现算的）。")
    A("")
    A("| 学科 | 可以问 | 需要查什么 |")
    A("|---|---|---|")
    for disc, q, how in DISCIPLINES:
        A(f"| {disc} | {q} | {how} |")
    A("")
    return "\n".join(L)


def metrics(book):
    """按学科把「要问的问题」对应的图查询真跑一遍，返回实测值。

    这是本文件的核心纪律：**问题必须能落到一条查询上**。
    跑不出来（返回 None）的学科，说明数据还不够，分析时不许写。
    """
    d, geo, zlabel = load(book)
    evs, rels, locs, chars = d["events"], d["relations"], d["locations"], d["characters"]
    n = len(evs)
    rb = Counter(r.get("rel_base") or "其他关系" for r in rels)
    tb = Counter(e.get("type_base") or "其他" for e in evs)
    lb = Counter(l.get("type_base") or "其他场所" for l in locs)
    tr = Counter(p.get("tier") or "cameo" for p in chars)
    dom = rb.get("支配", 0) + rb.get("上下级", 0)
    # 生产/商业要看**地点功能基类**，不是 geo 分区 ——
    # 分区是「墙内/墙外」这种空间划分，跟经济系统不是一回事（第一版就取错了字段）
    prod = lb.get("生产处理", 0) + lb.get("商业服务", 0)
    return {
        "支配+上下级 边": f"{dom} 条（{pct(dom, len(rels))}）",
        "龙套人物占比": pct(tr.get("cameo", 0), len(chars)),
        "记忆情感事件": f"{tb.get('记忆情感', 0)} 件（{pct(tb.get('记忆情感', 0), n)}）",
        "副本任务事件": f"{tb.get('副本任务', 0)} 件（{pct(tb.get('副本任务', 0), n)}）",
        "生产+商业场所": f"{prod} 处（{pct(prod, len(locs))}）",
        "制度秩序事件": f"{tb.get('制度秩序', 0)} 件（{pct(tb.get('制度秩序', 0), n)}）",
        "成长学习事件": f"{tb.get('成长学习', 0)} 件（{pct(tb.get('成长学习', 0), n)}）",
        "事件密度": f"{n / d['meta']['chapters']:.1f} 件/章",
        "冲突+战斗": f"{tb.get('战斗', 0) + tb.get('冲突对峙', 0)} 件"
                     f"（{pct(tb.get('战斗', 0) + tb.get('冲突对峙', 0), n)}）",
    }


def main():
    docs = os.path.join(BASE, "docs")
    os.makedirs(docs, exist_ok=True)
    parts = [
        "# 拆书 KG 规格说明",
        "",
        "> 本文件由 `src/graph_spec.py` 从 `data/<book>/data.json` **现算生成**，"
        "不手写数字。数据更新后重跑一次即可。",
        "",
        "用途：做多学科视角分析时，先在这里确认「要问的问题有没有对应的边可查」，"
        "再动手写解读。没有边支撑的问题不写——那是空谈。",
        "",
        "---",
        "",
    ]
    for b in BOOKS:
        parts.append(spec_book(b))
        parts.append("")
        parts.append("---")
        parts.append("")

    # ---------- ④′ 两本书实测值 ----------
    mt = {b: metrics(b) for b in BOOKS}
    note = {
        "支配+上下级 边": "社会学/政治学：权力结构是扁平还是科层",
        "龙套人物占比": "社会学：人群是分层还是流动",
        "记忆情感事件": "心理学：情感线密集度",
        "副本任务事件": "经济学：任务-收益结构强度",
        "生产+商业场所": "经济学：有没有经济系统",
        "制度秩序事件": "政治学：规则由谁定、是否被挑战",
        "成长学习事件": "教育学：成长弧的显性程度",
        "事件密度": "叙事学：节奏快慢",
        "冲突+战斗": "叙事学：外部冲突 vs 内部冲突",
    }
    parts += [
        "## ④′ 同一把尺子量两本书（实测值，现算）",
        "",
        "| 指标 | 天才基本法 | 我在废土世界扫垃圾 | 能回答什么 |",
        "|---|---|---|---|",
    ]
    for k in mt[BOOKS[0]]:
        parts.append(f"| {k} | {mt['tiancai'][k]} | {mt['feitu'][k]} | {note.get(k, '')} |")
    parts += [
        "",
        "读法：两列的**差值**就是两本书的体裁差异，且每一格都能回到 KG 里复算。",
        "写解读时就按这个表取数，不要另起口径。",
        "",
    ]
    parts += [
        "## ⑤ 两本书共用的缺口（任何学科分析都要先声明）",
        "",
        "| 缺口 | 影响 | 应对 |",
        "|---|---|---|",
        "| 事件 `year` 字段基本为空 | 无法做公元纪年的时间序列 | 一律改用章节序号 / `time_hint` / 阶段轴 |",
        "| `participants` 含群体称谓 | 参与边数虚高、人物侧对不上 | 查询时排除非人物表取值 |",
        "| `other_events` 无实体字段 | 不能当节点，只能引用原文 | 仅作证据引用，不进统计 |",
        "| 关系基类仍有「其他」残差 | 关系图有一圈未归约边 | 报告中已脚注披露，分析时单独说明 |",
        "| 天才基本法源文本有重复章节 | 对白/事件计数可能重复计入 | 已披露 57 对；做比例类指标时留意 |",
        "",
        "## ⑥ 怎么用这份文件",
        "",
        "1. 先写「要问的问题」，再回④找对应的边；找不到就说明数据不够，**换问题或补抽取**。",
        "2. 每个结论必须能指到「节点/边 + 数量 + 占比」，和报告里「结论先行」的纪律一致。",
        "3. 数据变了就重跑 `python src/graph_spec.py`，不要手工改本文档。",
        "",
    ]
    out = os.path.join(docs, "KG_SPEC.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"[done] {out}（{os.path.getsize(out) / 1024:.1f} KB）")


if __name__ == "__main__":
    main()
