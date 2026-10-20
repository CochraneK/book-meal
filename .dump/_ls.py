import os, time
base = r"D:\2026\WB项目\明朝\papers_pilot"
rows = []
for pid in ("anthropology", "systems"):
    root = os.path.join(base, pid)
    for r, d, f in os.walk(root):
        for x in f:
            p = os.path.join(r, x)
            try:
                t = time.strftime("%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p)))
            except Exception:
                t = "?"
            rows.append((t, os.path.getsize(p), p.replace(base, "")))
rows.sort()
for t, s, p in rows:
    print(t, s, p)
