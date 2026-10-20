# -*- coding: utf-8 -*-
"""全库扫「正文 \\cite 了但 references.bib 里没有的 key」。

这类悬空不会进 LaTeX 的 undefined citation 告警（natbib 对未定义 bibkey 只静默出 [?]），
所以闸 1 抓不到。这是发现 sovereign/freeman1979 那条之后补的扫描。
"""
import io
import os
import re
import sys

PDIR = r"D:\2026\WB项目\明朝\papers_pilot"
sys.path.insert(0, os.path.join(PDIR, "_lib"))
from dup_blocks import is_pid


def read(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""


def strip_comments(t):
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c == "\\" and i + 1 < n:
            out.append(t[i:i + 2]); i += 2; continue
        if c == "%":
            j = t.find("\n", i)
            if j == -1: break
            i = j; continue
        out.append(c); i += 1
    return "".join(out)


total = 0
for pid in sorted(d for d in os.listdir(PDIR) if is_pid(d)):
    bib = read(os.path.join(PDIR, pid, "paper", "references.bib"))
    keys = set(re.findall(r"(?m)^\s*@\w+\{\s*([^,]+)\s*,", bib))
    used = set()
    base = os.path.join(PDIR, pid, "paper")
    for f in sorted(os.listdir(os.path.join(base, "sections"))):
        t = strip_comments(read(os.path.join(base, "sections", f)))
        for blk in re.findall(r"\\cite[a-z]*\{([^}]*)\}", t):
            for k in blk.split(","):
                k = k.strip()
                if k:
                    used.add(k)
    # main.tex 里的 \bibliography 或 \addbibresource 由 bibtex 解析，也算已用
    miss = sorted(used - keys)
    if miss:
        total += len(miss)
        print("%-22s 缺 %d: %s" % (pid, len(miss), miss))
print()
print("全库悬空 cite key 合计 =", total)
