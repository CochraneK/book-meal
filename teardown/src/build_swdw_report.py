# -*- coding: utf-8 -*-
"""独立报告生成器：把回收站找回的整本知识图谱 D（世界级精读）渲染为
单文件离线 HTML —— out/swdw.html。不依赖五元组流水线模板，忠实还原
「天幕机制 / 七世界人物·情节·判定·死亡 / 规则演化 / 余黎成长弧 / 全本目录」。

2026-10-21 改版：首屏从「一篇论文」改成「一眼看清七世界」——
  ① 抬头下方是四个数字（章 / 世界 / 人物 / 裁定），每个带自己的口径小字；
  ② 第二个屏幕是七世界卡片墙（世界号 · 短裁定 · 章节区间 · 世界设定），点卡片
     跳到该世界的完整档案；裁定构成用一条堆叠条统一给出；
  ③ 档案本身改成可折叠，默认只展开第一个世界——7 个世界全展开是 7 屏长文，
     读者没法先看结构再决定读哪一段；
  ④ 配色与家族对齐（纸墨 + 本书紫），字号收敛到 5 级。
"""
import json, os, html, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "swdw", "data.json")
OUT = os.path.join(BASE, "out", "swdw.html")

D = json.load(open(DATA, encoding="utf-8"))
M = D["meta"]
MECH = D.get("mechanism", {})
WORLDS = D.get("worlds", [])
RULE_EVO = D.get("rule_evolution", [])
YU_ARC = D.get("yu_arc", [])
THEME = D.get("theme", "")
CH_IDX = D.get("chapter_index", [])
CHARS = D.get("characters", [])
EVENTS = D.get("events", [])
RELS = D.get("relations", [])

def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)

def vclass(v):
    v = v or ""
    if "数据销毁" in v: return "v-destroy"
    if "不通过" in v: return "v-fail"
    if "通过" in v: return "v-pass"
    if "未宣判" in v or "未及" in v: return "v-pending"
    return "v-pending"

VLABEL = {"v-pass": "通过", "v-fail": "不通过", "v-destroy": "数据销毁", "v-pending": "未宣判"}

def vlabel(v):
    """短标签：卡片上只放四个规范词，完整裁定（含复审期等附加条件）留在档案里。"""
    return VLABEL[vclass(v)]

def wspan(w):
    s, e = w.get("chapter_start") or 0, w.get("chapter_end") or 0
    return (e - s + 1) if e >= s else 0

ACCENT = "#5a4b8c"

# 裁定构成：按每个世界的**最终结果**统计（W2 先判不通过、后因造假销毁，计入销毁）
VC = {"v-pass": 0, "v-fail": 0, "v-destroy": 0, "v-pending": 0}
for _w in WORLDS:
    VC[vclass((_w.get("verdict") or {}).get("world", ""))] += 1

# ---------------- 顶部导航 ----------------
NAV = [
    ("overview", "概览"), ("mech", "天幕机制"), ("worlds", "七世界档案"),
    ("rules", "规则演化"), ("arc", "余黎成长"), ("theme", "主题"),
    ("index", "全本目录"),
]
nav_html = "".join('<a href="#%s">%s</a>' % (k, t) for k, t in NAV)

# ---------------- HERO ----------------
FLAGS = [
    "回收站找回 · 全量图谱",
    "%d 章索引" % len(CH_IDX),
    "%d 世界档案" % len(WORLDS),
    "%d 条规则演化" % len(RULE_EVO),
    "%d 段成长弧" % len(YU_ARC),
]
flags_html = "".join('<span class="flag">%s</span>' % esc(f) for f in FLAGS)

WCH = 0
for _w in WORLDS:
    WCH = max(WCH, wspan(_w))

