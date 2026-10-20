# -*- coding: utf-8 -*-
"""anthropology 篇统计底稿 —— 家国同构：名分、继承与互惠的文化语法。

一条命令复算：
  python papers_pilot/anthropology/_stats.py
落盘： .dump/_stats_anthropology.json

口径（三条铁律）：
  1. relations[].from/to 是裸人物名，按名字查，不做前缀映射。
  2. 亲属词判定前先把所有已知人物名（含别名）从 rel 文本里掩掉，
     否则「孙承宗」「孙传庭」这类人名里的「孙」会被误判为晚辈词。
  3. 截断桶必须改名，不沿用被截断的键名。
"""
import sys, os, json, collections, re

sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

OUT = {}

# ---------------- 0. 规模常量 ----------------
chars = md.characters()
rels = md.relations()
evs = md.events()
OUT["counts"] = {"characters": len(chars), "relations": len(rels),
                 "events": len(evs), "locations": len(md.locations())}

# ---------------- 1. 人物名掩码 ----------------
# ⚠️ 「太子」「皇子」「皇后」等在人物表里同时也是别名（指向具体某人），但它们本身
#    就是「家的词被用作国的职称」——正是本文要测的对象，故**不掩**，另立严格口径对照。
STOP_MASK = {"太子", "皇子", "皇太子", "懿文太子", "公主", "长公主",
             "太后", "皇太后", "皇后", "王妃", "太妃"}
_names = set()
for c in chars:
    if c.get("name"):
        _names.add(c["name"])
    for a in (c.get("aliases") or []):
        if len(str(a)) >= 2:
            _names.add(str(a))
NAMES = sorted(n for n in _names if n not in STOP_MASK)
NAMES.sort(key=len, reverse=True)
_MASK = "◆"


def mask(text):
    t = text or ""
    for nm in NAMES:
        if nm in t:
            t = t.replace(nm, _MASK * len(nm))
    return t


# ---------------- 2. 亲属关系的方向分布与代际跨度 ----------------
kin = [r for r in rels if r.get("category") == "亲属"]

# 长辈词 / 晚辈词 / 平辈词（掩码后再判）
SENIOR = ["祖", "父", "母", "叔", "伯", "舅", "姑", "姨", "翁", "岳"]
JUNIOR = ["子", "孙", "侄", "甥", "婿", "媳"]
FLAT = ["兄弟", "兄妹", "姐弟", "姐妹", "夫妻", "亲家", "内弟", "大舅子",
        "妹夫", "妻", "兄", "弟", "姐", "妹"]

# 代际跨度：复合词 -> 跨度（代）
SPAN = {"父子": 1, "母子": 1, "父女": 1, "母女": 1, "祖孙": 2, "祖父": 2,
        "祖母": 2, "叔侄": 1, "侄叔": 1, "翁婿": 1, "堂叔侄": 1, "外甥": 1,
        "养子": 1, "养父": 1, "继父": 1, "先祖": 2, "兄弟": 0, "夫妻": 0}


def direction(rel_text):
    """返回 (方向, 跨度)；方向 ∈ {down, up, flat, senior_only, junior_only, unknown}"""
    t = mask(rel_text)
    ps = min([t.find(w) for w in SENIOR if w in t] or [9999])
    pj = min([t.find(w) for w in JUNIOR if w in t] or [9999])
    pf = min([t.find(w) for w in FLAT if w in t] or [9999])
    if ps < 9999 and pj < 9999:
        return ("down" if ps < pj else "up"), span_of(rel_text)
    if pf < 9999:
        return "flat", 0
    if ps < 9999:
        return "senior_only", span_of(rel_text)
    if pj < 9999:
        return "junior_only", span_of(rel_text)
    return "unknown", 0


def span_of(rel_text):
    t = mask(rel_text)
    hits = [(t.find(k), v) for k, v in SPAN.items() if k in t]
    if not hits:
        return 0
    return sorted(hits)[0][1]


dir_cnt = collections.Counter()
span_cnt = collections.Counter()
dir_rows = []
for r in kin:
    d, s = direction(r.get("rel"))
    dir_cnt[d] += 1
    span_cnt[s] += 1
    dir_rows.append({"from": r.get("from"), "to": r.get("to"),
                     "rel": r.get("rel"), "dir": d, "span": s})

