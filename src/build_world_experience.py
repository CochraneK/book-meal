# -*- coding: utf-8 -*-
"""Generate a read-only, self-contained Book-Meal world entry.

This is an opt-in experience preview, NOT a replacement for any report.
Single source of the book list: book_registry.load().
"""
from __future__ import annotations

import argparse
import html
import re
from functools import lru_cache
from pathlib import Path

import book_registry
from world_components import digest

ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
EXTRAS = {
    "ming": [("圣地巡礼地图", "map"), ("历史时间轴", "timeline"),
             ("帝王与年谱", "dynasty"), ("人物图谱", "visuals")],
    "sanggan": [("走进暖水屯（原报告）", None), ("人物深描（原报告）", None)],
    "swdw": [("七世界探索（原报告）", None)],
    "tiancai": [("双时间线（原报告）", None)],
    "feitu": [("废土世界图谱（原报告）", None)],
}


def esc(x):
    return html.escape(str(x if x is not None else ""), quote=True)


def safe_report(m):
    value = str(book_registry.href_of(m)).strip()
    if not value or value.startswith(("/", "\\", "#")) or "://" in value:
        raise ValueError("external/absolute report path is not supported")
    if any(x in ("", ".", "..") for x in value.split("/")):
        raise ValueError("unsafe report path")
    if re.fullmatch(r"[A-Za-z0-9/_\-.]+", value) is None or not value.endswith(".html"):
        raise ValueError("unsafe report path")
    return "../" + value


def catalog(manifests):
    result, seen = [], set()
    for m in manifests:
        key = str(m.get("id", ""))
        if not IDENTIFIER.fullmatch(key) or key in seen:
            raise ValueError("bad or duplicate book id")
        seen.add(key)
        link = safe_report(m)
        planned = m.get("status") == "planned"
        nums = m.get("metrics") or {}
        for v in [m.get("chapters") or 0] + [nums.get(k) or 0 for k in ("characters","events","relations")]:
            if type(v) not in (int, str) or not str(v).isdigit() or int(v) < 0:
                raise ValueError("invalid metric")
        routes = {x: link for x in ("story", "explore", "research")}
        if key == "ming" and not planned:
            routes.update({
                "story": link+"#view=overview",
                "explore": link+"#view=visuals",
                "research": link+"#view=insight",
            })
        extras = []
        if not planned:
            for label, view in EXTRAS.get(key, []):
                suffix = "#view="+view if key == "ming" and view else ""
                extras.append((label, link+suffix))
        result.append({
            "id":key, "title":str(m.get("title") or ""), "author":str(m.get("author") or ""),
            "kind":str(m.get("kindLabel") or m.get("kind") or "其他"),
            "glyph":str(m.get("glyph") or key[0])[:1],
            "description":str(m.get("desc") or ""),
            "status":"planned" if planned else "ready", "report":link,
            "chapters":None if planned else int(m.get("chapters") or 0),
            "characters":None if planned else int(nums.get("characters") or 0),
            "events":None if planned else int(nums.get("events") or 0),
            "relations":None if planned else int(nums.get("relations") or 0),
            "routes":routes, "extras":extras,
        })
    return result


def detail(book):
    planned = book["status"] == "planned"
    status = "建档中" if planned else "已整理"
    s = (
        '<section class="hero" aria-labelledby="world-title">'
        '<div class="hero-meta"><span>%s</span><span>·</span><span>%s</span>'
        '<span class="state">%s</span></div>'
        '<h2 id="world-title" tabindex="-1">%s</h2><p>%s</p>'
        '<span class="hero-mark" aria-hidden="true">%s</span></section>'
    ) % tuple(map(esc, [book["kind"], book["author"], status,
                         book["title"], book["description"], book["glyph"]]))
    s += '<div class="stats" aria-label="书籍统计">'
    for label,key in [("章节","chapters"),("人物","characters"),
                      ("事件","events"),("关系","relations")]:
        value = "—" if book[key] is None else f'{book[key]:,}'
        s += '<div class="stat"><b>%s</b><small>%s%s</small></div>' % (
            esc(value), esc(label), " · 待抽取" if planned else ""
        )
    s += '</div>'
    if planned:
        return s+(
            '<section class="planned"><h3>这本书正在建档</h3>'
            '<p>人物、事件和研究结果尚未完成全书抽取。当前页面只提供书籍介绍，'
            '不会生成虚假的统计或模拟结果。</p>'
            '<a class="primary" href="%s">查看书籍建档页</a></section>'
        ) % esc(book["report"])
    s += (
        '<section aria-labelledby="paths-title"><div class="heading">'
        '<h3 id="paths-title">你想怎样走进这个世界？</h3>'
        '<span>同一本书 · 三种入口</span></div><div class="routes">'
    )
    paths = [
        ("读","读懂故事","章节、事件与时间线，理解原著发展。","story"),
        ("探","探索人物与关系","人物、组织、世界结构与关系网络。","explore"),
        ("研","研究与分析","已经整理的学科洞察与报告。","research"),
    ]
    for glyph,title,description,key in paths:
        link=book["routes"][key]
        action="直达相关视图" if "#view=" in link else "打开现有报告"
        s+=(
            '<a class="route" href="%s"><span class="ideogram" aria-hidden="true">%s</span>'
            '<h4>%s</h4><p>%s</p><span class="action">%s →</span></a>'
        )%tuple(map(esc,[link,glyph,title,description,action]))
    s+='</div></section><section class="more" aria-labelledby="more-title">'
    s+='<div class="heading"><h3 id="more-title">这本书的特别入口</h3><span>保留原有能力</span></div><div class="links">'
    for label,href in book["extras"]:
        s+='<a href="%s">%s</a>'%(esc(href),esc(label))
    s+='<a href="%s">完整原报告</a></div></section>'%esc(book["report"])
    s+=(
        '<aside class="disclaimer"><strong>关于数据和模拟</strong><p>'
        '这里的数字来自现有公开书目登记，并不是独立核验的科学结果。'
        '尚未提供专用深链的书籍将打开原报告。此入口不等于已经接入自主 Agent 或'
        '社会仿真；相应功能需要后续完成统一世界数据接口的验收。</p></aside>'
    )
    return s


