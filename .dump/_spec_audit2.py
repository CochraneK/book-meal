# -*- coding: utf-8 -*-
"""aris 规格审计 v2 —— 修掉 v1 的注释剥离过粗暴问题。

v1 用 re.sub(r"(?s)%.*?\\n","",t) 剥注释，但正文里若有**裸 %**（未写成 \\%），
% 会被当成注释起点，把后面的真内容（通常是中文摘要的一行或英文摘要尾巴）整段吃掉，
导致英文摘要词数被严重低估。

v2 的规则：只把「前面不是反斜杠的 %」当作注释起点。
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
            out.append(t[i:i + 2])
            i += 2
            continue
        if c == "%":
            j = t.find("\n", i)
            if j == -1:
                break
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def en_words(pid):
    t = strip_comments(read(os.path.join(PDIR, pid, "paper", "main.tex")))
    for pat in [r"(?is)\\begin\{abstract\}(.*?)\\end\{abstract\}",
                r"(?is)\\begin\{IEEEABSTR\}.*?\\end\{IEEEABSTR\}"]:
        m = re.search(pat, t)
        if m:
            return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", m.group(1))), len(m.group(1))
    return 0, 0


def cn_chars(pid):
    t = strip_comments(read(os.path.join(PDIR, pid, "paper", "main.tex")))
    m = re.search(r"(?is)\\textbf\{摘要（中文）\}(.*?)(?:\\begin\{abstract\}|Abstract)", t)
    if not m:
        return 0
    return len(re.findall(r"[\u4e00-\u9fff]", m.group(1)))


rows = []
for pid in sorted(d for d in os.listdir(PDIR) if is_pid(d)):
    w, n = en_words(pid)
    rows.append((pid, w, n, cn_chars(pid)))

print("%-22s %6s %8s %7s" % ("pid", "EN 词", "原文字符", "中文摘要"))
for pid, w, n, c in rows:
    tag = ""
    if not (150 <= w <= 250):
        tag = "  ✗ 越界"
    print("%-22s %6d %8d %7d%s" % (pid, w, n, c, tag))

bad = [(p, w) for p, w, _, _ in rows if not (150 <= w <= 250)]
print()
print("EN 摘要 150–250 词越界：%d → %s" % (len(bad), bad))
thin = [(p, c) for p, _, _, c in rows if c and not (200 <= c <= 350)]
print("中文摘要不在 200–350 字：%d → %s" % (len(thin), thin))