n_kin = len(kin)
OUT["kinship"] = {
    "n": n_kin,
    "direction_counts": dict(dir_cnt),
    "direction_pct": {k: round(100.0 * v / n_kin, 1) for k, v in dir_cnt.items()},
    "span_counts": {str(k): v for k, v in sorted(span_cnt.items())},
    "span_pct": {str(k): round(100.0 * v / n_kin, 1) for k, v in sorted(span_cnt.items())},
}
# 纵向 = down + up；横向 = flat；单侧标记单独列，不合并
vert = dir_cnt["down"] + dir_cnt["up"]
OUT["kinship"]["vertical_n"] = vert
OUT["kinship"]["vertical_pct"] = round(100.0 * vert / n_kin, 1)
OUT["kinship"]["flat_n"] = dir_cnt["flat"]
OUT["kinship"]["flat_pct"] = round(100.0 * dir_cnt["flat"] / n_kin, 1)
OUT["kinship"]["down_up_ratio"] = round(
    dir_cnt["down"] / float(dir_cnt["up"]), 2) if dir_cnt["up"] else None
# 下行占纵向的比例（方向不对称性）
OUT["kinship"]["down_share_of_vertical"] = round(100.0 * dir_cnt["down"] / vert, 1)

# ---------------- 3. 代际跨度的均值（只算纵向且跨度>0 的） ----------------
spans_pos = [r["span"] for r in dir_rows if r["dir"] in ("down", "up") and r["span"] > 0]
OUT["kinship"]["span_mean_vertical"] = round(sum(spans_pos) / float(len(spans_pos)), 3) if spans_pos else None
OUT["kinship"]["span_n_vertical"] = len(spans_pos)

# ---------------- 4. 家事国事化：亲属关系里的国家/权力语汇 ----------------
POWER = ["太子", "皇位", "继位", "传位", "篡", "监国", "削藩", "谋叛",
         "继统", "立为太子", "国本", "皇帝"]
kin_power = [r for r in dir_rows if any(w in (r["rel"] or "") for w in POWER)]
OUT["kinship"]["power_lexicon_n"] = len(kin_power)
OUT["kinship"]["power_lexicon_pct"] = round(100.0 * len(kin_power) / n_kin, 1)
OUT["kinship"]["power_lexicon_examples"] = [
    {"from": r["from"], "to": r["to"], "rel": r["rel"]} for r in kin_power[:14]]

# 亲属关系两端至少一端为帝王/皇族角色
name_idx = md.name_index()
ROYAL = ["皇帝", "太祖", "成祖", "宗", "王", "太子", "皇后", "太后", "贵妃", "妃"]
kin_royal = 0
for r in kin:
    for e in (r.get("from"), r.get("to")):
        role = (name_idx.get(e) or {}).get("role") or ""
        if any(w in role for w in ROYAL):
            kin_royal += 1
            break
OUT["kinship"]["royal_touching_n"] = kin_royal
OUT["kinship"]["royal_touching_pct"] = round(100.0 * kin_royal / n_kin, 1)

# ---------------- 5. 国事家语化：非亲属关系里的亲属语汇 ----------------
KINW = ["父", "母", "兄", "弟", "叔", "侄", "甥", "婿", "祖", "孙", "子"]
EXCLUDE = ["孔子", "公子", "弟子", "子弟", "天子", "臣子", "君子", "夫子",
           "老子", "庄子", "孟子", "妻子", "孝子", "才子"]


def has_kinword(text, strict=False):
    t = mask(text)
    for ex in EXCLUDE:
        t = t.replace(ex, _MASK * len(ex))
    if strict:  # 严格口径：把「太子/皇子」这类已职称化的词也排除，只留纯亲属语
        for ex in STOP_MASK:
            t = t.replace(ex, _MASK * len(ex))
    return [w for w in KINW if w in t]


