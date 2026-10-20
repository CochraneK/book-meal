import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for r in d:
    print("==", r["status"], r["key"])
    for m in (r["top_matches"] or [])[:2]:
        print("   ", m.get("matched_year"), m.get("matched_author"), "|",
              (m.get("matched_title") or "")[:70], "| ov=", m.get("title_overlap"),
              "yd=", m.get("year_diff"), "auth=", m.get("author_ok"))
