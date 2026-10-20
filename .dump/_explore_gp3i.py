# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md
BOOK = r"D:\2026\WB项目\明朝\明朝那些事儿.txt"
txt = open(BOOK, encoding="utf-8", errors="replace").read()

cands = [
 "如果再背上一个庶子的名分",
 "我修改了记录，所以我湮灭了证据",
 "史云：明朝亡于党争。我云：党争，起于此时。",
 "一片亡国之象",
 "让我们看看现在的大明王朝的五个关键词",
 "知遇之恩",
 "门生",
 "座主",
 "投桃报李",
 "礼尚往来",
 "报恩",
 "人情",
 "义气",
 "兄弟义气",
 "只有兄弟义气是最重要的",
 "为了兄弟义气",
 "干儿子",
 "认贼作父",
 "恩威并施",
 "施恩",
]
for c in cands:
    print("%3d  %s" % (md.hit_text(c), c))

def ctx(kw, k=2, w=180):
    print("\n########", kw, "命中", txt.count(kw))
    for m in list(re.finditer(re.escape(kw), txt))[:k]:
        s = max(0, m.start() - w); e = min(len(txt), m.end() + w)
        print("---", repr(txt[s:e]))

for kw in ["干儿子", "知遇之恩", "门生", "座主"]:
    ctx(kw, 2)
