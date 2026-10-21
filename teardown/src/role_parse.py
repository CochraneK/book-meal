# -*- coding: utf-8 -*-
"""把 characters[].role 的裸串解析成可筛选的结构化字段（A5）。

三条原则（照搬 ming 的 faction_profile）：
1. **词表驱动**，不用自由生成——只认下面写死的模式，命中不了就留空；
2. **宁可留空不可猜错**——推断不出就不给值，绝不拿「22岁」当身份；
3. **原串保留可回查**——结构化字段只是索引，详情里始终显示原文。

输出字段（都只在命中时出现）：
- id  主身份：首分句里**最靠后**的身份词（汉语中心语后置：「…的领导」是领导不是实习生）
- rel 亲属/从属关系：「林朝夕之父」→ {"to":"林朝夕","k":"父"}
- st  在场状态：「未出场」「已故」「仅被提及」

状态为什么要求 n_chapters==1：role 串描述的是**该章**的在场情况，
「（本章被提及）」出现在裴之（131 章）身上就是明证。只有全书只出现 1 章的人，
「未出场/仅被提及」才等于全书事实。出场多的角色一律不给 st——宁可留空。
"""
import re

# 身份词表：按「越长越优先」匹配，避免「医生」抢在「心理医生」前面
IDENTITIES = [
    "女主角", "男主角", "女主", "男主", "主角", "反派", "配角",
    "大四实习生", "实习生", "助理", "秘书", "顾问", "研究员", "研究生", "博士生",
    "班主任", "奥数老师", "老师", "教师", "教授", "校长", "院长", "园长",
    "心理医生", "医生", "医师", "护士", "药剂师",
    "警察", "刑警", "法医", "律师", "法官", "记者", "编辑", "作家",
    "清理者", "赏金猎人", "猎人", "拾荒者", "雇佣兵", "士兵", "军人", "队长",
    "学生会成员", "小学生", "中学生", "大学生", "学生", "学徒",
    "工人", "工程师", "技师", "技术员",
    "店主", "老板", "商人", "企业家", "会计", "司机", "门卫", "保安", "厨师",
    "部长", "主任", "领导", "经理", "总监", "会长", "成员",
    "人工智能", "AI", "系统", "实验体", "异能者", "感染者", "变异体",
    "孤儿", "养女", "养子",
]
IDENTITIES.sort(key=len, reverse=True)

# 「学生」必须不是「学生会/学生家长」这类复合词的一部分
_BOUNDARY = {"学生": re.compile(r"学生(?!会|家长)")}

# 亲属/从属关系：之X 与 的X 两族
_KIN = "父|母|妻|夫|子|女|兄|弟|姐|妹|孙|婿|媳"
_ROLE_REL = ("父亲|母亲|妻子|丈夫|儿子|女儿|家人|亲属|助手|助理|合作者|同事|朋友|邻居"
             "|学生|老师|师父|徒弟|队长|上司|下属|房东|客户")
REL_PATTERNS = [
    re.compile(r"([\u4e00-\u9fa5A-Za-z0-9·]{1,10})之(" + _KIN + r")"),
    re.compile(r"([\u4e00-\u9fa5A-Za-z0-9·]{1,10})的(" + _ROLE_REL + r")"),
]
# 关系主体必须是「名字样的东西」：长度 ≤6 且不含功能词/指示词/动词开头，
# 否则是把整个短语吞进来（「推动沈美去找裴之的学生会成员」「看裴之星星眼的学生群体」）
_BAD_TO = re.compile(r"[的了着过给让被把和与在为对向从去来找将已]"
                     r"|^(附近|同|某|该|这|那|其|一|另一)"
                     r"|^(看|说|想|笑|哭|打|走|来)")
MAX_TO = 6

# 首分句以动词/介词开头 → 整句是「干了什么」而不是「是谁」，不取身份
VERB_HEAD = re.compile(r"^(负责|参与|出现|作为|被|将|把|因|为|与|和|给|在|从|向|对|让|使|令|曾任|担任)")
# 以「…的人 / …者」收尾 → 描述性从句，中心语不是身份
DESC_HEAD = re.compile(r"(的人|者|之一)$")
# 身份词后面紧跟亲属词 → 那是关系不是身份（「实验体母亲」）
_KIN_SUFFIX = re.compile(r"^(母亲|父亲|妻子|丈夫|儿子|女儿|家人|亲属)")

