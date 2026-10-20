import json
d = json.load(open(r"d:\2026\WB项目\明朝\.dump\_refcheck_anthropology.json", encoding="utf-8"))
items = d if isinstance(d, list) else d.get("items", d.get("results", []))
out = []
for it in items:
    key = it.get("key") or it.get("ref_key")
    if key in ("albert2000", "newman2003", "watson1982"):
        out.append("=== %s status=%s" % (key, it.get("status")))
        out.append("   plan: %s" % json.dumps({k: v for k, v in it.items() if k in ("title", "author", "year", "venue")}, ensure_ascii=False))
        for m in (it.get("top_matches") or [])[:4]:
            out.append("   match: %s" % json.dumps(m, ensure_ascii=False)[:600])
open(r"d:\2026\WB项目\明朝\.dump\_refx2.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
