# -*- coding: utf-8 -*-
"""
拆书流水线 · 阶段⑤ 报告生成
============================
输入 data/<book>/{data.json, geo_annotations.json, extract_raw.json}
输出 out/<book>.html（单文件离线 HTML）

- 模板在 web/{template,css,js}，本脚本把紧凑 JSON 注入骨架后拼成单文件
- 阶段划分：废土（副本流）按卷/副本弧切分；天才基本法（现实+穿越）按 time 关键词切分，兜底等长分段
- 构建后自检：CSS 括号平衡 / JS 语法（node --check）/ 数据占位符唯一
"""

import json
import os
import re
import subprocess
import sys
import tempfile

# 曾经的写法是写死本机那一个绝对 Windows 路径，结果在 Linux runner 上
# subprocess 直接 FileNotFoundError（2026-10-21 拆书工程第一次进 CI 就挂在这）。
# 构建期只用它做一次 JS 语法自检，找不到就跳过——不该让「没装 node」
# 变成构建失败，那是环境问题不是代码问题。
NODE_WIN = "C:/Users/cunyi/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"


def find_node():
    """按 环境变量 → PATH → 本机已知位置 的顺序找 node；找不到返回 None。"""
    import shutil
    for key in ("NODE_BIN", "NODE"):
        v = os.environ.get(key)
        if v and os.path.exists(v):
            return v
    for name in ("node", "node.exe"):
        p = shutil.which(name)
        if p:
            return p
    if os.path.exists(NODE_WIN):
        return NODE_WIN
    return None
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_to_html import md_to_html  # noqa: E402  长文 Markdown → 报告内嵌 HTML
from insight_link import build_insight_index, extend_linked  # noqa: E402  学科视角/论文 ↔ 实体 联动索引

# 共享核心：阶段划分与章号换算的唯一真源。
# 此前本文件与 perspectives_prep.py 各存一份 derive_phases 拷贝、写法还不同，
# 是 v3.3 学科文档数字漂移的根因；现已统一收敛到 src/core，此处只 import。
from core.books import BASE, load  # noqa: E402
from core.chapters import build_idx2no, build_key2no  # noqa: E402
from core.phases import derive_phases, phases_to_no, stage_of  # noqa: E402
from role_parse import coverage as role_coverage, parse_role  # noqa: E402  A5 身份结构化


def build_story(book_id):
    """把 docs/story_<book>.md 转成报告内嵌 HTML，并自检章号链接。

    自检为什么重要：长文里的「第N章」是手写的，写错了不会报错，
    只会变成一个点了没反应的死链。这里在构建期就把每个 data-no
    拿 chapters.json 对一遍，越界就 **raise**——宁可在构建时炸，
    不要在产品里静默失效。
    """
    path = os.path.join(BASE, "docs", "story_%s.md" % book_id)
    if not os.path.exists(path):
        print("[warn] %s：缺少 %s，「故事」视图将显示占位说明" % (book_id, path))
        return None
    md = open(path, encoding="utf-8").read()
    html, headings = md_to_html(md, ref=True)

    d = load(os.path.join(BASE, "data", book_id, "data.json"))
    valid_no = {int(c.get("no") or c.get("index")) for c in (d or {}).get("chapters", [])}
    refs = {int(x) for x in re.findall(r'data-no="(\d+)"', html)}
    bad = sorted(n for n in refs if valid_no and n not in valid_no)
    if bad:
        raise RuntimeError(
            "story_%s.md 有 %d 个章号链接越界（%s…）——长文与 chapters.json 不一致，"
            "先跑 src/verify_story_refs.py" % (book_id, len(bad), bad[:8]))

    toc = [{"lv": lv, "t": t, "id": hid} for lv, t, hid in headings if lv <= 3]
    return {
        "html": html,
        "toc": toc,
        "src": "docs/story_%s.md" % book_id,
        "md_chars": len(md),
        "ref_count": len(refs),
    }


