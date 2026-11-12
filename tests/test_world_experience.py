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
    assert set(b["routes"].values())=={b["report"]}
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
