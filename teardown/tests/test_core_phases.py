# -*- coding: utf-8 -*-
"""core.phases —— 阶段划分唯一真源。

钉死三件事：
  1. 阶段数与基线一致（天才 14 / 废土 43）——防未来又长出一份派生；
  2. derive_phases(tiancai) 不再读 chapters.json（含原文，版权敏感），改用传入的 data.json；
  3. phase_key 区间键格式与 stage_of 的「首章归属」口径。
"""
import json
import os
import unittest

from core import chapters as ch
from core import phases as ph
from core.books import BOOK_IDS, load_data, load_raw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = json.load(open(os.path.join(ROOT, "src", "core", "baseline_phases.json"),
                          encoding="utf-8"))


class TestPhaseBaseline(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(BASELINE["tiancai"]["index"]), 14)
        self.assertEqual(len(BASELINE["feitu"]["index"]), 43)


class TestDerive(unittest.TestCase):
    def test_derive_matches_baseline(self):
        for b in BOOK_IDS:
            cs = load_data(b)["chapters"]
            raw = load_raw(b) if b == "tiancai" else None
            derived = ph.derive_phases(b, cs, raw)
            self.assertEqual(derived, BASELINE[b]["index"],
                             "阶段派生与基线不一致：%s" % b)

    def test_returns_index_scope_with_valid_bounds(self):
        cs = load_data("feitu")["chapters"]
        for p in ph.derive_phases("feitu", cs):
            self.assertIsInstance(p["s"], int)
            self.assertIsInstance(p["e"], int)
            self.assertLessEqual(p["s"], p["e"])

    def test_phase_key_format(self):
        self.assertEqual(ph.phase_key({"name": "X", "s": 1, "e": 5}), "X（1–5）")

    def test_stage_of_first_no(self):
        cs = load_data("tiancai")["chapters"]
        idx2no = ch.build_idx2no(cs)
        derived = ph.derive_phases("tiancai", cs, load_raw("tiancai"))
        phases_no = ph.phases_to_no(derived, idx2no)
        smap = ph.stage_map(phases_no)
        k2n = ch.build_key2no(cs)
        # 第一章落在现实线（基线首段）
        key = ph.stage_of({"chapters": [cs[0]["key"]]}, k2n, phases_no, smap)
        self.assertIsNotNone(key)
        self.assertTrue(key.startswith("现实线"))


if __name__ == "__main__":
    unittest.main()
