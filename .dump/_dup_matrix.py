# -*- coding: utf-8 -*-
"""全库两两正文 4-gram Jaccard 矩阵 + 定位逐字共享块的长度分布。"""
import io, os, re, itertools

ROOT = r"D:\2026\WB项目\明朝"
PDIR = os.path.join(ROOT, "papers_pilot")


def is_pid(d):
    p = os.path.join(PDIR, d)
    if d.startswith("_") or d.startswith("."):
        return False
    return os.path.exists(os.path.join(p, "paper", "main.tex"))


def body(pid):
    d = os.path.join(PDIR, pid, "paper", "sections")
    t = ""
    for f in sorted(os.listdir(d)):
        t += io.open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", t)


def grams(t, n=4):
    return set(t[i:i + n] for i in range(len(t) - n + 1))


pids = sorted(d for d in os.listdir(PDIR) if is_pid(d))
G = {}
LEN = {}
for p in pids:
    b = body(p)
    LEN[p] = len(b)
    G[p] = grams(b)

print("pid 数 =", len(pids))
print()
rows = []
for a, b in itertools.combinations(pids, 2):
    j = len(G[a] & G[b]) / max(1, len(G[a] | G[b]))
    rows.append((j, a, b))
rows.sort(reverse=True)
print("== 两两 Jaccard top 30 ==")
for j, a, b in rows[:30]:
    flag = "  ✗越界" if j >= 0.45 else ("  ·注意" if j >= 0.30 else "")
    print("  %.4f  %-18s <-> %-18s%s" % (j, a, b, flag))
print()
over = [r for r in rows if r[0] >= 0.45]
warn = [r for r in rows if 0.30 <= r[0] < 0.45]
print("越界(≥0.45) %d 对；注意(0.30~0.45) %d 对；合计 %d 对需处理"
      % (len(over), len(warn), len(over) + len(warn)))
print()
# 谁卷入
hits = set()
for j, a, b in over + warn:
    hits.add(a); hits.add(b)
print("卷入的 pid（%d）：" % len(hits))
print("  " + "  ".join(sorted(hits)))
print()
print("== 干净 pid（未被卷入）==")
clean = [p for p in pids if p not in hits]
print("  " + "  ".join(clean))
print()
# 逐字共享块长度分布：对最糟的一对
if over:
    (j, a, b) = over[0]
    A, B = body(a), body(b)
    k = 25
    S = set(A[i:i + k] for i in range(len(A) - k + 1))
    out, i, n = [], 0, len(B)
    while i < n - k + 1:
        if B[i:i + k] in S:
            s = i
            while i + k <= n and B[i:i + k] in S:
                i += 1
            out.append((s, i + k))
        else:
            i += 1
    tot = sum(e - s for s, e in out)
    print("== %s 逐字覆盖 %s 的块分布 ==" % (b, a))
    print("  块数 %d，覆盖 %d 字（正文 %d，%.1f%%）" % (len(out), tot, len(B), 100.0 * tot / len(B)))
    lens = sorted((e - s) for s, e in out)
    buckets = [(30, 60), (60, 100), (100, 150), (150, 250), (250, 9999)]
    for lo, hi in buckets:
        c = sum(1 for L in lens if lo <= L < hi)
        print("    长度 %4d-%-4s : %d 块" % (lo, hi, c))
