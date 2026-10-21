# -*- coding: utf-8 -*-
"""阶段划分 —— 全项目唯一真源（此前在 generate_report.py 与 perspectives_prep.py 各存一份拷贝）。

两本书的切分策略不同，因为叙事结构本就不同：

* 废土（feitu）：副本流。按「卷 / 副本弧」切，主线推进章累积成段 → 17 副本弧 + 23 主线
  + 序章 1 + 番外 2 = 43 段。
* 天才基本法（tiancai）：现实 + 穿越双线。按 ``extract_raw`` 的 ``time`` 关键词切，
  无关键词时兜底等长分段（每 18 章）→ 14 段。

**返回值一律是 index 口径**（内部切片需要连续编号），
对外输出前必须用 ``phases_to_no()`` 换算成书中真实章号。
"""

import re

# 天才基本法：time 关键词 → 阶段名（按顺序匹配，先命中先得）
TC_TIME_HINTS = [
    ("芝士", "芝士世界（高中线）"), ("高中", "高中线"), ("高三", "高中线"),
    ("考研", "考研线"), ("大学", "大学线"), ("现实", "现实线"), ("22岁", "现实线"),
    ("28岁", "现实线"), ("小时候", "回忆线"), ("童年", "童年线"),
]
# 注：旧 generate_report.py 末项写成 ("小时候", "童年线")，排在 ("小时候", "回忆线")
# 之后永远命中不到（死项）。core 统一为语义正确的 ("童年", "童年线")，
# 已用基线验证两书阶段划分结果不变（天才 14 段 / 废土 43 段）。

# 同一副本在目录里可能出现标题变体（如「无法离开的公司」与「无法逃离的公司」），
# 不归一就会把一条弧切成好几段，这里统一到主标题。
ARC_ALIAS = {
    "无法逃离的公司": "无法离开的公司",
}


def cn_arc(title):
    """「吃人的火锅店（一）」→「吃人的火锅店」；非弧标题返回 None。"""
    m = re.match(r"^(.+?)（[一二三四五六七八九十百零]+）$", title)
    if not m:
        return None
    arc = m.group(1)
    return ARC_ALIAS.get(arc, arc)


# ---------------------------------------------------------------- 废土（副本流）

def _derive_feitu(chapters):
    phases = []
    volume = "第一卷"
    run = []  # 主线推进的累积章

    def flush_run():
        if not run:
            return
        if len(run) >= 6:
            phases.append({"name": volume + "·主线", "s": run[0], "e": run[-1]})
        elif phases:
            phases[-1]["e"] = run[-1]  # 短过渡并入上一阶段
        else:
            phases.append({"name": volume + "·主线", "s": run[0], "e": run[-1]})
        del run[:]

    for c in chapters:
        t = c["title"]
        if "卷完" in t:
            flush_run()
            continue
        if t == "序章":
            flush_run()
            volume = "第二卷"
            phases.append({"name": "序章", "s": c["index"], "e": c["index"]})
            continue
        if t.startswith("番外"):
            flush_run()
            phases.append({"name": t, "s": c["index"], "e": c["index"]})
            continue
        arc = cn_arc(t)
        if arc:
            flush_run()
            if phases and phases[-1]["name"] == arc and phases[-1]["e"] == c["index"] - 1:
                phases[-1]["e"] = c["index"]
            else:
                phases.append({"name": arc, "s": c["index"], "e": c["index"]})
        else:
            run.append(c["index"])
            if len(run) >= 16:
                flush_run()
    flush_run()
    return [p for p in phases if p["e"] >= p["s"]]


# ------------------------------------------------------------ 天才（双线穿越）

def _derive_tiancai(chapters, raw):
    time_by_key = {r.get("key"): (r.get("time") or "") for r in raw}
    # 不再读 chapters.json（含小说原文，版权敏感、不入库）：index→key 直接从
    # 传入的 data.json 章节取，与基线比对可证明零行为变更（verify_core 守门）。
    key_by_index = {c["index"]: c["key"] for c in chapters}
    seg = []
    cur_name, cur_start = None, None
    seg_size = 18
    n = 0
    for c in chapters:
        idx = c["index"]
        hint = ""
        t = time_by_key.get(key_by_index.get(idx, ""), "")
        for kw, name in TC_TIME_HINTS:
            if kw in t:
                hint = name
                break
        n += 1
        name = hint or ("第" + str((n - 1) // seg_size + 1) + "段")
        if cur_name is None:
            cur_name, cur_start = name, idx
        elif name != cur_name or (idx - cur_start) >= seg_size * 2:
            seg.append({"name": cur_name, "s": cur_start, "e": idx - 1})
            cur_name, cur_start = name, idx
    if cur_name:
        seg.append({"name": cur_name, "s": cur_start, "e": chapters[-1]["index"]})
    # 合并过短段（<4 章）到邻居
    merged = []
    for p in seg:
        if merged and p["e"] - p["s"] < 3 and merged[-1]["e"] == p["s"] - 1:
            merged[-1]["e"] = p["e"]
        else:
            merged.append(p)
    return merged


# ------------------------------------------------------------------- 统一入口

def derive_phases(book_id, chapters, raw=None):
    """按书切分阶段，**返回 index 口径**（对外输出前用 phases_to_no 换算）。

    :param chapters: data.json 的 chapters（标准结构，含 index/key/no/title）
    :param raw:      仅 tiancai 需要（extract_raw.json，提供 time 字段）
    """
    if book_id == "feitu":
        return _derive_feitu(chapters)
    if book_id == "tiancai":
        return _derive_tiancai(chapters, raw or [])
    raise ValueError("未知书目：%s" % book_id)


def phases_to_no(phases, idx2no):
    """index 口径阶段 → no 口径（书中真实章号）。"""
    return [{"name": p["name"],
             "s": idx2no.get(p["s"], p["s"]),
             "e": idx2no.get(p["e"], p["e"])} for p in phases]


def phase_key(p):
    """阶段唯一键：「名（起–止）」。

    **阶段名不唯一**（天才「芝士世界（高中线）」×7、废土「第一卷·主线」×10），
    所以凡是要当字典键、要做链接目标、要写进文档引用的地方，一律用这个带区间的键，
    绝不能只用裸名 —— v3.3 就是靠它避免了「一段链代表多段」的错挂。
    """
    return "%s（%d–%d）" % (p["name"], p["s"], p["e"])


def stage_map(phases_no):
    """no 口径阶段 → {章号: 阶段唯一键}。查询 O(1)。"""
    m = {}
    for p in phases_no:
        k = phase_key(p)
        for no in range(p["s"], p["e"] + 1):
            m[no] = k
    return m


def stage_of(obj, key2no, phases_no, _map=None):
    """事件/关系 → 所属阶段唯一键；首章不在任何区间内 → None。

    口径：**first_no** —— 以「首次出现的章」落到的阶段为准（全项目统一）。
    """
    m = _map if _map is not None else stage_map(phases_no)
    n = None
    ks = obj.get("chapters") or []
    ns = sorted({key2no[k] for k in ks if k in key2no})
    n = ns[0] if ns else None
    return m.get(n) if n is not None else None
