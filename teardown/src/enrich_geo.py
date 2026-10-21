# -*- coding: utf-8 -*-
"""
拆书流水线 · 阶段④ 地理增强
============================
给 data/<book>/data.json 的地点补坐标，输出：
  data/<book>/geo_annotations.json   {地点名: {coords, geo_status, source, zone}}
  data/<book>/geo_zones.json         [{key, label, cx, cy, r, desc}]（示意坐标系的区块定义）

三种地理模型（按 config.json 的 kind + 词典命中决定）：
  real      真实地名（上海/北京/南京/清华…）→ 真实经纬度 (lng, lat)
  schematic 虚构地点 → 自建示意坐标系 (x, y) ∈ [0,100]，明确标注「非现实坐标，仅示意」
            · modern_real 书（天才基本法）：虚构的「安宁市」按城区功能分带
              （大学城 / 中小学区 / 居住街巷 / 生活服务 / 城郊）
            · fictional_world 书（废土）：墙内核心 / 副本空间 / 墙外废土 / 污染区
  pending   无法归类 → 待核验，不硬填

坐标元组顺序：real=(lng, lat)（经度在前，审计查 abs(lat)>90）；schematic=(x, y)。
"""

import hashlib
import json
import math
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 真实地名词典（lng, lat, 今址说明, 来源）
GAZ = {
    "上海": (121.4737, 31.2304, "上海市", "GAZ 内置词典"),
    "北京": (116.4074, 39.9042, "北京市", "GAZ 内置词典"),
    "南京": (118.7969, 32.0603, "南京市", "GAZ 内置词典"),
    "清华": (116.3266, 39.9998, "北京·清华大学", "GAZ 内置词典"),
    "北大": (116.3100, 39.9878, "北京·北京大学", "GAZ 内置词典"),
    "复旦": (121.5020, 31.2989, "上海·复旦大学", "GAZ 内置词典"),
    "交大": (121.4370, 31.0300, "上海·上海交通大学", "GAZ 内置词典"),
}

# 天才基本法·虚构安宁市：城区功能分带（示意坐标，非现实地理）
# prio = 特异度。越小越泛：泛词区（life/home）当兜底，具体区（campus/school）优先。
TC_ZONES = [
    {"key": "campus", "label": "大学城", "cx": 30, "cy": 28, "r": 13, "prio": 60,
     "kws": ["大学", "学院", "校区", "图书馆", "阶梯教室", "学生会", "活动中心", "礼堂",
             "数学系", "教研室", "实验室", "教学楼", "科研所"]},
    {"key": "school", "label": "中小学区", "cx": 72, "cy": 30, "r": 12, "prio": 60,
     "kws": ["小学", "中学", "附中", "初中", "学校", "教室", "考场", "操场", "奥数班",
             "班主任", "辅导班", "夏令营", "兴趣班", "希望工程"]},
    # 飞地 1：草莓世界是本书「另一个世界」的核心设定，不能混在城郊里
    {"key": "otherworld", "label": "异世界（草莓/芝士世界）", "cx": 90, "cy": 86, "r": 9, "prio": 95,
     "kws": ["草莓世界", "芝士世界", "另一个自己", "上辈子", "穿越", "平行"]},
    # 飞地 2：故事主体在安宁市，永川市/莫斯科/机场属于外地
    {"key": "away", "label": "外地/境外", "cx": 10, "cy": 86, "r": 11, "prio": 95,
     "kws": ["莫斯科", "永川", "境外", "外地", "机场", "出差", "外省"]},
    {"key": "home", "label": "居住街巷", "cx": 34, "cy": 66, "r": 13, "prio": 30,
     "kws": ["小区", "巷", "新村", "宿舍", "福利院", "门卫", "公寓", "院", "家",
             "天井", "居民区", "小平房", "平房", "楼道", "老房"]},
    {"key": "life", "label": "生活服务", "cx": 66, "cy": 66, "r": 13, "prio": 20,
     "kws": ["医院", "店", "面馆", "咖啡", "超市", "烧烤", "摊", "公园", "街", "餐厅",
             "银行", "派出所", "网吧", "网咖", "商场", "公交站", "公交", "路边", "车站",
             "警局", "交管", "政务", "承安区", "路基"]},
]
TC_OUTSKIRT = {"key": "outskirt", "label": "城郊/其他", "cx": 50, "cy": 47, "r": 40}

