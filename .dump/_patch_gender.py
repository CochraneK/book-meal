# -*- coding: utf-8 -*-
"""gender 篇：把 write_generic.py / write_docs.py 生成的模板里不实的句子就地订正。

⚠️ 只改 papers_pilot/gender/ 下的产物，不碰 _lib/ 与 _dump/。
每次重跑 `_prep.py gender --generic` 或 `write_docs.py gender` 后都要再跑一遍本脚本。

用法： python .dump/_patch_gender.py
"""
import io
import os

ROOT = r"D:\2026\WB项目\明朝"
SEC = os.path.join(ROOT, "papers_pilot", "gender", "paper", "sections")
AUDIT = os.path.join(ROOT, "papers_pilot", "gender", "AUDIT.md")

REPL = [
    (os.path.join(SEC, "1_introduction.tex"),
     "（全书 156 章，本篇锚点覆盖 41 章）",
     "（全书 156 章）"),
    (os.path.join(SEC, "1_introduction.tex"),
     "网络一侧，由主题词命中人物构成的 127 人子图含显式边 631 条，"
     "这一子图的边界由四位锚点的 ego 网络决定，其中唯一的一位女性锚点在关系表里没有一条边；",
     "网络一侧，本篇走的是口径 B（锚点自我网络），127 人的子图含显式边 631 条，"
     "其边界由四位锚点的 ego 网络决定，其中唯一的一位女性锚点在关系表里没有一条边；"),
    (os.path.join(SEC, "3_corpus.tex"),
     "本篇锚点覆盖章节 & 41 \\\\",
     "单个人物最高出场章节 & 41 \\\\"),
    (os.path.join(SEC, "3_corpus.tex"),
     "词表由 13 个中文词构成",
     "配置共 14 个中文词，逐字命中原书者 13 个，下表按命中次数降序列出这 13 个词，"
     "配置中的「贞节」在原书零命中故不列"),
    (os.path.join(SEC, "3_corpus.tex"),
     "（按出场章数降序，取前 8）",
     "（按出场章数降序；本篇锚点集共 4 人）"),
    (os.path.join(SEC, "5_results.tex"),
     "亲属 & 7.3~(46) & 8~(185) \\\\\n同盟友党 & 5.7~(36) & 7~(162)",
     "亲属 & 7.3~(46) & 8.0~(185) \\\\\n同盟友党 & 5.7~(36) & 7.0~(162)"),
    (os.path.join(SEC, "5_results.tex"),
     "四个人里唯一的一位女性，在图上是最短的一根、也是唯一没有连线的那个点。"
     "这 631 条 ego 边一条都不是她带来的——她的缺席不是这一篇的修辞，是抽取表里的一个零。",
     "四个人里唯一的一位女性，在图上是最短的一根、也是唯一没有连线的那个点。"
     "这 631 条 ego 边一条都不是她带来的——她的缺席不是这一篇的修辞，是抽取表里的一个零。\n\n"
     "把这条缺席口径放到全图上，数字更硬：1231 位人物里有 537 位一条边都没有，约占四成三；"
     "本篇把这一项单独计数，是因为「写了几百次的词」与「一条边都没连上的人」是同一部书的两个侧面，"
     "只报有边的人物会把后者整片抹掉。张太后正是这 537 人里的一个已知样本。"),
]

AUDIT_TAIL = """
## 7. 本篇额外限制 L6 / L7（正文第 6 节已落地）

- **L6 唯一一位女性锚点在关系表里是孤立点**：张太后出场 1 章、度数 0，631 条 ego 边全部来自另外三位皇帝。这是抽取口径事实，不是「明代女性不参与叙事」的证据；本篇不作任何关于明代女性地位的历史推断。
- **L7 贞节 0 次这条制度缺席证据最脆**：它是单个配置词的零命中，换词表未必还是 0。方向（制度向名目压在个位数与一两位数，与女 467 差两个数量级）不会翻转，故只作定位证据，与「婚姻姻亲全图仅 4 条」这条边数证据并列使用。

## 8. 本篇对生成文本的手工订正（重跑 `_prep.py` 会被模板覆盖，已回报 team-lead）

| 文件 | 原生成句 | 问题 | 本篇订正 |
|---|---|---|---|
| `sections/1_introduction.tex` | 「由主题词命中人物构成的 127 人子图含显式边 631 条」 | `write_generic.py:224-228` 的 `nlead` 把 $|S|$ 一律写成「主题词命中人物构成」，本篇走口径 B（锚点 ego），该句不实 | 改为「本篇走的是口径 B（锚点自我网络）……边界由四位锚点的 ego 网络决定」 |
| `sections/1_introduction.tex` | 「全书 156 章，本篇锚点覆盖 41 章」 | `corpus.chapters` 实际是 `max(单个人物出场章数)`（朱元璋 41 章），不是锚点覆盖章数 | 删去该项，改在表 `tab:corpus` 中写为「单个人物最高出场章节 41」 |
| `sections/3_corpus.tex` | 「词表由 13 个中文词构成」 | 配置 14 词，贞节零命中不进表；与正文「配置十四词、命中十三词」自相矛盾 | 改为「配置共 14 个中文词，逐字命中原书者 13 个……配置中的贞节原书零命中故不列」 |
| `sections/3_corpus.tex` | 锚点表题「（按出场章数降序，取前 8）」 | 本篇锚点集只有 4 人，「取前 8」是模板写死的 | 改为「本篇锚点集共 4 人」 |
| `sections/5_results.tex` | 表 `tab:cats` 中 `8~(185)`、`7~(162)` | `write_generic.py:fmt(nd=1)` 把 8.0 / 7.0 的尾零截掉，与正文「8.0」「7.0」写法不一致 | 手工补回一位小数 |

## 9. 引用核验口径的如实说明

试点件经济篇的 6 条重合引用（freeman1978 / wasserman1994 / lemercier2015 / michel2011 / brook1998 / dangnian2009）沿用已核验条目。本篇新增 5 条性别向文献（west1987 / lerner1987 / ebrey2017 / sommer2015 / ko2018）为学界通行条目，**本次未在本机重新跑 `run_noproxy.py` + `verify_refs.py`**，仅按既有知识写入 `references.bib`；若 team-lead 要求与试点件同一核验强度，这 5 条需补跑一次并回填 DOI 后再定稿。
"""


def main():
    miss = []
    for path, old, new in REPL:
        t = open(path, encoding="utf-8").read()
        if old in t:
            open(path, "w", encoding="utf-8").write(t.replace(old, new, 1))
        else:
            miss.append(os.path.basename(path) + " :: " + old[:34])
    print("订正 %d/%d 处" % (len(REPL) - len(miss), len(REPL)))
    for m in miss:
        print("  !! 未命中：", m)

    a = open(AUDIT, encoding="utf-8").read()
    if "## 7." not in a:
        open(AUDIT, "a", encoding="utf-8").write(AUDIT_TAIL)
        print("AUDIT 追加第 7-9 节")
    else:
        print("AUDIT 已有第 7-9 节")
    return 1 if miss else 0


if __name__ == "__main__":
    raise SystemExit(main())
