# -*- coding: utf-8 -*-
"""本地一键门禁（C4 配套）—— 复刻 CI 的 6 步，提交前自验。

用法：
    python run_checks.py            # 跑全部（含无头冒烟，需本机 Chrome/Edge）
    python run_checks.py --no-headless   # 跳过无头浏览器自检

步骤：语法 → 单测 → 重建派生产物 → 深审 → 构建报告 → 无头冒烟。
任一步失败即非零退出，并打印失败摘要。
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
SRC = os.path.join(ROOT, "src")


def step(name, args, timeout=600):
    print("\n=== %s ===" % name)
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    out = (r.stdout + r.stderr)[-1500:]
    if r.returncode == 0:
        print("[OK] %s" % name)
    else:
        print("[FAIL] %s (exit %d)" % (name, r.returncode))
        print(out)
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-headless", action="store_true", help="跳过无头浏览器自检")
    args = ap.parse_args()

    fails = []

    # 1. 语法
    rc = step("syntax: py_compile", [PY, "-m", "py_compile"]
              + [os.path.join(SRC, f) for f in os.listdir(SRC) if f.endswith(".py")])
    if rc:
        fails.append("syntax(py)")
    js = os.path.join(ROOT, "web", "js", "app.js")
    if os.path.exists(js):
        rc = step("syntax: node --check app.js", ["node", "--check", js])
        if rc:
            fails.append("syntax(js)")

    # 2. 单测
    rc = step("unit tests", [PY, "-m", "pytest", "tests", "-q"], timeout=300)
    if rc:
        fails.append("pytest")

    # 3. 重建派生产物
    for s in ("papers_prep.py", "papers_render.py", "perspectives_prep.py"):
        rc = step("regen: %s" % s, [PY, os.path.join(SRC, s)])
        if rc:
            fails.append(s)

    # 4. 深审
    for s in ("verify_core.py", "verify_perspectives.py", "verify_story_refs.py",
              "verify_papers.py"):
        rc = step("deep review: %s" % s, [PY, os.path.join(SRC, s)])
        if rc:
            fails.append(s)
    rc = step("sync_readme --check", [PY, os.path.join(SRC, "sync_readme.py"), "--check"])
    if rc:
        fails.append("sync_readme")

    # 5. 构建报告
    rc = step("build: generate_report.py", [PY, os.path.join(SRC, "generate_report.py")])
    if rc:
        fails.append("generate_report")

    # 6. 无头冒烟（需 Chrome/Edge）
    if not args.no_headless:
        try:
            from check_report import find_chrome
            find_chrome()
            rc = step("headless: check_report.py", [PY, os.path.join(SRC, "check_report.py")],
                      timeout=600)
            if rc:
                fails.append("check_report")
        except RuntimeError:
            print("\n[skip] 本机未安装 Chrome/Edge，跳过无头冒烟（CI 会安装后跑）")

    print("\n" + "=" * 60)
    if fails:
        print("门禁未通过：%s" % ", ".join(fails))
        sys.exit(1)
    print("全部门禁通过 ✓")
    sys.exit(0)


if __name__ == "__main__":
    main()