# 废土·架空世界：同心分带（墙内核心 → 副本 → 废土 → 污染区）+ 两个「飞地」
# 判定三级：region 前缀 → 关键词（按特异度）→ unzoned。
#
# 为什么必须给 prio（上一版踩的坑）：
#   旧逻辑按列表顺序取「第一个命中」，而 wall_in 排第一且含「公司/家/公寓」
#   这类泛词，结果「鲍瑞铭的意识体云端」被 wall_in 或 instance 抢走、
#   16 处地点结论互相打架；另有 75 处无任何命中，被硬塞进 wasteland——
#   「刘年年豪宅」「祝宁的房间」明明在墙内，却被扔到墙外废土。
#   泛elench = 兜底，不应当大哥。
FT_ZONES = [
    # 飞地最具体：词出现就基本确定，优先级最高
    {"key": "cloud", "label": "网络/云端", "cx": 88, "cy": 13, "r": 8, "prio": 90,
     "kws": ["网络", "云端", "意识体", "副脑", "系统", "论坛", "直播间", "内部网络",
             "虚拟", "数据", "群聊", "坟贴", "主页"]},
    {"key": "north", "label": "极北之地", "cx": 50, "cy": 8, "r": 9, "prio": 90,
     "kws": ["极北", "北地", "沙鹤队", "鹿角"]},
    {"key": "instance", "label": "副本空间", "cx": 50, "cy": 50, "r": 26, "prio": 60,
     "kws": ["副本", "火锅店", "海洋馆", "牙医", "VIP", "乌托邦", "空中门", "神降",
             "永生", "另一个自己", "红房子", "神国", "小鬼", "序列"]},
    {"key": "polluted", "label": "污染区", "cx": 50, "cy": 50, "r": 45, "prio": 60,
     "kws": ["污染", "丧尸", "霉菌", "孢子", "死亡冰柱", "蝌蚪人", "蟾蜍人", "金市"]},
    {"key": "wasteland", "label": "墙外废土", "cx": 50, "cy": 50, "r": 34, "prio": 40,
     "kws": ["墙外", "废土", "荒村", "避难所", "列车", "补给站", "坟场", "巨人森林",
             "松山寺", "北墙", "一级防护", "黑鸟市", "丰渔村", "驻扎军",
             "军团", "交警", "公路", "雪原"]},
    # 墙内词最泛（公司/家/住宅/房间到处都是），只能当兜底
    {"key": "wall_in", "label": "墙内核心", "cx": 50, "cy": 50, "r": 14, "prio": 10,
     "kws": ["墙内", "城内", "市区", "公司", "清洁中心", "基金会", "公寓", "宅",
             "小区", "栋", "豪宅", "住宅", "区"]},
]
# 兜底：不再假装归类。旧版把没命中的全扔给 wasteland，
# 等于给「祝宁的房间」编了一个「墙外废土」的假位置。
FT_UNZONED = {"key": "unzoned", "label": "未归类", "cx": 50, "cy": 50, "r": 48, "prio": 0}
FT_DEFAULT = FT_UNZONED

# region 首段 → 分区 key（优先级最高）
FT_PREFIX = {
    "墙内": "wall_in",
    "墙外": "wasteland",
    "副本空间": "instance",
    "污染区": "polluted",
    "污染区域": "polluted",
    "网络空间": "cloud",
    "云端": "cloud",
    "极北之地": "north",
    "北地": "north",
}


def stable_hash(s):
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF


def zone_for(loc, zones, default, prefix_map=None):
    """判定地点属于哪个示意分区。判定顺序（从强到弱，不能随意调换）：

    0) 地名本身命中「高特异度」分区 → 直接采用
       「极北之地」被抽取者标成 region=墙外/一级防护墙外，但地名已经说明
       它就是极北飞地；「乌托邦地下」同理属副本。地名比 region 稳定得多
       （region 有 390 种自由取值，是最不可靠的字段），所以专名优先。
    1) region 首段前缀 —— 有层级路径时用它
    2) 关键词，按特异度 prio 取最高（不是取列表第一个）
    3) 都不中 → 兜底分区（unzoned），不硬塞进任何一个具体区
    """
    name = (loc.get("name") or "").strip()
    region = (loc.get("region") or "").strip()
    text = region + name + (loc.get("type") or "")

    # 0) 专名优先：只看名字，且只认特异度��的分区（飞地/副本/污染区），
    #    墙内(prio 10)、墙外(40) 这类泛区不参与，避免「黑鸟市的学校」被地名抢走。
    if name:
        strong = [z for z in zones
                  if z.get("prio", 50) >= 60 and any(k in name for k in z.get("kws", []))]
        if strong:
            strong.sort(key=lambda z: z.get("prio", 50), reverse=True)
            return strong[0]

    # 1) region 前缀
    if prefix_map:
        key = prefix_map.get(region.split("/")[0].strip())
        if key:
            for z in zones:
                if z["key"] == key:
                    return z

    # 2) 关键词按特异度
    hits = []
    for i, z in enumerate(zones):
        if any(k in text for k in z.get("kws", [])):
            hits.append((z.get("prio", 50), -i, z))
    if hits:
        hits.sort(key=lambda h: (h[0], h[1]), reverse=True)
        return hits[0][2]
    return default


