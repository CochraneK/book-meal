# -*- coding: utf-8 -*-
"""
金句抽取
========
输入：小说原文 TXT + data/<book>/data.json（提供人物表与别名）
输出：data/<book>/quotes.json

为什么这样做
------------
报告里缺「金句名言」这一层。全书逐句让模型挑太贵（废土 209 万字），
而且模型挑出来的容易脱离原文。所以这里用**结构信号 + 主题打分**先做筛选，
再交给报告展示。两路来源，分开放：

  对白 —— 引号里的话，作者专门让人物说出来的。归属到具体人物。
  叙述 —— 引号外的文字。天才基本法的金句大半在这里，只挖对白会漏掉。
         其中第一人称的另标「独白」，不与旁白混为一谈。

三版失败，教训都写在下面（这是本脚本最值钱的部分）
--------------------------------------------------
1. 说话人归属：最早在引号前 24 字里找「(任意1-12字)+说/道/问」，
   候选组贪婪且含汉字 → 「祝宁又说道」被切成 候选=「祝宁又说」+「道」，
   600 条里冒出 383 个"说话人"（轻声/继续/又笑/道/完 都算人）。
   修法：按段落结构定位标签，且候选必须解析到人物表里的真人名，否则留空。

2. 打分：量的是「像不像一句话」，不是「能不能脱离语境成立」。
   v1 偏长 → 选出剧情解释；v2 把「因为/所以/其实/怎么」当主题词 → 满屏情节问答；
   v3 收窄成偏好短句 → 又漏进「这起码是八十年之前款式吧」这类情节陈述句。
   修法：硬门槛 = 谈大词 or 长成格言；再罚指代（这/那/他）与专名（绑在情节上）。

3. 回响信号：以为「作者重复写 = 作者认为重要」。
   废土成立（6767 句里仅 74 句重复，1.1%）；天才不成立 ——
   43% 的对白是草莓/芝士平行世界的同场景重演，不是金句回响，
   照搬会让「您来啦，我还以为您不来了呢」混进金句榜。
   修法：先算重复占比，>15% 就判定为结构性重播，关掉这个信号。

4. 章号：一开始用正则「第N章」定位，两本书**一个都没命中**
   （天才是「1.真实」，废土是裸标题「新工作」），705 条金句的章号静默变成 0。
   修法：改用 chapters.json 的正文前 100 字定位（439/221 章全部命中）。
   **凡是"没匹配到"的路径都必须报警，不能让它安静地退化成 0。**

设计纪律：宁可少收，不可错挂。说话人不确定时不硬填，重复不辨真伪时不加分。
"""

import json
import os
import re
import statistics
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OPENERS = "\u201c\u300c\u2018"
CLOSERS = "\u201d\u300d\u2019"
# 取整段对白（不设上限），随后按句切开 —— 见 split_sentences 的注释
QUOTE_BLOCK_RE = re.compile("[" + OPENERS + "]([^" + CLOSERS + "]{4,1200})[" + CLOSERS + "]")

# ---- 说话人线索 ----
# 踩过的坑（重要）：最早写成「引号前的 24 字里找 (任意1-12字)+说/道/问」，
# 候选组贪婪且包含汉字，于是「祝宁又说道」被切成 候选=「祝宁又说」+「道」，
# 「轻声」「继续」「又笑」这类副词碎片全被当成了人名 —— 600 条里冒出 383 个"说话人"。
# 现在改成：按**段落结构**定位标签，且候选必须能解析到人物表里的真实人物，否则宁可留空。
SAY_VERBS = ("说|道|问|答|喊|叫|补充|打断|反问|回答|解释|提醒|警告|安慰|质问|重复|继续|"
             "念|叹|笑|低声|沉声|轻声|喃喃|自语|嘟囔|嘀咕|开口|应|回|反驳|吩咐|嘱咐|"
             "承认|宣布|承诺|保证|试探|嘀咕|咕哝|评价|总结|提议|建议|命令")

