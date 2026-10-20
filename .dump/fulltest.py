# -*- coding: utf-8 -*-
"""把 info/paper 完整拷到 .dump/bibfull 再编译，判断错误是否随正文一起复现。"""
import os, shutil, subprocess

ROOT = r"D:\2026\WB项目\明朝"
TECT = r"E:\tex\tectonic.exe"
SRC = os.path.join(ROOT, "papers_pilot", "info", "paper")
SD = os.path.join(ROOT, ".dump", "bibfull")

if __name__ == "__main__":
    if os.path.isdir(SD):
        shutil.rmtree(SD)
    shutil.copytree(SRC, SD)
    logp = os.path.join(SD, "main.log")
    if os.path.exists(logp):
        os.remove(logp)
    p = subprocess.run([TECT, "main.tex", "--outdir", "out", "--keep-logs"],
                       cwd=SD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    txt = open(logp, encoding="utf-8", errors="replace").read() if os.path.exists(logp) else ""
    bbl = ""
    bp = os.path.join(SD, "out", "main.bbl")
    if os.path.exists(bp):
        bbl = open(bp, encoding="utf-8", errors="replace").read()
    open(os.path.join(ROOT, ".dump", "_fulltest.txt"), "w", encoding="utf-8").write(
        "RC=%d\nHARD=%s\nBIBWARN=%s\nBBL_LINES=%d\n=== BBL 1..40 ===\n%s"
        % (p.returncode, [l for l in txt.splitlines() if l.startswith("! ") or " LaTeX Error" in l][:5],
           "errors were issued by BibTeX" in txt, len(bbl.splitlines()),
           "\n".join(bbl.splitlines()[:40])))
