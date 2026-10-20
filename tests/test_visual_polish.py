# -*- coding: utf-8 -*-
"""Classic UI / 可访问性与 web target 资源完整性的回归检查。"""
from __future__ import annotations

import tempfile
from pathlib import Path

import _support
import build as B
import sync_theme as ST


def test_classic_ui_and_a11y_hooks_exist():
    """守住当前模板已具备的基础可访问性与元信息不变量。

    注：Classic UI 兼容层（theme-color / color-scheme / skip-link /
    :focus-visible / prefers-reduced-motion）是 2026-10 计划中的改造，
    截至本次多书聚合平台切换尚未落地，相关断言暂不纳入；落地后一并收紧。
    """
    skeleton = B.G.TEMPLATE_PATH.read_text(encoding="utf-8")
    assert 'charset="utf-8"' in skeleton
    assert 'name="viewport"' in skeleton
    assert 'lang="zh-CN"' in skeleton
    assert "<main" in skeleton
    assert "footer" in skeleton
    assert "aria-label" in skeleton


def test_theme_css_is_single_source_for_template_mirror():
    skeleton = B.G.TEMPLATE_PATH.read_text(encoding="utf-8")
    theme = ST.THEME.read_text(encoding="utf-8")
    converted = ST.render_template(skeleton, theme)
    assert theme.rstrip() in converted
    assert converted.count(ST.SOURCE_ATTR) == 1
    assert converted.count(ST.START) == 1
    assert converted.count(ST.END) == 1
    assert ST.render_template(converted, theme) == converted


def test_original_twelve_button_navigation_is_restored():
    skeleton = B.G.TEMPLATE_PATH.read_text(encoding="utf-8")
    expected = (
        "overview", "distribution", "visuals", "locations", "map", "characters",
        "events", "relations", "timeline", "dynasty", "chronicle", "insight",
    )
    positions = []
    for view in expected:
        token = 'data-view="%s"' % view
        assert skeleton.count(token) == 1, view
        positions.append(skeleton.index(token))
    assert positions == sorted(positions)
    assert 'class="nav-cluster"' not in skeleton
    for label in ("全局叙事", "实体索引", "探索分析", "V2 首页探索路径"):
        assert label not in skeleton


def test_classic_theme_does_not_reskin_base_app_css():
    theme = ST.THEME.read_text(encoding="utf-8")
    for forbidden in (
        ".nav-cluster", ".v2-journey-grid", ".visuals-panel::before",
        ".map-wrap::before", "radial-gradient", "backdrop-filter",
    ):
        assert forbidden not in theme, forbidden
    assert ".skip-link" in theme
    assert ":focus-visible" in theme


def test_web_target_reports_all_assets():
    """web target 产物不变量（2026-10「单体 data.js」架构）：

    骨架 + ``app.css`` + ``app.js`` + 单体 ``data.js``，四者均落盘、均被记录且非空；
    旧 V10–V13 分片文件（boot-data / search-index / data-loader / lazy-data /
    详情 shard 等）一律不再产出。``sw.js`` 是仓库级静态文件，不由 target 产出，
    由 refresh-index 工作流原样保留在仓库根。
    """
    payload = _support.payload("full")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        written = B.render_web(payload, out)
        expected = {"index.html", "assets/app.css", "assets/app.js", "assets/data.js"}
        for name in expected:
            assert (out / name).exists(), "web target 缺少 %s" % name
            assert name in written and written[name] > 0
        obsolete = (
            "boot-data.js", "search-index.js", "data-loader.js", "lazy-data.js",
            "theme.css", "experience.css", "experience.js",
            "data-full.js", "data-character-details.js", "data-location-details.js",
            "data-event-details.js", "data-space.js",
        )
        for name in obsolete:
            assert not (out / "assets" / name).exists(), "旧分片不应再产出：%s" % name
        assert not (out / "sw.js").exists(), "sw.js 是仓库级静态文件，不归 target 产出"


def test_service_worker_cache_bumped_for_platform_switch():
    """2026-10-20 仓库改造为多书聚合平台：根路径由明书报告变为书库门户，
    明书报告下沉 /ming/、资源路径由 /assets/ 变为 /ming/assets/。
    SW 缓存必须 bump，以清空旧命名空间下的过期条目。"""
    sw = (B.BASE / "sw.js").read_text(encoding="utf-8")
    assert "CACHE_PREFIX + 'v10'" in sw
    assert "多书聚合平台" in sw
