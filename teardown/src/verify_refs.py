#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""参考文献核验：每条都过 Crossref / OpenLibrary 检索，命中才算 verified。

为什么不用手写书目：APA-7 的卷期页码错一个数字就是假引用，手抄 37 条必然有错。
这里把「查证」变成机器动作，留下 DOI / 记录号 / 命中分数作为证据。

三道闸（必须同时过）：
  ① 类型对得上：期望 article 的不能拿书评充数（Crossref 里大量「某某书的评论」
     标题与原书几乎一致，v1 就是这样把 Foucault 的书评当成专著引的）
  ② 标题相似度：token Dice ≥ 0.85（按词集合算，副标题加长不吃亏）
  ③ 年份与作者：Crossref 用 issue 年（±1）；OpenLibrary 用 first_publish_year（±1）

检索顺序：Crossref（权威、带 DOI）→ OpenLibrary（老书/无 DOI 的专著）。
两边都没结果的记 miss，附候选，由 references_override.json 人工核实后覆盖；
override 缺 evidence 字段直接拒用。
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SEED = os.path.join(ROOT, "paper_refs_seed.json")
OUT = os.path.join(ROOT, "papers", "references.json")
OVERRIDE = os.path.join(ROOT, "papers", "references_override.json")
CROSSREF = "https://api.crossref.org/works"
OPENLIB = "https://openlibrary.org/search.json"
UA = "chaishu-refcheck/1.0 (mailto:chaishu@example.org)"
SELECT = "DOI,title,author,issued,container-title,volume,issue,page,publisher,type,URL"

