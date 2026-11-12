# -*- coding: utf-8 -*-
"""Lightweight, shared, searchable, PUBLIC-only World Contract index.

No private sources, no LLM calls and no extra JSON download. Lists are
rendered at build time and collapsed initially. Long worlds are capped.
"""
from __future__ import annotations

from html import escape
from urllib.parse import quote


def esc(value, limit=100):
    s=str(value if value is not None else "").replace("\n", " ").strip()
    return escape(s[:limit]+("…" if len(s)>limit else ""), quote=True)


def render(world: dict, report_href: str, *, cap: int = 200,
           event_deep_link: bool = False) -> str:
    if not isinstance(world, dict) or not report_href.startswith("../"):
        raise ValueError("invalid world / report URL")
    if cap < 1 or cap > 500:
        raise ValueError("record cap must be between 1 and 500")
    people = world.get("persons") or []
    events = world.get("events") or []
    relations = world.get("relations") or []
    names = {
        node["id"]:node.get("name","")
        for key in ("persons","entities","places")
        for node in world.get(key) or [] if node.get("id")
    }
    evidence = {e["id"]:e for e in world.get("evidence") or [] if e.get("id")}
    def evidence_type(row):
        e=next((evidence.get(i) for i in row.get("evidence_ids") or [] if evidence.get(i)),{})
        return "推断" if e.get("kind")=="INFER" else (
            "待核验" if e.get("kind")=="UNKNOWN" else "书内线索"
        )
    def chapter_label(row):
        chapter=(row.get("time") or {}).get("chapter")
        if chapter is not None:
            return "第"+str(chapter)+"章"
        ref=next((evidence.get(i) for i in row.get("evidence_ids") or [] if evidence.get(i)),{})
        chapters=(ref.get("source") or {}).get("chapters") or []
        return str(chapters[0]) if chapters else ""

    labels=(("persons","人物",len(people)),("events","事件",len(events)),
            ("relations","关系",len(relations)))
    parts=[
        '<details class="world-browser"><summary>浏览书籍世界索引 <small>人物 %d · 事件 %d · 关系 %d</small></summary>'%
        (len(people),len(events),len(relations)),
        '<div class="world-browser-inner">',
        '<p class="browser-note">仅展示已有结构化数据；“书内线索”不代表逐条原文复核。'
        '不展示私人内核、原著全文或未公开材料。</p>',
        '<div class="browser-tabs" role="group" aria-label="切换索引类型">'
    ]
    for idx,(key,label,count) in enumerate(labels):
        parts.append(
            '<button type="button" class="browser-tab" data-index-tab="%s" aria-pressed="%s">%s %d</button>'%
            (key,"true" if idx==0 else "false",label,count)
        )
    parts.append('</div><label class="browser-search-label">搜索当前索引'
                 '<input class="browser-search" type="search" data-world-search '
                 'placeholder="输入姓名、事件、关系…" autocomplete="off"></label>')
    parts.append('<div class="browser-result" data-world-result role="status" aria-live="polite"></div>')

    sections = (("persons",people),("events",events),("relations",relations))
    for idx,(key,records) in enumerate(sections):
        parts.append(
            '<section class="browser-section" data-index-section="%s" %s aria-label="%s索引">'%
            (key, "hidden" if idx else "", {"persons":"人物","events":"事件","relations":"关系"}[key])
        )
        parts.append('<div class="browser-rows">')
        for row in records[:cap]:
            if key=="persons":
                title=str(row.get("name") or "姓名待核")
                sub=((row.get("roles") or [""])[0] or "人物记录")
                chapter=chapter_label(row)
                info=(chapter+" · " if chapter else "")+str(sub)
                url=report_href+"#view=characters&person="+quote(title,safe="")
            elif key=="events":
                title=str(row.get("name") or row.get("source_id") or "未命名事件")
                chapter=chapter_label(row)
                time=(row.get("time") or {}).get("label") or ""
                info=((chapter+" · ") if chapter else "")+str(time or "时间待考")
                url=report_href+"#view=events"
                if event_deep_link and row.get("source_id"):
                    url+="&event="+quote(str(row["source_id"]),safe="")
            else:
                title=(str(names.get(row.get("from_id")) or "待核验")+"  ·  "+
                       str(row.get("predicate") or "关联")+"  ·  "+
                       str(names.get(row.get("to_id")) or "待核验"))
                info="关系分类："+evidence_type(row)
                url=report_href+"#view=relations"
            search=(title+" "+info).lower()
            parts.append(
                '<a class="browser-item" href="%s" data-index-record data-search="%s">'
                '<strong>%s</strong><small>%s</small></a>'%
                (esc(url,500),esc(search,240),esc(title,110),esc(info,105))
            )
        parts.append('</div>')
        if len(records)>cap:
            parts.append(
                '<p class="browser-more">此书数据量较大，当前先展示 %d / %d 项。'
                '<a href="%s">查看完整原报告</a></p>'%
                (cap,len(records),esc(report_href,500))
            )
        parts.append('</section>')
    parts.append('</div></details>')
    return "".join(parts)
