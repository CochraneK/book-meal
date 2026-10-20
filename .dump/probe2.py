import os, time, datetime
base = "papers_pilot"
rows = []
for r, d, f in os.walk(base):
    if "_prev_bak" in r or "_generic_bak" in r or "_mine_ready_to_drop" in r:
        continue
    for n in f:
        p = os.path.join(r, n)
        if n.endswith((".pdf", ".png", ".aux", ".log", ".out", ".bbl", ".blg")):
            continue
        try:
            mt = os.path.getmtime(p)
        except OSError:
            continue
        rows.append((mt, p.replace("\\", "/")))
rows.sort()
out = []
for mt, p in rows:
    out.append(datetime.datetime.fromtimestamp(mt).strftime("%m-%d %H:%M:%S") + "  " + p)
open(".dump/_probe2.txt", "w", encoding="utf-8").write("\n".join(out))

# info-specific detail
out2 = []
b2 = "papers_pilot/info"
for r, d, f in os.walk(b2):
    for n in f:
        p = os.path.join(r, n)
        mt = os.path.getmtime(p)
        out2.append(datetime.datetime.fromtimestamp(mt).strftime("%m-%d %H:%M:%S") + "  %8d  " % os.path.getsize(p) + p.replace("\\", "/"))
out2.sort()
open(".dump/_probe3.txt", "w", encoding="utf-8").write("\n".join(out2))
