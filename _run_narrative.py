# -*- coding: utf-8 -*-
import subprocess, sys, os, json, time
PY = r"C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe"
ROOT = r"D:/2026/WB项目/明朝"

def run(args, cwd=ROOT):
    r = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print("=" * 70)
    print("$ " + " ".join(args))
    if r.stdout:
        print(r.stdout)
    if r.stderr:
        print("[stderr]")
        print(r.stderr[-8000:])
    print("[exit=%d]" % r.returncode)
    return r

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "prep"
    if what == "prep":
        run(["_dump/_prep.py", "narrative", "--allfigs", "--generic"])
    elif what == "stats":
        run(["papers_pilot/_lib/show_stats.py", "narrative"])
    elif what == "genstats":
        run(["papers_pilot/_lib/gen_stats.py", "narrative"])
    elif what == "build":
        run(["papers_pilot/_lib/build_one.py", "narrative"])
    elif what == "docs":
        run(["papers_pilot/_lib/write_docs.py", "narrative"])
    elif what == "check":
        run(["papers_pilot/_lib/check_one.py", "narrative", "--strict"])
    elif what == "all":
        run(["_dump/_prep.py", "narrative", "--allfigs", "--generic"])
        run(["papers_pilot/_lib/show_stats.py", "narrative"])
    elif what == "fig":
        run(["papers_pilot/_lib/gen_figs.py", "narrative"])
    elif what == "lsdump":
        d = os.path.join(ROOT, ".dump")
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            print("%-40s %12d  %s" % (f, os.path.getsize(p), time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(p)))))
    elif what == "lsdir":
        d = os.path.join(ROOT, "papers_pilot", "narrative")
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            print("%-40s %s" % (f, "DIR" if os.path.isdir(p) else os.path.getsize(p)))
    elif what == "json":
        p = os.path.join(ROOT, ".dump", "_stats_narrative.json")
        print("exists=%s size=%s" % (os.path.exists(p),
              os.path.getsize(p) if os.path.exists(p) else "-"))
        if os.path.exists(p):
            s = json.load(open(p, encoding="utf-8"))
            print(json.dumps(s, ensure_ascii=False, indent=1)[:20000])
    elif what == "lsfig":
        d = os.path.join(ROOT, "papers_pilot", "narrative", "paper", "figures")
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            print("%-40s %10d  %s" % (f, os.path.getsize(p),
                                      "DIR" if os.path.isdir(p) else ""))