def build_perspectives(book_id):
    """把 docs/perspectives_<book>.md 转成报告内嵌 HTML（多学科视角分析）。

    与故事长文同一条 Markdown → 内嵌 HTML 流水线，但 **不挂章号链接**
    （分析文档引用的是阶段区间如「第6段（107–141）」，不是可点章节，
    ref=True 会把这类文本误判为章号链接，故关掉）。
    """
    path = os.path.join(BASE, "docs", "perspectives_%s.md" % book_id)
    if not os.path.exists(path):
        print("[warn] %s：缺少 %s，「学科视角」视图将显示占位说明" % (book_id, path))
        return None
    md = open(path, encoding="utf-8").read()
    html, headings = md_to_html(md, ref=False)
    toc = [{"lv": lv, "t": t, "id": hid} for lv, t, hid in headings if lv <= 3]
    # 学科视角 ↔ KG 实体 双向联动索引（人名/地名/事件名可点 + 详情反向入口）
    data = load(os.path.join(BASE, "data", book_id, "data.json"))
    ix = build_insight_index(data, md) if data else None
    if ix:
        # 论文正文里也提到人（祝宁 / 林朝夕 / 裴之…），不扩表的话论文视图里名额全是死字。
        # 只扩「可点表面形式」，不动 sections / byPerson —— 论文没有 sid 锚点（详见 extend_linked 注释）。
        n_paper_sf = extend_linked(ix, data, _papers_texts())
        print("  [insight] %s：命中人物 %d 人 / 地点 %d 个 / 事件 %d 件；"
              "可链表面形式 %d（实体表 %d 个，裁剪 %.0f%%）；论文正文 +%d"
              % (book_id, len(ix["byPerson"]), len(ix["byPlace"]), len(ix["byEvent"]),
                 ix["stats"]["linked"],
                 ix["stats"]["persons"] + ix["stats"]["places"] + ix["stats"]["events"],
                 100.0 * (1 - ix["stats"]["linked"] /
                          max(1, ix["stats"]["persons"] + ix["stats"]["places"] +
                              ix["stats"]["events"])),
                 n_paper_sf))
    return {
        "html": html,
        "toc": toc,
        "src": "docs/perspectives_%s.md" % book_id,
        "md_chars": len(md),
        "ref_count": 0,
        "insight": ix,
    }


def _papers_texts():
    """15 篇论文的正文（已去图片行），只给 insight_link.extend_linked 扩表面形式用。"""
    pdir = os.path.join(BASE, "papers")
    if not os.path.isdir(pdir):
        return []
    out = []
    for d in sorted(os.listdir(pdir)):
        f = os.path.join(pdir, d, d + ".md")
        if not os.path.isfile(f):
            continue
        md = open(f, encoding="utf-8").read()
        out.append(re.sub(r"!\[[^\]]*\]\([^)]*\)\n?", "", md))
    return out


def build_papers():
    """把 papers/<slug>/<slug>.md 的 15 篇论文装进报告（两书共用同一批论文）。

    为什么两书共用：论文本身就是**双文本对照**写的，同一篇里同时引两本书的
    数字，分别给两书各塞一份副本只会让体积翻倍、内容重复。
    单文件报告不能引用外部 PNG，图注保留、图片行去掉（图片在 papers/ 目录里）。
    """
    pdir = os.path.join(BASE, "papers")
    if not os.path.isdir(pdir):
        print("[warn] 缺少 papers/ 目录，「论文」视图将显示占位说明")
        return None
    items = []
    for d in sorted(os.listdir(pdir)):
        f = os.path.join(pdir, d, d + ".md")
        if not os.path.isfile(f):
            continue
        md = open(f, encoding="utf-8").read()
        zh = ""
        en = ""
        kzh = ""
        for line in md.splitlines():
            if not zh and line.startswith("# "):
                zh = line[2:].strip()
            elif not en and line.startswith("**") and line.endswith("**") and len(line) > 6:
                en = line[2:-2].strip()
            elif line.startswith("**关键词：**"):
                kzh = line.split("**关键词：**", 1)[1].strip()
        # 图片行去掉：单文件报告里 ./figures/fig1.png 打不开，留着就是碎图标
        md = re.sub(r"!\[[^\]]*\]\([^)]*\)\n?", "", md)
        html, _headings = md_to_html(md, ref=False)
        n_ref = md.count("https://doi.org/")
        items.append({"slug": d, "zh": zh, "en": en, "kzh": kzh,
                      "n_ref": n_ref, "chars": len(md), "html": html})
    if not items:
        return None
    print("  [papers] %d 篇（%s … %s）" % (len(items), items[0]["slug"], items[-1]["slug"]))
    return {"items": items, "n": len(items), "src": "papers/"}


