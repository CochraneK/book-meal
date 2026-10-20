# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"d:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md
sents = [
    "国家与国家之间的关系，和人其实差不多",
    "朱元璋绝对是个好父亲、好祖父",
    "在徐寿辉的部队里，兄弟义气是为人看重的",
    "好父亲、好祖父",
    "兄弟义气",
    "兄弟单位的部队",
    "朱元璋可能不是个好君主",
]
out = []
for s in sents:
    out.append("%d\t%s" % (md.hit_text(s), s))
open(r"d:\2026\WB项目\明朝\.dump\_hit4.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