@lru_cache(maxsize=1)
def _ming_public_world():
    """Ming: real public aggregate; never fetch Private Sanggan in Pages CI."""
    from export_world import build
    from world_contract import validate_world
    world=build("ming")
    problems=validate_world(world)
    if problems:
        raise ValueError("Ming world-contract validation failed: "+str(problems[:3]))
    return world


def render(manifests=None):
    books=catalog(book_registry.load() if manifests is None else manifests)
    has_ming=any(b["id"]=="ming" and b["status"]=="ready" for b in books)
    ming_preview=digest(_ming_public_world(),"../ming/index.html") if has_ming else ""
    if not books: raise ValueError("empty book registry")
    choices=[]
    templates=[]
    for i,b in enumerate(books):
        small="建档中" if b["status"]=="planned" else b["kind"]
        choices.append(
            '<a class="book" href="?book=%s" data-book="%s" data-search="%s"%s>'
            '<span class="glyph" aria-hidden="true">%s</span><span>'
            '<strong>%s</strong><small>%s</small></span></a>'
            % (esc(b["id"]),esc(b["id"]),
               esc((b["title"]+" "+b["author"]+" "+b["kind"]).lower()),
               ' aria-current="page"' if i==0 else "",
               esc(b["glyph"]),esc(b["title"]),esc(small))
        )
        supplement=ming_preview if b["id"]=="ming" and b["status"]=="ready" else ""
        templates.append('<template id="world-template-%s">%s</template>'%
                         (esc(b["id"]),detail(b)+supplement))
    css=(ROOT/"web/world_experience.css").read_text(encoding="utf-8")
    js=(ROOT/"web/world_experience.js").read_text(encoding="utf-8")
    if "</style" in css.lower() or "</script" in js.lower():
        raise ValueError("unsafe script/style source")
    return (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark">'
        '<title>书籍世界 · Book-Meal</title><style>%s</style></head><body>'
        '<a class="skip" href="#world-view">跳到当前世界</a>'
        '<div class="shell"><header class="top">'
        '<a class="logo" href="../index.html">BOOK<span>·</span>MEAL</a>'
        '<nav aria-label="主导航"><span>统一体验 · 预览</span>'
        '<a href="../index.html">返回书库</a></nav></header>'
        '<div class="intro"><span class="kicker">ONE BOOK · ONE WORLD</span>'
        '<h1>从一本书，到一个世界。</h1>'
        '<p>读懂故事、探索人物、研究另一种可能。'
        '先共享入口，也保留每本书已有的独特视图。</p></div>'
        '<div class="layout"><aside class="sidebar">'
        '<label class="search-label" for="world-search">选择一本书</label>'
        '<input class="search" id="world-search" type="search" '
        'placeholder="书名 / 作者 / 类型" autocomplete="off">'
        '<nav class="books" id="world-list" aria-label="书籍世界">%s</nav>'
        '<p class="nothing" id="world-empty" hidden>没有匹配的书。</p>'
        '<p class="sidebar-note">旧版报告仍完整保留。'
        '这里是统一体验层，不会修改原有书籍数据。</p>'
        '</aside><main class="stage" id="world-main">'
        '<div id="world-view">%s</div>'
        '<div class="footer">由现有 Book-Meal 书目清单生成 · '
        '这里展示已有成果的入口，不生成未经验证的模型结论。</div>'
        '</main></div><div class="sr-only" id="selection-status" '
        'role="status" aria-live="polite"></div></div>'
        '%s<script>%s</script></body></html>\n'
    )%(css,"".join(choices),
       detail(books[0])+(ming_preview if books[0]["id"]=="ming" else ""),
       "".join(templates),js)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=ROOT/"worlds"/"index.html")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args(argv)
    expected=render().encode("utf-8")
    if args.check:
        if not args.out.is_file() or args.out.read_bytes()!=expected: return 1
        print("[OK] unified world preview is current")
        return 0
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(expected)
    print("[OK] wrote",args.out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
