# -*- coding: utf-8 -*-
"""
数据体检：量化「脏」的程度
==========================
用法：
  python src/quality_checkup.py            # 两本都跑
  python src/quality_checkup.py feitu      # 只跑一本

设计纪律（血泪版）
------------------
**体检口径必须与报告口径一致**。第一版脚本统计的是归约前的原始字段，
导致 type_reduce.py 早已修掉的「事件其他 43%」「关系 1396 种」仍然在体检结果里
报警——后人看到会以为没修，重复劳动。所以这里对同一指标同时给出
「归约前 / 归约后」两个数字，并且用归约后的口径判断是否需要处理。

只输出可核验的计数，不打分、不美化。最后给一张「待办清单」。
"""

import json
import os
import re
import sys
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 泛称：没有辨识度、不应作为独立实体的名字
GENERIC = [
    "护士", "医生", "男医生", "女医生", "助理医师", "众人", "人群", "男人", "女人",
    "老人", "小孩", "小男孩", "小女孩", "少年", "少女", "青年", "中年男人",
    "工作人员", "店员", "保安", "门卫", "司机", "乘客", "路人", "居民", "村民",
    "士兵", "军人", "警察", "学生", "老师", "顾客", "病人", "患者", "尸体",
    "负责人", "管理员", "检测人员", "研究员", "技术员", "调查员", "分析员",
    "黑衣人", "陌生人", "声音", "人影", "对方", "那个人",
]
REST_KEYS = ("其他", "其他场所", "其他关系", "未分类")


def pct(a, b):
    return f"{a}/{b}（{a / b * 100:.0f}%）" if b else "0/0"


