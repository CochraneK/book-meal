# -*- coding: utf-8 -*-
"""
一次性数据修复（2026-10-17）
============================
问题背景：抽取期间 chapters.json 曾被重建成含 2 个空伪章的 224 版，
个别 agent 的键名/标签受影响。已验证 192/194 条记录的键名与 222 版
chapters.json 的章节标题一致，仅 2 条异常：

1. tiancai-c56：内容是「第60章 鉴定」的重复误录（人物/事件与 c60 记录
   完全一致）→ 删除该条；真实第 56 章「借口」从未被抽取，记入缺失。
2. tiancai-c160：键正确，chapter 标签被 agent 误写成「第160章 （标题误标为
   第157章）」→ 按 chapters.json 修正标签。

用法：python src/repair_records.py tiancai
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    book = sys.argv[1] if len(sys.argv) > 1 else "tiancai"
    ddir = os.path.join(BASE, "data", book)
    raw_path = os.path.join(ddir, "extract_raw.json")
    raw = json.load(open(raw_path, encoding="utf-8"))
    chs = {c["chapter_index"]: c for c in
           json.load(open(os.path.join(ddir, "chapters.json"), encoding="utf-8"))}

    removed, relabeled = [], []
    keep = []
    for r in raw:
        k = r.get("key", "")
        idx = int(k.split("-c")[1]) if "-c" in k else None
        # 规则 1：tiancai-c56 只删除「标签与权威标题不符」的那条历史误录
        # （曾把 c60「鉴定」的内容错记到 c56；真实第 56 章「借口」已补齐，
        #  这里必须按标签判定，否则会把正确记录一起删掉）
        if k == "tiancai-c56":
            want56 = f"第56章 {chs[56]['chapter_title']}" if 56 in chs else None
            if want56 and r.get("chapter") != want56:
                removed.append((k, r.get("chapter")))
                continue
        # 规则 2：chapter 标签与 chapters.json 不一致时按权威源修正
        if idx in chs:
            want = f"第{idx}章 {chs[idx]['chapter_title']}"
            if r.get("chapter") != want:
                relabeled.append((k, r.get("chapter"), want))
                r["chapter"] = want
        keep.append(r)

    keep.sort(key=lambda r: r["key"])
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=1)

    print(f"[done] {book}: 保留 {len(keep)} 条；删除 {removed}；重贴标签 {len(relabeled)} 条")
    for x in relabeled:
        print("       ", x)
    missing = [c["chapter_index"] for c in sorted(chs.values(), key=lambda x: x["chapter_index"])
               if f"{book}-c{c['chapter_index']}" not in {r["key"] for r in keep}]
    print(f"       仍缺失 {len(missing)} 章: {missing}")


if __name__ == "__main__":
    main()
