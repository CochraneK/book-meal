# -*- coding: utf-8 -*-
"""根路径、JSON 读写、书目常量 —— 全项目共用的地基。"""

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: 两本书。id → 展示名 / 类型（modern_real=现实向，fictional_world=架空世界）
BOOKS = {
    "tiancai": {"name": "天才基本法", "author": "长洱", "world": "modern_real"},
    "feitu": {"name": "我在废土世界扫垃圾", "author": "有花在野", "world": "fictional_world"},
}

BOOK_IDS = ("tiancai", "feitu")


def path(*parts):
    """项目根下的路径拼接。"""
    return os.path.join(BASE, *parts)


def load(p, default=None):
    """读 JSON；文件不存在返回 default。"""
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_data(book_id):
    """读 data/<book>/data.json（五元组主数据）。"""
    return load(path("data", book_id, "data.json"))


def load_raw(book_id):
    """读 data/<book>/extract_raw.json（逐章抽取原始记录，含 time 等字段）。"""
    return load(path("data", book_id, "extract_raw.json"), [])