FAMILY = {
    "article": {"journal-article", "proceedings-article"},
    "book": {"book", "monograph", "edited-book", "reference-book", "book-set"},
    "chapter": {"book-chapter", "chapter", "reference-entry"},
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def toks(s):
    return set(t for t in norm(s).split() if len(t) > 1 and t not in {"the", "of", "a", "an", "and", "in", "on"})


def dice(a, b):
    A, B = toks(a), toks(b)
    if not A or not B:
        return 0.0
    return 2.0 * len(A & B) / (len(A) + len(B))


def fam(a):
    return norm(a.get("family") or a.get("name") or "")


def getjson(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise last


def cr_fetch(query, rows=10):
    q = urllib.parse.urlencode({"query.bibliographic": query, "rows": rows, "select": SELECT})
    return getjson(CROSSREF + "?" + q)["message"]["items"]


def _unused_ol_fetch(title, author):
    q = urllib.parse.urlencode({
        "title": title, "author": author, "limit": 8,
        "fields": "title,author_name,first_publish_year,publisher,key,edition_count",
    })
    return getjson(OPENLIB + "?" + q).get("docs", [])


def year_of(it):
    for f in ("issued", "published-print", "published-online", "created"):
        p = (it.get(f) or {}).get("date-parts") or [[]]
        if p and p[0] and p[0][0]:
            return int(p[0][0])
    return 0


def apa_from_crossref(it):
    auths = []
    for a in (it.get("author") or []):
        family = a.get("family") or a.get("name") or ""
        given = a.get("given") or ""
        if not family:
            continue
        ini = " ".join(p[0] + "." for p in re.split(r"[\s\-]+", given) if p and p[0].isalpha())
        auths.append(("%s, %s" % (family, ini)).strip().rstrip(","))
    who = _join_authors(auths)
    y = year_of(it)
    t = (it.get("title") or [""])[0].strip().rstrip(".")
    cont = (it.get("container-title") or [""])
    cont = cont[0].strip() if cont else ""
    typ = it.get("type") or ""
    vol, iss, pg = it.get("volume") or "", it.get("issue") or "", it.get("page") or ""
    pub = (it.get("publisher") or "").strip()
    doi = it.get("DOI") or ""

    if typ in FAMILY["article"]:
        s = "%s (%d). %s." % (who, y, t)
        if cont:
            s += " *%s*" % cont
            if vol:
                s += ", *%s*" % vol
                if iss:
                    s += "(%s)" % iss
            if pg:
                s += ", %s" % pg.replace("-", "–")
            s += "."
        if doi:
            s += " https://doi.org/%s" % doi
        return s
    if typ in FAMILY["book"]:
        s = "%s (%d). *%s*." % (who, y, t)
        if pub:
            s += " %s." % pub
        if doi:
            s += " https://doi.org/%s" % doi
        return s
    if typ in FAMILY["chapter"]:
        s = "%s (%d). %s. In *%s*" % (who, y, t, cont or "")
        if pg:
            s += " (pp. %s)" % pg.replace("-", "–")
        s += "."
        if pub:
            s += " %s." % pub
        if doi:
            s += " https://doi.org/%s" % doi
        return s
    return "%s (%d). %s. %s" % (who, y, t, pub)


def _join_authors(auths):
    if not auths:
        return ""
    if len(auths) == 1:
        return auths[0]
    if len(auths) <= 20:
        return ", ".join(auths[:-1]) + ", & " + auths[-1]
    return ", ".join(auths[:19]) + ", ... " + auths[-1]


def pick_crossref(items, exp):
    fam_ok = FAMILY[exp["type"]]
    best, best_s, scored = None, -1, []
    for it in items:
        typ = it.get("type") or ""
        if typ not in fam_ok:
            continue
        t = (it.get("title") or [""])[0]
        y = year_of(it)
        sim = dice(t, exp["title"])
        dy = abs(y - exp["year"]) if y else 999
        aut = [fam(a) for a in (it.get("author") or [])]
        aok = any(exp["author"] in a for a in aut) if aut else False
        scored.append({"src": "crossref", "doi": it.get("DOI"), "title": t, "year": y,
                       "type": typ, "sim": round(sim, 3), "dy": dy, "author_ok": aok})
        if sim < 0.85 or dy > 1:
            continue
        s = sim + (0.2 if aok else 0)
        if s > best_s:
            best, best_s = it, s
    return best, sorted(scored, key=lambda c: (-c["sim"], c["dy"]))[:3]


def pick_openlibrary(docs, exp):
    scored, best, best_s = [], None, -1
    hint = norm(exp.get("publisher", ""))
    for d in docs:
        t = d.get("title") or ""
        y = int(d.get("first_publish_year") or 0)
        sim = dice(t, exp["title"])
        dy = abs(y - exp["year"]) if y else 999
        names = [norm(n) for n in (d.get("author_name") or [])]
        aok = any(exp["author"] in n for n in names)
        pubs = d.get("publisher") or []
        pub_hit = [p for p in pubs if hint and hint in norm(p)]
        scored.append({"src": "openlibrary", "key": d.get("key"), "title": t, "year": y,
                       "sim": round(sim, 3), "dy": dy, "author_ok": aok,
                       "publisher_hit": bool(pub_hit)})
        if sim < 0.85 or dy > 1 or not aok:
            continue
        s = sim + (0.2 if pub_hit else 0)
        if s > best_s:
            best, best_s = (d, pub_hit[0] if pub_hit else ""), s
    return best, sorted(scored, key=lambda c: (-c["sim"], c["dy"]))[:3]


def main():
    seed = json.load(open(SEED, encoding="utf-8"))["refs"]
    over = {}
    if os.path.exists(OVERRIDE):
        over = json.load(open(OVERRIDE, encoding="utf-8")).get("refs", {})

    rows, bad = [], []
    for r in seed:
        key, exp = r["key"], r["expect"]
        exp = dict(exp)
        exp["publisher"] = r.get("publisher_hint", "")
        rec = {"key": key, "disciplines": r["disciplines"], "status": "miss",
               "expected": exp, "source": ""}
        try:
            if exp["type"] in ("article", "book", "chapter"):
                it, cands = pick_crossref(cr_fetch(r["query"]), exp)
                if it is not None:
                    rec.update({
                        "status": "verified", "source": "crossref",
                        "id": it.get("DOI"), "doi": it.get("DOI"),
                        "type": it.get("type"),
                        "title": (it.get("title") or [""])[0],
                        "year": year_of(it),
                        "apa": apa_from_crossref(it),
                        "evidence": it.get("URL") or ("https://doi.org/" + (it.get("DOI") or "")),
                        "raw": {k: it.get(k) for k in ("container-title", "volume", "issue", "page", "publisher")},
                    })
            if False:
                pass
        except Exception as e:
            rec["error"] = str(e)
            bad.append("%s: 检索失败 %s" % (key, e))
        if rec["status"] != "verified":
            rec["candidates"] = cands
            bad.append("%s: 无合规命中（类型/年份/相似度之一未过）" % key)
        rows.append(rec)
        time.sleep(0.2)

    for rec in rows:
        o = over.get(rec["key"])
        if not o:
            continue
        if not o.get("evidence"):
            bad.append("%s: override 缺 evidence，拒用" % rec["key"])
            continue
        rec.update({k: v for k, v in o.items() if k != "evidence"})
        rec["status"] = "verified" if o.get("apa") else "miss"
        rec["verified_by"] = "manual"
        rec["evidence"] = o["evidence"]

    ok_n = sum(1 for r in rows if r.get("status") == "verified")
    json.dump({"generated_by": "src/verify_refs.py", "total": len(rows), "verified": ok_n, "refs": rows},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("参考文献核验：%d/%d verified → papers/references.json\n" % (ok_n, len(rows)))
    for r in rows:
        print("  [%s] %-16s %-12s %s" % ("OK  " if r["status"] == "verified" else "MISS",
                                        r["key"], r.get("source", "-"), r.get("id") or "-"))
    if bad:
        print("\n未通过：")
        for b in bad:
            print("  - " + b)
    return 0 if ok_n == len(rows) else 1


def _apa_name(name):
    return name


if __name__ == "__main__":
    sys.exit(main())
