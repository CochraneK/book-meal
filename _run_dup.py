# -*- coding: utf-8 -*-
"""临时封装：把 _lib/dup_blocks.py 的输出以 utf-8 落到文件，便于 Read。"""
import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "papers_pilot", "_lib"))

pid = sys.argv[1]
mink = sys.argv[2] if len(sys.argv) > 2 else "25"
show = sys.argv[3] if len(sys.argv) > 3 else "40"

buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    sys.argv = ["dup_blocks.py", pid, "--min", mink, "--show", show]
    import dup_blocks
    try:
        dup_blocks.main()
    except SystemExit:
        pass

out = os.path.join(ROOT, "_dupout_%s.txt" % pid)
io.open(out, "w", encoding="utf-8").write(buf.getvalue())
print("OK", out, len(buf.getvalue()))