hero = f"""
<header class="hero" id="overview">
  <div class="kicker">拆解报告 · 独立知识图谱</div>
  <h1>{esc(M['title'])}</h1>
  <div class="hero-sub">{esc(M['author'])} · {esc(M.get('genre',''))} · {esc(M.get('status',''))}</div>
  <div class="stats">
    <div class="stat"><div class="v">{esc(M.get('total_chapters'))}</div><div class="l">章</div>
      <div class="s">正文 {esc(round((M.get('total_chars') or 0)/10000,1))} 万字</div></div>
    <div class="stat"><div class="v">{esc(M.get('worlds'))}</div><div class="l">个评估世界</div>
      <div class="s">第 1–{esc(M.get('total_chapters'))} 章全覆盖</div></div>
    <div class="stat"><div class="v">{len(CHARS)}</div><div class="l">人物</div>
      <div class="s">{len(EVENTS)} 件事件 · {len(RELS)} 条关系</div></div>
    <div class="stat"><div class="v">4</div><div class="l">类裁定</div>
      <div class="s">通过 {VC['v-pass']} · 不通过 {VC['v-fail']}</div></div>
  </div>
  <div class="flags">{flags_html}</div>
  <p class="hero-note">{esc(M.get('note',''))}</p>
  <p class="hero-src">源站：<a href="{esc(M.get('source',''))}" target="_blank" rel="noopener">{esc(M.get('source',''))}</a> · 抓取于 {esc(M.get('scraped_at',''))}</p>
</header>
"""

# ---------------- 概览：七世界卡片墙 ----------------
def world_card_brief(w):
    idx = w.get("index")
    v = (w.get("verdict") or {}).get("world", "")
    cls = vclass(v)
    s, e = w.get("chapter_start"), w.get("chapter_end")
    span = wspan(w)
    pct = (span / (M.get("total_chapters") or 1) * 100)
    return f"""
<a class="wcard" href="#world-{esc(idx)}">
  <div class="wc-top"><span class="wc-idx">世界 {esc(idx)}</span>
    <span class="wc-badge {cls}">{esc(vlabel(v))}</span></div>
  <div class="wc-name">{esc(w.get('name'))}</div>
  <div class="wc-full">{esc(w.get('full_title',''))}</div>
  <div class="wc-range">第 {esc(s)}–{esc(e)} 章 · {span} 章</div>
  <div class="wc-set">{esc(w.get('setting',''))}</div>
  <div class="wc-foot"><span class="wc-bar"><i style="width:{pct:.1f}%"></i></span>
    <span class="wc-go">看档案 →</span></div>
</a>"""

def section_overview():
    cards = "".join(world_card_brief(w) for w in WORLDS)
    total = sum(VC.values()) or 1
    segs, legs = [], []
    for cls, name in (("v-pass", "通过"), ("v-fail", "不通过"),
                      ("v-destroy", "数据销毁"), ("v-pending", "未宣判")):
        n = VC[cls]
        if not n:
            continue
        segs.append('<i class="%s" style="width:%.2f%%" title="%s %d 个世界"></i>'
                    % (cls, n / total * 100, name, n))
        legs.append('<span class="lg"><i class="%s"></i>%s <b>%d</b></span>' % (cls, name, n))
    return f"""
<section class="sec" id="worlds-glance">
  <div class="sec-head"><h2>七世界一览</h2>
    <span class="hint">点卡片跳到该世界的完整档案（人物 / 情节 / 裁定 / 死亡清单）</span></div>
  <div class="wgrid">{cards}</div>
  <div class="vdist">
    <div class="vbar">{''.join(segs)}</div>
    <div class="vleg">{''.join(legs)}</div>
    <p class="vnote">注：世界 2 先判「不通过」，后因内容造假改为「数据销毁」，此处按最终结果计入销毁；
      天幕机制里的四种裁定各计一次（通过 3 / 不通过 3 / 销毁 1 / 未宣判 1），故合计 8 次、覆盖 7 个世界。</p>
  </div>
</section>
"""

# ---------------- 机制 ----------------
def section_mech():
    verdicts = MECH.get("verdicts", [])
    vcards = "".join(
        '<div class="vcard"><div class="vcount">%s</div><div class="vtype">%s</div><div class="vdesc">%s</div></div>'
        % (esc(v.get("count")), esc(v.get("type")), esc(v.get("desc"))) for v in verdicts)
    rules = MECH.get("rules", [])
    rlis = "".join('<li><b>%s</b><span>%s</span></li>' % (esc(r.get("id")), esc(r.get("desc"))) for r in rules)
    cond = "".join('<span class="cond">%s</span>' % esc(c) for c in MECH.get("pass_conditions", []))
    return f"""
<section class="sec" id="mech">
  <div class="sec-head"><h2>天幕机制 · {esc(MECH.get('name',''))}</h2>
    <span class="hint">{len(rules)} 条评审规则 · {len(verdicts)} 种裁定</span></div>
  <p class="lead">{esc(MECH.get('tianmu',''))}</p>
  <p class="lead">{esc(MECH.get('scope',''))}</p>
  <div class="cond-row"><span class="cond-k">晋升前提</span>{cond}</div>
  <div class="vgrid">{vcards}</div>
  <ul class="rules">{rlis}</ul>
</section>
"""

