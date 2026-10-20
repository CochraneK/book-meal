import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
PY = r"C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe"
D = r"d:\2026\WB项目\明朝\papers_pilot\anthropology\paper\figures"
# 先删掉与现存 PDF 不配套的旧脚本（一图一脚本）
for stale in ("make_fig1_kinship_direction.py", "make_fig2_generational_span.py",
              "make_fig3_two_way_bleed.py"):
    p = os.path.join(D, stale)
    if os.path.exists(p):
        os.remove(p)
        print("REMOVED stale script", stale)
for f in sorted(os.listdir(D)):
    if f.startswith("make_") and f.endswith(".py"):
        r = subprocess.run([PY, f], cwd=D, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print("----", f, "exit", r.returncode)
        print(r.stdout.strip())
        if r.stderr.strip():
            print("STDERR", r.stderr.strip()[-600:])
