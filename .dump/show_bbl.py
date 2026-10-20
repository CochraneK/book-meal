import os
p = "papers_pilot/info/paper/out/main.bbl"
if not os.path.exists(p):
    for r, d, f in os.walk("papers_pilot/info/paper"):
        for n in f:
            if n.endswith(".bbl") or n.endswith(".blg"):
                print("FOUND", os.path.join(r, n))
    open(".dump/_bbl_head.txt", "w", encoding="utf-8").write("no bbl")
else:
    txt = open(p, encoding="utf-8", errors="replace").read()
    lines = txt.splitlines()
    open(".dump/_bbl_head.txt", "w", encoding="utf-8").write(
        "TOTAL %d lines\n" % len(lines) + "\n".join(lines[:60]))
print(os.path.exists(p))
