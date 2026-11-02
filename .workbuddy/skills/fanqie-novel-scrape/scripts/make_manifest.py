# -*- coding: utf-8 -*-
"""
生成 book-meal 书库条目
=======================
把 fanqie.py 的产出接进 book-meal：
正文留在 `data/<id>/chapters/`（**已 gitignore，不入库**），
本脚本只负责写 `books/<id>/manifest.json`（可入库的书目名片）。

用法
----
    # 抓取直接落到 data/<id>/（推荐）
    python fanqie.py --book 7143038691944959011 --out "D:/2026/WB项目/book-meal/data/riye"

    # 写 manifest（order 自动取书库最大值+1）
    python make_manifest.py "D:/2026/WB项目/book-meal/data/riye" \
        --slug riye --repo "D:/2026/WB项目/book-meal"

产出
----
    <repo>/books/<slug>/manifest.json

版权红线（改代码前必读）
------------------------
本仓 `tests/check_copyright.py` 会拦下任何入库的原书正文：
- 名单：chapters.json / 已知书名
- 体积：任何 > 200 KB 的 .txt
- 内容：被跟踪 json 里单个字符串 > 8000 字
- 位置：`data/` 下禁止 .txt/.html/.epub 等载体

所以：
- 正文只能待在 `data/<id>/chapters/`（`data/**/*.txt` 已忽略）；
- **绝不要**把 chapters/ 复制到 `books/<id>/`；
- `books/<id>/` 只放 `index.html`（脱敏报告）+ `manifest.json`。
本脚本因此不再复制任何正文，只写 manifest。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re

# 深色书封基色，按书名哈希稳定取色（与书库现有风格同一色域）
ACCENTS = ["#5a4b8c", "#3d6b7d", "#7d5a3d", "#4b7d5a", "#8c4b5a",
           "#4b5a8c", "#7d7d3d", "#5a7d6b", "#8c6b4b", "#5a4b6b"]

GLYPH_SKIP = set("的了是在和有不这我你他她它们一二三四五六七八九十")

# 书名 → 报告类型（沿用书库既有取值）
KIND_CHOICES = ("history", "modern_real", "fictional_world", "humanities", "other")


def pick_accent(title):
    h = int(hashlib.md5(title.encode("utf-8")).hexdigest(), 16)
    return ACCENTS[h % len(ACCENTS)]


def pick_glyph(title):
    for ch in title:
        if ch not in GLYPH_SKIP and "\u4e00" <= ch <= "\u9fff":
            return ch
    return title[0] if title else "书"


def shorten(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def next_order(books_dir):
    if not os.path.isdir(books_dir):
        return 1
    orders = []
    for name in os.listdir(books_dir):
        mp = os.path.join(books_dir, name, "manifest.json")
        if os.path.exists(mp):
            try:
                orders.append(json.load(open(mp, encoding="utf-8")).get("order", 0) or 0)
            except Exception:
                pass
    return (max(orders) + 1) if orders else 1


def main():
    ap = argparse.ArgumentParser(description="生成 book-meal manifest（不复制正文）")
    ap.add_argument("dir", help="fanqie.py 的 --out 目录（含 meta.json）")
    ap.add_argument("--slug", required=True, help="书库目录名，如 riye / swdw")
    ap.add_argument("--repo", required=True, help="book-meal 仓库根目录")
    ap.add_argument("--kind", default="fictional_world", choices=KIND_CHOICES,
                    help="门户类型筛选用的分类")
    ap.add_argument("--order", type=int, default=0, help="排序号，0=自动取最大值+1")
    ap.add_argument("--note", default="", help="卡片徽标文字，缺省自动生成")
    args = ap.parse_args()

    src = os.path.abspath(args.dir)

    # 版权防线：正文不许出现在 books/ 下（先于一切文件检查）
    src_norm = src.replace("\\", "/").lower()
    if "/books/" in src_norm:
        raise SystemExit(
            "✗ 输出目录在 books/ 下。正文必须放 data/<id>/（gitignore 已覆盖），\n"
            "  books/<id>/ 只放 index.html + manifest.json。请把 --out 改成 data/<id>。"
        )

    meta_path = os.path.join(src, "meta.json")
    if not os.path.exists(meta_path):
        raise SystemExit(f"找不到 {meta_path}，先跑 fanqie.py")

    meta = json.load(open(meta_path, encoding="utf-8"))
    title = meta.get("title") or args.slug
    total = meta.get("chapters") or 0

    src_ch = os.path.join(src, "chapters")
    fetched = len([f for f in os.listdir(src_ch) if re.fullmatch(r"\d{4}\.txt", f)]) \
        if os.path.isdir(src_ch) else 0

    order = args.order or next_order(os.path.join(args.repo, "books"))
    note = args.note or (f"正文 {fetched}/{total} 章" if total and fetched != total
                         else f"正文 {fetched} 章")

    manifest = {
        "id": args.slug,
        "title": title,
        "author": meta.get("author") or "",
        "kind": args.kind,
        "desc": shorten(meta.get("abstract") or "", 120),
        "accent": pick_accent(title),
        "metrics": {"characters": 0, "events": 0, "relations": 0},
        "chapters": total,
        "fetched_chapters": fetched,
        "report": "index.html",
        "updated": (meta.get("fetched_at") or "")[:10],
        "order": order,
        "glyph": pick_glyph(title),
        "subtitle": (meta.get("tags") or ["番茄小说"])[0],
        "note": note,
        "external": False,
    }

    dest = os.path.join(args.repo, "books", args.slug)
    os.makedirs(dest, exist_ok=True)
    mp = os.path.join(dest, "manifest.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"已写 {mp}")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("\n提示：正文在 " + src + "（data/ 下，已 gitignore，不入库）")
    print("下一步：拆书流水线产出 books/%s/index.html，再把 metrics 回填。" % args.slug)


if __name__ == "__main__":
    main()
