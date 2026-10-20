# -*- coding: utf-8 -*-
"""在 .dump/bibtest 里用最小 main.tex 复现 bibtex/bbl 错误，并二分定位坏条目。"""
import os, re, subprocess, sys

ROOT = r"D:\2026\WB项目\明朝"
TECT = r"E:\tex\tectonic.exe"
SD = os.path.join(ROOT, ".dump", "bibtest")
BIB = os.path.join(ROOT, "papers_pilot", "info", "paper", "references.bib")


def split_entries():
    txt = open(BIB, encoding="utf-8").read()
    idx = [m.start() for m in re.finditer(r"^@", txt, re.M)]
    res = []
    for i, s in enumerate(idx):
        e = txt[s:]
        if i + 1 < len(idx):
            e = txt[s:idx[i + 1]]
        key = re.match(r"@\w+\s*\{\s*([^,]+),", e).group(1).strip()
        res.append((key, e))
    return res


def run(keys):
    os.makedirs(os.path.join(SD, "out"), exist_ok=True)
    entries = split_entries()
    chosen = [e for k, e in entries if k in keys]
    with open(os.path.join(SD, "references.bib"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(chosen))
    keylist = []
    for k, e in entries:
        if k in keys:
            name = re.match(r"@\w+\s*\{\s*([^,]+),", e).group(1).strip()
            keylist.append(name)
    with open(os.path.join(SD, "main.tex"), "w", encoding="utf-8") as fh:
        fh.write(r"\documentclass[conference]{IEEEtran}" + "\n"
                 r"\begin{document}" + "\n"
                 "x " + " ".join("\\cite{%s}" % k for k in keylist) + "\n"
                 r"\bibliographystyle{IEEEtran}" + "\n"
                 r"\bibliography{references}" + "\n"
                 r"\end{document}" + "\n")
    logpath = os.path.join(SD, "main.log")
    if os.path.exists(logpath):
        os.remove(logpath)
    p = subprocess.run([TECT, "main.tex", "--outdir", "out", "--keep-logs"],
                       cwd=SD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    txt = ""
    if os.path.exists(logpath):
        txt = open(logpath, encoding="utf-8", errors="replace").read()
    bad = ("missing \\item" in txt) or ("errors were issued by BibTeX" in txt) or ("LaTeX Error" in txt)
    return bad, p.returncode, txt[-2500:], len(chosen)


if __name__ == "__main__":
    keys = sys.argv[1:]
    bad, rc, tail, n = run(keys)
    open(os.path.join(ROOT, ".dump", "_bibtest.txt"), "w", encoding="utf-8").write(
        "keys=%s n=%d bad=%s rc=%d\n%s" % (keys, n, bad, rc, tail))
