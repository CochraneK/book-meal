# -*- coding: utf-8 -*-
"""narrative 篇：手工复核 check_one.py 新增的 5b/5c/5d 三项（因 check_one 自身有 bug 无法跑）。"""
import os, re, sys

ROOT = r"D:\2026\WB项目\明朝"
pdir = os.path.join(ROOT, "papers_pilot", "narrative", "paper")
secdir = os.path.join(pdir, "sections")

secs = sorted(f for f in os.listdir(secdir) if f.endswith(".tex"))
body = "".join(open(os.path.join(secdir, s), encoding="utf-8").read() for s in secs)

bad = []

# 5b 哨兵
for s in secs:
    t = open(os.path.join(secdir, s), encoding="utf-8").read()
    for m in re.findall(r"@@\w+@@", t):
        bad.append("5b 哨兵 %s: %s" % (s, m))

# 5c 悬空 \ref
labels = set(re.findall(r"\\label\{([^}]*)\}", body))
dangling = sorted(set(re.findall(r"\\ref\{([^}]*)\}", body)) - labels)
if dangling:
    bad.append("5c 悬空引用 %s" % dangling)

# 5d 裸 CR / 中文紧贴 ref
for d, _, fs in os.walk(pdir):
    for f in fs:
        if not f.endswith(".tex"):
            continue
        p = os.path.join(d, f)
        t = open(p, encoding="utf-8").read()
        if "\r" in t:
            bad.append("5d 裸回车 %s" % f)
        if re.search(r"[\u4e00-\u9fff]\s*ref\s*\{", t):
            bad.append("5d 中文紧贴 ref %s" % f)

# 双 \item
for s in secs:
    t = open(os.path.join(secdir, s), encoding="utf-8").read()
    for m in re.findall(r"\\\\item", t) + re.findall(r"\\item\s*\\item", t):
        bad.append("双 item %s: %r" % (s, m))
    if re.search(r"\n\s*\\item\s*\n", t):
        pass

# main.tex 关键项
mt = open(os.path.join(pdir, "main.tex"), encoding="utf-8").read()
for k in ("\\setCJKmainfont{STSong}", "\\author{Anonymous}", "\\begin{abstract}", "\\end{abstract}"):
    if k not in mt:
        bad.append("main.tex 缺 %s" % k)
if "\\renewcommand{\\bibname}" in mt:
    bad.append("main.tex 含 \\renewcommand{\\bibname}")
if "\\begin{comment}" in mt and "\\usepackage{comment}" not in mt:
    bad.append("main.tex 用了 comment 环境")

# 残留标记
for d, _, fs in os.walk(pdir):
    for f in fs:
        if f.endswith((".tex", ".bib")):
            t = open(os.path.join(d, f), encoding="utf-8").read()
            for kw in ("[VERIFY]", "TODO", "XXX"):
                if kw in t:
                    bad.append("残留 %s in %s" % (kw, f))

print("sections    :", secs)
print("汉字        :", len(re.findall(r"[\u4e00-\u9fff]", body)))
print("labels      :", sorted(labels))
print("\\ref 全集    :", sorted(set(re.findall(r"\\ref\{([^}]*)\}", body))))
import json
pool = set()


def flat(o):
    if isinstance(o, dict):
        for v in o.values():
            flat(v)
    elif isinstance(o, list):
        for v in o:
            flat(v)
    elif isinstance(o, (int, float)):
        pool.add(round(float(o), 2))
    elif isinstance(o, str):
        for m in re.findall(r"\d+(?:\.\d+)?", o):
            try:
                pool.add(round(float(m), 2))
            except ValueError:
                pass
    return None


flat(json.load(open(os.path.join(ROOT, ".dump", "_stats_narrative.json"), encoding="utf-8")))
used = sorted(set(round(float(x), 2) for x in re.findall(r"\d+\.\d+", body)))
unmatched = [u for u in used if not any(abs(u - v) <= 0.06 for v in pool)]
print("正文小数     :", used)
print("未匹配       : %d / %d = %.3f (闸阈值 0.34)" % (len(unmatched), len(used), len(unmatched) / float(len(used))))
print("   ", unmatched)
print()
if bad:
    print("问题 %d 条：" % len(bad))
    for b in bad:
        print("  ✗", b)
    sys.exit(1)
print("5b/5c/5d/main/残留 全部 OK")
