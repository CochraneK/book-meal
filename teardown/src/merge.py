# -*- coding: utf-8 -*-
"""
拆书流水线 · 阶段③ 聚合
========================
输入 data/<book>/extract_raw.json（逐章抽取记录）
输出 data/<book>/data.json（全书单一数据源）

做的事：
1. 人物归一：规范名 + 别名索引；同名跨章合并（别名/阵营/出场章并集）
2. 地点归一：按 name 合并，记录 modern/region/type 与出场章
3. 事件去重：按规范化事件名合并，参与者并集
4. 关系去重：(from, to, rel) 唯一，合并出场章
5. 端点类型判定：人物 → 地点 → 政权/机构 → 其他（供报告打徽标）
6. 人工层可插拔：manual_corrections.json（人物合并/地点修正/关系翻转）

设计原则：宁可留空不猜；未定位地点如实标 pending，不硬填坐标。
"""

import json
import os
import re
import sys
from collections import defaultdict

from type_reduce import event_base_of, place_base_of

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ORG_SUFFIX = ("公司", "基金会", "大学", "学院", "中学", "小学", "部", "司", "局",
              "院", "校", "队", "帮", "党", "政府", "中心", "机构", "联盟", "协会",
              "军团", "军队", "军校", "警局", "医院", "银行", "酒店", "饭店")
REGIME_WORDS = ("墙内", "墙外", "末日", "废土", "人类", "清洁工", "五等公民", "公民")


def norm(s):
    return re.sub(r"[\s\u3000]+", "", (s or "")).strip()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 关系归约：把自由发挥的关系描述收敛成有限基类
# ---------------------------------------------------------------------------
# 抽取时 agent 写的 rel 形如「上下级（队长/队员）」「队友（断网后仍等待其发现）」，
# 基类其实存在，但被括号备注稀释：废土 1606 条关系产生了 1396 种不同字符串，
# 结果关系图每条边都是独有标签，无法聚合、无法统计。
# 处理原则：基类作为「结论」，括号内容保留为「证据」（rel_note），不丢信息。
REL_BASE_MAP = [
    ("亲属", ("父女", "父子", "母女", "母子", "兄弟", "姐妹", "兄妹", "姐弟", "夫妻",
              "配偶", "祖父", "祖母", "外祖", "爷孙", "亲子", "养父", "养母", "养女",
              "养子", "收养", "领养", "拟领养", "拟收养", "血缘", "家族", "亲戚", "亲属",
              "叔侄", "舅甥", "姑侄", "继母", "继父")),
    ("师徒", ("师徒", "师生", "老师", "学生", "弟子", "门徒", "带教", "教导", "学长",
              "学姐", "学弟", "学妹", "同窗", "同学", "师兄", "师姐", "师弟", "师妹",
              "指导", "点评", "答疑", "学习对象", "辅导", "授课")),
    ("上下级", ("上下级", "上级", "下级", "队长/队员", "队长与队员", "领导", "指挥",
                "隶属", "管辖", "长官", "部属", "下属", "队长", "带领", "带队", "属下")),
    ("队友", ("队友", "队员", "同队", "战友", "搭档", "同伴", "同行", "伙伴", "战场伙伴")),
    ("同事", ("同事", "同僚", "共事")),
    ("敌对", ("敌对", "敌人", "仇敌", "仇人", "死敌", "宿敌", "对立", "追杀", "敌视",
              "加害", "杀害", "凶手", "背叛", "叛徒", "囚禁者", "仇家")),
    # 权力关系：造物主/宿主/操控者——废土里大量存在，且与「敌对」不同
    # （不是恨，而是「谁能支配谁」），单独成类才能读出世界观结构。
    ("支配", ("操控", "支配", "驱使", "控制", "豢养", "奴役", "献祭", "造物主", "造物",
              "主宰", "封印者", "囚禁", "支配者", "利用")),
    ("合作", ("合作", "协作", "联盟", "结盟", "同盟", "搭档关系", "互利", "同伙", "共犯",
              "合伙人")),
    ("爱慕", ("爱慕", "喜欢", "恋人", "情侣", "追求", "单恋", "暗恋", "相亲", "婚约")),
    ("同源", ("同源", "复制", "分身", "同体", "本体与复制", "克隆", "复制体", "同貌",
              "另一个自己", "自我")),
    ("寄生", ("寄生", "宿主", "寄居", "附身", "侵占", "夺舍")),
    ("交易", ("交易", "买卖", "雇佣", "委托", "雇主", "客户", "买卖关系", "契约")),
    ("旧识", ("旧识", "相识", "认识", "故人", "熟人", "旧交", "前辈")),
    ("朋友", ("朋友", "好友", "友人", "闺蜜", "知己")),
    ("救助", ("救助", "救命", "保护", "庇护", "守护", "抚养", "养育", "救治", "监护",
              "照顾", "照护", "医患", "收养", "收养人", "救助者", "被救者", "救援者",
              "抚养人", "照看", "护工", "院长", "院童", "阿姨")),
    ("融合", ("融合", "吞噬", "吞食", "吸收", "同化", "附体")),
]
REL_FALLBACK = "其他关系"


