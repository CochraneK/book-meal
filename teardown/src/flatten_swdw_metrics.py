# -*- coding: utf-8 -*-
"""给 swdw 的 data.json 补顶层 characters/events/relations 等键，
仅供 generate_report.build_portal 的 metrics() 计数用（只取 len）。
不改变原 D 的世界级结构；build() 因 standalone 跳过，不会用到这些键的结构。"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(BASE, "data", "swdw", "data.json")
D = json.load(open(p, encoding="utf-8"))

characters, events, relations = [], [], []
for w in D.get("worlds", []):
    wname = w.get("full_title") or w.get("name")
    for c in w.get("characters", []):
        characters.append({
            "id": "c%d" % (len(characters) + 1),
            "name": c.get("name"),
            "aliases": [], "factions": [w.get("name")], "faction_main": w.get("name"),
            "tier": "core" if c.get("role", "").find("主角") >= 0 else "major",
            "role": c.get("role", ""),
            "chapters": ["swdw-c%d" % i for i in range(w.get("chapter_start", 1), w.get("chapter_end", 1) + 1)],
            "mentions": 0,
        })
    for st in w.get("plot", []):
        events.append({"id": "e%d" % (len(events) + 1), "name": st.get("stage", ""),
                       "type": "情节阶段", "type_base": "情节阶段", "participants": [],
                       "location": "", "year": "", "note": "", "time_hint": "",
                       "chapters": ["swdw-c%d" % i for i in range(w.get("chapter_start", 1), w.get("chapter_end", 1) + 1)]})
    for dth in w.get("deaths", []):
        events.append({"id": "e%d" % (len(events) + 1), "name": "死亡：" + dth.get("name", ""),
                       "type": "角色死亡", "type_base": "角色死亡", "participants": [dth.get("name")],
                       "location": "", "year": "", "note": "第%d章" % dth.get("chapter", 0), "time_hint": "",
                       "chapters": ["swdw-c%d" % dth.get("chapter", 0)]})
    # 真实关系：观测员余黎 评估 该世界；主角 身处 该世界
    relations.append({"id": "r%d" % (len(relations) + 1), "from": "观测员余黎", "to": wname,
                      "rel": "观测/评估", "rel_base": "观测/评估", "rel_note": "",
                      "from_kind": "观测者", "to_kind": "小说世界",
                      "chapters": ["swdw-c%d" % i for i in range(w.get("chapter_start", 1), w.get("chapter_end", 1) + 1)]})
    if w.get("protagonist", {}).get("name"):
        relations.append({"id": "r%d" % (len(relations) + 1), "from": w["protagonist"]["name"], "to": wname,
                          "rel": "主角/身处", "rel_base": "主角/身处", "rel_note": "",
                          "from_kind": "角色", "to_kind": "小说世界",
                          "chapters": ["swdw-c%d" % i for i in range(w.get("chapter_start", 1), w.get("chapter_end", 1) + 1)]})

chapters = [{"index": c["n"], "key": "swdw-c%d" % c["n"], "no": c["n"], "title": c["t"], "chars": c["c"]}
            for c in D.get("chapter_index", [])]

D["characters"] = characters
D["events"] = events
D["other_events"] = []
D["relations"] = relations
D["locations"] = []
D["alias_index"] = {}
D["chapters"] = chapters

json.dump(D, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("characters=%d events=%d relations=%d chapters=%d"
      % (len(characters), len(events), len(relations), len(chapters)))
print("OK ->", p)