STATUS_PATTERNS = [
    ("未出场", re.compile(r"未出场|未登场|没有出场|未正式登场")),
    ("已故", re.compile(r"已故|已死|死亡|阵亡|牺牲|死后|遗体")),
    ("仅被提及", re.compile(r"仅被提及|仅提及|只在.{0,6}提及|被提及")),
]
# 弱信号：只有没有更强状态时才用（「已故调查者（仅被提及）」要报已故）
WEAK_STATUS = {"仅被提及"}

_NOISE = re.compile(r"\d+岁|本章|回忆|梦中|幻境")
# 「见证/目睹某人死亡」——死亡的是别人，不是这个角色
_WITNESS = re.compile(r"目睹|见证|看到|看见|得知|报告|发现")


def _first_clause(raw):
    return re.split(r"[，,。；;]", raw, maxsplit=1)[0].strip()


def _identity(head):
    """首分句里的**中心语**身份词。

    汉语中心语后置，且身份词基本都在分句末尾（「…的领导」「…的大学教授」）。
    所以只认「结束位置在分句末尾」的匹配，长度相同取更长的那个——这条约束
    一次性挡掉了「负责…押回逃跑实验体」把实验体当身份这类错。
    """
    if not head or _NOISE.search(head):
        return ""
    # 「陆志浩：班主任许老师之子」——首分句讲的是他爹，不能当他的身份
    head = re.sub(r"^.{1,10}之(" + _KIN + r")", "", head).strip()
    if not head or VERB_HEAD.search(head) or DESC_HEAD.search(head):
        return ""
    best, best_end = "", -1
    for w in IDENTITIES:
        pat = _BOUNDARY.get(w)
        i = (pat.search(head).start() if pat.search(head) else -1) if pat else head.rfind(w)
        if i < 0:
            continue
        end = i + len(w)
        if end != len(head):
            continue                       # 不是中心语
        if _KIN_SUFFIX.search(head[end:]):
            continue
        if end > best_end or (end == best_end and len(w) > len(best)):
            best, best_end = w, end
    return best


def _relation(raw):
    best = None
    for pat in REL_PATTERNS:
        m = pat.search(raw)
        if not m:
            continue
        to, k = m.group(1), m.group(2)
        if len(to) > MAX_TO or _BAD_TO.search(to):
            continue        # 「推动沈美去找裴之的学生会成员」不是亲属关系
        if best is None or m.start() < best[0]:
            best = (m.start(), to, k)
    return {"to": best[1], "k": best[2]} if best else None


def _status(raw, n_chapters):
    if n_chapters is not None and n_chapters != 1:
        return ""       # 出场多章的人，role 里的在场描述只对该章成立
    strong, weak = [], []
    for label, pat in STATUS_PATTERNS:
        if not pat.search(raw):
            continue
        if label == "已故" and _WITNESS.search(raw):
            continue
        (weak if label in WEAK_STATUS else strong).append(label)
    pick = strong or weak
    return pick[0] if pick else ""


def parse_role(raw, n_chapters=None):
    """返回 {id, rel:{to,k}, st}；全未命中返回 {}。"""
    if not raw or not isinstance(raw, str):
        return {}
    out = {}
    i = _identity(_first_clause(raw))
    if i:
        out["id"] = i
    r = _relation(raw)
    if r:
        out["rel"] = r
    s = _status(raw, n_chapters)
    if s:
        out["st"] = s
    return out


def coverage(chars):
    """characters 列表 → (n, {id,rel,st,any})，供构建期 INFO 披露（低覆盖必须让人看见）。"""
    n = len(chars)
    got = {"id": 0, "rel": 0, "st": 0, "any": 0}
    for c in chars:
        p = parse_role(c.get("role", ""), len(c.get("chapters") or []))
        if not p:
            continue
        got["any"] += 1
        for k in ("id", "rel", "st"):
            if k in p:
                got[k] += 1
    return n, got
