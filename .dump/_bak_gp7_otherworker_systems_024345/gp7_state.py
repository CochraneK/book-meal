# -*- coding: utf-8 -*-
"""general-purpose-7 私有临时脚本 —— 不与其他 worker 共用文件名。
快照 systems 目录 + 底稿 schema + 当前 sections 首行，用于判断碰撞归属。"""
import os, time, json, glob

ROOT = r"D:\2026\WB项目\明朝"
P = os.path.join(ROOT, "papers_pilot", "systems")
out = open(os.path.join(P, "gp7_state.txt"), "w", encoding="utf-8")


def w(s=""):
    out.write(s + "\n")


def mt(p):
    try:
        return time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(p)))
    except Exception:
        return "?"


w("=== now %s ===" % time.strftime("%H:%M:%S"))
w("\n=== .dump/_stats_systems.json ===")
try:
    j = json.load(open(os.path.join(ROOT, ".dump", "_stats_systems.json"), encoding="utf-8"))
    w("  mtime %s keys=%s" % (mt(os.path.join(ROOT, ".dump", "_stats_systems.json")), list(j.keys())))
except Exception as e:
    w("  ERR %s" % e)

w("\n=== papers_pilot/systems 全量 mtime（排除我自己的 gp7_/_dbg/_ls 临时件）===")
for a, dd, ff in os.walk(P):
    for f in sorted(ff):
        p = os.path.join(a, f)
        rel = os.path.relpath(p, P)
        if rel.startswith(("gp7_", "_dbg", "_dbg2", "_ls", "_ls2")):
            continue
        w("  %s  %s" % (mt(p), rel))

w("\n=== sections 首行 ===")
sd = os.path.join(P, "paper", "sections")
if os.path.isdir(sd):
    for f in sorted(os.listdir(sd)):
        p = os.path.join(sd, f)
        try:
            txt = open(p, encoding="utf-8").read()
        except Exception:
            continue
        w("  %s (%d chars) mtime=%s" % (f, len(txt), mt(p)))
        w("     %s" % txt.strip().replace("\n", " ")[:120])

w("\n=== main.tex / sections 里的 \\\\subsection 列表 ===")
for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
    try:
        txt = open(os.path.join(sd, f), encoding="utf-8").read()
    except Exception:
        continue
    for ln in txt.split("\n"):
        if ln.strip().startswith("\\subsection"):
            w("  %s  %s" % (f, ln.strip()[:80]))

w("\n=== systems 目录里所有 py/txt 临时件 ===")
for p in sorted(glob.glob(os.path.join(P, "*"))):
    if os.path.isfile(p):
        w("  %s  %s" % (mt(p), os.path.basename(p)))
out.close()
print("ok")
