# legacy/ — 停用脚本归档区

这里放的是**已被架构变更淘汰、但仍保留作参考**的脚本。它们不参与构建、不参与 CI，
运行它们大概率会失败，这是预期行为，不是 bug。

## 为什么停用

2026-10-01 的「单体 `data.js`」重构把在线交付从
`boot-data.js` + N 个详情 shard 的**分片架构**改回单体 payload。以下脚本全部
假定分片产物存在（`data-time.js` / `data-event-detail-*` / `data-lifespans.js` …），
在新架构下必然找不到文件：

| 脚本 | 原用途 | 停用原因 |
|---|---|---|
| `split_time_asset_v11.py` | 把年谱 `lifespans` 从 `data-time.js` 拆成独立块 | 分片产物已不存在 |
| `split_event_asset_v12.py` | 把 events 拆成摘要核心 + 8 个详情 shard | 同上 |
| `split_relation_asset_v13.py` | 把 relations 拆成可见 core + deferred metadata | 同上 |
| `check_time_layers_v11.py` | 校验 V11 时间层分片 | 依赖上者 |
| `check_event_layers_v12.py` | 校验 V12 事件层分片 | 依赖上者 |
| `check_relation_layers_v13.py` | 校验 V13 关系层分片 | 依赖上者 |
| `check_delivery.py` | 交付物体积与完整性检查（分片口径） | 口径已变 |
| `sync_readme_v11/v12/v13.py` | 把分片说明同步进 README | README 现由 `src/sync_readme.py` 模板渲染，不再按锚点打补丁 |

## 仍然有效的等价物

- 构建 / 门禁：`src/build.py`（`--check`）
- 数据审计：`src/audit_final.py`
- 体积预算：`src/check_budget.py`、`src/check_payload_budget.py`
- README 生成：`src/sync_readme.py`
- 门户生成：`src/build_hub.py`

## 什么时候可以删

按需加载（分片）若重新立项，可直接删掉本目录，从新架构重写；
在此之前保留，是为了让分片时代的口径决策有据可查。
