# -*- coding: utf-8 -*-
"""学科视角 ↔ KG 实体 双向联动索引（src/insight_link.py）
============================================================
把学科分析长文里的 **人名 / 地名 / 事件名** 变成可点链接，并在
人物 / 地点 / 事件详情里反向给出「相关分析」入口。

为什么不在前端现算
------------------
前端只有 payload，拿不到 alias_index 的原始归并关系；而且构建期算一遍，
可以把「通称过滤」「长名优先」「别名归一」的口径与 Python 侧其他复核脚本对齐，
避免又长出一份第二口径（v3.3 阶段派生三份口径的教训）。

用法（由 generate_report.build_perspectives 调用）：
    from insight_link import build_insight_index
    ix = build_insight_index(data, md)     # data = data.json；md = 分析文档原文
"""
import re

from md_to_html import slugify

__all__ = ["build_insight_index", "extend_linked", "GENERIC_BLOCK"]

# 标题行（与 md_to_html 的判定必须一致，否则 sid 与前端锚点对不上）
_H = re.compile(r"^(#{1,6})\s+(.*)$")

# 通称 / 称谓 / 非专名：绝不能链成人物卡或地点卡。
# 来源：alias_index 里存在「学姐→林朝夕」这类归约，正文里「学姐」出现频率远高于人名，
# 不过滤会把整篇文档链成筛子。判不准一律不链（本项目一贯纪律：错挂比不挂更糟）。
GENERIC_BLOCK = {
    # 称谓 / 亲属
    "学姐", "学长", "老师", "教授", "导师", "同学", "同窗", "师兄", "师姐", "师弟", "师妹",
    "父亲", "母亲", "爸爸", "妈妈", "爹", "娘", "儿子", "女儿", "孩子", "哥哥", "姐姐",
    "弟弟", "妹妹", "爷爷", "奶奶", "外公", "外婆", "舅舅", "阿姨", "叔叔", "婶婶", "姑姑",
    "丈夫", "妻子", "老公", "老婆", "男友", "女友", "家人", "亲人", "父母", "双亲",
    # 身份 / 职务通称
    "朋友", "同事", "上司", "下属", "队长", "队员", "队友", "组长", "班长", "校长", "院长",
    "老板", "经理", "员工", "医生", "护士", "警察", "士兵", "军官", "将军", "老师",
    "研究员", "管理员", "主持人", "记者", "编辑", "作家", "读者", "观众", "客人", "服务员",
    "司机", "工人", "农民", "商人", "学生", "考生", "选手", "对手", "冠军", "助理",
    # 人群通称
    "男人", "女人", "少年", "青年", "老人", "小孩", "孩子", "大家", "众人", "人群",
    "人类", "居民", "市民", "村民", "幸存者", "受害者", "参与者", "志愿者", "成员",
    "异种", "怪物", "丧尸", "感染者", "进化者", "异能者", "觉醒者", "复制体",
    "先生", "女士", "小姐", "夫人", "大人", "殿下", "阁下", "师傅", "师父", "主人",
    # 地点通称
    "学校", "教室", "食堂", "宿舍", "办公室", "实验室", "研究所", "医院", "病房",
    "基地", "总部", "分部", "房间", "走廊", "大厅", "广场", "街道", "城市", "城镇",
    "工厂", "仓库", "商场", "超市", "公园", "车站", "码头", "机场", "隧道", "地下",
    "废墟", "荒野", "森林", "山林", "河边", "山顶", "营地", "据点", "要塞",
    # ── v3.12 补充：论文视图把实体链接推到更多正文后，暴露出一批「普通词 → 某个具体人」
    #    的别名。这类链不是「不够精确」而是**必错**：正文里的「系统」「新世界」讲的是概念，
    #    不是祝宁；「主任」「部长」是职务，不是某一位主任。一律不链（错挂比不挂更糟）。
    #    职务 / 身份
    "主任", "部长", "局长", "处长", "科长", "店长", "馆长", "负责人", "主持人",
    "探员", "牙医", "教练", "女教师", "小老师", "监考", "领队", "队员",
    # 亲属 / 称呼
    "亲爹", "老爹", "岳父", "岳父大人", "老娘", "老二", "老三", "老头", "老者",
    "小男孩", "小女孩", "男方", "表姐", "姑娘", "大姐",
    # 泛称 / 群体
    "中介", "前台", "家长", "家长们", "学生们", "青年人", "坏人", "组员", "住户",
    "楼主", "小人", "婴儿", "老板娘", "有钱人", "本地人", "讲解员", "快递员",
    "保安队", "袭击者", "吸毒者", "游戏男", "女疯子", "小战士", "小明星", "残次品",
    # 隐喻绰号（同时是普通名词，最高危）
    "系统", "新世界", "恶魔", "火种", "真神", "宝贝", "武器", "领袖", "叛徒",
    "长官", "雇主", "老大", "先知", "净化器", "清理者",
}


