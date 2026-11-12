# -*- coding: utf-8 -*-
"""待拆书也能建档，但不会被伪装成已完成。"""
import book_registry as REG
import build_hub as HUB
import sync_readme as RD

def _book():
    return next(m for m in REG.load() if m["id"] == "ordinary-world")

def test_ordinary_world_metadata_without_fabricated_results():
    m = _book()
    assert m["title"] == "平凡的世界"
    assert m["author"] == "路遥"
    assert m.get("status") == "planned"
    assert not m.get("chapters")
    assert not any((m.get("metrics") or {}).values())

def test_planned_card_is_not_called_completed_report():
    card = HUB._card(_book())
    assert "查看建档页" in card
    assert "内容待抽取" in card
    assert "打开报告" not in card

def test_planned_readme_row_has_unknown_counts():
    row = RD._book_rows([_book()])
    assert "| — | — | — | — |" in row
    assert "查看建档页" in row

def test_existing_books_stay_ready():
    books = REG.load()
    assert len(books) >= 6
    assert sum(m.get("status") == "planned" for m in books) == 1
    assert sum(m.get("status") != "planned" for m in books) >= 5
