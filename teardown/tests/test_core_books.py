# -*- coding: utf-8 -*-
"""core.books —— 书目常量与 JSON 读写的契约。"""
import os
import unittest

from core.books import BOOKS, BOOK_IDS, load_data, path


class TestBooks(unittest.TestCase):
    def test_two_books(self):
        self.assertEqual(set(BOOKS), {"tiancai", "feitu"})
        self.assertEqual(BOOK_IDS, ("tiancai", "feitu"))

    def test_world_flag(self):
        # 两本书的叙事世界类型不同：现实向 vs 架空世界
        self.assertEqual(BOOKS["tiancai"]["world"], "modern_real")
        self.assertEqual(BOOKS["feitu"]["world"], "fictional_world")

    def test_load_data_both(self):
        for b in BOOK_IDS:
            d = load_data(b)
            self.assertIsInstance(d, dict)
            self.assertIn("characters", d)
            self.assertIn("chapters", d)
            self.assertIn("events", d)

    def test_path_join(self):
        p = path("data", "tiancai", "data.json")
        self.assertTrue(p.endswith("data/tiancai/data.json")
                        or p.endswith("data\\tiancai\\data.json"))


if __name__ == "__main__":
    unittest.main()
