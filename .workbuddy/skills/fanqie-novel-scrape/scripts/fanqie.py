# -*- coding: utf-8 -*-
"""
番茄小说抓取器
==============
把番茄小说（fanqienovel.com）的公开章节抓成本地 UTF-8 文本，供 book-meal 拆书流水线使用。

用法
----
    # 抓整本（book_id 或任意番茄链接都行）
    python fanqie.py --book 7143038691944959011 --out books/riye

    # 先试跑 5 章
    python fanqie.py --book https://fanqienovel.com/page/7143038691944959011 --out /tmp/t --limit 5

    # 只抓区间（含两端，1-based）
    python fanqie.py --book 7143038691944959011 --out books/riye --start 100 --end 200

    # 只要目录，不下正文
    python fanqie.py --book 7143038691944959011 --toc-only

    # 用自己账号的 Cookie 抓已购章节
    python fanqie.py --book 7143038691944959011 --out books/riye --cookie-file cookie.txt

产出
----
    <out>/
      chapters/0001.txt     # 每章一个文件：第 1 行标题，其余正文
      <书名>.txt            # 合并全本
      meta.jsonl            # 章节元数据（序号/itemId/标题/字数/分卷/状态）
      meta.json             # 书籍级元数据 + 抓取统计（可直接喂给 make_manifest.py）
      .cache/gidmap.json    # gid -> 汉字 缓存，跨章跨书复用
      .cache/*.woff2        # 页面用到的混淆字体

技术要点
--------
- 目录：GET /api/reader/directory/detail?bookId=<id>，一次返回全部章节（含分卷、标题、itemId）
- 正文：GET /reader/<itemId>，正文在 `div.muye-reader-content` 的 `<p>` 里
- **正文是 PUA 乱码**，必须用 font_deobf 解码；字体全书同一份，解一次即可
- 目录页只给前若干章链接，不能靠它枚举；用目录 API 才拿得全

付费边界（重要，别想着绕）
--------------------------
番茄的 `isChapterLock=1` 表示 VIP 章节。**未登录时页面只渲染几百字试读**，后面接一条
「登录 / 购买」提示。这不是技术障碍，是商业边界：
- 默认行为：只抓免费章，锁定章跳过并在 meta 里记明原因；
- 合法路径：用**你自己账号**的 Cookie（--cookie/--cookie-file）抓你已购买的章节。
脚本不提供、也不应添加任何绕过付费的机制。
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_deobf  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

DIR_API = "https://fanqienovel.com/api/reader/directory/detail?bookId={bid}"
PAGE_URL = "https://fanqienovel.com/page/{bid}"
READER_URL = "https://fanqienovel.com/reader/{item}"

# 试读页的特征词；同时命中「VIP/购买」且正文过短，判为预览而非完整章
WALL_WORDS = ("VIP", "购买")
PREVIEW_CHAR_LIMIT = 700


# ---------------------------------------------------------------- HTTP

def _headers(referer=None, cookie=None):
    h = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9", "Accept": "*/*"}
    if referer:
        h["Referer"] = referer
    if cookie:
        h["Cookie"] = cookie
    return h


def fetch(url, referer=None, retries=3, timeout=25, binary=False, cookie=None):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=_headers(referer, cookie))
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return raw if binary else raw.decode("utf-8", "ignore")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            code = getattr(e, "code", None)
            if code in (404, 403):
                break
            time.sleep(1.2 * (2 ** attempt) + random.random() * 0.4)
    raise RuntimeError(f"fetch failed: {url} -> {last}")


def parse_book_id(s):
    """从 URL / 纯数字 / 带前缀的串里取出 book_id。"""
    s = str(s).strip()
    for pat in (r"/page/(\d+)", r"bookId=(\d+)", r"(\d{10,})"):
        m = re.search(pat, s)
        if m:
            return m.group(1)
    raise ValueError(f"无法从 {s!r} 解析出 book_id")


# ---------------------------------------------------------------- 解析

class ReaderParser(HTMLParser):
    """提取 div.muye-reader-content 内的 <p> 段落，以及 h1.muye-reader-title。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_content = False
        self.depth = 0
        self.in_p = False
        self.buf = []
        self.paras = []
        self.in_title = False
        self.title_buf = []
        self.title = ""

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = d.get("class", "") or ""
        if tag == "div" and not self.in_content and "muye-reader-content" in cls and "noselect" in cls:
            self.in_content = True
            self.depth = 1
            return
        if self.in_content:
            if tag == "div":
                self.depth += 1
            elif tag == "p":
                self.in_p = True
                self.buf = []
        elif tag == "h1" and "muye-reader-title" in cls:
            self.in_title = True
            self.title_buf = []

    def handle_endtag(self, tag):
        if self.in_content:
            if tag == "div":
                self.depth -= 1
                if self.depth <= 0:
                    self.in_content = False
            elif tag == "p" and self.in_p:
                t = "".join(self.buf).strip()
                if t:
                    self.paras.append(t)
                self.in_p = False
        elif tag == "h1" and self.in_title:
            self.title = "".join(self.title_buf).strip()
            self.in_title = False

    def handle_data(self, data):
        if self.in_content and self.in_p:
            self.buf.append(data)
        elif self.in_title:
            self.title_buf.append(data)


