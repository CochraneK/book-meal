# -*- coding: utf-8 -*-
import sys, collections
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

rels = md.relations()
kin = [r for r in rels if r.get("category") == "亲属"]

SENIOR = ["祖", "父", "母", "叔", "伯", "舅", "姑", "姨", "翁", "岳"]
JUNIOR = ["子", "孙", "侄", "甥", "婿", "媳"]
FLAT = ["兄弟", "兄妹", "姐弟", "姐妹", "夫妻", "亲家", "内弟", "大舅子", "妹夫", "妻", "兄", "弟", "姐", "妹"]

def cls(t):
    t = t or ""
    ps = min([t.find(w) for w in SENIOR if w in t] or [999])
    pj = min([t.find(w) for w in JUNIOR if w in t] or [999])
    pf = min([t.find(w) for w in FLAT if w in t] or [999])
    if ps < 999 and pj < 999:
        return ("down" if ps < pj else "up")
    if pf < 999:
        return "flat"
    if ps < 999:
        return "senior_only"
    if pj < 999:
        return "junior_only"
    return "unknown"

buckets = collections.defaultdict(list)
for r in kin:
    buckets[cls(r.get("rel"))].append(r.get("rel"))
for k, v in buckets.items():
    print("==", k, len(v))
    print("   ", collections.Counter(v).most_common(30))
