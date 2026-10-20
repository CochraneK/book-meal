import os, subprocess, sys, glob
sys.stdout.reconfigure(encoding="utf-8")
PY = r"C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe"
D = r"d:\2026\WB项目\明朝\papers_pilot\systems\paper\figures"
for f in sorted(glob.glob(os.path.join(D, "make_fig*.py"))):
    r = subprocess.run([PY, os.path.basename(f)], cwd=D, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    print("----", os.path.basename(f), "exit", r.returncode)
    print(r.stdout.strip())
    if r.stderr.strip():
        print("STDERR", r.stderr.strip()[-700:])
print("FINAL PDFs:")
for f in sorted(glob.glob(os.path.join(D, "*.pdf"))):
    print("   ", os.path.basename(f), os.path.getsize(f))
