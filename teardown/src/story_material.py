# -*- coding: utf-8 -*-
"""
故事长文 · 取材器
================
输入：data/<book>/data.json + chapters.json + extract_raw.json + quotes.json
输出：docs/_material_<book>.md（写作素材包，非交付物）

为什么不让模型直接「凭记忆写全书梗概」
----------------------------------
那等于用训练数据里的印象替代这本书，写出来的东西无法核对、也无法覆盖
439 章的细节。所以这里先把 KG 里**真实抽取到的**情节按章节顺序筛出来，
模型只做「取舍 + 连缀 + 措辞」，不做「发明」。

筛法（全部可复算）：
  ① 按阶段分段，段内按「重要度」取前 K 条，再按章号排回叙事顺序；
  ② 重要度 = 核心人物参与(4) + 主要人物参与(2) + 推进型事件类型(2)
            + 摘要信息量(0~2) + 有地点(0.5)；
  ③ 每章只取 1 条「最早发生的事」保底，避免某章整章被跳过。
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 共享核心：阶段划分与章号换算的唯一真源（此前从 generate_report 拷贝）
from core.books import BASE, load  # noqa: E402
from core.chapters import build_idx2no, build_key2no  # noqa: E402
from core.phases import derive_phases, phases_to_no  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BOOKS = ["tiancai", "feitu"]
# 推进剧情的事件类型（其余多为日常/背景，长文里只作点缀）
PLOT_TYPES = {"副本任务", "战斗", "危机伤亡", "探索发现", "密谋博弈", "撤离救援",
              "制度秩序", "冲突对峙", "科研医疗", "成长学习"}
TOP_EV_PER_PHASE = 6      # 副本弧：一条弧取几条
MAIN_PER_PHASE = 3        # 主线过渡段：只取骨架，避免淹没了副本


def line_of(e):
    """把事件归到一条世界线。

    天才基本法是双线结构：22 岁现实线 + 穿越回的 12 岁芝士世界线，
    而且**同一场景会在两条线里反复重演**（心算王骗局在 11 个章号里出现）。
    按章号平铺等于把同一个故事讲十一遍，所以先分线、再去重。
    """
    t = (e.get("time_hint") or "")
    if "番外" in t:
        return "番外"
    if "现实线" in t and "芝士" not in t and "穿越" not in t:
        return "现实线（22岁）"
    if "穿越线" in t:
        return "穿越线"
    if "芝士" in t or "平行世界" in t:
        return "芝士世界（12岁）"
    if "童年线" in t or "11岁" in t or "12岁" in t:
        return "芝士世界（12岁）"
    if "现实线" in t:
        return "现实线（22岁）"
    return "未标注"


def norm_name(s):
    return re.sub(r"[\s，。！？、；：,\.\?!\"'…—\-—_（）()]", "", s or "")


def build(book):
    ddir = os.path.join(BASE, "data", book)
    d = load(os.path.join(ddir, "data.json"))
    raw = load(os.path.join(ddir, "extract_raw.json"), [])
    quotes = load(os.path.join(ddir, "quotes.json"), {})
    m = d["meta"]

    idx2no = build_idx2no(d["chapters"])
    key2no = build_key2no(d["chapters"])
    title_by_no = {c.get("no", c["index"]): c["title"] for c in d["chapters"]}

    # 阶段：与报告同源（core.phases 唯一真源），再把内部 index 换成书中真实章号
    book_id = "feitu" if m["kind"] == "fictional_world" else "tiancai"
    phases = phases_to_no(derive_phases(book_id, d["chapters"], raw), idx2no)

    # 人物分层集合
    core = {p["name"] for p in d["characters"] if p.get("tier") == "core"}
    major = {p["name"] for p in d["characters"] if p.get("tier") == "major"}

    def first_no(e):
        nos = [key2no.get(k) for k in e.get("chapters", []) if k in key2no]
        return min(nos) if nos else 0

    def score(e):
        ps = e.get("participants") or []
        s = 0
        if any(p in core for p in ps):
            s += 4
        if any(p in major for p in ps):
            s += 2
        if (e.get("type_base") or "") in PLOT_TYPES:
            s += 2
        s += min(len(e.get("note") or ""), 60) / 30
        if (e.get("location") or "").strip():
            s += 0.5
        return s

    # 事件 → 阶段
    evs = []
    for e in d["events"]:
        no = first_no(e)
        ph = None
        for p in phases:
            if p["s"] <= no <= p["e"]:
                ph = p
                break
        evs.append((e, no, ph))
    orphan = [e for e, no, ph in evs if ph is None]

    L = []
    A = L.append
    A(f"# {m['title']} · 故事素材包（中间产物，非交付物）")
    A("")
    A(f"{m['author']} · {m['chapters']} 章 · {m['chars'] / 10000:.1f} 万字 · "
      f"事件 {len(d['events'])} 条（100% 带原文摘要）· 阶段 {len(phases)} 个")
    A("")
    A("> 用法：下面是筛出来的关键事件，**按章号排序**。写长文时只做取舍与连缀，"
      "不要新增这里没有的情节。每条都带章号，可回原文核对。")
    A("")

    # ---- 核心人物 ----
    A("## 核心人物（按出场章数）")
    A("")
    for p in sorted(d["characters"], key=lambda x: -len(x.get("chapters", [])))[:14]:
        al = [a for a in p.get("aliases", []) if len(a) >= 2][:5]
        A(f"- **{p['name']}**（出场 {len(p.get('chapters', []))} 章，"
          f"{p.get('tier')}）{p.get('faction_main') or ''}"
          f"{('｜别名：' + '、'.join(al)) if al else ''}"
          f"{('｜' + p['role']) if p.get('role') else ''}")
    A("")

    # ---- 关系结构 ----
    rb = Counter(r.get("rel_base") or "其他关系" for r in d["relations"])
    A("## 关系结构 Top 10")
    A("")
    A(" · ".join(f"{k} {v}" for k, v in rb.most_common(10)))
    A("")

    # ---- 场景重演表 ----
    # 同一批人反复卷入同一类事 = 作者刻意重演（平行世界同场景）。
    # 注意：重演的事件**名字往往不同**（「公园心算王速算骗局摆摊」/
    # 「公园速算骗局与林朝夕质疑」/「心算王公园摆摊卖速算法骗局」），
    # 所以按名字去重抓不到，改用「核心人物 + 事件类型」做签名。
    sig_ch = {}
    for e, no, ph in evs:
        ps = [p for p in (e.get("participants") or []) if p in core]
        if not ps or not no:
            continue
        sig = (tuple(sorted(ps)[:2]), e.get("type_base") or "其他")
        sig_ch.setdefault(sig, set()).add(no)
    repeats = sorted(((len(v), k, sorted(v)) for k, v in sig_ch.items() if len(v) >= 5),
                     reverse=True)
    if repeats:
        A("## 场景重演表（同一组人 + 同一类事，跨多章反复出现）")
        A("")
        for cnt, (ps, tb), nos in repeats[:10]:
            A(f"- **{'、'.join(ps)}** · {tb} × {cnt} 章"
              f"（章 {'、'.join(str(n) for n in nos[:14])}"
              + ("…" if len(nos) > 14 else "") + "）")
        A("")

    # ---- 关键事件：双线书按世界线分组，其余按阶段（副本弧/主线）分组 ----
    line_counts = Counter(line_of(e) for e in d["events"])
    use_lines = line_counts.get("未标注", 0) < 0.3 * len(d["events"])
    A("## 关键事件" + ("（按世界线，已按场景去重）" if use_lines else "（按阶段）"))
    A("")
    picked_total = 0
    if use_lines:
        groups = {}
        for e, no, ph in evs:
            groups.setdefault(line_of(e), []).append((e, no))
        order = ["现实线（22岁）", "芝士世界（12岁）", "穿越线", "未标注", "番外"]
        caps = {"现实线（22岁）": 12, "芝士世界（12岁）": 26, "穿越线": 8,
                "未标注": 8, "番外": 4}
    else:
        groups = {}
        for e, no, ph in evs:
            groups.setdefault(ph["name"] if ph else "（未归段）", []).append((e, no))
        order = [p["name"] for p in phases]
        caps = {}

    for gname in order:
        pool = groups.get(gname) or []
        if not pool:
            continue
        if use_lines:
            # 同名场景只留分数最高的一条，但记下它在哪些章还出现过
            best, seen_ch = {}, {}
            for e, no in pool:
                k = norm_name(e["name"])
                seen_ch.setdefault(k, set()).add(no)
                if k not in best or score(e) > score(best[k][0]):
                    best[k] = (e, no)
            picked = sorted(best.values(), key=lambda x: -score(x[0]))[:caps.get(gname, 8)]
        else:
            cap = MAIN_PER_PHASE if "主线" in gname else TOP_EV_PER_PHASE
            picked = sorted(pool, key=lambda x: -score(x[0]))[:cap]
            seen_ch = {}
        picked.sort(key=lambda x: x[1])
        picked_total += len(picked)
        A(f"### {gname}（事件 {len(pool)} 条，入选 {len(picked)} 条）")
        A("")
        for e, no in picked:
            ps = "、".join((e.get("participants") or [])[:4])
            loc = (e.get("location") or "").strip()
            note = (e.get("note") or "").strip().replace("\n", " ")
            rep = sorted(seen_ch.get(norm_name(e["name"]), {no}))
            extra = (f"｜同场景还见于章 {'、'.join(str(x) for x in rep[1:10])}"
                     if len(rep) > 1 else "")
            A(f"- 第{no}章《{title_by_no.get(no, '')}》"
              f"【{e.get('type_base') or '其他'}】{e['name']}"
              + (f"｜{ps}" if ps else "")
              + (f"｜地：{loc}" if loc else "")
              + (f"｜{note}" if note else "") + extra)
        A("")
    print(f"    入选事件合计 {picked_total} 条"
          f"（{'按世界线' if use_lines else '按阶段'}）")

    # ---- 阶段骨架 ----
    A("## 阶段骨架（结构索引）")
    A("")
    A(" · ".join(f"{p['name']}({p['s']}–{p['e']})" for p in phases))
    A("")

    if orphan:
        A(f"> 注：{len(orphan)} 条事件未能归入任何阶段（章号越界），已略去。")
        A("")

    # ---- 金句备选 ----
    if quotes:
        A("## 金句备选（长文可直接引用）")
        A("")
        for q in (quotes.get("top") or [])[:14]:
            who = q.get("s") or (q.get("h") or "叙述")
            A(f"- 「{q['t']}」——{who}（第{q.get('ch')}章 {q.get('ct', '')}）")
        A("")

    out = os.path.join(BASE, "docs", f"_material_{book}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"[done] {out}（{os.path.getsize(out) / 1024:.1f} KB）"
          f" 阶段 {len(phases)} · 入选事件 {sum(1 for _ in L if _.startswith('- 第'))}")


if __name__ == "__main__":
    for b in sys.argv[1:] or BOOKS:
        build(b)