# ---------------- 世界档案 ----------------
def world_card(w):
    idx = w.get("index")
    s, e = w.get("chapter_start"), w.get("chapter_end")
    v = w.get("verdict", {})
    vw = v.get("world", "")
    cls = vclass(vw)
    chars = "".join(
        '<div class="ccard"><div class="cname">%s</div><div class="crole">%s</div><div class="cquote">“%s”</div></div>'
        % (esc(c.get("name")), esc(c.get("role")), esc(c.get("quote"))) for c in w.get("characters", []))
    plots = "".join(
        '<div class="pnode"><div class="pstage">%s</div><div class="ptext">%s</div></div>'
        % (esc(p.get("stage")), esc(p.get("text"))) for p in w.get("plot", []))
    vp = v.get("protagonist", "")
    rules_used = "".join('<span class="ru">%s</span>' % esc(x) for x in (v.get("rules_used") or []))
    new_rules = "".join('<span class="nr">%s</span>' % esc(x) for x in (v.get("new_rules") or []))
    deaths = w.get("deaths") or []
    death_tbl = ""
    if deaths:
        rows = "".join("<tr><td>%s</td><td class='num'>第%d章</td><td>%s</td></tr>"
                       % (esc(d.get("name")), d.get("chapter", 0), esc(d.get("cause"))) for d in deaths)
        death_tbl = ('<h4>死亡清单<span class="hint">%d 人</span></h4>'
                     '<div class="table-wrap"><table class="dtbl"><thead><tr><th>角色</th><th>章节</th><th>死因</th></tr></thead>'
                     '<tbody>%s</tbody></table></div>' % (len(deaths), rows))
    quotes = "".join('<blockquote>“%s”</blockquote>' % esc(q) for q in (w.get("quotes") or []))
    return f"""
<details class="world" id="world-{esc(idx)}"{" open" if idx == 1 else ""}>
  <summary class="whead">
    <span class="widx">世界 {esc(idx)}</span>
    <span class="wtitle"><b>{esc(w.get('name'))}</b><span class="wfull">{esc(w.get('full_title',''))}</span></span>
    <span class="wrange">第 {esc(s)}–{esc(e)} 章 · {wspan(w)} 章</span>
    <span class="wbadge {cls}">{esc(vlabel(vw))}</span>
    <span class="wcaret"></span>
  </summary>
  <div class="wbody">
    <div class="wcols">
      <div class="wcol">
        <h4>世界设定</h4><p class="setting">{esc(w.get('setting',''))}</p>
        <h4>主角</h4>
        <p class="prot"><b>{esc(w.get('protagonist',{}).get('name',''))}</b> — {esc(w.get('protagonist',{}).get('identity',''))}<br><span class="sit">{esc(w.get('protagonist',{}).get('situation',''))}</span></p>
        <h4>余黎介入</h4><p class="interv">{esc(w.get('yu_intervention',''))}</p>
      </div>
      <div class="wcol">
        <h4>主要角色<span class="hint">{len(w.get('characters',[]))} 人</span></h4>
        <div class="cgrid">{chars}</div>
      </div>
    </div>
    <h4>情节脉络<span class="hint">{len(w.get('plot',[]))} 个阶段</span></h4>
    <div class="ptimeline">{plots}</div>
    {death_tbl}
    <div class="verdict-box {cls}">
      <div class="vb-row"><span class="vb-k">世界裁定</span><span class="vb-v">{esc(vw)}</span></div>
      <div class="vb-row"><span class="vb-k">主角裁定</span><span class="vb-v">{esc(vp)}</span></div>
      <div class="vb-row"><span class="vb-k">适用规则</span><span class="vb-v">{rules_used}</span></div>
      <div class="vb-row"><span class="vb-k">新增规则</span><span class="vb-v">{new_rules}</span></div>
    </div>
    <h4>金句<span class="hint">{len(w.get('quotes') or [])} 条</span></h4><div class="quotes">{quotes}</div>
    <h4>余黎在该世界的成长</h4><p class="growth">{esc(w.get('yu_growth',''))}</p>
  </div>
</details>"""