def build(book_id):
    cfg = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))["books"][book_id]
    ddir = os.path.join(BASE, "data", book_id)
    data = load(os.path.join(ddir, "data.json"))
    if not data:
        raise RuntimeError(f"{book_id}: data.json 不存在，先跑 merge.py")
    geo = load(os.path.join(ddir, "geo_annotations.json"), {})
    raw = load(os.path.join(ddir, "extract_raw.json"), [])

    # ---------- 章节（带每章实体数） ----------
    # 注意：data.json 里 characters/events 的 chapters 字段存的是**章节 key**
    # （如 tiancai-c1），不是整数索引；这里必须先映射成 index 再计数，
    # 否则每章人物/事件数会全部统计成 0，分布图直接空白。
    key2idx = {c["key"]: c["index"] for c in data["chapters"]}
    # 前端 chapterById / 阶段划分全部以整数 index 为键，而 data.json 的
    # chapters 字段是 key（tiancai-c1）。不过这道映射的后果：
    #   · 事件表「章节」列渲染出裸 key，点了没反应
    #   · renderPhaseBody 用 `i >= ph.s && i <= ph.e` 筛阶段事件，
    #     字符串与数字比较恒 false → 阶段事件表**整张是空的**
    #   · 故事视图点「第N章」查该章事件同样恒为 0 条
    # 所以 payload 里所有 chapters 字段一律转成整数 index 再出门。
    def to_idx(keys):
        return [key2idx.get(k, k) for k in (keys or [])]

    # 悬空 key（chapters.json 里没有对应章节）必须报数：静默丢字段会让
    # 「该章事件数」凭空少几条，而读者以为数是对的。
    dangling = set()
    for _grp, _field in ((data["characters"], "chapters"), (data["events"], "chapters"),
                         (data["locations"], "chapters"), (data["relations"], "chapters"),
                         (data["other_events"], "chapters")):
        for _x in _grp:
            for k in (_x.get(_field) or []):
                if k not in key2idx:
                    dangling.add(k)
    if dangling:
        print("[warn] %s：%d 个悬空章节 key（%s…）已原样透传"
              % (book_id, len(dangling), sorted(dangling)[:3]))

    # 章号唯一换算（core）：key → 书中真实章号 no。事件所属阶段用 first_no 口径
    # （全项目统一，见 core.phases.stage_of 文档串）。
    key2no = build_key2no(data["chapters"])

    per_ch_p, per_ch_e = {}, {}
    for p in data["characters"]:
        for k in p["chapters"]:
            i = key2idx.get(k, k)
            per_ch_p[i] = per_ch_p.get(i, 0) + 1
    for e in data["events"]:
        for k in e["chapters"]:
            i = key2idx.get(k, k)
            per_ch_e[i] = per_ch_e.get(i, 0) + 1
    chapters = [{"i": c["index"], "n": c.get("no", c["index"]), "t": c["title"], "c": c["chars"],
                 "p": per_ch_p.get(c["index"], 0), "e": per_ch_e.get(c["index"], 0)}
                for c in data["chapters"]]

    # ---------- 阶段 ----------
    # 唯一真源：src/core/phases.derive_phases(book_id, chapters, raw)
    # 两本书切分策略不同（废土按副本弧 / 天才按 time 关键词），但入口统一，
    # 入参一律是 data.json 的 chapters 标准结构（含 index/key/no/title）。
    phases = derive_phases(book_id, data["chapters"], raw)

    # 阶段轴的分界是按内部 index 算的，展示要换成书中真实章号（book_no），
    # 否则天才基本法会出现「第112章」而实际是第109章
    idx2no = build_idx2no(data["chapters"])
    phases = phases_to_no(phases, idx2no)

    # ---------- 实体键名映射（长键 → 前端紧凑短键） ----------
    # fm=主阵营（出现最多的那个）  tr=分层（core/major/minor/cameo）
    # rl=role 结构化（A5）。role 是每章抽出来的自由文本，三段式解析成
    # 身份/关系/在场，命中不了就留空（宁少不错）；原串 r 始终保留。
    persons = [{"i": p["id"], "n": p["name"], "a": p["aliases"], "f": p["factions"],
                "fm": p.get("faction_main", ""), "tr": p.get("tier", ""),
                "r": p["role"], "c": to_idx(p["chapters"]), "m": p["mentions"],
                "rl": parse_role(p["role"], len(p["chapters"] or []))}
               for p in data["characters"]]
    # 覆盖率必须披露：结构化是「索引」不是「全量」，低覆盖要让人看见而不是假装完整
    _n, _cov = role_coverage(data["characters"])
    print("[info] %s：身份结构化 %d/%d 人命中（身份 %d · 关系 %d · 在场 %d）；"
          "未命中的显示原串，不做推断" % (book_id, _cov["any"], _n,
                                          _cov["id"], _cov["rel"], _cov["st"]))
    # st=事件所属阶段唯一键「名（起–止）」（first_no 口径，走 core.stage_of）。
    # 为什么要构建期算好：前端拿事件的章（index）比阶段边界（no）要先过换算，
    # 而事件表 2591 行每行都算不如构建期算一次；顺带取代了全空的「年份」列
    # （两书 year 字段 100% 为空，833/833、2591/2591，该列零信息——ui_audit §3-4）。
    no_stage = 0
    events_p = []
    for e in data["events"]:
        st = stage_of(e, key2no, phases)
        if st is None:
            no_stage += 1
        events_p.append({"i": e["id"], "n": e["name"], "ty": e["type"], "p": e["participants"],
                         # tb=叙事功能基类（战斗冲突/情报对话…），ty 保留原文作证据
                         "tb": e.get("type_base", ""),
                         "loc": e["location"], "yr": e["year"], "no": e["note"],
                         "th": e.get("time_hint", ""), "c": to_idx(e["chapters"]),
                         "st": st})
    if no_stage:
        print("[info] %s：%d 个事件首章不在任何阶段区间（多为卷间过渡章），阶段列显示「—」"
              % (book_id, no_stage))
    # rb=关系基类（16 类归约） rn=括号里的原始备注（作为证据保留）
    relations_p = [{"i": r["id"], "f": r["from"], "t": r["to"], "r": r["rel"],
                    "rb": r.get("rel_base", ""), "rn": r.get("rel_note", ""),
                    "fk": r["from_kind"], "tk": r["to_kind"], "c": to_idx(r["chapters"])}
                   for r in data["relations"]]
    other_p = [{"text": o["text"], "c": to_idx(o["chapters"])} for o in data["other_events"]]

    # ---------- 地点合并地理标注 ----------
    zones = load(os.path.join(ddir, "geo_zones.json"), [])
    places = []
    for l in data["locations"]:
        g = geo.get(l["name"], {})
        places.append({"i": l["id"], "n": l["name"], "mo": l["modern"], "rg": l["region"],
                       "t": l["type"], "tb": l.get("type_base", ""),
                       "c": to_idx(l["chapters"]), "m": l["mentions"],
                       "tr": l.get("tier", ""),
                       "g": g.get("geo_status", "pending"), "co": g.get("coords"),
                       "src": g.get("source", ""), "z": g.get("zone", "")})

    # ---------- 统计 ----------
    # 注意：必须显式传入数据集。此前按 key 猜数据集（"ty"→events / "r"→relations
    # / 其余→locations），导致「事件类型」误用了地点数据、「关系类别」全是未分类。
    def counter(items, key, fallback="未分类"):
        d = {}
        for x in items:
            v = x.get(key) or fallback
            d[v] = d.get(v, 0) + 1
        return d

    # 事件/地点/关系一律用**归约后的基类**统计，不用原始自由文本：
    #   事件原文 47 种里「其他」占 43%，地点在「室内/设施/建筑」之间摇摆，
    #   关系原文 1396 种。三者都是「有标签、没分类学」，直接排行等于把噪声
    #   摆在第一位。原始 type 仍然保留在事件卡/地点卡里，可回溯。
    stats = {"eventTypes": counter(data["events"], "type_base", "其他"),
             "placeTypes": counter(data["locations"], "type_base", "其他场所"),
             "relTypes": counter(data["relations"], "rel_base", "其他关系")}

    # ---------- 金句 ----------
    # 两路来源分开存：对白（有说话人）/ 叙述·独白（无说话人）。
    # 报告里绝不能把叙述句挂到角色名下，所以这里从数据层就隔离。
    quotes = load(os.path.join(ddir, "quotes.json"), {})

    # ---------- 故事长文 ----------
    # 长文是「一篇文章讲完全部故事」，与报告是同源的两张皮：
    # 同一批事件，一个给人读、一个给人查。挂进报告后，正文里的「第N章」
    # 全部变成可点链接，点开就是该章的 KG 事件——「可回原文核对」才真的可点。
    story = build_story(book_id)
    perspectives = build_perspectives(book_id)
    papers = build_papers()

    payload = {
        "meta": data["meta"],
        "chapters": chapters,
        "persons": persons,
        "places": places,
        "events": events_p,
        "relations": relations_p,
        "other": other_p,
        "alias_index": data["alias_index"],
        "phases": phases,
        "stats": stats,
        "quotes": quotes,
        "story": story,
        "perspectives": perspectives,
        "papers": papers,
        # 学科视角 ↔ KG 实体 双向联动（顶层，人物/地点/事件详情也要用）
        "insightIndex": (perspectives or {}).get("insight"),
    }
    # 源文本质量：重复章节（防盗章/多源拼合伪影）如实带入报告
    dup = load(os.path.join(ddir, "duplicate_report.json"), {})
    # 抽取覆盖章数：以 extract_raw 里出现过的章节 key 计，避免页面显示 undefined
    payload["meta"]["extracted"] = len({r.get("key") for r in raw if r.get("key")})
    payload["meta"]["dup_pairs"] = len(dup.get("pairs", []))
    payload["meta"]["dup_chapters"] = dup.get("dup_chapters", [])
    payload["meta"]["dup_groups"] = dup.get("dup_groups", [])
    payload["meta"]["geo_zones"] = zones
    # meta.generated 刷新为本次生成时间
    import datetime
    payload["meta"]["generated"] = datetime.datetime.now().isoformat(timespec="seconds")

    # ---------- 组装单文件 ----------
    tpl = open(os.path.join(BASE, "web", "template", "index.html"), encoding="utf-8").read()
    css = open(os.path.join(BASE, "web", "css", "app.css"), encoding="utf-8").read()
    js = open(os.path.join(BASE, "web", "js", "app.js"), encoding="utf-8").read()

    # 按书换肤：存在 web/css/theme-<book>.css 就追到 app.css 之后（主题盘与母题
    # 用 html[data-book] 作用域覆写，零侵入；不存在则只挂 data-book 标记，无害）。
    theme_css = ""
    theme_path = os.path.join(BASE, "web", "css", f"theme-{book_id}.css")
    if os.path.exists(theme_path):
        theme_css = open(theme_path, encoding="utf-8").read()
        print(f"  [theme] 已注入主题皮肤 theme-{book_id}.css")
    tpl = tpl.replace('<html lang="zh-CN">', f'<html lang="zh-CN" data-book="{book_id}">')

    # 自检 1：CSS 括号平衡
    if css.count("{") - css.count("}") != 0:
        raise RuntimeError("CSS 花括号不平衡，终止构建")

    # 自检 2：JS 语法（node --check）。找不到 node 就跳过并说明，不因此中断构建。
    node = find_node()
    if not node:
        print("[warn] 未找到 node，跳过 JS 语法自检（装好 node 或设 NODE_BIN 即会启用）")
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
            tmp_js = f.name
        try:
            r = subprocess.run([node, "--check", tmp_js], capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError("JS 语法错误：\n" + (r.stderr or r.stdout))
        finally:
            os.unlink(tmp_js)

    # 自检 3：数据占位符唯一
    if tpl.count("__DATA__") != 1:
        raise RuntimeError("__DATA__ 占位符必须且只能出现一次")

    data_js = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    html = tpl.replace("__CSS__", css + "\n" + theme_css).replace("__JS__", js) \
              .replace("__DATA__", data_js) \
              .replace("__TITLE__", cfg["title"])

    # 自检 4：无残留占位符
    for token in ("__CSS__", "__JS__", "__DATA__", "__TITLE__"):
        if token in html:
            raise RuntimeError(f"占位符 {token} 未替换干净")

    # 自检 5：payload 里不允许再出现裸章节 key
    # 历史 bug：data.json 的 chapters 字段是 key（tiancai-c1），原样透传后
    # 前端以 index 为键的地方全部失效（事件表章节列、阶段事件表、故事视图章号弹窗）。
    # 这三处都不会报错，只会安静地显示 0 条 / 空表，所以这里在构建期就拦死。
    for book_prefix in ("tiancai-c", "feitu-c"):
        if book_prefix in data_js:
            n = data_js.count(book_prefix)
            raise RuntimeError(
                "payload 里仍有 %d 处裸章节 key（%s…）——chapters 字段必须过 key2idx 转 index"
                % (n, book_prefix))

    out_dir = os.path.join(BASE, "out")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{book_id}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(out) / 1024 / 1024
    st = ("故事视图已挂入（%d 个章号链接）" % story["ref_count"]) if story else "无故事长文"
    print(f"[done] {cfg['title']} → out/{book_id}.html（{size:.2f} MB）"
          f" 阶段 {len(phases)} 个：{phases[0]['name']} … {phases[-1]['name']} · {st}")
    return out


PORTAL_TPL = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>拆书 · 书库</title>
<style>
:root{--bg:#f6f4ef;--ink:#2b2a26;--muted:#6f6a5f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:40px 28px 64px}
.hd{margin-bottom:8px}
h1{font-size:28px;margin:0}
.sub{color:var(--muted);font-size:13px;margin:4px 0 0}
.summary{color:var(--muted);font-size:14px;margin:18px 0 22px}
.summary b{color:var(--ink);font-weight:700}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px}
.chip{border:1px solid #ddd8cc;background:#fff;color:var(--ink);font-size:13px;
padding:7px 14px;border-radius:999px;cursor:pointer;font-family:inherit}
.chip:hover{border-color:#8c4a2f}
.chip.on{background:#2b2a26;color:#fff;border-color:#2b2a26}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}
.bk{position:relative;background:#fff;border:1px solid #e7e2d6;border-radius:14px;overflow:hidden;
box-shadow:0 1px 3px rgba(40,35,25,.08);display:flex}
.bk-accent{width:6px;background:var(--accent)}
.bk-body{padding:20px 22px;flex:1}
.bk-top{display:flex;align-items:center;justify-content:space-between;gap:8px}
.bk-top h2{font-size:19px;margin:0}
.ext{font-size:11px;color:#b8862f;border:1px solid #e6c98a;border-radius:6px;padding:2px 7px;white-space:nowrap}
.bk-author{color:var(--muted);font-size:13px;margin:4px 0 10px}
.tag{display:inline-block;font-size:11px;color:#fff;background:var(--accent);border-radius:6px;padding:2px 8px}
.bk-desc{font-size:13px;line-height:1.6;color:#4a463d;margin:12px 0 16px}
.metrics{display:flex;gap:18px;margin-bottom:16px}
.m{display:flex;flex-direction:column}
.m b{font-size:20px;line-height:1}
.m span{font-size:11px;color:var(--muted);margin-top:4px}
.m.off b{color:#bcb7ab}
.bk-open{display:inline-block;text-decoration:none;color:var(--accent);font-weight:700;font-size:14px}
.bk-open:hover{text-decoration:underline}
@media print{.filters{display:none}}
</style></head><body><div class="wrap">
<div class="hd"><h1>拆书 · 书库</h1><p class="sub">多本书的五元组知识图谱 · 单文件离线报告</p></div>
<div class="summary">__SUMMARY__</div>
<div class="filters">__CHIPS__</div>
<div class="grid">__CARDS__</div>
</div>
<script>
document.querySelectorAll('.chip').forEach(function(c){
  c.onclick=function(){
    document.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});
    c.classList.add('on');
    var f=c.dataset.f;
    document.querySelectorAll('.bk').forEach(function(k){
      k.style.display=(f==='all'||k.dataset.kind===f)?'':'none';
    });
  };
});
</script>
</body></html>"""


def _portal_books(cfg_all):
    """门户数据源：config 的 books 为底，逐条叠加 data/<id>/manifest.json。

    内容/平台分离：新增「独立报告 / 外部书」只需放一份 manifest.json，无需改平台代码；
    五元组书仍需 config（build() 用 file/heading），manifest 由 build_manifest.py 派生。
    """
    books = {bid: dict(b) for bid, b in cfg_all.get("books", {}).items()}
    data_dir = os.path.join(BASE, "data")
    if os.path.isdir(data_dir):
        for name in sorted(os.listdir(data_dir)):
            mp = os.path.join(data_dir, name, "manifest.json")
            if not os.path.isfile(mp):
                continue
            try:
                m = json.load(open(mp, encoding="utf-8"))
            except Exception:
                continue
            bid = m.get("id") or name
            merged = dict(books.get(bid, {}))
            for k in ("title", "author", "kind", "desc", "accent", "report", "data_json"):
                if m.get(k):
                    merged[k] = m[k]
            st = m.get("status")
            for flag in ("external", "missing", "standalone"):
                merged.pop(flag, None)
            if st in ("external", "missing", "standalone"):
                merged[st] = True
            merged["_manifest"] = m
            books[bid] = merged
    return books


def build_portal():
    cfg_all = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
    kinds = cfg_all.get("kinds", {})
    books = _portal_books(cfg_all)

    def metrics(b):
        man = b.get("_manifest") or {}
        mm = man.get("metrics")
        if isinstance(mm, dict) and all(k in mm for k in ("characters", "events", "relations")):
            return mm["characters"], mm["events"], mm["relations"]
        dj = b.get("data_json")
        if not dj:
            return None
        p = os.path.join(BASE, dj)
        if not os.path.exists(p):
            return None
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            return None
        ch = len(d.get("characters") or [])
        ev = len(d.get("events") or []) + len(d.get("other_events") or [])
        rl = len(d.get("relations") or [])
        return ch, ev, rl

    rows, tot = [], {"ch": 0, "ev": 0, "rl": 0, "ready": 0}
    for bid, b in books.items():
        m = metrics(b)
        if m:
            tot["ch"] += m[0]; tot["ev"] += m[1]; tot["rl"] += m[2]; tot["ready"] += 1
            ch, ev, rl = m
            mtxt = ('<div class="m"><b>{0}</b><span>人物</span></div>'
                    '<div class="m"><b>{1}</b><span>事件</span></div>'
                    '<div class="m"><b>{2}</b><span>关系</span></div>').format(ch, ev, rl)
        else:
            mtxt = ('<div class="m off"><b>—</b><span>人物</span></div>'
                    '<div class="m off"><b>—</b><span>事件</span></div>'
                    '<div class="m off"><b>—</b><span>关系</span></div>')
        accent = b.get("accent", "#8c4a2f")
        kind = b.get("kind", "")
        klabel = kinds.get(kind, kind)
        report = b.get("report", bid + ".html")
        ext = b.get("external")
        missing = b.get("missing")
        standalone = b.get("standalone")
        if ext:
            badge = '<span class="ext">外部书</span>'
        elif missing:
            badge = '<span class="ext" style="color:#9a6b2f;background:#fbf3e2">待重建</span>'
        elif standalone:
            badge = '<span class="ext" style="color:#5a4b8c;background:#efeaf8">独立报告</span>'
        else:
            badge = ""
        if missing:
            open_html = '<span class="bk-open" style="color:#bcb7ab;cursor:default">数据待重建</span>'
        else:
            open_html = '<a class="bk-open" href="{report}">打开报告 →</a>'.format(report=report)
        rows.append(
            '<article class="bk" data-kind="{kind}" style="--accent:{accent}">'
            '<div class="bk-accent"></div><div class="bk-body">'
            '<div class="bk-top"><h2>{title}</h2>{badge}</div>'
            '<div class="bk-author">{author}</div>'
            '<span class="tag">{klabel}</span>'
            '<p class="bk-desc">{desc}</p>'
            '<div class="metrics">{mtxt}</div>'
            '{open_html}'
            '</div></article>'.format(
                kind=kind, accent=accent, title=b.get("title", bid),
                badge=badge, author=b.get("author", ""),
                klabel=klabel, desc=b.get("desc", ""), mtxt=mtxt, open_html=open_html))

    n = len(books)
    ready = tot["ready"]
    missing_n = sum(1 for b in books.values() if b.get("missing"))
    summary = ('共 <b>{n}</b> 本书'.format(n=n)
               + (' · 已就绪 <b>{r}</b> 本'.format(r=ready) if ready else '')
               + (' · 待重建 <b>{m}</b> 本'.format(m=missing_n) if missing_n else '')
               + ' · 人物 <b>{ch}</b>'.format(ch=tot["ch"] or "—")
               + ' · 事件 <b>{ev}</b>'.format(ev=tot["ev"] or "—")
               + ' · 关系 <b>{rl}</b>'.format(rl=tot["rl"] or "—"))
    chips = '<button class="chip on" data-f="all">全部</button>' + "".join(
        '<button class="chip" data-f="{k}">{v}</button>'.format(k=k, v=v)
        for k, v in kinds.items())
    html = (PORTAL_TPL.replace("__SUMMARY__", summary)
            .replace("__CHIPS__", chips)
            .replace("__CARDS__", "".join(rows)))
    out = os.path.join(BASE, "out", "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("[done] 书库入口页 → out/index.html（{0} 本书，{1} 本已就绪数据）".format(n, ready))


def main():
    cfg = json.load(open(os.path.join(BASE, "config.json"),
                        encoding="utf-8"))["books"]
    books = sys.argv[1:] or [b for b in cfg
                             if not cfg[b].get("external")
                             and not cfg[b].get("missing")
                             and not cfg[b].get("standalone")]
    for b in books:
        if cfg[b].get("external"):
            print("[skip] {0} 是外部书，跳过本地构建（入口页仍收录）".format(b))
            continue
        if cfg[b].get("missing"):
            print("[skip] {0} 数据缺失（missing），跳过本地构建（入口页占位收录）".format(b))
            continue
        if cfg[b].get("standalone"):
            print("[skip] {0} 是独立报告（standalone），跳过五元组流水线构建（入口页收录）".format(b))
            continue
        build(b)
    build_portal()


if __name__ == "__main__":
    main()
