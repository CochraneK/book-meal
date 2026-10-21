# -*- coding: utf-8 -*-
"""
拆书流水线 · 源文本质量检测：重复章节（防盗章伪影）
====================================================
部分网络小说 txt 由多源拼合而成，存在跨章重复/雷同段落（防盗章机制产物）。
本脚本用「开头 N 字相同 + 长度接近 + SequenceMatcher 相似度」三条件判定，
输出 data/<book>/duplicate_report.json：

  {"pairs": [{"a": 50, "b": 76, "sim": 0.93, "chars_a": 3100, "chars_b": 3000}, ...],
   "dup_groups": [[50, 76, 82], ...],        # 同源章组（传递闭包）
   "dup_chapters": [50, 76, 82, ...]}        # 所有涉及重复的章序号

原则：不删内容、不改正文——重复章在报告里如实标注（分布图斜纹 + 总览披露），
实体计数保留原样（源透明度），但读者能看出哪些章是重复源。
"""

import difflib
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM_THRESHOLD = 0.85
HEAD_N = 300


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build(book_id):
    ddir = os.path.join(BASE, "data", book_id)
    chapters = load(os.path.join(ddir, "chapters.json"))
    bodies = {c["chapter_index"]: c["body"].replace("\n", "") for c in chapters}
    idxs = sorted(bodies)
    pairs = []
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            a, b = idxs[i], idxs[j]
            ba, bb = bodies[a], bodies[b]
            # 快速筛：开头 300 字几乎一致（autojunk=False：中文常用字多，
            # 默认 autojunk 会把高频字当 junk，导致相似度虚高、误报泛滥）
            if difflib.SequenceMatcher(None, ba[:HEAD_N], bb[:HEAD_N], autojunk=False).quick_ratio() < 0.98:
                continue
            # 长度差 >20% 的直接排除（拼合错位/改写扩写不算重复）
            if abs(len(ba) - len(bb)) / max(len(ba), len(bb)) > 0.2:
                continue
            # 全文相似度：只开头像不算重复（同一场景被重述是正常叙事）
            sim = difflib.SequenceMatcher(None, ba, bb, autojunk=False).ratio()
            if sim >= SIM_THRESHOLD:
                pairs.append({"a": a, "b": b, "sim": round(sim, 3),
                              "chars_a": len(ba), "chars_b": len(bb)})
    # 传递闭包找同源组
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        parent[find(x)] = find(y)
    for p in pairs:
        union(p["a"], p["b"])
    groups = {}
    for n in idxs:
        if n in parent:
            groups.setdefault(find(n), []).append(n)
    dup_groups = sorted((sorted(v) for v in groups.values()), key=lambda g: g[0])
    dup_chapters = sorted({n for g in dup_groups for n in g})
    report = {"threshold": SIM_THRESHOLD, "pairs": pairs,
              "dup_groups": dup_groups, "dup_chapters": dup_chapters,
              "total_chapters": len(idxs)}
    out = os.path.join(ddir, "duplicate_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"[done] {book_id} 重复检测：{len(pairs)} 对章节相似度 ≥{SIM_THRESHOLD}，"
          f"涉及 {len(dup_chapters)} 章 / {len(dup_groups)} 个同源组")
    for g in dup_groups[:10]:
        print("       同源组:", g)
    return report


def main():
    for b in (sys.argv[1:] or json.load(open(os.path.join(BASE, "config.json"),
                                             encoding="utf-8"))["books"]):
        build(b)


if __name__ == "__main__":
    main()