def section_worlds():
    cards = "".join(world_card(w) for w in WORLDS)
    over = "".join(
        '<tr><td class="num">{i}</td><td>{name}</td><td class="dim">{t}</td><td class="dim">第 {s}–{e} 章</td><td class="{vc}">{vw}</td></tr>'
        .format(i=esc(w.get("index")), name=esc(w.get("name")), t=esc(w.get("full_title","")),
                s=esc(w.get("chapter_start")), e=esc(w.get("chapter_end")),
                vc=vclass(w.get("verdict",{}).get("world","")), vw=esc(vlabel(w.get("verdict",{}).get("world",""))))
        for w in WORLDS)
    return f"""
<section class="sec" id="worlds">
  <div class="sec-head"><h2>七世界评估档案</h2>
    <button class="mini-btn" id="expandAll" type="button">全部展开 / 收起</button></div>
  <div class="table-wrap"><table class="otbl"><thead><tr><th>#</th><th>世界</th><th>原书名</th><th>章节</th><th>裁定</th></tr></thead><tbody>{over}</tbody></table></div>
  <div class="worlds-wrap">{cards}</div>
</section>
"""

# ---------------- 规则演化 ----------------
def section_rules():
    nodes = "".join(
        '<div class="rnode"><div class="rworld">世界 {w}</div><div class="rrule">{r}</div><div class="rnote">{n}</div></div>'
        .format(w=esc(e.get("world")), r=esc(e.get("rule")), n=esc(e.get("note"))) for e in RULE_EVO)
    return f"""
<section class="sec" id="rules">
  <div class="sec-head"><h2>规则演化</h2><span class="hint">{len(RULE_EVO)} 条 · 从机械执行到价值权衡</span></div>
  <p class="lead">余黎在七个世界的评估中，逐步把临时判断沉淀为可复用规则，评审口径从机械执行走向价值权衡。</p>
  <div class="rtimeline">{nodes}</div>
</section>
"""

# ---------------- 余黎成长 ----------------
def section_arc():
    nodes = "".join(
        '<div class="anode"><div class="astage">%s</div><div class="atext">%s</div></div>'
        % (esc(a.get("stage")), esc(a.get("text"))) for a in YU_ARC)
    return f"""
<section class="sec" id="arc">
  <div class="sec-head"><h2>观测员余黎 · 成长弧</h2><span class="hint">{len(YU_ARC)} 个阶段</span></div>
  <div class="atimeline">{nodes}</div>
</section>
"""

# ---------------- 主题 ----------------
def section_theme():
    return f"""
<section class="sec" id="theme">
  <div class="sec-head"><h2>主题</h2></div>
  <p class="theme-text">{esc(THEME)}</p>
</section>
"""

# ---------------- 目录 ----------------
def section_index():
    rows = "".join(
        '<tr data-t="{t}" data-w="{w}"><td class="num">{n}</td><td class="ct">{t}</td><td class="cw">世界 {w}</td><td class="cc num">{c}</td></tr>'
        .format(n=esc(c.get("n")), t=esc(c.get("t")), w=esc(c.get("w")), c=esc(c.get("c")))
        for c in CH_IDX)
    return f"""
<section class="sec" id="index">
  <div class="sec-head"><h2>全本目录</h2><span class="hint">{len(CH_IDX)} 章 · 可搜索</span></div>
  <input id="chSearch" type="search" placeholder="搜索章节标题 / 世界号，如「观测」「世界 3」" oninput="filterChapters()">
  <div class="itbl-wrap"><table class="itbl"><thead><tr><th>章</th><th>标题</th><th>归属世界</th><th>字数</th></tr></thead><tbody id="chBody">{rows}</tbody></table></div>
</section>
"""

