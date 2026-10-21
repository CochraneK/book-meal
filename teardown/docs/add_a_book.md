# 新增一本书 · Runbook

> 目标：把一本书变成「门户里一张可点开的卡片」。内容 / 平台分离——每本书只产出一份自包含报告 + 一份 `manifest.json`，平台只做索引。

## 0. 一本书 = 报告 + manifest

```
data/<id>/manifest.json     # 名片：书名/作者/类型/指标/体积/状态/报告路径（门户唯一数据源）
out/<id>.html               # 自包含单文件报告（不引 CDN）
```

`manifest.json` 由 `src/build_manifest.py` 从 `config.json` + `data/<id>/data.json` **派生**，不手抄（避免两处漂移）。

## 1. 判定书型（决定走哪条路）

| 书型 | status | 走什么 | 例子 |
|---|---|---|---|
| 五元组 KG（人物/地点/事件/关系/其他） | `ready` | 五元组流水线 `generate_report.py` | 天才基本法 / 废土扫垃圾 |
| 世界级/专题精读（自带 schema 与生成器） | `standalone` | 专用生成器（如 `build_swdw_report.py`） | 小说维度晋升 |
| 外部独立站 | `external` | 只登记、外链 | 明朝那些事儿 |

## 2. 五种书型的最小动作

### A. 五元组书（ready）
1. 放原文 `book.txt`；**版权：TXT / chapters.json 绝不入库**（`.gitignore` 已排除）。
2. `config.json > books` 加条目：`title/author/kind/file/heading/accent` + `data_json`/`report`。
   `heading`：`numbered`（`1. 标题`）/ `plain`（裸标题+全角缩进）/ 本书若为「第N章」需在 `split_chapters.py` 加模式。
3. 跑管线：`split_chapters → (LLM 逐章抽取 append_extract) → merge → type_reduce → generate_report`。
4. `build_manifest.py` → `generate_report.py`（构建报告 + 门户）。

### B. 独立报告书（standalone）
1. 自备 `data/<id>/data.json`（自有 schema）+ 一个 `src/build_<id>_report.py` 生成 `out/<id>.html`。
2. `config.json` 条目加 `"standalone": true`、`data_json`、`report`（**不加 `missing`**）。
3. `generate_report.py` 会自动**跳过**它的五元组 build，门户照常计数 + 可点。
4. `build_manifest.py` → 重建门户。

### C. 外部书（external）
1. `config.json` 条目加 `"external": true`、`report: "../某站/standalone.html"`（部署时换成可访问 URL）。
2. `build_manifest.py` → 门户收录（若 `data_json` 指向外部 `data.json`，指标现算）。

### D. 只有 manifest、连 config 都不想加
门户 `_portal_books()` 会扫描 `data/*/manifest.json`：**只要放一份 manifest + 报告文件**，即使 config 里没有，也能出现在门户（适用于纯外链/成品报告）。五元组书仍需 config（build 用 `file/heading`）。

## 3. manifest schema

```json
{
  "schema": 1,
  "id": "tiancai",
  "title": "天才基本法",
  "author": "长洱",
  "kind": "modern_real",
  "desc": "……",
  "accent": "#8c4a2f",
  "report": "tiancai.html",
  "status": "ready",              // ready | standalone | external | missing
  "metrics": { "characters": 140, "events": 1399, "relations": 482 },
  "chapters": 221,
  "chars": 695000,
  "updated": "2026-10-20"
}
```

## 4. 门禁（每本书收尾必跑）

```bash
python src/build_manifest.py            # 派生 manifest
python src/generate_report.py           # 构建报告 + 门户（external/missing/standalone 自动跳过 build）
python src/check_report.py              # 12 视图无头冒烟（只覆盖 tiancai/feitu）
python -m pytest tests -q               # 单测
python src/sync_readme.py --check       # README 规模表一致
grep -c '{esc(' out/<id>.html           # 单文件报告占位符必须为 0
```

## 5. 纪律红线

- **不编造**：只用工件数据，不凭记忆补情节。
- **引语须原文命中**：金句/语录必须先在该书原文出现，0 命中即弃用。
- **文献须核验**：论文参考文献逐条 Crossref 核验后才写入。
- **原文不入库**：TXT / chapters.json 不提交、不发布。
- **单文件离线**：报告不引 CDN，生成后 grep 占位符为 0。

## 6. 规模上限（长期扩展）

- GitHub Pages 单站约 1GB（软）、带宽另计。小书塞同一站，**大书（>数十 MB）独立 Pages + 门户外链**。
- 报告天然自包含 → 每本书可独立成仓、CI 发布产物，平台只做链接（未来演进方向）。
