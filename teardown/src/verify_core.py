# -*- coding: utf-8 -*-
"""
共享核心自检（src/verify_core.py）
==================================
src/core 是阶段划分与章号换算的唯一真源。本脚本守住三件事：

1. **阶段回归**：core 派生结果必须与重构前基线 ``core/baseline_phases.json``
   逐格相同（index 口径 + no 口径）。改了算法而结果不同 → 立即失败。
2. **章号口径不变量**：key2no / idx2no 与基线一致；no 必须全 int；
   两书 index↔no 的对齐关系符合已知事实（废土 index==no，天才 112 后 index=no+3）。
3. **唯一真源治理**：src/ 下不得再出现 derive_phases 的第二份定义
   （此前在 generate_report.py 与 perspectives_prep.py 各存一份，是 v3.3 漂移的根因）。

用法：
    python src/verify_core.py              # 检查（默认）
    python src/verify_core.py --snapshot   # 用当前 core 重刷基线（确认行为变更后才用）

退出码：0=全一致；1=有回归或违规。
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.books import BOOK_IDS, load, path  # noqa: E402
from core.chapters import build_idx2no, build_key2no  # noqa: E402
from core.phases import derive_phases, phases_to_no  # noqa: E402

SRC = os.path.dirname(os.path.abspath(__file__))          # .../src
BASELINE = os.path.join(SRC, "core", "baseline_phases.json")

fails = []


def chk(cond, msg):
    if cond:
        print("  [OK] " + msg)
    else:
        print("  [FAIL] " + msg)
        fails.append(msg)


print("=" * 68)
print("共享核心自检")
print("=" * 68)

# ---------------------------------------------------------------- 1. 唯一真源治理
print("\n[1] 唯一真源：src/ 下不得有第二份阶段派生定义")
# 只扫 src/*.py（不含 core/ 子目录 —— 那里是唯一真源本身）
src_files = [f for f in glob.glob(os.path.join(SRC, "*.py"))
             if os.path.basename(f) != "verify_core.py"]
dup = []
for f in src_files:
    txt = open(f, encoding="utf-8").read()
    # 只看「定义」，import/调用不算
    if re.search(r"^def\s+derive_phases", txt, re.M):
        dup.append(os.path.basename(f))
chk(not dup, "无重复的 derive_phases 定义" + ("（发现：%s）" % dup if dup else ""))

# 章号换算也不允许各自为政（只允许 core/chapters.py 定义 build_*2no）
dup2 = []
for f in src_files:
    txt = open(f, encoding="utf-8").read()
    if re.search(r"^def\s+build_(key2no|idx2no)", txt, re.M):
        dup2.append(os.path.basename(f))
chk(not dup2, "无重复的 build_key2no/idx2no 定义" + ("（发现：%s）" % dup2 if dup2 else ""))

# ---------------------------------------------------------------- 2. 阶段回归
print("\n[2] 阶段回归：与基线逐格比对")
base = load(BASELINE, {})
if not base:
    chk(False, "基线文件缺失：%s" % BASELINE)
else:
    for book in BOOK_IDS:
        data = load(path("data", book, "data.json"))
        raw = load(path("data", book, "extract_raw.json"), [])
        chapters = data["chapters"]
        idx2no = build_idx2no(chapters)

        got_idx = derive_phases(book, chapters, raw)
        got_no = phases_to_no(got_idx, idx2no)

        b = base.get(book, {})
        chk(got_idx == b.get("index"),
            "%s index 口径 %d 段与基线一致" % (book, len(got_idx)))
        chk(got_no == b.get("no"),
            "%s no 口径 %d 段与基线一致" % (book, len(got_no)))

# ---------------------------------------------------------------- 3. 章号口径不变量
print("\n[3] 章号口径不变量")
for book in BOOK_IDS:
    data = load(path("data", book, "data.json"))
    chapters = data["chapters"]
    k2n = build_key2no(chapters)
    i2n = build_idx2no(chapters)

    chk(all(isinstance(v, int) for v in k2n.values()) and
        all(isinstance(v, int) for v in i2n.values()),
        "%s 章号全为 int（防 str/int 混用静默出错）" % book)

    chk(len(set(k2n.values())) == len(chapters),
        "%s key→no 一一对应（%d 章）" % (book, len(chapters)))

    if book == "feitu":
        bad = [i for i, n in i2n.items() if i != n]
        chk(not bad, "废土 index == no（%d 章）" % len(i2n))
    else:
        # 天才：index 112 之后 index = no + 3（防盗章伪影）
        chk(max(i2n.values()) == 221 and max(i2n) == 224,
            "天才 no 最大 221 / index 最大 224")
        late = {i: n for i, n in i2n.items() if i > 112}
        chk(all(i == n + 3 for i, n in late.items()),
            "天才 index>112 满足 index = no + 3（%d 章）" % len(late))

# ---------------------------------------------------------------- 4. 阶段覆盖
print("\n[4] 阶段覆盖（如实披露，非失败）")
for book in BOOK_IDS:
    data = load(path("data", book, "data.json"))
    chapters = data["chapters"]
    idx2no = build_idx2no(chapters)
    ph = phases_to_no(derive_phases(
        book, chapters, load(path("data", book, "extract_raw.json"), [])), idx2no)
    covered = set()
    for p in ph:
        covered |= set(range(p["s"], p["e"] + 1))
    allno = set(idx2no.values())
    miss = sorted(allno - covered)
    print("  [INFO] %s：%d 章，未落入任何阶段 %s"
          % (book, len(allno), miss if miss else "无"))

print("\n" + "=" * 68)
if fails:
    print("未通过 %d 项" % len(fails))
    sys.exit(1)
print("全部通过")
sys.exit(0)
