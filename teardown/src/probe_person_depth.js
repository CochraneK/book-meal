// 探针：人物卡深度（A4 卡背语录 + A5 role 结构化）+ 金句章号口径（src/probe_person_depth.js）
// 背景：
//   A4 —— 卡背此前只有阵营/出场/来源，quotes.json 里归属好的对白没被用上；
//   A5 —— role 是自由文本裸串（「女主角，22岁哲学系大四实习生」），详情里一坨；
//   顺带修：金句页章号标签印的是**内部索引**（天才 ch=221 实际第 218 章），
//   点开弹窗却显示 218——同一句两个章号。这里一并固化成断言。
// 用法：node src/probe_person_depth.js [book]
// 断言：
//   ① 人物视图有卡背语录（.poke-quote >= 1），且每条都带章号来源
//   ② 详情弹窗有「语录」分组 + 最多 3 条，章号标签 = DATA 里的真章号（不是索引）
//   ③ 详情弹窗身份区有结构化徽章 + **原文**保留（标签错时读者能看出来）
//   ④ 金句视图所有章号标签都等于该索引对应的真章号（全书扫，抓 221/218 这类）
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "feitu";

const CFG = {
  feitu: { person: "祝宁", roleTag: "女主" },
  tiancai: { person: "林朝夕", roleTag: "女主角" },
}[book];
if (!CFG) { console.log("未知书目：" + book); process.exit(1); }

const html = fs.readFileSync(OUT + "\\" + book + ".html", "utf-8");
const tmp = OUT + "\\_probe_depth.html";

// 页面内自检：把结果拼进 title，逐条带 PASS/FAIL 原因
const script = `
<script>
function chNo(i) {
  var m = {};
  (window.DATA.chapters || []).forEach(function (c) { m[c.i] = c.n; });
  return m[i];
}
setTimeout(function () {
  var out = [];
  var act = document.querySelector(".view.active");
  var dlg = document.getElementById("dialog");
  var bd = document.getElementById("dialog-backdrop");

  // ① 卡背语录
  var cards = document.querySelectorAll("#view-characters .poke-card").length;
  var qs = document.querySelectorAll("#view-characters .poke-quote");
  var qOk = qs.length > 0;
  var srcOk = true;
  Array.prototype.forEach.call(qs, function (q) {
    var s = q.querySelector(".poke-quote-src");
    if (!s || !/第\\d+章/.test(s.textContent)) srcOk = false;
  });
  out.push("A4back=" + (qOk && srcOk ? "PASS" : "FAIL(q=" + qs.length + ",src=" + srcOk + ",cards=" + cards + ")"));

  // ② / ③ 详情弹窗
  var txt = dlg ? dlg.textContent : "";
  var qLinks = dlg ? dlg.querySelectorAll(".q-meta .chip-link[data-ch]") : [];
  var qBad = [];
  Array.prototype.forEach.call(qLinks, function (a) {
    var i = +a.getAttribute("data-ch");
    var want = chNo(i);
    var m = /第(\\d+)章/.exec(a.textContent);
    if (!m || +m[1] !== want) qBad.push(a.textContent.trim() + "(ch=" + i + ",want=" + want + ")");
  });
  var nQuote = dlg ? dlg.querySelectorAll(".q-item.q-inline").length : 0;
  out.push("A4dlg=" + (nQuote > 0 && nQuote <= 3 && !qBad.length
    ? "PASS(n=" + nQuote + ",links=" + qLinks.length + ")"
    : "FAIL(n=" + nQuote + ",bad=" + qBad.join(";") + ")"));

  var badges = dlg ? Array.prototype.map.call(dlg.querySelectorAll("dd .badge"), function (b) {
    return b.textContent;
  }) : [];
  var hasTag = badges.indexOf("${CFG.roleTag}") >= 0;
  var hasRaw = txt.indexOf("原文：") >= 0;
  out.push("A5=" + (hasTag && hasRaw ? "PASS(" + badges.join("/") + ")"
    : "FAIL(tags=" + badges.join("/") + ",raw=" + hasRaw + ")"));

  // ④ 金句页章号口径全量核对
  var qv = document.getElementById("view-quotes");
  var bad = [];
  if (qv) {
    Array.prototype.forEach.call(qv.querySelectorAll(".chip-link[data-ch]"), function (a) {
      var i = +a.getAttribute("data-ch");
      var want = chNo(i);
      var m = /第(\\d+)章/.exec(a.textContent);
      if (!m || +m[1] !== want) bad.push(a.textContent.trim() + "(ch=" + i + ",want=" + want + ")");
    });
  }
  var nChecked = qv ? qv.querySelectorAll(".chip-link[data-ch]").length : 0;
  out.push("QUOTE-CH=" + (bad.length ? "FAIL(" + bad.slice(0, 3).join(";") + ")"
    : "PASS(n=" + nChecked + ")") + (nChecked ? "" : "EMPTY"));

  document.title = "DEPTH|" + out.join("|");
  if (act) { /* keep linter happy */ }
}, 1000);
</scr` + `ipt>`;

fs.writeFileSync(tmp, html.replace("</body>", script + "</body>"), "utf-8");

function run(hash) {
  const dom = execFileSync(CHROME, [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    "--virtual-time-budget=7000", "--dump-dom",
    "file:///" + tmp + hash,
  ], { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  const m = dom.match(/<title>([^<]*)<\/title>/);
  return m ? m[1] : "(no title)";
}

// ④ 需要金句视图；②③ 需要详情弹窗。分两次跑，互不影响
const t1 = run("#view=characters&person=" + encodeURIComponent(CFG.person) + "&detail=1");
const t2 = run("#view=quotes");

fs.unlinkSync(tmp);

function check(label, title) {
  const parts = title.replace(/^DEPTH\|/, "").split("|");
  const hit = parts.filter(function (p) { return p.indexOf(label) === 0; })[0] || "(missing)";
  const ok = hit.indexOf("PASS") > 0;
  console.log((ok ? "  [PASS] " : "  [FAIL] ") + hit);
  return ok;
}

console.log("== " + book + " 人物卡深度 / 金句章号 ==");
let ok = true;
ok = check("A4back", t1) && ok;
ok = check("A4dlg", t1) && ok;
ok = check("A5", t1) && ok;
ok = check("QUOTE-CH", t2) && ok;
console.log(ok ? "PROBE-OK " + book : "PROBE-FAIL " + book);
process.exit(ok ? 0 : 1);
