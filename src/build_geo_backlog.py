# -*- coding: utf-8 -*-
"""
生成「未定位地点」人工考据队列（docs/geo_backlog.md）
====================================================
README 路线图里「未定位地点与未知年份事件的人工考据」以前只是一句话待办，
既不知道剩多少、也不知道从哪条开始。本脚本把它变成一份按提及频次排序、
可直接开工的队列。

**纪律（与 README「数据纪律」一致）**：
  - 数据来源只有 `data/data.json` 的书本抽取结果，不引入 Web 查证、不引入记忆；
  - 只列证据与「建议核验路径」，**绝不填坐标**——圣地巡礼场景里，
    错误坐标比留空更有害（宁可留空不可猜错）；
  - 表里每一项都标注出处章节 key，方便回原书核对；
  - 章节正文 / chapters.json 不入库，本脚本只读章节 key，任何环境生成结果一致，
    因此 `--check` 可以直接进 CI。

用法：
    python src/build_geo_backlog.py           # 生成 docs/geo_backlog.md
    python src/build_geo_backlog.py --check   # 只校验，不一致返回 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "data.json"
OUT = BASE / "docs" / "geo_backlog.md"

PARTS = {
    "p1": "壹部", "p2": "贰部", "p3": "叁部", "p4": "肆部",
    "p5": "伍部", "p6": "陆部", "p7": "柒部",
}

# 按「书中身份」给核验路径的类型化建议；是方法论提示，不是地理结论。
ROUTE = {
    "地名": "先查《明史·地理志》《读史方舆纪要》确认建置沿革 → 地方志定位到今县级行政区 → 再定坐标",
    "古战场": "先定战役所在水系/山系 → 对照《明史》本纪与参战方行军路线 → 地方志战场地望 → 再定坐标",
    "遗址·陵": "查地方志「陵墓/古迹」条与文保单位名录 → 确认现存实体 → 再定坐标",
    "祠·庙": "查地方志「祠祀」条与现存祠庙名录 → 确认是否仍存 → 再定坐标",
    "关隘": "查《明史·地理志》关隘条与长城/边镇图志 → 比定今关口位置 → 再定坐标",
}


def esc(v) -> str:
    """表格单元格转义：竖线会撑破 Markdown 表格。"""
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def chapters_text(keys) -> str:
    keys = keys or []
    if not keys:
        return "—"
    parts = []
    for k in keys:
        p = str(k).split("-", 1)[0]
        parts.append(PARTS.get(p, p) + "·" + str(k))
    return "、".join(parts)


def render() -> str:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    locations = data.get("locations", [])
    pending = [l for l in locations if l.get("lat") is None or l.get("lng") is None]
    pending.sort(key=lambda l: (-len(l.get("chapters") or []), str(l.get("ancient", ""))))

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
            % (i, esc(l.get("ancient")), len(l.get("chapters") or []),
               esc(chapters_text(l.get("chapters"))), esc(alias), esc(trace),
               esc(l.get("status")), esc(l.get("modern_address")) or "待考",
               esc(l.get("note")) or "—")
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

    return (
        "# 未定位地点 · 人工考据队列\n\n"
        "> 本文件由 `src/build_geo_backlog.py` 从 `data/data.json` 生成，**勿手改**；\n"
        "> 改文案或口径请改生成器后重跑 `python src/build_geo_backlog.py`。\n\n"
        "## 口径与纪律\n\n"
        "- 数据来源：**只有书本抽取结果** `data/data.json`，不含 Web 查证、不含记忆推断。\n"
        "- 入选条件：`lat` 或 `lng` 为空。按 `data/data.json` **原始抽取口径**：\n"
        "  全库 %(total)d 个地点，已定位 %(located)d 个，**待考 %(pending)d 个**。\n"
        "- 口径差异：README / 报告里写的「583 个地点 · 553 已定位」是\n"
        "  `generate_report.build_scope('full')` 补入衍生地点后的**展示口径**；\n"
        "  两种口径差额 20 个均已定位，因此待考数同为 30。本表只用原始抽取口径，\n"
        "  避免把衍生记录混进人工考据队列。\n"
        "- 表中「出处章节」是原书分部章序 key（`p<部>-c<章序>`），用于回书核对；\n"
        "  章节正文按版权红线不入库、也不写进本文件。\n"
        "- **本表不填任何坐标**。对「圣地巡礼」而言错误坐标比留空更有害；\n"
        "  考据结论须另行标注来源层级（书本抽取 / 记忆 / Web）后才可回填 `geo_annotations.json`。\n"
        "- 排序口径：按书中提及章数降序（冷门地点优先），同频按地名排序。\n"
        "- 「书中提及形式」来自 `mentioned_as`，抽取时偶尔会混入上下文短语，\n"
        "  **不全是严谨别名**，仅作回书检索线索，不据此推断地望。\n\n"
        "## 待考清单（%(pending)d 条）\n\n"
        "| # | 地点 | 提及章数 | 出处章节 | 书中提及形式 | 书中身份 | 现状 | 今地 | 备注 |\n"
        "|--:|---|--:|---|---|---|---|---|---|\n"
        "%(rows)s\n\n"
        "## 建议核验路径（方法论，不是地理结论）\n\n"
        "%(routes)s\n\n"
        "## 未知年份事件\n\n"
        "`src/generate_report.py` 的 `build_scope('full')` 口径下，全书 1106 个事件中\n"
        "**1104 个已有年份、仅 2 个年份待考**，可在「事件」视图里筛选 `年份待考` 逐条处理。\n"
        "本队列聚焦地点，不重复罗列事件。\n\n"
        "## 完成后怎么回填\n\n"
        "1. 逐条查证，把结论与出处写进 `data/geo_annotations.json`（`source` 字段必须区分来源）；\n"
        "2. 跑 `python src/merge.py` → `python src/build.py --check` → 重建报告；\n"
        "3. 重跑本生成器，队列自动缩短；README 的「已定位」数字由 `sync_readme.py` 同步。\n"
    ) % {
        "total": len(locations),
        "located": len(locations) - len(pending),
        "pending": len(pending),
        "rows": "\n".join(rows),
        "routes": "\n".join(routes),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成未定位地点人工考据队列")
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