def main():
    books = sys.argv[1:] or ["feitu", "tiancai"]
    for book in books:
        path = os.path.join(BASE, "data", book, "data.json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding="utf-8"))
        report(book, d)


def report(book, d):
    ps, ls, es, rs = d["characters"], d["locations"], d["events"], d["relations"]
    nch = len(d["chapters"])
    todo = []   # 待办清单：本轮真正需要处理的问题

    print(f"\n{'=' * 66}\n{book} 数据体检（{nch} 章）\n{'=' * 66}")

    # ---------- 1. 阵营字段 ----------
    print("\n【1】阵营字段（factions）")
    fc = sorted(len(p["factions"]) for p in ps)
    total_f, uniq_f = sum(fc), len({f for p in ps for f in p["factions"]})
    fm = Counter(p.get("faction_main") or "" for p in ps)
    no_fm = fm.get("", 0)
    print(f"  原始字符串 {total_f} 条 / {uniq_f} 种；每人物平均 {total_f / len(ps):.1f} 个，"
          f"最多 {fc[-1]} 个")
    print(f"  归约后（faction_main，报告用这个）：{len(fm) - (1 if no_fm else 0)} 种")
    print(f"  未标注任何归属：{pct(no_fm, len(ps))}  ← 已在阵营面板脚注披露")
    # 「-clean 中心 / 猎豹队」这类层级路径：同一阵营被按层级重复计数
    pathy = [f for p in ps for f in p["factions"] if f.count("/") >= 1]
    if pathy:
        print(f"  含「/」的层级路径型 faction：{pct(len(pathy), total_f)}"
              f"  ← 归约取主阵营后不再重复计数")
    if fc[-1] > 25:
        todo.append(("阵营", f"最多的人物挂了 {fc[-1]} 个阵营串（多为同一阵营的层级路径变体，"
                            "已按 faction_main 归约展示，不需处理，仅备注）"))

    # ---------- 2. 人物 ----------
    print("\n【2】人物实体")
    tier = Counter(p.get("tier") for p in ps)
    one_ch = sum(1 for p in ps if len(p["chapters"]) <= 1)
    generic_hit = [p["name"] for p in ps if p["name"] in GENERIC]
    # 泛称不等于脏。「技术员」在废土里出场 12 章、有 role 有关系，是固定角色；
    # 「检测人员」只出场 1 章且无关系，才是背景板。按 tier 分级判断：
    # 只有「泛称 + 单章」才算噪声，多章泛称是书里确有其人的职位型角色。
    gen_noise = [n for n in generic_hit
                 if any(p["name"] == n and len(p["chapters"]) <= 1 and not p.get("relations")
                        for p in ps)]
    gen_real = [n for n in generic_hit if n not in gen_noise]
    short_role = sum(1 for p in ps if len(p.get("role") or "") < 6)
    nore = sum(1 for p in ps if not p.get("role"))
    print(f"  总数 {len(ps)}；分层 核心 {tier.get('core', 0)} / 主要 {tier.get('major', 0)} / "
          f"次要 {tier.get('minor', 0)} / 龙套 {tier.get('cameo', 0)}")
    print(f"  只出场 1 章：{pct(one_ch, len(ps))}  ← 这是本书的取景特点，不是脏数据；"
          f"默认视图已折叠")
    print(f"  泛称命名共 {len(generic_hit)} 个 → {generic_hit[:8]}")
    if gen_real:
        print(f"    其中 {len(gen_real)} 个已形成稳定角色（多章/有关系），保留：{gen_real[:6]}")
    if gen_noise:
        print(f"    其中 {len(gen_noise)} 个是单章背景板：{gen_noise[:6]}")
    print(f"  role 缺失 {nore}，role 短于 6 字 {short_role}")
    ali = sum(len(p["aliases"]) for p in ps)
    print(f"  别名总数 {ali}，平均每人物 {ali / len(ps):.1f} 个")
    if gen_noise:
        todo.append(("人物", f"{len(gen_noise)} 个单章泛称背景板实体，可考虑合并或折叠："
                            f"{'、'.join(gen_noise[:6])}"))

    # ---------- 3. 事件 ----------
    print("\n【3】事件（对照归约前后）")
    raw = Counter(e.get("type") or "未分类" for e in es)
    base = Counter(e.get("type_base") or "其他" for e in es)
    raw_rest = sum(v for k, v in raw.items() if k in REST_KEYS)
    base_rest = sum(v for k, v in base.items() if k in REST_KEYS)
    print(f"  总数 {len(es)}")
    print(f"  归约前：{len(raw)} 种类型，兜底类占 {pct(raw_rest, len(es))}")
    print(f"  归约后：{len([k for k in base if k not in REST_KEYS])} 个功能类，"
          f"兜底类占 {pct(base_rest, len(es))}  ← 报告用这个口径")
    print(f"  归约后 Top6：{[(k, v) for k, v in base.most_common(6) if k not in REST_KEYS]}")
    one_ch_e = sum(1 for e in es if len(e["chapters"]) <= 1)
    nopart = sum(1 for e in es if not e.get("participants"))
    print(f"  只在 1 章出现：{pct(one_ch_e, len(es))}  ← 逐章抽取的必然结果，"
          f"说明「事件」是章节片段而非跨章事件")
    print(f"  无参与主体的事件：{nopart}")
    if base_rest / len(es) > 0.15:
        todo.append(("事件", f"归约后兜底类仍占 {base_rest / len(es) * 100:.1f}%，"
                             "可再补一轮关键词"))
    if nopart and nopart / len(es) > 0.05:
        todo.append(("事件", f"{nopart} 条事件无单一参与者（多为区域/群体级事件），"
                            "报告中已标注，但无法挂到具体人物"))

    # ---------- 4. 地点 ----------
    print("\n【4】地点")
    lraw = Counter(l.get("type") or "未分类" for l in ls)
    lbase = Counter(l.get("type_base") or "其他场所" for l in ls)
    lbase_rest = sum(v for k, v in lbase.items() if k in REST_KEYS)
    one_ch_l = sum(1 for l in ls if len(l["chapters"]) <= 1)
    print(f"  总数 {len(ls)}；归约前 {len(lraw)} 种 → 归约后 "
          f"{len([k for k in lbase if k not in REST_KEYS])} 类，"
          f"归约率 {(1 - lbase_rest / len(ls)) * 100:.1f}%")
    print(f"  只出现 1 章：{pct(one_ch_l, len(ls))}")
    reg = Counter((l.get("region") or "(空)").split("/")[0] for l in ls)
    print(f"  region 首段 Top6：{reg.most_common(6)}")
    vague = [l["name"] for l in ls if re.search(r"(房间|走廊|门口|角落|尽头|深处|入口|出口)$", l["name"])]
    print(f"  泛地点（以 房间/走廊/门口 结尾）：{len(vague)} → {vague[:6]}")
    # 分区覆盖：报告统一用 zone 显示，这里查「落不进任何分区」的剩余量
    unzoned_n = 0
    gpath = os.path.join(BASE, "data", book, "geo_annotations.json")
    if os.path.exists(gpath):
        ann = json.load(open(gpath, encoding="utf-8"))
        zc = Counter(v.get("zone") for v in ann.values())
        default_keys = {"unzoned", "outskirt"}
        unzoned_n = sum(v for k, v in zc.items() if k in default_keys)
        print(f"  示意分区覆盖：{[f'{k} {v}' for k, v in zc.most_common()]}")
        print(f"  未落区（unzoned/兜底）：{pct(unzoned_n, len(ls))}")
    # region 自由文本发散是已知事实（几百种取值），但报告已统一改用 zone 显示；
    # 真正需要处理的是「连 zone 都落不进去」的剩余量。
    if unzoned_n and unzoned_n / len(ls) > 0.05:
        todo.append(("地点", f"{unzoned_n} 个地点落不进任何示意分区"
                            f"（{unzoned_n / len(ls) * 100:.0f}%），需要补分区规则"))

    # ---------- 5. 关系 ----------
    print("\n【5】关系（对照归约前后）")
    rraw = Counter(r["rel"] for r in rs)
    rbase = Counter(r.get("rel_base") or "其他关系" for r in rs)
    rbase_rest = sum(v for k, v in rbase.items() if k in REST_KEYS)
    print(f"  总数 {len(rs)}")
    print(f"  归约前：{len(rraw)} 种自由文本，兜底占 {pct(rbase_rest, len(rs))}")
    print(f"  归约后：{len([k for k in rbase if k not in REST_KEYS])} 个基类，"
          f"Top6：{[(k, v) for k, v in rbase.most_common(6) if k not in REST_KEYS]}")
    same_pair = Counter((r["from"], r["to"]) for r in rs)
    multi = sum(1 for v in same_pair.values() if v > 1)
    print(f"  同一对实体间有多种关系描述：{multi} 对  ← 关系图已按「人-人」合并成一条边")
    dupn = sum(v - 1 for v in Counter((r["from"], r["to"], r["rel"]) for r in rs).values() if v > 1)
    print(f"  重复三元组：{dupn} 条冗余")
    # 孤岛人物
    linked = {r["from"] for r in rs} | {r["to"] for r in rs}
    lonely = [p["name"] for p in ps if p["name"] not in linked]
    print(f"  无关系孤岛人物：{pct(len(lonely), len(ps))} → {lonely[:8]}")
    if len(lonely) / len(ps) > 0.3:
        todo.append(("关系", f"{len(lonely)} 个人物没有任何关系（{len(lonely) / len(ps) * 100:.0f}%），"
                             "关系图对他们是空白的"))

    # ---------- 6. 信息密度 ----------
    print("\n【6】信息密度")
    print(f"  平均每章：人物 {sum(len(p['chapters']) for p in ps) / nch:.1f} 次 · "
          f"事件 {sum(len(e['chapters']) for e in es) / nch:.1f} 次")
    print(f"  平均每人出场 {sum(len(p['chapters']) for p in ps) / len(ps):.1f} 章 · "
          f"平均每事件覆盖 {sum(len(e['chapters']) for e in es) / len(es):.1f} 章")

    # ---------- 待办清单 ----------
    print(f"\n【待办】本轮需要处理 {len(todo)} 项")
    if not todo:
        print("  （无）当前无需要处理的问题")
    for i, (scope, desc) in enumerate(todo, 1):
        print(f"  {i}. [{scope}] {desc}")


if __name__ == "__main__":
    main()
