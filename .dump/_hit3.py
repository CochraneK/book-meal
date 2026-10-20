# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r"d:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

cands = [
    "家国同构", "国是家的放大", "家是最小的国，国是最大的家",
    "父母官", "君父", "君父之国", "列祖列宗", "祖训", "祖宗之法",
    "皇子", "太子", "立储", "嫡长子继承制", "兄终弟及", "父死子继",
    "一人得道", "皇家", "宗法", "宗族", "家法", "名分",
    "君君臣臣", "君臣父子", "父为子纲", "孝悌",
    "一人得道鸡犬升天",
]
hits = md.hit_any(cands)
out = ["--- unigram/kw ---"]
for k in sorted(hits, key=lambda x: -hits[x]):
    out.append("%-14s %d" % (k, hits[k]))

# 候选长句（本书里可能出现的叙述句），逐条逐字命中
sent = [
    "这套逻辑，就是皇权",
    "在中国古代，家与国是一回事",
    "皇位继承",
    "嫡长子",
    "父传子，家传长",
]
out.append("--- long sentences ---")
for s in sent:
    out.append("%-20s %d" % (s, md.hit_text(s)))

open(r"d:\2026\WB项目\明朝\.dump\_hit3.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
