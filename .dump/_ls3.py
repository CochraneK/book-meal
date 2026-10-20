import os, time
base = r"d:\2026\WB项目\明朝\papers_pilot"
for pid in ("anthropology", "systems"):
    p = os.path.join(base, pid)
    print("=" * 20, pid, os.path.isdir(p))
    for root, dirs, files in os.walk(p):
        dirs.sort()
        for f in sorted(files):
            fp = os.path.join(root, f)
            try:
                sz = os.path.getsize(fp)
                mt = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(fp)))
            except Exception:
                sz, mt = -1, "?"
            print(f"{mt} {sz:>8} {os.path.relpath(fp, p)}")
print("=" * 20, ".dump")
d = r"d:\2026\WB项目\明朝\.dump"
for f in sorted(os.listdir(d)):
    fp = os.path.join(d, f)
    if os.path.isfile(fp):
        print(time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(fp))), os.path.getsize(fp), f)
