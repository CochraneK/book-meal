# -*- coding: utf-8 -*-
"""把 out/ 下的报告产物同步到发布平台（书库门户），并刷新 books/<id>/manifest.json。

背景
----
本工程（拆书）产单文件报告 ``out/<id>.html``，长期 harder-link 到发布平台
``book-meal``（本市另一目录）的 ``books/<id>/index.html``。这一步原先靠手工 ``cp``，
再手改 manifest 里的 ``updated`` 字段——漏改一次，门户卡片就会显示旧日期。
本脚本把「拷产物 + 刷清单」合成一条命令，并把**内容字段的唯一真源**收敛到本工程。

字段分工（重要）
--------------
+-----------------------------------+----------------------------------------------+
| 字段                              | 来源                                         |
+===================================+==============================================+
| title/author/kind/desc/accent/    | 本工程 ``data/<id>/manifest.json``            |
| metrics/chapters/chars            | （由 src/build_manifest.py 从 config + data 派生）|
+-----------------------------------+----------------------------------------------+
| order/glyph/subtitle/note/external| **平台专有**展示字段：已有则原样保留，          |
|                                   | 缺失才补默认值（glyph 缺省取书名首字）        |
+-----------------------------------+----------------------------------------------+
| report/updated                    | 本脚本写恒定值 index.html / 今天              |
+-----------------------------------+----------------------------------------------+

这样做的好处：内容元数据不会被平台侧手改悄悄带偏（每次同步都以本工程为准），
排序 / 字形 / 副标题这类纯排版字段又不会被同步抹掉。

用法::

    python src/publish_books.py                # 同步全部可发布书目
    python src/publish_books.py tiancai        # 只同步指定书
    python src/publish_books.py --check        # 只比对不一致项，不写任何文件
    python src/publish_books.py --platform X   # 指定平台仓库根目录

默认平台目录 = 本工程的父目录（即站点的仓库根，门户 index.html 与 books/ 所在处）；
可用环境变量 ``BOOK_PLATFORM`` 或 ``--platform`` 覆盖。
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 平台根目录 = 本工程的父目录。
# 2026-10-21 两仓合并：本工程作为 teardown/ 子目录并入 book-meal 仓库，
# 门户 index.html 与 books/<id>/ 都在同一仓库里，因此父目录就是平台根。
# 合并前本工程与平台仓是同级目录，那时默认路径写的是 ../明朝。
DEFAULT_PLATFORM = os.path.dirname(BASE)

# 平台专有字段：同步时必须原样保留（缺失时才按规则补）
PLATFORM_ONLY = ("order", "glyph", "subtitle", "note", "external")


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# meta.generated 是每次构建都会刷新的时间戳（形如 "generated":"2026-10-21T16:53:22"）。
# 比对必须抹掉它：它不是内容变化，而「重跑了一遍构建但什么都没改」在我们的
# 工作流里天天发生——尤其 CI 里总是先构建再检查，不抹掉这一步会每次都失败。
_GENERATED_RE = re.compile(rb'"generated":"[^"]*"')


def canonical_digest(data: bytes) -> str:
    """产物比对用的摘要：忽略 generated 时间戳，只反映真正的内容变化。

    写入平台时复制的仍是原文件（含最新时间戳），归一化只影响「要不要复制」的判断。
    """
    return digest(_GENERATED_RE.sub(b"", data))


def publishable_books(cfg):
    """返回需要同步的书目 [(id, cfg)]。

    排除两类：
      - external（如《明朝那些事儿》，它的产物就活在平台仓里，本工程不拥有它）；
      - missing（原书文本缺失，只有一份占位 manifest）。
    """
    out = []
    for bid, b in (cfg.get("books") or {}).items():
        if b.get("external") or b.get("missing"):
            continue
        out.append((bid, b))
    return out


def build_manifest(bid, local_man, cfg_entry, old_platform, today):
    """合成平台侧 manifest：内容字段取本工程，平台专有字段取现有值。"""
    src = dict(local_man or {})
    man = {
        "id": bid,
        "title": src.get("title") or cfg_entry.get("title") or bid,
        "author": src.get("author") or cfg_entry.get("author") or "",
        "kind": src.get("kind") or cfg_entry.get("kind") or "other",
        "desc": src.get("desc") or cfg_entry.get("desc") or "",
        "accent": src.get("accent") or cfg_entry.get("accent") or "#8c4a2f",
        "metrics": src.get("metrics") or {},
        "chapters": src.get("chapters"),
        "report": "index.html",
        "updated": today,
    }
    # 平台专有展示字段：先继承旧值，缺的再补默认
    old = old_platform or {}
    for key in PLATFORM_ONLY:
        if key in old and old[key] not in (None, ""):
            man[key] = old[key]
    man.setdefault("order", 99)
    man.setdefault("glyph", (man["title"] or bid)[:1])
    man.setdefault("subtitle", "")
    man.setdefault("note", "")
    man.setdefault("external", False)
    return man


def main(argv=None):
    ap = argparse.ArgumentParser(description="同步报告产物与 manifest 到发布平台")
    ap.add_argument("books", nargs="*", help="只同步指定书目 id（默认全部可发布书目）")
    ap.add_argument("--platform", default=None, help="平台仓库根目录（默认本工程的父目录）")
    ap.add_argument("--check", action="store_true", help="只比对不落盘，有差异返回 1")
    args = ap.parse_args(argv)

    platform_root = os.path.abspath(
        args.platform or os.environ.get("BOOK_PLATFORM") or DEFAULT_PLATFORM
    )
    books_dir = os.path.join(platform_root, "books")
    cfg = load_json(os.path.join(BASE, "config.json"), {})
    today = datetime.date.today().isoformat()

    if not os.path.isdir(books_dir):
        print("[error] 平台 books/ 目录不存在：%s" % books_dir)
        print("        用 --platform 指定正确的平台仓库根目录")
        return 2

    targets = publishable_books(cfg)
    if args.books:
        wanted = set(args.books)
        unknown = wanted - {bid for bid, _ in targets}
        if unknown:
            print("[error] 未知书目：%s" % "、".join(sorted(unknown)))
            return 2
        targets = [t for t in targets if t[0] in wanted]

    changed_copy, changed_manifest, problems, rows = [], [], [], []

    for bid, entry in targets:
        report_name = entry.get("report") or (bid + ".html")
        src_path = os.path.join(BASE, "out", report_name)
        local_man = load_json(os.path.join(BASE, "data", bid, "manifest.json"))
        dest_dir = os.path.join(books_dir, bid)
        dest_html = os.path.join(dest_dir, "index.html")
        dest_man = os.path.join(dest_dir, "manifest.json")

        if not os.path.isfile(src_path):
            problems.append("%s：产物不存在 %s（先跑构建）" % (bid, src_path))
            continue
        if not local_man:
            problems.append("%s：缺少本地 data/%s/manifest.json（先跑 src/build_manifest.py）" % (bid, bid))
            continue

        old_man = load_json(dest_man)
        new_man = build_manifest(bid, local_man, entry, old_man, today)
        src_bytes = read_bytes(src_path)

        # 1) 产物是否同步（按内容比对，不看 mtime；忽略构建时间戳）
        same_html = (
            os.path.isfile(dest_html)
            and canonical_digest(read_bytes(dest_html)) == canonical_digest(src_bytes)
        )
        # 2) manifest 是否会变（忽略 _order 这类门户内部计算字段）
        same_man = False
        if old_man:
            same_man = {k: v for k, v in old_man.items() if not k.startswith("_")} == new_man

        rows.append((bid, len(src_bytes), "same" if same_html else "COPY",
                     "same" if same_man else "UPDATE", new_man))

        if not args.check and not same_html:
            os.makedirs(dest_dir, exist_ok=True)
            with open(dest_html, "wb") as f:
                f.write(src_bytes)
            changed_copy.append(bid)
        if not args.check and not same_man:
            os.makedirs(dest_dir, exist_ok=True)
            with open(dest_man, "w", encoding="utf-8", newline="\n") as f:
                json.dump(new_man, f, ensure_ascii=False, indent=2)
                f.write("\n")
            changed_manifest.append(bid)

    for bid, size, html_state, man_state, man in rows:
        m = man.get("metrics") or {}
        print("  %-8s %7.2f MB  产物=%-4s 清单=%-6s %s人/%s事/%s关系 | %s章 | updated=%s"
              % (bid, size / 1048576, html_state, man_state,
                 m.get("characters"), m.get("events"), m.get("relations"),
                 man.get("chapters"), man.get("updated")))

    for p in problems:
        print("[warn] " + p)

    if args.check:
        dirty = [b for b, _, hs, ms, _ in rows if hs != "same" or ms != "same"]
        if problems:
            print("\n[check] 失败：%d 个问题（见上）" % len(problems))
            return 1
        if dirty:
            print("\n[check] 平台副本落后：%s" % "、".join(dirty))
            return 1
        print("\n[check] OK：%d 本书产物与清单均与本工程一致" % len(rows))
        return 0

    if problems:
        print("\n[done] 部分同步：拷贝 %d / 清单 %d，跳过 %d"
              % (len(changed_copy), len(changed_manifest), len(problems)))
        return 1
    print("\n[done] 拷贝 %d 份产物，更新 %d 份清单 → %s"
          % (len(changed_copy), len(changed_manifest), books_dir))
    print("       别忘了在平台仓重跑 src/build_hub.py 重建门户")
    return 0


if __name__ == "__main__":
    sys.exit(main())
