// 调试用（临时）：点人物卡里的章节 chip，验证 gotoChapter 真的弹出该章事件。
// 背景：gotoChapter 原先找 .phase-seg[data-ch=…]，而阶段段用的是 data-ph，
// 所以永远是 null —— 一个安静的死按钮。现已改为直接弹该章事件。
const fs = require("fs");
const { execFileSync } = require("child_process");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const book = process.argv[2] || "tiancai";

let html = fs.readFileSync(`${__dirname}/../out/${book}.html`, "utf8");
const probe = `<script>
window.__errs = [];
window.addEventListener("error", function (e) { window.__errs.push(String(e.message)); });
window.addEventListener("load", function () {
  var out = [];
  try {
    // 人物卡是翻牌结构，详情弹窗由卡内的 data-detail「详情」chip 触发
    var person = document.querySelector("#view-characters [data-detail]");
    out.push("详情入口=" + (person ? person.getAttribute("data-detail") : "NONE"));
    if (!person) throw new Error("没有详情入口");
    person.click();
    var d0 = document.querySelector("#dialog");
    out.push("弹窗文本=" + (d0 ? d0.textContent.replace(/\s+/g, " ").slice(0, 160) : "NONE"));
    var chips = document.querySelectorAll("#dialog .chip-link[data-ch]");
    out.push("弹窗内章节chip数=" + chips.length);
    if (!chips.length) throw new Error("弹窗里没有章节 chip");
    var c = chips[chips.length - 1];
    out.push("点的chip data-ch=" + c.getAttribute("data-ch") + " 显示=" + c.textContent.trim());
    c.click();
    var bd = document.querySelector("#dialog-backdrop");
    var d = document.querySelector("#dialog");
    out.push("弹窗=" + (bd && !bd.hidden ? "开" : "未开"));
    out.push("标题=" + (d && d.querySelector("h3") ? d.querySelector("h3").textContent.trim() : "(无h3)"));
    out.push("摘要=" + (d ? d.textContent.replace(/\s+/g, " ").slice(0, 140) : ""));
  } catch (e) {
    out.push("ERR " + e.name + ": " + e.message);
  }
  out.push("pageErrors=" + JSON.stringify(window.__errs || []));
  document.title = out.join(" ||| ");
});
</script>`;
html = html.replace("</body>", probe + "</body>");
const tmp = `${__dirname}/../out/_shots/_dbg_chip_${book}.html`;
fs.writeFileSync(tmp, html);
const dom = execFileSync(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=8000",
  "--dump-dom", "file:///" + tmp.replace(/\\/g, "/") + "#view=characters",
], { encoding: "utf8", maxBuffer: 1 << 28 });
const m = /<title>([\s\S]*?)<\/title>/.exec(dom);
console.log(m ? m[1].split(" ||| ").join("\n") : "(no title)");