tot_cat = collections.Counter(r.get("category") for r in rels)
hit_cat = collections.Counter()
hit_cat_strict = collections.Counter()
hit_examples = collections.defaultdict(list)
for r in rels:
    cat = r.get("category")
    if cat == "亲属":
        continue
    ws = has_kinword(r.get("rel"))
    if ws:
        hit_cat[cat] += 1
        if len(hit_examples[cat]) < 6:
            hit_examples[cat].append({"from": r.get("from"), "to": r.get("to"),
                                      "rel": r.get("rel"), "words": ws})
    if has_kinword(r.get("rel"), strict=True):
        hit_cat_strict[cat] += 1

nonkin_total = sum(v for k, v in tot_cat.items() if k != "亲属")
nonkin_hit = sum(hit_cat.values())
nonkin_hit_strict = sum(hit_cat_strict.values())
OUT["state_kin_vocab"] = {
    "nonkin_total": nonkin_total,
    "nonkin_hit": nonkin_hit,
    "nonkin_pct": round(100.0 * nonkin_hit / nonkin_total, 1),
    "nonkin_hit_strict": nonkin_hit_strict,
    "nonkin_pct_strict": round(100.0 * nonkin_hit_strict / nonkin_total, 1),
    "by_category": [{"category": k, "n": tot_cat[k], "hit": hit_cat[k],
                     "pct": round(100.0 * hit_cat[k] / tot_cat[k], 1),
                     "hit_strict": hit_cat_strict.get(k, 0),
                     "pct_strict": round(100.0 * hit_cat_strict.get(k, 0) / tot_cat[k], 1),
                     "examples": hit_examples[k]}
                    for k, _ in hit_cat.most_common()],
}
# 只看国家政治类（君臣从属 + 政治攻讦 + 敌对冲突 + 同盟友党）
POLCAT = ["君臣从属", "政治攻讦", "敌对冲突", "同盟友党"]
pol_n = sum(tot_cat[c] for c in POLCAT)
pol_h = sum(hit_cat[c] for c in POLCAT)
OUT["state_kin_vocab"]["political_n"] = pol_n
OUT["state_kin_vocab"]["political_hit"] = pol_h
OUT["state_kin_vocab"]["political_pct"] = round(100.0 * pol_h / pol_n, 1)
OUT["state_kin_vocab"]["political_hit_strict"] = sum(hit_cat_strict[c] for c in POLCAT)
OUT["state_kin_vocab"]["political_pct_strict"] = round(
    100.0 * sum(hit_cat_strict[c] for c in POLCAT) / pol_n, 1)
OUT["state_kin_vocab"]["junchen_n"] = tot_cat["君臣从属"]
OUT["state_kin_vocab"]["junchen_hit"] = hit_cat["君臣从属"]
OUT["state_kin_vocab"]["junchen_pct"] = round(100.0 * hit_cat["君臣从属"] / tot_cat["君臣从属"], 1)

# 对比基准：亲属关系本身含亲属语汇的比例（应接近 100%）
kin_self_hit = sum(1 for r in kin if has_kinword(r.get("rel")))
OUT["state_kin_vocab"]["kin_self_hit"] = kin_self_hit
OUT["state_kin_vocab"]["kin_self_pct"] = round(100.0 * kin_self_hit / n_kin, 1)
# 亲属类里出现「太子/皇子」等职称化亲属词的条数（家语被国用，发生在亲属类内部）
kin_title = sum(1 for r in kin if any(w in (r.get("rel") or "")
                                      for w in ["太子", "皇子", "皇后", "皇帝"]))
OUT["state_kin_vocab"]["kin_title_n"] = kin_title
OUT["state_kin_vocab"]["kin_title_pct"] = round(100.0 * kin_title / n_kin, 1)

# ---------------- 6. 继承序：人物 role 字段里的长幼/名分标注 ----------------
ORDER = ["长子", "次子", "三子", "四子", "幼子", "长孙", "太子", "皇子",
         "世子", "嫡子", "庶子", "嫡长", "长兄"]
order_cnt = {}
for w in ORDER:
    order_cnt[w] = sum(1 for c in chars if w in (c.get("role") or ""))
