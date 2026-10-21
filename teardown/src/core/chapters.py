# -*- coding: utf-8 -*-
"""章号口径 —— index / no / key 三套编号的唯一换算入口。

背景（务必先读，否则极易出错）
------------------------------
每章有三套编号：

* ``index`` —— 抽取器的位置编号（0/1 起，连续）
* ``no``    —— 正文标题上的真实章号（书中写的「第 N 章」）
* ``key``   —— 章节唯一键（形如 ``tiancai-c126``），事件/关系的 ``chapters`` 字段存的是它

**两本书的对齐关系不同**：

* 废土（feitu）：两套一致，index == no（1–439）
* 天才基本法（tiancai）：index 112 之后 ``index = no + 3``（防盗章伪影），
  最大 index 224 / 最大 no 221

**所有对外输出一律用 ``no``**（报告、故事长文、学科分析、章号链接）。
事件/关系的 ``chapters`` 存的是 key，必须先经 ``build_key2no`` 换算再输出。

统一转 ``int()`` 的原因：v3.3 踩过坑——一处转 int 一处不转，
``"126"`` 与 ``126`` 在集合/字典里是两回事，导致阶段归属统计对不上。
"""

from .books import load, path


def no_of(c):
    """从一条 chapter 记录取「书中真实章号」，缺省回落 index，且强制 int。

    int() 不是为了好看：data.json 里 no 可能是字符串，不统一类型会在
    集合去重 / 区间比较时静默出错（v3.3 实测踩到）。
    """
    v = c.get("no", c.get("index"))
    return int(v) if v is not None and str(v).strip() != "" else int(c.get("index", 0))


def build_key2no(chapters):
    """key → no。事件/关系的 chapters 字段存的是 key，靠它换算成章号。"""
    return {c["key"]: no_of(c) for c in chapters}


def build_idx2no(chapters):
    """index → no。阶段划分内部用 index 连续切片，输出前靠它换算。"""
    return {c["index"]: no_of(c) for c in chapters}


def build_no2key(chapters):
    """no → key（反向查章节详情时用）。"""
    return {no_of(c): c["key"] for c in chapters}


def nos_of(obj, key2no):
    """事件或关系对象 → 它涉及的所有章号（升序去重）。

    ``obj["chapters"]`` 存 key 列表；缺失或空 → 返回 []。
    """
    ks = obj.get("chapters") or []
    return sorted({key2no[k] for k in ks if k in key2no})


def first_no(obj, key2no):
    """事件/关系的最小章号（阶段归属口径：以「首次出现」的章为准）。

    这是全项目统一的阶段归属口径 —— 沿用 ``story_material.py`` 的 first_no 定义，
    学科素材包与复核脚本必须与之一致。无章 → None。
    """
    ns = nos_of(obj, key2no)
    return ns[0] if ns else None


def chapters_in_range(chapters, s, e):
    """落在 [s, e] 章号区间内的章（按 no 判定）。用于「共 N 章」取实数。"""
    return [c for c in chapters if s <= no_of(c) <= e]
