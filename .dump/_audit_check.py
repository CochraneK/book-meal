# -*- coding: utf-8 -*-
"""只读：确认 gender 的 AUDIT.md 手写附录还在，且编译产物一致。"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"D:\2026\WB项目\明朝"
p = os.path.join(ROOT, "papers_pilot", "gender", "AUDIT.md")
t = open(p, encoding="utf-8").read()
print("AUDIT size=%d chars, has §7=%s §8=%s §9=%s" % (os.path.getsize(p), "## 7." in t, "## 8." in t, "## 9." in t))
print("tail:", t[-160:].replace("\n", " | "))

sec = os.path.join(ROOT, "papers_pilot", "gender", "paper", "sections", "5_results.tex")
b = open(sec, encoding="utf-8").read()
labels = sorted(set(re.findall(r"\\label\{([^}]*)\}", b)))
refs = sorted(set(re.findall(r"\\ref\{([^}]*)\}", b)))
print("labels:", labels)
print("refs   :", refs)
print("dangling:", [r for r in refs if r not in labels])
print("has 537sentence:", "537 位一条边都没有" in b)
print("has 口径B sentence:", "本篇走的是口径 B" in open(
    os.path.join(ROOT, "papers_pilot", "gender", "paper", "sections", "1_introduction.tex"), encoding="utf-8").read())
