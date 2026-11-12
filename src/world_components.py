# -*- coding: utf-8 -*-
"""Shared, evidence-aware World Contract preview components.

A read-only human-readable projection, not a replacement ontology or a
simulation. Use only with data explicitly permitted to be published.
"""
from __future__ import annotations

from collections import Counter
from html import escape
from urllib.parse import quote


def text(value, limit=100):
    s=str(value if value is not None else "").replace("\n"," ").strip()
    return escape(s[:limit]+("…" if len(s)>limit else ""),quote=True)


def digest(world: dict, report_href: str, *, limit_people: int = 6, limit_events: int = 4,
           event_deep_link: bool = False) -> str:
    """Render a collapsible real-world sample from ANY validated World Contract."""
    if not isinstance(world,dict) or not report_href.startswith("../"):
        raise ValueError("invalid world or report href")
    people=world.get("persons") or []
    events=world.get("events") or []
    relations=world.get("relations") or []
    ev={x.get("id"):x for x in world.get("evidence") or []}
    deg=Counter()
    for r in relations:
        deg[r.get("from_id")]+=1
        deg[r.get("to_id")]+=1
    featured=sorted(people,key=lambda p:(-deg[p.get("id")],p.get("name") or ""))[:limit_people]
    pids={p.get("id") for p in featured}
    nodes={x.get("id"):x.get("name","") for x in (world.get("persons") or [])+(world.get("entities") or [])+(world.get("places") or [])}
    # Prefer relationships visible between selected people over incidental edges.
    selected_rels=[r for r in relations if r.get("from_id") in pids and r.get("to_id") in pids][:6]
    selected_events=sorted(events,key=lambda e:(
        e.get("time",{}).get("year_start") is None,
        e.get("time",{}).get("year_start") if e.get("time",{}).get("year_start") is not None else 99999,
        str(e.get("source_id") or ""),
    ))[:limit_events]
    chunks=['<details class="world-glimpse"><summary>预览真实人物、事件与关系索引 <span>基于统一数据契约</span></summary>',
            '<p class="glimpse-notice">下列是已有结构化记录的部分索引，不代表全书事实已逐条回原著核验。'
            '这里只显示公开可发布的样本，不包含人物心理推断或私有内核。</p>']
    chunks.append('<div class="glimpse-columns"><section aria-label="人物示例"><h4>人物</h4><div class="glimpse-list">')
    for p in featured:
        evidence=next((ev.get(i) for i in p.get("evidence_ids") or [] if ev.get(i)),{})
        source=(evidence or {}).get("source") or {}
        chapters=source.get("chapters") or []
        chapter=(" · "+text(chapters[0],24)) if chapters else ""
        name=str(p.get("name") or "")
        href=report_href+"#view=characters&person="+quote(name,safe="")
        role=(p.get("roles") or [""])[0]
        chunks.append('<a class="glimpse-record" href="%s"><strong>%s</strong><small>%s%s</small></a>'%
                      (escape(href,quote=True),text(name,36),text(role,58),chapter))
    chunks.append('</div></section><section aria-label="事件示例"><h4>事件</h4><div class="glimpse-list">')
    for e in selected_events:
        timing=e.get("time") or {}
        chapter=timing.get("chapter")
        chapter_label=("第"+str(chapter)+"章") if chapter is not None else ""
        time_label=timing.get("label") or "时间待核"
        href=report_href+"#view=events"
        if event_deep_link and e.get("source_id"):
            href+="&event="+quote(str(e["source_id"]),safe="")
        when=(text(chapter_label,20)+" · " if chapter_label else "")+text(time_label,32)
        chunks.append('<a class="glimpse-record" href="%s"><strong>%s</strong><small>%s</small></a>'%
                      (escape(href,quote=True),text(e.get("name") or e.get("source_id"),62),when))
    chunks.append('</div></section></div>')
    if selected_rels:
        chunks.append('<div class="relation-preview"><h4>人物关系样例</h4><ul>')
        for r in selected_rels:
            subject=nodes.get(r.get("from_id")) or "待核验"
            obj=nodes.get(r.get("to_id")) or "待核验"
            chunks.append('<li>%s <b>· %s ·</b> %s</li>'%
                          (text(subject,30),text(r.get("predicate"),40),text(obj,30)))
        chunks.append('</ul><a class="text-link" href="%s#view=relations">打开完整关系图 →</a></div>'%
                      escape(report_href,quote=True))
    chunks.append('</details>')
    return "".join(chunks)
