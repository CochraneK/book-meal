# -*- coding: utf-8 -*-
"""
生成「未定位地点 + 未知年份事件」人工考据队列（docs/geo_backlog.md）
====================================================================
README 路线图里「未定位地点与未知年份事件的人工考据」以前只是一句话待办，
既不知道剩多少、也不知道从哪条开始。本脚本把两类都变成可直接开工的队列：
地点按提及章数降序逐条列出；事件逐条列出、数字与条目全部从 data.json 派生
（旧版把「1106 / 1104 / 2」写死在文案里，数据一动就失真）。

**纪律（与 README「数据纪律」一致）**：
  - 数据来源只有 `data/data.json` 的书本抽取结果，不引入 Web 查证、不引入记忆；
  - 只列证据与「建议核验路径」，**绝不填坐标、绝不填推断年份**——圣地巡礼
    场景里错误坐标比留空更有害（宁可留空不可猜错）；
  - 同一章里别的事件有纪年，不等于本事件有纪年，不做前后顺序倒推；
  - 表里每一项都标注出处章节 key，方便回原书核对；
  - 章节正文 / chapters.json 不入库，本脚本只读章节 key，任何环境生成结果一致，
    因此 `--check` 可以直接进 CI；
  - 排序、转义、章节 key 与待考筛选口径统一由 `src/backlog_common.py` 提供。

用法：
    python src/build_geo_backlog.py           # 生成 docs/geo_backlog.md
    python src/build_geo_backlog.py --check   # 只校验，不一致返回 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import backlog_common as BC  # noqa: E402

OUT = BASE / "docs" / "geo_backlog.md"

# 按「书中身份」给核验路径的类型化建议；是方法论提示，不是地理结论。
ROUTE = {
    "地名": "先查《明史·地理志》《读史方舆纪要》确认建置沿革 → 地方志定位到今县级行政区 → 再定坐标",
    "古战场": "先定战役所在水系/山系 → 对照《明史》本纪与参战方行军路线 → 地方志战场地望 → 再定坐标",
    "遗址·陵": "查地方志「陵墓/古迹」条与文保单位名录 → 确认现存实体 → 再定坐标",
    "祠·庙": "查地方志「祠祀」条与现存祠庙名录 → 确认是否仍存 → 再定坐标",
    "关隘": "查《明史·地理志》关隘条与长城/边镇图志 → 比定今关口位置 → 再定坐标",
}


def render() -> str:
    # 口径（排序 / 章节 key / 转义）统一由 backlog_common 提供，
    # 与 docs/quote_backlog.md、verify_quotes.py --stats、README 同源。
    data = BC.load_data()
    locations = data.get("locations", [])
    pending = BC.pending_locations(data)
    year_pending = BC.pending_years(data)
    ev = BC.event_stats(data)

    rows = []
    for i, l in enumerate(pending, 1):
        trace = str(l.get("trace_type") or "地名")
        route = ROUTE.get(trace, ROUTE["地名"])
        # mentioned_as 偶尔混进整句抽取上下文（不是别名），截断避免撑破表格
        alias_parts = []
        for a in (l.get("mentioned_as") or [])[:3]:
            a = str(a).strip()
            alias_parts.append(a[:24] + "…" if len(a) > 24 else a)
        alias = "、".join(alias_parts)
        rows.append(
            "| %d | **%s** | %d | %s | %s | %s | %s | %s | %s |"
            % (i, BC.esc(l.get("ancient")), len(l.get("chapters") or []),
               BC.esc(BC.chapters_text(l.get("chapters"))), BC.esc(alias), BC.esc(trace),
               BC.esc(l.get("status")), BC.esc(l.get("modern_address")) or "待考",
               BC.esc(l.get("note")) or "—")
        )
    # 建议核验路径单独成节，避免把表格撑到不可读
    routes = []
    seen = set()
    for l in pending:
        t = str(l.get("trace_type") or "地名")
        if t in seen:
            continue
        seen.add(t)
        routes.append("- **%s**：%s" % (t, ROUTE.get(t, ROUTE["地名"])))

    # 未知年份事件：以前只写一句「剩 2 个」，既不列条目也把数字写死了。
    # 现在逐条列出，数字全部从 data.json 派生，队列可勾选。
    year_rows = []
    for i, e in enumerate(year_pending, 1):
        people = "、".join(str(p) for p in (e.get("participants") or [])[:6])
        if len(e.get("participants") or []) > 6:
            people += "…"
        year_rows.append(
            "| %d | **%s** | %s | %s | %s | %s | %s | 年份待考 |"
            % (i, BC.esc(e.get("name")), BC.esc(e.get("category")) or "—",
               BC.esc(e.get("type")) or "—", BC.esc(people) or "—",
               BC.esc(e.get("location")) or "—",
               BC.esc(BC.chapters_text(e.get("chapters"))))
        )
    if not year_rows:
        year_rows.append("| — | *全部事件已有年份* | — | — | — | — | — | — |")

    return (
        "# 未定位地点与未知年份事件 · 人工考据队列\n\n"
        "> 本文件由 `src/build_geo_backlog.py` 从 `data/data.json` 生成，**勿手改**；\n"
        "> 排序、章节 key 与待考口径统一由 `src/backlog_common.py` 提供，\n"
        "> 与 `docs/quote_backlog.md`、`verify_quotes.py --stats`、README 同源。\n\n"
        "## 口径与纪律\n\n"
        "- 数据来源：**只有书本抽取结果** `data/data.json`，不含 Web 查证、不含记忆推断。\n"
        "- 地点入选条件：`lat` 或 `lng` 为空。按 `data/data.json` **原始抽取口径**：\n"
        "  全库 %(total)d 个地点，已定位 %(located)d 个，**待考 %(pending)d 个**。\n"
        "- 口径差异：README / 报告里的地点总数是 `generate_report.build_scope('full')`\n"
        "  补入衍生地点后的**展示口径**（数字由 `src/sync_readme.py` 派生写入 README）；\n"
        "  这些衍生记录均已定位，因此两种口径的待考数相同。本表只用原始抽取口径，\n"
        "  避免把衍生记录混进人工考据队列。\n"
        "- 表中「出处章节」是原书分部章序 key（`p<部>-c<章序>`），用于回书核对；\n"
        "  章节正文按版权红线不入库、也不写进本文件。\n"
        "- **本表不填任何坐标、不填任何推断年份**。对「圣地巡礼」而言错误坐标比留空\n"
        "  更有害；考据结论须标注来源层级（书本抽取 / 记忆 / Web）后才可回填。\n"
        "- 地点排序：按书中提及章数降序（冷门地点优先），同频按地名排序；\n"
        "  事件保持 `data.json` 原序。\n"
        "- 「书中提及形式」来自 `mentioned_as`，抽取时偶尔会混入上下文短语，\n"
        "  **不全是严谨别名**，仅作回书检索线索，不据此推断地望。\n\n"
        "## 未定位地点（%(pending)d 条）\n\n"
        "| # | 地点 | 提及章数 | 出处章节 | 书中提及形式 | 书中身份 | 现状 | 今地 | 备注 |\n"
        "|--:|---|--:|---|---|---|---|---|---|\n"
        "%(rows)s\n\n"
        "## 建议核验路径（方法论，不是地理结论）\n\n"
        "%(routes)s\n\n"
        "## 未知年份事件（%(ev_pending)d 条）\n\n"
        "全书 %(ev_total)d 个事件中 %(ev_dated)d 个已有年份、"
        "**%(ev_pending)d 个年份待考**。\n"
        "既有 `data/manual_event_years.json` 已补过一批年份并逐条标了 `source`；\n"
        "聚合时 `src/merge.py` 只对 `year` 为空的事件回填，且写入\n"
        "`year_source` / `year_approx` / `year_note`，重跑不丢。\n\n"
        "这两条多为「说法 / 公案」而非有明确纪年的单次事件，年份未必存在唯一解。\n"
        "核对时先找书里有没有**本事件**可换算的纪年（年号 / 干支 / 相对时间）：\n"
        "**同一章里别的事件有纪年，不等于本事件有纪年**，不要按人物生卒、\n"
        "事件前后顺序或同章年份倒推。没有书内依据就保持留空。\n\n"
        "| # | 事件 | 类别 | 类型 | 相关人员 | 地点 | 出处章节 | 现状 |\n"
        "|--:|---|---|---|---|---|---|---|\n"
        "%(year_rows)s\n\n"
        "## 完成后怎么回填\n\n"
        "1. 地点：逐条查证，把结论与出处写进 `data/geo_annotations.json`\n"
        "   （`source` 字段必须区分来源）；\n"
        "2. 事件：确认有书内依据后，按 `事件名: {year, source, note, approx}`\n"
        "   写进 `data/manual_event_years.json`；`source` 必须标来源层级，\n"
        "   通行说法而非书中明确纪年时置 `approx: true`；无依据则保持留空；\n"
        "3. 跑 `python src/merge.py` → `python src/build.py --check` → 重建报告；\n"
        "4. 重跑本生成器，队列自动缩短；README 数字由 `src/sync_readme.py` 同步。\n"
    ) % {
        "total": len(locations),
        "located": len(locations) - len(pending),
        "pending": len(pending),
        "rows": "\n".join(rows),
        "routes": "\n".join(routes),
        "year_rows": "\n".join(year_rows),
        "ev_total": ev["total"],
        "ev_dated": ev["dated"],
        "ev_pending": ev["pending"],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成未定位地点与未知年份事件人工考据队列")
    ap.add_argument("--check", action="store_true", help="只校验文档是否与数据一致")
    args = ap.parse_args(argv)
    doc = render()
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if doc == old:
        print("[check] OK：docs/geo_backlog.md 与数据一致" if args.check
              else "[done] 已是最新，无需写入")
        return 0
    if args.check:
        print("[check] 失败：docs/geo_backlog.md 落后，请跑 python src/build_geo_backlog.py",
              file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    print("[done] 已生成 %s（%d 字符）" % (OUT.relative_to(BASE), len(doc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
