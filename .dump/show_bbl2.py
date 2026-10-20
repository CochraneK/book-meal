import os, glob
out = []
for r, d, f in os.walk("papers_pilot/info"):
    for n in f:
        if n.endswith((".bbl", ".blg", ".bib", ".aux")):
            p = os.path.join(r, n)
            out.append("%8d %s" % (os.path.getsize(p), p.replace("\\", "/")))
out.append("--- paper dir listing ---")
for r, d, f in os.walk("papers_pilot/info/paper"):
    for n in f:
        p = os.path.join(r, n)
        if p.endswith((".bbl", ".blg", ".aux", ".log")):
            out.append("%8d %s" % (os.path.getsize(p), p.replace("\\", "/")))
open(".dump/_bbl_list.txt", "w", encoding="utf-8").write("\n".join(out))
