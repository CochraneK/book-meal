# -*- coding: utf-8 -*-
"""为每本书生成自描述清单 data/<book>/manifest.json（门户的唯一数据源）。

设计原则：内容 / 平台分离。
  - manifest = 一本书对外发布的「名片」：书名/作者/类型/指标/体积/状态/报告路径。
  - config.json = 构建配方（file/heading 等，build() 用）；manifest 由本脚本从 config + data.json 派生，
    二者不手抄、始终一致（改了 config 跑一遍本脚本即可）。
  - build_portal() 逐条扫描 data/*/manifest.json 出卡片；新增「独立报告 / 外部书」只需放一份 manifest，
    无需改平台代码。

用法：python src/build_manifest.py
"""
import json, os, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = 1


def _load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _counts(data):
    """章节数 + 字数（多 schema 兜底）。"""
    if not isinstance(data, dict):
        return None, None
    chs = data.get("chapters")
    if isinstance(chs, list) and chs:
        return len(chs), sum(int(c.get("chars") or 0) for c in chs if isinstance(c, dict))
    ci = data.get("chapter_index")          # swdw 世界级 schema
    if isinstance(ci, list) and ci:
        return len(ci), sum(int(c.get("c") or 0) for c in ci if isinstance(c, dict))
    meta = data.get("meta") or {}
    return meta.get("total_chapters"), meta.get("total_chars")


def _metrics(data):
    if not isinstance(data, dict):
        return None
    return {
        "characters": len(data.get("characters") or []),
        "events": len(data.get("events") or []) + len(data.get("other_events") or []),
        "relations": len(data.get("relations") or []),
    }


def status_of(b):
    if b.get("external"):
        return "external"
    if b.get("missing"):
        return "missing"
    if b.get("standalone"):
        return "standalone"
    return "ready"


def main():
    cfg = _load(os.path.join(BASE, "config.json"), {})
    books = cfg.get("books", {})
    today = datetime.date.today().isoformat()
    written = []

    for bid, b in books.items():
        dj = b.get("data_json")
        data = None
        if dj:
            data = _load(os.path.normpath(os.path.join(BASE, dj)))
        st = status_of(b)
        n, chars = _counts(data) if data else (None, None)
        man = {
            "schema": SCHEMA,
            "id": bid,
            "title": b.get("title", bid),
            "author": b.get("author", ""),
            "kind": b.get("kind", ""),
            "desc": b.get("desc", ""),
            "accent": b.get("accent", "#8c4a2f"),
            "report": b.get("report", bid + ".html"),
            "status": st,
            "metrics": _metrics(data),
            "chapters": n,
            "chars": chars,
            "updated": today,
        }
        d = os.path.join(BASE, "data", bid)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "manifest.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(man, f, ensure_ascii=False, indent=2)
        written.append((bid, st, man["metrics"]))

    for bid, st, m in written:
        print("[manifest] %-8s %-11s %s" % (bid, st, m))
    print("[done] 生成 %d 份 manifest" % len(written))


if __name__ == "__main__":
    main()
