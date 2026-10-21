# -*- coding: utf-8 -*-
"""
拆书流水线 · 章号规范化（tiancai 专用，可重复执行）
====================================================
问题背景
--------
《天才基本法》源 txt 是 numbered 模式（标题形如「109.变化」），但 split_chapters
曾把若干「作业清单行」（如「3.下节课发报名表，一定要考上！」）误判为章标题，
导致：
  - 内部 chapter_index 在 108 章之后整体偏移（c112 的真实标题其实是「109.变化」）
  - 多出 1 个伪章（chapter_index=111，标题「3.下节课发报名表…」，正文只是 108 章
    结尾的一行字）

处理策略（保守，不动 key）
--------------------------
key（tiancai-cNNN）保持原样，作为内部唯一 ID —— 已入库的 222 条抽取记录、批次文件、
下游 payload 全部依赖它，改名风险远大于收益。

改为：
  1. 从 heading_raw 解析**书中真实章号** `book_no`，写入 chapters.json；
  2. 剔除 book_no 非递增的伪章（即那个 heading=3 的重复项），同时删掉它的抽取记录；
  3. 下游展示统一用 book_no（见 merge.py 的 "no" 字段与 app.js 的章节标签）。

用法：
    python src/normalize_chapters.py tiancai
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HEAD_RE = re.compile(r"^\s*(\d+)\s*[.．、]")


def main():
    book = sys.argv[1] if len(sys.argv) > 1 else "tiancai"
    ddir = os.path.join(BASE, "data", book)
    ch_path = os.path.join(ddir, "chapters.json")
    raw_path = os.path.join(ddir, "extract_raw.json")

    chapters = json.load(open(ch_path, encoding="utf-8"))
    chapters.sort(key=lambda c: c["chapter_index"])

    kept, dropped = [], []
    prev_no = 0
    for c in chapters:
        m = HEAD_RE.match(c.get("heading_raw") or "")
        if not m:
            # 解析不出章号时按顺序递补，不丢弃
            c["book_no"] = prev_no + 1
            prev_no = c["book_no"]
            kept.append(c)
            continue
        no = int(m.group(1))
        if no <= prev_no:
            # 章号没有前进 → 伪章（误切的清单行）
            dropped.append((c["key"], c.get("heading_raw"), c["chars"]))
            continue
        c["book_no"] = no
        prev_no = no
        kept.append(c)

    # 校验真实章号是否 1..N 连续，不连续要如实报告（可能是源文缺章）
    nos = [c["book_no"] for c in kept]
    gaps = [n for n in range(1, max(nos) + 1) if n not in set(nos)]

    with open(ch_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=1)

    # 同步删除被剔除伪章的抽取记录
    drop_keys = {k for k, _, _ in dropped}
    if os.path.exists(raw_path) and drop_keys:
        raw = json.load(open(raw_path, encoding="utf-8"))
        raw = [r for r in raw if r.get("key") not in drop_keys]
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=1)

    print(f"[done] {book}: 保留 {len(kept)} 章（真实章号 1..{max(nos)}）")
    for k, h, n in dropped:
        print(f"       剔除伪章 {k}：heading_raw={h!r}（{n} 字）")
    print(f"       真实章号缺口：{gaps if gaps else '无（连续）'}")
    off = [(c["chapter_index"], c["book_no"]) for c in kept if c["chapter_index"] != c["book_no"]]
    if off:
        print(f"       内部索引与真实章号不一致 {len(off)} 处"
              f"（首个 c{off[0][0]}→第{off[0][1]}章，末个 c{off[-1][0]}→第{off[-1][1]}章）")


if __name__ == "__main__":
    main()