# ① 引号后紧跟「祝宁问。」
TAG_AFTER = re.compile(r"^[，,、]?\s*([\u4e00-\u9fff]{1,8})\s*(?:" + SAY_VERBS + r")")
# ② 引号前、同句末的「……XX说：」
TAG_BEFORE = re.compile(r"([^\s，。！？、；：\n]{1,12})\s*(?:" + SAY_VERBS + r")"
                        r"[^。\n]{0,6}[：:]?\s*$")
# ③ 引号前、句首直接是人名（「祝宁干脆就演个疯子，“……”」）
TAG_HEAD = re.compile(r"^[\s　]*([^\s，。！？、；：\n「\u201c]{1,8})")
# ④ 上一段以「祝宁：」「祝宁说：」结尾（对话独立成段）
TAG_CROSS = re.compile(r"[\s　]*([\u4e00-\u9fff]{1,8})\s*(?:" + SAY_VERBS + r")?\s*[：:]\s*$")

# 代词不是说话人；名字前面是介词说明它是宾语不是主语
PRONOUNS = {"你", "我", "他", "她", "它", "们", "大家", "有人", "众人", "对方", "任何人",
            "所有人", "每个人", "别人", "那人", "这人", "一个", "两个"}
PREP_BEFORE = "对向和跟与把被让给替为同带叫请帮向朝冲"
STRIP_CHARS = "你说我他她它们\"\u201c\u201d：: ，,。！？、；\n　 "

# 「大词」：一句话在谈人生/世界/命运/选择这类东西时，才可能是金句
BIG = ["人生", "世界", "命运", "意义", "选择", "活着", "活下去", "死", "生命", "灵魂",
       "希望", "理想", "梦想", "相信", "自由", "公平", "真相", "真实", "代价",
       "值得", "永远", "从来", "勇气", "坚持", "放弃", "守护", "承诺", "记忆", "时间",
       "人性", "未来", "信仰", "孤独", "痛苦", "幸福", "遗憾", "后悔", "离别",
       "重逢", "归属", "同类", "怪物", "正义", "善良", "邪恶", "强大", "弱小", "害怕",
       "恐惧", "爱", "人类", "一生", "一辈子", "所有人", "每个人", "善", "恶",
       "凭什么", "为什么活", "一条命", "一条活路", "对不起", "谢谢", "抱歉"]
# 指代/现场词：一句话要靠「这/那/它/他」才读得懂，说明它离不开情节现场
DEIXIS = ["这", "那", "这儿", "那儿", "这里", "那里", "这个", "那个", "这时",
          "那边", "它", "他", "她", "你们", "咱们"]
# 「中词」：不够撑起一句金句，但能说明这句话在谈什么（现实题材小说的主战场）
MID = ["努力", "天赋", "天才", "学习", "数学", "机会", "运气", "公平", "成功", "失败",
       "长大", "重要", "擅长", "喜欢", "放弃", "遗憾", "答案", "问题", "朋友", "自己",
       "爸爸", "父亲", "女儿", "家人", "老师", "同学", "孩子", "聪明", "普通"]
# 格言句式：一句话只要长成这个样子，就算没有大词也自足
APHORISM = [r"不是[^，。]{1,12}[，,]\s*而是", r"只有[^，。]{1,12}[，,]\s*才",
            r"哪怕[^，。]{1,12}[，,]\s*也", r"就算[^，。]{1,12}[，,]\s*也",
            r"与其[^，。]{1,12}[，,]\s*不如", r"难道", r"凭什么", r"谁说",
            r"没什么大不了"]
# 句法骨架：名言的典型连接方式，权重低于大词
SKELETON = ["不是", "而是", "只有", "从来", "永远", "其实", "不过", "却", "但",
            "因为", "所以", "如果", "既然", "哪怕", "就算"]
# 情节问答标志：这些是推动剧情的问句，不是金句
ASK = ["吗", "呢", "为什么", "怎么", "什么", "是不是", "有没有", "会不会", "谁",
       "哪里", "哪儿", "多少"]
