# -*- coding: utf-8 -*-
"""
把「书库导航条」注入所有已发布报告（幂等 / 可校验）
==================================================
为什么是**一个后处理注入器**，而不是散到 4 条构建链里各写一遍：

  1. 本仓有 4 条互不相同的报告构建链（`src/build.py` 明书、
     `teardown/src/generate_report.py` 天才/废土、`teardown/src/build_swdw_report.py`
     天幕、私有仓 `CochraneK/sanggan` 桑乾河）。逐个改要维护 4 份同样的代码，
     且第 4 条根本不在本仓里。
  2. 所有产物都是单文件离线 HTML，导航条必须内联；构建期统一注入正好满足。
  3. `refresh-index.yml` 会在 CI 里重新生成并回写 standalone.html / ming/index.html
     / index.html，因此注入步骤必须是**可重放**的幂等命令，而不是手改进产物。

书单来自 `book_registry.load()`（books/*/manifest.json），因此新增一本书
只要放 manifest + 报告，导航条自动带它，本脚本不用改。

用法：
    python src/sync_shelf.py            # 注入 / 刷新全部产物
    python src/sync_shelf.py --check    # 只校验，有落后返回 1（CI 用）
    python src/sync_shelf.py --list     # 列出目标与相对前缀
    python src/sync_shelf.py --quiet    # 减少输出

配套：
    teardown/src/publish_books.py  拷贝产物时调 inject_shelf，本地发布不丢导航条
    .github/workflows/refresh-index.yml  重建产物后跑本脚本再回写
    .github/workflows/ci.yml            跑 --check，防止有人漏跑
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import book_registry as REG  # noqa: E402

#: 额外的「非 books/ 目录」产物：明书完整离线单文件，在站点根。
EXTRA_TARGETS = (
    ("standalone.html", "ming"),
)


def targets():
    """返回 [(相对路径, 当前书 id, 回到站点根的相对前缀)]。

    base 由产物相对仓库根的深度算出，不写死：书挪目录时不会留下死链。
    """
    out = []
    for m in REG.load(BASE / "books"):
        href = m["href"]
        if href.startswith(("http://", "https://", "//")):
            continue  # 站外书不注入
        p = Path(href)
        if p.is_absolute() or ".." in p.parts:
            continue
        depth = len(p.parts) - 1
        base = "../" * depth if depth else "./"
        out.append((href, str(m["id"]), base))
    for href, book_id in EXTRA_TARGETS:
        out.append((href, book_id, "./"))
    return out


def check_warnings(targets_list) -> list:
    """目标产物缺文件 / 统一书单为空，都属于应该让人看见的问题。"""
    warns = []
    if not REG.load(BASE / "books"):
        warns.append("统一书单为空：books/ 下没有可用的 manifest.json")
    for href, _bid, _base in targets_list:
        if not (BASE / href).is_file():
            warns.append("导航条目标产物不存在：%s" % href)
    return warns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="把统一书库导航条注入所有已发布报告")
    ap.add_argument("--check", action="store_true", help="只校验不落盘，有落后返回 1")
    ap.add_argument("--list", action="store_true", help="列出注入目标与相对前缀")
    ap.add_argument("--quiet", action="store_true", help="减少输出")
    args = ap.parse_args(argv)

    tlist = targets()
    if args.list:
        for href, bid, base in tlist:
            print("  %-34s id=%-10s base=%s" % (href, bid, base))
        print("共 %d 个产物" % len(tlist))
        return 0

    warns = check_warnings(tlist)
    for w in warns:
        print("[warn] " + w)

    stale, written, skipped = [], [], []
    for href, bid, base in tlist:
        path = BASE / href
        if not path.is_file():
            skipped.append(href)
            continue
        actual = path.read_bytes()
        expected = REG.inject_shelf(actual, bid, base)
        if expected == actual:
            if not args.quiet:
                print("  %-34s 已是最新" % href)
            continue
        stale.append(href)
        if not args.check:
            path.write_bytes(expected)
            written.append(href)
            if not args.quiet:
                print("  %-34s 已注入（+%d 字节）" % (href, len(expected) - len(actual)))

    if args.check:
        if warns or stale or skipped:
            print("\n[check] 失败：警告 %d / 落后 %d / 缺失 %d" %
                  (len(warns), len(stale), len(skipped)))
            if stale:
                print("        落后产物：%s" % "、".join(stale))
                print("        执行 python src/sync_shelf.py 刷新")
            return 1
        print("\n[check] OK：%d 个报告均带最新书库导航条" % len(tlist))
        return 0

    if warns or skipped:
        print("\n[done] 部分完成：刷新 %d，警告 %d，缺失 %d" %
              (len(written), len(warns), len(skipped)))
        return 1
    if not args.quiet:
        print("\n[done] 刷新 %d / %d 个产物（其余已是最新）" % (len(written), len(tlist)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
