# -*- coding: utf-8 -*-
"""统一构建入口（Phase 4）。

     python src/build.py                          # 全书 → index.html（单文件）
     python src/build.py --scope p3               # 叁部 → report_p3.html
     python src/build.py --target web             # 分离资源版 → dist/full/
     python src/build.py --check                  # 只校验不落盘

职责边界：
- ``generate_report.py`` 负责数据聚合（build_scope）与模板装载（load_template）；
- ``validators.py`` 负责 payload 不变量；
- 本文件只做「调度 + 渲染 + 落盘 + 退出码」，不再包含业务逻辑。

两个 target 的差别：
- ``standalone``（默认）：CSS/JS/DATA 全部内联，产物是可直接双击打开的单文件，
  用于 GitHub Pages 发布（唯一正式交付形态）。
- ``web``：CSS/JS/DATA 拆成 ``assets/`` 外链，便于本地调试与浏览器 DevTools
  逐文件断点；数据来自同一份 payload，因此两种产物内容等价。
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_report as G  # noqa: E402
import validators as V  # noqa: E402

SCOPES = ("full", "p1", "p2", "p3", "p4", "p5", "p6", "p7")
DIST_DIR = BASE / "dist"

# 单文件模板里的历史遗留：某处模板字符串多了一个反引号，发布前统一抹平
# （真正的替换在 generate_report.compose_document 里，此处只作说明锚点）。
# web target 下骨架里的两个锚点整块替换（含外层标签），需要与骨架逐字一致。
_STYLE_ANCHOR = "<style>\n/*{{INLINE_CSS}}*/</style>"
_SCRIPT_ANCHOR = "<script>\n/*{{INLINE_JS}}*/</script>"
_DATA_CONST = "const DATA=__DATA__;\n"
_INSIGHT_CONST = "const INSIGHT_DATA=__INSIGHT_DATA__;\n"


def _json_for_script(obj) -> str:
    """把 Python 对象序列化成可安全嵌进 <script> 的 JSON。

    ``</`` 必须转义，否则数据里一旦出现 ``</script>`` 会提前闭合脚本标签。
    """
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def render_standalone(payload: dict) -> str:
    """单文件形态：直接复用 generate_report 的注入实现，杜绝两套口径。"""
    return G.compose_document(payload)


# 数据域分块契约（与 web/js/data-loader.js 的 ALL_CHUNKS 一一对应）。
# boot 只保留元数据；下列键在 boot 中置空，完整数据拆到 assets/data-<name>.js 按需加载。
CHUNK_MAP = {
    "characters": ["characters"],
    "locations": ["locations"],
    "events": ["events"],
    "relations": ["relations"],
    "time": ["timeline"],
    "lifespans": ["lifespans"],
    "graphs": ["visualizations", "relationGraphFull", "relationGraphEntities"],
    "place-chapters": ["chapterLocations"],
    "voyages": ["voyages"],
    "insight": ["insightIndex"],
}


def _empty_like(value):
    """保留原类型（list→[]，dict→{}），boot 里占位，避免 app.js 顶层访问 undefined。"""
    return [] if isinstance(value, list) else {}


def split_boot_and_chunks(payload: dict) -> dict:
    """返回 boot：复制全量 payload，但把所有分块键置为空占位。"""
    boot = copy.deepcopy(payload)
    for keys in CHUNK_MAP.values():
        for k in keys:
            if k in boot:
                boot[k] = _empty_like(boot[k])
    return boot


def _chunk_file(name: str, data: dict) -> str:
    """生成一个分块文件：把数据并入全局 DATA 并标记 ready，再广播 ming:data-chunk。"""
    return (
        "(function(){Object.assign(DATA, %s);"
        "window.__MING_DATA_CHUNKS__['%s']=true;"
        "document.dispatchEvent(new CustomEvent('ming:data-chunk',{detail:{name:'%s'}}));})();\n"
        % (_json_for_script(data), name, name)
    )


def render_web(payload: dict, out_dir: Path) -> dict:
    """分离资源形态（按需加载版）：

    写 index.html + assets/{app.css, app.js, data.js(boot), data-loader.js,
    lazy-data.js, data-<chunk>.js}。首屏只下 boot 元数据，各数据域在视图/实体
    被访问时由 data-loader/lazy-data 注入式懒加载。
    """
    skeleton = G.TEMPLATE_PATH.read_text(encoding="utf-8")
    css = G.CSS_PATH.read_text(encoding="utf-8")
    js = G.JS_PATH.read_text(encoding="utf-8")
    for anchor, name in ((_STYLE_ANCHOR, "css"), (_SCRIPT_ANCHOR, "js")):
        if anchor not in skeleton:
            raise SystemExit("骨架缺少锚点 %s（%s 无法外链）" % (name, anchor))

    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "app.css").write_text(css, encoding="utf-8")

    # 运行时加载器（与 app.js 同目录的源文件）
    loader_src = BASE / "web" / "js"
    shutil.copyfile(loader_src / "data-loader.js", assets / "data-loader.js")
    shutil.copyfile(loader_src / "lazy-data.js", assets / "lazy-data.js")

    # boot：元数据全量，数据域置空
    boot = split_boot_and_chunks(payload)
    data_js = "const DATA=%s;\nconst INSIGHT_DATA=%s;\n" % (
        _json_for_script(boot),
        _json_for_script(G.INSIGHT_PAYLOAD),
    )
    (assets / "data.js").write_text(data_js, encoding="utf-8")

    # 各数据域分块
    written = {
        "index.html": 0,
        "assets/app.css": (assets / "app.css").stat().st_size,
        "assets/data.js": (assets / "data.js").stat().st_size,
        "assets/data-loader.js": (assets / "data-loader.js").stat().st_size,
        "assets/lazy-data.js": (assets / "lazy-data.js").stat().st_size,
    }
    for name, keys in CHUNK_MAP.items():
        chunk = {k: payload[k] for k in keys if k in payload}
        cf = assets / ("data-%s.js" % name)
        cf.write_text(_chunk_file(name, chunk), encoding="utf-8")
        written["assets/data-%s.js" % name] = cf.stat().st_size

    # app.js：剥离内联数据常量（数据改由 data.js + 分块提供）
    body = js.replace(_DATA_CONST, "", 1).replace(_INSIGHT_CONST, "", 1)
    (assets / "app.js").write_text(body, encoding="utf-8")
    written["assets/app.js"] = (assets / "app.js").stat().st_size

    # index.html：脚本顺序 data.js → data-loader.js → app.js → lazy-data.js
    # （data-loader 需 DATA；lazy-data 需 setView + __MING_ENSURE_*，故在 app.js 之后）
    html = skeleton.replace(_STYLE_ANCHOR, '<link rel="stylesheet" href="assets/app.css">')
    html = html.replace(
        _SCRIPT_ANCHOR,
        '<script src="assets/data.js"></script>\n'
        '<script src="assets/data-loader.js"></script>\n'
        '<script src="assets/app.js"></script>\n'
        '<script src="assets/lazy-data.js"></script>',
    )
    html = html.replace("__TITLE__", payload["scopeLabel"])
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    written["index.html"] = (out_dir / "index.html").stat().st_size
    return written


def check_render(payload: dict, findings: list) -> list:
    """渲染层自检：锚点是否齐全、替换后是否残留占位符。"""
    doc = render_standalone(payload)
    for token in ("__DATA__", "__INSIGHT_DATA__", "__TITLE__"):
        if token in doc:
            findings.append(V.Finding(V.ERROR, "V-TPL-01", "渲染后仍残留占位符 %s" % token))
    if "const DATA=" not in doc:
        findings.append(V.Finding(V.ERROR, "V-TPL-02", "渲染结果里找不到 DATA 注入点"))
    if not doc.rstrip().endswith("</html>"):
        findings.append(V.Finding(V.ERROR, "V-TPL-03", "渲染结果未正常闭合 </html>"))
    if len(doc) < 500_000:
        findings.append(
            V.Finding(V.WARNING, "V-TPL-04", "渲染结果仅 %d 字符，远小于历史规模，可能数据缺失" % len(doc))
        )
    skeleton = G.TEMPLATE_PATH.read_text(encoding="utf-8")
    for anchor in (_STYLE_ANCHOR, _SCRIPT_ANCHOR):
        if anchor not in skeleton:
            findings.append(V.Finding(V.ERROR, "V-TPL-05", "骨架缺少锚点：%s" % anchor))
    return findings


def _default_out(scope: str, target: str) -> Path:
    if target == "web":
        return DIST_DIR / scope
    if scope == "full":
        return BASE / "index.html"
    return BASE / ("report_%s.html" % scope)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="明朝知识报告统一构建入口")
    parser.add_argument("--scope", choices=SCOPES, default="full", help="构建范围，默认全书")
    parser.add_argument("--target", choices=("standalone", "web"), default="standalone", help="产物形态")
    parser.add_argument("--out", type=Path, default=None, help="覆盖输出路径（文件或目录）")
    parser.add_argument("--check", action="store_true", help="只做校验与内存渲染，不写任何文件")
    parser.add_argument("--json", type=Path, default=None, help="把校验结论写成 JSON")
    parser.add_argument("--quiet", action="store_true", help="只打印一行结论")
    args = parser.parse_args(argv)

    payload = G.build_scope(args.scope)
    metrics = " · ".join("%s %s" % (k, v) for k, v in payload["metrics"].items())
    if not args.quiet:
        print("[1/3] 数据聚合完成：%s" % metrics)

    findings = V.validate_payload(payload)
    findings = check_render(payload, findings)
    findings = V.sort_findings(findings)
    counts = V.count_by_severity(findings)
    if args.json:
        V.write_json(findings, args.json)
    if not args.quiet:
        print("[2/3] %s" % V.format_report(findings, "scope=%s target=%s" % (args.scope, args.target)))
    else:
        print("校验：ERROR %d / WARNING %d / INFO %d" % (counts[V.ERROR], counts[V.WARNING], counts[V.INFO]))

    if V.has_errors(findings):
        print("[!] 存在 ERROR，已中止构建（数据自相矛盾，不要发布）", file=sys.stderr)
        return 2

    if args.check:
        print("[3/3] --check：未写入任何文件")
        return 0

    out = args.out or _default_out(args.scope, args.target)
    if args.target == "standalone":
        out.parent.mkdir(parents=True, exist_ok=True)
        doc = render_standalone(payload)
        out.write_text(doc, encoding="utf-8")
        print("[3/3] 单文件已生成 %s（%d 字符 / %.1f MB）" % (out, len(doc), out.stat().st_size / 1048576))
    else:
        out.mkdir(parents=True, exist_ok=True)
        written = render_web(payload, out)
        print("[3/3] 分离资源已生成 %s" % out)
        for name, size in written.items():
            print("      %-32s %7.1f KB" % (name, size / 1024.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