# 明显是日常对白/动作指令，直接排除
NOISE = ["开门", "过来", "走吧", "快点", "别吵", "吃饭", "睡觉", "多少钱", "在哪儿",
         "你在哪", "喂", "嗯", "啊", "哦", "喂？", "走开", "闭嘴", "等着", "别动",
         "给我", "拿来", "放下", "进来", "出去", "上车", "下车", "小心！", "快跑",
         "面板", "佩戴", "签到", "积分", "副本", "任务", "系统"]

MIN_LEN, MAX_LEN = 10, 80


def make_resolver(alias_to_canon, people_sorted):
    """把正则抓到的候选片段解析成人物表里的规范名。

    只认「候选里最靠右、且最长」的真人名。理由：汉语里名字紧贴动词，
    「祝宁又说道」→ 候选「祝宁又说」，最靠右的名字就是说话人；而
    「面对祝宁的疑问」→ 名字前面是介词「对」、后面是「的」，这是宾语，判掉。
    解析不出来就返回空 —— 宁可显示「未归属」，也不挂错人。
    """
    def resolve(cand):
        if not cand:
            return ""
        cand = cand.strip(STRIP_CHARS)
        if not cand or cand in PRONOUNS:
            return ""
        if cand in alias_to_canon:
            return alias_to_canon[cand]
        best, best_end = "", -1
        for n in people_sorted:              # 已按长度降序：同位置优先长名
            idx = cand.rfind(n)
            if idx < 0:
                continue
            end = idx + len(n)
            if end <= best_end:
                continue
            if idx > 0 and cand[idx - 1] in PREP_BEFORE:   # 「面对祝宁」→ 宾语
                continue
            if end < len(cand) and cand[end] == "的":      # 「祝宁的刀」→ 定语
                continue
            best, best_end = n, end
        return alias_to_canon.get(best, best) if best else ""
    return resolve


def split_paras(text, start, end):
    """取引号所在段落的前半 / 后半，以及上一段。对话标签的位置决定了归属规则。"""
    ps = text.rfind("\n", 0, start)
    ps = 0 if ps < 0 else ps + 1
    pe = text.find("\n", end)
    pe = len(text) if pe < 0 else pe
    p2 = text.rfind("\n", 0, max(0, ps - 1))
    p2 = 0 if p2 < 0 else p2 + 1
    return text[ps:start], text[end:pe], text[p2:ps]


def find_speaker(pre, post, prev, resolve):
    """按可靠性排序找说话人：作者明确标的 > 结构推断 > 不猜。

    返回 (说话人, 依据)。依据会写进 JSON，报告里可以披露「这句话为什么算他说的」。
    """
    m = TAG_AFTER.match(post)            # ① “……”祝宁问。
    if m:
        r = resolve(m.group(1))
        if r:
            return r, "引号后标签"
    seg = re.split(r"[。！？]", pre)[-1]  # 只看最后一句，避免上文干扰
    m = TAG_BEFORE.search(seg)           # ② ……祝宁说：“……”
    if m:
        r = resolve(m.group(1))
        if r:
            return r, "引号前标签"
    m = TAG_HEAD.match(seg)              # ③ 祝宁干脆就演个疯子，“……”
    if m:
        r = resolve(m.group(1))
        if r:
            return r, "句首人名"
    m = TAG_CROSS.search(prev)           # ④ 上一段「祝宁：」+ 本段纯对白
    if m:
        r = resolve(m.group(1))
        if r:
            return r, "上段人名"
    return "", ""


def norm(text):
    """归一化：全半角逗号、省略号不同不算两句话。"""
    return re.sub(r"[\s，。！？、；：,\.\?!\"'…—\-—_]", "", text)


