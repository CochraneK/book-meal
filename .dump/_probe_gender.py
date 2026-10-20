# -*- coding: utf-8 -*-
"""gender 篇终检：哨兵 / 双 \item / 未定义 ref / 中文乱码 / 摘要词数。"""
import json, os, re

ROOT = r"D:\2026\WB项目\明朝"
pdir = os.path.join(ROOT, "papers_pilot", "gender", "paper")
secs = sorted(f for f in os.listdir(os.path.join(pdir, "sections")) if f.endswith(".tex"))
body = "".join(open(os.path.join(pdir, "sections", f), encoding="utf-8").read() for f in secs)

print("残留 @@ 哨兵 :", len(re.findall(r"@@\w+@@", body)), re.findall(r"@@\w+@@", body)[:5])
print("双 \\item    :", len(re.findall(r"\\item\s*\\item", body)))
print("问号 ref    :", len(re.findall(r"\?\?", body)))
print("\\ref 目标   :", sorted(set(re.findall(r"\\ref\{([^}]+)\}", body))))
main = open(os.path.join(pdir, "main.tex"), encoding="utf-8").read()
print("label 定义  :", sorted(set(re.findall(r"\\label\{([^}]+)\}", body + main))))
print("乱码 U+FFFD :", body.count("\ufffd"))

# 摘要词数
sp = {}
import importlib.util
spec = importlib.util.spec_from_file_location("sg", os.path.join(ROOT, "papers_pilot", "_lib", "spec_gender.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ae = m.SPEC["abstract_en"]
print("abstract_en 词数 :", len(ae.split()), "(150-250)")
ac = m.SPEC["abstract_cn"]
print("abstract_cn 字数 :", len(re.findall(r"[\u4e00-\ufffd]", ac)))
print("abstract_en 含 % :", "%" in ae, "| abstract_cn 含 % :", "%" in ac)

# 正文里出现的小数是否都能在底稿找到
S = json.load(open(os.path.join(ROOT, ".dump", "_stats_gender.json"), encoding="utf-8"))
pool = set()


def flat(o):
    if isinstance(o, dict):
        for v in o.values():
            flat(v)
    elif isinstance(o, list):
        for v in o:
            flat(v)
    elif isinstance(o, (int, float)):
        pool.add(round(float(o), 2))
    elif isinstance(o, str):
        for x in re.findall(r"\d+(?:\.\d+)?", o):
            pool.add(round(float(x), 2))
flat(S)
bad = sorted({round(float(x), 2) for x in re.findall(r"\d+\.\d+", body)
              if not any(abs(round(float(x), 2) - v) <= 0.06 for v in pool)})
print("正文小数总数 :", len(set(re.findall(r"\d+\.\d+", body))), "| 底稿找不到 :", bad)

# 关键数字一致检查
for k in ("1809", "1657", "152", "467", "301", "288", "206", "163", "96", "81", "79", "44",
          "13", "3", "0", "127", "631", "12.9", "6.3", "537", "0.87", "49.4", "39.9",
          "8.0", "7.3", "2.7", "0.2", "8.3", "3.5", "46", "185", "312", "927"):
    if k not in body:
        print("  !! 正文缺失关键数字", k)
print("中文标题：", m.SPEC["title_cn"])
