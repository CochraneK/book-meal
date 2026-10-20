import os, datetime
out = []
p = "papers_pilot/info/paper/out"
out.append("exists=%s" % os.path.isdir(p))
for r, d, f in os.walk(p):
    for n in f:
        fp = os.path.join(r, n)
        out.append(datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%H:%M:%S")
                   + " %8d %s" % (os.path.getsize(fp), fp.replace("\\", "/")))
open(".dump/_lsout.txt", "w", encoding="utf-8").write("\n".join(out))
