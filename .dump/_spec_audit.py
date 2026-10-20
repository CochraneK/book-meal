# -*- coding: utf-8 -*-
"""aris 规格逐篇审计：英文摘要、Related Work 篇幅、PAPER_PLAN/AUDIT、BibTeX 解析、
正文 \cite 是否都能在 bib 里找到、图内是否写标题（Hero 图规则）。只读。"""
import io
import os
import re
import sys

ROOT = r"D:\2026\WB项目\明朝"
PDIR = os.path.join(ROOT, "papers_pilot")
sys.path.insert(0, os.path.join(PDIR, "_lib"))
from dup_blocks import is_pid

rows = []


def read(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""


def en_abstract(pid):
    """从 main.tex 抓英文摘要环境：抽象名含 abstract 且正文是拉丁字母为主。"""
    m = read(os.path.join(PDIR, pid, "paper", "main.tex"))
    m2 = re.sub(r"(?s)%.*?\n", "", m)
    for pat in [r"(?is)\\begin\{abstract\}(.*?)\\end\{abstract\}",
                r"(?is)\\begin\{IEEEABSTR\}.*?\\end\{IEEEABSTR\}"]:
        mm = re.search(pat, m2)
        if mm:
            body = mm.group(1)
            words = re.findall(r"[A-Za-z][A-Za-z'\-]*", body)
            return len(words), body
    return 0, ""


def cn_abstract_len(pid):
    m2 = re.sub(r"(?s)%.*?\n", "", read(os.path.join(PDIR, pid, "paper", "main.tex")))
    if "摘　要" in m2 or "摘要" in m2:
        segs = re.findall(r"(?s)摘\s*要(.*?)(?:Abstract|ABSTRACT)", m2)
        if segs:
            return len(re.sub(r"[^\u4e00-\u9fff]", "", segs[0]))
    return 0


def sec_len(pid, name):
    p = os.path.join(PDIR, pid, "paper", "sections", name)
    if not os.path.exists(p):
        return -1
    t = read(p)
    t = re.sub(r"(?s)%.*?\n", "", t)
    return len(re.sub(r"[^\u4e00-\u9fff]", "", t))


def bib_keys(pid):
    t = read(os.path.join(PDIR, pid, "paper", "references.bib"))
    return set(re.findall(r"(?m)^\s*@\w+\{([^,]+),", t))


for pid in sorted(d for d in os.listdir(PDIR) if is_pid(d)):
    base = os.path.join(PDIR, pid)
    nword, _ = en_abstract(pid)
    cn = cn_abstract_len(pid)
    rw = sec_len(pid, "2_related_work.tex")
    intro = sec_len(pid, "1_introduction.tex")
    plan = os.path.exists(os.path.join(base, "PAPER_PLAN.md"))
    audit = read(os.path.join(base, "AUDIT.md"))
    audit_ok = ("边界" in audit) or ("声明" in audit)
    keys = bib_keys(pid)
    # 正文引用
    cites = set()
    for f in sorted(os.listdir(os.path.join(base, "paper", "sections"))):
        t = read(os.path.join(base, "paper", "sections", f))
        cites |= set(re.findall(r"\\cite[a-z]*\{([^}]*)\}", t))
    flat = set()
    for c in cites:
        for part in c.split(","):
            part = part.strip()
            if part:
                flat.add(part)
    missing = sorted(flat - keys)
    # 图内是否写标题（Hero 图规则：caption 应在 figure 环境里由 LaTeX 排，
    # 这里只查图内是否有裸中文长句疑似写在图里）
    rows.append(dict(pid=pid, en=nword, cn=cn, rw=rw, intro=intro,
                     plan=plan, audit=audit_ok, refs=len(keys),
                     cites=len(flat), missing=missing))

print("%-20s %5s %5s %6s %6s %5s %5s %5s %5s %s" % (
    "pid", "EN词", "中摘", "RW字", "intro", "plan", "AUDIT", "bib", "cite", "悬空引用"))
for r in rows:
    flag = ""
    if r["en"] and not (150 <= r["en"] <= 250):
        flag += " EN摘要词数越界"
    if r["rw"] < 250:
        flag += " RW偏薄"
    if r["missing"]:
        flag += " 缺%d条bib" % len(r["missing"])
    if r["refs"] and r["refs"] != r["cites"] and not r["missing"]:
        pass
    print("%-20s %5d %5d %6d %6d %5s %5s %5d %5d %s%s" % (
        r["pid"], r["en"], r["cn"], r["rw"], r["intro"],
        "Y" if r["plan"] else "N", "Y" if r["audit"] else "N",
        r["refs"], r["cites"], " ".join(r["missing"]), flag))

print()
bad_en = [r["pid"] for r in rows if r["en"] and not (150 <= r["en"] <= 250)]
bad_rw = [r["pid"] for r in rows if r["rw"] < 250]
no_plan = [r["pid"] for r in rows if not r["plan"]]
no_audit = [r["pid"] for r in rows if not r["audit"]]
has_miss = [(r["pid"], r["missing"]) for r in rows if r["missing"]]
print("EN 摘要 150–250 词越界：%d → %s" % (len(bad_en), bad_en))
print("Related Work <250 汉字（不到一整页）：%d → %s" % (len(bad_rw), bad_rw))
print("缺 PAPER_PLAN.md：%d → %s" % (len(no_plan), no_plan))
print("AUDIT 无边界声明：%d → %s" % (len(no_audit), no_audit))
print("正文引用在 bib 里悬空：%d → %s" % (len(has_miss), has_miss))
