# -*- coding: utf-8 -*-
"""从 data/chapters.json 导出轻量章节字数表 data/chapter_lengths.json。

背景：``data/chapters.json`` 约 4.5MB（含全书正文），被 .gitignore 排除，
CI 构建因此读不到正文、算不出 ``textLength``，分布视图的「每万字密度」
会全部变成 0。本脚本只导出每章正文字符数（约 4KB），随仓库提交，
让 CI 也能算出密度；本地有正文时构建仍以正文长度为准，两者口径一致。

用法：``python src/dump_chapter_lengths.py``
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "data" / "chapters.json"
OUT = BASE / "data" / "chapter_lengths.json"


def main() -> int:
    records = json.loads(SRC.read_text(encoding="utf-8"))
    lengths = {
        item["key"]: len(item.get("body", ""))
        for item in records
        if item.get("type") == "chapter" and item.get("key")
    }
    OUT.write_text(
        json.dumps(lengths, ensure_ascii=False, indent=0, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("已写入 %s：%d 章" % (OUT.relative_to(BASE), len(lengths)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
