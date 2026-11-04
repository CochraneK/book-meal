# -*- coding: utf-8 -*-
"""
体验基建回归自检（teardown 模板）
================================
为什么要有第二个自检
--------------------
src/check_report.py 卡的是「12 个视图渲染得出来吗」，属于产出物冒烟。
2026-10-28 ~ 11-02 陆续加进模板的这批能力，此前全靠人工在 Playwright 里
点一遍确认，CI 里一条断言都没有：

    启动守卫 / 懒渲染缓存 / 人物与地点分页 / 别名归一搜索 /
    翻面卡 inert / beforeprint 打印补齐 / skip-link 与 live region

任何一次前端改动都可能悄悄把其中一项弄坏，而 check_report.py 照样全绿
（视图渲染得出来 ≠ 基础设施还在）。这个脚本把那批人工验证固化下来。

实现沿用 check_report.py 的机制：往产物里注入一段探针脚本，用无头 Chrome
--dump-dom 取回快照，探针把断言结果写进 #__exp_report[data-result]。
不引入 Playwright / 第三方依赖，CI 上复用 browser-actions/setup-chrome。

用法：
  python src/check_experience.py              # 校验 out/ 下全部可用书
  python src/check_experience.py tiancai      # 只校验一本
"""
import html as html_mod
import json
import os
import re
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
DEFAULT_BOOKS = ["tiancai", "feitu"]

# 探针在 load 之后执行（boot 走 DOMContentLoaded，须等它跑完）。
# 结果全部写进 DOM 节点，--dump-dom 就能把断言带回来。
PROBE_JS = r"""
(function () {
  function run() {
    var r = {};
    try {
      r.ready = (window.__KG_READY === true);
      r.failbar = document.querySelectorAll('.fail-bar').length;
      r.book = document.documentElement.getAttribute('data-book');
      r.skipLink = !!document.querySelector('.skip-link');
      r.mainTabindex = (document.getElementById('views') || {}).getAttribute
        ? document.getElementById('views').getAttribute('tabindex') : null;
      var toast = document.getElementById('toast-bar');
      r.ariaLive = toast ? toast.getAttribute('aria-live') : null;

      // 懒渲染：首屏只应渲染总览，未访问过的视图 DOM 必须还是空的
      var papers = document.getElementById('view-papers');
      r.lazyEmpty = !!papers && papers.innerHTML.length === 0;
      var overview = document.getElementById('view-overview');
      r.overviewReady = !!overview && overview.innerHTML.length > 400;

      // 打印补齐：beforeprint 之后 12 个视图一个都不能空
      window.dispatchEvent(new Event('beforeprint'));
      var empties = [];
      Array.prototype.forEach.call(document.querySelectorAll('.view'), function (v) {
        if (!v.innerHTML.length) empties.push(v.id);
      });
      r.printEmpty = empties;
      r.viewCount = document.querySelectorAll('.view').length;

      // 分页器：补渲染后人物 / 地点 / 事件三处都应存在
      r.pager = {
        char: !!document.getElementById('char-next'),
        place: !!document.getElementById('place-next'),
        event: !!document.getElementById('ev-next')
      };

      // 翻面卡 inert：初始背朝前（back inert），翻面后反转
      var card = document.querySelector('#view-characters .poke-card');
      if (card) {
        var f = card.querySelector('.poke-front');
        var b = card.querySelector('.poke-back');
        r.inertBefore = { f: !!f.inert, b: !!b.inert };
        card.click();
        r.inertAfter = {
          f: !!f.inert, b: !!b.inert,
          flipped: card.classList.contains('flipped')
        };
      } else {
        r.cardMissing = true;
      }

      // 别名索引：数据层必须真的注入了（否则归一搜索是空转）
      r.aliasCount = (window.DATA && DATA.alias_index)
        ? Object.keys(DATA.alias_index).length : -1;
    } catch (e) {
      r.probeError = String((e && e.message) || e);
    }
    var d = document.createElement('div');
    d.id = '__exp_report';
    d.setAttribute('data-result', JSON.stringify(r));
    (document.body || document.documentElement).appendChild(d);
  }
  if (document.readyState === 'complete') {
    setTimeout(run, 50);
  } else {
    window.addEventListener('load', function () { setTimeout(run, 50); });
  }
})();
"""


