# -*- coding: utf-8 -*-
"""多书聚合门户生成器（平台层）。

把 CochraneK/book-meal（原 CochraneK/ming）从「单书站」改造为「多书拆解聚合平台」后，
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

    路径一律相对门户页（它就在仓库根）解析。本站挂在 GitHub Pages 子路径 `/book-meal/`
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
    glyph = str(m.get("glyph") or (m.get("title") or "")[:1])

    badges = []
    if m.get("external"):
        badges.append('<span class="bdg bdg-ext">外链</span>')
    if m.get("note"):
        badges.append('<span class="bdg bdg-note">%s</span>' % esc(m.get("note")))
    badge_html = "".join(badges)

    stats_html = "".join(
        '<div><b>%s</b><span>%s</span></div>' % (esc(metrics.get(key)), esc(label))
        for key, label in (("characters", "人物"), ("events", "事件"), ("relations", "关系"))
    )
    if ch:
        stats_html += '<div><b>%s</b><span>章</span></div>' % esc(ch)

    meta_line = " · ".join(
        x for x in (m.get("author", ""), m.get("subtitle", "")) if x
    )

    return (
        '<article class="card" data-kind="{kind}" style="--accent:{accent}">'
        '<div class="cover" aria-hidden="true"><span class="glyph">{glyph}</span>'
        '<span class="cover-kind">{kind_label}</span></div>'
        '<div class="body">'
        '<div class="k-row"><span class="bdg bdg-kind">{kind_label}</span>{badges}</div>'
        "<h2>{title}</h2>"
        '<p class="author">{meta}</p>'
        '<p class="desc">{desc}</p>'
        '<div class="mts">{stats_html}</div>'
        '<div class="ft"><span>{updated}</span>'
        '<a class="open" href="{href}">打开报告 <i>→</i></a></div>'
        "</div></article>"
    ).format(
        kind=esc(kind),
        accent=esc(m.get("accent", "#8a4a2f")),
        glyph=esc(glyph),
        kind_label=esc(kind_label),
        badges=badge_html,
        title=esc(m.get("title")),
        meta=esc(meta_line),
        desc=esc(m.get("desc", "")),
        stats_html=stats_html,
        updated=("更新 " + esc(m.get("updated"))) if m.get("updated") else "",
        href=esc(report_href(m)),
    )

CSS = """
:root{
  --bg:#f2eee6; --paper:#fffdf8; --ink:#27231f; --muted:#716960;
  --line:#ded6c9; --accent:#8d3025; --gold:#b88b35;
  --shadow:0 8px 24px rgba(42,31,21,.08);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;
  line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1160px;margin:0 auto;padding:40px 24px 64px}
