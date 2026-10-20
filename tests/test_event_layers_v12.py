# -*- coding: utf-8 -*-
"""V12 事件摘要前端钩子的同步回归。

注：原 V11/V12/V13 分层后处理用例（data-events.js 拆分、shard 有界性、
data-loader 懒加载路由）随 2026-10「单体 data.js」重构停用，相关用例已移除；
此处只保留仍在前端构建链中使用的 sync_event_cards_v12 幂等性回归。
"""
from __future__ import annotations

import sync_event_cards_v12


def test_v12_event_list_source_count_sync_is_idempotent():
    source = sync_event_cards_v12.TARGET.read_text(encoding="utf-8")
    rendered = sync_event_cards_v12.render_source(source)
    assert sync_event_cards_v12.NEW in rendered
    assert sync_event_cards_v12.OLD not in rendered
    assert sync_event_cards_v12.render_source(rendered) == rendered
