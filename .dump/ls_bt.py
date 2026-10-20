import os, datetime
out = []
for r, d, f in os.walk(os.path.join(r"D:\2026\WB项目\明朝", ".dump", "bibtest")):
    for n in f:
        fp = os.path.join(r, n)
        out.append(datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%H:%M:%S")
                   + " %8d %s" % (os.path.getsize(fp), fp.replace("\\", "/")))
open(r"D:\2026\WB项目\明朝\.dump\_lsbt.txt", "w", encoding="utf-8").write("\n".join(out))
