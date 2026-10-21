# -*- coding: utf-8 -*-
"""core.chapters —— 章号口径（index / no / key 三套编号的换算）。

这是 v3.3 踩过坑的地方：一处把章号转 int 一处不转，导致阶段归属统计对不上。
测试把两条最关键的不变量钉死：
  1. no_of 永远返回 int（字符串章号也必须被强转）；
  2. 两本书的 index↔no 错位关系（废土恒等、天才「盗版章伪影」index = no + 3）。
"""
import unittest

from core import chapters as ch
from core.books import BOOK_IDS, load_data


class TestNoOf(unittest.TestCase):
    def test_forces_int_from_string(self):
        self.assertIsInstance(ch.no_of({"no": "126", "index": 0}), int)
        self.assertEqual(ch.no_of({"no": "126", "index": 0}), 126)

    def test_fallback_to_index(self):
        self.assertEqual(ch.no_of({"index": 5}), 5)

    def test_empty_no_falls_back(self):
        # no 为空串时回落到 index，而不是把 "" 当 0 之外的怪值
        self.assertEqual(ch.no_of({"no": "", "index": 7}), 7)

    def test_no_no_field_falls_back(self):
        # 缺 no 字段也安全回落 index
        self.assertEqual(ch.no_of({"index": 3}), 3)


class TestChaptersData(unittest.TestCase):
    def test_no_is_int_everywhere(self):
        for b in BOOK_IDS:
            for c in load_data(b)["chapters"]:
                self.assertIsInstance(ch.no_of(c), int)

    def test_feitu_index_equals_no(self):
        # 废土两套编号一致：index == no
        for c in load_data("feitu")["chapters"]:
            self.assertEqual(c["index"], ch.no_of(c))

    def test_tiancai_offset_invariant(self):
        # 天才 index 112 之后存在「盗版章伪影」：index = no + 3
        diffs = set()
        for c in load_data("tiancai")["chapters"]:
            diffs.add(c["index"] - ch.no_of(c))
        self.assertTrue(diffs.issubset({0, 3}),
                        "天才 index-no 错位出现非预期值：%s" % diffs)
        self.assertIn(3, diffs, "天才应至少存在一处 index=no+3 的伪影")

    def test_key2no_and_idx2no_int(self):
        for b in BOOK_IDS:
            cs = load_data(b)["chapters"]
            self.assertTrue(all(isinstance(v, int)
                                for v in ch.build_key2no(cs).values()))
            self.assertTrue(all(isinstance(v, int)
                                for v in ch.build_idx2no(cs).values()))

    def test_nos_of_sorted_unique(self):
        k2n = ch.build_key2no(load_data("tiancai")["chapters"])
        ks = list(k2n)[:3]
        ns = ch.nos_of({"chapters": ks}, k2n)
        self.assertEqual(ns, sorted(ns))
        self.assertEqual(len(ns), len(set(ns)))

    def test_first_no_is_min(self):
        cs = load_data("feitu")["chapters"]
        k2n = ch.build_key2no(cs)
        ks = sorted(k2n)[:3]
        self.assertEqual(ch.first_no({"chapters": ks}, k2n), k2n[ks[0]])

    def test_chapters_in_range(self):
        cs = load_data("feitu")["chapters"]
        sel = ch.chapters_in_range(cs, 1, 11)
        self.assertTrue(all(1 <= ch.no_of(c) <= 11 for c in sel))
        self.assertEqual(len(sel), 11)


if __name__ == "__main__":
    unittest.main()
