// 探针：验证「回顶按钮」（src/probe_back_top.js）
// 背景：故事/学科视角两个长文视图 7 万字单页滚动，目录在顶部，
//       滚到中间后回不去（ui_audit §3-6）。修复：#back-top 滚动过 800px 出现，
//       点击平滑回顶。
// 用法：node src/probe_back_top.js [book]
// 断言：① #back-top 存在；② 未滚动时隐藏、滚到 3000px 后获得 .show 类；
//       ③ 点击后确实向 window.scrollTo 发起了 top=0 的回顶调用。
// 两个无头环境限制（实测，勿判为应用 bug）：
//   · --dump-dom 模式下程序化 window.scrollTo 只改 scrollY、**不派发 scroll 事件**
//     （无渲染帧，实测 fired=0），所以探针在滚动后手动 dispatchEvent 一次，
//     验证的是「事件处理函数按 scrollY 切类」这个逻辑本身；
//   · 平滑滚动（behavior:smooth）依赖动画帧，无头模式下不推进，
//     所以不断言最终 scrollY，断言「发起了回顶」这个意图。
// 因此 app.js 的 scroll 处理里也不能包 requestAnimationFrame（同样不产帧）——
// 浏览器对 scroll 事件本就已节流，直接同步切类即可（v3.7 修）。
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "feitu";
// 注意：Chrome 必须加载**注入过探针的 tmp 副本**，不是 out/ 下的原件
// （曾经在这里误传 url 指向原件，探针脚本根本没被执行，还显示原始标题）。
const url = "file:///" + OUT + "\\_probe_backtop.html#view=story";

const probe = `
(function () {
  function fail(msg) { document.title = "PROBE-ERR: " + msg; }
  // 记录 scrollTo 的 top 参数（支持 (x,y) 与 ({top}) 两种签名）
  var calls = [];
  var orig = window.scrollTo.bind(window);
  window.scrollTo = function (a, b) {
    var top = (b === undefined && a && typeof a === "object") ? a.top : b;
    calls.push(String(top));
    return orig.apply(null, arguments);
  };
  setTimeout(function () {
    var btn = document.getElementById("back-top");
    if (!btn) { fail("no #back-top element"); return; }
    var hidden0 = btn.classList.contains("show") ? 0 : 1;
    orig(0, 3000);   // 原生滚动（不进记录，避免污染 calls）
    // 无头 dump-dom 不派发 scroll 事件，手动补一次（见文件头说明）
    window.dispatchEvent(new Event("scroll"));
    setTimeout(function () {
      var shown = btn.classList.contains("show") ? 1 : 0;
      if (!shown) { document.title = "PROBE-ERR: no .show after scroll 3000"; return; }
      btn.click();
      setTimeout(function () {
        document.title = "BACK-TOP hidden0=" + hidden0 + " shown=" + shown +
          " calls=[" + calls.join(",") + "]";
      }, 600);
    }, 500);
  }, 800);
})();`;

const tmp = OUT + "\\_probe_backtop.html";
let html = fs.readFileSync(OUT + "\\" + book + ".html", "utf-8");
html = html.replace("</body>", "<script>" + probe + "</scr" + "ipt></body>");
fs.writeFileSync(tmp, html, "utf-8");
let code = 1;   // process.exit 不会执行 finally，所以先记结果、最后退出
try {
  const dom = execFileSync(CHROME, [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    "--virtual-time-budget=10000", "--dump-dom", url,
  ], { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  const m = dom.match(/<title>([^<]*)<\/title>/);
  const title = m ? m[1] : "(no title)";
  console.log("[" + book + "] " + title);
  // calls 里必须出现一次 top=0（点击回顶发起的滚动）
  const ok = /BACK-TOP hidden0=1 shown=1 calls=\[[\d,]*\b0\b[\d,]*\]/.test(title)
    && !title.includes("PROBE-ERR");
  console.log(ok ? "PROBE-OK" : "PROBE-FAIL");
  code = ok ? 0 : 1;
} finally {
  fs.unlinkSync(tmp);
}
process.exit(code);
