# -*- coding: utf-8 -*-
"""
交付能力自检：把 README 路线图里「已完成」的声明变成可执行的断言
==============================================================
路线图以前是凭记忆维护的四条 `- [ ]`，其中两条其实早就做完了却一直没销账，
另一条把「离线单文件」和「按需加载」混为一谈。本脚本把能机器验证的事实
固定下来，改坏了 CI 立刻红，而不是等下次有人翻 README 才发现。

只做静态检查（不启浏览器）：浏览器级的行为取证在
`tests/browser_check.py` 与 `.ci/verify_roadmap.py` 里做过，这里守住结构前提。

用法：
    python src/check_delivery.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MING = BASE / "ming"
ASSETS = MING / "assets"
BOOT_MAX_KB = 500          # boot 元数据上限；超了说明又把全量数据塞回 data.js
CHUNK_MIN_COUNT = 8        # 数据分块数量下限
CHUNK_MIN_MB = 2.0         # 分块总量下限（太小说明拆了个寂寞）
SKELETON_MAX_KB = 40       # 分层版骨架上限（内联全量数据会撑爆它）


def kb(path: Path) -> float:
    return path.stat().st_size / 1024 if path.exists() else 0.0


def chunks():
    """真正的数据分块；data.js 是 boot，data-loader.js / lazy-data.js 是加载器。"""
    skip = {"data.js", "data-loader.js", "lazy-data.js", "app.js", "app.css"}
    return sorted(p for p in ASSETS.glob("data-*.js") if p.name not in skip)


def check() -> list:
    """返回 [(是否通过, 断言名, 实测值说明)]。"""
    out = []

    # ---- ① 明书分层版：按需加载是真的，不是把 5 MB 换了个文件名 ----
    boot = ASSETS / "data.js"
    out.append((boot.is_file() and 0 < kb(boot) < BOOT_MAX_KB,
                "ming/ boot 元数据是精简版",
                "data.js %.0f KB（上限 %d KB）" % (kb(boot), BOOT_MAX_KB)))
    cs = chunks()
    total_mb = sum(p.stat().st_size for p in cs) / 1048576
    out.append((len(cs) >= CHUNK_MIN_COUNT and total_mb >= CHUNK_MIN_MB,
                "ming/ 数据确实被拆成按需分块",
                "%d 个分块 / 共 %.1f MB" % (len(cs), total_mb)))
    skel = MING / "index.html"
    out.append((skel.is_file() and kb(skel) < SKELETON_MAX_KB,
                "ming/ 骨架没有内联全量数据",
                "index.html %.1f KB（上限 %d KB）" % (kb(skel), SKELETON_MAX_KB)))
    s = skel.read_text(encoding="utf-8") if skel.is_file() else ""
    out.append(("assets/data-loader.js" in s and "assets/lazy-data.js" in s,
                "ming/ 骨架挂载了两个加载器", "data-loader.js + lazy-data.js"))

    # ---- ② 洞察长文与图谱实体互跳：正向 / 反向两侧都必须在 ----
    js = (BASE / "web/js/app.js").read_text(encoding="utf-8")
    out.append(("function linkifyInsight(" in js and "function insightBlock(" in js,
                "洞察 ↔ 实体互跳双向实现都在", "linkifyInsight + insightBlock"))
    out.append(("data-ins-goto" in js and "ins-link ins-" in js,
                "正向（正文→实体卡）与反向（卡片→章节）钩子都在",
                "data-ins-goto + .ins-link"))

    # ---- ③ standalone.html 是有意的离线单文件，别误当按需加载未做 ----
    st = BASE / "standalone.html"
    st_text = st.read_text(encoding="utf-8") if st.is_file() else ""
    out.append((st.is_file() and "const DATA=" in st_text,
                "离线单文件仍自带全量数据", "%.2f MB" % (st.stat().st_size / 1048576)))
    out.append(('<script src="assets/' not in st_text,
                "离线单文件不依赖任何外链资源", "无 assets/ 外链"))

    # ---- ④ 书库导航条：5 本报告 + 门户的连通性 ----
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import sync_shelf as S  # noqa: E402
    targets = S.targets()
    missing = [href for href, _b, _base in targets if not (BASE / href).is_file()]
    out.append((not missing and len(targets) >= 6,
                "书库导航条覆盖全部报告产物", "%d 个目标" % len(targets)))
    no_bar = []
    for href, _b, _base in targets:
        p = BASE / href
        # 不能只搜文件头：tiancai / feitu / sanggan 的 <style> 就有几十 KB，
        # 导航条紧跟 <body>，在几万字节之后（第一版只扫 20KB 全部误报）。
        if p.is_file() and b"BOOK_SHELF_START" not in p.read_bytes():
            no_bar.append(href)
    out.append((not no_bar, "各报告已注入书库导航条",
                "缺条：%s" % "、".join(no_bar) if no_bar else "全部在位"))

    hub = (BASE / "index.html").read_text(encoding="utf-8")
    out.append((all(t in hub for t in ('id="book-search"', 'id="book-sort"',
                                       'id="theme-btn"', 'class="skip-link"')),
                "书库门户具备搜索 / 排序 / 明暗 / 跳转链接", "4 项齐全"))
    return out


def main(argv=None) -> int:
    results = check()
    bad = 0
    for ok, name, detail in results:
        print("[%s] %-38s %s" % ("OK" if ok else "FAIL", name, detail))
        bad += not ok
    print("\n交付能力断言 %d 项，失败 %d 项" % (len(results), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
