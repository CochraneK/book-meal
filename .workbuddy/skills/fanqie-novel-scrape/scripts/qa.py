# -*- coding: utf-8 -*-
"""
抓取结果自检
============
抓完之后跑一遍，确认没有残留乱码、没有空章、没有异常短章。

用法
----
    python qa.py <书目录>
    python qa.py data/riye --min 300
    python qa.py data/riye --strict      # 缺章也算失败（整本抓完后用）

检查项
------
1. `chapters/NNNN.txt` 覆盖率（对有正文的章节而言）
2. 每个文件的 PUA 残留数（必须为 0）
3. 字数分布：最短/最长/均值；零星短章只提示，占比 >20% 判系统性截断
4. 标题行是否缺失
5. meta.jsonl 里 status 分布（缺章默认只提示，--strict 才失败）

退出码：0 通过；1 有问题；2 目录结构不对。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_deobf  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="检查番茄抓取结果")
    ap.add_argument("dir", help="fanqie.py 的 --out 目录")
    ap.add_argument("--min", type=int, default=300, help="可疑短章阈值（字符）")
    ap.add_argument("--strict", action="store_true",
                    help="把「缺章」也当失败（默认只提示，因为分段试抓本就会有缺口）")
    args = ap.parse_args()

    d = os.path.abspath(args.dir)
    chap = os.path.join(d, "chapters")
    if not os.path.isdir(chap):
        print(f"✗ 找不到 {chap}")
        sys.exit(2)

    files = sorted(f for f in os.listdir(chap) if re.fullmatch(r"\d{4}\.txt", f))
    if not files:
        print("✗ chapters/ 下没有 NNNN.txt")
        sys.exit(2)

    sizes, residue, no_title = [], [], []
    for f in files:
        t = open(os.path.join(chap, f), encoding="utf-8").read()
        body = t.strip()
        sizes.append((f, len(body)))
        r = font_deobf.residue(body)
        if r:
            residue.append((f, r))
        if not body.splitlines() or not body.splitlines()[0].strip():
            no_title.append(f)

    total = sum(s for _, s in sizes)
    nums = [s for _, s in sizes]
    short = [(f, s) for f, s in sizes if s < args.min]

    print(f"目录：{d}")
    print(f"章节文件：{len(files)} 个")
    print(f"正文合计：{total} 字   最短 {min(nums)} / 最长 {max(nums)} / 均值 {total // len(nums)}")

    ok = True
    warned = False
    if residue:
        ok = False
        print(f"✗ PUA 残留：{len(residue)} 个文件，例 {residue[:5]}")
    else:
        print("✓ PUA 残留：0")

    if short:
        # 零星短章可能本就如此；占比过高才是系统性截断（付费墙/选择器失效）
        systemic = len(short) > max(3, int(0.2 * len(files)))
        if systemic:
            ok = False
            print(f"✗ 偏短章节过多（<{args.min} 字）：{len(short)}/{len(files)}，例 {short[:5]}")
            print("  八成是撞上付费墙或正文容器选择器变了，先看 meta.jsonl 的 status。")
        else:
            warned = True
            print(f"⚠ 零星偏短章节（<{args.min} 字）：{len(short)} 个，例 {short[:5]}")
    else:
        print(f"✓ 无偏短章节（阈值 {args.min}）")

    if no_title:
        warned = True
        print(f"⚠ 缺标题行：{no_title[:5]}")
    else:
        print("✓ 标题行齐备")

    mp = os.path.join(d, "meta.jsonl")
    if os.path.exists(mp):
        rows = [json.loads(l) for l in open(mp, encoding="utf-8")]
        stat = {}
        for r in rows:
            stat[r.get("status", "?")] = stat.get(r.get("status", "?"), 0) + 1
        print(f"meta.jsonl：{len(rows)} 条  status={stat}")
        missing = [r["n"] for r in rows if r.get("status") == "missing"]
        if missing:
            hint = "（--strict 视为失败）" if not args.strict else ""
            warned = True
            print(f"⚠ 缺章：{len(missing)} 个，例 {missing[:10]} {hint}")
            print("  说明：分段/试抓本就会留缺口；若整本抓完仍有缺章，才需要复查。")
            if args.strict:
                ok = False
    else:
        print("（无 meta.jsonl，跳过状态统计）")

    merged = [f for f in os.listdir(d) if f.endswith(".txt")]
    print(f"合并文件：{merged}")
    if not ok:
        verdict = "存在问题，请查上面 ✗"
    elif warned:
        verdict = "基本正常（有提示项，逐条看 ⚠）"
    else:
        verdict = "全绿 ✓"
    print("结论：" + verdict)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
