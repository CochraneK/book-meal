# -*- coding: utf-8 -*-
# 用 gh api 把 _publish/ 推送到 GitHub（沙箱 git 无法直连，故走 gh）
# 空仓库需先用 Contents API 引导出 main 分支，再走 Git Database API 批量提交大文件
import os, json, base64, subprocess, tempfile

OWNER = "CochraneK"
REPO  = "mingchao-knowledge-graph"
PUB   = "D:/2026/WB项目/明朝/_publish"
API   = f"/repos/{OWNER}/{REPO}"

ENV = {k: v for k, v in os.environ.items()}
for k in list(ENV):
    if k.upper() in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        del ENV[k]

def gh(method, path, input_obj=None):
    cmd = ["gh", "api", "--method", method, path]
    tmp = None
    if input_obj is not None:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(input_obj, tmp, ensure_ascii=False)
        tmp.close()
        cmd += ["--input", tmp.name]
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    if tmp:
        try: os.unlink(tmp.name)
        except: pass
    if r.returncode != 0:
        raise RuntimeError(f"gh {method} {path} failed:\n{r.stderr}\n{r.stdout}")
    return json.loads(r.stdout) if r.stdout.strip() else {}

def gh_form(method, path, fields):
    cmd = ["gh", "api", "--method", method, path]
    for k, v in fields.items():
        cmd += ["-f", f"{k}={v}"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    if r.returncode != 0:
        raise RuntimeError(f"gh_form {method} {path} failed:\n{r.stderr}\n{r.stdout}")
    return json.loads(r.stdout) if r.stdout.strip() else {}

# 收集文件
files = []
for root, _, fs in os.walk(PUB):
    for f in fs:
        lp = os.path.join(root, f)
        rp = os.path.relpath(lp, PUB).replace("\\", "/")
        files.append((lp, rp))
files.sort(key=lambda x: x[1])
print(f"total files: {len(files)}")

# 1) 用 Contents API 引导 main 分支（提交最小的 README.md）
readme = next(x for x in files if x[1] == "README.md")
with open(readme[0], "rb") as fh:
    r64 = base64.b64encode(fh.read()).decode("ascii")
print("bootstrapping main via Contents API (README.md) ...")
gh_form("PUT", f"{API}/contents/README.md",
        {"message": "Bootstrap: add README", "content": r64, "branch": "main"})
print("✓ main branch bootstrapped")

# 2) 取当前 main HEAD / base tree
ref = gh("GET", f"{API}/git/refs/heads/main")
head_sha = ref["object"]["sha"]
base_tree = gh("GET", f"{API}/git/commits/{head_sha}")["tree"]["sha"]
print("HEAD:", head_sha, " base_tree:", base_tree)

# 3) 其余文件走 Git Database API（blob 可带大文件）
remaining = [x for x in files if x[1] != "README.md"]
blobs = []
for i, (lp, rp) in enumerate(remaining, 1):
    with open(lp, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    sha = gh("POST", f"{API}/git/blobs", {"content": b64, "encoding": "base64"})["sha"]
    blobs.append({"path": rp, "mode": "100644", "type": "blob", "sha": sha})
    print(f"  [{i}/{len(remaining)}] blob {rp}  ({os.path.getsize(lp)//1024}KB)")

tree_sha = gh("POST", f"{API}/git/trees", {"base_tree": base_tree, "tree": blobs})["sha"]
commit_sha = gh("POST", f"{API}/git/commits",
                {"message": "Add pipeline(src), derived data, and interactive report(web)",
                 "tree": tree_sha, "parents": [head_sha]})["sha"]
gh("PATCH", f"{API}/git/refs/heads/main", {"sha": commit_sha})
print("✓ committed", len(remaining), "files; commit", commit_sha)
print("REPO_URL=https://github.com/%s/%s" % (OWNER, REPO))
