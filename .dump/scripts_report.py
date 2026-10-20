import os, re
ROOT = r"D:\2026\WB项目\明朝"
out = []
d = os.path.join(ROOT, "papers_pilot", "info", "paper", "figures")
for n in sorted(os.listdir(d)):
    if not n.startswith("make_"):
        continue
    t = open(os.path.join(d, n), encoding="utf-8", errors="replace").read()
    outs = re.findall(r"savefig\w*\(\s*[\"']([^\"']+)[\"']", t)
    outs2 = re.findall(r"(fig_[a-z0-9_]+)\.(?:pdf|png)", t)
    outs = sorted(set(outs + outs2))
    has_title = bool(re.search(r"set_title\s*\(\s*[\"'][^\"']*[\u4e00-\u9fff]", t))
    out.append("%s\n   OUT=%s  CH_TITLE=%s  LINES=%d" % (n, outs, has_title, t.count("\n")))
open(os.path.join(ROOT, ".dump", "_scripts.txt"), "w", encoding="utf-8").write("\n".join(out))