def build_sections(md):
    """按标题切分，返回 [(sid, title, text)]；sid 与 md_to_html 生成的锚点逐字一致。"""
    used = set()
    out = []
    cur = None
    for raw in (md or "").replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        m = _H.match(line)
        if m:
            title = m.group(2).strip()
            sid = slugify(title, used)
            if cur:
                out.append(cur)
            cur = [sid, title, []]
            continue
        if cur is None:
            cur = ["sec", "（开头）", []]
        if not line:
            continue
        if line.startswith("|"):
            # 表格行保留单元格内容（学科文档的数据大量在表格里，跳过会漏掉实体），
            # 但丢掉分隔行 `---`；表头词不会命中实体表，无需特判。
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.match(r"^:?-{2,}:?$", c) for c in cells if c):
                continue
            cur[2].append(" ".join(c for c in cells if c))
        else:
            cur[2].append(line)
    if cur:
        out.append(cur)
    return [(s, t, " ".join(b)) for s, t, b in out]


def _strip_markup(s):
    """去掉 markdown 行内标记，只留纯文本用于匹配。"""
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = s.replace("**", "").replace("*", "")
    return s


def _add(mapping, surface, canon, blocked):
    """登记一个表面形式。长度 <2、通称、已被更长名占据的一律跳过。"""
    if not surface:
        return
    s = surface.strip()
    if len(s) < 2 or s in GENERIC_BLOCK or s in blocked:
        return
    if s in mapping and mapping[s] != canon:
        return          # 歧义表面形式（两个实体同名）→ 不链，避免错挂
    mapping[s] = canon


def build_entity_surfaces(data):
    """返回 (person_map, place_map, event_map)：表面形式 → 规范名 / 事件 id。"""
    alias_index = data.get("alias_index") or {}

    # 别名反查：{规范名: [别名...]}
    alias_by_canon = {}
    for surface, canon in alias_index.items():
        if isinstance(canon, str):
            alias_by_canon.setdefault(canon, []).append(surface)

    persons = {}
    for c in data.get("characters", []):
        name = (c.get("name") or "").strip()
        if not name:
            continue
        _add(persons, name, name, ())
        for a in (c.get("aliases") or []):
            _add(persons, a, name, ())
        for a in alias_by_canon.get(name, []):
            _add(persons, a, name, ())

    # 地点：人物已占用的表面形式不再作为地点（人物优先）
    places = {}
    for l in data.get("locations", []):
        name = (l.get("name") or "").strip()
        if not name:
            continue
        _add(places, name, name, persons)

    # 事件：人物/地点已占用的表面形式不再作为事件
    events = {}
    for e in data.get("events", []):
        name = (e.get("name") or "").strip()
        if not name:
            continue
        _add(events, name, e.get("id") or name, set(persons) | set(places))

    return persons, places, events


def _hits(text, mapping):
    """在 text 里找 mapping 的表面形式，长名优先（已占用区间不再被短名切走）。

    返回 (规范名 → 次数, 命中的表面形式 → 规范名)。后者用于裁剪 payload：
    整份实体表有数千个表面形式，但文档里真正出现的通常只有几十个，
    全量塞进 payload 会让单文件凭空涨 25%。
    """
    surfaces = sorted(mapping.keys(), key=lambda x: (-len(x), x))
    taken = [False] * len(text)
    found = {}
    hit_surfaces = {}
    for s in surfaces:
        start = 0
        while True:
            i = text.find(s, start)
            if i < 0:
                break
            start = i + 1
            if any(taken[i:i + len(s)]):
                continue
            for k in range(i, i + len(s)):
                taken[k] = True
            key = mapping[s]
            found[key] = found.get(key, 0) + 1
            hit_surfaces[s] = key
    return found, hit_surfaces


