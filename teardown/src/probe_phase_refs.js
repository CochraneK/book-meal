// 探针：验证「学科视角」视图里点阶段引用链接，真的能跳到阶段轴并高亮对应阶段段。
// 只跑 dump-dom 只能看到静态正文，看不到点击后的跳转——而跳转正是这次挂入的核心
// （分析文档与阶段轴从此不是两张皮）。所以这里模拟真实点击，再把跳转结果 dump 出来核对。
//
// 用法：node src/probe_phase_refs.js [book] [匹配式,匹配式…]
//   匹配式 = 链接文本包含的子串（如 "第6段（107–141）"），或 "#N" 表示第 N 个链接（从 0 计）
//   例：node src/probe_phase_refs.js tiancai "第6段（107–141）" "#0"
//       （多个匹配式用逗号隔开传一个参数，或分成多个参数均可）
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "tiancai";
const pats = (process.argv.slice(3).join(",") || "#0,#1,#2")
  .split(",").map((s) => s.trim()).filter(Boolean);

let html = fs.readFileSync(`${OUT}\\${book}.html`, "utf8");
const probe = `<script>
window.addEventListener("load", function () {
  try {
    var pats = ${JSON.stringify(pats)};
    var box = document.createElement("div");
    box.id = "probe-box";
    document.body.appendChild(box);
    var tab = document.querySelector('.tab[data-view="perspectives"]');
    if (tab) tab.click();
    var all = Array.prototype.slice.call(document.querySelectorAll("a.ph-ref"));
    box.appendChild(document.createTextNode("链接总数=" + all.length));
    pats.forEach(function (pat) {
      box.appendChild(document.createElement("hr"));
      var a = null, label = pat;
      if (pat.charAt(0) === "#") {
        var i = parseInt(pat.slice(1), 10);
        a = all[i] || null;
        label = "第" + i + "个链接";
      } else {
        for (var k = 0; k < all.length; k++) {
          if (all[k].textContent.indexOf(pat) >= 0) { a = all[k]; break; }
        }
      }
      box.appendChild(document.createTextNode("=== " + label + " ==="));
      if (!a) { box.appendChild(document.createTextNode("页面上没有该链接")); return; }
      var want = a.getAttribute("data-ph");
      box.appendChild(document.createTextNode("链接文本=" + a.textContent + " data-ph=" + want));
      a.click();
      var vp = document.getElementById("view-phases");
      var on = document.querySelector(".phase-seg.on");
      var body = document.getElementById("phase-body");
      box.appendChild(document.createTextNode("阶段轴激活=" + (vp && vp.classList.contains("active"))));
      box.appendChild(document.createTextNode("on段data-ph=" + (on ? on.getAttribute("data-ph") : "(无)")));
      box.appendChild(document.createTextNode("on段标题=" + (on ? on.getAttribute("title") : "(无)")));
      box.appendChild(document.createTextNode("阶段正文=" + (body ? body.textContent.slice(0, 60).replace(/\\s+/g, " ") : "(无)")));
    });
    box.appendChild(document.createTextNode("PROBE-END-SENTINEL"));
  } catch (e) {
    document.title = "PROBE-ERR: " + e.message;
  }
});
</script>`;
html = html.replace("</body>", probe + "</body>");
const tmp = `${OUT}\\_shots\\_probe_phase_${book}.html`;
fs.writeFileSync(tmp, html);

const dom = execFileSync(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=8000", "--dump-dom",
  "file:///" + tmp.replace(/\\/g, "/") + "#view=perspectives",
], { encoding: "utf8", maxBuffer: 1024 * 1024 * 200 });

if (/PROBE-ERR/.test(dom)) {
  const t = /<title>([\s\S]*?)<\/title>/.exec(dom);
  const msg = t ? t[1] : "(未拿到 title)";
  if (/^PROBE-ERR/.test(msg)) {
    console.log("PROBE-ERR：" + msg.replace(/^PROBE-ERR:?\s*/, ""));
    process.exit(1);
  }
}
const m = dom.match(/<div id="probe-box">([\s\S]*?)PROBE-END-SENTINEL/);
if (!m) {
  console.log("(探针未取到内容：probe-box 没进 dump，或结束哨兵缺失)");
  process.exit(1);
}
// 逐块核对：data-ph 必须与 on 段一致，且阶段轴必须被激活
const blocks = m[1].split("=== ").slice(1);
let bad = 0;
blocks.forEach(function (b) {
  const head = "=== " + b.split(" ===")[0] + " ===";
  const noLink = /没有该链接/.test(b);
  const want = /data-ph=(\d+)/.exec(b);
  const on = /on段data-ph=(\d+)/.exec(b);
  const active = /阶段轴激活=true/.test(b);
  const title = /on段标题=([^<]*)/.exec(b);
  const bodyTxt = /阶段正文=([^<]*)/.exec(b);
  const ok = !noLink && want && on && want[1] === on[1] && active;
  if (!ok) bad++;
  console.log(head, ok ? "√ 跳转正确" : "× 跳转异常",
    want ? "data-ph=" + want[1] : "", on ? "on段=" + on[1] : "",
    "激活=" + active, title ? "| " + title[1].trim() : "",
    bodyTxt ? "| " + bodyTxt[1].trim().slice(0, 40) : "");
});
console.log(bad ? `[FAIL] ${bad} 个链接跳转异常` : `[OK] ${blocks.length} 个链接全部跳到对应阶段段`);
process.exit(bad ? 1 : 0);
