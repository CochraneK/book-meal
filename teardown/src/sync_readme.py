# -*- coding: utf-8 -*-
"""README「当前状态」表自动刷新（src/sync_readme.py）
=====================================================
起因：v3.3 发现两份学科分析文档有 4 处结论级数字漂移——手写数字抄了旧素材包，
而旧复核脚本又只查总量不查阶段级，于是「36 项全绿」和「整节数字全错」并存。
同样的风险正躺在 README：规模表 12 行全是手写，改了数据没人会同步。

做法：从 `data/<book>/data.json` 等**最终产物**现算，与 README 表格逐格比对。
  --check（默认）：不一致就列出差异并以退出码 1 失败 —— 当门禁用
  --write        ：把实算值写回 README

不能现算的行（质量门 WARNING 数、视图冒烟结果、长文引用数）**不动**，
它们依赖跑完审计/冒烟才知道，脚本不猜。
"""
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = ["tiancai", "feitu"]
LABEL = {"tiancai": "天才基本法", "feitu": "我在废土世界扫垃圾"}


def load(p, default=None):
    path = os.path.join(BASE, p)
    if not os.path.exists(path):
        return default
    return json.load(io.open(path, encoding="utf-8"))


def stats(book):
    """只从最终产物现算，口径与 data.json 一致。"""
    ddir = os.path.join(BASE, "data", book)
    data = load(os.path.join("data", book, "data.json"), {})
    ch = data.get("chapters", [])
    nos = [int(c.get("no", c.get("index"))) for c in ch]
    ev = data.get("events", [])
    loc = data.get("locations", [])
    rel = data.get("relations", [])

    ev_base = {e.get("type_base", "") for e in ev}
    loc_base = {l.get("type_base", "") for l in loc}
    rel_base = {r.get("rel_base", "") for r in rel}

    q = load(os.path.join("data", book, "quotes.json"), {})
    qm = q.get("meta", {}) if isinstance(q, dict) else {}
    dup = load(os.path.join("data", book, "duplicate_report.json"), {})
    dup_ch = len(dup.get("dup_chapters", []) or [])

    return {
        "章节覆盖": "%d / %d（100%%）" % (len(ch), max(nos) if nos else len(ch)),
        "人物 / 地点": "%d / %d" % (len(data.get("characters", [])), len(loc)),
        "事件 / 关系": "%d / %d" % (len(ev), len(rel)),
        "同章上下文事件": str(len(data.get("other_events", []))),
        "类型归约": "事件 %d 类 / 地点 %d 类 / 关系 %d 类"
                    % (len(ev_base), len(loc_base), len(rel_base)),
        "金句": "对白 %s 条（%s 位说话人）+ 叙述 %s 条"
                % (qm.get("picked", "?"), qm.get("speakers", "?"), qm.get("narr_picked", "?")),
        "源文本重复": ("%d 对（涉及 %d 章）" % (len(dup.get("pairs", []) or []), dup_ch))
                     if dup.get("pairs") else "0 对",
    }


# 只刷新这些行；其余保持手写（依赖审计/冒烟结果，脚本不猜）
AUTO_ROWS = ["章节覆盖", "人物 / 地点", "事件 / 关系", "同章上下文事件",
             "类型归约", "金句", "源文本重复"]


def norm(s):
    """比较用：剥掉加粗/斜体标记，只比实质数字。"""
    return s.replace("*", "").replace("_", "").strip()


def row_re(label):
    return re.compile(r"^\|\s*" + re.escape(label) + r"\s*\|(.*\|.*)\|\s*$", re.M)


def main():
    write = "--write" in sys.argv
    st = {b: stats(b) for b in BOOKS}
    path = os.path.join(BASE, "README.md")
    md = io.open(path, encoding="utf-8").read()
    diffs = []

    for label in AUTO_ROWS:
        m = row_re(label).search(md)
        if not m:
            diffs.append("README 里找不到行「%s」" % label)
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) != 2:
            diffs.append("行「%s」不是两列" % label)
            continue
        new = [st["tiancai"][label], st["feitu"][label]]
        # 比较时剥离加粗标记（README 里部分单元格是 **粗体**），写回时保留原样式
        if [norm(c) for c in cells] != [norm(c) for c in new]:
            diffs.append("%-12s README %s → 实算 %s" % (label, cells, new))
            if write:
                out = ["**%s**" % v if ("**" in cells[i]) else v
                       for i, v in enumerate(new)]
                md = md[:m.start()] + "| %s | %s | %s |" % (label, out[0], out[1]) + \
                    md[m.end():]

    if write:
        io.open(path, "w", encoding="utf-8").write(md)
        print("[write] README「当前状态」表已刷新 %d 行" % len(AUTO_ROWS))
        return 0
    if diffs:
        print("[FAIL] README 与实算不一致（%d 处）：" % len(diffs))
        for d in diffs:
            print("   " + d)
        print("修法：python src/sync_readme.py --write")
        return 1
    print("[OK] README「当前状态」表 %d 行与实算一致" % len(AUTO_ROWS))
    for b in BOOKS:
        print("   %s：%s" % (LABEL[b], st[b]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
