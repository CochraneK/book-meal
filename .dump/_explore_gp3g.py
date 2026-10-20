# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

BOOK = r"D:\2026\WB项目\明朝\明朝那些事儿.txt"
txt = open(BOOK, encoding="utf-8", errors="replace").read()
print("书长", len(txt))

def ctx(kw, k=3, w=160):
    print("\n########", kw, "命中", txt.count(kw))
    for m in list(re.finditer(re.escape(kw), txt))[:k]:
        s = max(0, m.start() - w); e = min(len(txt), m.end() + w)
        print("---", repr(txt[s:e]))

for kw in ["君父", "家国", "立嫡", "嫡长子", "长幼有序", "争国本", "国本", "三纲五常",
           "天地君亲师", "忠孝", "以孝治天下", "孝道"]:
    ctx(kw, 2)

for kw in ["最后一根稻草", "雪崩", "积重难返", "大厦将倾", "不可救药", "气数已尽", "系统"]:
    ctx(kw, 2)
