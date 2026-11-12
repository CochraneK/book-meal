# -*- coding: utf-8 -*-
"""Headless browser test for actual world switching and finished Pages artifact."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

page=Path(sys.argv[1] if len(sys.argv)>1 else ".ci/site/worlds/index.html").resolve()
browser=(shutil.which("google-chrome") or shutil.which("chromium")
         or shutil.which("chromium-browser") or shutil.which("chrome"))
if not page.is_file():
    print("[FAIL] missing world preview:",page)
    raise SystemExit(1)
if not browser:
    print("[SKIP] browser absent; static tests still cover generated HTML")
    raise SystemExit(0)


def run(book, title, expected_route):
    with tempfile.TemporaryDirectory(prefix="world-ui-") as home:
        result=subprocess.run([
            browser,"--headless=new","--no-sandbox","--disable-gpu",
            "--disable-dev-shm-usage","--disable-background-networking",
            "--disable-extensions","--virtual-time-budget=1200",
            "--user-data-dir="+home,"--dump-dom",
            page.as_uri()+"?book="+book
        ],capture_output=True,text=True,timeout=35)
    doc=result.stdout
    # Restrict to the actual rendered stage, never templates or embedded scripts.
    m=re.search(r'<div id="world-view">([\s\S]*?)<div class="footer">',doc)
    stage=m.group(1) if m else ""
    active=re.search(r'<a[^>]*data-book="'+re.escape(book)+r'"[^>]*aria-current="page"',doc)
    # Browser may normalize attribute order.
    if not active:
        active=re.search(r'<a[^>]*aria-current="page"[^>]*data-book="'+re.escape(book)+r'"',doc)
    ok=(result.returncode==0 and
        bool(re.search(r'<h2 id="world-title"[^>]*>'+re.escape(title)+r'</h2>',stage))
        and expected_route in stage and bool(active))
    print("[OK]" if ok else "[FAIL]",book,"switch & active DOM")
    if not ok:
        print("rc=",result.returncode,"stage-tail=",stage[-900:],"stderr=",result.stderr[-400:])
    return ok


assert run("ming","明朝那些事儿","../ming/index.html#view=visuals")
assert run("sanggan","太阳照在桑乾河上","../books/sanggan/index.html")
assert run("ordinary-world","平凡的世界","查看书籍建档页")
print("[OK] all world preview smoke checks")

# Keep visual evidence separate from source control. Four screenshots are taken
# from the same generated preview tested above; they contain public UI only.
shots=Path(".ci/world-preview-screenshots")
shots.mkdir(parents=True,exist_ok=True)
for book in ("ming","sanggan"):
    for view,size in (("desktop","1280,820"),("mobile","390,844")):
        dest=(shots/(book+"-"+view+".png")).resolve()
        with tempfile.TemporaryDirectory(prefix="world-shot-") as home:
            result=subprocess.run([
                browser,"--headless=new","--no-sandbox","--disable-gpu",
                "--disable-dev-shm-usage","--disable-background-networking",
                "--disable-extensions","--hide-scrollbars","--force-device-scale-factor=1",
                "--virtual-time-budget=1500","--window-size="+size,
                "--user-data-dir="+home,"--screenshot="+str(dest),
                page.as_uri()+"?book="+book
            ],capture_output=True,text=True,timeout=35)
        if result.returncode!=0 or not dest.is_file() or dest.stat().st_size<1000:
            raise AssertionError("screenshot failed: "+str(dest)+" "+result.stderr[-250:])
        print("[OK] screenshot",dest.name,dest.stat().st_size,"bytes")
