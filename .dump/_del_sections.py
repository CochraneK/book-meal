import os, glob
D = r"d:\2026\WB项目\明朝\papers_pilot\systems\paper\sections"
os.makedirs(D, exist_ok=True)
for f in glob.glob(os.path.join(D, "*.tex")):
    os.remove(f)
    print("removed", os.path.basename(f))
# 旧版 generic 作图脚本清掉，一图一脚本
F = r"d:\2026\WB项目\明朝\papers_pilot\systems\paper\figures"
for f in glob.glob(os.path.join(F, "make_fig*_systems.py")):
    os.remove(f)
    print("removed script", os.path.basename(f))
print("sections now:", os.listdir(D))
print("scripts now:", sorted(os.path.basename(x) for x in glob.glob(os.path.join(F, "*.py"))))
