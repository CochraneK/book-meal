# -*- coding: utf-8 -*-
import os, subprocess, shutil

T = r"E:\tex\tectonic.exe"
PRE = r"""\documentclass[conference]{IEEEtran}
\usepackage{ctex}
\setCJKmainfont{STSong}
\usepackage[numbers]{natbib}
\usepackage{amsmath}
\newcommand{\Rho}{\rho}
\newcommand{\pct}[1]{#1\%}
\begin{document}
"""
POST = r"""
\end{document}
"""

cases = {
    "c": "A $p<10^{-4}$ B",
    "d": "A $p < 10^{-4}$ B",
    "e": "A \\Rho=0.706 B",
    "f": "A \\Rho=0.706（$p<10^{-4}$）B",
    "g": "A\\Rho\n=0.706（$p<10^{-4}$）。",
    "h": "A \\pct{2.7} B",
    "i": "A \\Rho=0.706 相关为 $p<10^{-4}$ B",
}

d = r"D:\2026\WB项目\明朝\.dump\_tmptest"
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)
for k, v in cases.items():
    open(os.path.join(d, "s_%s.tex" % k), "w", encoding="utf-8").write(PRE + v + POST)
for k in sorted(cases):
    out = os.path.join(d, "out_%s" % k)
    os.makedirs(out, exist_ok=True)
    p = subprocess.run([T, "s_%s.tex" % k, "--outdir", out], cwd=d,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    bad = b"Missing $" in p.stdout
    print(k, "exit=", p.returncode, "Missing$=", bad)
    if bad:
        s = p.stdout.decode("utf-8", "replace").splitlines()
        for l in s:
            if l.startswith("! ") or "Missing $" in l:
                print("    ", l[:120])