seq = ["长子", "次子", "三子", "四子", "幼子"]
OUT["succession_marking"] = {
    "by_term": order_cnt,
    "birth_order_terms": {w: order_cnt[w] for w in seq},
    "birth_order_total": sum(order_cnt[w] for w in seq),
    "birth_order_pct": round(100.0 * sum(order_cnt[w] for w in seq) / len(chars), 1),
    "taizi_n": order_cnt["太子"],
    "taizi_pct": round(100.0 * order_cnt["太子"] / len(chars), 1),
    "n_persons": len(chars),
}
# role 字段非空人数（分母口径）
OUT["succession_marking"]["role_nonempty"] = sum(1 for c in chars if (c.get("role") or "").strip())

# ---------------- 7. 互惠：师生同门 / 同盟友党 的规模 ----------------
OUT["reciprocity"] = {
    "shisheng_n": tot_cat["师生同门"],
    "tongmeng_n": tot_cat["同盟友党"],
    "marriage_n": tot_cat["婚姻姻亲"],
    "jun_chen_n": tot_cat["君臣从属"],
    "shisheng_pct": round(100.0 * tot_cat["师生同门"] / len(rels), 1),
    "tongmeng_pct": round(100.0 * tot_cat["同盟友党"] / len(rels), 1),
}
# 拟亲属：非亲属关系里出现「父/母/子/孙/兄弟」等**明确拟制亲属**词（不含太子等官职名）
FICTIVE = ["干儿子", "义子", "养子", "义孙", "干爹", "如母", "本生父母", "嫡母", "父子", "母子"]
# 「经营出来的关系」（师生 + 同盟 + 姻亲）与「血缘亲属」的规模对比
OUT["reciprocity"]["earned_total"] = (tot_cat["师生同门"] + tot_cat["同盟友党"]
                                      + tot_cat["婚姻姻亲"])
OUT["reciprocity"]["earned_over_blood"] = round(
    (tot_cat["师生同门"] + tot_cat["同盟友党"] + tot_cat["婚姻姻亲"]) / float(n_kin), 2)
fic = [r for r in rels if r.get("category") != "亲属" and any(w in (r.get("rel") or "") for w in FICTIVE)]
OUT["reciprocity"]["fictive_kin_n"] = len(fic)
OUT["reciprocity"]["fictive_kin_examples"] = [
    {"from": r.get("from"), "to": r.get("to"), "rel": r.get("rel")} for r in fic[:10]]

# ---------------- 8. 书内证据逐字核验 ----------------
QUOTES = [
    "如果再背上一个庶子的名分",
    "我修改了记录，所以我湮灭了证据",
    "影响了无数人的一生，以及大明王朝的国运，而这件事情，在历史上有个专用名词",
    "争国本",
    "立嫡不立长",
    "相当于皇帝的家规",
    "长幼有序",
    "我没有嫡子",
    "明代的官场网络大致由两种关系组成，一种是同学（同年），另一种是师生（门生）",
    "约定门生",
    "有奶就是娘，有权就是爹",
    "二十孩儿、四十猴孙、五百义孙",
    "以天子门生自居",
    "我就让我爹来收拾你们",
]
OUT["book_evidence"] = {q: md.hit_text(q) for q in QUOTES}

# ---------------- 9. 亲属 vs 君臣 两端的角色重合度 ----------------
kin_persons = set()
for r in kin:
    kin_persons.update([r.get("from"), r.get("to")])
jc_persons = set()
for r in rels:
    if r.get("category") == "君臣从属":
        jc_persons.update([r.get("from"), r.get("to")])
both = kin_persons & jc_persons
OUT["overlap"] = {
    "kin_persons": len(kin_persons),
    "jun_chen_persons": len(jc_persons),
    "both": len(both),
    "jaccard": round(len(both) / float(len(kin_persons | jc_persons)), 3),
    "both_examples": sorted(list(both))[:20],
}

path = md.write_stats("anthropology", OUT)
print("WROTE", path)
print(json.dumps({k: OUT[k] for k in ("counts", "kinship", "state_kin_vocab",
                                      "succession_marking", "overlap")},
                 ensure_ascii=False, indent=2)[:4000])
print("\nbook_evidence:", OUT["book_evidence"])