def clean_para(t):
    t = t.replace("\u3000", " ").replace("\xa0", " ")
    t = re.sub(r"<!--.*?-->", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def extract_chapter(html_text):
    p = ReaderParser()
    try:
        p.feed(html_text)
    except Exception:
        pass
    paras = [clean_para(x) for x in p.paras]
    paras = [x for x in paras if x and x != "\u200b"]
    return p.title or "", paras


def extract_font_urls(html_text):
    urls = re.findall(r'https?://[^"\'\s\)]+?\.woff2', html_text)
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def looks_preview(html_text, paras):
    """付费墙判定：含 VIP/购买 字样且正文显著偏短。"""
    chars = sum(len(p) for p in paras)
    return chars < PREVIEW_CHAR_LIMIT and all(w in html_text for w in WALL_WORDS)


# ---------------------------------------------------------------- 元数据

def _txt(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return htmllib.unescape(s).strip()


def get_book_meta(book_id, cookie=None):
    """从书籍页抓书名/作者/简介/标签/状态；失败不影响主流程。"""
    meta = {"book_id": book_id, "title": "", "author": "", "abstract": "",
            "tags": [], "status": "", "source": PAGE_URL.format(bid=book_id)}
    try:
        h = fetch(PAGE_URL.format(bid=book_id), cookie=cookie)
    except Exception:
        return meta

    m = (re.search(r'<div[^>]*class="[^"]*info-name[^"]*"[^>]*>\s*<h1[^>]*>(.*?)</h1>', h, re.S)
         or re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
         or re.search(r"<title>(.*?)</title>", h, re.S))
    if m:
        t = _txt(m.group(1))
        meta["title"] = re.sub(r"(完整版.*|在线.*|_.*)$", "", t).strip()

    m = (re.search(r'<span[^>]*class="[^"]*author-name-text[^"]*"[^>]*>(.*?)</span>', h, re.S)
         or re.search(r'<span[^>]*class="[^"]*info-author[^"]*"[^>]*>(.*?)</span>', h, re.S))
    if m:
        meta["author"] = _txt(m.group(1))

    m = (re.search(r'<div[^>]*class="[^"]*page-abstract-content[^"]*"[^>]*>(.*?)</div>', h, re.S)
         or re.search(r'<div[^>]*class="[^"]*page-abstract[^"]*"[^>]*>(.*?)</div>', h, re.S))
    if m:
        body = re.sub(r"^简介[：:]\s*", "", _txt(m.group(1)))
        meta["abstract"] = re.sub(r"\n{2,}", "\n", body)[:500]

    meta["tags"] = [_txt(x) for x in
                    re.findall(r'<span[^>]*class="[^"]*info-label-grey[^"]*"[^>]*>(.*?)</span>', h, re.S)]

    m = re.search(r'<span[^>]*class="[^"]*info-label-yellow[^"]*"[^>]*>(.*?)</span>', h, re.S)
    if m:
        meta["status"] = _txt(m.group(1))
    return meta


def get_toc(book_id, cookie=None):
    raw = fetch(DIR_API.format(bid=book_id), referer=PAGE_URL.format(bid=book_id), cookie=cookie)
    data = json.loads(raw)["data"]
    groups = data.get("chapterListWithVolume") or []
    items = []
    if groups and isinstance(groups[0], list):
        for vol in groups:
            items.extend(vol)
    else:
        items = groups

    out = []
    for i, ch in enumerate(items, 1):
        out.append({
            "n": i,
            "item_id": ch.get("itemId"),
            "title": (ch.get("title") or "").strip(),
            "volume": ch.get("volume_name", ""),
            "need_pay": ch.get("needPay", 0),
            "vip": bool(ch.get("isChapterLock")),
        })
    return out, data.get("volumeNameList") or []


# ---------------------------------------------------------------- 字体/解码

def ensure_decoder(book_out, sample_html, cookie=None, verbose=True):
    """准备 PUA -> 汉字 映射。返回 pua_map。"""
    fonts = extract_font_urls(sample_html)
    if not fonts:
        if verbose:
            print("  ⚠ 页面里没有 woff2，可能该章无混淆或站点结构变了")
        return {}

    cache_dir = os.path.join(book_out, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    gid_cache = os.path.join(cache_dir, "gidmap.json")

    font_url = next((u for u in fonts if "-400" in u or "normal" in u.lower()), fonts[0])
    name = os.path.basename(font_url.split("?")[0])
    local = os.path.join(cache_dir, name)
    if not os.path.exists(local):
        if verbose:
            print(f"  下载字体：{name}")
        blob = fetch(font_url, referer="https://fanqienovel.com/", binary=True, cookie=cookie)
        with open(local, "wb") as f:
            f.write(blob)
    gid_map = font_deobf.build_gid_map(local, gid_cache, verbose=verbose)
    return font_deobf.map_for_font(local, gid_map)


# ---------------------------------------------------------------- 主流程

def write_chapter(chap_dir, n, title, paras, pua_map):
    body = [font_deobf.decode(p, pua_map) for p in paras]
    text = (title + "\n\n" if title else "") + "\n".join(body)
    with open(os.path.join(chap_dir, f"{n:04d}.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    return text


def merge_all(out, chap_dir, title, author):
    files = sorted(f for f in os.listdir(chap_dir) if re.fullmatch(r"\d{4}\.txt", f))
    if not files:
        return None
    parts = []
    if title:
        head = f"《{title}》"
        if author:
            head += f"\n作者：{author}"
        parts.append(head + "\n")
    for f in files:
        with open(os.path.join(chap_dir, f), encoding="utf-8") as fh:
            parts.append(fh.read().strip())
    merged = "\n\n".join(parts) + "\n"
    safe = re.sub(r'[\\/:*?"<>|]', "_", title or "fanqie_book")
    path = os.path.join(out, f"{safe}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(merged)
    return path, merged, len(files)


def main():
    ap = argparse.ArgumentParser(description="抓取番茄小说正文为 UTF-8 文本")
    ap.add_argument("--book", required=True, help="book_id 或任意番茄书籍/阅读页链接")
    ap.add_argument("--out", default=".", help="输出目录")
    ap.add_argument("--start", type=int, default=1, help="起始章序号（1-based，含）")
    ap.add_argument("--end", type=int, default=0, help="结束章序号（含，0=到末章）")
    ap.add_argument("--limit", type=int, default=0, help="只抓前 N 章，用于试跑")
    ap.add_argument("--workers", type=int, default=3, help="并发数，建议 2-4，过高会触发风控")
    ap.add_argument("--delay", type=float, default=0.25, help="每次请求后的基础延迟（秒）")
    ap.add_argument("--toc-only", action="store_true", help="只导出目录，不下正文")
    ap.add_argument("--force", action="store_true", help="已存在的章节也重抓")
    ap.add_argument("--vip", action="store_true",
                    help="尝试 VIP 章（必须同时提供 --cookie，仅用于你已购买的章节）")
    ap.add_argument("--cookie", default="", help="浏览器 Cookie 字符串")
    ap.add_argument("--cookie-file", default="", help="从文件读 Cookie（一行）")
    args = ap.parse_args()

    cookie = args.cookie
    if args.cookie_file:
        with open(args.cookie_file, encoding="utf-8") as f:
            cookie = f.read().strip()
    if args.vip and not cookie:
        print("✗ --vip 需要配合 --cookie/--cookie-file，使用你自己账号的凭据。")
        sys.exit(2)

    book_id = parse_book_id(args.book)
    out = os.path.abspath(args.out)
    chap_dir = os.path.join(out, "chapters")
    os.makedirs(chap_dir, exist_ok=True)

    print(f"书籍 ID：{book_id}")
    meta = get_book_meta(book_id, cookie)
    toc, volumes = get_toc(book_id, cookie)
    print(f"书名：{meta['title'] or '(未知)'}  作者：{meta['author'] or '(未知)'}")
    print(f"目录：{len(toc)} 章 / {len(volumes)} 卷  状态：{meta['status'] or '(未知)'}")
    if meta["tags"]:
        print(f"标签：{' / '.join(meta['tags'])}")

    vip = [c for c in toc if c["vip"]]
    free = [c for c in toc if not c["vip"]]
    print(f"章节构成：免费 {len(free)} 章 / VIP {len(vip)} 章")
    if vip and not cookie:
        print("  ⚠ VIP 章未登录只返回试读片段，默认跳过。"
              "如需抓已购章节，用 --cookie 传你自己账号的 Cookie。")

    meta.update({"chapters": len(toc), "volumes": volumes,
                 "vip_chapters": len(vip), "free_chapters": len(free),
                 "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")})

    if args.toc_only:
        with open(os.path.join(out, "meta.jsonl"), "w", encoding="utf-8") as f:
            for ch in toc:
                f.write(json.dumps(ch, ensure_ascii=False) + "\n")
        with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        print("已导出 meta.jsonl / meta.json")
        return

    end = args.end or len(toc)
    if args.limit:
        end = min(end, args.start + args.limit - 1)
    window = [c for c in toc if args.start <= c["n"] <= end]
    targets = [c for c in window if (not c["vip"]) or args.vip]
    skipped = [c["n"] for c in window if c["vip"] and not args.vip]
    if skipped:
        print(f"跳过 VIP 章 {len(skipped)} 个：{skipped[:10]}{'…' if len(skipped) > 10 else ''}")
    print(f"待抓：{len(targets)} 章（{args.start}–{end}）")
    if not targets:
        print("没有可抓章节，结束。")
        return

    # 用第一章（优先免费章）做字体样本
    sample_html = None
    for ch in sorted(targets, key=lambda c: c["vip"]):
        try:
            sample_html = fetch(READER_URL.format(item=ch["item_id"]),
                                referer=PAGE_URL.format(bid=book_id), cookie=cookie)
            break
        except Exception as e:
            print(f"  取样失败 ch{ch['n']}: {e}")
    if sample_html is None:
        print("无法取得样本页，退出")
        sys.exit(1)

    pua_map = ensure_decoder(out, sample_html, cookie)
    if pua_map:
        print(f"  PUA 映射：{len(pua_map)} 条")

    done, failed, previews, short = [], [], [], []

    def work(ch):
        path = os.path.join(chap_dir, f"{ch['n']:04d}.txt")
        if not args.force and os.path.exists(path) and os.path.getsize(path) > 50:
            return ch, "skip", 0
        h = fetch(READER_URL.format(item=ch["item_id"]),
                  referer=PAGE_URL.format(bid=book_id), cookie=cookie)
        title, paras = extract_chapter(h)
        if not paras:
            return ch, "empty", 0
        if looks_preview(h, paras):
            return ch, "preview", sum(len(p) for p in paras)
        text = write_chapter(chap_dir, ch["n"], title or ch["title"], paras, pua_map)
        time.sleep(args.delay + random.random() * args.delay)
        return ch, "ok", len(text)

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(work, ch): ch for ch in targets}
        for i, fut in enumerate(as_completed(futs), 1):
            ch = futs[fut]
            try:
                _, status, chars = fut.result()
            except Exception as e:
                status, chars = f"fail:{e}", 0
                failed.append((ch["n"], str(e)[:80]))

            if status == "ok":
                done.append((ch["n"], chars))
                if chars < 300:
                    short.append((ch["n"], chars))
            elif status == "preview":
                previews.append(ch["n"])
            elif status.startswith("fail") or status == "empty":
                failed.append((ch["n"], status))

            if i % 10 == 0 or i == len(targets):
                print(f"  进度 {i}/{len(targets)}  用时 {time.time()-t0:.0f}s  "
                      f"失败 {len(failed)}")

    total_chars = sum(c for _, c in done)
    print(f"完成：本次新抓={len(done)} 已存在={len(targets)-len(done)-len(previews)-len(failed)} "
          f"预览={len(previews)} 失败={len(failed)}  用时 {time.time()-t0:.0f}s")
    if done:
        print(f"正文合计 {total_chars} 字，平均 {total_chars//len(done)} 字/章")
    if short:
        print(f"  ⚠ 偏短章节（可能缺内容）：{short[:8]}")
    if previews:
        print(f"  预览章（付费墙）：{previews[:10]}")

    merged = merge_all(out, chap_dir, meta["title"], meta["author"])
    if merged:
        path, text, n = merged
        print(f"合并：{path}  ({len(text)} 字 / {n} 章)")
        meta["merged_chars"] = len(text)
        meta["merged_chapters"] = n

    # 回写章节状态：**以磁盘实际文件为准**，否则续传时会把已抓的章误标 missing
    stat = {"ok": 0, "preview": 0, "vip_skipped": 0, "missing": 0}
    with open(os.path.join(out, "meta.jsonl"), "w", encoding="utf-8") as f:
        for ch in toc:
            ch = dict(ch)
            p = os.path.join(chap_dir, f"{ch['n']:04d}.txt")
            if os.path.exists(p) and os.path.getsize(p) > 50:
                ch["status"] = "ok"
                ch["chars"] = len(open(p, encoding="utf-8").read().strip())
            elif ch["n"] in previews:
                ch["status"] = "preview"
            elif ch["vip"] and not args.vip:
                ch["status"] = "vip_skipped"
            else:
                ch["status"] = "missing"
            stat[ch["status"]] += 1
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")

    meta["stats"] = dict(stat, failed=len(failed))
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    if failed:
        print("失败章节：", [n for n, _ in failed][:20])
        sys.exit(1)


if __name__ == "__main__":
    main()