JS = """
function filterChapters(){
  var q=document.getElementById('chSearch').value.trim().toLowerCase();
  var rows=document.getElementById('chBody').getElementsByTagName('tr');
  for(var i=0;i<rows.length;i++){
    var t=rows[i].getAttribute('data-t').toLowerCase();
    var w=rows[i].getAttribute('data-w');
    rows[i].style.display=(!q||t.indexOf(q)>=0||('世界 '+w).indexOf(q)>=0)?'':'none';
  }
}
/* 概览卡片是 #world-N 锚点，但档案是 <details>：不手动 open，跳过去只会看到
   一行折叠标题。这里在 hashchange 与首屏各开一次。 */
(function(){
  function openHash(){
    var id=(location.hash||'').slice(1);
    if(!id) return;
    var el=document.getElementById(id);
    if(el && el.tagName==='DETAILS') el.open=true;
  }
  window.addEventListener('hashchange', openHash);
  openHash();
})();
/* 「全部展开 / 收起」：7 个世界逐个点太麻烦，这里按当前状态取反 */
(function(){
  var b=document.getElementById('expandAll');
  if(!b) return;
  b.addEventListener('click', function(){
    var ds=document.querySelectorAll('.worlds-wrap details.world');
    var anyClosed=false, i;
    for(i=0;i<ds.length;i++) if(!ds[i].open) anyClosed=true;
    for(i=0;i<ds.length;i++) ds[i].open=anyClosed;
  });
})();
"""

