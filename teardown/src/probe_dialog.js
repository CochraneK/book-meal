// 临时探针：验证「点击后」才渲染的内容（人物详情弹窗）。
// 单靠 dump-dom 拿不到交互态，所以在页面加载后直接调用 showPerson 复现已定義的弹窗，
// 再把结果 dump 出来检查。用完即删。
const fs = require("fs");
const { execFileSync } = require("child_process");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const OUT = __dirname + "\\..\\out";
const book = process.argv[2] || "feitu";
const names = (process.argv[3] || "祝宁").split(",");

let html = fs.readFileSync(`${OUT}\\${book}.html`, "utf8");
const probe = `<script>
window.addEventListener("load", function () {
  try {
    var names = ${JSON.stringify(names)};
    var box = document.createElement("div");
    box.id = "probe-box";
    document.body.appendChild(box);
    // showPerson 在闭包里，外部调不到 —— 所以模拟真实点击：
    // 先切到总览，点列表里对应人物的行。（总览 Top12 正好含主角）
    names.forEach(function (n) {
      var target = null;
      document.querySelectorAll("[data-person]").forEach(function (el) {
        if (el.dataset.person === n && !target) target = el;
      });
      box.appendChild(document.createElement("hr"));
      if (!target) {
        box.appendChild(document.createTextNode("=== " + n + " === 页面上没找到该人物的可点元素"));
        return;
      }
      target.click();
      var d = document.querySelector(".dialog-backdrop, .dialog");
      box.appendChild(document.createTextNode("=== " + n + " ==="));
      box.appendChild(d ? d.cloneNode(true) : document.createTextNode("(弹窗未出现)"));
    });
  } catch (e) {
    document.title = "PROBE-ERR: " + e.message;
  }
});
</script>`;
html = html.replace("</body>", probe + "</body>");
const tmp = `${OUT}\\_shots\\_probe_${book}.html`;
fs.writeFileSync(tmp, html);

const dom = execFileSync(CHROME, [
  "--headless=new", "--disable-gpu", "--virtual-time-budget=6000", "--dump-dom",
  "file:///" + tmp.replace(/\\/g, "/"),
], { encoding: "utf8", maxBuffer: 1024 * 1024 * 200 });

const t = (dom.match(/<title>([^<]*)<\/title>/) || [])[1];
if (t && t.startsWith("PROBE-ERR")) {
  console.log("探针报错:", t);
  process.exit(1);
}
const i = dom.indexOf('id="probe-box"');
console.log(dom.slice(i, i + 4000).replace(/<[^>]*>/g, "|").replace(/\|{2,}/g, "|"));