def schematic_point(name, zone):
    """确定性散布：同名地点每次构建坐标一致。

    取值压在 [2, 88]。为什么不铺满 [0,100]：示意坐标与真实经纬度共用
    coords 字段，一旦出现 >90 的值就会被当成可疑纬度（旧审计就是这么误报的）。
    留出边界余量，让「示意 ≠ 经纬度」这件事在数值上也说得清。
    """
    a = stable_hash(name) * 6.2831853
    rad = (0.18 + 0.82 * stable_hash(name + "r")) * zone["r"]
    x = zone["cx"] + rad * math.cos(a)
    y = zone["cy"] + rad * math.sin(a) * 0.74
    return [round(max(2, min(88, x)), 2), round(max(2, min(88, y)), 2)]


def match_gaz(loc):
    for g in GAZ:
        if g in loc["name"] or g in (loc.get("modern") or ""):
            return g
    return None


def build(book_id):
    cfg = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
    kind = cfg["books"][book_id]["kind"]
    ddir = os.path.join(BASE, "data", book_id)
    data = json.load(open(os.path.join(ddir, "data.json"), encoding="utf-8"))

    zones = TC_ZONES if kind == "modern_real" else FT_ZONES
    default_zone = TC_OUTSKIRT if kind == "modern_real" else FT_DEFAULT
    # 第一遍：逐个判定初始分区
    raw_zone = {}
    ann = {}
    for loc in data["locations"]:
        g = match_gaz(loc)
        if g:
            raw_zone[loc["name"]] = "real"
            continue
        z = zone_for(loc, zones, default_zone,
                     FT_PREFIX if kind != "modern_real" else None)
        raw_zone[loc["name"]] = z["key"]

    # 第二遍：让「祝宁的房间」「二号诊室」这类子空间继承所属建筑的分区。
    # 依据不是猜：它的 region / 名字里明确写了母地名（region=蜂巢内、小白兔口腔四楼）。
    # 只在明确包含时继承，命中多个取出现最多、其次名字最长的那个。
    for loc in data["locations"]:
        if raw_zone.get(loc["name"]) != default_zone["key"]:
            continue
        text = (loc.get("region") or "") + "／" + loc["name"]
        best, best_key = None, ""
        for parent, pz in raw_zone.items():
            if parent == loc["name"] or pz in (default_zone["key"], "real"):
                continue
            if parent in text and len(parent) >= 2:
                if best is None or len(parent) > len(best):
                    best, best_key = parent, pz
        if best:
            raw_zone[loc["name"]] = best_key

    zone_by_key = {z["key"]: z for z in zones}
    zone_by_key[default_zone["key"]] = default_zone
    for name, key in raw_zone.items():
        if key == "real":
            continue
        z = zone_by_key[key]
        ann[name] = {
            "coords": schematic_point(name, z),
            "geo_status": "schematic",
            "modern": "",
            "source": "示意坐标系（虚构地点，仅表现空间关系）",
            "zone": z["key"],
        }
    # GAZ 命中的真实地名仍走真实坐标（前一轮已排除，这里补回）
    for loc in data["locations"]:
        g = match_gaz(loc)
        if g:
            lng, lat, modern, src = GAZ[g]
            ann[loc["name"]] = {"coords": [lng, lat], "geo_status": "real",
                                "modern": modern, "source": src, "zone": "real"}

    with open(os.path.join(ddir, "geo_annotations.json"), "w", encoding="utf-8") as f:
        json.dump(ann, f, ensure_ascii=False, indent=1)

    zone_defs = [{"key": z["key"], "label": z["label"], "cx": z["cx"], "cy": z["cy"], "r": z["r"]}
                 for z in zones]
    if default_zone not in zones:
        zone_defs.append({"key": default_zone["key"], "label": default_zone["label"],
                          "cx": default_zone["cx"], "cy": default_zone["cy"], "r": default_zone["r"]})
    with open(os.path.join(ddir, "geo_zones.json"), "w", encoding="utf-8") as f:
        json.dump(zone_defs, f, ensure_ascii=False, indent=1)

    n_real = sum(1 for v in ann.values() if v["geo_status"] == "real")
    n_sch = sum(1 for v in ann.values() if v["geo_status"] == "schematic")
    n_pend = sum(1 for v in ann.values() if v["geo_status"] == "pending")
    print(f"[done] {book_id} 地理标注 {len(ann)} 条：real {n_real} / schematic {n_sch} / pending {n_pend}"
          f"；示意分区 {len(zones)} 个")


def main():
    for b in (sys.argv[1:] or json.load(open(os.path.join(BASE, "config.json"),
                                             encoding="utf-8"))["books"]):
        build(b)


if __name__ == "__main__":
    main()