.hero{display:grid;grid-template-columns:1.45fr 1fr;gap:24px;align-items:center;
  background:linear-gradient(180deg,#342c25,#2a241f);color:#f7efe2;
  border-radius:14px;padding:34px 36px;margin-bottom:22px;box-shadow:var(--shadow)}
.kicker{margin:0 0 10px;color:#d8bf86;font-size:13px;letter-spacing:.2em}
.hero h1{margin:0;font-size:34px;line-height:1.22;color:#fff;font-weight:800;letter-spacing:.01em}
.lede{margin:14px 0 0;color:#dfd0c1;font-size:14px;line-height:1.7;max-width:52ch}
.hero-stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:0}
.hero-stats>div{background:rgba(255,255,255,.06);border:1px solid rgba(200,168,106,.28);border-radius:10px;padding:12px 14px}
.hero-stats dd{margin:0;font-size:28px;line-height:1.05;font-weight:800;color:#f3e3c4;font-variant-numeric:tabular-nums}
.hero-stats dt{margin-top:4px;color:#cdbfa9;font-size:12px}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}
.chip{border:1px solid var(--line);background:var(--paper);color:var(--muted);
  border-radius:999px;padding:6px 15px;font-size:13px;cursor:pointer;transition:.15s}
.chip:hover{border-color:var(--accent);color:var(--ink)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:18px}
.card{display:flex;background:var(--paper);border:1px solid var(--line);border-radius:12px;
  overflow:hidden;box-shadow:0 2px 9px rgba(50,40,30,.05);
  transition:transform .15s ease,box-shadow .15s ease}
.card:hover{transform:translateY(-3px);box-shadow:var(--shadow)}
.cover{flex:0 0 96px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;
  padding:18px 8px 12px;color:#fff;background:var(--accent);
  background:linear-gradient(160deg,var(--accent),color-mix(in srgb,var(--accent) 60%,#1d1713))}
.glyph{font-family:'Songti SC','STSong','SimSun',serif;font-size:42px;font-weight:700;line-height:1;margin-top:8px}
.cover-kind{font-size:10px;letter-spacing:.18em;opacity:.85;writing-mode:vertical-rl}
.body{flex:1;min-width:0;padding:16px 18px 14px;display:flex;flex-direction:column}
.k-row{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.bdg{font-size:11px;padding:1px 8px;border-radius:999px;letter-spacing:.04em;white-space:nowrap}
.bdg-kind{background:#f3ece0;color:#8a6a2a}
.bdg-ext{background:#e8f1ec;color:#2f6b4f}
.bdg-note{background:#f6efe4;color:#86632a}
.card h2{margin:0;font-size:20px;line-height:1.3;color:#2f2822}
.author{margin:3px 0 0;font-size:12px;color:var(--muted)}
.desc{margin:10px 0 14px;font-size:13px;color:#4a443b;flex:1;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.mts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;
  border-top:1px dashed var(--line);padding-top:10px;margin-bottom:10px}
.mts b{display:block;font-size:16px;font-variant-numeric:tabular-nums;color:#3a3029}
.mts span{font-size:10.5px;color:var(--muted)}
.ft{display:flex;justify-content:space-between;align-items:center;gap:8px;
  font-size:11.5px;color:var(--muted)}
.open{color:var(--accent);text-decoration:none;font-weight:700;font-size:12.5px;white-space:nowrap}
.open i{font-style:normal;transition:transform .15s}
.open:hover i{display:inline-block;transform:translateX(2px)}
footer{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
.empty{grid-column:1/-1;text-align:center;color:var(--muted);padding:48px 0}
@media(max-width:900px){.hero{grid-template-columns:1fr}.hero h1{font-size:28px}.hero-stats{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:640px){
  .wrap{padding:24px 14px 48px}
  .hero{padding:24px 22px}
  .hero h1{font-size:25px}
  .hero-stats{grid-template-columns:repeat(2,minmax(0,1fr))}
  .grid{grid-template-columns:1fr}
  .card{flex-direction:column}
  .cover{flex:none;width:100%;height:84px;flex-direction:row;justify-content:flex-start;gap:12px;padding:0 18px}
  .glyph{margin:0;font-size:32px}
  .cover-kind{writing-mode:horizontal-tb}
}
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
        '<header class="hero">\n'
        "<div>\n"
        '<p class="kicker">书库 · 拆书平台</p>\n'
        "<h1>%d 本书，拆成可读的结构</h1>\n"
        '<p class="lede">长篇小说与知识类书籍的结构化拆解：五元组知识图谱、地点坐标、'
        "关系网络与多视角分析。每本书一份单文件离线报告，按章节保留来源与核验状态。</p>\n"
        "</div>\n"
        '<dl class="hero-stats">\n'
        '<div><dd>%d</dd><dt>本书</dt></div>\n'
        '<div><dd>%d</dd><dt>人物</dt></div>\n'
        '<div><dd>%d</dd><dt>事件</dt></div>\n'
        '<div><dd>%d</dd><dt>关系</dt></div>\n'
        "</dl>\n</header>\n"
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
