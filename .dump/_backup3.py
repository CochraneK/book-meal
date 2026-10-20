import os, shutil, time
base = r"d:\2026\WB项目\明朝\papers_pilot"
tag = time.strftime("%H%M%S")
for pid in ("anthropology", "systems"):
    src = os.path.join(base, pid, "paper")
    dst = os.path.join(r"d:\2026\WB项目\明朝\.dump", "_bak_gp3_%s_%s" % (pid, tag))
    n = 0
    for root, dirs, files in os.walk(src):
        for f in files:
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, src)
            out = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(fp, out)
            n += 1
    print("backed", pid, n, "files ->", os.path.basename(dst))
