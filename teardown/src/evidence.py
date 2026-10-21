# -*- coding: utf-8 -*-
"""
原文取证：把某个词在全书正文里的上下文片段打出来，用于裁定命名冲突。
用法：python src/evidence.py feitu 祝遥 [每章最多几条] [最多总条数]
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


def main():
    book = sys.argv[1]
    word = sys.argv[2]
    per_ch = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    chapters = json.load(open(os.path.join(BASE, "data", book, "chapters.json"),
                             encoding="utf-8"))
    chapters.sort(key=lambda c: c["chapter_index"])

    shown = 0
    for c in chapters:
        body = c["body"]
        if word not in body:
            continue
        hits = 0
        for m in re.finditer(re.escape(word), body):
            if hits >= per_ch or shown >= limit:
                break
            s = max(0, m.start() - 70)
            e = min(len(body), m.end() + 70)
            frag = body[s:e].replace("\n", " ")
            no = c.get("book_no", c["chapter_index"])
            print(f"[第{no}章 {c['chapter_title']}] …{frag}…")
            hits += 1
            shown += 1
        if shown >= limit:
            break
    print(f"\n[evidence] 共输出 {shown} 条含「{word}」的片段")


if __name__ == "__main__":
    main()