def split_sentences(block):
    """把一整段对白切成句子，返回 (句子, 段内偏移)。

    踩过的坑：最初用 `[^”]{8,110}` 只收「整段引号内容」，结果凡是被包在长对白
    里的名句，都随着整段一起被丢弃 —— 「那么我的病是我的病，你的人生是你的人生。」
    就死在这里（它后面还跟着半段解释，整块超过 110 字）。
    改成先取整段、再按句末标点切开，长对白里的名句才捞得出来。
    """
    out = []
    for m in re.finditer(r"[^。！？]*[。！？]|[^。！？]+$", block):
        t = m.group(0).strip()
        if t:
            out.append((t, m.start()))
    return out


def score(text, echo=1.0, entities=frozenset()):
    """给一句话打「金句度」。

    三版教训，都记在这里：
      第一版「长 + 主题词多」 → 选出复杂剧情解释和业务话术；
      第二版把「因为/所以/其实/怎么」也算主题词 → 选出满屏情节问答
        （「他们为什么都聚在学校了？那边是不是有什么东西我们错过了？」）；
      第三版收窄成偏好短句 → 又漏进一批**情节陈述句**
        （「这起码是八十年之前款式吧。」「意思是清洁中心放弃我们了。」）。

    这三版都栽在同一个地方：它们量的是「这句话像不像一句话」，
    而不是「这句话能不能脱离语境单独成立」。第四版改成后者：

      ① 硬门槛：必须谈「人生/世界/命运/选择/死/爱」这类大词。
         不谈任何大词的句子，无论多工整，都是情节零件。
      ② 指代罚：靠「这/那/它/他」才读得懂 → 绑在情节现场，罚。
      ③ 专名罚：句子里出现别的人物/地点 → 读者得先认识那个人，罚。
      ④ 回响奖：作者自己重复写过的句子，重奖。
         注意 echo 是**相对频率**（除以全书对白出现次数的中位数）：
         天才基本法的源 TXT 有大段重复（同一句出现过 17 次），
         用绝对次数会把「复制粘贴」误当成「作者刻意回响」。
    """
    if len(text) < MIN_LEN or len(text) > MAX_LEN:
        return -99
    s = 0
    L = len(text)
    # 凝练优先：12-30 字是名言的舒适区，越长越不像
    if 12 <= L <= 30:
        s += 6
    elif 30 < L <= 45:
        s += 2
    else:
        s -= 4
    # 逗号数量 = 句子复杂度。名言通常一口气说完
    commas = text.count("，") + text.count(",")
    if commas == 0:
        s += 3
    elif commas == 1:
        s += 1
    elif commas >= 3:
        s -= 4

    # ① 门槛：既不谈大词、又不长成格言 → 情节零件，出局。
    # 注意：MID（中词）和 echo（回响）都不能开门，它们只是加分项。
    # 原因见 build() 里的 repeat_share —— 天才基本法有 43% 的对白是平行世界重演，
    # 若让 echo 开门，等于把「场景重播」当成了「作者金句」。
    big = [w for w in BIG if w in text]
    aphor = any(re.search(p, text) for p in APHORISM)
    if not big and not aphor:
        return -99
    s += min(len(big), 3) * 3
    s += min(sum(1 for w in MID if w in text), 4) * 2     # 中词
    s += 2 if aphor else 0
    s += min(sum(1 for w in SKELETON if w in text), 4)    # 句法骨架
    # ② 指代罚 / ③ 专名罚
    s -= min(sum(1 for w in DEIXIS if w in text), 4)
    if entities and any(e in text for e in entities):
        s -= 4
    for w in NOISE:
        if text.startswith(w) or (w in text and L < 16):
            s -= 5

    # 疑问句：几乎都是推动剧情，不是金句
    if "？" in text or "?" in text:
        s -= 2
        if any(w in text for w in ASK):
            s -= 6
    tail = text.rstrip()[-1:]
    if tail in "。！":
        s += 2
    elif tail in "？?":
        s -= 1
    else:
        s -= 3          # 没句末标点 = 多半是被引号截断的半截话，不成句
    # 语气词结尾（吧/啊/呢/吗/呀）：口语碎句，不是可引用的判断。
    # 这比一刀切抬阈值好 —— 「你听谁说的，怎么这么八卦」正是栽在这里。
    if re.search(r"[吧啊呢吗哦嘛咧呀]\s*[。！？!?]?$", text):
        s -= 3

    if re.search(r"[^，。]{1,10}是[^，。]{1,10}", text):     # 判断句
        s += 2
    if re.search(r"[你我他她][都总也]?[永远从来一直]", text):  # 全称判断
        s += 2
    if text.count("…") + text.count("...") >= 2:
        s -= 2
    zh = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    if zh < L * 0.6:
        s -= 4
    if echo >= 2:              # 作者自己重复的句子，一定是作者认为重要的
        s += 6
    return s


