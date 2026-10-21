# -*- coding: utf-8 -*-
"""
拆书流水线 · 阶段② 辅助：按范围打印章节正文
==========================================
用法：
    python src/dump_chapters.py <book> <start> <end>
    python src/dump_chapters.py tiancai 1 8
    python src/dump_chapters.py feitu 100 107

供抽取 agent 读取章节正文用（避免把整个 chapters.json 读进上下文）。
输出为带行号的纯文本，每章之间以 ===== 分隔。

注意：Windows 下 stdout 默认可能是 GBK/cp936，输出中文长文会抛
UnicodeEncodeError 且被外层吞掉（表现为 exit -1 无输出）。这里强制
把 stdout 切到 UTF-8，调用方无需再设 PYTHONIOENCODING。
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 强制 UTF-8 输出，避免不同终端编码导致的静默失败
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return
    book, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    path = os.path.join(BASE, "data", book, "chapters.json")
    chapters = json.load(open(path, encoding="utf-8"))
    idx = {c["chapter_index"]: c for c in chapters}

    printed = 0
    for n in range(start, end + 1):
        c = idx.get(n)
        if not c:
            print(f"===== [缺失] chapter_index={n} 不存在于 chapters.json =====")
            print()
            continue
        print(f"===== {c['key']} | {c['chapter_title']} | {c['chars']}字 =====")
        print(c["body"])
        print()
        printed += 1

    # 结尾汇总走 stderr，避免污染正文
    print(f"[dump] {book} {start}-{end}：实际输出 {printed} 章", file=sys.stderr)


if __name__ == "__main__":
    main()
