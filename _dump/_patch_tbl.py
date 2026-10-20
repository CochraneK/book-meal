# -*- coding: utf-8 -*-
"""把 write_generic.py 里用 % 做模板的表片段改成 @@BODY@@ 哨兵替换（LaTeX 串里 % 是转义地雷）。"""
import py_compile

p = r"D:\2026\WB项目\明朝\papers_pilot\_lib\write_generic.py"
t = open(p, encoding="utf-8").read()
n0 = t.count("@@BODY@@")

CATS_OLD = '''    return r"""
\\begin{table}[!t]
\\centering
\\caption{子图与全图的类别构成对比（括号内为边数；仅列子图或基线中占比 $\\geq1\\%$ 的类别）}
\\label{tab:cats}
\\small
\\begin{tabular}{lrr}
\\toprule
类别 & 子图 & 全图基线 \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}
""" % "\\n".join(body)'''
CATS_NEW = '''    return r"""
\\begin{table}[!t]
\\centering
\\caption{子图与全图的类别构成对比（括号内为边数；仅列子图或基线中占比 $\\geq1\\%$ 的类别）}
\\label{tab:cats}
\\small
\\begin{tabular}{lrr}
\\toprule
类别 & 子图 & 全图基线 \\\\
\\midrule
@@BODY@@
\\bottomrule
\\end{tabular}
\\end{table}
""".replace("@@BODY@@", "\\n".join(body))'''

CORP_OLD = '''    body = "\\n".join(" & ".join([a, str(b)]) + r" \\\\" for a, b in rows)
    return r"""
\\begin{table}[!t]
\\centering
\\caption{语料与结构化抽取产物规模}
\\label{tab:corpus}
\\small
\\begin{tabular}{lr}
\\toprule
项目 & 数量 \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}
""" % body'''
CORP_NEW = '''    body = "\\n".join(" & ".join([a, str(b)]) + r" \\\\" for a, b in rows)
    return r"""
\\begin{table}[!t]
\\centering
\\caption{语料与结构化抽取产物规模}
\\label{tab:corpus}
\\small
\\begin{tabular}{lr}
\\toprule
项目 & 数量 \\\\
\\midrule
@@BODY@@
\\bottomrule
\\end{tabular}
\\end{table}
""".replace("@@BODY@@", body)'''

for old, new in ((CATS_OLD, CATS_NEW), (CORP_OLD, CORP_NEW)):
    if old not in t:
        raise SystemExit("PATTERN NOT FOUND")
    t = t.replace(old, new)

open(p, "w", encoding="utf-8").write(t)
py_compile.compile(p, doraise=True)
print("patched @@BODY@@ %d -> %d, compiled" % (n0, t.count("@@BODY@@")))