def chapter_marks(text, chapters):
    """把每一章在原文里的起始位置标出来。

    踩过的坑：我一开始用正则「第N章」找章节，两本书**一个都没命中** ——
    天才基本法的标题是「1.真实」，废土的是裸标题「新工作」。
    于是全部 705 条金句的章号静默变成了 0，而统计上完全看不出来。

    改成用 chapters.json 里每章正文的开头 100 字去定位：
    两本书 439 / 221 章全部命中，位置单调递增。
    教训：**凡是"没匹配到"的路径都要报警**，不能让它安静地退化成 0。
    """
    marks, pos = [], 0
    for c in chapters:
        body = c.get("body", "")
        i = text.find(body[:100], pos)
        if i < 0:                                   # 退而求其次：找标题行
            h = c.get("heading_raw", "")
            j = text.find("\n" + h + "\n", pos)
            i = j + 1 if j >= 0 else pos
        marks.append(i)
        pos = i + max(1, len(body) - 300)
    if any(marks[i] > marks[i + 1] for i in range(len(marks) - 1)):
        print(f"  [warn] 章节定位非单调，章号可能不准")
    return marks


def mine_narration(text, entities):
    """从**非对白**的叙述文字里挖金句。

    为什么要这一路：天才基本法的对白几乎全是数学题和日常拌嘴，它真正被读者
    记住的句子在叙述里（「就算是开局坏到极点的人生，也还有无限可能。」）。
    只挖对白会得出「这本书没有金句」的错误结论。

    做法：把引号内容整段抹成等长换行（保住偏移量，章号才对得上），
    剩下的就是叙述，再按句切开。旁白不挂到任何角色名下，报告里单列
    「叙述者」一栏 —— 不能让人以为某个人物说了这句话。
    """
    plain = QUOTE_BLOCK_RE.sub(lambda m: "\n" * len(m.group(0)), text)
    skip = re.compile(r"第[0-9零一二三四五六七八九十百]+[章节]|本书名称|来源来自|"
                      r"内容版权|请于下载|http|www\.|版权归作者")
    seen, out = set(), []
    for m in re.finditer(r"[^\n。！？]{10,80}[。！？]", plain):
        s = m.group(0).strip().lstrip("—-·　 ")
        if not s or skip.search(s):
            continue
        key = norm(s)
        if key in seen:
            continue
        seen.add(key)
        sc = score(s, 1.0, entities)
        if sc <= 0:
            continue
        # 第一人称的句子不是「旁白」，是角色的内心独白。两者必须分开标：
        # 报告里把它们混成一类，读者会以为叙述者在说自己。
        kind = "独白" if (s.startswith(("我", "我们")) or
                     re.search(r"(?:我想|我觉得|我知道|我以为|我相信|我希望|我逃|我对)", s)) \
            else "叙述"
        out.append({"t": s, "s": "", "h": kind, "k": "n", "sc": sc,
                    "e": 1.0, "pos": m.start()})
    return out


