# -*- coding: utf-8 -*-
"""把 web/css/theme-ming.css 镜像进明书报告的模板主题块。

与 sync_theme.py / sync_experience.py 同一套约定：
  - 人工只维护 web/css/theme-ming.css；
  - 模板里的对应 <style> 块是生成镜像，勿手改；
  - standalone.html 与 ming/ 分层版共用 web/template/index.html，
    因此只镜像一次，两种交付形态自带同一套母题皮肤。

为什么放在 </head> 前：模板首个 <style> 是 build.py 的 INLINE_CSS 占位块
（web target 会被换成 <link>），不能用；放到最后还保证母题覆写的优先级
高于 app.css / theme.css / experience.css。

用法：
    python src/sync_ming_theme.py
    python src/sync_ming_theme.py --check
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
TEMPLATE = BASE / "web" / "template" / "index.html"
SOURCE = BASE / "web" / "css" / "theme-ming.css"

SOURCE_ATTR = 'data-generated-from="web/css/theme-ming.css"'
START = "/* MING_THEME_SYNC_START */"
END = "/* MING_THEME_SYNC_END */"


def generated_block(css: str) -> str:
    return '<style %s>\n%s\n%s\n%s\n</style>' % (
        SOURCE_ATTR, START, css.rstrip(), END)


def render_template(source: str, css: str) -> str:
    block = generated_block(css)
    pattern = re.compile(
        r'<style\s+data-generated-from="web/css/theme-ming\.css">\n'
        r'/\* MING_THEME_SYNC_START \*/.*?/\* MING_THEME_SYNC_END \*/\n</style>',
        re.DOTALL,
    )
    if pattern.search(source):
        updated, count = pattern.subn(lambda _m: block, source, count=1)
    else:
        if source.count("</head>") != 1:
            raise SystemExit("模板 </head> 锚点数量不是 1，无法插入母题主题块")
        updated = source.replace("</head>", block + "\n</head>", 1)
        count = 1
    if count != 1:
        raise SystemExit("母题主题镜像锚点异常：匹配 %d 处" % count)
    if any(updated.count(t) != 1 for t in (SOURCE_ATTR, START, END)):
        raise SystemExit("母题主题镜像标记数量异常（可能重复插入）")
    return updated


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="同步明书母题主题 CSS 到 standalone 模板")
    ap.add_argument("--check", action="store_true", help="只检查镜像是否最新")
    args = ap.parse_args(argv)

    if not SOURCE.is_file():
        print("[error] 缺少真源：%s" % SOURCE, file=sys.stderr)
        return 2
    css = SOURCE.read_text(encoding="utf-8")
    current = TEMPLATE.read_text(encoding="utf-8")
    updated = render_template(current, css)
    if updated == current:
        print("[check] OK：主题镜像已是最新" if args.check else "[done] 已是最新，无需写入")
        return 0
    if args.check:
        print("[check] 失败：模板里的母题主题镜像落后，请跑 python src/sync_ming_theme.py",
              file=sys.stderr)
        return 1
    TEMPLATE.write_text(updated, encoding="utf-8", newline="\n")
    print("[done] 已同步 %s → %s（%d 字节 CSS）" %
          (SOURCE.relative_to(BASE), TEMPLATE.relative_to(BASE), len(css.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
