# -*- coding: utf-8 -*-
"""Run03: preview uses the existing registry without rewriting legacy reports."""
import book_registry
import build_dist
import build_world_experience as W


def test_world_catalog_reuses_existing_book_registry():
    manifests=book_registry.load()
    b=W.catalog(manifests)
    assert len(b)>=6
    assert [x["id"] for x in b]==[x["id"] for x in manifests]
    assert all(x["report"].startswith("../") for x in b)


def test_ming_legacy_deep_links_remain_reachable():
    ming=next(b for b in W.catalog(book_registry.load()) if b["id"]=="ming")
    assert ming["routes"]["story"]=="../ming/index.html#view=overview"
    assert ming["routes"]["explore"]=="../ming/index.html#view=visuals"
    assert ming["routes"]["research"]=="../ming/index.html#view=insight"
    assert any(x[1].endswith("#view=map") for x in ming["extras"])


def test_sanggan_uses_only_existing_public_report():
    b=next(x for x in W.catalog(book_registry.load()) if x["id"]=="sanggan")
    assert b["report"]=="../books/sanggan/index.html"
    assert b["routes"] == {
        "story": b["report"] + "#view=events",
        "explore": b["report"] + "#view=characters",
        "research": b["report"] + "#view=insight",
    }
    output=W.render()
    assert "world/kernel/" not in output
    assert "world/index/persons.json" not in output


def test_ordinary_world_is_planned_not_fake_complete():
    book=next(x for x in W.catalog(book_registry.load()) if x["id"]=="ordinary-world")
    assert book["status"]=="planned"
    assert all(book[key] is None for key in ("chapters","characters","events","relations"))
    fragment=W.detail(book)
    assert "建档中" in fragment
    assert "待抽取" in fragment
    assert 'class="routes"' not in fragment
    assert "查看书籍建档页" in fragment


def test_preview_is_single_file_and_deterministic():
    doc=W.render()
    assert doc==W.render()
    for token in ['lang="zh-CN"','name="viewport"','id="world-list"',
                  'id="world-search"','id="world-view"',
                  'id="world-template-ming"','id="world-template-sanggan"',
                  'aria-live="polite"','prefers-reduced-motion','id="paths-title"']:
        assert token in doc
    assert "<script src=" not in doc
    assert 'href="https://' not in doc
    assert "<iframe" not in doc


def test_untrusted_manifest_is_escaped_and_traversal_blocked():
    example=[{"id":"sample","title":'</template><script>alert("x")</script>',
              "author":'<img src=x onerror=alert(1)>',
              "desc":"n","kind":"history","report":"index.html",
              "chapters":1,"metrics":{"characters":1,"events":2,"relations":3}}]
    doc=W.render(example)
    assert "</template><script>alert" not in doc
    assert "<img src=x onerror" not in doc
    for unsafe in ("../evil.html","https://example.org/report.html","/root.html","javascript:alert.html"):
        try: W.safe_report({"id":"sample","report":unsafe})
        except ValueError: pass
        else: raise AssertionError("unsafe report URL accepted: "+unsafe)


def test_build_dist_publishes_generated_preview_without_source_files():
    items=build_dist.plan()
    generated=[rel for src,rel in items if src is None]
    assert generated==["worlds/index.html"]
    rendered=build_dist.generated_world_preview()
    assert rendered.startswith(b"<!doctype html>")
    assert b"world-template-ming" in rendered
    assert b"world/kernel/" not in rendered
    assert not any(rel.endswith(".py") for _,rel in items if rel.startswith("worlds/"))


def test_old_homepage_only_adds_preview_link():
    import build_hub
    home = (W.ROOT / "index.html").read_text(encoding="utf-8")
    assert 'href="worlds/index.html"' in home
    assert 'class="world-teaser"' in home
    assert 'href="worlds/index.html"' in build_hub.render(book_registry.load(), [])
    assert 'id="book-search"' in home and 'id="book-sort"' in home


def test_real_ming_shared_glimpse_is_evidence_aware():
    from world_components import digest
    from export_world import build
    world=build("ming")
    excerpt=digest(world,"../ming/index.html")
    assert 'class="world-glimpse"' in excerpt
    assert '章节' not in excerpt or '基于统一数据契约' in excerpt
    assert '#view=characters&amp;person=' in excerpt
    assert '#view=events' in excerpt
    assert '<script' not in excerpt
    assert "私有内核" in excerpt
    preview=W.render()
    assert excerpt in preview


def test_shared_component_handles_synthetic_sanggan_without_private_fixture():
    from world_adapters import sanggan
    from world_components import digest
    sample={
        "manifest":{"book":{"title":"Test","author":"Synthetic"}},
        "persons":[
            {"id":"person:A","name":"Test A","evidence":"observed","first_chapter":1},
            {"id":"person:B","name":"Test B","evidence":"inferred","first_chapter":1},
        ],"places":[],
        "events":{"events":[
            {"id":"event:X","chapter":2,"summary":"An event","actors":["person:A","person:B"],"evidence":"observed"},
        ]},
        "relations":{"relations":[
            {"id":"rel:1","from":"person:A","to":"person:B","sub_pred":"colleague","source_type":"observed"}
        ]},
        "kernel":{"count":2,"persons":[]},
    }
    world=sanggan.adapt(sample)
    s=digest(world,"../books/sanggan/index.html")
    assert "Test A" in s and "Test B" in s
    assert "An event" in s
    assert "colleague" in s
    assert "<script" not in s



