/* ============================================================
 * 拆书报告 · 前端应用（无构建、无框架、离线可用）
 * 数据来自 DATA（Python 注入的紧凑 JSON）
 * 章节引用一律用章序号（整数），前端再查表
 * ============================================================ */
(function () {
  "use strict";

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  // 正则字面量转义（阶段名里可能有 · （ ） 等，先转再拼模式）
  function reEsc(s) {
    return String(s == null ? "" : s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, html) {
    var d = document.createElement(tag);
    if (cls) d.className = cls;
    if (html != null) d.innerHTML = html;
    return d;
  }
  function debounce(fn, ms) {
    var t = null;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }
  /* 搜索框统一入口：防抖 + 输入法合成保护 + 重渲染后还原光标 */
  function bindSearch(input, render) {
    if (!input) return;
    var composing = false;
    input.addEventListener("compositionstart", function () { composing = true; });
    input.addEventListener("compositionend", function () {
      composing = false;
      render(input.value.trim());
    });
    input.addEventListener("input", debounce(function () {
      if (!composing) render(input.value.trim());
    }, 220));
  }
  function hl(text, q) {
    var s = esc(text);
    if (!q) return s;
    var i = s.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return s;
    return s.slice(0, i) + "<mark class='hl'>" + s.slice(i, i + q.length) + "</mark>" + s.slice(i + q.length);
  }
  function toast(msg, withRetry) {
    var bar = $("toast-bar");
    bar.innerHTML = "<span>" + esc(msg) + "</span>";
    if (withRetry) {
      var b = el("button", null, "重试");
      b.onclick = function () { bar.hidden = true; withRetry(); };
      bar.appendChild(b);
    }
    var x = el("button", null, "关闭");
    x.onclick = function () { bar.hidden = true; };
    bar.appendChild(x);
    bar.hidden = false;
  }
  function chapterLabel(idx) {
    var c = chapterById[idx];
    // 展示用书中真实章号（c.n），导航仍用内部索引 idx
    var no = c && c.n ? c.n : idx;
    return c ? ("第" + no + "章 " + c.t) : ("第" + no + "章");
  }
  function chapterLinks(list) {
    // 抽取产出的 chapters 顺序不稳定（同一人物的章号可能 99 排在 221 后面），
    // 这里按内部索引排一次再输出，否则「出场章节」看起来是乱的。
    return (list || []).slice().sort(function (a, b) { return a - b; }).map(function (i) {
      var c = chapterById[i];
      var label = c && c.n ? c.n : i;   // 显示真实章号，data-ch 仍传内部索引
      return "<span class='chip-link' data-ch='" + i + "'>" + label + "</span>";
    }).join(" ");
  }
  // 点章节 chip（人物卡/地点卡/事件表里的「第N章」）→ 弹出该章的 KG 事件。
  // 之前这里写的是找 .phase-seg[data-ch=…]，但阶段段用的是 data-ph，
  // 所以永远找不到，点了只会切个视图、什么也不发生——一个安静的死按钮。
  function gotoChapter(i) {
    var c = chapterById[i];
    showChapterRef(c ? c.n : i, false);
  }

  /* ---------- 索引 ---------- */
  var persons = DATA.persons, places = DATA.places, events = DATA.events,
      relations = DATA.relations, chapters = DATA.chapters, phases = DATA.phases;
  var chapterById = {};
  chapters.forEach(function (c) { chapterById[c.i] = c; });
  // 章号 → 内部索引。全站的 data-ch 契约是「内部索引」，而 quotes.json 的 ch
  // 存的是**书中章号**（按 chapter_title 逐条核对：天才 105/105、废土 251/251），
  // 直接把 ch 塞进 data-ch 会让天才 112 章之后的点击错位 3 章（ch=221 会打开 218）。
  var idxByNo = {};
  chapters.forEach(function (c) { idxByNo[c.n] = c.i; });
  // 内部索引 i → 书中真实章号 n。天才基本法索引 112 之后 n = i - 3（防盗章伪影），
  // 两套编号混用就会错位：阶段轴的 s/e 是 n，而事件表里存的是 i，
  // 所以凡是拿事件的章去比阶段边界，都必须先过这道换算。
  var idx2no = {};
  chapters.forEach(function (c) { idx2no[c.i] = c.n; });
  var personById = {}, placeById = {}, eventById = {};
  persons.forEach(function (p) { personById[p.i] = p; });
  places.forEach(function (p) { placeById[p.i] = p; });
  events.forEach(function (e) { eventById[e.i] = e; });
  var aliasIndex = DATA.alias_index || {};
  // 人物语录索引（A4）：quotes.json 的 by_person 已按归属归属好的对白，
  // 按分数取靠前的几条。**绝不把叙述句挂到人名下**——叙述在 quotes 顶层，
  // 这里只吃 by_person，数据层就没混过。
  var quoteByPerson = {};
  ((DATA.quotes || {}).by_person || []).forEach(function (q) {
    var list = (q.quotes || []).slice().sort(function (a, b) { return (b.sc || 0) - (a.sc || 0); });
    if (list.length) quoteByPerson[q.name] = list;
  });
  // 示意分区标签：地图 / 地点表 / 详情三处共用一套口径。
  // 原 region 字段有 390 种自由取值（最散的那种脏），只作悬停证据，不拿来 displaying。
  var zoneLabel = {};
  // 分区表在 DATA.meta.geo_zones（不是 DATA.zones——那个键不存在，
  // 曾导致地点表格整列显示「—」）。两者都兼容一下，避免以后再踩。
  ((DATA.meta && DATA.meta.geo_zones) || DATA.zones || []).forEach(function (z) {
    zoneLabel[z.key] = z.label;
  });
  function placeZone(p) { return zoneLabel[p.z] || "—"; }
  // 未具名实体：名字是职业/身份称谓而非人名。只标注不删除——
  // 「技术员」出场 12 章有完整身份，是固定角色；「护士」出场 1 章才是背景板。
  var GENERIC_NAMES = ["护士", "医生", "男医生", "女医生", "助理医师", "众人", "人群", "男人",
    "女人", "老人", "小孩", "小男孩", "小女孩", "少年", "少女", "青年", "中年男人", "工作人员",
    "店员", "保安", "门卫", "司机", "乘客", "路人", "居民", "村民", "士兵", "军人", "警察",
    "学生", "老师", "顾客", "病人", "患者", "尸体", "负责人", "管理员", "检测人员", "检测员",
    "研究员", "技术员", "调查员", "分析员", "黑衣人", "陌生人", "声音", "人影", "对方", "那个人",
    "牙医们", "流浪汉"];
  // 地点功能基类：原始 t 在「室内/设施/建筑/机构」之间摇摆（同一个清洁中心
  // 被不同章标成不同类），展示一律用归约后的 tb，t 仅在悬停时作证据给出。
  function placeCat(p) { return p.tb || p.t || "—"; }
  function canonPerson(name) {
    if (personById["person:" + name]) return name;
    return aliasIndex[name] || name;
  }
  var relByPerson = {};
  relations.forEach(function (r) {
    (relByPerson[r.f] = relByPerson[r.f] || []).push(r);
    (relByPerson[r.t] = relByPerson[r.t] || []).push(r);
  });
  var eventsByPerson = {};
  events.forEach(function (e) {
    (e.p || []).forEach(function (n) {
      (eventsByPerson[canonPerson(n)] = eventsByPerson[canonPerson(n)] || []).push(e);
    });
  });
  var placesByChapter = {};
  places.forEach(function (p) {
    (p.c || []).forEach(function (i) {
      (placesByChapter[i] = placesByChapter[i] || []).push(p);
    });
  });

  var KIND_LABEL = { person: "人物", place: "地点", org: "派系/机构", regime: "政权/阵营", other: "其他实体" };
  var KIND_COLOR = { person: "var(--accent-2)", place: "var(--green)", org: "var(--gold)",
                     regime: "var(--red)", other: "var(--ink-3)" };
  var GEO_LABEL = { real: "真实坐标", schematic: "示意坐标", pending: "待核验" };

  // 关系基类配色：16 类固定色，避免「每条边都是独有标签」导致的视觉噪声
  var REL_COLOR = {
    "亲属": "#8c4a2f", "师徒": "#9c7a33", "上下级": "#3f6478", "队友": "#2f7d6b",
    "同事": "#6b8f9c", "敌对": "#a83e3e", "合作": "#4f7a4a", "爱慕": "#a3517a",
    "同源": "#7a5ca8", "寄生": "#6b4a2f", "交易": "#9a7b3f", "旧识": "#7a7a6b",
    "朋友": "#3f8a7a", "救助": "#3f6fa8", "融合": "#8a5a3f",
    // 支配 = 造物主/操控者/宿主一类的权力关系（废土特有），单独配色
    "支配": "#5a4a8a", "其他关系": "#b9b2a4"
  };
  // 人物分层查表（关系图默认只画核心人物）
  var personTier = {};
  var personByName = {};
  (typeof persons !== "undefined" ? persons : []).forEach(function (p) {
    personTier[p.n] = p.tr;
    personByName[p.n] = p;
  });
  // 阵营配色：按名字哈希取稳定色，同一阵营在所有视图里颜色一致
  var FACTION_PALETTE = ["#8c4a2f", "#3f6478", "#2f7d6b", "#9c7a33", "#a3517a",
    "#4f7a4a", "#7a5ca8", "#a83e3e", "#6b8f9c", "#8a5a3f"];
  function factionColor(f) {
    if (!f) return "var(--ink-3)";
    var h = 0;
    for (var i = 0; i < f.length; i++) h = (h * 31 + f.charCodeAt(i)) % 9973;
    return FACTION_PALETTE[h % FACTION_PALETTE.length];
  }
  var graphScope = "core";   // core | core_major | all
  function scopeAllows(name) {
    var t = personTier[name];
    if (!t) return true;                    // 非人物节点不受人物分层限制
    if (graphScope === "core") return t === "core";
    if (graphScope === "core_major") return t === "core" || t === "major";
    return true;
  }

  /* ---------- 标签页 ---------- */
  var VIEWS = [
    ["overview", "总览"], ["distribution", "分布"], ["characters", "人物"],
    ["places", "地点"], ["map", "地图"], ["events", "事件"],
    ["relations", "关系"], ["phases", "阶段轴"], ["quotes", "金句"], ["story", "故事"],
    ["perspectives", "学科视角"], ["papers", "论文"]
  ];
  function buildTabs() {
    var nav = $("tabs");
    VIEWS.forEach(function (v, i) {
      var b = el("button", "tab" + (i === 0 ? " active" : ""), esc(v[1]));
      b.setAttribute("role", "tab");
      b.dataset.view = v[0];
      b.onclick = function () { switchView(v[0]); };
      nav.appendChild(b);
    });
    var theme = el("button", "theme-toggle", "");
    applyTheme(loadTheme(), theme);
    theme.onclick = function () {
      applyTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
      if (currentView === "map") renderMap();
      if (currentView === "relations") renderRelations();
    };
    nav.appendChild(theme);
  }
  /* ---------- 主题：墨玉深色 dark / 素纸亮色 light ----------
     旧实现用 ink(=暗)/xuan(=亮，靠 :root 兜底) 两个反直觉的名字且刷新即丢，
     现改为语义化命名 + localStorage 持久化 + 首次访问跟随系统偏好。 */
  function loadTheme() {
    try {
      var s = localStorage.getItem("kg-report-theme");
      if (s === "dark" || s === "light") return s;
    } catch (e) { /* 隐私模式下 localStorage 不可用，按系统偏好走 */ }
    return (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  }
  function applyTheme(t, btn) {
    document.body.dataset.theme = t;
    try { localStorage.setItem("kg-report-theme", t); } catch (e) {}
    btn = btn || $("theme-toggle");
    if (btn) {
      btn.textContent = t === "dark" ? "素纸亮色" : "墨玉深色";
      btn.title = "切换主题（当前：" + (t === "dark" ? "墨玉深色" : "素纸亮色") + "）";
    }
  }
  var currentView = "overview";
  function switchView(v) {
    currentView = v;
    Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (t) {
      t.classList.toggle("active", t.dataset.view === v);
    });
    Array.prototype.forEach.call(document.querySelectorAll(".view"), function (s) {
      s.classList.toggle("active", s.id === "view-" + v);
    });
    if (v === "map") renderMap();
    if (v === "relations") renderRelations();
    if (v === "papers") renderPapers();
    syncHash();   // 地址栏即状态：切视图也回写，复制 URL 即可分享当前所在
  }

  /* ---------- 总览 ---------- */
  /* 首屏只回答一个问题：这本书长什么样。
     层级：一句话导读 + 可信边界标签 → 五个数字（每个都带自己的口径小字）
           → 章节节奏（可点阶段图例）+ 事件功能 → 五句结论（数字即证据）
           → 折叠的「数据体检」（原审计口径一字不减，只是默认不占屏）。
     纪律：视觉层只放能一眼读完的量；任何判断都要能在折叠区找到对应数字。 */
  /* 调色顺序按「相邻对比」排：同一本里挨着的两条叙事线必须一眼分得开，
     所以不能按色相顺时针摆（前三个都是砖红/赭石，看起来像同一条线）。 */
  var PHASE_PALETTE = ["#8c4a2f", "#2f6f6a", "#b08a3e", "#5a4b8c", "#3f7a4e",
    "#a3517a", "#2f5d8a", "#a8683a", "#6f8a45", "#8a4470"];
  /* 阶段名有重复：天才的「芝士世界（高中线）」跨了 7 段、废土的第一/二卷主线各出现 12 次。
     按「名字」而不是「段序」分组，同一叙事线在所有视图里同色，读者才能看出
     双时间线怎么来回切、副本流的主线在哪儿收束。 */
  var PHASE_GROUPS = [], PHASE_GROUP_IDX = {};
  phases.forEach(function (ph) {
    if (!PHASE_GROUP_IDX.hasOwnProperty(ph.name)) {
      PHASE_GROUP_IDX[ph.name] = PHASE_GROUPS.length;
      PHASE_GROUPS.push({ name: ph.name, spans: [], chapters: 0 });
    }
    var g = PHASE_GROUPS[PHASE_GROUP_IDX[ph.name]];
    g.spans.push([ph.s, ph.e]);
    g.chapters += (ph.e - ph.s + 1);
  });
  function groupOfNo(no) {
    for (var i = 0; i < phases.length; i++) {
      if (no >= phases[i].s && no <= phases[i].e) return phases[i].name;
    }
    return null;
  }
  function colorOfNo(no) {
    var nm = groupOfNo(no);
    if (nm === null || !PHASE_GROUP_IDX.hasOwnProperty(nm)) return "var(--ink-3)";
    return PHASE_PALETTE[PHASE_GROUP_IDX[nm] % PHASE_PALETTE.length];
  }

  function renderOverview() {
    var m = DATA.meta;
    var lede = String(m.desc || "").replace(/[。.]\s*$/, "");
    $("view-overview").innerHTML = [
      "<div class='ov-head'>" +
        "<div class='ov-lede'>" + esc(lede) + "。" +
          "全书 " + m.chapters + " 章按「章 / 人 / 地 / 事 / 关系」五元组逐章抽取，" +
          "下面每个数字都能在末尾的「数据体检」里追到原始口径。</div>" +
        "<div class='ov-flags'>" + ovFlags() + "</div>" +
      "</div>",
      ovStats(),
      "<div class='ov-row'>" + ovSparkPanel() + ovEventPanel() + "</div>",
      ovClaimsPanel(),
      ovAuditPanel()
    ].join("");
    bindOverviewClicks();
  }

  /* 可信边界标签：不写形容词，只标「这份报告做到了什么、没做什么」 */
  function ovFlags() {
    var m = DATA.meta, out = ["书中抽取 · 无外部补写"];
    var toc = (DATA.perspectives && DATA.perspectives.toc) || [];
    if (toc.length) out.push(toc.length + " 节学科视角");
    var np = ((DATA.papers && DATA.papers.items) || []).length;
    if (np) out.push(np + " 篇论文");
    if (phases.length) out.push(phases.length + " 个阶段");
    if (m.dup_pairs) out.push(m.dup_pairs + " 对重复章");
    return out.map(function (t) {
      return "<span class='ov-flag'>" + esc(t) + "</span>";
    }).join("");
  }

  /* 五个数字：每个数字下面那行小字才是重点——它说明这个数字可信到什么程度 */
  function ovStats() {
    var m = DATA.meta;
    var tc = { core: 0, major: 0, minor: 0, cameo: 0 };
    persons.forEach(function (p) { if (tc[p.tr] !== undefined) tc[p.tr]++; });
    // 地理三态按实际计数说话：两本书的现实坐标都是 0，硬写成「真实坐标 0 · 待核验 0」
    // 等于把两行零当说明——这里只报这本书真的有哪一种。
    var g = { real: 0, schematic: 0, pending: 0 };
    places.forEach(function (p) { if (g[p.g] !== undefined) g[p.g]++; });
    var geoNote = g.real
      ? "真实坐标 " + g.real + (g.pending ? " · 待核验 " + g.pending : (g.schematic ? " · 示意 " + g.schematic : ""))
      : (g.schematic ? "示意坐标 " + g.schematic + (g.pending ? " · 待核验 " + g.pending : "")
                     : "待核验 " + g.pending);
    var staged = events.filter(function (e) { return e.st; }).length;
    var rk = Object.keys(DATA.stats.relTypes || {}).filter(function (k) {
      return !REST_KEYS[k];
    });
    var cells = [
      [m.chapters, "章", "正文 " + (m.chars / 10000).toFixed(1) + " 万字"],
      [persons.length, "人物", "核心 " + tc.core + " · 主要 " + tc.major],
      [places.length, "地点", geoNote],
      [events.length, "事件", "归入阶段 " + staged],
      [relations.length, "关系", rk.length + " 类归约"]
    ];
    return "<div class='ov-hero'>" + cells.map(function (c) {
      return "<div class='ov-stat'><div class='v'>" + c[0] + "</div>" +
        "<div class='l'>" + esc(c[1]) + "</div>" +
        "<div class='s'>" + esc(c[2]) + "</div></div>";
    }).join("") + "</div>";
  }

  /* 章节节奏：一根柱 = 该章抽出的事件数。
     439 章逐根 1px 就成条形码，趋势被高频噪声淹没——超过 240 章自动把相邻章
     合并成桶，桶高取「每章平均」，与分布页按阶段聚合的口径完全一致。 */
  function ovSparkPanel() {
    var n = chapters.length || 1;
    var step = n > 240 ? Math.ceil(n / 150) : 1;
    var buckets = [], i;
    for (i = 0; i < chapters.length; i += step) {
      var grp = chapters.slice(i, i + step), ev = 0, pe = 0;
      grp.forEach(function (c) { ev += (c.e || 0); pe += (c.p || 0); });
      buckets.push({
        a: grp[0].n, b: grp[grp.length - 1].n,
        ev: ev / grp.length, pe: pe / grp.length,
        color: colorOfNo(grp[0].n)
      });
    }
    var max = 0;
    buckets.forEach(function (b) { if (b.ev > max) max = b.ev; });
    max = max || 1;
    var bars = buckets.map(function (b) {
      var h = Math.max(3, Math.round(b.ev / max * 92));
      var tip = "第" + b.a + (b.b !== b.a ? "–" + b.b : "") + "章：每章平均 " +
        b.ev.toFixed(1) + " 件事件 / " + b.pe.toFixed(1) + " 个人物出场";
      return "<i style='height:" + h + "px;background:" + b.color +
        "' title='" + esc(tip) + "'></i>";
    }).join("");
    // 图例按覆盖章数取前 8 条叙事线；点一下跳到该线第一段的阶段轴
    var ranked = PHASE_GROUPS.slice().sort(function (x, y) { return y.chapters - x.chapters; });
    var legend = ranked.slice(0, 8).map(function (g) {
      var sp = g.spans[0];
      return "<button type='button' data-ovphase='" +
        esc(g.name + "（" + sp[0] + "–" + sp[1] + "）") + "' title='" +
        g.spans.length + " 段 / 共 " + g.chapters + " 章'><i style='background:" +
        PHASE_PALETTE[PHASE_GROUP_IDX[g.name] % PHASE_PALETTE.length] + "'></i>" +
        esc(g.name) + "</button>";
    }).join("");
    if (PHASE_GROUPS.length > 8) {
      legend += "<button type='button' data-ovall='1' class='ov-more'>全部 " +
        phases.length + " 段 →</button>";
    }
    var lastNo = chapters.length ? chapters[chapters.length - 1].n : 1;
    return "<div class='ov-panel'><div class='ov-panel-head'><h3>章节节奏</h3>" +
      "<span class='hint'>" + (step > 1 ? "每 " + step + " 章合并 · " : "") +
      "柱高 = 每章事件数</span></div>" +
      "<div class='ov-spark'>" + bars + "</div>" +
      "<div class='ov-axis'><span>第1章</span><span>第" + lastNo + "章</span></div>" +
      "<div class='ov-legend'>" + legend + "</div></div>";
  }

  /* 事件功能：分布页的「一眼版」。只留前 6 类 + 其余合并，
     原始自由文本类型仍在事件卡里可回溯，这里不重复展示噪声。 */
  function ovEventPanel() {
    var et = DATA.stats.eventTypes || {};
    var total = 0;
    Object.keys(et).forEach(function (k) { total += et[k]; });
    var rows = [], rest = 0;
    Object.keys(et).forEach(function (k) {
      if (REST_KEYS[k]) rest += et[k];
      else rows.push([k, et[k]]);
    });
    rows.sort(function (a, b) { return b[1] - a[1]; });
    var top = rows.slice(0, 6);
    for (var i = 6; i < rows.length; i++) rest += rows[i][1];
    if (rest) top.push(["其他", rest]);
    // 归一化的分母必须在「其他」合并之后再取：合并后的「其他」常常比第一名还大
    // （废土 34% vs 14%），先取 max 会让它超出轨道被裁掉，横条长度就撒谎了。
    var mx = 0;
    top.forEach(function (r) { if (r[1] > mx) mx = r[1]; });
    mx = mx || 1;
    return "<div class='ov-panel'><div class='ov-panel-head'><h3>事件功能</h3>" +
      "<span class='hint'>" + total + " 件 · 归约后 " + Object.keys(et).length + " 类</span></div>" +
      "<div class='ov-figs'>" + top.map(function (r) {
        return "<div class='ov-fig' title='" + esc(r[0]) + " " + r[1] + " 件'>" +
          "<span class='nm'>" + esc(r[0]) + "</span>" +
          "<span class='tr'><span style='width:" + (r[1] / mx * 100).toFixed(1) +
          "%;background:var(--accent-2)'></span></span>" +
          "<span class='vl'>" + (r[1] / total * 100).toFixed(0) + "%</span></div>";
      }).join("") + "</div>" +
      "<div class='ov-note'>按叙事功能基类统计；原始自由文本类型保留在事件卡里，可回溯。</div></div>";
  }

  /* 结论先行：五句人话，每句自带分子/分母，读者能自己验算 */
  function ovClaimsPanel() {
    var fs = deriveFindings();
    return "<div class='ov-panel'><div class='ov-panel-head'><h3>数据说了什么</h3>" +
      "<span class='hint'>结论先行 · 数字即证据</span></div>" +
      "<div class='ov-claims'>" + fs.map(function (f) {
        return "<div class='ov-claim'><div class='c'>" + f.claim + "</div>" +
          "<div class='e'>证据：" + f.evidence + "</div></div>";
      }).join("") + "</div></div>";
  }

  /* 数据体检：原来的「关于本书 / 数据规模 / 数据状态 / Top12 / 完整分布」全部保留，
     只是默认收起。审计内容不删、不改口径——它只是不该占着第一屏。 */
  function ovAuditPanel() {
    var m = DATA.meta;
    var pendingPlaces = places.filter(function (p) { return p.g === "pending"; }).length;
    var unknownYear = events.filter(function (e) { return !e.yr; }).length;
    var h = [];
    h.push("<div class='ov-audit'>" +
      "<button type='button' class='ov-audit-bar' id='ovAuditToggle' " +
      "aria-expanded='false' aria-controls='ovAuditBody'>" +
      "<span class='ov-audit-t'>数据体检</span>" +
      "<span class='ov-audit-d'>关于本书 · 数据规模 · 数据状态 · 出场最多人物 · 完整分布</span>" +
      "<span class='ov-caret'>展开</span></button>" +
      "<div class='ov-audit-body' id='ovAuditBody'>");

    h.push("<div class='ov-panel'><h3>关于本书</h3>" +
      "<p class='ov-about'>" + esc(m.desc || "") + "</p>" +
      "<div class='small muted'>作者 " + esc(m.author || "—") +
      " · 来源：" + esc(m.source) + " · 抽取覆盖 " + m.extracted + "/" + m.chapters +
      " 章 · 数据生成于 " + esc(m.generated) + "</div></div>");

    h.push("<div class='ov-row'>");
    h.push("<div class='ov-panel'><h3>数据规模</h3><div class='table-wrap'><table class='data'><tbody>");
    [["章节", m.chapters], ["人物", persons.length], ["地点", places.length],
     ["事件", events.length], ["关系", relations.length],
     ["同章上下文事件", DATA.other.length]].forEach(function (r) {
      h.push("<tr><td>" + r[0] + "</td><td class='num'>" + r[1] + "</td></tr>");
    });
    h.push("</tbody></table></div></div>");

    h.push("<div class='ov-panel'><h3>数据状态<span class='hint'>诚实披露，不藏缺失</span></h3><div class='table-wrap'><table class='data'><tbody>");
    h.push("<tr><td>已定位地点（真实坐标）</td><td class='num'>" +
      places.filter(function (p) { return p.g === "real"; }).length + " / " + places.length + "</td></tr>");
    if (m.kind === "fictional_world") {
      h.push("<tr><td>示意坐标地点（架空世界）</td><td class='num'>" +
        places.filter(function (p) { return p.g === "schematic"; }).length + "</td></tr>");
    }
    h.push("<tr><td>待核验地点</td><td class='num'>" + pendingPlaces + "</td></tr>");
    h.push("<tr><td>未知年份事件</td><td class='num'>" + unknownYear + "</td></tr>");
    h.push("<tr><td>无任何关系的人物</td><td class='num'>" +
      persons.filter(function (p) { return !relByPerson[p.n]; }).length + "</td></tr>");
    // 实体分层：解释「为什么默认只显示一部分」，把取舍摊在明面上
    var tc = { core: 0, major: 0, minor: 0, cameo: 0 };
    persons.forEach(function (p) { if (tc[p.tr] !== undefined) tc[p.tr]++; });
    h.push("<tr><td title='按出场章数分层：核心≥20 / 主要≥5 / 次要≥2 / 龙套1'>人物分层</td><td class='num'>核心 " +
      tc.core + " / 主要 " + tc.major + " / 次要 " + tc.minor + " / 龙套 " + tc.cameo + "</td></tr>");
    var lc = { core: 0, major: 0, minor: 0, cameo: 0 };
    places.forEach(function (p) { if (lc[p.tr] !== undefined) lc[p.tr]++; });
    h.push("<tr><td title='龙套多为走廊/门口这类一过性场景'>地点分层</td><td class='num'>核心 " +
      lc.core + " / 主要 " + lc.major + " / 次要 " + lc.minor + " / 龙套 " + lc.cameo + "</td></tr>");
    if (m.dup_pairs) {
      h.push("<tr><td title='多源拼合 / 防盗章伪影'>重复章节对</td><td class='num'>" +
        m.dup_pairs + " 对 / 涉及 " + (m.dup_chapters || []).length + " 章</td></tr>");
    }
    h.push("</tbody></table></div></div></div>");

    h.push("<div class='ov-row'>");
    h.push("<div class='ov-panel'><h3>出场最多人物 Top 12</h3><div class='table-wrap'><table class='data'><tbody>");
    persons.slice(0, 12).forEach(function (p) {
      // 只显示主阵营（出现最多的那个）。一个人物最多挂过 51 个阵营字符串，
      // 全列或「等 N 项」都是噪声。
      var fs = p.f || [];
      // 只显示主阵营（出现最多的那个）。一个人物最多挂过 51 个阵营字符串，
      // 全列或「+50」都是噪声——完整列表进 title，需要核对的读者悬停即可。
      var fshow = "<span title='" + esc(fs.join(" / ")) + "'>" + esc(p.fm || (fs[0] || "—")) + "</span>";
      h.push("<tr data-person='" + esc(p.n) + "'><td>" + esc(p.n) + "</td><td class='small muted'>" +
        fshow + "</td><td class='num'>" + p.c.length + " 章</td></tr>");
    });
    h.push("</tbody></table></div></div>");

    h.push("<div class='ov-panel'><h3>事件功能完整分布<span class='hint'>归约后全部类别</span></h3>" +
      renderTypeBars(DATA.stats.eventTypes, "var(--accent-2)") +
      evRestHint(DATA.stats.eventTypes, events.length) + "</div></div>");

    h.push("</div></div>");
    return h.join("");
  }

  function deriveFindings() {
    var out = [], N = chapters.length || 1;
    function pct(a, b) { return (a / (b || 1) * 100); }

    // ① 视角结构：主角覆盖率决定这本书是「单主角」还是「群像」
    var top = persons[0];
    if (top) {
      var cover = pct(top.c.length, N);
      out.push({
        claim: cover >= 60
          ? "单主角强视角：全书由「" + esc(top.n) + "」一人贯穿"
          : "群像推进：没有单一主角，" + esc(top.n) + " 出场最多也仅占 " + cover.toFixed(0) + "%",
        evidence: esc(top.n) + " 出场 " + top.c.length + " / " + N + " 章（" + cover.toFixed(1) +
          "%）；前 3 名为 " +
          persons.slice(0, 3).map(function (p) { return esc(p.n) + " " + p.c.length + " 章"; }).join("、")
      });
    }

    // ② 叙事引擎：事件功能 Top2 决定「这本书靠什么往前走」
    var et = DATA.stats.eventTypes || {};
    var ek = Object.keys(et).filter(function (k) { return k !== "其他"; })
      .sort(function (a, b) { return et[b] - et[a]; });
    var etSum = 0; Object.keys(et).forEach(function (k) { etSum += et[k]; });
    if (ek.length >= 2) {
      out.push({
        claim: "主要推进力是「" + ek[0] + "」与「" + ek[1] + "」，两者合计占 " +
          (pct(et[ek[0]] + et[ek[1]], etSum)).toFixed(0) + "%",
        evidence: ek.slice(0, 4).map(function (k) {
          return k + " " + et[k] + " 件（" + pct(et[k], etSum).toFixed(1) + "%）";
        }).join("、") + "；合计 " + etSum + " 件"
      });
    }

    // ③ 场景流动性：一次性地点占比。只说事实，不推断题材——
    // 51% 和 65% 是两回事，用同一个「公路式」结论去套校园小说会失真。
    var once = places.filter(function (p) { return p.c.length === 1; }).length;
    if (places.length) {
      var r = pct(once, places.length);
      var flow = r >= 60 ? "场景高度流动：多数地点只用一次，故事靠不断开新场景推进"
        : r >= 40 ? "场景半流动：约一半地点只用一次，另一半反复出现"
        : "场景集中：多数地点反复出现，故事在少数固定空间里深挖";
      out.push({
        claim: flow,
        evidence: places.length + " 个地点中 " + once + " 个只出现 1 章（" + r.toFixed(1) +
          "%）；出场最多的是 " + places.slice(0, 3).map(function (p) {
            return esc(p.n) + "（" + p.c.length + " 章）";
          }).join("、")
      });
    }

    // ④ 关系结构：最大关系类说明「张力在哪」
    var rt = DATA.stats.relTypes || {};
    var rk = Object.keys(rt).filter(function (k) { return k !== "其他关系"; })
      .sort(function (a, b) { return rt[b] - rt[a]; });
    var rSum = 0; Object.keys(rt).forEach(function (k) { rSum += rt[k]; });
    if (rk.length >= 2) {
      out.push({
        claim: "人物关系的骨架是「" + rk[0] + "」与「" + rk[1] + "」",
        evidence: rk.slice(0, 4).map(function (k) {
          return k + " " + rt[k] + " 对";
        }).join("、") + "；共 " + rSum + " 对关系，归为 " + rk.length + " 个大类"
      });
    }

    // ⑤ 节奏峰值：哪一段最密
    if (phases.length && chapters.length) {
      var best = null;
      phases.forEach(function (ph) {
        var grp = chapters.filter(function (c) { var n = (c.n || c.i); return n >= ph.s && n <= ph.e; });
        if (!grp.length) return;
        var ev = 0, pe = 0;
        grp.forEach(function (c) { ev += (c.e || 0); pe += (c.p || 0); });
        var per = ev / grp.length;
        if (!best || per > best.per) best = { name: ph.name, s: ph.s, e: ph.e, per: per, pe: pe / grp.length };
      });
      if (best) {
        out.push({
          claim: "最密的一段是「" + esc(best.name) + "」（第 " + best.s + "–" + best.e + " 章）",
          evidence: "该阶段平均每章 " + best.per.toFixed(1) + " 件事件、" + best.pe.toFixed(1) +
            " 个人物出场；全书共划分 " + phases.length + " 个阶段"
        });
      }
    }
    return out;
  }
  /* 总览内的事件绑定：人物行点击开人物卡、阶段图例跳阶段轴、
     「全部阶段」跳阶段视图、体检条开合。全部用属性选择器，不依赖渲染顺序。 */
  function bindOverviewClicks() {
    var root = $("view-overview");
    Array.prototype.forEach.call(root.querySelectorAll("[data-person]"), function (tr) {
      tr.onclick = function () { showPerson(tr.dataset.person); };
    });
    Array.prototype.forEach.call(root.querySelectorAll("[data-ovphase]"), function (b) {
      b.onclick = function () { gotoPhase(b.dataset.ovphase); };
    });
    Array.prototype.forEach.call(root.querySelectorAll("[data-ovall]"), function (b) {
      b.onclick = function () { switchView("phases"); };
    });
    var tg = $("ovAuditToggle");
    if (tg) {
      tg.onclick = function () {
        var body = $("ovAuditBody");
        var open = body.classList.toggle("open");
        tg.setAttribute("aria-expanded", open ? "true" : "false");
        var c = tg.querySelector(".ov-caret");
        if (c) c.textContent = open ? "收起" : "展开";
      };
    }
  }

  /* ---------- 分布 ---------- */
  function renderDistribution() {
    var st = DATA.stats, html = [];
    html.push("<div class='panel'><h3>章节实体密度<span class='hint'>" +
      (chartMode === "phase" ? "按阶段聚合取每章平均，看全书节奏" : "逐章明细，看局部波动") + "</span></h3>");
    html.push("<div class='tier-row'><span class='muted small'>聚合粒度</span>" +
      "<button class='chip tier-btn " + (chartMode === "phase" ? "on" : "") + "' data-cmode='phase'>按阶段 " +
      phases.length + "</button>" +
      "<button class='chip tier-btn " + (chartMode === "chapter" ? "on" : "") + "' data-cmode='chapter'>逐章 " +
      chapters.length + "</button></div>");
    html.push(renderChapterBars(chartMode));
    html.push("</div>");
    html.push("<div class='grid-2'>");
    html.push("<div class='panel'><h3>事件功能分布<span class='hint'>按叙事功能归约</span></h3>" +
      renderTypeBars(st.eventTypes, "var(--accent-2)") + evRestHint(st.eventTypes, events.length) + "</div>");
    html.push("<div class='panel'><h3>地点功能分布<span class='hint'>按场所功能归约</span></h3>" +
      renderTypeBars(st.placeTypes, "var(--green)") + evRestHint(st.placeTypes, places.length) + "</div>");
    html.push("</div><div class='grid-2'>");
    html.push("<div class='panel'><h3>阵营/势力 Top 12<span class='hint'>按提及人数</span></h3>" +
      renderFactionBars() + factionHint() + "</div>");
    html.push("<div class='panel'><h3>关系类别 Top 12<span class='hint'>已归约为有限基类</span></h3>" +
      renderTypeBars(st.relTypes, "var(--gold)") + evRestHint(st.relTypes, relations.length) + "</div>");
    html.push("</div>");
    $("view-distribution").innerHTML = html.join("");
    Array.prototype.forEach.call($("view-distribution").querySelectorAll(".chip[data-cmode]"), function (c) {
      c.onclick = function () { chartMode = c.dataset.cmode; renderDistribution(); };
    });
  }
  var chartMode = "phase";   // phase = 按阶段取平均（默认）｜chapter = 逐章
  function renderChapterBars(mode) {
    mode = mode || chartMode;
    var dupSet = {};
    (DATA.meta.dup_chapters || []).forEach(function (i) { dupSet[i] = true; });
    var w = 1100, h = 240, pad = 34;

    // 439 章逐根柱子视觉上就是条形码，趋势被高频噪声淹没。
    // 默认按阶段聚合取「每章平均」，换成 43 根柱就能看出节奏。
    var units;
    if (mode === "phase") {
      units = phases.map(function (ph) {
        var grp = chapters.filter(function (c) {
          var n = (c.n || c.i);
          return n >= ph.s && n <= ph.e;
        });
        if (!grp.length) return null;
        var sp = 0, se = 0;
        grp.forEach(function (c) { sp += (c.p || 0); se += (c.e || 0); });
        var ap = sp / grp.length, ae = se / grp.length;
        return {
          label: ph.name, p: ap, e: ae, dup: false,
          tip: ph.name + "（第" + ph.s + "–" + ph.e + " 章，共 " + grp.length + " 章）每章平均：人物 " +
            ap.toFixed(1) + " / 事件 " + ae.toFixed(1)
        };
      }).filter(Boolean);
    } else {
      units = chapters.map(function (c) {
        var dup = dupSet[c.i];
        return {
          label: "第" + (c.n || c.i) + "章 " + c.t,
          p: c.p || 0, e: c.e || 0, dup: dup,
          tip: "第" + (c.n || c.i) + "章 " + c.t + "：人物 " + (c.p || 0) + " / 事件 " + (c.e || 0) +
            (dup ? "（源文本重复章）" : "")
        };
      });
    }
    var maxN = 1;
    units.forEach(function (u) { maxN = Math.max(maxN, u.p, u.e); });
    // 纵轴上界取整：直接用最大值会出现「11 / 8 / 4」这种别扭刻度。
    // 抬到能被 4 整除的档位，四等分后就是 3/6/9/12 这样的整数。
    var NICE = [4, 8, 12, 16, 20, 24, 30, 40, 50, 60, 80, 100, 120, 150, 200];
    for (var ni = 0; ni < NICE.length; ni++) {
      if (NICE[ni] >= maxN) { maxN = NICE[ni]; break; }
    }
    var bw = Math.max(2, (w - pad * 2) / units.length - 1.5);
    var s = ["<svg viewBox='0 0 " + w + " " + h + "' role='img' aria-label='章节实体密度图'>"];
    [0, 0.25, 0.5, 0.75, 1].forEach(function (f) {
      var y = h - pad - f * (h - pad * 2);
      s.push("<line x1='" + pad + "' y1='" + y + "' x2='" + (w - pad) + "' y2='" + y +
        "' stroke='var(--line)' stroke-width='1'/>");
      s.push("<text x='" + (pad - 6) + "' y='" + (y + 4) + "' text-anchor='end' font-size='10' fill='var(--ink-3)'>" +
        Math.round(f * maxN) + "</text>");
    });
    units.forEach(function (c, i) {
      var x = pad + i * ((w - pad * 2) / units.length);
      var hp = (c.p || 0) / maxN * (h - pad * 2), he = (c.e || 0) / maxN * (h - pad * 2);
      var dup = c.dup;
      var op = dup ? 0.3 : 0.85;
      var tip = c.tip;
      // 阶段模式下柱子更宽、并排画；逐章模式错开半个柱宽避免互相遮挡
      var off = mode === "phase" ? 0 : bw / 2;
      s.push("<rect x='" + x.toFixed(2) + "' y='" + (h - pad - hp).toFixed(2) + "' width='" + bw.toFixed(2) +
        "' height='" + hp.toFixed(2) + "' fill='var(--accent-2)' opacity='" + op + "'><title>" +
        esc(tip) + "</title></rect>");
      s.push("<rect x='" + (x + off).toFixed(2) + "' y='" + (h - pad - he).toFixed(2) + "' width='" + bw.toFixed(2) +
        "' height='" + he.toFixed(2) + "' fill='var(--accent)' opacity='" + (dup ? 0.25 : 0.75) + "'><title>" +
        esc(tip) + "</title></rect>");
    });
    // 阶段分界线只在逐章模式下有意义（阶段模式本身就是按阶段排的柱）
    if (mode === "chapter") phases.forEach(function (ph) {
      var x1 = pad + (ph.s - 1) * ((w - pad * 2) / chapters.length);
      var x2 = pad + ph.e * ((w - pad * 2) / chapters.length);
      s.push("<line x1='" + x1.toFixed(2) + "' y1='14' x2='" + x1.toFixed(2) + "' y2='" + (h - pad) +
        "' stroke='var(--gold)' stroke-dasharray='3 3' stroke-width='1'/>");
      // 阶段多时（本书 40+ 个）标签必然重叠：只在够宽处标注，并按宽度截断，
      // 完整名称放进 <title> 供悬停查看
      var span = x2 - x1;
      if (span < 42) return;
      var maxChars = Math.max(2, Math.floor(span / 9));
      var label = ph.name.length > maxChars ? ph.name.slice(0, maxChars - 1) + "…" : ph.name;
      s.push("<text x='" + ((x1 + x2) / 2).toFixed(2) + "' y='10' text-anchor='middle' font-size='10' fill='var(--gold)'>" +
        esc(label) + "<title>" + esc(ph.name) + "（第" + ph.s + "–" + ph.e + "章）</title></text>");
    });
    s.push("</svg>");
    if (mode === "phase") {
      s.push("<div class='chart-legend'><span><i style='background:var(--accent-2)'></i>每阶段平均出场人物</span>" +
        "<span><i style='background:var(--accent)'></i>每阶段平均发生事件</span>" +
        "<span class='muted'>共 " + units.length + " 个阶段 · 悬停看阶段名与章范围</span></div>");
    } else {
      s.push("<div class='chart-legend'><span><i style='background:var(--accent-2)'></i>每章出场人物</span>" +
        "<span><i style='background:var(--accent)'></i>每章发生事件</span>" +
        "<span><i style='background:var(--gold)'></i>阶段分界</span>" +
        "<span style='opacity:.5'><i style='background:var(--ink-3)'></i>半透明 = 源文本重复章（多源拼合，计数仍计入）</span></div>");
    }
    return s.join("");
  }
  // 归约不是全能的：总有一次性情节归纳不进任何类。这里把「没归进去多少」
  // 明说出来——比假装 100% 归类更可信，也避免读者以为榜单就是全貌。
  // 兜底桶：「其他/其他场所/其他关系」是归约失败的产物，不是一类信息。
  // 让它参与排行会把噪声顶到第一名（读者第一眼看到的仍然是「其他 336」），
  // 所以从榜单里剔除，改用脚注如实披露数量——信息不减，但不再喧宾夺主。
  var REST_KEYS = { "其他": 1, "其他场所": 1, "其他关系": 1, "未分类": 1 };
  function evRestHint(counts, total) {
    var keys = Object.keys(counts || {}), sum = 0, rest = 0;
    keys.forEach(function (k) { sum += counts[k]; if (REST_KEYS[k]) rest += counts[k]; });
    if (!sum) return "";
    var real = keys.filter(function (k) { return !REST_KEYS[k]; });
    var parts = [];
    if (rest) parts.push(rest + " 条（" + (rest / sum * 100).toFixed(1) + "%）无法归入任何类，未参与排序、原样保留");
    if (real.length > 12) parts.push("另有 " + (real.length - 12) + " 个小类未在图上显示");
    return parts.length ? "<div class='muted small' style='margin-top:10px;line-height:1.6'>注：" + parts.join("；") + "。</div>" : "";
  }
  function renderTypeBars(counts, color) {
    var keys = Object.keys(counts || {}).filter(function (k) { return !REST_KEYS[k]; })
      .sort(function (a, b) { return counts[b] - counts[a]; }).slice(0, 12);
    var mx = keys.length ? counts[keys[0]] : 1, s = [];
    keys.forEach(function (k) {
      s.push("<div class='bar-row'><span class='lb' title='" + esc(k) + "'>" + esc(k) + "</span><div class='track'><div class='fill' style='width:" +
        (counts[k] / mx * 100).toFixed(1) + "%;background:" + color + "'></div></div><span class='val'>" + counts[k] + "</span></div>");
    });
    return s.join("") || "<div class='muted small'>无数据</div>";
  }
  function factionHint() {
    // 有名字但没有归属的人数不算小：废土里大量散人/独狼，不披露会让人
    // 误以为榜单覆盖了全部人物。
    var none = persons.filter(function (p) { return !p.fm; }).length;
    if (!none) return "";
    return "<div class='muted small' style='margin-top:10px;line-height:1.6'>注：另有 " + none +
      " 人未标注任何归属（散人/独狼/身份未明），不计入榜。</div>";
  }
  function renderFactionBars() {
    var cnt = {};
    // 按主阵营统计：一个人物挂几十个阵营字符串时，全量统计会把榜单撑成噪声
    persons.forEach(function (p) { if (p.fm) cnt[p.fm] = (cnt[p.fm] || 0) + 1; });
    return renderTypeBars(cnt, "var(--teal)");
  }

  /* ---------- 人物 ---------- */
  var charQuery = "";
  var charTier = "main";   // main = 核心+主要（默认）｜all = 全部含龙套
  var TIER_LABEL = { core: "核心", major: "主要", minor: "次要", cameo: "龙套" };
  var TIER_ORDER = ["core", "major", "minor", "cameo"];
  function tierCounts(list) {
    var c = { core: 0, major: 0, minor: 0, cameo: 0 };
    list.forEach(function (x) { if (c[x.tr] !== undefined) c[x.tr]++; });
    return c;
  }
  function renderCharacters() {
    var q = charQuery;
    var searched = persons.filter(function (p) {
      if (!q) return true;
      return (p.n + " " + (p.a || []).join(" ") + " " + (p.f || []).join(" ") + " " + p.r)
        .toLowerCase().indexOf(q.toLowerCase()) >= 0;
    });
    var tc = tierCounts(searched);
    // 默认只给「核心 + 主要」，一次性龙套折叠起来——379 张卡平铺等于没有信息
    var list = charTier === "all" ? searched : searched.filter(function (p) {
      return p.tr === "core" || p.tr === "major";
    });

    var html = [];
    html.push("<div class='panel'><div class='search-row'>" +
      "<div class='search-box'><span>🔍</span><input id='char-search' type='text' placeholder='搜索姓名 / 别名 / 阵营 / 身份（共 " +
      persons.length + " 人）' value='" + esc(q) + "'></div>" +
      "<button class='chip' id='print-cards'>打印本页卡片</button></div>");

    // 分层切换：把「显示多少」这件事交给读者，而不是默认倒全部
    html.push("<div class='tier-row'><span class='muted small'>显示范围</span>" +
      "<button class='chip tier-btn " + (charTier === "main" ? "on" : "") + "' data-tier='main'>" +
      "核心 + 主要 " + (tc.core + tc.major) + "</button>" +
      "<button class='chip tier-btn " + (charTier === "all" ? "on" : "") + "' data-tier='all'>" +
      "全部 " + searched.length + "（含龙套 " + tc.cameo + "）</button>" +
      "</div>");

    if (!list.length) {
      html.push("<div class='muted'>没有匹配「" + esc(q) + "」的人物。</div></div>");
      $("view-characters").innerHTML = html.join("");
      bindSearch($("char-search"), function (v) { charQuery = v; renderCharacters(); syncHash(); });
      bindTierBtns();
      return;
    }
    html.push("<div class='small muted' style='margin-bottom:10px'>当前 " + list.length +
      " 人 · 点击卡片翻面看详情 · 分层依据：出场章数 ≥20 核心 / ≥5 主要 / ≥2 次要 / 1 章龙套</div>");

    // 分组展示：核心 / 主要 / 次要 / 龙套 各自成段，读者一眼知道谁重要
    TIER_ORDER.forEach(function (t) {
      var grp = list.filter(function (p) { return p.tr === t; });
      if (!grp.length) return;
      html.push("<div class='tier-head'><b>" + TIER_LABEL[t] + "</b>" +
        "<span class='muted small'> " + grp.length + " 人</span></div>");
      html.push("<div class='card-grid'>");
      grp.forEach(function (p) { html.push(pokeCard(p)); });
      html.push("</div>");
    });
    html.push("</div>");
    $("view-characters").innerHTML = html.join("");
    bindSearch($("char-search"), function (v) { charQuery = v; renderCharacters(); syncHash(); });
    bindTierBtns();
    bindCardEvents();
  }
  function bindTierBtns() {
    Array.prototype.forEach.call(document.querySelectorAll(".tier-btn"), function (b) {
      b.onclick = function () { charTier = b.dataset.tier; renderCharacters(); };
    });
  }
  function pokeCard(p) {
    var one = p.r || "（本章身份未标注）";
    var fm = p.fm || "书中人物";
    // 卡背语录（A4）：只放一句，取归属分数最高的一条。没有归属到人的对白
    // 就不放——空白好过编一句。章号走 chapterById 换真章号（不用内部索引）。
    var qs = quoteByPerson[p.n] || [];
    var q1 = qs[0];
    var qCh = q1 ? q1.ch : 0;
    var quoteHtml = q1
      ? "<div class='poke-quote'>「" + esc(q1.t) + "」" +
        "<span class='poke-quote-src'>第" + qCh + "章" +
        (q1.h ? " · " + esc(q1.h) : "") + "</span></div>"
      : "";
    var back = "<div class='poke-face poke-back'>" +
      "<div class='poke-kv'><b>姓名</b> " + esc(p.n) + "</div>" +
      (p.a && p.a.length ? "<div class='poke-kv'><b>别名</b> " + esc(p.a.join("、")) + "</div>" : "") +
      "<div class='poke-kv'><b>主阵营</b> " + esc(fm) + "</div>" +
      (p.f && p.f.length > 1 ? "<div class='poke-kv'><b>其他归属</b> " + esc(p.f.filter(function (x) { return x !== fm; }).slice(0, 4).join(" / ")) +
        (p.f.length > 5 ? " 等 " + (p.f.length - 1) + " 项" : "") + "</div>" : "") +
      "<div class='poke-kv'><b>出场</b> " + p.c.length + " 章 · 提及 " + p.m + " 次</div>" +
      quoteHtml +
      "<div class='poke-kv'><b>来源</b> <span class='badge src'>书中抽取</span></div>" +
      "<div style='flex:1'></div>" +
      "<div class='flip-hint'><span class='chip-link' data-detail='" + esc(p.n) + "'>详情</span> · 点击翻回</div></div>";
    return "<div class='poke-card tier-" + (p.tr || "cameo") + "' data-person='" + esc(p.n) + "' title='" + esc(p.n) + "'>" +
      "<div class='poke-inner'>" +
      "<div class='poke-face poke-front'>" +
      "<div class='poke-faction'>" + esc(fm) + "</div>" +
      "<div class='poke-name'>" + esc(p.n) + "</div>" +
      "<div class='poke-one'>" + esc(one) + "</div>" +
      "<div class='poke-foot'>出场 " + p.c.length + " 章" +
      (p.tr === "cameo" ? " · 龙套" : "") + "</div></div>" + back + "</div></div>";
  }
  function bindCardEvents() {
    Array.prototype.forEach.call(document.querySelectorAll(".poke-card"), function (card) {
      card.onclick = function (e) {
        if (e.target.dataset && e.target.dataset.detail) {
          showPerson(e.target.dataset.detail);
          e.stopPropagation();
          return;
        }
        card.classList.toggle("flipped");
      };
    });
    var pb = $("print-cards");
    if (pb) pb.onclick = printCards;
  }
  function printCards() {
    // 注意两点（都是探针抓出来的真 bug）：
    // 1) 卡片容器是 class="card-grid" 且按 tier 分段（核心/主要各一个 grid），
    //    不是 id="card-grid"——旧代码按 id 找恒为 null，一张卡都没打出来；
    // 2) 只取第一个 grid 等于只打核心档。应按「当前人物视图里全部卡片」克隆，
    //    与屏幕上看到的内容（默认核心+主要）一致。
    var cards = document.querySelectorAll("#view-characters .poke-card");
    if (!cards.length) { toast("请先进入人物视图再打印卡片"); return; }
    var area = $("print-area") || (function () {
      var d = el("div"); d.id = "print-area"; document.body.appendChild(d); return d;
    })();
    area.innerHTML = "";
    Array.prototype.forEach.call(cards, function (card) {
      var c = card.cloneNode(true);
      c.classList.remove("flipped");
      area.appendChild(c);
    });
    // 打印作用域收窄为「仅卡片」：此前 @media print 输出全部 11 个视图
    // （实测 Ctrl+P 得 69 页 / 10.8MB），与「打印本页卡片」的文案不符。
    // 不加这个类时仍是完整手册模式（全部视图），两种用法都保留。
    document.body.classList.add("printing-cards");
    var done = function () { document.body.classList.remove("printing-cards"); };
    window.addEventListener("afterprint", done, { once: true });
    setTimeout(done, 30000); // 兜底：afterprint 不触发的环境（如无头）防类名残留
    window.print();
  }

  /* ---------- 地点 ---------- */
  var placeQuery = "";
  function renderPlaces() {
    var q = placeQuery;
    var list = places.filter(function (p) {
      if (!q) return true;
      return (p.n + " " + (p.mo || "") + " " + (p.rg || "") + " " + (p.t || "") + " " + (p.tb || "") + " " + placeZone(p))
        .toLowerCase().indexOf(q.toLowerCase()) >= 0;
    });
    var html = ["<div class='panel'><div class='search-row'>" +
      "<div class='search-box'><span>🔍</span><input id='place-search' type='text' placeholder='搜索地点 / 今址 / 区域 / 类型（共 " +
      places.length + " 处）' value='" + esc(q) + "'></div></div>"];
    if (!list.length) {
      html.push("<div class='muted'>没有匹配「" + esc(q) + "」的地点。</div>");
    } else {
      html.push("<div class='small muted' style='margin-bottom:10px'>命中 " + list.length + " 处 · 点击查看详情（含出场章节）</div>");
      html.push("<div class='table-wrap'><table class='data'><thead><tr><th>地点</th><th>今址/对应</th><th>所在分区</th><th>功能类别</th><th>坐标状态</th><th>出场</th></tr></thead><tbody>");
      list.slice(0, 400).forEach(function (p) {
        html.push("<tr data-place='" + esc(p.n) + "'><td>" + hl(p.n, q) + "</td><td class='small'>" +
          esc(p.mo || "—") + "</td><td class='small' title='抽取原文区域：" + esc(p.rg || "空") + "'>" + esc(placeZone(p)) + "</td><td class='small' title='抽取原文类型：" + esc(p.t || "空") + "'>" +
          esc(placeCat(p)) + "</td><td><span class='badge " + p.g + "'>" + (GEO_LABEL[p.g] || p.g) + "</span></td>" +
          "<td class='num'>" + p.c.length + " 章</td></tr>");
      });
      html.push("</tbody></table></div>");
      if (list.length > 400) html.push("<div class='small muted' style='margin-top:8px'>仅显示前 400 处，请用搜索缩小范围。</div>");
    }
    html.push("</div>");
    $("view-places").innerHTML = html.join("");
    bindSearch($("place-search"), function (v) { placeQuery = v; renderPlaces(); syncHash(); });
    Array.prototype.forEach.call($("view-places").querySelectorAll("[data-place]"), function (tr) {
      tr.onclick = function () { showPlace(tr.dataset.place); };
    });
  }

  /* ---------- 地图 ---------- */
  var leafletLoading = false, mapInstance = null;
  var mapScope = "main";   // main = 核心+主要（默认）｜all = 全部
  var ZONE_COLORS = ["var(--accent)", "var(--accent-2)", "var(--teal)", "var(--gold)", "var(--green)", "var(--red)"];
  function renderMap() {
    var box = $("view-map");
    // 1037 个点全画出来等于没画：默认只给核心+主要，其余按需展开
    var pick = function (arr) {
      return mapScope === "all" ? arr : arr.filter(function (p) {
        return p.tr === "core" || p.tr === "major";
      });
    };
    var allSch = places.filter(function (p) { return p.g === "schematic" && p.co; });
    var allReal = places.filter(function (p) { return p.g === "real" && p.co; });
    var real = pick(allReal);
    var sch = pick(allSch);
    var pend = places.filter(function (p) { return p.g === "pending"; });
    var zones = (DATA.meta.geo_zones || []);
    var html = ["<div class='panel'><h3>地图</h3>"];
    if (DATA.meta.kind === "fictional_world") {
      html.push("<div class='small muted' style='margin-bottom:10px'>本书为架空世界：下图是<b>示意坐标系</b>（非现实坐标，仅表现空间关系），按 " +
        zones.map(function (z) { return esc(z.label); }).join(" / ") + " 分带。</div>");
    } else if (real.length && sch.length) {
      html.push("<div class='small muted' style='margin-bottom:10px'>真实地名落真实坐标（在线地图）；虚构城市「安宁市」的地点用<b>城市示意坐标</b>（非现实地理位置）。</div>");
    } else if (sch.length) {
      html.push("<div class='small muted' style='margin-bottom:10px'>故事发生在虚构城市「安宁市」：下图按城区功能分带（" +
        zones.map(function (z) { return esc(z.label); }).join(" / ") + "），坐标为<b>示意</b>，非现实地理位置。</div>");
    } else {
      html.push("<div class='small muted' style='margin-bottom:10px'>真实地名落到真实坐标；未定位地点列为「待核验」，不硬填坐标。</div>");
    }
    var totalMapped = allReal.length + allSch.length;
    var shown = real.length + sch.length;
    html.push("<div class='tier-row'><span class='muted small'>显示范围</span>" +
      "<button class='chip tier-btn " + (mapScope === "main" ? " on" : "") + "' data-mscope='main'>核心 + 主要 " +
      pick(allReal.concat(allSch)).length + "</button>" +
      "<button class='chip tier-btn " + (mapScope === "all" ? " on" : "") + "' data-mscope='all'>全部 " +
      totalMapped + "</button>" +
      (mapScope !== "all" && totalMapped > shown
        ? "<span class='muted small'>（隐藏 " + (totalMapped - shown) + " 个只出现 1–4 章的地点）</span>" : "") +
      "</div>");
    html.push("<div class='map-layout'><div class='map-canvas' id='map-canvas'></div>" +
      "<div class='map-side' id='map-side'></div></div>");
    html.push("<div class='map-note' id='map-note'></div></div>");
    box.innerHTML = html.join("");
    Array.prototype.forEach.call(box.querySelectorAll(".chip[data-mscope]"), function (c) {
      c.onclick = function () { mapScope = c.dataset.mscope; renderMap(); };
    });

    if (DATA.meta.kind === "modern_real" && real.length && !zones.length) {
      loadLeaflet(function () { renderLeafletMap(real); }, function () {
        renderSvgMap(real, true);
        toast("在线地图加载失败，已切换为离线点位图", function () { renderMap(); });
      });
    } else if (zones.length && sch.length) {
      renderSvgMap(sch, false);
    } else {
      renderSvgMap(real, true);
    }

    var side = $("map-side");
    var items = (sch.length ? sch : real).concat(pend.slice(0, 40));
    side.innerHTML = "<div class='small muted' style='margin-bottom:8px'>共 " + items.length +
      " 处（点击查看详情）</div>" + items.map(function (p) {
        return "<div class='map-item' data-place='" + esc(p.n) + "'><div class='nm'>" + esc(p.n) + "</div>" +
          "<div class='small muted'>" + esc(placeCat(p)) + " · " + esc(placeZone(p)) +
          " · " + p.c.length + " 章 <span class='badge " + p.g + "'>" + (GEO_LABEL[p.g] || p.g) + "</span></div></div>";
      }).join("");
    Array.prototype.forEach.call(side.querySelectorAll("[data-place]"), function (it) {
      it.onclick = function () { showPlace(it.dataset.place); };
    });
    var note = $("map-note");
    if (pend.length) {
      note.innerHTML = "另有 <b>" + pend.length + "</b> 处地点未能定位（生僻或高度歧义），已如实标注「待核验」——对巡礼场景，错误坐标比缺失更有害。";
    } else if (sch.length && DATA.meta.kind === "modern_real") {
      note.innerHTML = "示意坐标不指向真实地理位置，仅用于表达书中地点的相对空间关系（同区聚集、跨区距离）。";
    }
  }
  function loadLeaflet(onOk, onFail) {
    if (window.L) { onOk(); return; }
    if (leafletLoading) { setTimeout(function () { loadLeaflet(onOk, onFail); }, 400); return; }
    leafletLoading = true;
    var css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(css);
    var js = document.createElement("script");
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    js.onload = function () { leafletLoading = false; if (window.L) onOk(); else onFail(); };
    js.onerror = function () { leafletLoading = false; onFail(); };
    document.head.appendChild(js);
  }
  function renderLeafletMap(real) {
    var L = window.L, canvas = $("map-canvas");
    canvas.innerHTML = "";
    mapInstance = L.map(canvas).setView([35, 110], 5);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
      attribution: "Esri", maxZoom: 15
    }).addTo(mapInstance);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "OSM", maxZoom: 15
    }).addTo(mapInstance);
    var group = [];
    real.forEach(function (p) {
      var mk = L.circleMarker([p.co[1], p.co[0]], {
        radius: 7, color: "#8c4a2f", fillColor: "#b08a3e", fillOpacity: .9, weight: 1.5
      }).addTo(mapInstance);
      mk.bindTooltip(p.n, { direction: "top" });
      mk.on("click", function () { showPlace(p.n); });
      group.push(mk);
    });
    setTimeout(function () {
      if (group.length) mapInstance.fitBounds(L.featureGroup(group).getBounds().pad(0.25));
    }, 300);
  }
  function renderSvgMap(list, isReal) {
    var canvas = $("map-canvas");
    if (!canvas) return;
    var W = 760, H = 480;
    var zones = DATA.meta.geo_zones || [];
    var s = ["<svg viewBox='0 0 " + W + " " + H + "' role='img' aria-label='地点分布图'>"];
    if (zones.length && !isReal) {
      var zColor = {};
      // 只画「当前范围内有地点」的分区。空分区会在地图上留一个没有点的
      // 虚线空圈（异地/异世界这类飞地地点少，默认视图全被折叠），
      // 读者看到会以为是渲染错误。
      var liveZones = {};
      list.forEach(function (p) { if (p.z) liveZones[p.z] = (liveZones[p.z] || 0) + 1; });
      var hiddenZones = [];
      zones.forEach(function (z, i) {
        zColor[z.key] = ZONE_COLORS[i % ZONE_COLORS.length];
        if (!liveZones[z.key]) { hiddenZones.push(z.label); return; }
        var cx = z.cx / 100 * W, cy = z.cy / 100 * H, rx = z.r / 100 * W * 1.02, ry = z.r / 100 * H * 0.8;
        s.push("<ellipse cx='" + cx + "' cy='" + cy + "' rx='" + rx.toFixed(1) + "' ry='" + ry.toFixed(1) +
          "' fill='" + zColor[z.key] + "' opacity='0.07' stroke='" + zColor[z.key] +
          "' stroke-opacity='0.35' stroke-dasharray='5 4'/>");
        s.push("<text class='zone-label' x='" + cx + "' y='" + (cy - ry - 6).toFixed(1) +
          "' text-anchor='middle' fill='" + zColor[z.key] + "'>" + esc(z.label) +
          "（" + liveZones[z.key] + "）</text>");
      });
      list.forEach(function (p) {
        var x = p.co[0] / 100 * W, y = p.co[1] / 100 * H;
        var c = zColor[p.z] || "var(--accent)";
        s.push("<g class='map-dot' data-place='" + esc(p.n) + "'><circle cx='" + x.toFixed(1) + "' cy='" + y.toFixed(1) +
          "' r='6' fill='" + c + "' opacity='0.85' stroke='var(--panel)' stroke-width='1.5'><title>" +
          esc(p.n) + "（" + esc(placeCat(p)) + "）</title></circle></g>");
      });
      s.push("<text x='12' y='" + (H - 10) + "' font-size='10' fill='var(--ink-3)'>示意坐标系 · 非现实地理位置 · 共 " +
        list.length + " 处" +
        (hiddenZones.length ? "（已折叠分区：" + esc(hiddenZones.join("、")) + "，切「全部」可见）" : "") +
        "</text>");
    } else {
      var lngs = list.map(function (p) { return p.co[0]; }), lats = list.map(function (p) { return p.co[1]; });
      var minx = Math.min.apply(null, lngs), maxx = Math.max.apply(null, lngs);
      var miny = Math.min.apply(null, lats), maxy = Math.max.apply(null, lats);
      if (maxx - minx < 1) { maxx = minx + 1; }
      if (maxy - miny < 1) { maxy = miny + 1; }
      var pad = 40;
      list.forEach(function (p) {
        var x = pad + (p.co[0] - minx) / (maxx - minx) * (W - pad * 2);
        var y = H - pad - (p.co[1] - miny) / (maxy - miny) * (H - pad * 2);
        s.push("<g class='map-dot' data-place='" + esc(p.n) + "'><circle cx='" + x.toFixed(1) + "' cy='" + y.toFixed(1) +
          "' r='7' fill='var(--accent)' opacity='0.85' stroke='var(--panel)' stroke-width='1.5'><title>" +
          esc(p.n) + "（" + esc(p.mo || "") + "）</title></circle>" +
          "<text x='" + (x + 10).toFixed(1) + "' y='" + (y + 4).toFixed(1) + "' font-size='11' fill='var(--ink-2)'>" +
          esc(p.n) + "</text></g>");
      });
      s.push("<text x='" + pad + "' y='" + (H - 12) + "' font-size='10' fill='var(--ink-3)'>离线投影 · 共 " + list.length + " 个已定位地点</text>");
    }
    s.push("</svg>");
    canvas.innerHTML = s.join("");
    Array.prototype.forEach.call(canvas.querySelectorAll("[data-place]"), function (g) {
      g.onclick = function () { showPlace(g.dataset.place); };
    });
  }

  /* ---------- 事件 ---------- */
  var evQuery = "", evType = "", evPage = 0, PAGE = 50;
  // 事件分类用「叙事功能基类」(tb)，不用原始自由文本 (ty)：
  // ty 有 47 种且「其他」占 43%，按它做筛选条等于给人看噪声。
  // ty 仍然保留，进事件详情时作为「抽取原文」展示，可回溯。
  function evCat(e) { return e.tb || e.ty || "其他"; }
  function renderEvents() {
    var q = evQuery.toLowerCase();
    var list = events.filter(function (e) {
      if (evType && evCat(e) !== evType) return false;
      if (!q) return true;
      return (e.n + " " + e.ty + " " + evCat(e) + " " + (e.p || []).join(" ") + " " + (e.loc || "") + " " + (e.no || "") + " " + (e.st || ""))
        .toLowerCase().indexOf(q) >= 0;
    });
    var types = {};
    events.forEach(function (e) { var k = evCat(e); types[k] = (types[k] || 0) + 1; });
    var chips = Object.keys(types).sort(function (a, b) { return types[b] - types[a]; }).map(function (t) {
      return "<span class='chip" + (evType === t ? " on" : "") + "' data-type='" + esc(t) + "'>" + esc(t) + " " + types[t] + "</span>";
    }).join("");
    var pages = Math.max(1, Math.ceil(list.length / PAGE));
    evPage = Math.min(evPage, pages - 1);
    var html = ["<div class='panel'><div class='search-row'>" +
      "<div class='search-box'><span>🔍</span><input id='event-search' type='text' placeholder='搜索事件 / 参与者 / 地点（共 " +
      events.length + " 件）' value='" + esc(evQuery) + "'></div></div>" +
      "<div class='filter-chips'><span class='chip" + (evType ? "" : " on") + "' data-type=''>全部</span>" + chips + "</div>" +
      // 「阶段」列取代了原「年份」列：两书 year 字段 100% 为空（833/833、2591/2591），
      // 整列「待考」零信息（ui_audit §3-4）。阶段键由构建期按 first_no 口径算好
      // （src/generate_report.py → core.phases.stage_of），与阶段轴同一把尺子；
      // 同名多段因此带「（起–止）」区间，不会一段链代表多段。
      "<div class='table-wrap' style='margin-top:10px'><table class='data'><thead><tr><th>事件</th><th>功能类别</th><th>参与者</th><th>地点</th><th>阶段</th><th>章节</th></tr></thead><tbody>"];
    list.slice(evPage * PAGE, evPage * PAGE + PAGE).forEach(function (e) {
      // 单元格展示基类，鼠标悬停可看抽取时的原始类型（证据）
      html.push("<tr data-event='" + esc(e.i) + "'><td>" + hl(e.n, evQuery) +
        "</td><td class='small' title='抽取原文类型：" + esc(e.ty || "空") + "'>" + esc(evCat(e)) +
        "</td><td class='small'>" + esc((e.p || []).slice(0, 4).join("、")) + ((e.p || []).length > 4 ? " 等" : "") +
        "</td><td class='small'>" + esc(e.loc || "—") + "</td><td class='small' title='按事件首章所属阶段（first_no 口径）'>" + esc(e.st || "—") +
        "</td><td class='num small'>" + (e.c || []).map(function (i) {
          // data-ch 存内部索引（gotoChapter 按索引找章节），但**显示**必须是书中真实
          // 章号——天才基本法索引 112 之后 n = i - 3，直接显示索引会让读者对不上书。
          var n = idx2no[i];
          return "<span class='chip-link' data-ch='" + i + "' title='第" + (n == null ? i : n) +
            " 章'>" + (n == null ? i : n) + "</span>";
        }).join(" ") + "</td></tr>");
    });
    html.push("</tbody></table></div><div class='pager'>" +
      "<button id='ev-prev'" + (evPage === 0 ? " disabled" : "") + ">上一页</button>" +
      "<span>第 " + (evPage + 1) + " / " + pages + " 页 · 共 " + list.length + " 件</span>" +
      "<button id='ev-next'" + (evPage >= pages - 1 ? " disabled" : "") + ">下一页</button></div></div>");
    $("view-events").innerHTML = html.join("");
    bindSearch($("event-search"), function (v) { evQuery = v; evPage = 0; renderEvents(); syncHash(); });
    Array.prototype.forEach.call($("view-events").querySelectorAll(".chip[data-type]"), function (c) {
      c.onclick = function () { evType = c.dataset.type; evPage = 0; renderEvents(); };
    });
    $("ev-prev").onclick = function () { evPage--; renderEvents(); };
    $("ev-next").onclick = function () { evPage++; renderEvents(); };
    Array.prototype.forEach.call($("view-events").querySelectorAll("[data-event]"), function (tr) {
      tr.onclick = function (e) {
        if (e.target.dataset && e.target.dataset.ch) { gotoChapter(+e.target.dataset.ch); return; }
        showEvent(tr.dataset.event);
      };
    });
  }

  /* ---------- 关系 ---------- */
  var graphMode = "person"; // person | entity
  function renderRelations() {
    var html = ["<div class='panel'><h3>关系网络</h3>" +
      "<div class='filter-chips'><span class='chip" + (graphMode === "person" ? " on" : "") + "' data-mode='person'>人物关系图</span>" +
      "<span class='chip" + (graphMode === "entity" ? " on" : "") + "' data-mode='entity'>全书实体图</span></div>" +
      "<div class='tier-row'><span class='muted small'>节点范围</span>" +
      "<button class='chip tier-btn " + (graphScope === "core" ? " on" : "") + "' data-scope='core'>核心人物</button>" +
      "<button class='chip tier-btn " + (graphScope === "core_major" ? " on" : "") + "' data-scope='core_major'>核心+主要</button>" +
      "<button class='chip tier-btn " + (graphScope === "all" ? " on" : "") + "' data-scope='all'>全部</button>" +
      "</div>" +
      "<div class='rel-legend' id='rel-legend'></div>" +
      "<div class='graph-wrap' id='graph-wrap'></div>" +
      "<div class='small muted'>边按关系基类着色（原始描述见悬停提示）。共 " +
      relations.length + " 条关系，归约为 " + relBaseCount() + " 个基类。</div></div>"];
    $("view-relations").innerHTML = html.join("");
    Array.prototype.forEach.call($("view-relations").querySelectorAll(".chip[data-mode]"), function (c) {
      c.onclick = function () { graphMode = c.dataset.mode; renderRelations(); };
    });
    Array.prototype.forEach.call($("view-relations").querySelectorAll(".chip[data-scope]"), function (c) {
      c.onclick = function () { graphScope = c.dataset.scope; renderRelations(); };
    });
    drawGraph();
  }
  function relBaseCount() {
    var s = {};
    relations.forEach(function (r) { if (r.rb) s[r.rb] = true; });
    return Object.keys(s).length;
  }
  function drawGraph() {
    var wrap = $("graph-wrap");
    if (!wrap) return;
    var rs = relations;
    if (graphMode === "person") {
      rs = rs.filter(function (r) {
        return r.fk === "person" && r.tk === "person" && scopeAllows(r.f) && scopeAllows(r.t);
      });
    }
    var nodes = {}, links = [], pairMap = {};
    rs.forEach(function (r) {
      if (!nodes[r.f]) nodes[r.f] = { name: r.f, kind: r.fk, deg: 0 };
      if (!nodes[r.t]) nodes[r.t] = { name: r.t, kind: r.tk, deg: 0 };
      // 同一对人的多条关系描述合并成一条边：31 个核心人物原本会画出 1000+ 条边，
      // 但绝大多数是同一对人之间的不同措辞，视觉上全是噪声。
      var pk = r.f + "|" + r.t;
      var pr = pairMap[pk];
      if (!pr) {
        pr = pairMap[pk] = { s: r.f, t: r.t, bases: {}, notes: [] };
        links.push(pr);
        nodes[r.f].deg++; nodes[r.t].deg++;
      }
      pr.bases[r.rb || "其他关系"] = (pr.bases[r.rb || "其他关系"] || 0) + 1;
      if (r.rn && pr.notes.indexOf(r.rn) < 0 && pr.notes.length < 6) pr.notes.push(r.rn);
    });
    // 一对多关系时用「最有信息量」的基类作为边的颜色
    var BASE_PRIORITY = ["亲属", "爱慕", "敌对", "师徒", "上下级", "队友", "合作",
      "同源", "寄生", "融合", "支配", "交易", "救助", "朋友", "同事", "旧识", "其他关系"];
    links.forEach(function (l) {
      l.rb = BASE_PRIORITY.filter(function (b) { return l.bases[b]; })[0] || "其他关系";
      l.rbAll = Object.keys(l.bases);
    });
    var arr = Object.keys(nodes).map(function (k) { return nodes[k]; });
    if (!arr.length) {
      wrap.innerHTML = "<div class='muted'>当前范围下没有可画的关系。可切到「核心+主要」或「全部」。</div>";
      var lg0 = $("rel-legend"); if (lg0) lg0.innerHTML = "";
      return;
    }
    // 节点上限：人眼一次能读的边就这么多，超了就糊
    arr.sort(function (a, b) { return b.deg - a.deg; });
    var keep = arr.slice(0, graphMode === "person" ? 60 : 90);
    var keepSet = {};
    keep.forEach(function (n) { keepSet[n.name] = true; });
    links = links.filter(function (l) { return keepSet[l.s] && keepSet[l.t]; });
    simulate(keep, links, 760, 560);
    fitGraph(keep, 760, 560, 56);
    var nidx = {};
    keep.forEach(function (n) { nidx[n.name] = n; });
    var s = ["<svg viewBox='0 0 760 560'>"];
    links.forEach(function (l) {
      var sn = nidx[l.s], tn = nidx[l.t];
      if (!sn || !tn) return;
      var col = REL_COLOR[l.rb] || "var(--ink-3)";
      var tip = l.s + " —" + l.rbAll.join("/") + "→ " + l.t +
        (l.notes && l.notes.length ? "：" + l.notes.join("；") : "");
      s.push("<line class='graph-link' x1='" + sn.x.toFixed(1) + "' y1='" + sn.y.toFixed(1) +
        "' x2='" + tn.x.toFixed(1) + "' y2='" + tn.y.toFixed(1) + "' stroke='" + col +
        "' stroke-opacity='0.42'><title>" + esc(tip) + "</title></line>");
    });
    keep.forEach(function (n) {
      var pobj = personByName[n.name];
      // 人物按主阵营着色，图才有语义（否则所有点一个颜色，只剩拓扑）
      var c = pobj ? factionColor(pobj.fm) : (KIND_COLOR[n.kind] || "var(--ink-3)");
      var r = Math.min(9, 3 + Math.sqrt(n.deg) * 1.6);
      var tip2 = n.name + "（" + (KIND_LABEL[n.kind] || n.kind) +
        (pobj && pobj.fm ? " · " + pobj.fm : "") + "，关系 " + n.deg + " 条）";
      s.push("<g class='graph-node' data-node='" + esc(n.name) + "' transform='translate(" + n.x.toFixed(1) + "," + n.y.toFixed(1) + ")'>" +
        "<circle r='" + r.toFixed(1) + "' fill='" + c + "' opacity='0.9'><title>" + esc(tip2) + "</title></circle>" +
        "<text y='" + (r + 11).toFixed(1) + "' text-anchor='middle'>" + esc(n.name.length > 8 ? n.name.slice(0, 8) + "…" : n.name) +
        "</text></g>");
    });
    s.push("</svg>");
    wrap.innerHTML = s.join("");
    var legend = $("rel-legend");
    var bases = {};
    links.forEach(function (l) {
      Object.keys(l.bases).forEach(function (b) { bases[b] = (bases[b] || 0) + 1; });
    });
    legend.innerHTML = Object.keys(bases).sort(function (a, b) {
      // 兜底类垫底：它是归约失败，不该排在队友/上下级前面
      var ra = a === "其他关系" ? 1 : 0, rb2 = b === "其他关系" ? 1 : 0;
      if (ra !== rb2) return ra - rb2;
      return bases[b] - bases[a];
    })
      .map(function (k) {
        return "<span><i style='background:" + (REL_COLOR[k] || "var(--ink-3)") + "'></i>" + esc(k) +
          " " + bases[k] + "</span>";
      }).join("") + "<span class='muted'>（显示 " + keep.length + " 个节点 / " + links.length +
      " 条关系对，同一对人的多种关系已合并）</span>";
    Array.prototype.forEach.call(wrap.querySelectorAll("[data-node]"), function (g) {
      g.onclick = function () {
        var n = g.dataset.node;
        if (personById["person:" + n]) showPerson(n); else showPlace(n);
      };
    });
  }
  // 力导向收敛后节点常挤在画布一角（节点少时尤其明显）。
  // 这里按内容外框等比缩放并居中，让图填满画布——比反复调斥力参数稳。
  function fitGraph(nodes, w, h, pad) {
    if (nodes.length < 2) return;
    var i, xs = [], ys = [];
    for (i = 0; i < nodes.length; i++) { xs.push(nodes[i].x); ys.push(nodes[i].y); }
    var minx = Math.min.apply(null, xs), maxx = Math.max.apply(null, xs);
    var miny = Math.min.apply(null, ys), maxy = Math.max.apply(null, ys);
    var dw = Math.max(1, maxx - minx), dh = Math.max(1, maxy - miny);
    var cx = (minx + maxx) / 2, cy = (miny + maxy) / 2;
    var s = Math.min((w - pad * 2) / dw, (h - pad * 2) / dh);
    s = Math.max(0.6, Math.min(s, 3.2));   // 别过度放大，避免节点散得失真
    for (i = 0; i < nodes.length; i++) {
      nodes[i].x = w / 2 + (nodes[i].x - cx) * s;
      nodes[i].y = h / 2 + (nodes[i].y - cy) * s;
    }
  }
  function simulate(nodes, links, w, h) {    var W = w, H = h;
    nodes.forEach(function (n, i) {
      var a = i * 2.399963;
      var rad = 40 + 200 * Math.sqrt((i + 0.5) / nodes.length);
      n.x = W / 2 + rad * Math.cos(a); n.y = H / 2 + rad * Math.sin(a) * 0.7;
      n.vx = 0; n.vy = 0;
    });
    var idx = {};
    nodes.forEach(function (n) { idx[n.name] = n; });
    for (var it = 0; it < 260; it++) {
      var k = 1 - it / 260;
      for (var i = 0; i < nodes.length; i++) {
        var a = nodes[i];
        for (var j = i + 1; j < nodes.length; j++) {
          var b = nodes[j], dx = b.x - a.x, dy = b.y - a.y;
          var d2 = dx * dx + dy * dy || 1, d = Math.sqrt(d2);
          var f = Math.min(60, 900 / d2);
          var fx = dx / d * f, fy = dy / d * f;
          a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy;
        }
        a.vx += (W / 2 - a.x) * 0.0016; a.vy += (H / 2 - a.y) * 0.0016;
      }
      links.forEach(function (l) {
        var s = idx[l.s], t = idx[l.t];
        var dx = t.x - s.x, dy = t.y - s.y, d = Math.sqrt(dx * dx + dy * dy) || 1;
        var f = (d - 62) * 0.012;
        var fx = dx / d * f, fy = dy / d * f;
        s.vx += fx; s.vy += fy; t.vx -= fx; t.vy -= fy;
      });
      nodes.forEach(function (n) {
        n.vx *= 0.82; n.vy *= 0.82;
        n.x += n.vx * k; n.y += n.vy * k;
        n.x = Math.max(30, Math.min(W - 30, n.x));
        n.y = Math.max(24, Math.min(H - 24, n.y));
      });
    }
  }

  /* ---------- 阶段轴 ---------- */
  var curPhase = 0;
  function renderPhases() {
    var html = ["<div class='panel'><h3>阶段轴<span class='hint'>本书无公元纪年，按章节推进划分阶段；点击切换</span></h3>"];
    html.push("<div class='phase-bar'>");
    phases.forEach(function (ph, i) {
      html.push("<div class='phase-seg" + (i === curPhase ? " on" : "") + "' data-ph='" + i + "' title='第" +
        ph.s + "—" + ph.e + "章'>" + esc(ph.name) + "</div>");
    });
    html.push("</div><div class='phase-body' id='phase-body'></div></div>");
    $("view-phases").innerHTML = html.join("");
    Array.prototype.forEach.call($("view-phases").querySelectorAll("[data-ph]"), function (seg) {
      seg.onclick = function () { curPhase = +seg.dataset.ph; renderPhases(); syncHash(); };
    });
    renderPhaseBody();
  }
  function renderPhaseBody() {
    var ph = phases[curPhase];
    if (!ph) return;
    // 事件的 chapters 存的是内部索引 i，而阶段边界 ph.s/ph.e 已经换成书中真实章号 n
    // （generate_report.py 里过了一道 idx2no）。两边必须同口径再比，否则天才基本法
    // 索引 112 之后的阶段会把事件算到相邻阶段去。
    var inPhase = function (list) {
      return (list || []).filter(function (i) {
        var n = idx2no[i];
        return n != null && n >= ph.s && n <= ph.e;
      }).length;
    };
    var phPersons = persons.map(function (p) {
      return { p: p, n: inPhase(p.c) };
    }).filter(function (x) { return x.n > 0; }).sort(function (a, b) { return b.n - a.n; }).slice(0, 10);
    var phEvents = events.filter(function (e) { return inPhase(e.c) > 0; })
      .sort(function (a, b) { return inPhase(b.c) - inPhase(a.c) || a.n.localeCompare(b.n); }).slice(0, 40);
    var phPlaces = places.filter(function (p) { return inPhase(p.c) > 0; }).slice(0, 20);
    // 「共 N 章」不能直接用 ph.e - ph.s + 1：章号有断档（天才基本法索引 112 之后
    // n = i - 3，中间还有 15 个章号没有以它为首章的事件），按区间减会多数出几章。
    // 老老实实数一遍落在区间内的章节。
    var phChCount = chapters.filter(function (c) {
      var n = (c.n || c.i);
      return n >= ph.s && n <= ph.e;
    }).length;
    var html = [];
    html.push("<div class='small muted'>第 <b>" + ph.s + "</b> — <b>" + ph.e + "</b> 章 · 共 " +
      phChCount + " 章</div>");
    html.push("<div class='grid-2' style='margin-top:10px'>");
    html.push("<div><h3 style='font-size:14px'>本阶段主要人物</h3><div class='table-wrap'><table class='data'><tbody>");
    phPersons.forEach(function (x) {
      html.push("<tr data-person='" + esc(x.p.n) + "'><td>" + esc(x.p.n) + "</td><td class='small muted'>" +
        esc((x.p.f || [])[0] || "") + "</td><td class='num'>" + x.n + " 章</td></tr>");
    });
    html.push("</tbody></table></div>");
    html.push("<h3 style='font-size:14px;margin-top:12px'>本阶段地点</h3><div class='small'>" +
      phPlaces.map(function (p) {
        return "<span class='chip-link' data-place='" + esc(p.n) + "'>" + esc(p.n) + "</span>";
      }).join(" ") + "</div></div>");
    html.push("<div><h3 style='font-size:14px'>本阶段事件（按出场章数）</h3><div class='table-wrap'><table class='data'><tbody>");
    phEvents.forEach(function (e) {
      html.push("<tr data-event='" + esc(e.i) + "'><td>" + esc(e.n) + "</td><td class='small muted'>" +
        esc(e.ty || "") + "</td><td class='num small'>" + inPhase(e.c) + " 章</td></tr>");
    });
    html.push("</tbody></table></div></div></div>");
    $("phase-body").innerHTML = html.join("");
    Array.prototype.forEach.call($("phase-body").querySelectorAll("[data-person]"), function (tr) {
      tr.onclick = function () { showPerson(tr.dataset.person); };
    });
    Array.prototype.forEach.call($("phase-body").querySelectorAll("[data-place]"), function (sp) {
      sp.onclick = function () { showPlace(sp.dataset.place); };
    });
    Array.prototype.forEach.call($("phase-body").querySelectorAll("[data-event]"), function (tr) {
      tr.onclick = function () { showEvent(tr.dataset.event); };
    });
  }

  /* ---------- 详情弹窗 ---------- */
  function openDialog(html) {
    var bd = $("dialog-backdrop"), d = $("dialog");
    d.innerHTML = "<button class='close-x' id='dlg-close'>×</button>" + html;
    bd.hidden = false;
    $("dlg-close").onclick = closeDialog;
  }
  function closeDialog() {
    $("dialog-backdrop").hidden = true;
    lastEntity = null;
    syncHash();
  }
  $("dialog-backdrop").addEventListener("click", function (e) {
    if (e.target === this) closeDialog();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDialog();
  });
  function showPerson(name) {
    var p = personById["person:" + name];
    if (!p) { toast("未找到人物：" + name); return; }
    lastEntity = { kind: "person", v: name };
    var rels = relByPerson[name] || [];
    var evs = eventsByPerson[name] || [];
    var placesOf = [];
    evs.forEach(function (e) { if (e.loc) placesOf.push(e.loc); });
    // 同一地点在多个事件里出现会重复计数，去重后按出现次数排序
    var plCount = {};
    placesOf.forEach(function (n) { plCount[n] = (plCount[n] || 0) + 1; });
    placesOf = Object.keys(plCount).sort(function (a, b) { return plCount[b] - plCount[a]; });
    // 泛称判断：名字是职业/身份称谓而非人名（技术员、护士…）。
    // 注意「泛称」不等于「噪声」——技术员出场 12 章有完整 role，是固定角色；
    // 只有单章泛称才是背景板。所以这里只做标注，不做删除。
    var isGeneric = GENERIC_NAMES.indexOf(name) >= 0;
    var html = ["<h2>" + esc(p.n) + "</h2>" +
      "<div><span class='badge src'>书中抽取</span>" +
      (isGeneric ? "<span class='badge pending'>未具名（职业/身份称谓）</span>" : "") +
      // 阵营只显示主阵营 +N。曾有人在详情里被铺了 51 个阵营串，
      // 那些多为同一阵营的层级路径变体；全列 = 噪声。原文放 title 可查。
      (p.fm || p.f && p.f[0]
        ? "<span class='badge' title='" + esc((p.f || []).join(" / ")) + "'>" +
          esc(p.fm || p.f[0]) + ((p.f || []).length > 1 ? " +" + ((p.f || []).length - 1) : "") + "</span>"
        : "") + "</div>"];
    html.push("<dl class='kv-grid'>");
    if (p.a && p.a.length) {
      // 别名多的时候（祝宁有 60 个：代号、昵称、冒名…）一口气铺满整屏。
      // 折叠显示前 8 个，其余点「展开」再看，和列表视图的取舍逻辑一致。
      var as = p.a, shown = as.slice(0, 8).map(esc).join("、");
      html.push("<dt>别名<span class='hint'>共 " + as.length + " 个</span></dt><dd>" + shown +
        (as.length > 8
          ? " <span class='chip-link' data-alias-toggle='" + esc(name) + "'>展开全部 " + as.length + " 个</span>" +
            "<span class='muted small' data-alias-full hidden>　" + esc(as.join("、")) + "</span>"
          : "") + "</dd>");
    }
    // A5：role 是自由文本裸串，构建期用词表解析成 身份 / 关系 / 在场 三类标签
    // （src/role_parse.py，宁可留空不可猜错）。标签只是索引，原串永远保留可回查——
    // 解析错了读者一眼能看出「标签 ≠ 原文」，不会以为数据被改过。
    var rl = p.rl || {}, tags = [];
    if (rl.id) tags.push("<span class='badge' title='身份（词表匹配）'>" + esc(rl.id) + "</span>");
    if (rl.rel) tags.push("<span class='badge' title='关系（原文模式匹配）'>" + esc(rl.rel.to + "的" + rl.rel.k) + "</span>");
    if (rl.st) tags.push("<span class='badge pending' title='在场状态（仅单章角色才判定）'>" + esc(rl.st) + "</span>");
    html.push("<dt>身份</dt><dd>" + (tags.length
      ? tags.join("") + "<div class='muted small' style='margin-top:4px'>原文：" + esc(p.r) + "</div>"
      : esc(p.r || "未标注")) + "</dd>");
    html.push("<dt>出场</dt><dd>" + p.c.length + " 章 · 提及 " + p.m + " 次</dd>");
    // A4：详情里给最多 3 句本人对白（含章号可点）。归属依据 h 作悬停证据，
    // 让读者能判断「这句为什么算他说的」。
    var qs = (quoteByPerson[name] || []).slice(0, 3);
    if (qs.length) {
      html.push("<dt>语录<span class='hint'>共 " + quoteByPerson[name].length + " 句</span></dt><dd>" +
        qs.map(function (q) {
          return "<div class='q-item q-inline'><div class='q-text'>" + esc(q.t) + "</div>" +
            "<div class='q-meta'><span class='chip-link' data-ch='" + (idxByNo[q.ch] || q.ch) +
            "'>第" + q.ch + "章</span>" +
            (q.h ? " <span class='muted' title='归属依据'>· " + esc(q.h) + "</span>" : "") +
            "</div></div>";
        }).join("") + "</dd>");
    }
    // 孤岛人物不空着：31%（废土）/59%（天才）的人物没有任何关系，
    // 空白会被读成「加载失败」，说清楚是「没抽到」才诚实。
    if (rels.length) {
      // 按「对方」聚合：抽取时同一对的关系被拆成多条（付医生与祝宁就有
      // 救助/队友/师徒 6 条），逐条铺开就是重复噪声，整个弹窗没法读。
      var byWho = {}, order = [];
      rels.forEach(function (r) {
        var other = r.f === name ? r.t : r.f;
        if (!byWho[other]) { byWho[other] = []; order.push(other); }
        var b = r.rb || r.r || "其他关系";
        if (byWho[other].indexOf(b) < 0) byWho[other].push(b);
      });
      // 「其他关系」是归约失败的产物，只要有具名关系就往后排（跟图例同一纪律）
      order.forEach(function (o) {
        byWho[o].sort(function (a, b) {
          var ra = a === "其他关系" ? 1 : 0, rb = b === "其他关系" ? 1 : 0;
          return ra - rb;
        });
      });
      order.sort(function (a, b) { return byWho[b].length - byWho[a].length; });
      html.push("<dt>关系<span class='hint'>按对象合并，" + rels.length + " 条归 " +
        order.length + " 人</span></dt><dd>" + order.slice(0, 14).map(function (o) {
          return "<span class='chip-link' data-person='" + esc(o) + "'>" + esc(o) +
            "（" + esc(byWho[o].join("、")) + "）</span>";
        }).join("、") + (order.length > 14 ? " 等 " + order.length + " 人" : "") + "</dd>");
    } else {
      html.push("<dt>关系</dt><dd class='muted small'>无已知关系（本书未抽取到该角色与其他角色的关系）</dd>");
    }
    html.push("<dt>参与事件</dt><dd>" + (evs.length ? evs.slice(0, 12).map(function (e) {
      return "<span class='chip-link' data-event='" + esc(e.i) + "'>" + esc(e.n) + "</span>";
    }).join("、") + (evs.length > 12 ? " 等 " + evs.length + " 件" : "") : "无记录") + "</dd>");
    if (placesOf.length) html.push("<dt>相关地点</dt><dd>" +
      placesOf.slice(0, 8).map(function (n) {
        return "<span class='chip-link' data-place='" + esc(n) + "'>" + esc(n) +
          (plCount[n] > 1 ? " ×" + plCount[n] : "") + "</span>";
      }).join("、") + (placesOf.length > 8 ? " 等 " + placesOf.length + " 处" : "") + "</dd>");
    html.push("</dl>");
    if (rels.length) {
      html.push("<h3 style='font-size:14px'>关系（" + rels.length + " 条）</h3><div class='table-wrap'><table class='data'><tbody>");
      rels.slice(0, 30).forEach(function (r) {
        var other = r.f === name ? r.t : r.f;
        var dir = r.f === name ? "→ " : "← ";
        html.push("<tr><td class='small'>" + dir + esc(r.rel) + "</td><td>" +
          (personById["person:" + other]
            ? "<span class='chip-link' data-person='" + esc(other) + "'>" + esc(other) + "</span>"
            : "<span class='badge kind-" + (r.f === name ? r.tk : r.fk) + "'>" + (KIND_LABEL[r.f === name ? r.tk : r.fk] || "实体") + "</span> " + esc(other)) +
          "</td><td class='small muted'>" + r.c.length + " 章</td></tr>");
      });
      html.push("</tbody></table></div>");
    }
    html.push("<h3 style='font-size:14px;margin-top:12px'>出场章节</h3><div class='small'>" + chapterLinks(p.c) + "</div>");
    html.push(insightBlock("p", name));
    openDialog(html.join(""));
    bindDialogLinks();
    syncHash();   // 弹窗打开即回写地址栏（detail=1/place=/event=），复制 URL 可直接复现
  }
  function showPlace(name) {
    var p = placeById["place:" + name];
    if (!p) { toast("未找到地点：" + name); return; }
    lastEntity = { kind: "place", v: name };
    var evs = events.filter(function (e) { return e.loc === name; });
    var personsHere = {};
    evs.forEach(function (e) { (e.p || []).forEach(function (n) { personsHere[n] = 1; }); });
    var html = ["<h2>" + esc(p.n) + "</h2><div>" +
      "<span class='badge " + p.g + "'>" + (GEO_LABEL[p.g] || p.g) + "</span>" +
      (p.t ? "<span class='badge'>" + esc(p.t) + "</span>" : "") +
      "<span class='badge src'>书中抽取</span></div>"];
    html.push("<dl class='kv-grid'>");
    html.push("<dt>今址/对应</dt><dd>" + esc(p.mo || "—（虚构或未考）") + "</dd>");
    html.push("<dt>所在分区</dt><dd>" + esc(placeZone(p)) + "</dd>");
    if (p.rg) html.push("<dt>区域原文</dt><dd class='small muted'>" + esc(p.rg) + "</dd>");
    html.push("<dt>坐标</dt><dd>" + (p.co ? esc(p.co.join(", ")) + " <span class='small muted'>" + esc(p.src || "") + "</span>" : "未定位（待核验）") + "</dd>");
    html.push("<dt>出场</dt><dd>" + p.c.length + " 章 · 提及 " + p.m + " 次</dd>");
    var ps = Object.keys(personsHere);
    if (ps.length) html.push("<dt>相关人物</dt><dd>" + ps.slice(0, 12).map(function (n) {
      return "<span class='chip-link' data-person='" + esc(n) + "'>" + esc(n) + "</span>";
    }).join("、") + "</dd>");
    html.push("</dl>");
    if (evs.length) {
      html.push("<h3 style='font-size:14px'>相关事件（" + evs.length + "）</h3><div class='table-wrap'><table class='data'><tbody>");
      evs.slice(0, 30).forEach(function (e) {
        html.push("<tr data-event='" + esc(e.i) + "'><td>" + esc(e.n) + "</td><td class='small muted'>" + esc(e.ty || "") + "</td></tr>");
      });
      html.push("</tbody></table></div>");
    }
    html.push("<h3 style='font-size:14px;margin-top:12px'>出场章节</h3><div class='small'>" + chapterLinks(p.c) + "</div>");
    html.push(insightBlock("l", name));
    openDialog(html.join(""));
    bindDialogLinks();
    syncHash();   // 弹窗打开即回写地址栏（detail=1/place=/event=），复制 URL 可直接复现
  }
  function showEvent(id) {
    var e = eventById[id];
    if (!e) { toast("未找到事件"); return; }
    lastEntity = { kind: "event", v: id };
    var html = ["<h2>" + esc(e.n) + "</h2><div>" +
      (evCat(e) && evCat(e) !== "其他" ? "<span class='badge'>" + esc(evCat(e)) + "</span>" : "") +
      // 原文类型作为证据保留，与基类并列显示，方便核对我是否归错
      (e.ty && e.ty !== evCat(e) ? "<span class='badge src'>抽取原文：" + esc(e.ty) + "</span>" : "") +
      "<span class='badge src'>书中抽取</span>" +
      (e.yr ? "" : "<span class='badge pending'>年份待考</span>") + "</div>"];
    html.push("<dl class='kv-grid'>");
    html.push("<dt>时间线索</dt><dd>" + esc(e.th || "—") + "</dd>");
    html.push("<dt>年份</dt><dd>" + esc(e.yr || "未知（书中未给）") + "</dd>");
    html.push("<dt>地点</dt><dd>" + (e.loc ? "<span class='chip-link' data-place='" + esc(e.loc) + "'>" + esc(e.loc) + "</span>" : "—") + "</dd>");
    html.push("<dt>参与者</dt><dd>" + ((e.p || []).length ? (e.p || []).map(function (n) {
      return "<span class='chip-link' data-person='" + esc(n) + "'>" + esc(n) + "</span>";
    }).join("、") : "—") + "</dd>");
    if (e.no) html.push("<dt>说明</dt><dd>" + esc(e.no) + "</dd>");
    html.push("</dl>");
    html.push("<h3 style='font-size:14px'>出场章节</h3><div class='small'>" + chapterLinks(e.c) + "</div>");
    html.push(insightBlock("e", id));
    openDialog(html.join(""));
    bindDialogLinks();
    syncHash();   // 弹窗打开即回写地址栏（detail=1/place=/event=），复制 URL 可直接复现
  }
  function bindDialogLinks() {
    Array.prototype.forEach.call($("dialog").querySelectorAll("[data-person]"), function (s) {
      s.onclick = function () { showPerson(s.dataset.person); };
    });
    Array.prototype.forEach.call($("dialog").querySelectorAll("[data-place]"), function (s) {
      s.onclick = function () { showPlace(s.dataset.place); };
    });
    Array.prototype.forEach.call($("dialog").querySelectorAll("[data-event]"), function (s) {
      s.onclick = function () { showEvent(s.dataset.event); };
    });
    Array.prototype.forEach.call($("dialog").querySelectorAll("[data-ch]"), function (s) {
      s.onclick = function () { closeDialog(); gotoChapter(+s.dataset.ch); };
    });
    // 「相关分析」反向入口：跳到学科视角里命中该实体的小节
    Array.prototype.forEach.call($("dialog").querySelectorAll(".ins-chip"), function (s) {
      s.onclick = function () { gotoInsight(s.dataset.ins); };
    });
    // 别名折叠：点「展开全部」就地展开，不重开弹窗（避免刷掉当前阅读位置）
    Array.prototype.forEach.call($("dialog").querySelectorAll("[data-alias-toggle]"), function (s) {
      s.onclick = function () {
        s.hidden = true;
        var full = $("dialog").querySelector("[data-alias-full]");
        if (full) full.hidden = false;
      };
    });
  }

  /* ---------- 金句 ---------- */
  // 这一页的设计纪律有三条，都写在代码里免得后人改坏：
  //  ① 叙述句与人物对白**分栏**存放。旁白不是任何角色说的话，挂到人名下就是造假。
  //  ② 说话人不确定的对白单列一栏，不塞进「未归属」这种含糊说法里 ——
  //     读者需要知道「有多少条我们其实不知道是谁说的」。
  //  ③ 先交代口径再给句子。没有口径的金句榜和摘抄本没区别。
  var quoteScope = "major";   // core | major | all
  function quoteItem(q) {
    // 三类要分清楚，不能都写成「—」：
    //   对白+有说话人 → 人名；对白+无说话人 → 「说话人未确定」；叙述/独白 → 叙述
    var who = q.s
      ? "<span class='who' data-person='" + esc(q.s) + "'>" + esc(q.s) + "</span>"
      : "<span class='muted'>" + (q.k === "n" ? esc(q.h || "叙述") : "说话人未确定") + "</span>";
    // q.ch 是书中章号（不是内部索引，见 idxByNo 处的说明）：标签直接用，
    // 点击要换成索引再交给 gotoChapter——否则天才 112 章之后会打开错章。
    var ch = q.ch
      ? " · <span class='chip-link' data-ch='" + (idxByNo[q.ch] || q.ch) + "'>第" + q.ch + "章" +
        (q.ct ? " " + esc(q.ct) : "") + "</span>"
      : "";
    var basis = (q.s && q.h)
      ? " <span class='muted' title='归属依据：这句话为什么算他说的'>· " + esc(q.h) + "</span>"
      : "";
    return "<div class='q-item" + (q.k === "n" ? " q-narr" : "") + "'>" +
      "<div class='q-text'>" + esc(q.t) + "</div>" +
      "<div class='q-meta'>" + who + basis + ch + "</div></div>";
  }
  function renderQuotes() {
    var Q = DATA.quotes || {};
    var meta = Q.meta || {};
    var dlg = Q.quotes || [], nar = Q.narration || [], top = Q.top || [];
    var box = $("view-quotes"), html = [];
    if (!dlg.length && !nar.length) {
      box.innerHTML = "<div class='panel'><h3>金句</h3><p class='small muted'>" +
        "本书尚无金句数据 —— 需先运行 src/extract_quotes.py。</p></div>";
      return;
    }
    var picked = meta.picked || 0, narrPicked = meta.narr_picked || 0;
    var attr = meta.attributed || 0, how = meta.how_counts || {};

    // ① 口径：先说清这批句子是怎么选出来的
    html.push("<div class='panel'><h3>这些句子是怎么选出来的<span class='hint'>口径与局限</span></h3>");
    html.push("<div class='findings'><div class='finding'><div class='claim'>从全书 " +
      meta.dialogue_lines + " 句对白与 " + meta.narr_candidates + " 句叙述中，按" +
      "「能否脱离语境单独成立」筛出 " + (picked + narrPicked) + " 条（对白 " +
      picked + " · 叙述 " + narrPicked + "）。</div><div class='ev'>证据：门槛 = 谈" +
      "「人生／世界／命运／选择」这类大词，或长成「不是A而是B」「只有A才B」的格言句式；" +
      "再扣掉靠「这／那／他」才读得懂的句子、以及嵌着具体人名地名的句子 —— " +
      "它们离不开情节现场，单拿出来不成立。</div></div></div>");
    html.push("<div class='table-wrap' style='margin-top:12px'><table class='data'><tbody>");
    var rows = [
      ["对白候选 → 精选", meta.candidates + " → " + picked],
      ["叙述候选 → 精选", meta.narr_candidates + " → " + narrPicked],
      ["每人收录上限", meta.per_person_cap + " 条（避免主角独占版面）"],
      ["说话人已归属", attr + " / " + picked + " 条（" +
        (picked ? Math.round(attr / picked * 100) : 0) + "%）"],
      ["对白重复率", (meta.repeated_share * 100).toFixed(1) + "%（回响信号" +
        (meta.echo_signal ? "开" : "关") + "）"]
    ];
    rows.forEach(function (r) {
      html.push("<tr><td>" + r[0] + "</td><td class='num'>" + r[1] + "</td></tr>");
    });
    html.push("</tbody></table></div>");
    var howTxt = Object.keys(how).map(function (k) { return k + " " + how[k]; }).join(" · ");
    html.push("<div class='small muted' style='margin-top:8px'>归属依据分布：" + esc(howTxt || "—") +
      "。说话人不确定时留空、不猜 —— 「宁可少收，不可错挂」。</div>");
    if (!meta.echo_signal) {
      html.push("<div class='small muted' style='margin-top:4px'>注：本书对白重复率过高（" +
        (meta.repeated_share * 100).toFixed(1) + "%），判定为平行世界同场景重演而非作者刻意回响，" +
        "因此「作者重复写过的句子更重要」这一信号在本报告中已关闭。</div>");
    }
    html.push("</div>");

    // ② 全书 Top：对白与叙述各留配额后混排，避免旁白天然凝练而挤掉人物台词
    html.push("<div class='panel'><h3>全书金句 Top<span class='hint'>对白与叙述各留配额</span></h3><div class='q-grid'>");
    top.slice(0, 30).forEach(function (q) { html.push(quoteItem(q)); });
    html.push("</div></div>");

    // ③ 人物语录：这一栏才回答「每个人的金句名言」
    var byP = Q.by_person || [];
    var shown = byP.filter(function (p) {
      if (quoteScope === "all") return true;
      if (quoteScope === "core") return p.tier === "core";
      return p.tier === "core" || p.tier === "major";
    });
    html.push("<div class='panel'><h3>人物语录<span class='hint'>按出场章数排序</span></h3>");
    html.push("<div class='filter-chips' style='margin-bottom:12px'>");
    [["core", "仅核心"], ["major", "核心+主要"], ["all", "全部 " + byP.length + " 人"]]
      .forEach(function (o) {
        html.push("<span class='chip" + (quoteScope === o[0] ? " on" : "") +
          "' data-qscope='" + o[0] + "'>" + o[1] + "</span>");
      });
    html.push("</div>");
    if (!shown.length) {
      html.push("<p class='small muted'>该层级下没有可归属的人物语录，切「全部」可见。</p>");
    } else {
      html.push("<div class='q-grid'>");
      shown.forEach(function (p) {
        html.push("<div><div class='q-person'><span class='nm' data-person='" + esc(p.name) + "'>" +
          esc(p.name) + "</span><span class='small muted'>出场 " + p.chapters + " 章 · 收录 " +
          p.quotes.length + " 条</span></div>");
        p.quotes.forEach(function (q) { html.push(quoteItem(q)); });
        html.push("</div>");
      });
      html.push("</div>");
    }
    html.push("</div>");

    // ④ 叙述与独白（不挂任何角色名下）
    if (nar.length) {
      html.push("<div class='panel'><h3>叙述与独白<span class='hint'>不归属任何角色</span></h3>" +
        "<div class='small muted' style='margin-bottom:10px'>取自引号以外的文字。" +
        "第一人称的标为「独白」，第三人称的标为「叙述」—— 两者都不是某个人物" +
        "「说」的话，因此不进入上方的人物语录。</div><div class='q-grid'>");
      nar.forEach(function (q) { html.push(quoteItem(q)); });
      html.push("</div></div>");
    }

    // ⑤ 说话人未确定
    var unknown = dlg.filter(function (q) { return !q.s; });
    if (unknown.length) {
      html.push("<div class='panel'><h3>说话人未确定<span class='hint'>" + unknown.length +
        " 条</span></h3><div class='small muted' style='margin-bottom:10px'>这些句子确定是人物对白，" +
        "但原文没有写明是谁说的（纯对白段落、无人称标签）。不猜、不硬填，如实列出。</div>" +
        "<div class='q-grid'>");
      unknown.forEach(function (q) { html.push(quoteItem(q)); });
      html.push("</div></div>");
    }

    box.innerHTML = html.join("");
    Array.prototype.forEach.call(box.querySelectorAll("[data-person]"), function (s) {
      s.onclick = function () { showPerson(s.dataset.person); };
    });
    Array.prototype.forEach.call(box.querySelectorAll("[data-qscope]"), function (s) {
      s.onclick = function () { quoteScope = s.dataset.qscope; renderQuotes(); };
    });
  }

  /* ---------- 故事长文 ---------- */
  // 章号（书中真实编号 no）→ 内部索引 i。长文里写的是 no，事件表里存的是 i，
  // 两张表必须过一道换算，否则点「第207章」会翻到第207个索引（=书中第210章）——
  // 天才基本法索引 112 之后 no = index - 3，直接混用必然错位。
  var noById = {};
  chapters.forEach(function (c) { noById[c.n] = c.i; });

  // fromStory=false 表示从人物卡/地点卡/事件表的章节 chip 点进来，
  // 文案不能写「本篇长文引用」——那是故事视图专属的口径。
  function showChapterRef(no, fromStory) {
    var idx = noById[no];
    var ch = chapterById[idx];
    var list = idx == null ? [] : events.filter(function (e) {
      return (e.c || []).indexOf(idx) >= 0;
    });
    var ps = {};
    list.forEach(function (e) { (e.p || []).forEach(function (p) { ps[p] = (ps[p] || 0) + 1; }); });
    var topPs = Object.keys(ps).sort(function (a, b) { return ps[b] - ps[a]; }).slice(0, 8);
    var html = ["<h3 style='margin:0 0 4px'>" + esc(chapterLabel(idx == null ? no : idx)) + "</h3>"];
    html.push("<div class='small muted' style='margin-bottom:12px'>" +
      (fromStory === false ? "第 " + no + " 章" : "本篇长文引用的第 " + no + " 章") +
      " · KG 收录该章事件 <b>" + list.length + "</b> 条" +
      (topPs.length ? " · 出场最多：" + topPs.map(function (p) {
        return esc(p) + "(" + ps[p] + ")";
      }).join("、") : "") + "</div>");
    if (!list.length) {
      html.push("<p class='small muted'>该章在 KG 中没有事件记录。长文只复述有事件支撑的情节，" +
        "没有记录的部分会标「未收录」，不代答。</p>");
    } else {
      html.push("<div class='table-wrap' style='max-height:52vh;overflow:auto'><table class='data'><tbody>");
      list.sort(function (a, b) { return a.n.localeCompare(b.n); }).forEach(function (e) {
        html.push("<tr><td>" + esc(e.n) + "</td><td class='small muted'>" + esc(evCat(e)) +
          "</td><td class='small muted'>" + esc((e.p || []).slice(0, 4).join("、")) +
          ((e.p || []).length > 4 ? " 等" : "") + "</td></tr>");
        if (e.no) {
          html.push("<tr><td colspan='3' class='small' style='color:var(--ink-2);padding-top:0'>" +
            esc(e.no) + "</td></tr>");
        }
      });
      html.push("</tbody></table></div>");
    }
    openDialog(html.join(""));
  }

  function renderStory() {
    var box = $("view-story"), S = DATA.story;
    if (!S || !S.html) {
      box.innerHTML = "<div class='panel'><h3>故事长文</h3><p class='small muted'>" +
        "本书尚未生成故事长文 —— 先写 <code>docs/story_" +
        (DATA.meta && DATA.meta.book ? DATA.meta.book : "") + ".md</code>，" +
        "再跑 <code>python src/generate_report.py</code>。</p>" +
        "<p class='small muted'>口径：长文只复述 KG 事件支撑的情节，不凭记忆补梗概；" +
        "素材未覆盖处标「未收录」。</p></div>";
      return;
    }
    var html = [];
    // ① 口径：先说清这段文字是什么、能信到什么程度
    html.push("<div class='panel'><h3>一篇文章讲完全部故事<span class='hint'>与左侧九个视图同源</span></h3>");
    html.push("<div class='findings'><div class='finding'><div class='claim'>这不是文学评论，" +
      "是故事复述 —— 从同一批 KG 事件里长出来的另一张皮。</div>" +
      "<div class='ev'>证据：全文只做取舍、连缀与措辞，不补充抽取结果里没有的情节；" +
      "素材未覆盖处明确标「未收录」，不代答。源文件 " + esc(S.src) + "（" +
      S.md_chars + " 字符）。</div></div></div>");
    html.push("<div class='table-wrap' style='margin-top:12px'><table class='data'><tbody>");
    [["可点章号链接", S.ref_count + " 个"], ["小节", (S.toc || []).length + " 个"]].forEach(function (r) {
      html.push("<tr><td>" + r[0] + "</td><td class='num'>" + r[1] + "</td></tr>");
    });
    html.push("</tbody></table></div>");
    html.push("<div class='small muted' style='margin-top:8px'>正文里每个「第N章」都是可点的：" +
      "点一下弹出该章在 KG 里的事件清单，可当场核对这段复述有没有据。 " +
      "章号用书中真实编号（非抽取器索引），天才基本法索引 112 之后两者相差 3，" +
      "长文与报告已统一按真实编号。</div></div>");

    // ② 目录：长文上千行，没有目录等于没有导航
    if ((S.toc || []).length) {
      html.push("<div class='panel'><h3>目录</h3><div class='story-toc'>");
      S.toc.forEach(function (h) {
        html.push("<a class='story-toc-item lv" + h.lv + "' href='#" + esc(h.id) + "'>" +
          esc(h.t) + "</a>");
      });
      html.push("</div></div>");
    }

    // ③ 正文
    html.push("<div class='panel story' id='story-body'>" + S.html + "</div>");
    box.innerHTML = html.join("");
    Array.prototype.forEach.call(box.querySelectorAll(".ch-ref"), function (a) {
      a.onclick = function (ev) {
        ev.preventDefault();
        showChapterRef(+a.dataset.no);
      };
    });
  }

  /* ---------- 多学科视角分析（ming 式） ---------- */
  // 把正文里的「可信度：高」/「性质：实测」标记成明察式徽章
  function badgeify(s) {
    if (!s) return s;
    s = s.replace(/可信度[：:](高|中|低)/g, function (_, k) {
      var c = { "高": "h", "中": "m", "低": "l" }[k];
      return '<span class="badge cred-' + c + '">可信度 ' + k + '</span>';
    });
    s = s.replace(/性质[：:](实测|推断)/g, function (_, k) {
      var c = { "实测": "real", "推断": "inf" }[k];
      return '<span class="badge nature-' + c + '">性质 ' + k + '</span>';
    });
    return s;
  }
  // 阶段引用 → 可点链接：正文里的「阶段名（起–止）」点击后跳到阶段轴并高亮该段。
  // 纪律：只链能无歧义对应到唯一一段的写法——
  //   1) 名（起–止）恒可链（精确到段）；
  //   2) 裸名仅当该书阶段里唯一（「第一卷·主线」有 11 段，裸名不链——错挂比不链更糟）。
  // 实现：只走文本节点（TreeWalker），跳过 a/code/script 里的内容；
  //   带区间与裸名两类模式合成一个交替正则，长的在前优先匹配。
  function linkifyPhases(root) {
    if (!root || !phases.length) return 0;
    var counts = {};
    phases.forEach(function (p) { counts[p.name] = (counts[p.name] || 0) + 1; });
    var parts = [];
    phases.forEach(function (p, i) {
      parts.push({
        src: reEsc(p.name) + "[（(]\\s*" + p.s + "\\s*[–—~～-]\\s*" + p.e + "\\s*[）)]",
        ph: i
      });
      if (counts[p.name] === 1 && p.name.length >= 2) {
        parts.push({ src: reEsc(p.name), ph: i });
      }
    });
    parts.sort(function (a, b) { return b.src.length - a.src.length; });
    var RE = new RegExp(parts.map(function (x) { return "(" + x.src + ")"; }).join("|"), "g");
    var SKIP = { A: 1, CODE: 1, SCRIPT: 1, STYLE: 1, BUTTON: 1 };
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        var tag = node.parentNode && node.parentNode.nodeName;
        return (tag && SKIP[tag]) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    var n = 0;
    nodes.forEach(function (tn) {
      var text = tn.nodeValue;
      RE.lastIndex = 0;
      var m, last = 0, frag = null, hit = false;
      while ((m = RE.exec(text))) {
        var gi = 0;
        for (var g = 1; g < m.length; g++) {
          if (m[g] !== undefined) { gi = g; break; }
        }
        if (!gi) continue;
        if (!frag) frag = document.createDocumentFragment();
        if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        var ph = phases[parts[gi - 1].ph];
        var a = document.createElement("a");
        a.className = "ph-ref";
        a.href = "javascript:void(0)";
        a.setAttribute("data-ph", String(parts[gi - 1].ph));
        a.textContent = m[0];
        a.title = "跳到阶段轴：第" + ph.s + "—" + ph.e + " 章";
        frag.appendChild(a);
        last = m.index + m[0].length;
        hit = true;
        n++;
      }
      if (hit) {
        if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
        tn.parentNode.replaceChild(frag, tn);
      }
    });
    Array.prototype.forEach.call(root.querySelectorAll("a.ph-ref"), function (a) {
      a.onclick = function (ev) {
        ev.preventDefault();
        curPhase = +a.getAttribute("data-ph");
        switchView("phases");
        renderPhases();
        var seg = document.querySelector(".phase-seg.on");
        if (seg && seg.scrollIntoView) {
          seg.scrollIntoView({ block: "nearest", inline: "center" });
        }
      };
    });
    return n;
  }
  /* ---------- 学科视角 ↔ KG 实体 双向联动 ---------- */
  // 数据来自构建期 src/insight_link.py 产出的 DATA.insightIndex：
  //   正向：正文里的人名 / 地名 / 事件名 → 可点（长名优先，通称与歧义名已滤）
  //   反向：详情弹窗里的「相关分析」chip → 跳到命中的分析小节
  function insightIndex() {
    return (typeof DATA !== "undefined" && DATA.insightIndex) || null;
  }

  function linkifyEntities(root) {
    var IX = insightIndex();
    if (!IX || !root) return 0;
    // 只拿构建期筛出的「文档里真出现过」的表面形式（整份实体表不下发，省 25% 体积）
    var map = {}, list = [];
    Object.keys(IX.linked || {}).forEach(function (s) {
      map[s] = IX.linked[s];      // [kind, 规范名/事件id]
      list.push(s);
    });
    if (!list.length) return 0;
    // 长名优先：保证「假祝宁」不被「祝宁」切走（JS 正则交替最左优先，同起点取先出现的分支）
    list.sort(function (a, b) { return b.length - a.length || (a < b ? -1 : 1); });
    var re;
    try {
      re = new RegExp("(" + list.map(function (s) {
        return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      }).join("|") + ")", "g");
    } catch (err) { return 0; }

    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var p = n.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        var t = p.tagName;
        if (t === "A" || t === "BUTTON" || t === "CODE" || t === "SCRIPT" || t === "STYLE") {
          return NodeFilter.FILTER_REJECT;
        }
        return n.nodeValue ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var nodes = [], cur;
    while ((cur = walker.nextNode())) nodes.push(cur);
    var total = 0;
    nodes.forEach(function (node) {
      var text = node.nodeValue, m, last = 0, hit = 0, frag = null;
      re.lastIndex = 0;
      while ((m = re.exec(text)) !== null) {
        var s = m[0];
        if (!(s in map)) continue;
        if (!frag) frag = document.createDocumentFragment();
        frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        var kind = map[s][0], key = map[s][1];
        var b = document.createElement("button");
        b.className = "ins-link ins-" + kind;
        b.textContent = s;
        if (kind === "p") { b.dataset.person = key; b.title = "人物：" + key; }
        else if (kind === "l") { b.dataset.place = key; b.title = "地点：" + key; }
        else { b.dataset.event = key; b.title = "事件详情"; }
        frag.appendChild(b);
        last = m.index + s.length;
        hit++;
      }
      if (!hit) return;
      frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
      total += hit;
    });
    return total;
  }

  // 反向入口：插在人物 / 地点 / 事件详情弹窗里
  function insightBlock(kind, key) {
    var IX = insightIndex();
    if (!IX) return "";
    var sids = kind === "p" ? (IX.byPerson || {})[key]
      : kind === "l" ? (IX.byPlace || {})[key]
        : (IX.byEvent || {})[key];
    if (!sids || !sids.length) return "";
    var chips = sids.map(function (sid) {
      return "<button class='ins-chip' data-ins='" + esc(sid) + "'>" +
        esc((IX.titles || {})[sid] || sid) + "</button>";
    }).join("");
    return "<div class='ins-block'><span class='ins-label'>相关分析</span>" + chips + "</div>";
  }

  function gotoInsight(sid) {
    // 弹窗是 top-layer，不关掉会盖住正文（明朝项目踩过：点了像没反应）
    var bd = $("dialog-backdrop");
    if (bd && !bd.hidden) closeDialog();
    switchView("perspectives");
    setTimeout(function () {
      var t = document.getElementById(sid);
      if (!t) return;
      t.scrollIntoView({ behavior: "smooth", block: "center" });
      t.classList.add("ins-flash");
      setTimeout(function () { t.classList.remove("ins-flash"); }, 2600);
    }, 80);
  }

  /* ---------- 论文（15 篇双文本对照论文） ---------- */
  // 论文是两书共用的：同一篇里同时引两本书的数字，因此不随书切换。
  // curPaper 记住当前选中的篇目，深链 paper=<slug> 与它对应。
  var curPaper = 0;
  function paperHtml(it) {
    return "<div class='panel story' id='paper-body'>" + it.html + "</div>";
  }
  function renderPapers() {
    var box = $("view-papers"), S = DATA.papers;
    if (!S || !S.items || !S.items.length) {
      box.innerHTML = "<div class='panel'><h3>论文体系</h3><p class='small muted'>" +
        "尚未生成论文 —— 先跑 <code>python src/papers_prep.py</code> 与 " +
        "<code>python src/papers_render.py</code>，再重建报告。</p></div>";
      return;
    }
    if (curPaper < 0 || curPaper >= S.items.length) curPaper = 0;
    var it = S.items[curPaper];
    var html = [];
    html.push("<div class='panel'><h3>论文体系<span class='hint'>" + S.items.length +
      " 篇 · 双文本对照</span></h3>");
    html.push("<div class='findings'><div class='finding'><div class='claim'>" +
      "不是学科视角的复述：每篇论文有中英双语题录、独立的方法与讨论、数据图，" +
      "以及<b>逐条经 Crossref 核验</b>的 APA-7 参考文献（DOI 可直接打开原记录）。</div>" +
      "<div class='ev'>正文里的数字不手写，全部由 <code>src/papers_prep.py</code> 现算后用占位符替换；" +
      "<code>src/verify_papers.py</code> 独立复算一遍，并检查结构、引用闭合、数字可溯源。" +
      "图片在本地 <code>papers/&lt;篇名&gt;/figures/</code>（单文件报告不内嵌 PNG）。</div></div></div>");
    html.push("<div class='paper-list'>");
    S.items.forEach(function (p, i) {
      html.push("<button class='paper-item" + (i === curPaper ? " on" : "") + "' data-i='" + i + "'>" +
        "<b>" + esc(p.zh) + "</b><span>" + esc(p.en) + "</span>" +
        "<em>" + esc(p.kzh || "") + " · " + p.n_ref + " 条文献</em></button>");
    });
    html.push("</div></div>");
    html.push(paperHtml(it));
    box.innerHTML = html.join("");
    Array.prototype.forEach.call(box.querySelectorAll(".paper-item"), function (b) {
      b.onclick = function () {
        curPaper = +b.dataset.i;
        renderPapers();
        syncHash();
      };
    });
    Array.prototype.forEach.call(box.querySelectorAll(".chip-link[data-ch]"), function (c) {
      c.onclick = function () { showChapterRef(+c.dataset.ch); };
    });
    // 论文正文的人名/地名/事件名也做成可点（复用学科视角的实体索引）。
    // 注意只链「本报告 payload 里有的」实体——论文是双文本对照，另一本书的实体
    // 在本书 payload 中根本不存在，点开也无卡可看，所以那些名字保持纯文本，不造假链接。
    var nEnt = linkifyEntities($("paper-body"));
    Array.prototype.forEach.call(box.querySelectorAll(".ins-link"), function (b) {
      b.onclick = function () {
        if (b.dataset.person) showPerson(b.dataset.person);
        else if (b.dataset.place) showPlace(b.dataset.place);
        else if (b.dataset.event) showEvent(b.dataset.event);
      };
    });
    if (nEnt) {
      var pn = el("div", "small muted");
      pn.style.marginTop = "8px";
      pn.innerHTML = "本篇正文里 <b>" + nEnt + "</b> 处人名 / 地名 / 事件名可点（点开详情弹窗）。" +
        "论文是两本书对照写的，<b>只有本书的实体可点</b>——另一本书的实体不在本报告的 payload 里。";
      box.appendChild(pn);
    }
  }

  function renderPerspectives() {
    var box = $("view-perspectives"), S = DATA.perspectives;
    if (!S || !S.html) {
      box.innerHTML = "<div class='panel'><h3>多学科视角分析</h3><p class='small muted'>" +
        "本书尚未生成学科视角分析 —— 先写 <code>docs/perspectives_" +
        (DATA.meta && DATA.meta.book ? DATA.meta.book : "") + ".md</code>，" +
        "再跑 <code>python src/generate_report.py</code>。</p>" +
        "<p class='small muted'>口径：结论先行 + 证据（KG 实测节点/边/数量/占比）+ 口径声明；" +
        "数字由 <code>src/verify_perspectives.py</code> 独立复核。</p></div>";
      return;
    }
    var html = [];
    html.push("<div class='panel'><h3>多学科视角分析<span class='hint'>明察式 · 结论先行</span></h3>");
    html.push("<div class='findings'><div class='finding'><div class='claim'>这不是读后感，" +
      "是 KG 实测数据驱动的学科拆解 —— 每条结论按明察纪律标注 <b>可信度</b>（高/中/低）与 <b>性质</b>（实测/推断），" +
      "<b>推断不得冒充事实</b>。</div>" +
      "<div class='ev'>方法论：结论先行 + 证据（KG 节点/边/数量/占比，带分子·分母可复算）+ 来源（data.json 具体字段）+ 可信度标注。" +
      "数字由 <code>src/perspectives_prep.py</code> 现算、<code>src/verify_perspectives.py</code> 独立复核（== KG_SPEC ④′）。源文件 " +
      esc(S.src) + "（" + S.md_chars + " 字符）。</div></div></div>");
    // 可信度图例
    // 学科清单从目录现取，不再手写死：v3.10 把 6 科扩到 14 科时，这行文案
    // 曾停留在旧清单（页头说 6 科、正文有 14 节），是典型的「同一事实两处维护」。
    // 取 h2 里以序号开头的标题，去掉序号与副标题，得到「社会学 / 心理学 / …」。
    var disc = (S.toc || []).filter(function (h) {
      // 末节「口径与缺口声明」也带序号，但它不是学科——只排除**标题开头**是
      // 口径/参考/附录 的节，不能按关键词排除（「性别研究…（本节只报缺口）」会被误杀）
      return h.lv === 2 && /^\d+\s/.test(h.t) && !/^\d+\s*(口径|参考|附录|声明)/.test(h.t);
    }).map(function (h) {
      return h.t.replace(/^\d+\s*/, "").split(/[：:]/)[0];
    });
    html.push("<div class='table-wrap' style='margin-top:12px'><table class='data'><tbody>");
    [["覆盖学科", (disc.length ? disc.join(" / ") : "社会学 / 心理学 / 经济学 / 政治学 / 叙事学 / 教育学") +
      (disc.length ? "（共 " + disc.length + " 科）" : "")],
     ["可信度 高", "直接计数得出，分母明确，零推断"],
     ["可信度 中", "数据实测，但结论是一步归纳"],
     ["可信度 低", "文学/结构解读，标「推断」，反向证据可推翻"],
     ["性质 实测", "直接计数 / 字段值"],
     ["性质 推断", "由实测推得的解释性结论，不当事实"],
     ["复核", "现算 == ④′ canonical == 文档"]].forEach(function (r) {
      html.push("<tr><td>" + r[0] + "</td><td class='num'>" + r[1] + "</td></tr>");
    });
    html.push("</tbody></table></div>");
    html.push("<div class='small muted' style='margin-top:8px'>时间口径：事件 year 字段全空，" +
      "一律用书中章号与阶段轴，不用公元纪年。口径缺口（其他关系残差、群体称谓、重复章节等）" +
      "在文档末节（口径与缺口声明）单列说明。</div></div>");

    if ((S.toc || []).length) {
      html.push("<div class='panel'><h3>目录</h3><div class='story-toc'>");
      S.toc.forEach(function (h) {
        html.push("<a class='story-toc-item lv" + h.lv + "' href='#" + esc(h.id) + "'>" +
          esc(h.t) + "</a>");
      });
      html.push("</div></div>");
    }

    var body = badgeify(S.html);
    html.push("<div class='panel story' id='perspectives-body'>" + body + "</div>");
    box.innerHTML = html.join("");
    Array.prototype.forEach.call(box.querySelectorAll(".ch-ref"), function (a) {
      a.onclick = function (ev) {
        ev.preventDefault();
        showChapterRef(+a.dataset.no);
      };
    });
    // 顺序不能反：阶段引用先链接化，实体后做（实体链接会跳过已生成的 a）。
    // 反过来的话，实体链接会把「第一卷·主线（220–232）」这类阶段名从中间切碎
    // （「主线」被包成 button），阶段引用就再也匹配不到——实测废土 88 → 60，丢了 28 个。
    // 阶段名内部的词本就不该被链成实体，先阶段后实体恰好是正确取舍。
    var nPh = linkifyPhases($("perspectives-body"));
    var nEnt = linkifyEntities($("perspectives-body"));

    Array.prototype.forEach.call(box.querySelectorAll(".ins-link"), function (b) {
      b.onclick = function () {
        if (b.dataset.person) showPerson(b.dataset.person);
        else if (b.dataset.place) showPlace(b.dataset.place);
        else if (b.dataset.event) showEvent(b.dataset.event);
      };
    });

    var note = el("div", "small muted");
    note.style.marginTop = "8px";
    var parts = [];
    if (nEnt) {
      parts.push("<b>" + nEnt + "</b> 个人名 / 地名 / 事件名可点（点开详情弹窗）");
    }
    if (nPh) {
      parts.push("<b>" + nPh + "</b> 个「阶段名（起–止）」引用可点（跳阶段轴并高亮该段）");
    }
    if (parts.length) {
      note.innerHTML = parts.join("；") +
        "。同名多段的合计数字不设链接，避免一段链代表多段；" +
        "通称（老师 / 队长 / 基地…）一律不链，避免把整篇文档链成筛子。";
      box.firstChild.appendChild(note);
    }
  }

  /* ---------- 深链（地址栏即状态，复制即可分享） ---------- */
  // 读支持的参数（可组合，如 #view=characters&person=祝宁&detail=1）：
  //   view=<视图键>   切视图（键非法回退总览——否则没有任何 .view 带 active，整页空白）
  //   q=<文本>        预填当前视图的搜索框（人物/地点/事件三个有搜索的视图）
  //   person=<姓名>   切人物视图 + 搜索定位 + 闪烁；支持别名（canonPerson）
  //   detail=1        配合 person：直接打开该人物的详情弹窗
  //   place=<地名>    切地点视图并打开详情弹窗
  //   event=<事件id>  切事件视图并打开详情弹窗（id 形如 event:祝宁穿越至废土世界）
  //   phase=<序号|键> 阶段轴定位该段并闪烁；序号或「名（起–止）」唯一键均可
  // 写：history.replaceState 回写当前状态。**不能用 location.hash 赋值**——
  // 那会触发 hashchange → 再 apply → 死循环；replaceState 不触发事件，刚好。
  var lastEntity = null;   // 最近打开的详情 {kind:"person"|"place"|"event", v:...}
  function parseHash() {
    var out = {};
    (location.hash || "").replace(/^#/, "").split("&").forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf("=");
      var k = i < 0 ? kv : kv.slice(0, i);
      var v = i < 0 ? "" : kv.slice(i + 1);
      try { out[decodeURIComponent(k)] = decodeURIComponent(v); }
      catch (e) { out[k] = v; }   // 畸形编码不炸，按原样用
    });
    return out;
  }
  function syncHash() {
    var parts = ["view=" + currentView];
    if (currentView === "events" && evQuery) parts.push("q=" + encodeURIComponent(evQuery));
    if (currentView === "characters" && charQuery) parts.push("q=" + encodeURIComponent(charQuery));
    if (currentView === "places" && placeQuery) parts.push("q=" + encodeURIComponent(placeQuery));
    if (currentView === "phases") parts.push("phase=" + curPhase);
    if (currentView === "papers" && DATA.papers && DATA.papers.items[curPaper]) {
      parts.push("paper=" + encodeURIComponent(DATA.papers.items[curPaper].slug));
    }
    // 详情弹窗参数只在「当前视图与实体同类」时才回写——
    // 从金句/学科视角点开的人物不写 person=，否则地址栏会谎报你所在的视图。
    var bd = $("dialog-backdrop");
    if (lastEntity && bd && !bd.hidden) {
      if (lastEntity.kind === "person" && currentView === "characters") {
        parts.push("person=" + encodeURIComponent(lastEntity.v), "detail=1");
      } else if (lastEntity.kind === "place" && currentView === "places") {
        parts.push("place=" + encodeURIComponent(lastEntity.v));
      } else if (lastEntity.kind === "event" && currentView === "events") {
        parts.push("event=" + encodeURIComponent(lastEntity.v));
      }
    }
    var h = "#" + parts.join("&");
    if (h !== location.hash) {
      try { history.replaceState(null, "", h); } catch (e) { /* 个别环境禁用时静默降级 */ }
    }
  }
  function personCard(nm) {
    var found = null;
    Array.prototype.forEach.call(document.querySelectorAll(".poke-card"), function (c) {
      if (c.dataset.person === nm) found = c;
    });
    return found;
  }
  function flashPerson(nm) {
    var card = personCard(nm);
    if (!card) { toast("未找到人物：" + nm); return; }
    card.classList.add("dl-flash");
    if (card.scrollIntoView) card.scrollIntoView({ block: "center", behavior: "smooth" });
    setTimeout(function () { card.classList.remove("dl-flash"); }, 2600);
  }
  // 阶段唯一键的 JS 侧副本，必须与 core/phases.py 的 phase_key 逐字一致
  // （「名（起–止）」，连接符是 en-dash –）——两边不一致深链就匹配不上。
  function phaseKeyJs(ph) { return ph.name + "（" + ph.s + "–" + ph.e + "）"; }
  function gotoPhase(key) {
    var i = -1;
    if (/^\d+$/.test(String(key))) {
      i = +key;
    } else {
      phases.forEach(function (p, k) { if (phaseKeyJs(p) === key) i = k; });
    }
    if (i < 0 || i >= phases.length) { toast("未找到阶段：" + key); return; }
    curPhase = i;
    switchView("phases");
    renderPhases();
    var seg = document.querySelector(".phase-seg.on");
    if (seg) {
      seg.classList.add("dl-flash");
      if (seg.scrollIntoView) seg.scrollIntoView({ block: "nearest", inline: "center" });
      setTimeout(function () { seg.classList.remove("dl-flash"); }, 2600);
    }
  }
  function applyHash() {
    var h = parseHash();
    switchView(VIEWS.some(function (x) { return x[0] === h.view; }) ? h.view : "overview");
    if (h.q) {
      if (currentView === "events") { evQuery = h.q; evPage = 0; renderEvents(); }
      else if (currentView === "characters") { charQuery = h.q; renderCharacters(); }
      else if (currentView === "places") { placeQuery = h.q; renderPlaces(); }
    }
    if (h.paper) {
      var idx = -1;
      (DATA.papers && DATA.papers.items || []).forEach(function (p, i) {
        if (p.slug === h.paper) idx = i;
      });
      if (idx >= 0) { curPaper = idx; if (currentView === "papers") renderPapers(); }
    }
    if (h.phase != null && h.phase !== "") gotoPhase(h.phase);
    if (h.person) {
      var nm = canonPerson(h.person);
      if (currentView !== "characters") switchView("characters");
      charQuery = nm;
      renderCharacters();
      // 目标人物可能只在「全部（含龙套）」档里——默认视图看不到等于深链失效，
      // 这时自动放宽显示范围（UI 上的分层按钮会如实反映这个状态）。
      if (!personCard(nm) && charTier !== "all") { charTier = "all"; renderCharacters(); }
      flashPerson(nm);
      if (h.detail === "1") showPerson(nm);
    } else if (h.place) {
      if (currentView !== "places") switchView("places");
      showPlace(h.place);
    } else if (h.event) {
      if (currentView !== "events") switchView("events");
      showEvent(h.event);
    }
    // 归一化回写：把「view + q + 弹窗实体」整理成规范 hash
    // （如只给 #person=X 时会补成 #view=characters&person=X&detail=1）
    syncHash();
  }

  /* ---------- 头部与页脚 ---------- */
  function renderHeader() {
    var m = DATA.meta;
    $("book-title").textContent = m.title;
    $("book-sub").textContent = m.author + " · " + m.chapters + " 章 · " +
      (m.chars >= 10000 ? (m.chars / 10000).toFixed(1) + " 万字" : m.chars + " 字") +
      " · " + (m.kind === "fictional_world" ? "架空世界" : "现实背景");
    // 头部只留一行极简计数：五个盒子挤在标题旁边会把首屏重心拉回「后台看板」，
    // 真正的数字在总览 hero 里放大给出；这一行负责让其余 11 个视图也有上下文。
    var stats = [["章", m.chapters], ["人物", persons.length], ["地点", places.length],
                 ["事件", events.length], ["关系", relations.length]];
    $("header-stats").innerHTML = "<span class='header-stat-line'>" + stats.map(function (s) {
      return "<b>" + s[1] + "</b> " + s[0];
    }).join("<span class='sep'>·</span>") + "</span>";
    var f = $("site-footer");
    f.innerHTML = "<div><b>源透明度</b>：全部实体标注「书中抽取」；地点坐标分 <span class='badge real'>真实坐标</span>" +
      (DATA.meta.kind === "fictional_world" ? "<span class='badge schematic'>示意坐标</span>（非现实坐标，仅表现空间关系）" : "") +
      "<span class='badge pending'>待核验</span> 三态，未定位地点不硬填坐标。</div>" +
      (DATA.meta.dup_pairs ? "<div style='margin-top:4px'><b>源文本质量</b>：检测到 " + DATA.meta.dup_pairs +
        " 对章节全文高度重复（涉及 " + (DATA.meta.dup_chapters || []).length +
        " 章），疑为多源拼合/防盗章伪影。重复内容未做删除（保持源透明），分布图中以半透明标注，解读计数时请注意。</div>" : "") +
      "<div style='margin-top:4px'><b>数据链路</b>：章节正文 → 逐章五元组抽取 → 聚合归一 → 地理增强 → 静态报告。" +
      "生成于 " + esc(m.generated) + " · 本页为单文件离线 HTML，除在线地图瓦片外不依赖网络。</div>";
  }

  /* ---------- 启动 ---------- */
  // 回顶按钮：长文视图（故事/学科视角）滚动过 800px 才出现。
  // ui_audit §3-6：7 万字单页滚动，目录在顶部，滚到中间后回不去。
  // 注意：scroll 处理里**不要**包 requestAnimationFrame——无头 dump-dom 模式下
  // 没有合成器帧，rAF 回调永不执行，按钮也就不出现（probe_back_top.js 实测踩过）。
  // 浏览器对 scroll 事件本就已节流，直接切类即可。
  function bindBackTop() {
    var btn = $("back-top");
    if (!btn) return;
    window.addEventListener("scroll", function () {
      btn.classList.toggle("show", window.scrollY > 800);
    }, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
  function boot() {
    renderHeader();
    buildTabs();
    renderOverview();
    renderDistribution();
    renderCharacters();
    renderPlaces();
    renderEvents();
    renderPhases();
    renderQuotes();
    renderStory();
    renderPerspectives();
    renderPapers();
    bindBackTop();
    // 深链：完整参数（view/q/person/detail/event/place/phase）见本文件「深链」节；
    // 键名非法或缺失时回退到总览，否则没有任何 .view 会带上 active，整页会显示为空白
    applyHash();
    window.addEventListener("hashchange", function () { applyHash(); });
    document.addEventListener("click", function (e) {
      if (e.target.dataset && e.target.dataset.ch) gotoChapter(+e.target.dataset.ch);
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
