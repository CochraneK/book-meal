# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

BOOK = r"D:\2026\WB项目\明朝\明朝那些事儿.txt"
txt = open(BOOK, encoding="utf-8", errors="replace").read()

cands = [
 "影响了无数人的一生，以及大明王朝的国运，而这件事情，在历史上有个专用名词",
 "立嫡不立长",
 "相当于皇帝的家规",
 "长幼有序",
 "我没有嫡子",
 "争国本",
 "苟延残喘的骆驼，只等生命中那最后一根稻草",
 "大厦将倾，独木难支",
 "上天给元朝的最后一根稻草终于压了下来",
 "连锁反应",
 "牵一发",
 "多米诺",
 "覆灭",
 "亡国",
 "党争",
 "名分",
 "大礼议",
 "本生父母",
 "继嗣",
 "过继",
 "认祖归宗",
 "侄子",
 "我的三个儿子一起封王",
 "祖训",
 "家规",
 "国之根本",
 "根本",
]
for c in cands:
    print("%3d  %s" % (md.hit_text(c), c))

def ctx(kw, k=2, w=200):
    print("\n########", kw, "命中", txt.count(kw))
    for m in list(re.finditer(re.escape(kw), txt))[:k]:
        s = max(0, m.start() - w); e = min(len(txt), m.end() + w)
        print("---", repr(txt[s:e]))

for kw in ["名分", "连锁", "一环", "崩", "亡国", "党争"]:
    ctx(kw, 2)
