// 探针：验证深链参数（src/probe_deeplink.js）
// 背景：原先只有 #view= 一个参数，报告无法通过地址栏分享定位（roadmap B1）。
// 现已支持：view / q / person(+detail) / place / event / phase，且交互状态会
// 通过 history.replaceState 回写地址栏（不触发 hashchange，不会回环）。
// 用法：node src/probe_deeplink.js [book]
// 断言（每条一个 URL，读无头 DOM 的 title 摘要）：
//   ① #view=characters&person=X&detail=1 → 人物视图激活 + 弹窗打开 + h2==规范名（别名也认）
//   ② #view=events&event=<id>           → 事件视图激活 + 弹窗打开 + h2==事件名
//   ③ #view=places&place=Y              → 地点视图激活 + 弹窗打开 + h2==Y
//   ④ #view=phases&phase=5              → 阶段视图激活 + 高亮段正是第 5 段（data-ph=5）
//   ⑤ #view=events&q=Z                  → 搜索框预填 Z 且表格被过滤（行数 < 全量）
//   ⑥ #view=bogus                       → 非法键回退总览（view-overview active）
//   ⑦ #view=phases                      → replaceState 回写生效（hash 里出现 phase=0）
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "feitu";

// 每本书的测试实体（都在 data.json 里实证存在）
const CFG = {
  feitu: { person: "祝宁", place: "清洁中心", q: "清洁中心", phase: 5 },
  tiancai: { person: "学姐", expect: "林朝夕", place: "安宁市", q: "林朝夕", phase: 3 },
}[book];
if (!CFG) { console.log("未知书目：" + book); process.exit(1); }

const html = fs.readFileSync(OUT + "\\" + book + ".html", "utf-8");
// 从 payload 里取第一个事件的 id/name 当 ② 的用例（不硬编码，书换了也能跑）
const m0 = html.match(/"i":"(event:[^"]+)","n":"([^"]+)"/);
if (!m0) { console.log("payload 里找不到事件"); process.exit(1); }
const EV_ID = m0[1], EV_NAME = m0[2];
// 第一个阶段的「名（起–止）」唯一键，当 ⑧ 的用例（连接符必须是 en-dash –，
// 与 core/phases.py 的 phase_key 逐字一致）
const m1 = html.match(/"name":"([^"]+)","s":(\d+),"e":(\d+)/);
if (!m1) { console.log("payload 里找不到阶段"); process.exit(1); }
const PH_KEY = m1[1] + "（" + m1[2] + "–" + m1[3] + "）";

const summary = `
<script>
setTimeout(function () {
  var act = document.querySelector(".view.active");
  var bd = document.getElementById("dialog-backdrop");
  var dlg = document.getElementById("dialog");
  var h2 = dlg && dlg.querySelector("h2") ? dlg.querySelector("h2").textContent : "";
  var seg = document.querySelector(".phase-seg.on");
  var input = act ? act.querySelector("input[type=text]") : null;
  var rows = act ? act.querySelectorAll("tbody tr").length : 0;
  // 论文视图：篇目数 + 当前篇正文首标题（深链是否真的选中了那一篇）
  var pn = document.querySelectorAll(".paper-item").length;
  var pb = document.getElementById("paper-body");
  var pt = pb && pb.querySelector("h1") ? pb.querySelector("h1").textContent : "";
  document.title = "DL|view=" + (act ? act.id : "none") +
    "|pn=" + pn + "|pt=" + pt +
    "|dlg=" + (bd && !bd.hidden ? 1 : 0) +
    "|h2=" + h2 +
    "|seg=" + (seg ? seg.getAttribute("data-ph") : "none") +
    "|q=" + (input ? input.value : "") +
    "|rows=" + rows +
    "|hash=" + location.hash;
}, 900);
</scr` + `ipt>`;

const tmp = OUT + "\\_probe_deeplink.html";
fs.writeFileSync(tmp, html.replace("</body>", summary + "</body>"), "utf-8");

function run(hash) {
  const dom = execFileSync(CHROME, [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    "--virtual-time-budget=6000", "--dump-dom",
    "file:///" + tmp + hash,
  ], { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  const m = dom.match(/<title>([^<]*)<\/title>/);
  return m ? m[1] : "(no title)";
}

let bad = 0;
function check(no, desc, hash, expect) {
  const t = run(hash);
  let ok = true, why = [];
  Object.keys(expect).forEach(function (k) {
    var re = expect[k];
    if (re === "*") return;
    if (!re.test(t)) { ok = false; why.push(k + " 不匹配"); }
  });
  if (!ok) bad++;
  console.log("  [" + (ok ? "OK  " : "FAIL") + "] " + no + " " + desc + "\n         " + t +
    (why.length ? "\n         缺：" + why.join("；") : ""));
}

try {
  console.log("===== " + book + "（深链探针）=====");
  check("①", "person+detail（别名→规范名）",
    "#view=characters&person=" + encodeURIComponent(CFG.person) + "&detail=1",
    { view: /view=view-characters/, dlg: /dlg=1/, h2: new RegExp("h2=" + (CFG.expect || CFG.person)) });
  check("②", "event 详情",
    "#view=events&event=" + encodeURIComponent(EV_ID),
    { view: /view=view-events/, dlg: /dlg=1/, h2: new RegExp("h2=" + EV_NAME.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")) });
  check("③", "place 详情",
    "#view=places&place=" + encodeURIComponent(CFG.place),
    { view: /view=view-places/, dlg: /dlg=1/, h2: new RegExp("h2=" + CFG.place) });
  check("④", "phase 定位",
    "#view=phases&phase=" + CFG.phase,
    { view: /view=view-phases/, seg: new RegExp("seg=" + CFG.phase + "(\\||$)") });
  check("⑤", "q 预填 + 过滤",
    "#view=events&q=" + encodeURIComponent(CFG.q),
    { view: /view=view-events/, q: new RegExp("q=" + CFG.q), rows: /rows=\d+/ });
  check("⑥", "非法 view 键回退总览",
    "#view=bogus",
    { view: /view=view-overview/ });
  check("⑦", "replaceState 回写地址栏",
    "#view=phases",
    { view: /view=view-phases/, hash: /hash=#view=phases(&|&amp;)phase=\d+/ });
  check("⑧", "phase 唯一键（名（起–止））定位",
    "#view=phases&phase=" + encodeURIComponent(PH_KEY),
    { view: /view=view-phases/, seg: /seg=0(\\||$)/ });
  // 论文是两书共用的同一批篇目（双文本对照），因此 book 参数不影响篇目数
  check("⑨", "paper 深链（篇目定位）",
    "#view=papers&paper=13-gender",
    { view: /view=view-papers/, pn: /pn=15(\||$)/, pt: /十分之一/,
      hash: /paper=13-gender/ });
} finally {
  fs.unlinkSync(tmp);
}
console.log(bad ? "PROBE-FAIL（" + bad + " 条未过）" : "PROBE-OK");
process.exit(bad ? 1 : 0);
