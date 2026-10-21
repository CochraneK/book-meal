# -*- coding: utf-8 -*-
"""
拆书流水线 · 进度统计
====================
按 chapters.json 里的**真实章节键**比对 extract_raw.json，输出：
- 已覆盖 / 总数
- 缺失章节号（紧凑区间表示）
- 孤儿记录（extract_raw 里存在但 chapters.json 已无此章）

用法：
    python src/progress.py            # 两本书都看
    python src/progress.py feitu      # 只看一本
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def compact(nums):
    """把 [1,2,3,7,9,10] 压成 '1-3,7,9-10'。"""
    if not nums:
        return "-"
    nums = sorted(nums)
    out = []
    s = p = nums[0]
    for n in nums[1:]:
        if n == p + 1:
            p = n
            continue
        out.append(str(s) if s == p else f"{s}-{p}")
        s = p = n
    out.append(str(s) if s == p else f"{s}-{p}")
    return ",".join(out)


def report(book):
    ch_p = os.path.join(BASE, "data", book, "chapters.json")
    raw_p = os.path.join(BASE, "data", book, "extract_raw.json")
    if not os.path.exists(ch_p):
        print(f"{book}: 缺少 chapters.json")
        return
    chapters = json.load(open(ch_p, encoding="utf-8"))
    want = {c["key"]: c["chapter_index"] for c in chapters}
    recs = json.load(open(raw_p, encoding="utf-8")) if os.path.exists(raw_p) else []
    have = {r.get("key") for r in recs if r.get("key")}

    missing = [want[k] for k in want if k not in have]
    orphan = sorted(k for k in have if k not in want)
    pct = 100.0 * (len(want) - len(missing)) / max(1, len(want))

    print("=" * 64)
    print(f"{book}: 记录 {len(recs)} 条 | 覆盖 {len(want) - len(missing)}/{len(want)}"
          f" ({pct:.1f}%)")
    print(f"  缺失 ({len(missing)}): {compact(missing)}")
    if orphan:
        print(f"  孤儿记录 ({len(orphan)}): {', '.join(orphan)}")


targets = sys.argv[1:] or ["tiancai", "feitu"]
for b in targets:
    report(b)
