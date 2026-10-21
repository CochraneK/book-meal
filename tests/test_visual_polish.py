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
    """web target 产物不变量（2026-10-21 恢复「按需加载」架构）：

    骨架 + ``app.css`` + ``app.js`` + **boot** ``data.js`` + 运行时加载器
    ``data-loader.js`` / ``lazy-data.js`` + 每个数据域一个 ``data-<域>.js``。
    全部落盘、全部被 ``render_web`` 记录且非空。

    boot 必须只含元数据：数据域键在 boot 里被置空占位，真正的数据在分块里，
    因此 boot 体积远小于全量（这条是「按需加载没有退化成单体」的护栏）。

    旧 V10–V13 分片文件（boot-data / search-index / 详情 shard 等）仍不产出。
    ``sw.js`` 是仓库级静态文件，不由 target 产出，由 refresh-index 工作流
    原样保留在仓库根。
    """
    payload = _support.payload("full")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        written = B.render_web(payload, out)
        expected = {
            "index.html", "assets/app.css", "assets/app.js", "assets/data.js",
            "assets/data-loader.js", "assets/lazy-data.js",
        }
        expected |= {"assets/data-%s.js" % name for name in B.CHUNK_MAP}
        for name in expected:
            assert (out / name).exists(), "web target 缺少 %s" % name
            assert name in written and written[name] > 0

        # boot 只保留元数据：体积必须远小于各分块之和（否则说明又退回单体）
        chunk_bytes = sum(
            (out / "assets" / ("data-%s.js" % name)).stat().st_size
            for name in B.CHUNK_MAP
        )
        assert chunk_bytes > 0
        boot_bytes = (out / "assets" / "data.js").stat().st_size
        assert boot_bytes * 4 < chunk_bytes, \
            "boot data.js 过大（%d B vs 分块合计 %d B），按需加载已退化" % (
                boot_bytes, chunk_bytes)

        # 首屏脚本顺序：先有 DATA，再装加载器，再跑 app，最后装懒加载门控
        html = (out / "index.html").read_text(encoding="utf-8")
        order = [html.find('src="assets/%s"' % n) for n in
                 ("data.js", "data-loader.js", "app.js", "lazy-data.js")]
        assert all(pos >= 0 for pos in order), "index.html 缺少必要脚本：%s" % order
        assert order == sorted(order), "脚本顺序错误：%s" % order

        obsolete = (
            "boot-data.js", "search-index.js",
            "theme.css", "experience.css", "experience.js",
            "data-full.js", "data-character-details.js", "data-location-details.js",
            "data-event-details.js", "data-space.js",
        )
        for name in obsolete:
            assert not (out / "assets" / name).exists(), "旧分片不应再产出：%s" % name
        assert not (out / "sw.js").exists(), "sw.js 是仓库级静态文件，不归 target 产出"


def test_service_worker_cache_bumped_for_platform_switch():
    """2026-10-20 仓库改造为多书聚合平台：根路径由明书报告变为书库门户，
    明书报告下沉 /ming/、资源路径由 /assets/ 变为 /ming/assets/；
    随后仓库由 ming 改名为 book-meal，缓存前缀同步改为 book-meal-。
    SW 缓存必须 bump，以清空旧命名空间下的过期条目。"""
    sw = (B.BASE / "sw.js").read_text(encoding="utf-8")
    assert "CACHE_PREFIX + 'v12'" in sw
    assert "多书聚合平台" in sw
