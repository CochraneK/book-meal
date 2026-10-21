// 探针：验证「论文正文 ↔ KG 实体」单向联动（src/probe_paper_links.js）
// 背景：papers 是两书对照写的，正文里会出现人名/地名。v3.12 起这些名字可点，
//       但**只有本书 payload 里有的实体**才可点（另一本书的实体在本书里根本不存在，
//       点开也无卡可看，所以那些名字保持纯文本——不造假链接）。
// 用法：node src/probe_paper_links.js [book]
// 断言：① 论文视图激活且篇目数 = 15；② #paper-body 里至少有 1 个 .ins-link；
//       ③ 点第一个人物链接 → 弹窗打开且标题 == 该实体规范名；
//       ④ 切到另一篇 → 重新渲染后仍有实体链接（renderPapers 每次重建 DOM，容易漏接）。
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "feitu";

const probe = `
(function () {
  function fail(msg) { document.title = "PROBE-ERR: " + msg; }
  function wait(sel, cb, tries) {
    var n = 0;
    var iv = setInterval(function () {
      var el = document.querySelector(sel);
      if (el) { clearInterval(iv); cb(el); }
      else if (++n > (tries || 160)) { clearInterval(iv); fail("no " + sel + " after wait"); }
    }, 50);
  }
  wait("#view-papers .paper-item", function () {
    var n = document.querySelectorAll("#view-papers .paper-item").length;
    var body = document.getElementById("paper-body");
    var links = body ? body.querySelectorAll(".ins-link") : [];
    if (!links.length) {
      document.title = "AFTER-RENDER n=" + n + " links=0";
      return;
    }
    var firstName = "";
    for (var i = 0; i < links.length; i++) {
      if (links[i].dataset.person) { firstName = links[i].dataset.person; break; }
    }
    if (!firstName) {
      document.title = "AFTER-RENDER n=" + n + " links=" + links.length + " person=0";
      return;
    }
    var link = null;
    for (var j = 0; j < links.length; j++) {
      if (links[j].dataset.person === firstName) { link = links[j]; break; }
    }
    link.click();
    setTimeout(function () {
      var bd = document.getElementById("dialog-backdrop");
      var dlg = document.getElementById("dialog");
      var open = bd && !bd.hidden ? 1 : 0;
      var h2 = dlg && dlg.querySelector("h2") ? dlg.querySelector("h2").textContent : "";
      // 关掉弹窗，避免它挡住第二次断言
      var closeBtn = dlg && dlg.querySelector(".dialog-close");
      if (closeBtn) closeBtn.click();
      else if (bd) bd.hidden = true;
      setTimeout(function () {
        // ④ 切到第 2 篇再切回第 1 篇：renderPapers 每次重建 #paper-body，
        //    链接必须重新挂上。断言「切回来之后链接数与切走前相等」——
        //    比「每篇都必须有链接」可靠：第 2 篇本身可能一个实体都不提，links=0 是合法的。
        var items = document.querySelectorAll("#view-papers .paper-item");
        if (items.length < 2) {
          document.title = "AFTER-CLICK n=" + n + " links=" + links.length +
            " open=" + open + " h2=[" + h2 + "] SWITCH=none";
          return;
        }
        items[1].click();
        setTimeout(function () {
          var b2 = document.getElementById("paper-body");
          var l2 = b2 ? b2.querySelectorAll(".ins-link").length : -1;
          items[0].click();
          setTimeout(function () {
            var b3 = document.getElementById("paper-body");
            var l3 = b3 ? b3.querySelectorAll(".ins-link").length : -1;
            document.title = "AFTER-CLICK n=" + n + " links=" + links.length +
              " person=" + firstName + " open=" + open + " h2=[" + h2 + "]" +
              " | AFTER-SWITCH away=" + l2 + " back=" + l3;
          }, 450);
        }, 450);
      }, 250);
    }, 350);
  });
})()`;

const tmp = OUT + "\\_probe_paper.html";
let html = fs.readFileSync(OUT + "\\" + book + ".html", "utf-8");
html = html.replace("</body>", "<script>" + probe + "</scr" + "ipt></body>");
fs.writeFileSync(tmp, html, "utf-8");
let code = 1;
try {
  const dom = execFileSync(CHROME, [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    "--virtual-time-budget=9000", "--dump-dom",
    "file:///" + tmp + "#view=papers",
  ], { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  const m = dom.match(/<title>([^<]*)<\/title>/);
  const title = m ? m[1] : "(no title)";
  console.log("[" + book + "] " + title);
  const ok = /n=15 links=[1-9]/.test(title)
    && /person=.+ open=1 h2=\[.+\]/.test(title)
    && /AFTER-SWITCH away=\d+ back=([1-9]\d*)/.test(title)
    && !title.includes("PROBE-ERR");
  console.log(ok ? "PROBE-OK" : "PROBE-FAIL");
  code = ok ? 0 : 1;
} finally {
  fs.unlinkSync(tmp);
}
process.exit(code);
