import os, sys, json
out = []
out.append("PYEXE=%r" % sys.executable)
out.append("CWD=%s" % os.getcwd())
base = "papers_pilot/info"
rows = []
for r, d, f in os.walk(base):
    for n in sorted(f):
        p = os.path.join(r, n)
        try:
            m = os.path.getsize(p)
        except OSError:
            m = -1
        rows.append((m, p.replace("\\", "/")))
rows.sort()
for m, p in rows:
    out.append("%8d %s" % (m, p))
open(".dump/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
print(len(rows))
