# -*- coding: utf-8 -*-
"""诊断 economics ↔ systems 的正文重合：量化被模板样板覆盖的比例。"""
import io, os, re

ROOT = r"D:\2026\WB项目\明朝"


def body(pid):
    d = os.path.join(ROOT, "papers_pilot", pid, "paper", "sections")
    t = ""
    for f in sorted(os.listdir(d)):
        t += io.open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", t)


def cover_blocks(B, A, k=25):
    """贪心扫描：B 中连续 k 字出现在 A 里就吸成一整块。返回 [(start, end)]。"""
    S = set(A[i:i + k] for i in range(len(A) - k + 1))
    out, i, n = [], 0, len(B)
    while i < n - k + 1:
        if B[i:i + k] in S:
            j = i
            while j + k <= n and B[j:j + k] in S:
                j += 1
            out.append((i, j + k))
            i = j + k
        else:
            i += 1
    return out


pairs = [("economics", "systems")]

# 先看全库所有两两，谁越界
import itertools
pids = ["economics", "systems", "museum", "politics", "law", "science", "info",
        "narrative", "synthesis", "geography", "ideology", "diplomacy"]
memo = {}
rows = []
for a, b in itertools.combinations(pids, 2):
    if a not in memo:
        memo[a] = body(a)
    if b not in memo:
        memo[b] = body(b)
    A, B = memo[a], memo[b]
    ga = set(A[i:i + 4] for i in range(len(A) - 3))
    gb = set(B[i:i + 4] for i in range(len(B) - 3))
    j = len(ga & gb) / max(1, len(ga | gb))
    if j >= 0.20:
        rows.append((j, a, b))
rows.sort(reverse=True)
print("== 两两 4-gram Jaccard（≥0.20 的都列出来）==")
for j, a, b in rows:
    print("  %.4f  %s <-> %s" % (j, a, b))

# 细查 economics <-> systems
A, B = body("economics"), body("systems")
bs = cover_blocks(B, A)
tot = sum(e - s for s, e in bs)
print()
print("systems 正文 %d 字；被 economics 逐字覆盖（≥25 字块）合计 %d 字 = %.1f%%"
      % (len(B), tot, 100.0 * tot / len(B)))
print("共 %d 个覆盖块，前 10 个：" % len(bs))
for s, e in bs[:10]:
    print("   @%5d len=%4d  %s" % (s, e - s, B[s:min(e, s + 60)]))
