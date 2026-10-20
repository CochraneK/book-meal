# -*- coding: utf-8 -*-
"""把已核验的 references.bib 复制到新篇，并按篇名改注释首行。"""
import os, sys
ROOT = r"D:\2026\WB项目\明朝\papers_pilot"
SRC = os.path.join(ROOT, "psychology", "paper", "references.bib")


def copy(pid):
    dst = os.path.join(ROOT, pid, "paper", "references.bib")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    s = open(SRC, encoding="utf-8").read()
    s = s.replace("仅纳入 verify_refs.py 已核验条目",
                  pid + " 篇：仅纳入 verify_refs.py 已核验条目（与已通过核验的通用池一致）")
    open(dst, "w", encoding="utf-8").write(s)
    print("copied ->", dst, len(s))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        copy(p)
