# -*- coding: utf-8 -*-
"""
统一书单（书库产品的单一数据源）
================================
此前 5 本报告是孤岛：点进任一本，既回不了书库，也切不到另一本。
书单散落在 build_hub.py 的 load_manifests、sync_readme.py 的表格、各报告的
硬编码里，新增一本书要改好几个地方。这个模块把「有哪些书、各自在哪」收成
一份，供：

  - 门户 build_hub.py（书卡、类型筛选、统计）
  - README 生成器 sync_readme.py（书单表、链接）
  - 所有报告页顶的「书库导航条」（shelf_block / inject_shelf）
  - 发布同步 publish_books.py（比对时剥离平台专有装饰）

为什么导航条要**构建期内联**而不是运行时 fetch：所有报告都是单文件离线
HTML，双击就能看，不能依赖网络或同源接口。BOOK_SHELF_BASE 由各产物所在
目录深度决定（books/<id>/ 是 ../../，ming/ 是 ../，根目录是 ./），保证
Pages 上的相对跳转也对；用 file:// 双击离线单文件时自动改指线上门户。

用法：
  from book_registry import load, load_with_warnings, shelf_block, inject_shelf
  load()                             # 统一书单（含派生 href / kindLabel）
  shelf_block("tiancai", "../../")    # 导航条 HTML（不含幂等标记）
  inject_shelf(html_bytes, "tiancai", "../../")  # 幂等注入，字节级确定性
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BOOKS_DIR = BASE / "books"

#: 线上书库根。离线双击单文件报告时，相对路径指向的兄弟目录并不存在，
#: 导航条改指这里，保证「← 书库 / 切换书目」在任何打开方式下都不是死链。
ONLINE_BASE = "https://cochranek.github.io/book-meal/"

KIND_LABELS = {
    "history": "历史",
    "modern_real": "现代现实",
    "fictional_world": "幻想世界",
    "humanities": "人文",
    "other": "其他",
}

DEFAULT_ORDER = 99
DEFAULT_ACCENT = "#8a4a2f"

# 幂等标记：注入器先删旧块再插新块，重复跑结果字节完全一致。
# publish_books.py / sync_shelf.py 的 --check 也靠它剥离平台专有装饰。
SHELF_START = "<!-- BOOK_SHELF_START -->"
SHELF_END = "<!-- BOOK_SHELF_END -->"


# 书库导航条的样式与脚本：所有报告共用同一份，视觉基线因此天然一致。
_BAR_CSS = """
/* ===== 书库导航条（src/book_registry.py 注入，勿在报告里另写一份） ===== */
.shelf-bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  padding:7px 18px;background:#2b2520;color:#f4ecdf;font-size:12.5px;
  font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;
  border-bottom:1px solid rgba(216,191,134,.28);position:relative;z-index:60}
