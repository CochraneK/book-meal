// 探针：验证「打印本页卡片」按钮的作用域收窄（src/probe_print_cards.js）
// 背景：此前 printCards() 把卡片克隆进 #print-area 后直接 window.print()，
// 但 CSS 无 #print-area 规则、@media print 又输出全部 11 个视图
// （实测 Ctrl+P 得 69 页 / 10.8MB）——按钮文案与行为不符。
// 现行为：点击后 body 加 .printing-cards（@media print 下隐藏 #app，
// 只留 #print-area）；未进人物视图时 toast 拦截。
// 用法：node src/probe_print_cards.js [book]
// 断言：① 按钮存在且点击后 body.printing-cards 生效；② #print-area 卡片数
//       == 人物视图卡片的 DOM 数；③ window.print 被调用且只被调用一次；
//       ④ 无头环境下 window.print 被 monkey-patch 成记录哨兵，不会真的打印。
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "tiancai";
const url = "file:///" + OUT + "\\" + book + ".html#view=characters";

// 注入脚本：拦 window.print、等 boot 渲染出按钮、点按钮、把结果写进 title（纯文本哨兵）
const probe = `
(function () {
  var printCalls = 0;
  window.print = function () { printCalls++; document.title = "PRINT-CALLED"; };
  function snap(tag) {
    var cards = document.querySelectorAll("#print-area .poke-card").length;
    var grid = document.querySelectorAll("#view-characters .poke-card").length;
    var cls = document.body.className;
    document.title = tag + " cards=" + cards + " grid=" + grid +
      " prints=" + printCalls + " cls=[" + cls + "]";
  }
  // 按钮由 renderCharacters() 在 boot 时生成——必须等 boot 跑完再点
  var tries = 0;
  var iv = setInterval(function () {
    var btn = document.getElementById("print-cards");
    if (btn) {
      clearInterval(iv);
      btn.click();
      snap("AFTER-CLICK");
    } else if (++tries > 100) {
      clearInterval(iv);
      document.title = "PROBE-ERR: no print-cards button after wait";
    }
  }, 50);
})();`;

// 用临时文件注入（--dump-dom 拿不到交互后状态，注入式探针同 probe_phase_refs.js 套路）
const tmp = OUT + "\\_probe_print.html";
let html = fs.readFileSync(OUT + "\\" + book + ".html", "utf-8");
html = html.replace("</body>", "<script>" + probe + "</scr" + "ipt></body>");
fs.writeFileSync(tmp, html, "utf-8");
let code = 1;   // process.exit 不会执行 finally，所以先记结果、最后退出
try {
  const dom = execFileSync(CHROME, [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    "--virtual-time-budget=6000", "--dump-dom",
    "file:///" + tmp,
  ], { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  const m = dom.match(/<title>([^<]*)<\/title>/);
  const title = m ? m[1] : "(no title)";
  console.log("[" + book + "] " + title);
  const ok = /AFTER-CLICK cards=\d+ grid=\d+ prints=1 cls=\[[^\]]*printing-cards[^\]]*\]/.test(title)
    && !title.includes("PROBE-ERR");
  const cards = (title.match(/cards=(\d+)/) || [])[1];
  const grid = (title.match(/grid=(\d+)/) || [])[1];
  const same = cards && grid && cards === grid;
  console.log(ok && same ? "PROBE-OK" : "PROBE-FAIL");
  code = ok && same ? 0 : 1;
} finally {
  fs.unlinkSync(tmp);
}
process.exit(code);