def test_existing_public_sanggan_report_maps_real_events_and_people():
    from world_adapters.sanggan_public import read_public_report, adapt
    from world_contract import validate_world
    raw, checksum=read_public_report(W.ROOT/"books/sanggan/index.html")
    assert len(checksum)==64
    assert (len(raw["characters"]),len(raw["events"]),len(raw["relations"]))==(78,124,123)
    world=adapt(raw,source_sha256=checksum)
    assert not validate_world(world),validate_world(world)[:10]
    assert (len(world["persons"]),len(world["events"]),len(world["relations"]))==(78,124,123)
    assert len(world["places"])==len(raw["scene"]["places"])
    assert world["extensions"]["sanggan_public"]["private_persona_kernels_included"] is False
    assert world["extensions"]["sanggan_public"]["only_public_index_fields"] is True
    assert {p["source_id"] for p in world["persons"]}=={p["id"] for p in raw["characters"]}
    for person in world["persons"]:
        assert set(person) <= {
            "id","source_id","name","ontology_version","ontology_ref",
            "aliases","roles","evidence_ids","extensions",
        }
        assert "persona_domains" not in person
        assert "trace" not in person and "by_batch" not in person
    assert not any("world/kernel/" in str(p) for p in world["persons"])


def test_same_component_shows_real_public_sanggan_and_deep_links():
    from world_components import digest
    world=W._sanggan_public_world()
    fragment=digest(world,"../books/sanggan/index.html",event_deep_link=True)
    assert 'class="world-glimpse"' in fragment
    assert "基于统一数据契约" in fragment
    assert "#view=characters&amp;person=" in fragment
    assert "#view=events&amp;event=" in fragment
    assert "第" in fragment and "章" in fragment
    html=W.render()
    assert fragment in html and 'id="world-template-sanggan"' in html


def test_public_sanggan_parser_never_executes_javascript():
    from world_adapters.sanggan_public import extract_report_data
    import json
    fixture={"characters":[],"events":[],"relations":[]}
    assert extract_report_data("const DATA = "+json.dumps(fixture)+";")==fixture
    for invalid in (
        "const DATA = alert('bad');",
        "const DATA = {};\\nconst DATA = {};",
        "var DATA = {};",
    ):
        try:extract_report_data(invalid)
        except ValueError:pass
        else:raise AssertionError("accepted executable or duplicate assignment")


def test_public_sanggan_evidence_provenance_and_unresolved_entities():
    from world_adapters.sanggan_public import adapt, read_public_report
    from world_contract import validate_world
    data,_=read_public_report(W.ROOT/"books/sanggan/index.html")
    w=adapt(data)
    assert not validate_world(w)
    assert all(e["source"]["path"].startswith("books/sanggan/index.html")
               for e in w["evidence"])
    assert all(e.get("verification")=="source_record_only" for e in w["evidence"])
    assert all(e["status"]=="unresolved" for e in w["entities"])
    assert all(r["evidence_ids"] for r in w["relations"])



def test_full_public_sanggan_index_is_accessible_and_searchable():
    from world_browse import render as browse
    src=W._sanggan_public_world()
    fragment=browse(src,"../books/sanggan/index.html",cap=250,event_deep_link=True)
    assert "人物 78" in fragment
    assert "事件 124" in fragment
    assert "关系 123" in fragment
    assert fragment.count('data-index-record')==78+124+123
    assert 'data-index-tab="persons"' in fragment
    assert 'data-index-tab="events"' in fragment
    assert 'data-index-tab="relations"' in fragment
    assert 'data-world-search' in fragment
    assert "#view=characters&amp;person=" in fragment
    assert "#view=events&amp;event=" in fragment
    assert fragment in W.render()


def test_large_ming_index_is_capped_and_preserves_full_report():
    from world_browse import render as browse
    w=W._ming_public_world()
    fragment=browse(w,"../ming/index.html",cap=40)
    assert "世界索引" in fragment
    assert fragment.count('data-index-record')==120
    assert "数据量较大" in fragment
    assert "查看完整原报告" in fragment
    assert fragment in W.render()


def test_search_index_escapes_untrusted_public_names():
    from world_browse import render as browse
    from world_adapters.sanggan_public import adapt
    fake={
        "characters":[{"id":"person:E","name":'<img src=x onerror=alert(1)>',
                       "role_in_book":"<svg onload=alert(1)>","first_chapter":1}],
        "events":[],"relations":[],"scene":{"places":[]},
    }
    fragment=browse(adapt(fake),"../books/sanggan/index.html")
    assert "<img" not in fragment and "<svg" not in fragment
    assert "&lt;img" in fragment and "&lt;svg" in fragment
    assert 'data-index-record' in fragment


def test_world_browser_script_contains_delegated_handlers():
    js=(W.ROOT/"web/world_experience.js").read_text(encoding="utf-8")
    assert '[data-index-tab]' in js
    assert '[data-world-search]' in js
    assert 'pane.addEventListener("click"' in js
    assert 'pane.addEventListener("input"' in js
