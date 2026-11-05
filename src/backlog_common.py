# -*- coding: utf-8 -*-
"""
人工考据队列的共享口径层
========================
README 路线图里两条「人工考据」待办（语录扩面 / 未定位地点与未知年份事件）
各有一份生成式队列文档。口径若散落在各个脚本里，很容易出现
「README 写 30、文档写 28、控制台写 32」这种各自漂移的数字。本模块把口径
收敛到一处，供生成器 / 门禁 / README 渲染器共用：

  - `data/data.json` 是唯一事实来源；
  - `data/character_quotes.json` 是语录唯一事实来源；
  - `data/quote_backlog_status.json` 只登记「已核对结论」，不是事实来源。

**纪律**：只读取聚合工件，绝不引入 Web 查证、记忆推断或原书正文；
原书 TXT 与章节正文按版权红线不入库，本模块也不输出任何原文片段。
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "data.json"
QUOTES = BASE / "data" / "character_quotes.json"
STATUS = BASE / "data" / "quote_backlog_status.json"

# 队列宽度：与 README / verify_quotes.py --stats 的「Top 20」口径一致
GAP_LIMIT = 20

PARTS = {
    "p1": "壹部", "p2": "贰部", "p3": "叁部", "p4": "肆部",
    "p5": "伍部", "p6": "陆部", "p7": "柒部",
}


def esc(v) -> str:
    """表格单元格转义：竖线会撑破 Markdown 表格。"""
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def chapters_text(keys) -> str:
    """把 p<部>-c<章序> 渲染成「壹部·p1-c12」，供回书检索。"""
    keys = keys or []
    if not keys:
        return "—"
    parts = []
    for k in keys:
        p = str(k).split("-", 1)[0]
        parts.append(PARTS.get(p, p) + "·" + str(k))
    return "、".join(parts)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_data():
    return load_json(DATA)


def quote_entries(quotes=None) -> set:
    """已收录语录的人物名；下划线开头的键是说明字段，不是人物。"""
    q = quotes if quotes is not None else load_json(QUOTES)
    return {k for k in q if not k.startswith("_")}


def load_status():
    """已核对结论登记表；文件不存在视为「还没有人核对过」。"""
    if not STATUS.is_file():
        return {}
    return load_json(STATUS)


def reviewed_names(status=None) -> set:
    """已登记结论的人名集合，这些人不再占用 Top 20 队列名额。"""
    s = status if status is not None else load_status()
    return {k for k in (s.get("entries") or {}) if not k.startswith("_")}


def quote_gaps(data=None, quotes=None, status=None, limit=GAP_LIMIT):
    """覆盖章节最多但仍无语录、且尚未登记结论的人物。

    排序刻意沿用 `verify_quotes.py --stats` 的单键稳定排序（只按章数降序），
    保证 Top 20 名单与历史输出完全一致；同频时的先后由 data.json 原序决定。
    """
    d = data if data is not None else load_data()
    entries = quote_entries(quotes)
    done = reviewed_names(status)
    chars = sorted(d.get("characters", []),
                   key=lambda c: -len(c.get("chapters") or []))
    out = [c for c in chars if c.get("name") not in entries
           and c.get("name") not in done]
    return out[:limit] if limit else out


def pending_locations(data=None):
    """未定位地点：lat 或 lng 为空，按提及章数降序、同频按地名排序。"""
    d = data if data is not None else load_data()
    pending = [l for l in d.get("locations", [])
               if l.get("lat") is None or l.get("lng") is None]
    pending.sort(key=lambda l: (-len(l.get("chapters") or []),
                                str(l.get("ancient", ""))))
    return pending


def pending_years(data=None):
    """未知年份事件：year 为空（None 或空串），保持 data.json 原序。"""
    d = data if data is not None else load_data()
    return [e for e in d.get("events", []) if e.get("year") in (None, "")]


def event_stats(data=None):
    """事件年份覆盖统计，供 README 与队列文档派生数字，避免硬编码。"""
    d = data if data is not None else load_data()
    total = len(d.get("events", []))
    pending = len(pending_years(d))
    return {"total": total, "dated": total - pending, "pending": pending}
