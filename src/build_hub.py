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
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BOOKS_DIR = BASE / "books"

# 书单的单一真源：门户 / README / 各报告的书库导航条都读它。
# 这里保留 KIND_LABELS / DEFAULT_ORDER / load_manifests / report_href 作为
# 对外名字（sync_readme.py 在用），实现全部委托过去，避免两份口径漂移。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_registry as REG  # noqa: E402

KIND_LABELS = REG.KIND_LABELS

# 书卡上的「气质」标签：一眼看出这本书的报告偏重什么，而不只是类型名。
KIND_TRAITS = {
    "history": "圣地巡礼 · 年谱",
    "modern_real": "现实图谱 · 深描",
    "fictional_world": "世界观 · 阶段轴",
    "humanities": "多视角 · 论文",
    "other": "结构化拆解",
}

# 卡片排序：order 小的在前；缺省排最后（保持稳定）
DEFAULT_ORDER = REG.DEFAULT_ORDER


def esc(v) -> str:
    """HTML 转义。None → 空串，数字原样。"""
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return str(v)
    return html.escape(str(v), quote=True)


def load_manifests(books_dir: Path = BOOKS_DIR):
    """扫描 books/*/manifest.json，返回 (manifests, warnings)。

    实现在 book_registry.load_with_warnings：同一份书单同时供门户、README、
    书库导航条使用，新增一本书不需要改本文件。
    """
    return REG.load_with_warnings(books_dir)


def report_href(m) -> str:
    """卡片「打开」链接，相对站点根（书库导航条用的是同一个 href）。"""
    return m.get("href") or REG.href_of(m)


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
    trait = KIND_TRAITS.get(kind, "结构化拆解")
    size = sum(int(metrics.get(k) or 0) for k in ("characters", "events", "relations"))
    haystack = " ".join(str(x or "") for x in (
        m.get("title"), m.get("author"), m.get("subtitle"), m.get("desc"), kind_label,
    )).lower()
    attrs = (
        'data-order="%s" data-size="%d" data-updated="%s" data-search="%s"'
        % (esc(m.get("order", 999)), size, esc(m.get("updated", "")), esc(haystack))
    )

    return (
        '<article class="card" data-kind="{kind}" style="--accent:{accent}" {attrs}>'
        '<div class="cover" aria-hidden="true"><span class="glyph">{glyph}</span>'
        '<span class="cover-kind">{kind_label}</span></div>'
        '<div class="body">'
        '<div class="k-row"><span class="bdg bdg-kind">{kind_label}</span>'
        '<span class="bdg bdg-trait">{trait}</span>{badges}</div>'
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
        attrs=attrs,
        trait=esc(trait),
    )

CSS = """
:root{
  --bg:#f2eee6; --paper:#fffdf8; --ink:#27231f; --muted:#716960;
  --line:#ded6c9; --accent:#8d3025; --gold:#b88b35;
  --shadow:0 8px 24px rgba(42,31,21,.08);
  --card-ink:#2f2822; --desc:#4a443b; --hero-bg1:#342c25; --hero-bg2:#2a241f;
}
body[data-theme="dark"]{
  --bg:#171613; --paper:#211f1b; --ink:#efe7da; --muted:#a79c8c;
  --line:#3b362e; --accent:#d08a72; --gold:#d8bf86;
  --shadow:0 8px 24px rgba(0,0,0,.4);
  --card-ink:#f4ecdf; --desc:#cfc4b4; --hero-bg1:#2a2621; --hero-bg2:#1d1a17;
}
*{box-sizing:border-box}
.skip-link{position:fixed;left:16px;top:10px;z-index:120;transform:translateY(-180%);
  padding:8px 12px;border-radius:6px;background:var(--paper);color:var(--accent);
  border:1px solid var(--line);font-weight:700;text-decoration:none;transition:transform .15s}
.skip-link:focus{transform:translateY(0)}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{
  outline:2px solid var(--gold);outline-offset:2px}
@media(prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;
    transition-duration:.001ms!important;scroll-behavior:auto!important}
}
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
.bdg-trait{background:transparent;color:var(--muted);border:1px solid var(--line)}
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

/* ===== 工具栏：搜索 / 排序 / 主题（门户重做） ===== */
.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 14px}
.search{flex:1;min-width:220px;position:relative}
.search input{width:100%;padding:9px 14px;border:1px solid var(--line);
  border-radius:9px;background:var(--paper);color:var(--ink);font:inherit;font-size:13.5px}
.search input::placeholder{color:var(--muted)}
.toolbar select,.theme-btn{padding:8px 12px;border:1px solid var(--line);border-radius:9px;
  background:var(--paper);color:var(--ink);font:inherit;font-size:13px;cursor:pointer}
.theme-btn{min-width:86px}
.hitcount{font-size:12px;color:var(--muted);margin-left:2px}
.trait{position:absolute;right:12px;top:12px;font-size:10.5px;
  color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:1px 8px}
.grid{align-items:stretch}
.card{position:relative}

/* 暗色下把几处硬编码浅色拉回可读 */
body[data-theme="dark"] .hero{background:linear-gradient(180deg,var(--hero-bg1),var(--hero-bg2))}
body[data-theme="dark"] .card h2{color:var(--card-ink)}
body[data-theme="dark"] .desc{color:var(--desc)}
body[data-theme="dark"] .mts b{color:var(--card-ink)}
body[data-theme="dark"] .bdg-kind,body[data-theme="dark"] .bdg-note{background:#3a3327;color:#d8bf86}
body[data-theme="dark"] .bdg-ext{background:#24362e;color:#8ec9a8}
@media print{.toolbar,.theme-btn,.skip-link{display:none!important}}
"""