def rel_base_of(rel):
    """把自由文本关系拆成（基类, 括号备注）。

    括号里的备注不只是「补充说明」，很多时候**真关系写在括号里**：
    「其他（拟收养）」「其他（院长与院童，抚养照护）」「其他票（救援者/被救者）」。
    所以头词判定失败时要拿备注再判一次，否则这些会白白落进「其他关系」。
    """
    rel = (rel or "").strip()
    m = re.match(r"^([^（(]+)[（(](.*)[)）]\s*$", rel)
    head, note = (m.group(1), m.group(2).strip()) if m else (rel, "")

    def match(text):
        parts = [p.strip() for p in re.split(r"[/、,，;；]", text) if p.strip()]
        for p in parts or [text]:
            for base, kws in REL_BASE_MAP:
                if any(k == p or k in p for k in kws):
                    return base
        return ""

    # 第一轮：头词。多标签（「队长/队员」）逐个试，取第一个命中
    hit = match(head)
    if hit:
        return hit, note
    # 第二轮：头词是「其他 / 空 / 自造词」时，用括号备注兜底
    if note and (head in ("其他", "", "关系", "其他关系") or not hit):
        hit = match(note)
        if hit:
            return hit, note
    return REL_FALLBACK, note


def tier_of(n_chapters):
    """实体分层：核心 / 主要 / 次要 / 一次性。用于视图默认裁剪。"""
    if n_chapters >= 20:
        return "core"
    if n_chapters >= 5:
        return "major"
    if n_chapters >= 2:
        return "minor"
    return "cameo"


