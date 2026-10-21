"""版权合规巡检：确认仓库里没有混进原书全文。

三条闸，各管一类漏法：

1. **名单**：已知的三本原著文件名，以及含正文的抽取文件 chapters.json。
   这是第一道，也是最便宜的一道。

2. **体积（仅 .txt）**：任何超过 200KB 的 .txt 都可疑。
   合法的 .txt 只有 requirements.txt 这类几行的文本文件；
   .json 不参与这条—— data.json 本身就有 2.7MB 的合法数据，用体积会误伤。

3. **内容特征**：扫描每个被跟踪的 json，若任何字符串值超过 ``MAX_STR``，
   判为疑似正文。脱敏后的五元组数据里不会有上万字的连续字符串，
   而原书正文会以整章 body 的形式出现。这条能在「忘了写 gitignore、
   换了个文件名」的情况下仍拦得住。

用法::

    python tests/check_copyright.py          # 有命中返回 1

退出码：0 = 通过，1 = 发现疑似全文（CI 会失败）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 已知受版权保护的原文与含正文的中间产物（小写比对）
NAME_PATTERNS = (
    "chapters.json",
    "明朝那些事儿",
    "天才基本法",
    "我在废土世界扫垃圾",
)

TXT_SIZE_LIMIT = 200 * 1024  # 200 KB，合法的 .txt 远小于此
MAX_STR = 8000  # 单个字符串值上限：正文会以整章 body 出现，远超此数

# data/ 是工程数据区，不该出现能装下大段正文的文件类型。
#
# 这条规则的来历：swdw 的正文被按章拆成 data/swdw/chapters/0001.txt …0160.txt，
# 文件名是纯数字、单个体积才 7KB——名单匹配不到、体积闸也够不着，
# 2026-10-21 仓库合并时差点整目录提交上去。用「位置 + 扩展名黑名单」兜底，
# 比猜文件名和猜体积都可靠。
#
# 为什么用黑名单而不是「只允许 .json」：data/ 下确实有正当的非 json 文件
# —— feitu/_canon.md（抽取口径表）、swdw/analysis/_t.js（KG 快照）——
# 一刀切会逼人去放宽白名单，反而更危险。要拦的是「能装正文的载体」。
DATA_DIR_FORBIDDEN_EXT = (".txt", ".htm", ".html", ".xml", ".epub", ".mobi")

# data/ 下非 json 的工程文件（md/js 等）体积上限。正常都远小于此。
DATA_FILE_SIZE_LIMIT = 1024 * 1024  # 1 MB


def tracked_files():
    # **必须关掉 core.quotepath**。否则 git 会把非 ASCII 路径输出成
    # "\345\244\251\346\211\215..." 这种八进制转义并加引号，结果是：
    #   - 名单比对永远匹配不到（路径里没有「天才基本法」几个字）
    #   - os.path.isfile() 也找不到文件，被 continue 静默跳过
    # 也就是说，不关掉它，含中文名的原文能大摇大摆进仓库而这道检查一声不吭。
    # （合并前 CI 里的 `git ls-files | grep '明朝那些事儿'` 正是这个毛病。）
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files"],
        cwd=BASE, capture_output=True, text=True, check=True,
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def check_names(files):
    hits = []
    for path in files:
        low = path.lower()
        for pat in NAME_PATTERNS:
            if pat.lower() in low:
                hits.append(f"{path}  ← 命中名单「{pat}」")
                break
    return hits


def check_txt_size(files):
    hits = []
    for path in files:
        if not path.lower().endswith(".txt"):
            continue
        full = os.path.join(BASE, path)
        if not os.path.isfile(full):
            continue
        if os.path.getsize(full) > TXT_SIZE_LIMIT:
            hits.append(f"{path}  ← {os.path.getsize(full)} B，超过 {TXT_SIZE_LIMIT} B")
    return hits


def _scan_strings(node, path, hits):
    """深度遍历，找出超长字符串。命中即记一笔。"""
    if isinstance(node, str):
        if len(node) > MAX_STR:
            hits.append(f"{path}  ← 存在 {len(node)} 字符的字符串值")
        return True
    if isinstance(node, dict):
        for key, val in node.items():
            if not _scan_strings(val, path, hits):
                return False
        return True
    if isinstance(node, list):
        for val in node:
            if not _scan_strings(val, path, hits):
                return False
        return True
    return True


def check_data_dir(files):
    """data/ 目录树内：禁止能装正文的扩展名，非 json 文件还查体积。

    json 不查体积—— data.json 本身就有 2.7MB 的合法数据，查了会天天误报；
    它的安全性由 check_json_content 的字符串长度闸负责。
    """
    hits = []
    for path in files:
        parts = path.split("/")
        if "data" not in parts[:-1]:
            continue
        full = os.path.join(BASE, path)
        if not os.path.isfile(full):
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext in DATA_DIR_FORBIDDEN_EXT:
            hits.append(
                f"{path}  ← data/ 下不该有 {ext} 文件（原书正文的常见载体）"
            )
            continue
        if ext != ".json" and os.path.getsize(full) > DATA_FILE_SIZE_LIMIT:
            hits.append(
                f"{path}  ← data/ 下的 {ext or '无扩展名'} 文件达 "
                f"{os.path.getsize(full)} B，超过 {DATA_FILE_SIZE_LIMIT} B"
            )
    return hits


def check_json_content(files):
    hits = []
    for path in files:
        if not path.lower().endswith(".json"):
            continue
        full = os.path.join(BASE, path)
        if not os.path.isfile(full):
            continue
        try:
            with open(full, encoding="utf-8") as f:
                data = json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            continue  # 非 UTF-8 JSON 或已损坏，交给其他检查处理
        _scan_strings(data, path, hits)
    return hits


def main():
    files = tracked_files()
    hits = (
        check_names(files)
        + check_data_dir(files)
        + check_txt_size(files)
        + check_json_content(files)
    )

    if hits:
        print("::error::疑似含原书正文，拒绝入库：")
        for h in hits:
            print("   " + h)
        print("\n请检查 .gitignore（以及与 teardown/.gitignore 的对应关系）。")
        return 1

    print(f"版权巡检通过 ✓  已检查 {len(files)} 个被跟踪文件")
    print(f"  名单 {len(NAME_PATTERNS)} 条 · .txt 体积闸 {TXT_SIZE_LIMIT} B · 字符串长度闸 {MAX_STR} 字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