def build(book, src_name):
    txt_path = os.path.join(BASE, src_name)
    if not os.path.exists(txt_path):
        print(f"[skip] 缺原文 {src_name}")
        return
    text = open(txt_path, encoding="utf-8", errors="replace").read()
    d = json.load(open(os.path.join(BASE, "data", book, "data.json"), encoding="utf-8"))

    alias_to_canon = {}
    for p in d["characters"]:
        alias_to_canon[p["name"]] = p["name"]
        for a in p.get("aliases", []):
            alias_to_canon[a] = p["name"]
    people_sorted = sorted(set(alias_to_canon), key=len, reverse=True)
    resolve = make_resolver(alias_to_canon, people_sorted)

    # 专名表：句子里出现具体人物/地点 = 绑在情节上，读者得先认识它
    entities = set()
    for p in d["characters"]:
        for n in [p["name"]] + list(p.get("aliases", [])):
            if len(n) >= 2:
                entities.add(n)
    for l in d.get("locations", []):
        n = l.get("name", "")
        if 2 <= len(n) <= 6:
            entities.add(n)

    blocks = [(m.group(1), m.start(), m.end()) for m in QUOTE_BLOCK_RE.finditer(text)]
    pieces = []
    for block, b0, b1 in blocks:
        for sent, off in split_sentences(block):
            pieces.append((sent, b0 + off, b0, b1))

    # 统计每句对白出现次数。用**中位数**做基准再算倍率：
    # 若源 TXT 整体被复制过，绝对次数会把复制粘贴误判成作者回响；
    # 除以中位数后，「回响」才是真的回响。
    echo = Counter(norm(s) for s, _, _, _ in pieces)
    base = max(1, statistics.median(echo.values()))
    # 重复到底是「作者刻意回响」还是「结构性重播」？用一个比例判别：
    #   废土 —— 6767 句里只有 74 句重复（1.1%）→ 少数重复 = 刻意强调，回响信号可用
    #   天才 —— 907 句里 387 句重复（42.7%）→ 那是草莓/芝士平行世界的同场景重演，
    #           不是金句回响。此时必须关掉这个信号，否则它给 87% 的候选各加 6 分，
    #           「您来啦，我还以为您不来了呢」也能混进金句榜。
    rep_share = sum(1 for v in echo.values() if v >= 2) / max(1, len(echo))
    echo_on = rep_share < 0.15

    # 说话人按**整段对白**判定一次，段内每句继承（同一段通常同一人说）。
    # 这样既省掉逐句重复解析，也避免段中间的承上启下句被误挂给别人。
    seen, out = set(), {}
    for block, b0, b1 in blocks:
        pre, post, prev = split_paras(text, b0, b1)
        sp, how = find_speaker(pre, post, prev, resolve)
        for sent, off in split_sentences(block):
            key = norm(sent)
            if key in seen:
                continue                   # 同一句在别处出现过，保留首次判定
            seen.add(key)
            sc = score(sent, (echo[key] / base) if echo_on else 1.0, entities)
            if sc <= 0:
                continue
            out[key] = {"t": sent, "s": sp, "h": how, "k": "d", "sc": sc,
                        "pos": b0 + off,
                        "e": round((echo[key] / base) if echo_on else 1.0, 2)}
    out = list(out.values())
    narr = mine_narration(text, entities)

    # 章号：按 chapters.json 的正文位置回填（见 chapter_marks 的注释）
    ch_path = os.path.join(BASE, "data", book, "chapters.json")
    chapters = json.load(open(ch_path, encoding="utf-8")) if os.path.exists(ch_path) else []
    marks = chapter_marks(text, chapters) if chapters else []
    for q in out + narr:
        idx = 0
        for i, p in enumerate(marks):
            if p <= q["pos"]:
                idx = i
            else:
                break
        q["ch"] = idx + 1 if marks else 0
        q["ct"] = chapters[idx].get("chapter_title", "") if marks and idx < len(chapters) else ""
        del q["pos"]

    out.sort(key=lambda x: (-x["sc"], x["ch"]))

    out.sort(key=lambda x: (-x["sc"], x["ch"]))
    narr.sort(key=lambda x: (-x["sc"], x["ch"]))

    # ---- 精选 ----
    # 初筛几千条里绝大多数是剧情对白，全塞进报告等于没选。两道收口：
    #   ① 阈值再提一档，只留「像句子」的
    #   ② 每人限 15 条，避免主角（出场 426 章）把整个语录集占满
    # 旁白另算：它没有说话人，只取前 80 条最高分，报告里单列一栏。
    # MIN_SC 是「够不够格进报告」的线。试过 6 和 7：6 放进游戏规则
    # （「变规则，每次只能取4颗」），7 仍放进闲聊（「你听谁说的，怎么这么八卦」）。
    # 宁可少而精 —— 金句榜的价值来自"没有凑数的"，不是"条目多"。
    PER_PERSON, MIN_SC, NARR_CAP = 15, 9, 80
    picked, cnt = [], {}
    for q in out:
        if q["sc"] < MIN_SC:
            break   # out 已按得分降序，后面都够不上，直接停
        who = q["s"] or ""
        if cnt.get(who, 0) >= PER_PERSON:
            continue
        cnt[who] = cnt.get(who, 0) + 1
        picked.append(q)
    npicked = [q for q in narr if q["sc"] >= MIN_SC][:NARR_CAP]

    # 按人归组（报告的主视图就是「谁说了什么」），说话人按出场章数排序。
    # tier 与全书其余视图同一套口径：核心≥20章 / 主要≥5 / 次要≥2 / 客串1
    chapters_of = {p["name"]: len(p.get("chapters", []) or []) for p in d["characters"]}
    by_person = {}
    for q in picked:
        if q["s"]:
            by_person.setdefault(q["s"], []).append(q)
    people_rank = sorted(by_person.items(),
                         key=lambda kv: (-chapters_of.get(kv[0], 0), -len(kv[1]), kv[0]))

    def tier_of(n):
        c = chapters_of.get(n, 0)
        return "core" if c >= 20 else "major" if c >= 5 else "minor" if c >= 2 else "cameo"

    attrib = sum(1 for q in picked if q["s"])
    # 总榜：两路各留 60 席再混排。旁白天然比口语凝练，若直接按分数混排，
    # 「谁说了什么」会被整片挤掉（废土试过，前 14 条里 13 条是旁白）。
    top = sorted(picked[:60] + npicked[:60], key=lambda x: (-x["sc"], x["ch"]))[:120]
    payload = {
        "meta": {
            "book": book,
            "candidates": len(out),
            "narr_candidates": len(narr),
            "picked": len(picked),
            "narr_picked": len(npicked),
            "attributed": attrib,
            "speakers": len(by_person),
            "per_person_cap": PER_PERSON,
            "min_score": MIN_SC,
            "dialogue_lines": len(echo),
            "repeated_share": round(rep_share, 3),
            "echo_signal": echo_on,
            "how_counts": dict(Counter(q["h"] for q in picked if q["h"])),
        },
        "quotes": picked,
        "narration": npicked,
        "top": top,
        "by_person": [{"name": k, "chapters": chapters_of.get(k, 0),
                       "tier": tier_of(k), "quotes": v}
                      for k, v in people_rank],
    }
    path = os.path.join(BASE, "data", book, "quotes.json")
    json.dump(payload, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[done] {book}：初筛 {len(out)} → 精选 {len(picked)} 条 | "
          f"已归属 {attrib}（{attrib / max(1, len(picked)) * 100:.0f}%）| "
          f"{len(by_person)} 位说话人 | 叙述 {len(npicked)}/{len(narr)} 条 | "
          f"对白重复率 {rep_share:.1%}（回响信号{'开' if echo_on else '关'}）")


def main():
    books = sys.argv[1:] or ["feitu", "tiancai"]
    for b in books:
        src = "我在废土世界扫垃圾.txt" if b == "feitu" else "天才基本法.txt"
        build(b, src)


if __name__ == "__main__":
    main()
