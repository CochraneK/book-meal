# -*- coding: utf-8 -*-
"""论文单篇「骨架准备」：复制已核验的 references.bib + 重出三张矢量图。

用法： python _dump/_prep.py <pid>
     python _dump/_prep.py <pid> --allfigs       （连 fig1/fig2 一并重出）
     python _dump/_prep.py <pid> --generic        （跑 write_generic.py 的 spec 层）
"""
import os
import subprocess
import sys

ROOT = r"D:\2026\WB项目\明朝"
PY = sys.executable
LIB = os.path.join(ROOT, "papers_pilot", "_lib")
SRC_BIB = os.path.join(ROOT, "papers_pilot", "psychology", "paper", "references.bib")


def sh(cmd, cwd=ROOT):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tail = (r.stdout or "").strip().splitlines()[-25:]
    print("  $ %s -> %d" % (" ".join(cmd), r.returncode))
    for l in tail:
        print("    " + l)
    if r.returncode != 0:
        print("  STDERR:", (r.stderr or "")[-800:])
    return r.returncode


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = set(a for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        print(__doc__); return 1
    pid = args[0]
    rc = 0

    bib = os.path.join(ROOT, "papers_pilot", pid, "paper", "references.bib")
    # 踩坑：旧骨架会在 references.bib 里先写一行空注释头（<200 B），
    # 若只判 exists 就会永久沿用空 bib，编译warning「Citation undefined」、闸 1 报「引用 0」。
    # 改判「不存在或小于 200 B 就重拷」。
    if not os.path.exists(bib) or os.path.getsize(bib) < 200:
        os.makedirs(os.path.dirname(bib), exist_ok=True)
        open(bib, "w", encoding="utf-8").write(
            open(SRC_BIB, encoding="utf-8").read().replace(
                "psychology 篇：", "%s 篇：" % pid).replace(
                "心理篇：", "%s 篇：" % pid))
        print("[prep] copied references.bib <- psychology (%d B)" % os.path.getsize(bib))

    if "--allfigs" in flags or "--genfigs" in flags:
        rc |= sh([PY, os.path.join(LIB, "gen_figs.py"), pid])

    if "--generic" in flags:
        rc |= sh([PY, os.path.join(LIB, "write_generic.py"), pid])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