def find_chrome():
    env = os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    import shutil
    for name in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    for p in CHROME_CANDIDATES + [
        "/usr/bin/google-chrome", "/usr/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]:
        if os.path.exists(p):
            return p
    return None


def instrument(src_html):
    return src_html.replace("</body>", "<script>" + PROBE_JS + "</script></body>", 1)


def source_assertions():
    """源码级断言：防止有人把基础设施整段删掉而运行时探针恰好没覆盖到。"""
    app = os.path.join(BASE, "web", "js", "app.js")
    tpl = os.path.join(BASE, "web", "template", "index.html")
    css = os.path.join(BASE, "web", "css", "app.css")
    checks = [
        (app, "renderAllForPrint", "打印补齐"),
        (app, "function matchesQuery", "别名归一搜索"),
        (app, "var rendered = {}", "懒渲染缓存"),
        (app, "function bootFail", "启动失败提示"),
        (app, "window.addEventListener(\"beforeprint\"", "beforeprint 绑定"),
        (app, "charPage", "人物分页"),
        (app, "placePage", "地点分页"),
        (tpl, "__KG_READY", "启动守卫"),
        (tpl, "skip-link", "跳转链接"),
        (css, "prefers-reduced-motion", "减弱动效"),
        (css, "focus-visible", "键盘焦点环"),
    ]
    out = []
    for path, token, label in checks:
        try:
            ok = token in open(path, encoding="utf-8").read()
        except OSError:
            ok = False
        out.append((label, ok, path if not ok else ""))
    return out


def evaluate(r):
    """把探针结果展开成 (断言名, 是否通过, 说明) 列表。"""
    out = []

    def chk(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    def get(key, default=None):
        return r.get(key, default) if isinstance(r, dict) else default

    chk("启动守卫 __KG_READY", get("ready") is True, str(get("ready")))
    chk("无误报错误条", get("failbar") == 0, "fail-bar=%s" % get("failbar"))
    chk("探针自身无异常", not get("probeError"), str(get("probeError") or ""))
    chk("data-book 主题标记", bool(get("book")), str(get("book")))
    chk("skip-link 存在", get("skipLink") is True)
    chk("main tabindex=-1", get("mainTabindex") == "-1", str(get("mainTabindex")))
    chk("toast aria-live", get("ariaLive") == "polite", str(get("ariaLive")))
    chk("首屏总览已渲染", get("overviewReady") is True)
    chk("懒渲染：未访问视图为空", get("lazyEmpty") is True)
    chk("视图数=12", get("viewCount") == 12, str(get("viewCount")))
    empties = get("printEmpty", ["<探针未返回>"])
    chk("beforeprint 补齐全部视图", isinstance(empties, list) and not empties,
        "空白视图：" + (", ".join(empties) if empties else "无"))
    pager = get("pager", {}) or {}
    chk("人物分页器", pager.get("char") is True, str(pager))
    chk("地点分页器", pager.get("place") is True, str(pager))
    chk("事件分页器", pager.get("event") is True, str(pager))
    chk("人物卡存在", not get("cardMissing"))
    before = get("inertBefore", {}) or {}
    after = get("inertAfter", {}) or {}
    chk("翻转前：背面 inert", before.get("f") is False and before.get("b") is True,
        str(before))
    chk("翻转后：正面 inert", after.get("f") is True and after.get("b") is False
        and after.get("flipped") is True, str(after))
    chk("alias_index 已注入", isinstance(get("aliasCount"), int) and get("aliasCount") > 0,
        "别名数 %s" % get("aliasCount"))
    return out


def run_book(chrome, book):
    src = os.path.join(BASE, "out", book + ".html")
    if not os.path.exists(src):
        return None
    patched = instrument(open(src, encoding="utf-8").read())
    tmp = os.path.join(tempfile.gettempdir(), "_exp_" + book + ".html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(patched)
    url = "file:///" + tmp.replace("\\", "/")
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--virtual-time-budget=9000", "--dump-dom", url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        dom = r.stdout or ""
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    m = re.search(r"id=\"__exp_report\"[^>]*data-result=\"([^\"]*)\"", dom)
    if not m:
        return {"__parse_error__": "探针节点未出现（页面可能未执行 JS 或被裁剪）"}
    try:
        return json.loads(html_mod.unescape(m.group(1)))
    except Exception as e:
        return {"__parse_error__": "探针结果无法解析：%s" % e}


def main():
    chrome = find_chrome()
    if not chrome:
        print("[FAIL] 未找到 Chrome / Chromium；CI 由 browser-actions/setup-chrome 提供，"
              "本机可用 CHROME_BIN=<路径> 指定。")
        return 1

    bad = 0
    print("=== 源码级断言 ===")
    for label, ok, detail in source_assertions():
        if not ok:
            bad += 1
        print("  [%s] %s%s" % ("OK  " if ok else "FAIL", label,
                               "  → " + detail if detail else ""))

    books = sys.argv[1:] or DEFAULT_BOOKS
    for book in books:
        src = os.path.join(BASE, "out", book + ".html")
        if not os.path.exists(src):
            print("\n[skip] 缺少 %s" % src)
            continue
        print("\n=== 运行时断言：%s ===" % book)
        r = run_book(chrome, book)
        if r is None or "__parse_error__" in r:
            bad += 1
            print("  [FAIL] %s" % (r or {}).get("__parse_error__", "未知"))
            continue
        if r.get("probeError"):
            print("  [warn] 探针捕获异常：%s" % r["probeError"])
        for label, ok, detail in evaluate(r):
            if not ok:
                bad += 1
            line = "  [%s] %s" % ("OK  " if ok else "FAIL", label)
            if detail and not ok:
                line += "  → " + str(detail)
            print(line)

    print("\n结果：%d 项未通过" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
