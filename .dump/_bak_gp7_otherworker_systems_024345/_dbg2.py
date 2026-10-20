# -*- coding: utf-8 -*-
import json, os, re, sys

ROOT = r"D:\2026\WB项目\明朝"
SP = os.path.join(ROOT, ".dump", "_stats_systems.json")
PD = os.path.join(ROOT, "papers_pilot", "systems", "paper")
out = open(os.path.join(ROOT, "papers_pilot", "systems", "_dbg2.txt"), "w", encoding="utf-8")


def w(s=""):
    out.write(s + "\n")


w("=== stats leaves ===")


def walk(o, pre=""):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, pre + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, pre + "[%d]" % i)
    elif isinstance(o, (int, float)):
        w("%-52s %s" % (pre, o))
    elif isinstance(o, str):
        w("%-52s %s" % (pre, o[:70]))


walk(json.load(open(SP, encoding="utf-8")))

w("\n=== pool / used / bad (check_one 同款) ===")
stats = json.load(open(SP, encoding="utf-8"))


def flatten_numbers(obj, out=None):
    out = set() if out is None else out
    if isinstance(obj, dict):
        for v in obj.values():
            flatten_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            flatten_numbers(v, out)
    elif isinstance(obj, (int, float)):
        out.add(round(float(obj), 2))
    elif isinstance(obj, str):
        for m in re.findall(r"\d+(?:\.\d+)?", obj):
            try:
                out.add(round(float(m), 2))
            except ValueError:
                pass
    return out


pool = flatten_numbers(stats)
used = set()
body = ""
for f in sorted(os.listdir(os.path.join(PD, "sections"))):
    body += open(os.path.join(PD, "sections", f), encoding="utf-8").read()
for m in re.findall(r"\d+\.\d+", body):
    used.add(round(float(m), 2))
bad = [u for u in used if not any(abs(u - v) <= 0.06 for v in pool)]
w("used=%d bad=%d  (阈值 0.34*used=%.2f)" % (len(used), len(bad), 0.34 * len(used)))
w("BAD=%s" % sorted(bad))

w("\n=== bad 逐一定位 ===")
lines = body.split("\n")
for u in sorted(bad):
    tgt = "%g" % u
    hit = 0
    for i, ln in enumerate(lines):
        if re.search(r"[^0-9]" + re.escape(tgt) + r"[^0-9]", ln):
            w("  [%s] L%d %s" % (tgt, i + 1, ln.strip()[:100]))
            hit += 1
            if hit >= 2:
                break
    if hit == 0:
        w("  [%s] 未定位" % tgt)
out.close()
print("ok")
