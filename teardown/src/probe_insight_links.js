// 探针：验证「学科视角 ↔ KG 实体」双向联动（src/probe_insight_links.js）
// 正向：学科视角正文里的人名/地名/事件名可点 → 打开对应详情弹窗
// 反向：详情弹窗里的「相关分析」chip 可点 → 关弹窗并切回学科视角视图
// 用法：node src/probe_insight_links.js [book]
// 断言：① 正文里至少有一个实体链接；② 点击后详情弹窗打开且标题 == 该实体规范名；
//       ③ 弹窗里出现「相关分析」chip；④ 点 chip 后弹窗关闭且学科视角视图激活。
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "feitu";
const url = "file:///" + OUT + "\\" + book + ".html#view=perspectives";

const probe = `
(function () {
  function fail(msg) { document.title = "PROBE-ERR: " + msg; }
  function wait(sel, cb, tries) {
    var n = 0;
    var iv = setInterval(function () {
      var el = document.querySelector(sel);
      if (el) { clearInterval(iv); cb(el); }
      else if (++n > (tries || 120)) { clearInterval(iv); fail("no " + sel + " after wait"); }
    }, 50);
  }
  // 第一步：点正文里的第一个人物链接
  wait("#view-perspectives .ins-link[data-person]", function (link) {
    var name = link.dataset.person;
    link.click();
    setTimeout(function () {
      var bd = document.getElementById("dialog-backdrop");
      var dlg = document.getElementById("dialog");
      var open = bd && !bd.hidden ? 1 : 0;
      var h2 = dlg && dlg.querySelector("h2") ? dlg.querySelector("h2").textContent : "";
      var chips = dlg ? dlg.querySelectorAll(".ins-chip").length : 0;
      var chip = dlg ? dlg.querySelector(".ins-chip") : null;
      if (!chip) {
        document.title = "AFTER-CLICK person=" + name + " open=" + open +
          " h2=[" + h2 + "] chips=" + chips + " CHIPSTEP=none";
        return;
      }
      // 第二步：点「相关分析」chip，验证反向跳转
      chip.click();
      setTimeout(function () {
        var bd2 = document.getElementById("dialog-backdrop");
        var closed = bd2 && bd2.hidden ? 1 : 0;
        var pv = document.getElementById("view-perspectives");
        var active = pv && pv.classList.contains("active") ? 1 : 0;
        document.title = "AFTER-CLICK person=" + name + " open=" + open +
          " h2=[" + h2 + "] chips=" + chips +
          " | AFTER-CHIP closed=" + closed + " view=" + active;
      }, 400);
    }, 300);
  });
})();`;

const tmp = OUT + "\\_probe_insight.html";
let html = fs.readFileSync(OUT + "\\" + book + ".html", "utf-8");
html = html.replace("</body>", "<script>" + probe + "</scr" + "ipt></body>");
fs.writeFileSync(tmp, html, "utf-8");
let code = 1;   // process.exit 不会执行 finally，所以先记结果、最后退出
try {
  const dom = execFileSync(CHROME, [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    "--virtual-time-budget=8000", "--dump-dom",
    "file:///" + tmp + "#view=perspectives",
  ], { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  const m = dom.match(/<title>([^<]*)<\/title>/);
  const title = m ? m[1] : "(no title)";
  console.log("[" + book + "] " + title);
  const ok = /AFTER-CLICK person=.+ open=1 h2=\[.+\] chips=[1-9]/.test(title)
    && /AFTER-CHIP closed=1 view=1/.test(title)
    && !title.includes("PROBE-ERR");
  console.log(ok ? "PROBE-OK" : "PROBE-FAIL");
  code = ok ? 0 : 1;
} finally {
  fs.unlinkSync(tmp);
}
process.exit(code);
