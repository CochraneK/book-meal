#!/usr/bin/env bash
set -u
unset HTTPS_PROXY HTTP_PROXY https_proxy http_proxy ALL_PROXY all_proxy
REPO=CochraneK/ming
BASE="D:/2026/WB项目/明朝"
OUT="$BASE/.dump"
LOG="$OUT/_deploy_log.txt"
: > "$LOG"
FILES=(
  "web/report.html"
  "web/report_p1.html"
  "data/data.json"
  "data/geo_annotations.json"
  "data/manual_relations.json"
  "src/generate_report.py"
  "src/enrich_geo.py"
  "src/enrich_relations.py"
)
for f in "${FILES[@]}"; do
  lp="$BASE/$f"
  b64="$OUT/$(echo "$f" | tr '/' '_').b64"
  base64 -w0 "$lp" > "$b64"
  sha=$(gh api "/repos/$REPO/contents/$f?ref=main" --jq '.sha' 2>/dev/null || true)
  msg="chore: 落地改进①②③④ — 地点全量8类标注、次要人物折叠、推导关系入库(relations=2331)"
  if [ -n "$sha" ]; then
    gh api --method PUT "/repos/$REPO/contents/$f" \
      -f "message=$msg" -f "content=@$b64" -f "branch=main" -f "sha=$sha" >> "$LOG" 2>&1 \
      && echo "OK   $f" >> "$LOG" || echo "FAIL $f" >> "$LOG"
  else
    gh api --method PUT "/repos/$REPO/contents/$f" \
      -f "message=$msg" -f "content=@$b64" -f "branch=main" >> "$LOG" 2>&1 \
      && echo "NEW  $f" >> "$LOG" || echo "FAIL $f" >> "$LOG"
  fi
done
cat "$LOG"
