# -*- coding: utf-8 -*-
"""
拆书流水线 · 阶段① 拆章
======================
把小说 TXT 按章节标题切成结构化章节，输出 data/<book>/chapters.json。

支持两种标题格式（config.json 的 heading 字段指定）：
  numbered —— 「1.真实」式：行首数字+点+标题（《天才基本法》，224 章）
  plain    —— 裸标题式：单独一行短标题，正文行以全角空格缩进（《我在废土世界扫垃圾》，439 章）

plain 模式的标题判定规则（四条同时满足）：
  1. 不以空格/全角空格/Tab 开头（正文都缩进）
  2. 长度 ≤ 20 且不以句末标点结尾（。！？，…—）
  3. 不含「：“」（排除对话行）
  4. 上一行为空行，且下一行以全角空格开头（正文缩进）
→ 该规则在本书实测可滤掉卷首的预收文简介，第一条真实标题为「新工作」。

输出字段：
  key           唯一键，如 tiancai-c1 / feitu-c437
  book          书籍 id（tiancai / feitu）
  chapter_index 全书章序号（从 1 起，含番外）
  chapter_title 章标题（plain 模式即原行；numbered 模式去掉「N.」前缀）
  heading_raw   原始标题行
  body          正文（去首尾空行）
  chars         正文字数
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(BASE, "config.json")

FW = "\u3000"
END_PUNCT = "\u3002\uff01\uff1f\uff0c\u2026\u2014"
NUM_RE = re.compile(r"^(\d+)\.(.+)$")


def is_plain_heading(lines, i):
    """plain 模式第 i 行（0 起）是否为章标题。"""
    s = lines[i].strip()
    if not s or len(s) > 20:
        return False
    if s[0] in (" ", FW, "\t"):
        return False
    if s[-1] in END_PUNCT:
        return False
    if "\uff1a\u201c" in s:  # ：「 排除对话
        return False
    prev = lines[i - 1].strip() if i > 0 else ""
    nxt = lines[i + 1] if i + 1 < len(lines) else ""
    return prev == "" and nxt.startswith(FW)


def split_numbered(lines):
    """numbered 模式：返回 [(行号, 标题)]。"""
    out = []
    for i, ln in enumerate(lines):
        m = NUM_RE.match(ln.strip())
        if m:
            out.append((i, m.group(2).strip()))
    return out


def split_plain(lines):
    """plain 模式：返回 [(行号, 标题)]。"""
    return [(i, lines[i].strip()) for i in range(len(lines)) if is_plain_heading(lines, i)]


def build(book_id, book_cfg):
    src = os.path.join(BASE, book_cfg["file"])
    if not os.path.exists(src):
        raise FileNotFoundError(f"找不到源文件：{src}")
    # utf-8-sig 去掉 BOM
    raw = open(src, encoding="utf-8-sig").read()
    lines = raw.split("\n")

    if book_cfg["heading"] == "numbered":
        heads = split_numbered(lines)
    else:
        heads = split_plain(lines)

    if not heads:
        raise RuntimeError(f"{book_id} 未识别到任何章节标题，请检查 heading 模式")

    chapters = []
    for n, (line_no, title) in enumerate(heads, 1):
        start = line_no + 1
        end = heads[n][0] if n < len(heads) else len(lines)
        body_lines = lines[start:end]
        while body_lines and body_lines[0].strip() == "":
            body_lines.pop(0)
        while body_lines and body_lines[-1].strip() == "":
            body_lines.pop()
        body = "\n".join(body_lines)
        # 修正误切：正文为空且标题以句末标点结尾的「N.……」行（如「109.完成…习题。」），
        # 是正文里的清单行而非章标题 → 并回上一章正文
        if not body.strip() and chapters and title[-1] in END_PUNCT:
            chapters[-1]["body"] += "\n" + lines[line_no].strip()
            chapters[-1]["chars"] = len(chapters[-1]["body"].replace("\n", ""))
            continue
        chapters.append({
            "key": f"{book_id}-c{n}",
            "book": book_id,
            "chapter_index": n,
            "chapter_title": title,
            "heading_raw": lines[line_no].strip(),
            "body": body,
            "chars": len(body.replace("\n", "")),
        })

    out_dir = os.path.join(BASE, "data", book_id)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "chapters.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=1)

    total = sum(c["chars"] for c in chapters)
    print(f"[done] {book_cfg['title']}（{book_id}）：{len(chapters)} 章，正文共 {total} 字，"
          f"平均 {total // len(chapters)} 字/章")
    print(f"       首章「{chapters[0]['chapter_title']}」 末章「{chapters[-1]['chapter_title']}」")
    # 异常短的章（可能是误切）
    tiny = [c["key"] for c in chapters if c["chars"] < 200]
    if tiny:
        print(f"       [warn] 正文 <200 字的章：{tiny}")
    return chapters


def main():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for bid, bc in cfg["books"].items():
        if only and bid != only:
            continue
        build(bid, bc)


if __name__ == "__main__":
    main()
