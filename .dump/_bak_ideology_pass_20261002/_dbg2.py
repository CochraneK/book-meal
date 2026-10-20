# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\2026\WB项目\明朝"
d = json.load(open(os.path.join(ROOT, ".dump", "_stats_ideology.json"), encoding="utf-8"))
out = []
out.append("keys: %s" % list(d.keys()))
out.append("top keys sample: %s" % json.dumps({k: (v if not isinstance(v, (list, dict)) else "<%s>" % type(v).__name__) for k, v in d.items()}, ensure_ascii=False))
out.append("rc: %s" % json.dumps(d.get("relation_categories"), ensure_ascii=False))
out.append("groups: %s" % json.dumps(d.get("groups"), ensure_ascii=False)[:3000])
with open(os.path.join(os.path.dirname(__file__), "_dbg2.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
