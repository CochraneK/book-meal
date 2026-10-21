# -*- coding: utf-8 -*-
"""insight_link —— 实体联动索引的口径纪律。

三条纪律（本项目一贯：错挂比不挂更糟）：
  1. 通称/隐喻绰号一律不链（GENERIC_BLOCK）；
  2. 别名归一（学姐→林朝夕）；
  3. 长名优先（假祝宁 不被 祝宁 切走）；
  4. 歧义表面形式（同一词指向两个规范名）直接放弃。
"""
import unittest

from core.books import load_data
from insight_link import GENERIC_BLOCK, _add, _hits, build_entity_surfaces


class TestGenericBlock(unittest.TestCase):
    def test_high_risk_words_blocked(self):
        # v3.12 暴露过的一批「普通词→某具体人」必错链
        for w in ["系统", "清理者", "主任", "新世界", "恶魔",
                  "武器", "领袖", "叛徒"]:
            self.assertIn(w, GENERIC_BLOCK, "%s 必须列入通称黑名单" % w)


class TestSurfaces(unittest.TestCase):
    def setUp(self):
        self.data = load_data("tiancai")

    def test_alias_resolution(self):
        persons, _, _ = build_entity_surfaces(self.data)
        self.assertIn("林朝夕", persons)
        # 找一个「非通称、指向真实人物」的别名，验证它能被归并到规范名
        # （注意：学姐/学长这类称呼词在 GENERIC_BLOCK 里，故意不链，不能当样本）
        ai = self.data.get("alias_index", {})
        names = {c["name"] for c in self.data.get("characters", [])}
        picked = None
        for surface, canon in ai.items():
            if surface not in GENERIC_BLOCK and canon in names and surface in persons:
                picked = (surface, canon)
                break
        self.assertIsNotNone(picked, "找不到可用的别名样本（非通称且指向真实人物）")
        self.assertEqual(persons[picked[0]], picked[1])

    def test_generic_not_a_person(self):
        persons, _, _ = build_entity_surfaces(self.data)
        self.assertNotIn("系统", persons)

    def test_long_name_priority(self):
        fake = {"characters": [{"name": "祝宁"}, {"name": "假祝宁"}],
                "locations": [], "events": [], "alias_index": {}}
        p, _, _ = build_entity_surfaces(fake)
        found, _ = _hits("假祝宁来了", p)
        self.assertIn("假祝宁", found)
        self.assertNotIn("祝宁", found)

    def test_ambiguity_guard(self):
        # 同一表面形式已被 A 占用、又指向 B → 必须放弃（不覆盖、不分裂）
        # 注意：_add 对长度 <2 的表面形式直接拦截，这里用双字符样本
        m = {}
        _add(m, "重名", "A", ())
        _add(m, "重名", "B", ())
        self.assertEqual(m.get("重名"), "A")
        self.assertNotIn("B", m.values())


if __name__ == "__main__":
    unittest.main()
