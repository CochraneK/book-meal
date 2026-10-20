import os, re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"d:\2026\WB项目\明朝\papers_pilot"
for pid in ("anthropology", "systems"):
    p = os.path.join(ROOT, pid, "paper")
    keys = {}
    for f in sorted(os.listdir(os.path.join(p, "sections"))) + ["main.tex"]:
        fp = os.path.join(p, "sections", f)
        if not os.path.exists(fp):
            fp = os.path.join(p, f)
        t = open(fp, encoding="utf-8").read()
        for m in re.finditer(r"\\cite[tp]?\{([^}]*)\}", t):
            for k in m.group(1).split(","):
                k = k.strip()
                if k:
                    keys.setdefault(k, []).append(f)
    print("===", pid, len(keys), "distinct cite keys")
    for k in sorted(keys):
        print("  ", k, keys[k])
