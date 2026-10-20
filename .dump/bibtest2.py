# -*- coding: utf-8 -*-
import os, subprocess, sys
ROOT = r"D:\2026\WB项目\明朝"
TECT = r"E:\tex\tectonic.exe"
SD = os.path.join(ROOT, ".dump", "bibtest")
p = subprocess.run([TECT, "main.tex", "--outdir", "out", "--keep-logs", "--print"],
                   cwd=SD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = "RC=%d\n%s" % (p.returncode, p.stdout.decode("utf-8", "replace")[-6000:])
for r, d, f in os.walk(SD):
    for n in f:
        out += "\nFILE %8d %s" % (os.path.getsize(os.path.join(r, n)), os.path.join(r, n).replace("\\", "/"))
open(os.path.join(ROOT, ".dump", "_bibtest2.txt"), "w", encoding="utf-8").write(out)
