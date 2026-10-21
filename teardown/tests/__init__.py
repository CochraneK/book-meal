# -*- coding: utf-8 -*-
"""测试包：把 src/ 加入导入路径，使 unittest 与 pytest 都能直接 import core / insight_link 等。"""
import os
import sys

_SRC = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
