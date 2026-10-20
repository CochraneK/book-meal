import os, time, json, glob
base = r"d:\2026\WB项目\明朝\papers_pilot"
out = []
def L(s):
    out.append(s)

def walk(rel):
    p = os.path.join(base, rel)
    if not os.path.isdir(p):
        L("MISSING " + rel); return
    for f in sorted(os.listdir(p)):
        fp = os.path.join(p, f)
        if os.path.isfile(fp):
            L("%s | %d B | %s" % (rel + "/" + f, os.path.getsize(fp),
                                  time.strftime("%H:%M", time.localtime(os.path.getmtime(fp)))))

for rel in ["anthropology", "anthropology/paper", "anthropology/paper/sections",
            "anthropology/paper/figures", "anthropology/paper/out"]:
    walk(rel)

L("--- systems ---")
for rel in ["systems", "systems/paper", "systems/paper/sections", "systems/paper/figures"]:
    walk(rel)

L("--- dump stats ---")
for f in ["_stats_anthropology.json", "_stats_systems.json"]:
    fp = os.path.join(r"d:\2026\WB项目\明朝\.dump", f)
    if os.path.exists(fp):
        d = json.load(open(fp, encoding="utf-8"))
        L("%s %d B mtime=%s keys=%s" % (f, os.path.getsize(fp),
          time.strftime("%H:%M", time.localtime(os.path.getmtime(fp))), sorted(d.keys())))
    else:
        L("%s MISSING" % f)

open(r"d:\2026\WB项目\明朝\.dump\_st3.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
