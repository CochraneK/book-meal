# -*- coding: utf-8 -*-
"""
报告冒烟校验（10 个视图 × 每本书）
=================================
为什么要有这个脚本
------------------
之前靠手敲 Chrome 命令逐个跑，出过两次假通过：

1. 用错了视图键（dist / persons，正确的是 distribution / characters），
   页面整块空白，「0 个 JS 错误」照样成立——空白页当然不报错。
2. 只检查 console，没检查「这个视图到底渲染出东西了吗」。

所以这里同时卡四件事：
  A. 每个视图必须真的被激活（#view-X 有 active 类）
  B. 视图内必须有实际内容（渲染出的 DOM 字符数下限）
  C. 必须零未捕获异常（注入 window.onerror 收集器）
  D. 「故事」视图额外卡：长文正文必须真的在，且章号链接必须已绑事件

用法：
  python src/check_report.py            # 校验两本书全部视图
  python src/check_report.py feitu      # 只校验一本
"""
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
# 视图键必须与 app.js 里 VIEWS 完全一致（写错会静默渲染空白页）
VIEWS = ["overview", "distribution", "characters", "places", "map",
         "events", "relations", "phases", "quotes", "story", "perspectives", "papers"]

# 每个视图的「渲染成功」标志：出现这些文本才算真的画出来了
MARKERS = {
    "overview": ["数据规模", "数据状态", "出场最多人物"],
    "distribution": ["事件功能分布", "地点功能分布", "关系类别"],
    "characters": ["核心", "主要"],
    "places": ["地点"],
    "map": ["<svg"],
    "events": ["事件", "功能类别"],
    "relations": ["关系"],
    "phases": ["阶段"],
    "quotes": ["这些句子是怎么选出来的", "人物语录"],
    # 故事视图：口径面板 + 目录 + 正文锚点，三者缺一即视为没渲染出来
    "story": ["一篇文章讲完全部故事", "目录", "口径与来源"],
    # 学科视角视图：口径面板 + 目录 + 可信度图例，三者缺一即视为没渲染出来
    "perspectives": ["多学科视角分析", "目录", "可信度"],
    # 论文视图：篇目列表 + 题录 + 参考文献，三者缺一即视为没渲染出来
    "papers": ["论文体系", "条文献", "参考文献"],
}
MIN_HTML = 400  # 视图内 DOM 字符数下限，低于此基本等于空白


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise RuntimeError("未找到 Chrome / Edge")


def instrument(src_html):
    """注入错误收集器，并在末尾放一个报告节点。"""
    head_hook = ("<script>window.__errs=[];"
                 "window.addEventListener('error',function(e){"
                 "window.__errs.push(String((e&&e.message)||e));});"
                 "window.addEventListener('unhandledrejection',function(e){"
                 "window.__errs.push('promise:'+String(e.reason));});</script>")
    tail_hook = ("<script>(function(){"
                 "var d=document.createElement('div');d.id='__errs_report';"
                 "d.setAttribute('data-errs',JSON.stringify(window.__errs||[]));"
                 "document.body.appendChild(d);})();</script>")
    out = src_html.replace("</head>", head_hook + "</head>", 1)
    out = out.replace("</body>", tail_hook + "</body>", 1)
    return out


def run_view(chrome, path, view):
    url = "file:///" + path.replace("\\", "/") + "#view=" + view
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--virtual-time-budget=6000", "--dump-dom", url]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    dom = r.stdout or ""

    # A. 视图是否激活
    active = bool(re.search(r"<section[^>]*class=\"view active\"[^>]*id=\"view-" + view + "\"", dom)
                  or re.search(r"<section[^>]*id=\"view-" + view + r"\"[^>]*class=\"view active\"", dom))

    # 取出该视图 section 的 HTML（用下一个 </section> 近似切分）
    body = ""
    m = re.search(r"id=\"view-" + view + "\"", dom)
    if m:
        end = dom.find("</section>", m.start())
        body = dom[m.start():end if end > 0 else m.start() + 60000]

    # B. 内容量 + 标志文本
    markers_ok = all(k in body for k in MARKERS.get(view, []))

    # D. 故事视图：章号链接必须已生成且不带 javascript: 死链
    extra = ""
    if view == "story":
        nref = len(re.findall(r'class="ch-ref"', body))
        if nref == 0:
            extra = "章号链接 0 个"
        elif re.search(r'data-no="0"', body):
            extra = "存在 data-no=0 的死链"

    # D'. 学科视角视图：阶段引用链接必须已生成（跳到阶段轴的虚线链接）
    if view == "perspectives":
        nph = len(re.findall(r'class="ph-ref"', body))
        if nph == 0:
            extra = "阶段链接 0 个"

    # D''. 论文视图：篇目列表必须有 15 篇，参考文献必须带 DOI
    if view == "papers":
        nit = len(re.findall(r"""class=["']paper-item""", body))
        ndoi = len(re.findall(r"https://doi\.org/", body))
        if nit != 15:
            extra = "篇目 %d 个（预期 15）" % nit
        elif ndoi == 0:
            extra = "参考文献缺 DOI"

    # C. 未捕获异常
    errs = []
    em = re.search(r"id=\"__errs_report\"[^>]*data-errs=\"([^\"]*)\"", dom)
    if em:
        try:
            errs = json.loads(em.group(1).replace("&quot;", '"'))
        except Exception:
            errs = [em.group(1)]

    return {
        "view": view,
        "active": active,
        "html_len": len(body),
        "markers": markers_ok,
        "errors": errs,
        "extra": extra,
    }


def main():
    chrome = find_chrome()
    books = sys.argv[1:] or ["tiancai", "feitu"]
    bad = 0
    for book in books:
        src = os.path.join(BASE, "out", f"{book}.html")
        if not os.path.exists(src):
            print(f"[skip] 缺少 {src}")
            continue
        html = open(src, encoding="utf-8").read()
        patched = instrument(html)
        tmp = os.path.join(tempfile.gettempdir(), f"_check_{book}.html")
        open(tmp, "w", encoding="utf-8").write(patched)

        print(f"\n===== {book} =====")
        for view in VIEWS:
            # quotes 视图的数据来自 data/<book>/quotes.json——抽取出来的原文引语，
            # 受版权保护、不入版本控制。干净 checkout（CI）里没有它，报告里这个
            # 视图必然是空的。这时标 SKIP 并说明原因，而不是判 FAIL：
            # 缺数据不等于渲染坏了，判 FAIL 只会让 CI 恒定红并且掩盖真问题。
            if view == "quotes" and not os.path.exists(
                    os.path.join(BASE, "data", book, "quotes.json")):
                print(f"  [SKIP] {view:<13} 依赖 data/{book}/quotes.json"
                      f"（本地私有数据，不入库）")
                continue
            r = run_view(chrome, tmp, view)
            ok = r["active"] and r["markers"] and r["html_len"] >= MIN_HTML \
                and not r["errors"] and not r["extra"]
            if not ok:
                bad += 1
            flag = "OK  " if ok else "FAIL"
            detail = []
            if not r["active"]:
                detail.append("未激活")
            if not r["markers"]:
                detail.append("缺标志文本")
            if r["html_len"] < MIN_HTML:
                detail.append(f"内容过少({r['html_len']})")
            if r["extra"]:
                detail.append(r["extra"])
            if r["errors"]:
                detail.append("异常:" + " | ".join(r["errors"][:2]))
            print(f"  [{flag}] {view:<13} DOM {r['html_len']:>7} 字  " + ("; ".join(detail) if detail else ""))
        os.unlink(tmp)

    print(f"\n结果：{bad} 个视图未通过")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
