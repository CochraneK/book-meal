# -*- coding: utf-8 -*-
"""Classic UI：体验镜像仍可同步，但不再注入可见 V2/V3 覆盖层。"""
from __future__ import annotations

import build as B
import sync_experience as SE


def test_experience_sources_sync_idempotently_into_template():
    skeleton = B.G.TEMPLATE_PATH.read_text(encoding="utf-8")
    css = SE.CSS_SOURCE.read_text(encoding="utf-8")
    js = SE.JS_SOURCE.read_text(encoding="utf-8")
    converted = SE.render_template(skeleton, css, js)

    assert css.rstrip() in converted
    assert js.rstrip() in converted
    for token in (
        SE.STYLE_ATTR, SE.SCRIPT_ATTR, SE.STYLE_START, SE.STYLE_END,
        SE.SCRIPT_START, SE.SCRIPT_END,
    ):
        assert converted.count(token) == 1, token
    assert converted.index(SE.SCRIPT_ATTR) > converted.index("/*{{INLINE_JS}}*/")
    assert SE.render_template(converted, css, js) == converted


def test_classic_mode_disables_visible_v2_v3_overlays():
    css = SE.CSS_SOURCE.read_text(encoding="utf-8")
    js = SE.JS_SOURCE.read_text(encoding="utf-8")
    assert "Classic UI mode" in css
    assert "Classic UI mode" in js
    assert "window.__MING_EXPERIENCE_READY=true" in js
    for forbidden in (
        "commandPalette", "v3-story", "v3-graph-reader", "command-trigger",
        "function renderCharacters", "function renderLocations", "function renderEvents",
    ):
        assert forbidden not in js, forbidden
    for forbidden in (".command-shell", ".v3-story-grid", ".v3-graph-reader", ".command-trigger"):
        assert forbidden not in css, forbidden


# 注：原 test_modern_delivery_remains_outside_experience_layer 依赖
# build.DATA_LOADER_JS_PATH / LAZY_DATA_JS_PATH 与 data-loader.js、lazy-data.js 的
# 分片按需加载契约；2026-10「单体 data.js」重构期间该用例随分层架构一并移除。
# 2026-10-21 已恢复按需加载（boot data.js + data-<域>.js 分块，loader/lazy-data
# 重新回到 web target 产物），分块契约现由 test_visual_polish.py 的
# test_web_target_reports_all_assets 覆盖；本文件仅保留体验层（experience.js）检查。
