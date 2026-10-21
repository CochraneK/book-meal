# -*- coding: utf-8 -*-
"""
拆书流水线 · 阶段⑥ 审计（质量门）
==================================
对最终模型（data/<book>/data.json + geo_annotations.json）做不变量检查，
分级 INFO / WARNING / ERROR，出现 ERROR 返回非 0（可做 CI 门禁）。

检查项：
  E-01 人物/地点/事件 id 唯一
  E-02 关系端点不得为空、不得自环
  E-03 关系端点类型与实体表一致性（person 必须在人物表内）
  E-04 坐标非法：|lat|>90 或 |lng|>180 或非数值（元组顺序必须是 lng,lat）
  E-05 事件参与者必须在人物表内（否则记为 WARNING，多为别名未归一）
  E-06 章节引用必须存在于 chapters
  E-07 geo 标注覆盖：每个地点都要有 geo_status
  W-01 未定位地点（pending）占比
  W-02 未知年份事件
  W-03 无关系人物
  W-04 抽取覆盖不足（extracted_chapters < chapters）
  W-05 源文本重复章节
  I-01 规模统计

用法：
  python src/audit_final.py            # 两本书
  python src/audit_final.py tiancai    # 指定书
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def audit(book):
    ddir = os.path.join(BASE, "data", book)
    data = load(os.path.join(ddir, "data.json"))
    if not data:
        print(f"[{book}] 跳过：data.json 不存在")
        return 0
    geo = load(os.path.join(ddir, "geo_annotations.json"), {})
    dup = load(os.path.join(ddir, "duplicate_report.json"), {})
    chapters = {c["key"] for c in load(os.path.join(ddir, "chapters.json"), [])}

    errors, warnings, infos = [], [], []

    persons = data["characters"]
    places = data["locations"]
    events = data["events"]
    rels = data["relations"]
    person_names = {p["name"] for p in persons}
    place_names = {l["name"] for l in places}
    chapter_keys = {c["key"] for c in data["chapters"]} or chapters

    # E-01 id 唯一
    for label, items in (("人物", persons), ("地点", places), ("事件", events)):
        ids = [x["id"] for x in items]
        if len(ids) != len(set(ids)):
            errors.append(f"E-01 {label} id 重复")

    # E-02/E-03 关系
    for r in rels:
        if not r["from"] or not r["to"]:
            errors.append(f"E-02 关系端点为空：{r}")
        if r["from"] == r["to"]:
            errors.append(f"E-02 自环：{r['from']} -{r['rel']}-> {r['to']}")
        if r["from_kind"] == "person" and r["from"] not in person_names:
            errors.append(f"E-03 关系端点标为人物但不在人物表：{r['from']}")
        if r["to_kind"] == "person" and r["to"] not in person_names:
            errors.append(f"E-03 关系端点标为人物但不在人物表：{r['to']}")

    # E-04 坐标
    for l in places:
        g = geo.get(l["name"])
        if not g:
            errors.append(f"E-07 地点无地理标注：{l['name']}")
            continue
        co = g.get("coords")
        if co is None:
            continue
        if not (isinstance(co, list) and len(co) == 2 and all(isinstance(x, (int, float)) for x in co)):
            errors.append(f"E-04 坐标格式非法：{l['name']} {co}")
            continue
        lng, lat = co
        status = g.get("geo_status")
        # 坐标合法性必须按类型分别校验（以前只按经纬度查，误伤示意坐标）：
        #   real      → 真实经纬度，lat∈[-90,90] / lng∈[-180,180]
        #   schematic → 虚构世界的示意坐标，定义在 [0,100]×[0,100]，
        #               与经纬度数值范围重叠但语义完全不同，不能用同一套阈值。
        # 顺带说明了为什么示意坐标要避开 |值|>90 的区间：否则连外部工具都会误判。
        if status == "real":
            if abs(lat) > 90:
                errors.append(f"E-04 纬度越界（疑似经纬倒置）：{l['name']} {co}")
            if abs(lng) > 180:
                errors.append(f"E-04 经度越界：{l['name']} {co}")
        elif status == "schematic":
            if not (0 <= lng <= 100 and 0 <= lat <= 100):
                errors.append(f"E-04 示意坐标越出 [0,100] 画布：{l['name']} {co}")

    # E-05 事件参与者
    missing_ptc = set()
    for e in events:
        for n in e["participants"]:
            if n not in person_names:
                missing_ptc.add(n)
    if missing_ptc:
        warnings.append(f"E-05 事件参与者不在人物表：{len(missing_ptc)} 个，例 {list(missing_ptc)[:8]}")

    # W-06 别名冲突：某名字既是独立人物，又被别人当作别名 → 归并歧义
    alias_owner = {}
    for p in persons:
        for a in p["aliases"]:
            alias_owner.setdefault(a, set()).add(p["name"])
    conflicts = {n: o for n, o in alias_owner.items() if n in person_names}
    if conflicts:
        samples = [f"{n}→{'/'.join(sorted(o))}" for n, o in list(conflicts.items())[:6]]
        warnings.append(f"W-06 别名与独立人物重名：{len(conflicts)} 个，例 {samples}")

    # E-06 章节引用
    for label, items in (("人物", persons), ("地点", places), ("事件", events)):
        for x in items:
            bad = [k for k in x["chapters"] if k not in chapter_keys]
            if bad:
                errors.append(f"E-06 {label}「{x['name']}」引用不存在的章节：{bad[:3]}")
                break

    # W 类
    pend = [l["name"] for l in places if (geo.get(l["name"], {}) or {}).get("geo_status") == "pending"]
    if places:
        warnings.append(f"W-01 待核验地点 {len(pend)}/{len(places)}"
                        f"（{len(pend) / len(places) * 100:.1f}%）")
    no_year = [e["name"] for e in events if not e["year"]]
    if no_year:
        warnings.append(f"W-02 未知年份事件 {len(no_year)} 件（已单列展示）")
    lonely = [p["name"] for p in persons if p["name"] not in
              {r["from"] for r in rels} | {r["to"] for r in rels}]
    if lonely:
        warnings.append(f"W-03 无任何关系的人物 {len(lonely)}/{len(persons)}")
    meta = data["meta"]
    if meta["extracted_chapters"] < meta["chapters"]:
        warnings.append(f"W-04 抽取覆盖 {meta['extracted_chapters']}/{meta['chapters']} 章"
                        f"（{meta['extracted_chapters'] / meta['chapters'] * 100:.1f}%）")
    if dup.get("pairs"):
        warnings.append(f"W-05 源文本重复章节对 {len(dup['pairs'])}（涉及 {len(dup.get('dup_chapters', []))} 章）")

    infos.append(f"I-01 章节 {meta['chapters']}（已抽 {meta['extracted_chapters']}）"
                 f" 人物 {len(persons)} 地点 {len(places)} 事件 {len(events)} 关系 {len(rels)}")

    print(f"\n===== {meta['title']}（{book}）审计 =====")
    for i in infos:
        print("  [INFO]   ", i)
    for w in warnings:
        print("  [WARN]   ", w)
    for e in errors[:15]:
        print("  [ERROR]  ", e)
    if len(errors) > 15:
        print(f"  [ERROR]   …… 另有 {len(errors) - 15} 条")
    print(f"  结论：ERROR {len(errors)} / WARNING {len(warnings)} / INFO {len(infos)}")
    return len(errors)


def main():
    books = sys.argv[1:] or ["tiancai", "feitu"]
    total = 0
    for b in books:
        total += audit(b)
    print(f"\n[audit] 总 ERROR：{total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
