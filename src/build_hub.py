# -*- coding: utf-8 -*-
"""多书聚合门户生成器（平台层）。

把 CochraneK/ming 从「单书站」改造为「多书拆解聚合平台」后，
仓库根目录的 ``index.html`` 不再是某本书的报告，而是由本脚本生成的**书库门户**：

    books/
      <book_id>/
        manifest.json     # 书目名片（书名/作者/类型/指标/入口/更新时间）
        index.html        # 该书报告（单文件离线，或分层版入口）
        assets/           # 分层资源（可选）
        standalone.html   # 离线单文件版（可选）

设计原则（内容 / 平台分离）：
- **新增一本书 = 放一个目录 + 一份 manifest**，不需要改本脚本、不需要改 CI；
- 门户只读 manifest，不读各书的 payload，因此永远保持轻量；
- 产物是单文件 HTML，不引任何 CDN，双击可开。

用法::

    python src/build_hub.py                # 生成根 index.html
    python src/build_hub.py --check        # 只校验不落盘
    python src/build_hub.py --out PATH     # 指定输出路径

兼容：本仓改造前，根路径就是《明朝那些事儿》报告，其深链全部挂在 ``#hash``
上（web/js/app.js 读 ``location.hash``）。生成的门户内置一段重定向：
带 hash 访问根时自动跳 ``ming/<hash>``，旧链接不失效。
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BOOKS_DIR = BASE / "books"

KIND_LABELS = {
    "history": "历史",
    "modern_real": "现代现实",
    "fictional_world": "幻想世界",
    "humanities": "人文",
    "other": "其他",
}

# 卡片排序：order 小的在前；缺省排最后（保持稳定）
DEFAULT_ORDER = 99


def esc(v) -> str:
    """HTML 转义。None → 空串，数字原样。"""
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return str(v)
    return html.escape(str(v), quote=True)


def load_manifests(books_dir: Path = BOOKS_DIR):
    """扫描 books/*/manifest.json，返回 (manifests, warnings)。"""
    manifests, warnings = [], []
    if not books_dir.is_dir():
        return manifests, ["books/ 目录不存在：%s" % books_dir]

    for child in sorted(books_dir.iterdir()):
        mf = child / "manifest.json"
        if not mf.is_file():
            continue
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - 坏 manifest 不应中断整站
            warnings.append("manifest 解析失败，已跳过：%s（%s）" % (mf, exc))
            continue
        if not data.get("title"):
            warnings.append("manifest 缺少 title，已跳过：%s" % mf)
            continue
        data.setdefault("id", child.name)
        data.setdefault("kind", "other")
        data.setdefault("metrics", {})
        data.setdefault("report", "index.html")
        data["_order"] = data.get("order", DEFAULT_ORDER)
        manifests.append(data)

    manifests.sort(key=lambda m: (m["_order"], str(m.get("id", ""))))
    return manifests, warnings


def report_href(m) -> str:
    """卡片「打开」链接。external 书的 report 视为绝对/站外地址。

    report 为纯文件名（如 `index.html`）时按 `books/<id>/<report>` 拼接；
    含 `/` 则视为站内相对路径原样使用，供报告不在 `books/<id>/` 下的情形
    （例：明书下沉到仓库根 `ming/`，写作 `ming/index.html`）。

    路径一律相对门户页（它就在仓库根）解析。本站挂在 GitHub Pages 子路径 `/ming/`，
    **不能**用 `/` 开头的绝对路径——那会跳到域名根。
    """
    rep = str(m.get("report", "index.html"))
    if m.get("external") or "/" in rep:
        return rep
    return "books/%s/%s" % (m.get("id", ""), rep)


def _card(m) -> str:
    kind = str(m.get("kind", "other"))
    kind_label = KIND_LABELS.get(kind, kind)
    metrics = m.get("metrics") or {}
    ch = m.get("chapters")

    badges = []
    if m.get("external"):
        badges.append('<span class="bdg bdg-ext">外链</span>')
    if m.get("note"):
        badges.append('<span class="bdg bdg-note">%s</span>' % esc(m.get("note")))
    badge_html = "".join(badges)

    metrics_html = "".join(
        '<div class="mt"><b>%s</b><span>%s</span></div>' % (esc(metrics.get(key)), esc(label))
        for key, label in (("characters", "人物"), ("events", "事件"), ("relations", "关系"))
    )

    chapters_html = (
        '<span class="ch">%s 章</span>' % esc(ch) if ch else ""
    )

    return (
        '<article class="card" data-kind="{kind}" style="--accent:{accent}">'
        '<div class="card-hd">'
        '<span class="bdg bdg-kind">{kind_label}</span>{badges}'
        "</div>"
        "<h2>{title}</h2>"
        '<p class="author">{author}</p>'
        '<p class="desc">{desc}</p>'
        '<div class="mts">{metrics_html}</div>'
        '<div class="card-ft">'
        "<span>{updated}{chapters}</span>"
        '<a class="open" href="{href}">打开报告 →</a>'
        "</div>"
        "</article>"
    ).format(
        kind=esc(kind),
        accent=esc(m.get("accent", "#5a4b8c")),
        kind_label=esc(kind_label),
        badges=badge_html,
        title=esc(m.get("title")),
        author=esc(m.get("author", "")),
        desc=esc(m.get("desc", "")),
        metrics_html=metrics_html,
        updated=esc(m.get("updated", "")),
        chapters=chapters_html,
        href=esc(report_href(m)),
    )


CSS = """
:root{
  --bg:#f6f4ef; --panel:#ffffff; --ink:#2b2620; --ink-soft:#6f675c;
  --line:#e3ddd2; --accent:#5a4b8c; --chip:#efeae0;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Source Han Sans SC",sans-serif;
  line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:48px 24px 64px}
header.hub{border-bottom:1px solid var(--line);padding-bottom:28px;margin-bottom:28px}
h1{font-size:30px;margin:0 0 6px;letter-spacing:.5px}
.sub{color:var(--ink-soft);font-size:14px;margin:0 0 22px}
.summary{display:flex;flex-wrap:wrap;gap:28px}
.summary .sm{display:flex;flex-direction:column}
.summary .sm b{font-size:26px;font-variant-numeric:tabular-nums}
.summary .sm span{font-size:12px;color:var(--ink-soft);letter-spacing:1px}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 24px}
.chip{border:1px solid var(--line);background:var(--chip);color:var(--ink-soft);
  border-radius:999px;padding:5px 14px;font-size:13px;cursor:pointer;transition:.15s}
.chip:hover{border-color:var(--accent);color:var(--ink)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(316px,1fr));gap:20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:20px 22px 18px;display:flex;flex-direction:column;
  border-left:4px solid var(--accent);box-shadow:0 1px 2px rgba(43,38,32,.04)}
.card-hd{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap}
.bdg{font-size:11px;padding:2px 9px;border-radius:999px;letter-spacing:.5px;white-space:nowrap}
.bdg-kind{background:#eef0f6;color:#4a4f6b}
.bdg-ext{background:#e8f1ec;color:#2f6b4f}
.bdg-note{background:#f4ecf8;color:#6b4a8c}
.card h2{font-size:19px;margin:0 0 2px}
.author{font-size:13px;color:var(--ink-soft);margin:0 0 10px}
.desc{font-size:13.5px;color:#4a443b;margin:0 0 16px;flex:1}
.mts{display:flex;gap:22px;border-top:1px dashed var(--line);padding-top:12px;margin-bottom:12px}
.mt{display:flex;flex-direction:column}
.mt b{font-size:19px;font-variant-numeric:tabular-nums}
.mt span{font-size:11px;color:var(--ink-soft)}
.card-ft{display:flex;justify-content:space-between;align-items:center;
  font-size:12px;color:var(--ink-soft)}
.card-ft .ch{margin-left:8px}
.open{color:var(--accent);text-decoration:none;font-weight:600;font-size:13px}
.open:hover{text-decoration:underline}
footer{margin-top:40px;padding-top:18px;border-top:1px solid var(--line);
  font-size:12px;color:var(--ink-soft)}
.empty{grid-column:1/-1;text-align:center;color:var(--ink-soft);padding:48px 0}
@media (max-width:560px){.wrap{padding:28px 16px}.summary{gap:18px}}
"""

JS = """
(function(){
  // 旧深链兼容：改造前根路径即《明朝那些事儿》报告，深链全在 #hash。
  // 带 hash 访问本门户时，转交 ming/ 下的报告（hash 原样保留）。
  var h = location.hash;
  if (h && h.length > 1) { location.replace('ming/' + h); return; }

  var chips = document.querySelectorAll('.chip');
  var cards = document.querySelectorAll('.card');
  chips.forEach(function(c){
    c.addEventListener('click', function(){
      chips.forEach(function(x){ x.classList.remove('on'); });
      c.classList.add('on');
      var k = c.getAttribute('data-kind');
      cards.forEach(function(card){
        card.style.display = (!k || k === 'all' || card.getAttribute('data-kind') === k) ? '' : 'none';
      });
    });
  });
})();
"""


def render(manifests, warnings, base: Path = BASE) -> str:
    total = {
        "characters": sum(int((m.get("metrics") or {}).get("characters") or 0) for m in manifests),
        "events": sum(int((m.get("metrics") or {}).get("events") or 0) for m in manifests),
        "relations": sum(int((m.get("metrics") or {}).get("relations") or 0) for m in manifests),
    }

    kinds = []
    for m in manifests:
        k = str(m.get("kind", "other"))
        if k not in kinds:
            kinds.append(k)
    chips = ['<button class="chip on" data-kind="all">全部 %d</button>' % len(manifests)]
    for k in kinds:
        n = sum(1 for m in manifests if str(m.get("kind", "other")) == k)
        chips.append(
            '<button class="chip" data-kind="%s">%s %d</button>'
            % (esc(k), esc(KIND_LABELS.get(k, k)), n)
        )

    cards = "".join(_card(m) for m in manifests)
    if not cards:
        cards = '<div class="empty">books/ 下还没有任何 manifest.json</div>'

    warn_html = ""
    if warnings:
        items = "".join("<li>%s</li>" % esc(w) for w in warnings)
        warn_html = '<ul class="empty" style="text-align:left;color:#9a6b2f">%s</ul>' % items

    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>书库 · 拆书平台</title>\n"
        "<style>%s</style>\n</head>\n<body>\n"
        '<div class="wrap">\n'
        '<header class="hub">\n'
        "<h1>书库 · 拆书平台</h1>\n"
        '<p class="sub">长篇小说与知识类书籍的结构化拆解：五元组知识图谱、地点坐标、'
        "关系网络与多视角分析。每本书一份单文件离线报告。</p>\n"
        '<div class="summary">\n'
        '<div class="sm"><b>%d</b><span>本书</span></div>\n'
        '<div class="sm"><b>%d</b><span>人物</span></div>\n'
        '<div class="sm"><b>%d</b><span>事件</span></div>\n'
        '<div class="sm"><b>%d</b><span>关系</span></div>\n'
        "</div>\n</header>\n"
        '<nav class="filters">%s</nav>\n'
        '<main class="grid">%s</main>\n'
        "%s"
        "<footer>由 src/build_hub.py 扫描 books/*/manifest.json 生成 · "
        "新增书籍只需放入 books/&lt;id&gt;/ 并附一份 manifest.json · "
        "报告均为单文件离线 HTML，不引用任何外部 CDN</footer>\n"
        "</div>\n"
        "<script>%s</script>\n"
        "</body>\n</html>\n"
    ) % (
        CSS,
        len(manifests),
        total["characters"],
        total["events"],
        total["relations"],
        "".join(chips),
        cards,
        warn_html,
        JS,
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成多书聚合门户（根 index.html）")
    ap.add_argument("--out", default=None, help="输出路径（默认仓库根 index.html）")
    ap.add_argument("--books", default=None, help="books 目录（默认 <repo>/books）")
    ap.add_argument("--check", action="store_true", help="只校验不落盘")
    ap.add_argument("--quiet", action="store_true", help="减少输出")
    args = ap.parse_args(argv)

    books_dir = Path(args.books) if args.books else BOOKS_DIR
    manifests, warnings = load_manifests(books_dir)

    # 断链校验：卡片「打开报告」指向的文件必须真实存在（站外地址不校验）。
    # 踩过的坑：明书产物下沉到 ming/ 后，manifest 仍写 index.html，
    # 门户照旧拼成 books/ming/index.html —— 页面能生成、测试也能过，但点进去是 404。
    for m in manifests:
        href = report_href(m)
        if href.startswith(("http://", "https://")):
            continue
        if not (BASE / href).exists():
            warnings.append("卡片链接指向的文件不存在：%s → %s" % (m.get("id"), href))

    for w in warnings:
        print("[warn]", w)

    if not args.quiet:
        print("扫描 %s：%d 本书" % (books_dir, len(manifests)))
        for m in manifests:
            print("  - %-10s %s（%s）" % (m.get("id"), m.get("title"), m.get("author", "")))

    out = Path(args.out) if args.out else BASE / "index.html"
    doc = render(manifests, warnings, BASE)

    # 落盘前自查：模板占位符不得残留（f-string/format 泄漏是已犯过的坑）
    for marker in ("{esc(", "{cards", "{chips", "{CSS", "{JS",
                   "{metrics_html", "{badges", "{href", "{kind_label"):
        if marker in doc:
            print("[error] 产物中残留未渲染占位符：%s" % marker)
            return 2

    if args.check:
        if warnings:
            print("[check] 失败：%d 个问题（见上）" % len(warnings))
            return 1
        print("[check] OK（未落盘）→ %s" % out)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    if not args.quiet:
        print("✓ 门户已生成：%s（%.1f KB）" % (out, out.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