def build_insight_index(data, md):
    """产出前端用的联动索引。

    结构：
      titles   {sid: 小节标题}
      sections {sid: {p: [[规范名, 次数]], l: ..., e: [[事件id, 次数]]}}
      aliasP / aliasL  表面形式 → 规范名（含别名，已滤通称）
      eventId          事件名 → 事件 id
      byPerson / byPlace / byEvent  规范名 / 事件id → [sid...]
    """
    persons, places, events = build_entity_surfaces(data)
    sections = {}
    titles = {}
    by_person, by_place, by_event = {}, {}, {}

    # linked：只保留文档里真正出现过的表面形式（裁剪 payload，见 _hits 注释）
    linked = {}

    for sid, title, body in build_sections(md):
        text = _strip_markup(body)
        hp, sp = _hits(text, persons)
        hl, sl = _hits(text, places)
        he, se = _hits(text, events)
        for s, c in sp.items():
            linked.setdefault(s, ["p", c])
        for s, c in sl.items():
            linked.setdefault(s, ["l", c])
        for s, c in se.items():
            linked.setdefault(s, ["e", c])
        titles[sid] = title
        sections[sid] = {
            "p": sorted(hp.items(), key=lambda x: -x[1]),
            "l": sorted(hl.items(), key=lambda x: -x[1]),
            "e": sorted(he.items(), key=lambda x: -x[1]),
        }
        for k in hp:
            by_person.setdefault(k, []).append(sid)
        for k in hl:
            by_place.setdefault(k, []).append(sid)
        for k in he:
            by_event.setdefault(k, []).append(sid)

    return {
        "titles": titles,
        "sections": sections,
        # 前端只拿「文档里真命中的」表面形式，整份实体表不下发
        "linked": linked,
        "byPerson": by_person,
        "byPlace": by_place,
        "byEvent": by_event,
        # 规模自检用（不下发实体表，只留计数）
        "stats": {"persons": len(persons), "places": len(places), "events": len(events),
                  "linked": len(linked)},
    }


def extend_linked(ix, data, texts):
    """把「额外正文」（论文）里出现的实体并进 linked，让论文里的人也点得动。

    为什么单独一个函数，而不是给 build_insight_index 再加参数：
      - `sections` / `byPerson` / `titles` 是**学科视角文档**的锚点体系（sid 对不上就跳错地方），
        论文没有 sid，也不能污染这套反向索引；论文里点开人物后看到的「相关分析」chip
        仍应指回学科视角，通篇不该出现「相关分析：某论文小节」这种假锚点。
      - 论文里被点到的实体，只要 `linked` 里有它，前端就能链；不需要反向入口。
    只增不删，且沿用同一套 `_hits` + `GENERIC_BLOCK` 口径（长名优先 / 通称不链 / 歧义不链）。

    返回新增的表面形式个数；同时把计数写进 ix["stats"]。
    """
    persons, places, events = build_entity_surfaces(data)
    linked = ix["linked"]
    added = 0
    for text in texts or ():
        t = _strip_markup(text or "")
        if not t:
            continue
        for mapping, kind in ((persons, "p"), (places, "l"), (events, "e")):
            _, hit = _hits(t, mapping)
            for s, c in hit.items():
                if s not in linked:
                    linked[s] = [kind, c]
                    added += 1
    ix["stats"]["linked"] = len(linked)
    ix["stats"]["linked_by_papers"] = added
    return added


if __name__ == "__main__":
    # 自检入口：python src/insight_link.py
    import json
    import os
    import sys

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for book in ("tiancai", "feitu"):
        data = json.load(open(os.path.join(base, "data", book, "data.json"), encoding="utf-8"))
        md = open(os.path.join(base, "docs", "perspectives_%s.md" % book), encoding="utf-8").read()
        ix = build_insight_index(data, md)
        print("   实体表 %s → 下发 %d 个（裁剪 %.0f%%）"
              % (ix["stats"], ix["stats"]["linked"],
                 100.0 * (1 - ix["stats"]["linked"] /
                          max(1, sum(ix["stats"][k] for k in ("persons", "places", "events"))))))
        # 口径：次数 = 各节命中计数之和（不是「节×实体」对数）
        def total(key):
            return sum(c for v in ix["sections"].values() for _, c in v[key])
        print("%s: 节 %d | 人物命中 %d 次/%d 人 | 地点 %d 次/%d 个 | 事件 %d 次/%d 件"
              % (book, len(ix["sections"]),
                 total("p"), len(ix["byPerson"]),
                 total("l"), len(ix["byPlace"]),
                 total("e"), len(ix["byEvent"])))
        top = sorted(
            ((k, sum(c for s in v for kk, c in ix["sections"][s]["p"] if kk == k))
             for k, v in ix["byPerson"].items()), key=lambda x: -x[1])[:5]
        print("   人物 top:", top)
        print("   地点 top:", sorted(ix["byPlace"].items(), key=lambda x: -len(x[1]))[:3])
        sys.stdout.flush()
