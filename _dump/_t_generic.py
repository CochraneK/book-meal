# -*- coding: utf-8 -*-
"""干跑 write_generic 的 4 个修复点，不编译、不写文件，只把渲染结果打到 stdout。"""
import os
import sys

sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import write_generic as W

root = r"D:\2026\WB项目\明朝"

S = W.load_stats("museum")
sp = dict(__import__("spec_museum").SPEC)
sp["_pid"] = "museum"

print("=== museum（口径 A / events.n=0 / chapters=41）===")
s1 = W.sec1(S, sp)
s4 = W.sec4(S, sp)
s5 = W.sec5("museum", S, sp)
for tag, txt in (("sec1", s1), ("sec4", s4), ("sec5", s5)):
    print("--", tag)
    for key in ("覆盖", "口径 B", "$|S_A|$=", "fig:anchors", "fig:events", "图 \\ref"):
        if key in txt:
            i = txt.find(key)
            print("   [%s] ...%s..." % (key, txt[max(0, i - 70):i + 90].replace("\n", " ")))
print("   rho 出现形式:", [x for x in __import__("re").findall(r"\$?\\rho=[0-9.]*\$?", s1 + s5)][:4])

# --- 合成一份「口径 B + events.n>0」的底稿，验证分支 ---
Sb = {
    "corpus": {"chapters": 41, "persons": 1231, "events": 1106,
               "relations": 2324, "locations": 563},
    "vocab": [{"word": "庙", "hits": 58}],
    "anchors": [{"name": "朱元璋", "degree": 87, "chapters": 41}],
    "subset": {"method": "B: ego(4 anchors)", "n_persons": 146, "n_explicit_edges": 646,
               "mean_degree": 11.79, "rho_chapter_degree": 0.871,
               "cat_composition": [{"cat": "其他", "n": 287, "pct": 44.4}]},
    "baseline": {"n_edges": 2324, "mean_degree": 6.27,
                 "cat_composition": [{"cat": "其他", "n": 927, "pct": 39.9}]},
    "events": {"n": 3, "year_hist": [{"label": "1404", "value": 1},
                                     {"label": "1581", "value": 1},
                                     {"label": "1601", "value": 1}]},
}
spb = dict(sp)
s4b = W.sec4(Sb, spb)
s5b = W.sec5("xxx", Sb, spb)
print()
print("=== 合成（口径 B / events.n=3）===")
for tag, txt in (("sec4", s4b), ("sec5", s5b)):
    print("--", tag)
    for key in ("$|S_B|$=", "锚点自我网络", "5.3", "fig:events"):
        if key in txt:
            i = txt.find(key)
            print("   [%s] ...%s..." % (key, txt[max(0, i - 40):i + 120].replace("\n", " ")))
print("   rho 位数:", __import__("re").findall(r"\\rho=[0-9.]+", s5b))
print("   figure 环境数 sec5b:", s5b.count("\\begin{figure}"))
print("   \\item 双写:", s5b.count("\\item \\item") + W.sec6(Sb, spb).count("\\item \\item"))
