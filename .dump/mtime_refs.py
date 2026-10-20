import os, datetime, glob
ROOT = r"D:\2026\WB项目\明朝"
out = []
for p in ["_refcheck_info.json", "_refcheck_info.md", "_refcheck_info_run.txt",
          "_refcheck_xref_info.json", "_pilot_refcheck.json", "_refcheck_read.txt"]:
    fp = os.path.join(ROOT, ".dump", p)
    if os.path.exists(fp):
        out.append(datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%m-%d %H:%M:%S")
                   + " %8d %s" % (os.path.getsize(fp), p))
    else:
        out.append("MISSING " + p)
open(os.path.join(ROOT, ".dump", "_mtrefs.txt"), "w", encoding="utf-8").write("\n".join(out))
