# -*- coding: utf-8 -*-
"""探一探原文能不能抽出「金句」：带引号的对白/独白，且带说话人线索。

只是可行性探针，不产出最终数据。用完可删。
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 中文成对引号： “ ”  「 」  ‘ ’
OPENERS = "\u201c\u300c\u2018"
CLOSERS = "\u201d\u300d\u2019"

for name in ("我在废土世界扫垃圾.txt", "天才基本法.txt"):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        continue
    text = open(path, encoding="utf-8", errors="replace").read()
    print("=" * 60)
    print(name, "字符数", len(text))

    for ch, label in (("\u201c", "左双弯“"), ("\u300c", "左角「"),
                      ("\u2018", "左单弯‘"), ('"', "半角双引")):
        print(f"   {label}: {text.count(ch)}")

    # 成对引号内的内容，长度 10-90 字
    pat = "[" + OPENERS + "]([^" + CLOSERS + "]{10,90})[" + CLOSERS + "]"
    hits = re.findall(pat, text)
    print(f"   成对引号片段（10-90 字）：{len(hits)}")
    for s in hits[:8]:
        print("     · " + s[:64])

    # 带说话人线索的：引号前面 20 字内有「XX说/道/问/答」等
    say = re.findall(r"(.{0,18}?)(?:说|道|问|答|喊|低声|沉声|轻声|自语|喃喃|开口)[^。\n]{0,6}?["
                     + OPENERS + "]([^" + CLOSERS + "]{10,90})[" + CLOSERS + "]", text)
    print(f"   带「某某说」线索的：{len(say)}")
    for a, b in say[:8]:
        print(f"     · [{a.strip()[-8:]}] {b[:56]}")