CSS = """
/* 纸墨 + 本书紫：与书库门户、拆书报告同一套底子，本书只换主色 */
:root{
  --bg:#f4f1ea; --paper:#fffdf8; --paper-2:#faf7f0;
  --ink:#27231f; --ink-2:#5f584f; --ink-3:#7c7469;
  --line:#e2dbcd; --line-2:#efe9dc;
  --accent:#5a4b8c; --accent-soft:#efeaf8; --gold:#b08a3e;
  --green:#3f7a4e; --amber:#b07a2e; --red:#a63a3a;
  --radius:12px; --shadow:0 1px 3px rgba(40,35,25,.08),0 8px 22px rgba(40,35,25,.05);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.72;
  font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",-apple-system,sans-serif;
  font-size:14.5px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.num{font-variant-numeric:tabular-nums}
.hint{font-weight:400;font-size:12px;color:var(--ink-3);margin-left:8px}
.lead{font-size:14.5px;color:var(--ink-2);margin:8px 0}
.table-wrap{overflow-x:auto}

/* ---------- 吸顶导航 ---------- */
nav.toc{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:4px;flex-wrap:wrap;
  padding:10px 24px;background:rgba(244,241,234,.94);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line)}
nav.toc .brand{font-size:13px;font-weight:700;color:var(--ink);margin-right:14px;letter-spacing:.02em}
nav.toc a{color:var(--ink-2);font-size:13px;padding:5px 11px;border-radius:999px}
nav.toc a:hover{background:var(--accent-soft);color:var(--accent);text-decoration:none}
@media(max-width:760px){nav.toc .brand{display:none}nav.toc{padding:8px 14px;gap:2px}
  nav.toc a{font-size:12.5px;padding:4px 8px}}

.wrap{max-width:1080px;margin:0 auto;padding:0 24px 80px}
@media(max-width:560px){.wrap{padding:0 16px 60px}}

/* ---------- 抬头 ---------- */
.hero{padding:46px 0 26px;border-bottom:1px solid var(--line)}
.kicker{font-size:12px;letter-spacing:.2em;color:var(--accent);font-weight:700}
.hero h1{font-size:34px;line-height:1.28;margin:8px 0 6px;letter-spacing:.01em}
.hero-sub{color:var(--ink-2);font-size:13.5px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:22px 0 0}
.stat{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);
  padding:13px 15px 11px;box-shadow:var(--shadow)}
.stat .v{font-size:30px;font-weight:700;line-height:1.05;letter-spacing:-.02em;color:var(--ink);
  font-variant-numeric:tabular-nums}
.stat .l{font-size:12px;color:var(--ink-2);margin-top:5px;letter-spacing:.06em}
.stat .s{font-size:11px;color:var(--ink-3);margin-top:1px}
@media(max-width:760px){.stats{grid-template-columns:repeat(2,1fr)}
  .hero h1{font-size:26px}.stat .v{font-size:24px}}
.flags{display:flex;gap:6px;flex-wrap:wrap;margin-top:14px}
.flag{font-size:11.5px;color:var(--ink-2);background:var(--paper);border:1px solid var(--line);
  border-radius:999px;padding:1px 10px}
.hero-note{font-size:13.5px;color:var(--ink-2);background:var(--paper-2);border-left:3px solid var(--gold);
  border-radius:0 8px 8px 0;padding:11px 15px;margin:16px 0 0}
.hero-src{font-size:11.5px;color:var(--ink-3);margin:8px 0 0;word-break:break-all}

/* ---------- 区块 ---------- */
.sec{padding:34px 0;border-bottom:1px solid var(--line)}
.sec:last-of-type{border-bottom:none}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;
  flex-wrap:wrap;margin-bottom:16px}
.sec-head h2{font-size:22px;margin:0;font-weight:700;letter-spacing:.01em}
.sec h4{font-size:13.5px;margin:22px 0 9px;color:var(--ink);font-weight:700;letter-spacing:.04em}
.mini-btn{cursor:pointer;font-family:inherit;font-size:12px;color:var(--ink-2);background:var(--paper);
  border:1px solid var(--line);border-radius:999px;padding:4px 12px}
.mini-btn:hover{color:var(--accent);border-color:var(--accent)}

/* ---------- 七世界卡片墙 ---------- */
.wgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:12px}
.wcard{display:flex;flex-direction:column;gap:3px;background:var(--paper);border:1px solid var(--line);
  border-radius:var(--radius);padding:14px 15px 12px;color:inherit;box-shadow:var(--shadow);
  transition:border-color .15s,transform .15s}
.wcard:hover{border-color:var(--accent);transform:translateY(-2px);text-decoration:none}
.wc-top{display:flex;align-items:center;justify-content:space-between;gap:8px}
.wc-idx{font-size:11px;letter-spacing:.1em;color:var(--accent);font-weight:700}
.wc-badge{font-size:11px;font-weight:700;color:#fff;border-radius:999px;padding:1px 9px}
.wc-name{font-size:16px;font-weight:700;margin-top:4px;line-height:1.35}
.wc-full{font-size:11.5px;color:var(--ink-3)}
.wc-range{font-size:11.5px;color:var(--ink-2);font-variant-numeric:tabular-nums}
.wc-set{font-size:12.5px;color:var(--ink-2);line-height:1.62;margin-top:6px;flex:1}
.wc-foot{display:flex;align-items:center;gap:8px;margin-top:10px;padding-top:8px;border-top:1px dashed var(--line)}
.wc-bar{flex:1;height:4px;background:var(--line-2);border-radius:2px;overflow:hidden}
.wc-bar i{display:block;height:100%;background:var(--accent);opacity:.55;border-radius:2px}
.wc-go{font-size:11px;color:var(--accent);white-space:nowrap}

/* 裁定构成：一条堆叠条 + 图例 */
.vdist{margin-top:16px;background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);
  padding:13px 16px}
.vbar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--line-2)}
.vbar i{display:block;height:100%}
.vleg{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--ink-2);margin-top:10px}
.vleg .lg{display:inline-flex;align-items:center;gap:5px}
.vleg .lg i{width:9px;height:9px;border-radius:2px;display:inline-block}
.vleg b{color:var(--ink);font-variant-numeric:tabular-nums}
.vnote{font-size:11.5px;color:var(--ink-3);line-height:1.65;margin:10px 0 0}

/* 裁定四色：短标签、堆叠条、表格文字共用一套 */
.v-pass{background:var(--green)}
.v-fail{background:var(--amber)}
.v-destroy{background:var(--red)}
.v-pending{background:var(--ink-3)}

/* ---------- 机制 ---------- */
.cond-row{margin:14px 0;font-size:13.5px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.cond-k{font-size:11.5px;letter-spacing:.08em;color:var(--ink-3)}
.cond{display:inline-block;background:var(--accent-soft);color:var(--accent);border-radius:6px;
  padding:3px 10px;font-size:12.5px;margin:2px 4px 2px 0}
.vgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin:14px 0 4px}
.vcard{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px}
.vcount{font-size:26px;font-weight:700;color:var(--accent);line-height:1.1;font-variant-numeric:tabular-nums}
.vtype{font-weight:700;font-size:13.5px;margin:4px 0 2px}
.vdesc{font-size:12.5px;color:var(--ink-2);line-height:1.62}
ul.rules{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:8px}
ul.rules li{display:flex;gap:12px;background:var(--paper);border:1px solid var(--line);
  border-radius:9px;padding:10px 14px;font-size:13.5px;line-height:1.65}
ul.rules li b{color:var(--accent);flex:none;min-width:26px;font-variant-numeric:tabular-nums}

/* ---------- 世界档案（折叠） ---------- */
.worlds-wrap{margin-top:16px}
details.world{background:var(--paper);border:1px solid var(--line);border-radius:14px;
  margin-bottom:10px;box-shadow:var(--shadow);overflow:hidden}
details.world[open]{border-color:#d8cdea}
details.world > summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:14px;
  flex-wrap:wrap;padding:14px 18px}
details.world > summary::-webkit-details-marker{display:none}
details.world > summary:hover{background:var(--paper-2)}
.widx{background:var(--accent);color:#fff;border-radius:9px;padding:5px 11px;font-weight:700;
  font-size:12.5px;white-space:nowrap}
.wtitle{display:flex;flex-direction:column;min-width:0;flex:1}
.wtitle b{font-size:17px;line-height:1.35}
.wfull{font-size:11.5px;color:var(--ink-3)}
.wrange{font-size:11.5px;color:var(--ink-2);font-variant-numeric:tabular-nums;white-space:nowrap}
.wbadge{font-size:11.5px;font-weight:700;color:#fff;border-radius:999px;padding:2px 11px;white-space:nowrap}
.wcaret{font-size:11.5px;color:var(--accent);border:1px solid var(--line);border-radius:999px;
  padding:1px 10px;white-space:nowrap}
/* 按钮文案跟着折叠状态走，不靠 JS 改文本 */
.wcaret::before{content:"展开"}
details.world[open] .wcaret{color:var(--ink-3)}
details.world[open] .wcaret::before{content:"收起"}
.wbody{padding:2px 18px 18px;border-top:1px solid var(--line-2)}
.wcols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
@media(max-width:820px){.wcols{grid-template-columns:1fr;gap:0}}
.setting{font-size:13.5px;background:var(--paper-2);border-radius:9px;padding:12px 14px;color:var(--ink)}
.prot{font-size:13.5px;margin:0}.prot .sit{display:block;color:var(--ink-2);font-size:12.5px;margin-top:4px}
.interv{font-size:13.5px;color:var(--ink-2);margin:0}
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:8px}
.ccard{background:var(--paper-2);border:1px solid var(--line-2);border-radius:9px;padding:9px 11px}
.cname{font-weight:700;font-size:13.5px}
.crole{font-size:11.5px;color:var(--accent);margin:2px 0}
.cquote{font-size:11.5px;color:var(--ink-3);font-style:italic;line-height:1.6}
.ptimeline{border-left:2px solid var(--accent);padding-left:18px;margin:6px 0}
.pnode{margin-bottom:13px;position:relative}
.pnode:before{content:"";position:absolute;left:-24px;top:7px;width:9px;height:9px;background:var(--accent);
  border-radius:50%;border:2px solid var(--paper)}
.pstage{font-weight:700;font-size:13px;color:var(--accent)}
.ptext{font-size:13.5px;color:var(--ink-2);line-height:1.7}
.dtbl{width:100%;border-collapse:collapse;font-size:12.5px;margin:6px 0}
.dtbl th,.dtbl td{border:1px solid var(--line);padding:7px 10px;text-align:left}
.dtbl th{background:#f7ecec;color:var(--red);font-weight:600}
.verdict-box{border-radius:11px;padding:13px 16px;margin:16px 0;font-size:13.5px}
.verdict-box .vb-row{display:flex;gap:14px;padding:6px 0;border-bottom:1px dashed rgba(40,35,25,.1)}
.verdict-box .vb-row:last-child{border-bottom:none}
.vb-k{color:var(--ink-3);min-width:76px;flex-shrink:0;font-size:12.5px}
.vb-v{flex:1;color:var(--ink)}
.ru,.nr{display:inline-block;background:var(--paper);border:1px solid var(--line);border-radius:6px;
  padding:2px 8px;margin:2px 4px 2px 0;font-size:11.5px;color:var(--ink-2)}
.quotes{display:grid;grid-template-columns:repeat(auto-fill,minmax(228px,1fr));gap:9px}
blockquote{margin:0;background:var(--paper-2);border-left:3px solid var(--accent);padding:10px 13px;
  font-size:12.5px;color:var(--ink-2);border-radius:0 8px 8px 0;line-height:1.65}
.growth{font-size:13.5px;color:var(--ink-2);background:var(--paper-2);border-radius:9px;padding:12px 14px}
/* 裁定框按结果换底色（浅色，正文仍是墨色） */
.verdict-box.v-pass{background:#eaf3ec}
.verdict-box.v-fail{background:#f9f1e2}
.verdict-box.v-destroy{background:#f8eaea}
.verdict-box.v-pending{background:#f1efe9}

/* ---------- 表格 ---------- */
.otbl{width:100%;border-collapse:collapse;font-size:13px;margin:0 0 6px}
.otbl th,.otbl td{border:1px solid var(--line);padding:8px 10px;text-align:left;background:var(--paper)}
.otbl th{background:var(--accent-soft);color:var(--accent);font-weight:600;font-size:12px;white-space:nowrap}
.otbl td.dim{color:var(--ink-2)}
.otbl td.v-pass,.itbl td.v-pass{background:var(--paper);color:var(--green);font-weight:700}
.otbl td.v-fail{background:var(--paper);color:var(--amber);font-weight:700}
.otbl td.v-destroy{background:var(--paper);color:var(--red);font-weight:700}
.otbl td.v-pending{background:var(--paper);color:var(--ink-3);font-weight:700}

/* ---------- 时间轴 ---------- */
.rtimeline,.atimeline{border-left:2px solid var(--accent);padding-left:18px;margin-top:12px}
.rnode,.anode{margin-bottom:16px;position:relative}
.rnode:before,.anode:before{content:"";position:absolute;left:-24px;top:7px;width:9px;height:9px;
  background:var(--accent);border-radius:50%;border:2px solid var(--bg)}
.rworld{font-size:11.5px;color:var(--accent);font-weight:700;letter-spacing:.06em}
.rrule{font-size:14.5px;font-weight:700;line-height:1.55}
.rnote{font-size:12.5px;color:var(--ink-2);line-height:1.65}
.astage{font-weight:700;color:var(--accent);font-size:13.5px}
.atext{font-size:13.5px;color:var(--ink-2);line-height:1.7}
.theme-text{font-size:15.5px;color:var(--ink);background:var(--accent-soft);border-radius:var(--radius);
  padding:20px 22px;line-height:1.9;margin:0}

/* ---------- 目录 ---------- */
#chSearch{width:100%;max-width:420px;padding:9px 14px;border:1px solid var(--line);border-radius:9px;
  font-size:13.5px;margin-bottom:12px;font-family:inherit;background:var(--paper);color:var(--ink)}
#chSearch:focus{outline:none;border-color:var(--accent)}
/* 表头吸顶：外层不能是滚动容器。overflow-x:auto 会把 overflow-y 一起算成 auto，
   而 th 的 top:52px 是相对**滚动容器**算的——结果表头常驻在表格顶部往下 52px，
   把前两行盖住（旧版截图里第 1、2 章被压在表头下）。桌面端让外层保持 visible，
   窄屏才开横向滚动并放弃吸顶。 */
.itbl-wrap{overflow:visible}
.itbl{width:100%;border-collapse:collapse;font-size:12.5px}
.itbl th,.itbl td{border-bottom:1px solid var(--line-2);padding:7px 10px;text-align:left}
.itbl th{position:sticky;top:52px;background:var(--accent-soft);color:var(--accent);z-index:5;
  font-size:11.5px;font-weight:600}
@media(max-width:760px){
  .itbl-wrap{overflow-x:auto}
  .itbl th{position:static;top:auto}
}
.itbl tbody tr:hover{background:var(--paper-2)}
.itbl .ct{font-weight:600;color:var(--ink)}
.itbl .cw{color:var(--ink-3);white-space:nowrap}
.itbl .cc{color:var(--ink-3);text-align:right;white-space:nowrap}
footer{text-align:center;color:var(--ink-3);font-size:11.5px;padding:34px 0 0;line-height:1.7}
"""

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(M['title'])} · 拆书报告</title>
<style>{CSS}</style></head>
<body>
<nav class="toc"><span class="brand">{esc(M['title'])}</span>{nav_html}</nav>
<div class="wrap">
{hero}
{section_overview()}
{section_mech()}
{section_worlds()}
{section_rules()}
{section_arc()}
{section_theme()}
{section_index()}
<footer>数据源：回收站找回的整本知识图谱 · {esc(M.get('source',''))}<br>
{len(CH_IDX)} 章 / {len(WORLDS)} 世界 / {len(CHARS)} 人物 / {len(EVENTS)} 件事件 · 生成于 {esc(M.get('scraped_at',''))} · 单文件离线 HTML，不依赖任何外部资源</footer>
</div>
<script>{JS}</script>
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(HTML)
print("[done] out/swdw.html (%d KB)" % (len(HTML.encode("utf-8")) // 1024))