JS = """
(function(){
  // 旧深链兼容：改造前根路径即《明朝那些事儿》报告，深链全在 #hash。
  // 带 hash 访问本门户时，转交 ming/ 下的报告（hash 原样保留）。
  var h = location.hash;
  if (h && h.length > 1) { location.replace('ming/' + h); return; }

  var KEY = 'book-shelf-theme';
  var body = document.body;
  var themeBtn = document.getElementById('theme-btn');
  // 首绘前的主题已在 <body> 起始的内联脚本里定好，这里只同步按钮文案
  function label(t){
    if (themeBtn) themeBtn.textContent = (t === 'dark') ? '切换亮色' : '切换暗色';
  }
  label(body.dataset.theme);
  if (themeBtn) themeBtn.addEventListener('click', function(){
    var t = (body.dataset.theme === 'dark') ? 'light' : 'dark';
    body.dataset.theme = t;
    try { localStorage.setItem(KEY, t); } catch (e) {}
    label(t);
  });

  var chips  = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var cards  = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var grid   = document.querySelector('.grid');
  var search = document.getElementById('book-search');
  var sort   = document.getElementById('book-sort');
  var hit    = document.getElementById('hitcount');
  var kind = 'all', q = '';

  function refresh(){
    var n = 0;
    cards.forEach(function(c){
      var okKind = (kind === 'all' || c.getAttribute('data-kind') === kind);
      var okQ = !q || (c.getAttribute('data-search') || '').indexOf(q) >= 0;
      var show = okKind && okQ;
      c.style.display = show ? '' : 'none';
      if (show) n++;
    });
    var mode = sort ? sort.value : 'order';
    var ordered = cards.slice().sort(function(a, b){
      if (mode === 'size') return (+b.dataset.size) - (+a.dataset.size);
      if (mode === 'updated') return String(b.dataset.updated || '').localeCompare(String(a.dataset.updated || ''));
      return (+a.dataset.order) - (+b.dataset.order);
    });
    ordered.forEach(function(c){ grid.appendChild(c); });
    if (hit) hit.textContent = '显示 ' + n + ' / ' + cards.length + ' 本';
  }

  chips.forEach(function(c){
    c.addEventListener('click', function(){
      chips.forEach(function(x){ x.classList.remove('on'); });
      c.classList.add('on');
      kind = c.getAttribute('data-kind') || 'all';
      refresh();
    });
  });
  if (search) {
    var timer = null;
    search.addEventListener('input', function(){
      clearTimeout(timer);
      timer = setTimeout(function(){
        q = search.value.trim().toLowerCase();
        refresh();
      }, 140);
    });
  }
  if (sort) sort.addEventListener('change', refresh);
  refresh();
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
        "<script>(function(){try{var t=localStorage.getItem('book-shelf-theme');"
        "if(t==='dark'||t==='light'){document.body.dataset.theme=t;return;}"
        "document.body.dataset.theme=(window.matchMedia&&"
        "matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';"
        "}catch(e){document.body.dataset.theme='light';}})();</script>\n"
        '<a class="skip-link" href="#shelf">跳到书单</a>\n'
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
        '<nav class="filters" aria-label="按类型筛选">%s</nav>\n'
        '<div class="toolbar">\n'
        '<label class="search"><input id="book-search" type="search" '
        'placeholder="搜索书名 / 作者 / 关键词" aria-label="搜索书目"></label>\n'
        '<select id="book-sort" aria-label="排序方式">'
        '<option value="order">默认顺序</option>'
        '<option value="size">按数据规模</option>'
        '<option value="updated">按更新时间</option></select>\n'
        '<button class="theme-btn" id="theme-btn" type="button" aria-label="切换明暗主题">切换暗色</button>\n'
        '<span class="hitcount" id="hitcount" role="status" aria-live="polite"></span>\n'
        "</div>\n"
        '<main class="grid" id="shelf" tabindex="-1">%s</main>\n'
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
