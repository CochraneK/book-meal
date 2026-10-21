// 调试用（临时）：点开一个阶段，验证「本阶段事件」表真的有数据。
// 背景：payload 的 chapters 字段曾是章节 key 而非 index，而 renderPhaseBody 用
// `i >= ph.s && i <= ph.e` 做数字比较，字符串恒 false → 整张表是空的。
const fs = require("fs");
const { execFileSync } = require("child_process");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const book = process.argv[2] || "tiancai";
const ph = process.argv[3] || "0";

let html = fs.readFileSync(`${__dirname}/../out/${book}.html`, "utf8");
const probe = `<script>
window.addEventListener("load", function () {
  var out = [];
  try {
    var seg = document.querySelectorAll('.phase-seg[data-ph="${ph}"]');
    out.push("segments=" + seg.length);
    if (!seg.length) throw new Error("没有该阶段段");
    seg[0].click();
    var body = document.querySelector(".phase-body") || document.getElementById("phase-body");
    out.push("phaseBody=" + (body ? body.textContent.length : "NONE"));
    if (body) {
      var rows = body.querySelectorAll("tr");
      out.push("rows=" + rows.length);
      var txt = body.textContent.replace(/\\s+/g, " ");
      out.push("head=" + txt.slice(0, 260));
      var bad = body.querySelectorAll("td");
      var keyLike = 0;
      for (var i = 0; i < bad.length; i++) {
        if (/${book}-c/.test(bad[i].textContent)) keyLike++;
      }
      out.push("裸章节key单元格=" + keyLike);
    }
  } catch (e) {
    out.push("ERR " + e.name + ": " + e.message);
  }
  document.title = out.join(" ||| ");
});
</script>`;
html = html.replace("</body>", probe + "</body>");
const tmp = `${__dirname}/../out/_shots/_dbg_phase_${book}.html`;
fs.writeFileSync(tmp, html);
const dom = execFileSync(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=8000",
  "--dump-dom", "file:///" + tmp.replace(/\\/g, "/") + "#view=phases",
], { encoding: "utf8", maxBuffer: 1 << 28 });
const m = /<title>([\s\S]*?)<\/title>/.exec(dom);
console.log(m ? m[1].split(" ||| ").join("\n") : "(no title)");
