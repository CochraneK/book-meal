# -*- coding: utf-8 -*-
"""
仓库体检与非破坏归档（repo hygiene）
====================================
这个仓库同时装着「网站源码 / 生成出来的成品 / 本机私有原文 / 一次性临时产物」，
四层东西混在一个目录里，最容易让人迷失，也最容易在清理时误删。本脚本把上一轮
人工盘点的判断固化成代码，提供三件事：

  1. ``--report``   分层体检：各层体积、是否入库、可归档量；
  2. ``--archive``  把纯缓存**移动**到仓外备份区（默认 dry-run），
     同时留档 .ci 里的验收截图；可 ``--restore`` 一键回滚；
  3. ``--check``    CI 门禁：私有输入必须被 gitignore 挡住、缓存目录必须仍在
     忽略名单、真源与成品必须存在。干净 checkout 也能跑。

**设计前提**：
  - 绝不永久删除。归档是 move，不是 rm；manifest 记录原路径，随时可还原。
  - 归档目标必须在仓库之外，避免备份本身又被当成仓库内容。
  - 「本机唯一、clone 拿不到」的文件一律不进归档白名单：
    3 本原著 TXT、chapters.json（含正文）、tiancai/feitu 的 quotes.json。
  - `.dump/` 整体归档即等于备份了它内部的独立 git 仓库；`papers_pilot/` 是
    另一个无远程的独立仓库，需显式 ``--include-assets`` 才动。
  - `teardown/out/` 明确不归档：它是本机 `publish_books.py --check` 的输入，
    移走会让门禁报「产物不存在」（CI 干净 checkout 不受影响，本机受影响）。

用法：
    python src/repo_hygiene.py --report
    python src/repo_hygiene.py --check
    python src/repo_hygiene.py --archive                       # dry-run
    python src/repo_hygiene.py --archive --apply              # 真正移动
    python src/repo_hygiene.py --archive --apply --include-assets
    python src/repo_hygiene.py --restore --dest <归档目录> --apply
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DEFAULT_DEST = BASE.parent / ("_book_meal_archive_" + datetime.date.today().strftime("%Y%m%d"))
MANIFEST_NAME = "manifest.json"

# ① 真源层：改这里才有意义，绝不归档
SOURCE_PATHS = (
    "src", "web", "tests", "data", "docs", ".github/workflows",
    "teardown/src", "teardown/web", "teardown/data",
    "books", "README.md", ".gitignore", "teardown/.gitignore",
)

# ② 成品层：Pages 白名单，绝不归档（它们是发布物，不是缓存）
PRODUCT_PATHS = (
    "index.html", "standalone.html", "sw.js",
    "ming/index.html", "books/tiancai/index.html", "books/feitu/index.html",
    "books/swdw/index.html", "books/sanggan/index.html",
)

# ③ 本机私有输入：必须被 gitignore 挡住。探针路径用 --no-index 验，
#    即使 CI 干净 checkout 里文件不存在也能断言。
PRIVATE_PROBES = (
    "明朝那些事儿.txt",
    "data/chapters.json",
    "teardown/天才基本法.txt",
    "teardown/我在废土世界扫垃圾.txt",
    "teardown/data/tiancai/quotes.json",
    "teardown/data/feitu/quotes.json",
    "teardown/data/tiancai/chapters.json",
    "teardown/data/feitu/chapters.json",
    "teardown/data/swdw/chapters/0001.txt",
)

# ④ 可归档的纯缓存：必须仍在忽略名单，且都能由构建命令重建
CACHE_PROBES = (
    ".ci/probe", "_site/probe", "dist/probe", "papers_pilot/probe",
    "teardown/out/probe", "src/__pycache__/probe.pyc",
)
ARCHIVE_DIRS = (".ci", "_site", "dist", ".dump")  # 整体移走（.dump 内含一个独立 git 仓库）
ASSET_REPOS = ("papers_pilot",)                   # 无远程的独立仓库，需显式 --include-assets
PRESERVE_NOTE = ("teardown/out", "本机 publish_books.py --check 的输入，移走会让门禁变红")
SCREENSHOT_DIR = ".ci"                            # 这里面的 *.png 先单独留档

SKIP_WALK = {".git", "papers_pilot", "git-sync", "node_modules"}


def ignored(rel: str) -> bool:
    """git check-ignore --no-index：路径不存在也能判断规则是否覆盖。"""
    r = subprocess.run(["git", "check-ignore", "-q", "--no-index", rel],
                       cwd=BASE, capture_output=True)
    return r.returncode == 0


def size_of(path: Path):
    if path.is_file():
        try:
            return path.stat().st_size, 1
        except OSError:
            return 0, 0
    total = n = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
                n += 1
            except OSError:
                pass
    return total, n


def mb(v) -> str:
    return "%.1f MB" % (v / 1048576)


def iter_pycache():
    """找出仓库内所有 __pycache__，跳过独立仓库与 .git。"""
    for root, dirs, _files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in SKIP_WALK]
        p = Path(root)
        if p.name == "__pycache__":
            yield p
            dirs[:] = []


def check() -> list:
    """CI 门禁断言；返回问题列表，空列表表示通过。"""
    problems = []
    for rel in PRIVATE_PROBES:
        if not ignored(rel):
            problems.append("私有输入未被 gitignore 覆盖：%s" % rel)
    for rel in CACHE_PROBES:
        if not ignored(rel):
            problems.append("缓存目录脱离忽略名单，可能被误提交：%s" % rel)
    for rel in SOURCE_PATHS:
        if not (BASE / rel).exists():
            problems.append("真源缺失：%s" % rel)
    for rel in PRODUCT_PATHS:
        if not (BASE / rel).exists():
            problems.append("发布成品缺失：%s" % rel)
    return problems


def report() -> None:
    print("仓库：%s" % BASE)
    print("\n--- 已入库主体 ---")
    for rel in ("src", "web", "tests", "data", "books", "ming", "docs",
                "papers", "legacy", "teardown", ".workbuddy"):
        p = BASE / rel
        if p.exists():
            s, n = size_of(p)
            print("  %-14s %9s / %4d 文件" % (rel, mb(s), n))
    for rel in ("index.html", "standalone.html", "sw.js", "README.md"):
        p = BASE / rel
        if p.exists():
            print("  %-14s %9s" % (rel, mb(p.stat().st_size)))

    print("\n--- 本机私有输入（clone 拿不到，绝不归档）---")
    for rel in PRIVATE_PROBES:
        print("  %-46s %s" % (rel, "已忽略" if ignored(rel) else "★ 未忽略"))

    print("\n--- 可归档纯缓存 ---")
    total = 0
    for rel in ARCHIVE_DIRS:
        p = BASE / rel
        if p.exists():
            s, n = size_of(p)
            total += s
            print("  %-14s %9s / %4d 文件  可整体移走" % (rel, mb(s), n))
    pc = list(iter_pycache())
    ps = sum(size_of(p)[0] for p in pc)
    total += ps
    print("  %-14s %9s / %4d 目录" % ("__pycache__", mb(ps), len(pc)))
    print("  小计：%s" % mb(total))

    print("\n--- 独立 git 仓库（无远程，删除前须先备份）---")
    print("  %-20s 随 .dump/ 整体归档，无需单独列出" % ".dump/git-sync")
    for rel in ASSET_REPOS:
        p = BASE / rel
        if p.exists():
            s, n = size_of(p)
            print("  %-20s %9s / %4d 文件  需 --include-assets" % (rel, mb(s), n))

    print("\n--- 明确保留 ---")
    print("  %-20s %s" % PRESERVE_NOTE)
    print("  另外：真源层、成品层、.workbuddy/memory/、books/sanggan/ 一律不动。")


def collect_targets(dest: Path, include_assets: bool, suffix: str = ""):
    """构造移动清单 [(src, dst, kind)]；dst 一律在 dest 之下。

    重复归档时给本批次的目标名加时间戳后缀，既不覆盖上一批，
    也能让 ``--restore`` 按 manifest 逐项回滚（清理是可重复动作，不是一次性的）。
    """
    items = []
    for rel in ARCHIVE_DIRS:
        src = BASE / rel
        if src.exists():
            items.append((src, dest / "cache" / (rel.replace("/", "_") + suffix), "cache"))
    covered = tuple(ARCHIVE_DIRS) + (tuple(ASSET_REPOS) if include_assets else ())
    for i, p in enumerate(sorted(iter_pycache(), key=lambda x: str(x))):
        rel_s = str(p.relative_to(BASE)).replace("\\", "/")
        # 这些目录会被整体移走，里面的 __pycache__ 不能再单列，否则移动时 src 已不存在
        if any(rel_s == c.replace("\\", "/") or
               rel_s.startswith(c.replace("\\", "/") + "/") for c in covered):
            continue
        items.append((p, dest / "cache" / ("pycache" + suffix) /
                      ("%03d" % i) / p.name, "pycache"))
    if include_assets:
        for rel in ASSET_REPOS:
            src = BASE / rel
            if src.exists():
                items.append((src, dest / "repos" /
                              (rel.replace("/", "_") + suffix), "asset-repo"))
    return items


def archive(dest: Path, apply_: bool, include_assets: bool) -> int:
    if os.path.commonpath([str(BASE), str(dest)]) == str(BASE):
        print("[error] 归档目标必须在仓库之外：%s" % dest, file=sys.stderr)
        return 2
    mf = dest / MANIFEST_NAME
    repeat = mf.is_file()          # 允许重复归档：__pycache__ 每次跑 Python 都会再生
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = ("_" + stamp) if repeat else ""

    items = collect_targets(dest, include_assets, suffix)
    shots = sorted((BASE / SCREENSHOT_DIR).glob("*.png")) if (BASE / SCREENSHOT_DIR).is_dir() else []
    print("归档目标：%s%s" % (dest, "（追加批次 %s）" % stamp if repeat else ""))
    print("验收截图留档：%d 张 → screenshots/" % len(shots))
    for src, dst, kind in items:
        s, n = size_of(src)
        print("  [%s] %-28s %9s / %4d 文件" % (kind, src.relative_to(BASE), mb(s), n))
    if not items and not shots:
        print("\n[done] 当前没有可归档内容，无需操作。")
        return 0
    if not apply_:
        print("\n[dry-run] 未移动任何文件。确认后加 --apply 执行；回滚用 --restore。")
        return 0

    conflicts = [dst for _src, dst, _kind in items if dst.exists()]
    if conflicts:
        print("[error] 归档目标已存在，放弃以免覆盖或产生半成品：", file=sys.stderr)
        for dst in conflicts[:5]:
            print("    " + str(dst), file=sys.stderr)
        return 2

    dest.mkdir(parents=True, exist_ok=True)
    if repeat:
        manifest = json.loads(mf.read_text(encoding="utf-8"))
        manifest["updated"] = stamp
    else:
        manifest = {"created": stamp, "repo": str(BASE), "entries": []}
    shot_dir = (dest / "screenshots" / stamp) if repeat else (dest / "screenshots")
    shot_dir.mkdir(parents=True, exist_ok=True)
    for p in shots:
        shutil.copy2(p, shot_dir / p.name)
        manifest["entries"].append({"kind": "screenshot-copy",
                                    "src": str(p.relative_to(BASE)),
                                    "dst": str((shot_dir / p.name).relative_to(dest)),
                                    "bytes": p.stat().st_size, "files": 1})
    for src, dst, kind in items:
        s, n = size_of(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        manifest["entries"].append({"kind": kind,
                                    "src": str(src.relative_to(BASE)),
                                    "dst": str(dst.relative_to(dest)),
                                    "bytes": s, "files": n})
    (dest / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n[done] 已归档 %d 项 + %d 张截图，清单：%s" %
          (len(items), len(shots), dest / MANIFEST_NAME))
    print("       这是移动不是删除；确认无误后再自行删除整个归档目录。")
    print("       回滚：python src/repo_hygiene.py --restore --dest %s --apply" % dest)
    return 0


def restore(dest: Path, apply_: bool) -> int:
    mf = dest / MANIFEST_NAME
    if not mf.is_file():
        print("[error] 找不到归档清单：%s" % mf, file=sys.stderr)
        return 2
    data = json.loads(mf.read_text(encoding="utf-8"))
    movable = [e for e in data["entries"] if e["kind"] != "screenshot-copy"]
    for e in movable:
        src, dst = BASE / e["src"], dest / e["dst"]
        print("  %s → %s" % (e["dst"], e["src"]))
        if not apply_:
            continue
        if not dst.exists():
            print("    [warn] 归档里已不存在，跳过", file=sys.stderr)
            continue
        if src.exists():
            print("    [warn] 原位置已有内容，跳过以免覆盖", file=sys.stderr)
            continue
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(src))
    print("[dry-run] 未移动任何文件。加 --apply 执行。" if not apply_
          else "[done] 已回滚 %d 项" % len(movable))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="仓库分层体检与非破坏归档")
    ap.add_argument("--report", action="store_true", help="输出分层体积与归档清单")
    ap.add_argument("--check", action="store_true", help="CI 门禁：忽略边界与主体完整性")
    ap.add_argument("--archive", action="store_true", help="归档纯缓存（默认 dry-run）")
    ap.add_argument("--restore", action="store_true", help="按 manifest 回滚")
    ap.add_argument("--dest", default=str(DEFAULT_DEST), help="仓外归档目录")
    ap.add_argument("--apply", action="store_true", help="真正执行移动")
    ap.add_argument("--include-assets", action="store_true",
                    help="连无远程的独立 git 仓库一起归档（默认不动）")
    args = ap.parse_args(argv)

    if args.check:
        problems = check()
        for p in problems:
            print("  [FAIL] " + p)
        if problems:
            print("\n[FAIL] 仓库卫生检查 %d 项未通过" % len(problems))
            return 1
        print("[OK] 仓库卫生检查通过：%d 条私有输入受保护、%d 条缓存规则在位、"
              "真源与成品齐全" % (len(PRIVATE_PROBES), len(CACHE_PROBES)))
        return 0
    if args.report:
        report()
        return 0
    if args.restore:
        return restore(Path(args.dest).resolve(), args.apply)
    if args.archive:
        return archive(Path(args.dest).resolve(), args.apply, args.include_assets)

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
