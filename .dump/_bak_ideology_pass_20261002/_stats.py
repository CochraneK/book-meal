# -*- coding: utf-8 -*-
"""ideology 篇统计底稿：思想语汇、关系构成与事件时间序列。"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

PID = "ideology"
TERMS = [
    "心学", "致良知", "知行合一", "王守仁", "理学", "讲学", "书院",
    "李贽", "存天理", "天理", "良知",
]
# 由人物 faction/role 与结构化关系、事件中的心学/王学/讲学/书院标记确定。
THOUGHT_GROUP = [
    "王守仁", "聂豹", "徐阶", "王艮", "王畿", "钱德洪",
    "何心隐", "李贽", "顾宪成", "高攀龙",
]
POWER_GROUP = ["张居正", "严嵩"]
ANCHORS = ["王守仁", "徐阶", "顾宪成", "高攀龙", "张居正", "严嵩"]
EVENT_KWS = ["心学", "知行", "格物", "学派", "论道", "书院", "讲学"]


def pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


def comp(rows):
    c = Counter((r.get("category") or "未分类") for r in rows)
    n = len(rows)
    return {
        "n": n,
        "categories": [
            {"name": k, "n": v, "pct": pct(v, n)}
            for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "teacher_peer_n": c.get("师生同门", 0),
        "teacher_peer_pct": pct(c.get("师生同门", 0), n),
        "power_relation_n": sum(c.get(k, 0) for k in ["君臣从属", "政治攻讦", "敌对冲突", "同盟友党"]),
        "power_relation_pct": pct(sum(c.get(k, 0) for k in ["君臣从属", "政治攻讦", "敌对冲突", "同盟友党"]), n),
    }


def incident(name_or_group, explicit_only=False):
    names = {name_or_group} if isinstance(name_or_group, str) else set(name_or_group)
    rows = [r for r in md.relations() if r.get("from") in names or r.get("to") in names]
    if explicit_only:
        rows = [r for r in rows if r.get("chapter") != "推导"]
    return rows


def main():
    deg = md.degree_map()
    hits = {t: md.hit_text(t) for t in TERMS}

    anchor_stats = {}
    for name in ANCHORS:
        anchor_stats[name] = {
            "degree": deg.get(name, 0),
            "all_incident": comp(incident(name)),
            "explicit_incident": comp(incident(name, explicit_only=True)),
        }

    thought_all = incident(THOUGHT_GROUP)
    thought_explicit = incident(THOUGHT_GROUP, explicit_only=True)
    power_all = incident(POWER_GROUP)
    power_explicit = incident(POWER_GROUP, explicit_only=True)

    ideology_events = []
    by_year = Counter()
    by_category = Counter()
    for e in md.events():
        blob = " ".join(str(e.get(k) or "") for k in ("name", "type"))
        if any(k in blob for k in EVENT_KWS):
            y = e.get("year")
            if isinstance(y, int):
                by_year[y] += 1
            by_category[e.get("category") or "未分类"] += 1
            ideology_events.append({
                "name": e.get("name"), "year": y, "category": e.get("category"),
                "participants": e.get("participants") or [], "chapters": e.get("chapters") or [],
            })

    windows = [(1480, 1507), (1508, 1528), (1529, 1578), (1579, 1600)]
    event_windows = []
    for lo, hi in windows:
        rows = [e for e in ideology_events if isinstance(e.get("year"), int) and lo <= e["year"] <= hi]
        event_windows.append({"label": f"{lo}--{hi}", "n": len(rows)})

    chaps = sorted({c for e in md.events() for c in (e.get("chapters") or [])})

    # 主结果口径（正文里出现的小数全部取自这里）
    peak = max(event_windows, key=lambda w: w["n"])
    stats = {
        "counts": {
            "characters": len(md.characters()), "events": len(md.events()),
            "relations": len(md.relations()), "locations": len(md.locations()),
            "chapters": len(chaps),
        },
        "text_hits": hits,
        "relation_categories": md.relation_categories(),
        "teacher_peer_global": {
            "n": next(x["n"] for x in md.relation_categories() if x["name"] == "师生同门"),
            "pct": next(x["pct"] for x in md.relation_categories() if x["name"] == "师生同门"),
        },
        "groups": {
            "thought_names": THOUGHT_GROUP,
            "power_names": POWER_GROUP,
            "thought_all": comp(thought_all),
            "thought_explicit": comp(thought_explicit),
            "power_all": comp(power_all),
            "power_explicit": comp(power_explicit),
        },
        "anchors": anchor_stats,
        "ideology_events": ideology_events,
        "ideology_events_n": len(ideology_events),
        "ideology_events_by_year": [
            {"year": y, "n": n} for y, n in sorted(by_year.items())
        ],
        "ideology_events_by_category": [
            {"name": k, "n": v, "pct": pct(v, len(ideology_events))}
            for k, v in sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "ideology_event_windows": event_windows,
        "peak_window": {
            "label": peak["label"], "n": peak["n"],
            "pct": pct(peak["n"], len(ideology_events)),
            "denominator": len(ideology_events),
        },
        "verified_book_evidence": {
            "知行合一": hits["知行合一"],
            "致良知": hits["致良知"],
            "讲学": hits["讲学"],
            "书院": hits["书院"],
        },
        "limitations": {
            "text_is_narrative_mentions_not_philosophical_treatises": True,
            "derived_edges_excluded_in_explicit_robustness": True,
            "framework_not_direct_measure": "突围/收编仅为解释框架；替代量为关系类别构成与事件时间序列",
        },
    }
    path = md.write_stats(PID, stats)
    print(path)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
