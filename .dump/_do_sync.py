# -*- coding: utf-8 -*-
import os, hashlib, shutil

ROOT = r"D:\2026\WB项目\明朝"
REMOTE = os.path.join(ROOT, ".dump", "_remote_pull", "CochraneK-ming-d696a7e")
SKIP = {".git", "__pycache__", ".dump"}  # 不要把远端 .dump 写回本地 .dump（避免覆盖发布脚本）

def sha(p):
    h = hashlib.sha1()
    try:
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(1 << 20), b""):
                h.update(c)
        return h.hexdigest()
    except Exception:
        return None

def walk(b):
    out = []
    for dp, dn, fn in os.walk(b):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            out.append(os.path.relpath(os.path.join(dp, f), b))
    return out

rf = walk(REMOTE)
remote_only, divergent, same = [], [], 0
for rel in rf:
    rp = os.path.join(REMOTE, rel)
    lp = os.path.join(ROOT, rel)
    if not os.path.exists(lp):
        remote_only.append(rel)
    elif sha(rp) != sha(lp):
        divergent.append(rel)
    else:
        same += 1

# 仅补入远端独有文件（本地不存在才复制，绝不覆盖）
copied = 0
for rel in remote_only:
    rp = os.path.join(REMOTE, rel)
    lp = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    shutil.copy2(rp, lp)
    copied += 1

rep = []
rep.append("# 本地 \u2194 GitHub(ming) 同步报告\n")
rep.append(f"- 远端文件总数: **{len(rf)}**")
rep.append(f"- 与本地完全相同: **{same}**")
rep.append(f"- 远端独有、已安全补入本地: **{len(remote_only)}**")
rep.append(f"- 两端都存在但内容不同（保留本地、未覆盖）: **{len(divergent)}**\n")

rep.append("## 一、已补入本地的远端独有文件（纯新增，未触碰任何本地文件）\n")
for r in sorted(remote_only):
    rep.append(f"- `{r}`  ({os.path.getsize(os.path.join(REMOTE, r)):,} B)")

rep.append("\n## 二、冲突文件（两端不同，按\"保留本地开发版\"处理，未覆盖）\n")
for r in sorted(divergent):
    rep.append(f"- `{r}`  \u2192  remote={os.path.getsize(os.path.join(REMOTE, r)):,}B / local={os.path.getsize(os.path.join(ROOT, r)):,}B")

open(os.path.join(ROOT, ".dump", "_SYNC_REPORT.md"), "w", encoding="utf-8").write("\n".join(rep))

print("copied(added):", copied)
print("divergent(kept-local):", len(divergent))
for d in sorted(divergent):
    print("  DIVERGENT:", d)
# 本地补入后是否还存在远端独有?
left = [r for r in remote_only if not os.path.exists(os.path.join(ROOT, r))]
print("still-missing-after-copy:", len(left))
