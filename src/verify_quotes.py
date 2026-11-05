# -*- coding: utf-8 -*-
"""
书内语录的原文命中门禁
======================
README「数据纪律」第 2 条：引语必须原文命中，0 命中即弃用。此前这条只写在
文档里，没人验——2026-11-05 复核发现 66 条里有 2 条被改写了词序/加了字
（姚广孝「愿送大王一顶白帽子」、朱由检「自去冠冕，以发覆面」），都偏离了
原书。本脚本把纪律变成 CI 会跑的断言。

两级口径（任一命中即通过）：
  1. 整句命中：引号内原话原样出现；
  2. 去注解命中：剥掉括号夹注后的核心句出现（兼容早期人工只记了白话正文的条目）。
原书自带的文言夹注（如「事济否」「朕与登有姻」）就写在括号里，剥离它
是为了**兼容旧数据**，不是允许改写正文——词序一变两级都命中不了。

归属核对（--strict-attribution，人工扩面时用）：定位引语所在的中文引号，
检查引号前 90 字内有没有「说话人 + 说道/答道/道」这类直接前缀。默认不做
硬校验，因为诗句、遗言、民间歌谣本来就没有「某某说道」前缀。
**自动抽取归属不可靠**：原文多为「A 对 B 说：…」，正则容易把 B 当成说话人
（2026-11-05 实测 15 条自动候选里 13 条归属错），所以本脚本只验「原文命中」，
绝不据此自动往库里加语录。

用法：
    python src/verify_quotes.py                      # 结构校验 + 原文命中（有 TXT 时）
    python src/verify_quotes.py --strict-attribution # 额外打印归属证据
    python src/verify_quotes.py --stats              # 打印覆盖率 Top 缺口
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
QUOTES = BASE / "data" / "character_quotes.json"
DATA = BASE / "data" / "data.json"
SOURCE = BASE / "明朝那些事儿.txt"


def norm(s: str) -> str:
    """只统一空白与标点形态，绝不改字词——保证「命中」是字面命中。"""
    s = re.sub(r"\s+", "", s)
    table = {
        "“": '"', "”": '"', "「": '"', "」": '"', "‘": "'", "’": "'",
        "，": ",", "。": ".", "！": "!", "？": "?", "：": ":", "；": ";",
        "（": "(", "）": ")",
    }
    return "".join(table.get(ch, ch) for ch in s)


def core(s: str) -> str:
    """剥掉括号夹注，只留白话正文。"""
    return re.sub(r"[（(][^）)]*[）)]", "", s).strip()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="校验书内语录的原文命中与结构")
    ap.add_argument("--strict-attribution", action="store_true",
                    help="额外打印每条引语的说话人前缀证据")
    ap.add_argument("--stats", action="store_true", help="打印覆盖率缺口 Top 20")
    args = ap.parse_args(argv)

    quotes = load_json(QUOTES)
    entries = {k: v for k, v in quotes.items() if not k.startswith("_")}
    data = load_json(DATA)
    names = {c["name"] for c in data.get("characters", [])}
    aliases = {}
    for c in data.get("characters", []):
        for a in (c.get("aliases") or []):
            if a:
                aliases.setdefault(a, c["name"])

    problems = []

    # ---- 结构校验：不依赖原文，CI 干净 checkout 也能跑 ----
    if "_comment" not in quotes:
        problems.append("缺少 _comment（说明数据来源与核对口径）")
    for k, v in entries.items():
        if not isinstance(v, str) or not v.strip():
            problems.append("%s：语录不是非空字符串" % k)
        elif k not in names:
            problems.append("%s：实体表里没有这个人（幽灵人物卡）" % k)

    print("书内语录 %d 人 · 实体表 %d 人" % (len(entries), len(names)))

    # ---- 原文命中：仅当本地有原著 TXT ----
    if not SOURCE.is_file():
        print("[skip] 原著 TXT 未入库（版权），跳过原文命中校验；"
              "本机有 TXT 时会自动启用完整校验")
    else:
        raw = norm(SOURCE.read_text(encoding="utf-8", errors="replace"))
        hit_exact = hit_core = 0
        for k, v in entries.items():
            if norm(v) in raw:
                hit_exact += 1
                continue
            c = core(v)
            if c and norm(c) in raw:
                hit_core += 1
                continue
            problems.append("%s：原文 0 命中（整句 / 去注解均未找到）→ %s" % (k, v[:60]))
        print("原文命中：整句 %d · 去注解 %d · 失败 %d" %
              (hit_exact, hit_core, len(entries) - hit_exact - hit_core))

        if args.strict_attribution:
            print("\n归属前缀证据（引号前 90 字）：")
            # 必须用「已验证命中的整句」在归一化原文里定位；用 core() 的前
            # 12 字会定位到前一个引号（原书括号夹注被剥掉后字面就不连续了）。
            nflat = norm(SOURCE.read_text(encoding="utf-8", errors="replace"))
            for k, v in entries.items():
                i = nflat.find(norm(v))
                if i < 0:
                    i = nflat.find(norm(core(v)))
                if i < 0:
                    print("  %-10s [定位失败]" % k)
                    continue
                l = nflat.rfind('"', 0, i + 1)
                pre = nflat[max(0, l - 90):l] if l >= 0 else nflat[max(0, i - 90):i]
                surf = [k] + [a for a, canon in aliases.items() if canon == k]
                ok = any(re.search(re.escape(s) + r"[^。！？]{0,30}(?:说道|答道|喝道|道|曰|说)", pre)
                         for s in surf if len(s) >= 2)
                # 无前缀不等于错：诗句、遗言、承前省略主语（「他…说」）都合法。
                print("  %-10s %s  …%s" %
                      (k, "✓ 人名前缀" if ok else "· 未见人名前缀（代词/诗句/遗言）", pre[-46:]))

    if args.stats:
        chars = sorted(data.get("characters", []),
                       key=lambda c: -len(c.get("chapters") or []))
        missing = [c for c in chars if c["name"] not in entries][:20]
        print("\n覆盖章节最多但仍无语录的 Top 20（人工考据队列）：")
        for c in missing:
            print("  %-12s %3d 章" % (c["name"], len(c.get("chapters") or [])))

    if problems:
        print("\n[FAIL] %d 个问题：" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("\n[OK] 语录数据纪律校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
