# -*- coding: utf-8 -*-
# 增量部署：报告在仓库根目录（index.html 唯一入口），
# 并删除冗余的 report_p1.html 与旧的 web/ 目录。保留仓库其余文件（data/、src/ 等）。
import os, json, base64, subprocess, tempfile

OWNER = "CochraneK"
REPO  = "ming"
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

# 新增/更新的文件（本地路径, 仓库内路径）
FILES = [
    ("index.html", "index.html"),
    ("_publish/README.md", "README.md"),
    ("data/data.json", "data/data.json"),
    ("data/geo_annotations.json", "data/geo_annotations.json"),
    ("data/manual_relations.json", "data/manual_relations.json"),
    ("data/manual_event_years.json", "data/manual_event_years.json"),
    ("data/manual_corrections.json", "data/manual_corrections.json"),
    ("data/manual_lifespans.json", "data/manual_lifespans.json"),
    ("data/manual_persons.json", "data/manual_persons.json"),
    ("data/event_places.json", "data/event_places.json"),
    ("data/derived_chapter_persons.json", "data/derived_chapter_persons.json"),
    ("src/derive_coverage.py", "src/derive_coverage.py"),
    ("src/merge.py", "src/merge.py"),
    ("src/enrich_geo.py", "src/enrich_geo.py"),
    ("src/generate_report.py", "src/generate_report.py"),
    ("src/audit_final.py", "src/audit_final.py"),
]

# 需删除的旧路径（GitHub tree 中 sha=null 即视为删除）
# web/ 与 report_p1.html 均已在上一轮提交中删除，此处留空（再删会触发 BadObjectState 422）
DELETES = [
]

ref = gh("GET", f"{API}/git/refs/heads/main")
head_sha = ref["object"]["sha"]
base_tree = gh("GET", f"{API}/git/commits/{head_sha}")["tree"]["sha"]
print("HEAD:", head_sha)

entries = []
for local, repo_path in FILES:
    with open(local, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    sha = gh("POST", f"{API}/git/blobs", {"content": b64, "encoding": "base64"})["sha"]
    entries.append({"path": repo_path, "mode": "100644", "type": "blob", "sha": sha})
    print(f"  blob {repo_path}  ({os.path.getsize(local)//1024}KB)")

for repo_path in DELETES:
    entries.append({"path": repo_path, "mode": "100644", "type": "blob", "sha": None})
    print(f"  del  {repo_path}")

tree_sha = gh("POST", f"{API}/git/trees", {"base_tree": base_tree, "tree": entries})["sha"]
commit_sha = gh("POST", f"{API}/git/commits",
                {"message": "feat: 文本反查补全人物出场105条+出场口径透明标注（抽取充分性审计）",
                 "tree": tree_sha, "parents": [head_sha]})["sha"]
gh("PATCH", f"{API}/git/refs/heads/main", {"sha": commit_sha})
print("✓ committed; new HEAD", commit_sha)
print("URL=https://github.com/%s/%s" % (OWNER, REPO))