.shelf-bar a{color:inherit;text-decoration:none}
.shelf-home{font-weight:700;white-space:nowrap;letter-spacing:.02em}
.shelf-home:hover{color:#e5c889}
.shelf-sep{opacity:.4}
.shelf-cur{color:#e5c889;font-weight:600;white-space:nowrap;
  max-width:22ch;overflow:hidden;text-overflow:ellipsis}
.shelf-spacer{flex:1}
.shelf-switch{position:relative}
.shelf-switch>button{cursor:pointer;background:transparent;color:#f4ecdf;
  border:1px solid rgba(216,191,134,.45);border-radius:6px;
  padding:3px 10px;font:inherit;font-size:12px}
.shelf-switch>button:hover{border-color:#e5c889;color:#e5c889}
.shelf-menu{position:absolute;right:0;top:calc(100% + 6px);min-width:210px;
  background:#fffdf8;color:#2f2822;border:1px solid #ded6c9;border-radius:9px;
  box-shadow:0 10px 30px rgba(42,31,21,.22);padding:6px;display:none;z-index:70}
.shelf-switch.open .shelf-menu{display:block}
.shelf-menu a{display:flex;align-items:center;gap:9px;padding:7px 9px;
  border-radius:6px;font-size:12.5px;white-space:nowrap}
.shelf-menu a:hover,.shelf-menu a[aria-current="page"]{background:#f3ece0}
.shelf-menu a[aria-current="page"]{font-weight:700}
.shelf-dot{width:8px;height:8px;border-radius:50%;flex:none}
.shelf-menu small{margin-left:auto;color:#8a8075;font-size:10.5px}
.shelf-switch>button:focus-visible,.shelf-menu a:focus-visible,.shelf-home:focus-visible{
  outline:2px solid #e5c889;outline-offset:2px}
/* 各报告的 skip-link 固定在 top:10px，会被导航条盖住，统一挪到条下方 */
.shelf-bar~.skip-link{top:46px}
@media(max-width:640px){.shelf-bar{padding:6px 12px;font-size:11.5px}
  .shelf-cur{max-width:12ch}}
@media print{.shelf-bar{display:none!important}}
"""

_BAR_JS = r"""
(function(){
  function esc(s){
    return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }
  var list = window.BOOK_SHELF || [];
  var cur  = window.BOOK_SHELF_CURRENT || '';
  var base = window.BOOK_SHELF_BASE || './';
  // 双击下载的离线单文件时，相对路径指向的兄弟目录不存在；
  // 此时导航条改指线上书库（链接是导航，不是内容依赖，不影响离线正文）。
  if (location.protocol === 'file:' && window.BOOK_SHELF_ONLINE_BASE) {
    base = window.BOOK_SHELF_ONLINE_BASE;
  }
  var bar  = document.getElementById('shelf-bar');
  if (!bar) return;

  var home = bar.querySelector('.shelf-home');
  if (home) home.href = base + 'index.html';

  var here = null;
  list.forEach(function(b){ if (b.id === cur) here = b; });
  var curEl = bar.querySelector('.shelf-cur');
  if (curEl) curEl.textContent = here ? here.title : (cur || '本报告');

  var sw   = document.getElementById('shelf-switch');
  var btn  = document.getElementById('shelf-toggle');
  var menu = document.getElementById('shelf-menu');
  if (!sw || !btn || !menu) return;

  menu.innerHTML = list.map(function(b){
    var on = b.id === cur;
    return '<a href="' + esc(base + b.href) + '"'
      + (on ? ' class="on" aria-current="page"' : '') + '>'
      + '<span class="shelf-dot" style="background:' + esc(b.accent) + '"></span>'
      + '<span></span><small>' + esc(b.kindLabel || '') + '</small></a>';
  }).join('');
  // 书名走 textContent，避免 title 里的特殊字符破坏结构（与整体转义纪律一致）
  Array.prototype.forEach.call(menu.querySelectorAll('a'), function(a, i){
    var span = a.querySelectorAll('span')[1];
    if (span && list[i]) span.textContent = list[i].title;
  });

  function toggle(open){
    sw.classList.toggle('open', typeof open === 'boolean' ? open : !sw.classList.contains('open'));
    btn.setAttribute('aria-expanded', sw.classList.contains('open') ? 'true' : 'false');
  }
  btn.addEventListener('click', function(e){ e.stopPropagation(); toggle(); });
  document.addEventListener('click', function(e){
    if (!sw.contains(e.target)) toggle(false);
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape') toggle(false);
  });
})();
"""


def href_of(m) -> str:
    """卡片 / 导航条的「打开」链接，一律相对站点根（门户就在根）。

    report 为纯文件名（如 index.html）时拼 books/<id>/<report>；含 / 则视为
    站内路径原样使用（例：明书下沉到 ming/，写 ming/index.html）。
    本站挂在 GitHub Pages 子路径 /book-meal/，**不能**用 / 开头的绝对路径。
    """
    rep = str(m.get("report", "index.html"))
    if m.get("external") or "/" in rep:
        return rep
    return "books/%s/%s" % (m.get("id", ""), rep)


def load_with_warnings(books_dir: Path = BOOKS_DIR):
    """扫描 books/*/manifest.json，返回 (完整书目列表, 警告列表)。

    返回的是**完整 manifest + 派生字段**，这样门户、README、导航条可以共用
    同一批对象，不用各自再解析一遍。派生字段统一带下划线前缀的只有 _order
    （历史契约，sync_readme.py 至今用它排序）。
    """
    manifests, warnings = [], []
    books_dir = Path(books_dir)
    if not books_dir.is_dir():
        return manifests, ["books/ 目录不存在：%s" % books_dir]

    for child in sorted(books_dir.iterdir()):
        mf = child / "manifest.json"
        if not mf.is_file():
            continue
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            warnings.append("manifest 解析失败，已跳过：%s（%s）" % (mf, exc))
            continue
        if not data.get("title"):
            warnings.append("manifest 缺少 title，已跳过：%s" % mf)
            continue
        data.setdefault("id", child.name)
        data.setdefault("kind", "other")
        data.setdefault("metrics", {})
        data.setdefault("report", "index.html")
        data.setdefault("author", "")
        data.setdefault("accent", DEFAULT_ACCENT)
        data.setdefault("glyph", str(data["title"])[:1])
        data.setdefault("order", DEFAULT_ORDER)
        data["_order"] = int(data.get("order") or DEFAULT_ORDER)
        data["href"] = href_of(data)
        data["kindLabel"] = KIND_LABELS.get(str(data["kind"]), str(data["kind"]))
        manifests.append(data)

    manifests.sort(key=lambda m: (m["_order"], str(m["id"])))
    return manifests, warnings


def load(books_dir: Path = BOOKS_DIR):
    """统一书单（无警告版，供只关心数据的调用方）。"""
    return load_with_warnings(books_dir)[0]


def _shelf_payload():
    """导航条只需要 5 个字段；不要在 5 MB 报告里塞整份 manifest。"""
    return [
        {
            "id": m["id"],
            "title": str(m.get("title", "")),
            "kindLabel": m.get("kindLabel") or KIND_LABELS.get(str(m.get("kind", "other")), ""),
            "accent": str(m.get("accent") or DEFAULT_ACCENT),
            "href": m["href"],
        }
        for m in load()
    ]


def shelf_block(current_id: str, base: str = "../../") -> str:
    """返回可直接插进 <body> 的书库导航条（样式 + 骨架 + 数据 + 逻辑）。

    base：从报告所在目录回到站点根的相对前缀。
      books/<id>/index.html → "../../"
      ming/index.html       → "../"
      standalone.html（根） → "./"
    """
    data = json.dumps(_shelf_payload(), ensure_ascii=False, separators=(",", ":"))
    cur = json.dumps(str(current_id), ensure_ascii=False)
    b = json.dumps(base, ensure_ascii=False)
    online = json.dumps(ONLINE_BASE, ensure_ascii=False)
    return (
        "<style>" + _BAR_CSS + "</style>\n"
        '<nav class="shelf-bar" id="shelf-bar" aria-label="书库导航">'
        '<a class="shelf-home" href="' + base + 'index.html">← 书库</a>'
        '<span class="shelf-sep">/</span>'
        '<span class="shelf-cur"></span>'
        '<span class="shelf-spacer"></span>'
        '<span class="shelf-switch" id="shelf-switch">'
        '<button type="button" id="shelf-toggle" aria-haspopup="true" aria-expanded="false">'
        '切换书目 ▾</button>'
        '<span class="shelf-menu" id="shelf-menu" role="menu"></span>'
        '</span></nav>\n'
        "<script>"
        "window.BOOK_SHELF=" + data + ";"
        "window.BOOK_SHELF_CURRENT=" + cur + ";"
        "window.BOOK_SHELF_BASE=" + b + ";"
        "window.BOOK_SHELF_ONLINE_BASE=" + online + ";"
        + _BAR_JS +
        "</script>\n"
    )


# 只删「标记 + 内容 + 其后一个换行」，不动标记前的那个换行。
# 这样剥离后字节恰好回到未注入状态，publish_books.py 的内容比对才成立。
_SHELF_RE = re.compile(
    re.escape(SHELF_START.encode("utf-8")) + rb".*?" +
    re.escape(SHELF_END.encode("utf-8")) + rb"\r?\n?",
    re.S,
)
_BODY_RE = re.compile(rb"<body\b[^>]*>")


def strip_shelf(data: bytes) -> bytes:
    """剥离平台专有导航条，用于产物内容比对。"""
    return _SHELF_RE.sub(b"", data)


def inject_shelf(data: bytes, current_id: str, base: str = "../../") -> bytes:
    """幂等地把导航条插到 <body> 之后，字节级确定性。

    用 bytes 而不是 str：各构建链产物的换行符可能是 CRLF 或 LF，转一遍
    Python 文本 IO 会把它们统一改写，导致 publish_books.py --check 误报。
    注入块跟随原文件的主流换行风格——本机 core.autocrlf=true 而 CI 是 LF，
    混着写会让同一份产物在两台机器上算出不同字节。
    """
    doc = strip_shelf(data)
    crlf = doc.count(b"\r\n")
    lf = doc.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    m = _BODY_RE.search(doc)
    if not m:
        raise ValueError("找不到 <body> 标签，无法注入书库导航条")
    first_nl = re.match(rb"\r?\n", doc[m.end():])
    at = m.end() + (first_nl.end() if first_nl else 0)
    raw = (
        SHELF_START + "\n" + shelf_block(current_id, base).rstrip() + "\n" +
        SHELF_END + "\n"
    ).encode("utf-8")
    if nl != b"\n":
        raw = raw.replace(b"\n", nl)
    return doc[:at] + raw + doc[at:]


def shelf_data_js() -> str:
    """仅书单数据（供门户 JS 复用，避免重复解析 manifest）。"""
    return "window.BOOK_SHELF=" + json.dumps(_shelf_payload(), ensure_ascii=False) + ";"


if __name__ == "__main__":
    for b in load():
        print("%-10s %-28s %s" % (b["id"], b["title"], b["href"]))
