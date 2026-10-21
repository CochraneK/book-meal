// 探针：验证「故事」视图里点章号链接真的能弹出该章的 KG 事件。
// 只跑 dump-dom 只能看到静态正文，看不到点击后的弹窗——而弹窗正是这次挂入的核心
// （长文与数据库从此不是两张皮）。所以这里模拟真实点击，再把弹窗内容 dump 出来核对。
//
// 用法：node src/probe_story_refs.js [book] [章号，逗号分隔]
//   例：node src/probe_story_refs.js tiancai 207,1,221
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "tiancai";
const nos = (process.argv[3] || "207,1").split(",").map((s) => s.trim()).filter(Boolean);

let html = fs.readFileSync(`${OUT}\\${book}.html`, "utf8");
const probe = `<script>
window.addEventListener("load", function () {
  try {
    var nos = ${JSON.stringify(nos)};
    var box = document.createElement("div");
    box.id = "probe-box";
    document.body.appendChild(box);
    // 切到故事视图，否则 .ch-ref 不在激活的面板里（虽然 querySelector 仍能拿到，
    // 但按真实用户路径走一遍更稳）
    var tab = document.querySelector('.tab[data-view="story"]');
    if (tab) tab.click();
    nos.forEach(function (no) {
      var a = document.querySelector('.ch-ref[data-no="' + no + '"]');
      box.appendChild(document.createElement("hr"));
      box.appendChild(document.createTextNode("=== 第" + no + "章 ==="));
      if (!a) { box.appendChild(document.createTextNode("页面上没有该章号链接")); return; }
      a.click();
      var d = document.querySelector("#dialog");
      var bd = document.querySelector("#dialog-backdrop");
      box.appendChild(document.createTextNode("弹窗可见=" + (bd && !bd.hidden)));
      box.appendChild(d ? d.cloneNode(true) : document.createTextNode("(弹窗未出现)"));
      if (bd) bd.hidden = true;
    });
    // 结束哨兵：box 是 JS append 到 body 末尾的，序列化后它后面跟着的是
    // </body> 而不是 <script>，所以不能拿「</div><script>」当边界——
    // 那样写永远匹配不上，探针会安静地什么都打印不出来。
    // 另外哨兵必须是纯文本：写成 HTML 注释会被序列化转义成 &lt;!--…--&gt;。
    box.appendChild(document.createTextNode("PROBE-END-SENTINEL"));
  } catch (e) {
    document.title = "PROBE-ERR: " + e.message;
  }
});
</script>`;
html = html.replace("</body>", probe + "</body>");
const tmp = `${OUT}\\_shots\\_probe_story_${book}.html`;
fs.writeFileSync(tmp, html);

const dom = execFileSync(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=8000", "--dump-dom",
  "file:///" + tmp.replace(/\\/g, "/") + "#view=story",
], { encoding: "utf8", maxBuffer: 1024 * 1024 * 200 });

if (/PROBE-ERR/.test(dom)) {
  // 注意：不能直接 test 整个 dom——探针源码本身就被注入页面，dom 里永远含着
  // "PROBE-ERR" 这串字面量，那样写会恒报错。只认 document.title。
  const t = /<title>([\s\S]*?)<\/title>/.exec(dom);
  const msg = t ? t[1] : "(未拿到 title)";
  if (/^PROBE-ERR/.test(msg)) {
    console.log("PROBE-ERR：" + msg.replace(/^PROBE-ERR:?\s*/, ""));
    process.exit(1);
  }
}
const m = dom.match(/<div id="probe-box">([\s\S]*?)PROBE-END-SENTINEL/);
const seg = m ? m[0] : "(未找到 probe-box)";
if (!m) {
  console.log("(探针未取到内容：probe-box 没进 dump，或结束哨兵缺失)");
}
// 只打印关键片段：每章的标题行 + 事件条数 + 前两条事件名
const blocks = seg.split("=== 第").slice(1);
blocks.forEach(function (b) {
  const head = "=== 第" + b.split("===")[0] + "===";
  const noLink = /没有该章号链接/.test(b);
  const visible = /弹窗可见=true/.test(b);
  const cnt = /KG 收录该章事件 <b>(\d+)<\/b> 条/.exec(b);
  const title = /<h3[^>]*>([^<]*)<\/h3>/.exec(b);
  const rows = (b.match(/<tr><td>([^<]{2,40})<\/td>/g) || []).slice(0, 3)
    .map((r) => r.replace(/<[^>]+>/g, ""));
  console.log(head,
    noLink ? "× 无链接" : (visible ? "√ 弹窗" : "× 弹窗未开"),
    title ? "《" + title[1].trim() + "》" : "",
    cnt ? "事件 " + cnt[1] + " 条" : "（无事件计数）",
    rows.length ? "| " + rows.join(" / ") : "");
});
fs.unlinkSync(tmp);
