# -*- coding: utf-8 -*-
"""anthropology 篇：就地修正 write_generic.py 模板写死的三处与本篇底稿不符的地方。

做法是先跑 `python _dump/_prep.py anthropology --generic`，再跑本脚本。
改的只有 papers_pilot/anthropology/paper/sections/*.tex（本篇自己的产物），
公共管线一行未动。三处都是模板 bug，已回报 team-lead：

  T1  sec4 模板把结论句写死成「故采用口径 A」，而本篇底稿 subset.method 是
      "B: ego(4 anchors)"（口径 A 命中不足 5 人，自动回落到锚点自我网络）。
      模板用 sub["n_persons"]=130 补了个 |S_A| 数字，等于用 B 的数去说 A。
  T2  sec5 的 5.3 标题与「本篇锚点的度数与出场章数如图 \ref{fig:anchors}」是
      写死的，但本篇 Fig.3 走的是主题事件年份分布（events.n=3：1404/1581/1601），
      且 figure 环境的 label 是裸 events/cats/vocab，没有 fig: 前缀。
  T3  sec1 把「全七部（156 章）」写死，而 tab:corpus 的「原书章节」取的是
      底稿 corpus.chapters=41；同一节还有 1231/1106/2324/563 也是写死的，
      本篇不去动它们（与底稿一致），只把章数对齐到底稿。

另外把模板 fmt(rho, nd=1) 截出来的 $\rho=0.9$ 还原成 $\rho=0.871$（同一个数，
只是精度被截掉了），避免出现「0.9」与「0.871」两个写法。
"""
import os

ROOT = r"D:\2026\WB项目\明朝"
SEC = os.path.join(ROOT, "papers_pilot", "anthropology", "paper", "sections")

PATCHES = {
    "1_introduction.tex": [
        ("全七部（156 章）", "全七部（41 章）"),
        ("由主题词命中人物构成的 130 人子图",
         "以四个核心锚点拉起的 130 人子图"),
        ("$\\rho=0.9$", "$\\rho=0.871$"),
    ],
    "4_method.tex": [
        ("本文该篇 $|S_A|$=130，故采用口径 A。",
         "本文该篇采用口径 B（四个锚点的自我网络），$|S_B|=130$ 人、显式边 636 条。"),
    ],
    "5_results.tex": [
        ("$\\rho=0.9$", "$\\rho=0.871$"),
        ("\\subsection{5.3 锚点：出场顺序与连线顺序不同步}",
         "\\subsection{5.3 锚点与继承争议：两张年表并置}"),
        ("本篇锚点的度数与出场章数如图 \\ref{fig:anchors}。",
         "锚点的度数与出场章数见表 \\ref{tab:anchors}，图 \\ref{fig:events} "
         "给的是仅有的三件带年份的主题事件。"),
        ("图 \\ref{fig:events} 给的是仅有的三件带年份的主题事件。图 \\ref{fig:events} 只有三根等等高的柱子",
         "图 \\ref{fig:events} 给的是仅有的三件带年份的主题事件，它只有三根等等高的柱子"),
        ("\\label{cats}", "\\label{fig:cats}"),
        ("\\label{vocab}", "\\label{fig:vocab}"),
        # 自适应：general-purpose-13 报的 label/ref 前缀坑。
        # 本篇采用的是「label 加 fig: 前缀、正文 ref 不动」这套；
        # 若日后主管线把模板改成「label 裸 cats/vocab、正文写 \ref{cats}」，
        # 上面两条 \label{...} 替换会 skip，这里再把正文里剩下的 \ref{fig:events}
        # 降成 \ref{events}，保证 ref 与 label 两端始终对得上（对不上就渲染成「图 ??」）。
        # sec5 模板漏了 Fig.3 的 figure 环境（只有 @@FIG1@@ / @@FIG2@@ 两个占位），
        # 图 3 已经生成却没人引用；这里补回一个 figure 环境，label 取 fig:events。
        # 守卫：若主管线已补上这个环境，就不再插第二个（否则同一张图进两遍）。
        ("\\subsection{5.3 锚点与继承争议：两张年表并置}",
         "\\subsection{5.3 锚点与继承争议：两张年表并置}\n\n"
         "\\begin{figure}[!t]\n"
         "\\centering\n"
         "\\includegraphics[width=\\columnwidth]{fig_anthropology_3.pdf}\n"
         r"""\caption{图 3 仅有的三件带年份的主题事件：1404、1581、1601 各 1 件。}""" + "\n"
         "\\label{fig:events}\n"
         "\\end{figure}"),
    ],
}


def main():
    # 0) 自适应归一（只能在替换之前判，因为没替换之前 label 长什么样一眼可见）
    p = os.path.join(SEC, "5_results.tex")
    t = open(p, encoding="utf-8").read()
    if "\\label{events}" in t and "\\ref{fig:events}" in t:
        t = t.replace("\\ref{fig:events}", "\\ref{events}")
        open(p, "w", encoding="utf-8").write(t + "")
        print("  ok  5_results.tex  label 走裸 events，正文 ref 归一为 \\ref{events}")

    for fn, subs in PATCHES.items():
        p = os.path.join(SEC, fn)
        t = open(p, encoding="utf-8").read()
        for old, new in subs:
            if "fig_anthropology_3.pdf" in new and "fig_anthropology_3.pdf" in t:
                print("  skip %-34s （Fig.3 的 figure 环境已在文中，不重复插入）" % fn)
                continue
            if old not in t:
                print("  skip (not found): %-34s <- %s" % (fn, old[:38]))
                continue
            n = t.count(old)
            t = t.replace(old, new)
            print("  ok  %-34s %s -> %s (x%d)" % (fn, old[:24], new[:20], n))
        open(p, "w", encoding="utf-8").write(t)


if __name__ == "__main__":
    main()
