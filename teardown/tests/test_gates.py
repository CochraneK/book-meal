# -*- coding: utf-8 -*-
"""门禁测试 —— 把现有「深审 + README 一致性 + 构建 + 无头冒烟」固化成可重复跑的断言。

这些脚本本就是项目的质量门，这里用 subprocess 驱动，保证：
  - 每次提交都能重跑同一套门禁（CI 直接复用）；
  - 不依赖浏览器时也能绿（无头冒烟仅在检测到 Chrome/Edge 时跑，否则 skip）。
"""
import os
import subprocess
import sys
import unittest

from check_report import find_chrome

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

GATE_SCRIPTS = [
    "verify_core.py",
    "verify_perspectives.py",
    "verify_story_refs.py",
    "verify_papers.py",
]


def _run(args, timeout=300):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          timeout=timeout)


class TestGates(unittest.TestCase):
    def test_verify_scripts_green(self):
        for s in GATE_SCRIPTS:
            with self.subTest(script=s):
                r = _run([PY, os.path.join(ROOT, "src", s)])
                self.assertEqual(r.returncode, 0,
                                 "%s 退出码 %d\n%s" % (s, r.returncode, r.stdout[-800:]))

    def test_sync_readme_consistent(self):
        r = _run([PY, os.path.join(ROOT, "src", "sync_readme.py"), "--check"],
                 timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout[-800:])

    def test_build_and_headless(self):
        try:
            find_chrome()
        except RuntimeError:
            self.skipTest("本机未安装 Chrome/Edge，跳过构建+无头冒烟（CI 会安装后跑）")
        # 先重建报告（保证 out/ 是最新的），再无头冒烟 12 视图 × 2 书
        b = _run([PY, os.path.join(ROOT, "src", "generate_report.py")], timeout=300)
        self.assertEqual(b.returncode, 0, b.stdout[-800:])
        h = _run([PY, os.path.join(ROOT, "src", "check_report.py")], timeout=600)
        self.assertEqual(h.returncode, 0, h.stdout[-1200:])


if __name__ == "__main__":
    unittest.main()
