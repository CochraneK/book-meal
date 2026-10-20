# -*- coding: utf-8 -*-
"""完整编译 info（拷贝件），保留中间产物，检查 bbl 是否有 12 条 bibitem。"""
import os, shutil, subprocess, zlib, re

ROOT = r"D:\2026\WB项目\明朝"
TECT = r"E:\tex\tectonic.exe"
SRC = os.path.join(ROOT, "papers_pilot", "info", "paper")
SD = os.path.join(ROOT, ".dump", "bibfull")

if __name__ == "__main__":
    if os.path.isdir(SD):
        shutil.rmtree(SD)
    shutil.copytree(SRC, SD)
    p = subprocess.run([TECT, "main.tex", "--outdir", "out", "--keep-logs",
                        "--keep-intermediates"],
                       cwd=SD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = ""
    lp = os.path.join(SD, "main.log")
    if os.path.exists(lp):
        log = open(lp, encoding="utf-8", errors="replace").read()
    log = open(os.path.join(ROOT, ".dump", "_compile_info.log"), encoding="utf-8").read()
    bblp = os.path.join(SD, "out", "main.bbl")
    bbl = open(bblp, encoding="utf-8", errors="replace").read() if os.path.exists(bblp) else ""
    pdf = os.path.join(SD, "out", "main.pdf")
    nleft = [l for l in log.splitlines() if "undefined" in l]
    out = ["RC=%d" % p.returncode,
           "BIBITEMS=%d" % len(re.findall(r"\\bibitem", bbl)),
           "UNDEF=%s" % nleft[:6],
           "BBL_HEAD=%s" % "\n".join(bbl.splitlines()[:14]),
           "PAGES=%d" % (os.path.getsize(pdf) if os.path.exists(pdf) else -1)]
    open(os.path.join(ROOT, ".dump", "_fulltest2.txt"), "w", encoding="utf-8").write("\n".join(out))
