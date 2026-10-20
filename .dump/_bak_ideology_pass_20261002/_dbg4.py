# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\2026\WB项目\明朝"
d = json.load(open(os.path.join(ROOT, ".dump", "_stats_ideology.json"), encoding="utf-8"))
out = []
for k in ("counts", "text_hits", "teacher_peer_global", "verified_book_evidence"):
    out.append("%s = %s" % (k, json.dumps(d.get(k), ensure_ascii=False)))
for g in ("thought_all", "thought_explicit", "power_all", "power_explicit"):
    out.append("%s = %s" % (g, json.dumps(d.get("groups", {}).get(g), ensure_ascii=False)))
for a, v in (d.get("anchors") or {}).items():
    out.append("anchor %s = %s" % (a, json.dumps(v, ensure_ascii=False)))
out.append("events_n = %s / %s" % (d.get("ideology_events_n"), json.dumps(d.get("ideology_events_by_category"), ensure_ascii=False)))
out.append("windows = %s" % json.dumps(d.get("ideology_event_windows"), ensure_ascii=False))
out.append("events = %s" % json.dumps(d.get("ideology_events"), ensure_ascii=False)[:2000])
with open(os.path.join(os.path.dirname(__file__), "_dbg4.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
