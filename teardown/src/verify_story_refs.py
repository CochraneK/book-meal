# -*- coding: utf-8 -*-
"""story_<book>.md 的引用章号与声明计数回算复核。

长文是人工写的，写错章号不会报错，只会静默给出一个看似合理的数。
这个脚本把文中每个「第N章」、每个「共 N 章」、每个章号-标题归属
全部拿 data.json 回算一遍，不一致就打印 MISMATCH。

用法：
    python src/verify_story_refs.py            # 两本都查
    python src/verify_story_refs.py tiancai    # 只查一本
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
# 共享核心：章号换算与阶段划分的唯一真源
from core.chapters import build_key2no, no_of  # noqa: E402
from core.phases import derive_phases  # noqa: E402
PY = sys.executable


def load(book):
    d = json.load(open(os.path.join(BASE, "data", book, "data.json"), encoding="utf-8"))
    # 章号一律用正文标题章号 no，不用抽取器索引 index（防盗章会导致 index != no）
    key2no = build_key2no(d["chapters"])
    no2title = {no_of(c): c.get("title", "") for c in d["chapters"]}
    return d, key2no, no2title


def nos(e, key2no):
    return sorted({key2no[c] for c in (e.get("chapters") or []) if c in key2no})


def chs(events, key2no, kws, mode="any"):
    """事件名+摘要命中关键词的章号集合。"""
    s = set()
    for e in events:
        blob = e["name"] + " " + (e.get("note") or "")
        hit = all(k in blob for k in kws) if mode == "all" else any(k in blob for k in kws)
        if hit:
            s.update(nos(e, key2no))
    return sorted(s)


def sig_chapters(d, key2no, a, b, tb):
    """场景重演签名：前两个核心人物 + 事件类型，一个事件只记 first_no。

    口径必须与 src/story_material.py 完全一致，否则和素材包重演表对不上。
    """
    core = {p["name"] for p in d["characters"] if p.get("tier") == "core"}
    out = set()
    for e in d["events"]:
        ps = [p for p in (e.get("participants") or []) if p in core]
        ns = nos(e, key2no)
        if not ps or not ns:
            continue
        if (tuple(sorted(ps)[:2]), e.get("type_base") or "其他") == (tuple(sorted([a, b])), tb):
            out.add(min(ns))
    return sorted(out)


def cited_numbers(txt):
    """抓 「第 12、13、51 章」这类写法里的所有数字。"""
    out = set()
    for m in re.finditer(r"第\s*(\d+(?:\s*、\s*\d+)*)\s*章", txt):
        for x in re.split(r"[、\s]+", m.group(1)):
            if x:
                out.add(int(x))
    return out


# 每本书要回算的声明：(标签, 实算章号列表, 文中声明的章号列表)
def build_checks_tiancai(d, key2no):
    E = d["events"]
    return [
        ("心算王重演 16 章",
         sig_chapters(d, key2no, "张老师", "林朝夕", "冲突对峙"),
         [12, 13, 32, 51, 71, 81, 93, 103, 107, 117, 144, 175, 182, 188, 190, 214]),
        ("病是我的病 7 章", chs(E, key2no, ["病是我的病"]),
         [61, 63, 123, 127, 137, 173, 197]),
        ("赌约 10 章", chs(E, key2no, ["省团体"]),
         [16, 34, 49, 87, 89, 110, 128, 155, 161, 191]),
        ("收养 12 章",
         sorted(set(chs(E, key2no, ["一并收养", "连她", "陈述"])) |
                set(chs(E, key2no, ["先天拇指"]))),
         [16, 34, 87, 89, 110, 128, 146, 155, 161, 176, 184, 191]),
        ("284/亲和数 10 章", chs(E, key2no, ["亲和数"]),
         [15, 40, 46, 80, 129, 177, 187, 195, 211, 212]),
        ("旧居无人 14 章",
         chs(E, key2no, ["房间整洁", "无人居住痕迹", "扒窗", "干净整洁",
                         "无小女孩痕迹", "无女孩痕迹", "空房无人", "无人居住"]),
         [8, 45, 75, 83, 99, 100, 105, 120, 124, 159, 172, 183, 185, 205]),
        ("没爹妈 9 章", chs(E, key2no, ["没爹妈"]),
         [10, 35, 73, 77, 82, 156, 157, 162, 185]),
        ("曾珊珊第10题 8 章", chs(E, key2no, ["第10题"]),
         [11, 43, 55, 74, 102, 111, 116, 174]),
        ("婉拒相亲 11 章", chs(E, key2no, ["婉拒"]),
         [2, 28, 31, 37, 41, 66, 135, 163, 168, 170, 208]),
        ("人生规划 8 章", chs(E, key2no, ["人生规划"]),
         [27, 38, 39, 54, 133, 196, 217, 218]),
        ("跳跳糖 3 章", chs(E, key2no, ["跳跳糖"]), [42, 70, 151]),
    ]


def build_checks_feitu(d, key2no):
    """废土的断言是另一套：结局章节归属 + 阶段结构 + 场景重演签名。"""
    E = d["events"]
    core = {p["name"] for p in d["characters"] if p.get("tier") == "core"}
    # 场景重演签名（祝宁单人 + 类型）
    sig = {}
    for e in E:
        ps = [p for p in (e.get("participants") or []) if p in core]
        ns = nos(e, key2no)
        if not ps or not ns:
            continue
        k = (tuple(sorted(ps)[:2]), e.get("type_base") or "其他")
        sig.setdefault(k, set()).add(min(ns))
    def sg(tb):
        return sorted(sig.get((("祝宁",), tb), set()))
    # 阶段结构：副本弧 / 主线 / 序章 / 番外
    ph = derive_phases("feitu", d["chapters"])
    arcs = [p["name"] for p in ph if "主线" not in p["name"]
            and "序章" not in p["name"] and "番外" not in p["name"]]
    mains = [p for p in ph if "主线" in p["name"]]
    # 每个副本弧的事件条数
    cnt = {}
    for name in arcs:
        p = [x for x in ph if x["name"] == name][0]
        c = sum(1 for e in E if nos(e, key2no) and
                p["s"] <= min(nos(e, key2no)) <= p["e"])
        cnt[name] = c
    zhuning_quest = [1, 4, 6, 7, 9, 12, 13, 14, 15, 16, 19, 20, 22, 29, 31, 32, 33, 34, 35,
                     44, 46, 47, 48, 55, 56, 58, 65, 71, 72, 73, 74, 75, 76, 77, 79, 80, 82,
                     102, 112, 114, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 137,
                     150, 152, 157, 159, 171, 172, 173, 174, 175, 176, 181, 183, 185, 186,
                     196, 197, 198, 203, 204, 206, 207, 208, 209, 210, 211, 216, 217, 219,
                     220, 228, 233, 239, 240, 241, 242, 260, 261, 262, 263, 264, 265, 269,
                     270, 274, 290, 291, 375, 421]
    checks = [
        ("祝宁·副本任务 99 章", sg("副本任务"), zhuning_quest),
        ("祝宁·科研医疗 17 章", sg("科研医疗"),
         [9, 23, 41, 60, 61, 117, 144, 161, 181, 209, 217, 234, 245, 271, 373, 421, 422]),
        ("hello,world @250", chs(E, key2no, ["hello"]), [250]),
        ("我是来吃掉你的 @409", chs(E, key2no, ["吃掉你"]), [409]),
        ("吞噬世界 @436", chs(E, key2no, ["吞噬世界"]), [436]),
        ("裴书一声汪 @385", chs(E, key2no, ["汪"]), [385]),
        ("9999步 @185", chs(E, key2no, ["9999"]), [185]),
    ]
    # 阶段结构断言（用特殊标记：期望的弧数/主线数/事件条数表）
    print("    [阶段结构] 43 个 = 副本弧 %d + 主线 %d + 序章/番外 %d"
          % (len(arcs), len(mains), len(ph) - len(arcs) - len(mains)))
    ok_phase = (len(arcs), len(mains), len(ph)) == (17, 23, 43)
    print("    %s 文中声明：17 个副本弧 + 23 段主线 + 序章 1 + 番外 2 = 43"
          % ("OK  " if ok_phase else "MISMATCH"))
    claimed = {"吃人的火锅店": 55, "追杀人的房子": 60, "怪奇海洋馆": 80, "黑色牙医馆": 93,
               "遗落的荒村": 86, "无法离开的公司": 97, "杀死VIP": 81, "另一个自己": 55,
               "永生药业基金会": 159, "神降": 64, "丧尸之城": 108, "霉菌之城": 49,
               "归乡号列车": 77, "蟾蜍人": 26, "蝌蚪痣": 29, "空中门": 51, "乌托邦": 23}
    bad = {k: (v, cnt[k]) for k, v in claimed.items() if cnt[k] != v}
    print("    %s 17 个副本弧的事件条数逐一复核%s"
          % ("OK  " if not bad else "MISMATCH", "" if not bad else "，不一致: %s" % bad))
    return checks, ok_phase and not bad


TITLE_CHECKS = {"tiancai": [(207, "报告"), (210, "奔走"), (221, "尾声"), (197, "母亲"),
                            (109, "变化"), (114, "假设"), (175, "一话"), (19, "章亮")],
                "feitu": [(250, ""), (409, ""), (436, ""), (385, ""), (185, ""),
                          (437, ""), (438, ""), (439, "")]}


def run(book):
    d, key2no, no2title = load(book)
    doc = os.path.join(BASE, "docs", "story_%s.md" % book)
    if not os.path.exists(doc):
        print("!! 缺文件：%s" % doc)
        return False
    txt = open(doc, encoding="utf-8").read()
    ok = True

    cited = cited_numbers(txt)
    bad = [n for n in sorted(cited) if n not in no2title]
    print("[1] 引用章号 %d 个，不存在的: %s" % (len(cited), bad or "无"))
    ok &= not bad

    print("[2] 声明的章号集合 vs 实算：")
    if book == "feitu":
        checks, ok_phase = build_checks_feitu(d, key2no)
        ok &= ok_phase
    else:
        checks = build_checks_tiancai(d, key2no)
    for label, got, claimed in checks:
        same = got == claimed
        ok &= same
        print("    %s %-18s 文中=%d 实算=%d %s"
              % ("OK  " if same else "MISMATCH", label, len(claimed), len(got),
                 "" if same else "\n        文中=%s\n        实算=%s" % (claimed, got)))

    print("[3] 章号存在性（废土只验章号存在，标题另由逐章抽检覆盖）：")
    for n, t in TITLE_CHECKS[book]:
        got = no2title.get(n)
        if t:
            same = got == t
            ok &= same
            print("    %s 第%d章 文中《%s》 实际《%s》" % ("OK  " if same else "MISMATCH", n, t, got))
        else:
            print("    OK   第%d章《%s》 存在" % (n, got))

    have = set()
    for e in d["events"]:
        have.update(nos(e, key2no))
    empty = [n for n in range(1, max(no2title) + 1) if n not in have]
    print("[4] 空章（完全无事件的章号）: %s" % (empty or "无"))
    ok &= not empty

    print("    => %s\n" % ("全部通过" if ok else "存在不一致，需复查"))
    return ok


if __name__ == "__main__":
    books = sys.argv[1:] or ["tiancai", "feitu"]
    allok = all(run(b) for b in books)
    sys.exit(0 if allok else 1)
