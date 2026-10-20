import json, sys
sys.path.insert(0, r"d:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md
d = json.load(open(r"d:\2026\WB项目\明朝\.dump\_stats_anthropology.json", encoding="utf-8"))
out = ["keys: " + " ".join(sorted(d.keys()))]
c = d.get("corpus") or {}
out.append("corpus keys: " + " ".join(sorted(c.keys())))
be = c.get("book_evidence") or []
out.append("book_evidence n=%d" % len(be))
for i, e in enumerate(be):
    out.append("[%d] %s" % (i, json.dumps(e, ensure_ascii=False)[:400]))
open(r"d:\2026\WB项目\明朝\.dump\_ev3.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
