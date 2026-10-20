import sys, json
sys.stdout.reconfigure(encoding="utf-8")
P = r"d:\2026\WB项目\明朝\.dump\_refcheck_anthropology.json"
d = json.load(open(P, encoding="utf-8"))
for it in d:
    if it.get("status") == "VERIFIED":
        continue
    print("=== %s  (%s)" % (it["key"], it["status"]))
    for m in it.get("top_matches", [])[:3]:
        print("   overlap=%.2f year=%s author_ok=%s type=%s doi=%s"
              % (m.get("title_overlap", 0), m.get("matched_year"),
                 m.get("author_ok"), m.get("matched_type"), m.get("doi")))
        print("      T:", m.get("matched_title"))
        print("      A:", m.get("matched_author"))