def build(book_id):
    cfg = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
    book = cfg["books"][book_id]
    ddir = os.path.join(BASE, "data", book_id)
    raw = load_json(os.path.join(ddir, "extract_raw.json"), [])
    chapters = load_json(os.path.join(ddir, "chapters.json"), [])
    manual = load_json(os.path.join(ddir, "manual_corrections.json"), {})

    if not raw:
        raise RuntimeError(f"{book_id}: extract_raw.json 为空，先完成抽取")

    ch_index = {c["key"]: c for c in chapters}
    ch_meta = [{"key": c["key"], "index": c["chapter_index"],
                # book_no = 书中真实章号（由 heading 解析，见 normalize_chapters.py）；
                # 与内部 index 可能不同，展示层一律用 book_no
                "no": c.get("book_no", c["chapter_index"]),
                "title": c["chapter_title"], "chars": c["chars"]}
               for c in sorted(chapters, key=lambda x: x["chapter_index"])]

    # 先统计每个字符串作为「规范名」出现的次数。
    # 用途：阻止「弱名吞并强名」——曾有 agent 把「祝宁」写成「初代祝宁」的
    # 别名，导致女主角 426 章的记录全被并入只有 9 章的小条目。
    name_freq = {}
    for rec in raw:
        for c in rec.get("characters", []) or []:
            nm = norm(c.get("name", ""))
            if nm:
                name_freq[nm] = name_freq.get(nm, 0) + 1

    # ---------- 人工层：人物合并（别名归并） ----------
    alias_to_canonical = {}
    for m in manual.get("character_merges", []):  # {"from": "别名或错名", "to": "规范名"}
        alias_to_canonical[norm(m["from"])] = norm(m["to"])

    # 强制别名：抽取记录里自造的别名可能张冠李戴（例如把「狞猫」挂到山猫名下，
    # 实际「狞猫」是祝宁的代号）。这里给出最高优先级的权威映射。
    forced_alias = {}
    for x in manual.get("alias_adds", []):     # {"person": "祝宁", "alias": "狞猫"}
        forced_alias[norm(x["alias"])] = norm(x["person"])
    # 要剔除的错误别名
    drop_global = {norm(x) for x in manual.get("alias_drops_global", [])}
    drop_pairs = {(norm(d["person"]), norm(d["alias"]))
                  for d in manual.get("alias_drops", [])}

    def canon_person(name):
        n = norm(name)
        if n in forced_alias:
            return forced_alias[n]
        return alias_to_canonical.get(n, n)

    # ---------- 人物 ----------
    persons = {}  # name -> record
    for rec in raw:
        k = rec.get("key", "")
        for c in rec.get("characters", []):
            name = canon_person(c.get("name", ""))
            if not name:
                continue
            p = persons.setdefault(name, {
                "id": f"person:{name}", "name": name, "aliases": set(),
                "factions": set(), "fcount": {}, "role": "", "chapters": set(),
                "mentions": 0})
            for a in c.get("aliases", []) or []:
                a = norm(a)
                if not a or a == name:
                    continue
                # 剔除明显不是人名的通用词，以及被明确判为误标的组合
                if a in drop_global or (name, a) in drop_pairs:
                    continue
                if a in forced_alias:
                    p["aliases"].add(a)
                    continue          # 强制映射优先，不许被记录覆盖
                # 弱名不得吞并强名：别名本身若更常作为独立规范名出现，就不兼并
                if name_freq.get(a, 0) > name_freq.get(name, 0):
                    continue
                p["aliases"].add(a)
                alias_to_canonical.setdefault(a, name)
            f = norm(c.get("faction", ""))
            if f:
                p["factions"].add(f)
                # 记频次：抽取时每章都写当章身份，导致一个角色挂几十个阵营字符串。
                # 展示层需要「主阵营」（出现最多的那个），否则列表里就是「等 34 项」。
                p["fcount"][f] = p["fcount"].get(f, 0) + 1
            if not p["role"] and c.get("role"):
                p["role"] = c["role"]
            p["chapters"].add(k)
            p["mentions"] += 1
    # 人工补录人物
    for p in manual.get("persons", []):
        name = norm(p.get("name", ""))
        if name and name not in persons:
            persons[name] = {"id": f"person:{name}", "name": name, "aliases": set(),
                             "factions": {norm(p.get("faction", ""))} - {""},
                             "fcount": {}, "role": p.get("role", ""),
                             "chapters": set(), "mentions": 0}

    # 应用强制别名：若该别名已被某个 agent 单独建成人物条目，合并进目标人物
    for alias, target in forced_alias.items():
        if alias in persons and alias != target:
            src = persons.pop(alias)
            if target not in persons:
                src["name"] = target
                src["id"] = f"person:{target}"
                src["aliases"] |= {alias}
                persons[target] = src
            else:
                dst = persons[target]
                dst["aliases"] |= src["aliases"] | {alias}
                dst["factions"] |= src["factions"]
                for fk, fv in src.get("fcount", {}).items():
                    dst["fcount"][fk] = dst["fcount"].get(fk, 0) + fv
                dst["chapters"] |= src["chapters"]
                dst["mentions"] += src["mentions"]
                if not dst["role"]:
                    dst["role"] = src["role"]
        elif target in persons:
            persons[target]["aliases"].add(alias)

    person_names = set(persons)

    # ---------- 地点 ----------
    loc_fixes = {norm(k): v for k, v in manual.get("location_fixes", {}).items()}
    locations = {}
    for rec in raw:
        k = rec.get("key", "")
        for l in rec.get("locations", []):
            name = norm(l.get("name", ""))
            if not name:
                continue
            fix = loc_fixes.get(name, {})
            name = norm(fix.get("name", name))
            loc = locations.setdefault(name, {
                "id": f"place:{name}", "name": name, "modern": "", "region": "",
                "type": "", "chapters": set(), "mentions": 0})
            m = norm(l.get("modern", "")) or norm(fix.get("modern", ""))
            if m and not loc["modern"]:
                loc["modern"] = m
            r = norm(l.get("region", "")) or norm(fix.get("region", ""))
            if r and not loc["region"]:
                loc["region"] = r
            t = norm(l.get("type", "")) or norm(fix.get("type", ""))
            if t and not loc["type"]:
                loc["type"] = t
            loc["chapters"].add(k)
            loc["mentions"] += 1
    location_names = set(locations)

    # ---------- 事件 ----------
    ev_fixes = {norm(k): v for k, v in manual.get("event_fixes", {}).items()}
    events = {}
    for rec in raw:
        k = rec.get("key", "")
        for e in rec.get("events", []):
            name = norm(e.get("name", ""))
            if not name:
                continue
            fix = ev_fixes.get(name, {})
            name = norm(fix.get("name", name))
            ev = events.setdefault(name, {
                "id": f"event:{name}", "name": name, "type": e.get("type", "") or fix.get("type", ""),
                "participants": [], "location": e.get("location", "") or fix.get("location", ""),
                "year": e.get("year", "") or fix.get("year", ""),
                "note": e.get("note", ""), "chapters": set(), "time_hint": rec.get("time", "")})
            for ptc in e.get("participants", []) or []:
                ptc = canon_person(ptc)
                if ptc and ptc not in ev["participants"]:
                    ev["participants"].append(ptc)
            if e.get("note") and not ev["note"]:
                ev["note"] = e["note"]
            ev["chapters"].add(k)
    for e in manual.get("event_years", []):
        n = norm(e.get("name", ""))
        if n in events and e.get("year"):
            events[n]["year"] = e["year"]

    # ---------- 关系 ----------
    def endpoint_kind(name):
        if name in person_names:
            return "person"
        if name in location_names:
            return "place"
        if any(w in name for w in REGIME_WORDS):
            return "regime"
        if name.endswith(ORG_SUFFIX) or "军" in name:
            return "org"
        return "other"

    relations = {}
    for rec in raw:
        k = rec.get("key", "")
        for r in rec.get("relations", []):
            a, b = canon_person(r.get("from", "")), canon_person(r.get("to", ""))
            if not a or not b or a == b:
                continue
            rel = norm(r.get("rel", "")) or "相关"
            rbase, rnote = rel_base_of(rel)
            key = (a, b, rel)
            rl = relations.setdefault(key, {
                "id": "relation:" + re.sub(r"\W", "", f"{a}|{b}|{rel}")[:40],
                "from": a, "to": b, "rel": rel,
                "rel_base": rbase, "rel_note": rnote, "chapters": set()})
            rl["chapters"].add(k)
    for f in manual.get("relation_fixes", {}).get("flip", []):
        a, b, rel = norm(f.get("from", "")), norm(f.get("to", "")), norm(f.get("rel", ""))
        if (a, b, rel) in relations:
            rl = relations.pop((a, b, rel))
            rl["from"], rl["to"] = b, a
            relations[(b, a, rel)] = rl
    for add in manual.get("relations", []):
        a, b = canon_person(add.get("from", "")), canon_person(add.get("to", ""))
        rel = norm(add.get("rel", ""))
        if a and b and a != b and rel and (a, b, rel) not in relations:
            relations[(a, b, rel)] = {"id": "relation:" + re.sub(r"\W", "", f"{a}|{b}|{rel}")[:40],
                                      "from": a, "to": b, "rel": rel, "chapters": set(),
                                      "manual": True}

    # ---------- 同章上下文事件（不计入参与） ----------
    other_events = defaultdict(set)
    for rec in raw:
        for s in rec.get("other_events", []) or []:
            s = norm(s)
            if s:
                other_events[s].add(rec.get("key", ""))

    # ---------- 别名索引 ----------
    alias_index = {}
    for p in persons.values():
        for a in p["aliases"]:
            alias_index[a] = p["name"]

    # ---------- 端点类型 ----------
    for rl in relations.values():
        rl["from_kind"] = endpoint_kind(rl["from"])
        rl["to_kind"] = endpoint_kind(rl["to"])

    data = {
        "meta": {
            "book": book_id, "title": book["title"], "author": book["author"],
            "kind": book["kind"], "desc": book.get("desc", ""),
            "chapters": len(ch_meta),
            "chars": sum(c["chars"] for c in ch_meta),
            "extracted_chapters": len(raw),
            "source": "书中抽取",
            "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        },
        "chapters": ch_meta,
        "characters": [serialize_person(p) for p in sorted(persons.values(),
                                                           key=lambda x: -len(x["chapters"]))],
        "locations": [serialize_loc(l) for l in sorted(locations.values(),
                                                       key=lambda x: -len(x["chapters"]))],
        "events": [serialize_event(e) for e in sorted(events.values(),
                                                      key=lambda x: (x["year"] == "", x["year"]))],
        "relations": [serialize_rel(r) for r in sorted(relations.values(),
                                                       key=lambda x: (x["from"], x["to"]))],
        "other_events": [{"text": t, "chapters": sorted(v)} for t, v in
                         sorted(other_events.items(), key=lambda kv: -len(kv[1]))],
        "alias_index": alias_index,
    }

    out = os.path.join(ddir, "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"[done] {book['title']}（{book_id}）聚合完成")
    print(f"       章节 {data['meta']['chapters']}（已抽 {data['meta']['extracted_chapters']}）"
          f" 人物 {len(data['characters'])} 地点 {len(data['locations'])} "
          f"事件 {len(data['events'])} 关系 {len(data['relations'])} "
          f"同章事件 {len(data['other_events'])}")
    return data


def serialize_person(p):
    fc = p.get("fcount") or {}
    main = max(fc, key=fc.get) if fc else ""
    return {"id": p["id"], "name": p["name"], "aliases": sorted(p["aliases"]),
            "factions": sorted(p["factions"]), "faction_main": main, "role": p["role"],
            "chapters": sorted(p["chapters"]), "mentions": p["mentions"],
            "tier": tier_of(len(p["chapters"]))}


def serialize_loc(l):
    return {"id": l["id"], "name": l["name"], "modern": l["modern"],
            "region": l["region"], "type": l["type"],
            # type_base = 归约后的功能基类（居住/据点/交通…），type 原样保留作证据。
            # 原始类型在「室内/设施/建筑」之间摇摆，同一地点会被不同 agent 标成
            # 不同类，直接拿来排行没有解释力——见 type_reduce.py 的说明。
            "type_base": place_base_of(l["name"], l["type"])[0],
            "chapters": sorted(l["chapters"]), "mentions": l["mentions"],
            "tier": tier_of(len(l["chapters"])),
            "geo_status": "pending"}


def serialize_event(e):
    return {"id": e["id"], "name": e["name"], "type": e["type"],
            # 叙事功能基类：战斗冲突/情报对话/探索发现…（type 保留原文）
            "type_base": event_base_of(e["name"], e["type"])[0],
            "participants": e["participants"], "location": e["location"],
            "year": e["year"], "note": e["note"],
            "time_hint": e["time_hint"], "chapters": sorted(e["chapters"])}


def serialize_rel(r):
    return {"id": r["id"], "from": r["from"], "to": r["to"], "rel": r["rel"],
            "rel_base": r.get("rel_base", ""), "rel_note": r.get("rel_note", ""),
            "from_kind": r["from_kind"], "to_kind": r["to_kind"],
            "chapters": sorted(r["chapters"]), "manual": r.get("manual", False)}


def main():
    books = sys.argv[1:] or json.load(open(os.path.join(BASE, "config.json"),
                                           encoding="utf-8"))["books"].keys()
    for b in books:
        build(b)


if __name__ == "__main__":
    main()
