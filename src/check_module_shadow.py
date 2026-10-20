# -*- coding: utf-8 -*-
"""巡检：仓库内不得存在会遮蔽 Python 标准库模块的 .py 文件。

背景（2026-10-20 事故）：CI 以 `python .dump/_browser_check.py` 这类方式运行脚本时，
Python 会把**脚本所在目录**放进 sys.path[0]。若该目录下有与标准库同名的 .py，就会被
优先导入。`.dump/_bisect.py`（实为一份 LaTeX 排版测试脚本，内容与 bisect 无关）正是
这样遮蔽了 C 扩展模块 `_bisect`，使 `import random` 内部的 `from _bisect import *`
命中它并去调 `E:\\tex\\tectonic.exe`，导致 CI 全线崩溃——而该脚本从未被显式调用过，
**仅仅存在于同目录就足以破坏任何 Python 进程的启动**。

因此这条巡检必须在 CI 早期执行：任何命中都返回 1。
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# papers_pilot 与 .dump/git-sync 是独立 git 仓库，不属于本仓巡检范围
SKIP_DIRS = {".git", "papers_pilot", "git-sync", "node_modules", "__pycache__", ".ci"}


def find_shadows(root: Path):
    stdlib = set(sys.stdlib_module_names)
    hits = []
    for p in root.rglob("*.py"):
        if set(p.parts) & SKIP_DIRS:
            continue
        if p.stem in stdlib:
            hits.append(p)
    return sorted(hits)


def main() -> int:
    hits = find_shadows(BASE)
    if not hits:
        print("[check_module_shadow] OK：无遮蔽标准库模块的文件")
        return 0
    print("[check_module_shadow] FAIL：以下文件会遮蔽标准库模块：", file=sys.stderr)
    for p in hits:
        print("  %s -> %s" % (p.relative_to(BASE), p.stem), file=sys.stderr)
    print(
        "\n重命名该文件（加项目专属前缀即可），或加入 .gitignore。\n"
        "详见 docs/add_a_book.md 与 src/check_module_shadow.py 顶部注释。",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
