# -*- coding: utf-8 -*-
p = r"D:\2026\WB项目\明朝\papers_pilot\_lib\write_psychology.py"
s = open(p, encoding="utf-8").read()
bad = "\\" + "$$"
print("bad count", s.count(bad))
s = s.replace(bad, "$" + "\\" + "rho" + "$")
open(p, "w", encoding="utf-8").write(s)
import re
for m in re.finditer(".{0,25}" + "\\" + "rho" + ".{0,15}", s):
    print(repr(m.group(0)))
