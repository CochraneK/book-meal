# Run 02 · 暖水屯私有源结构联调（仅聚合统计）

状态：2026-11-13。**本文件仅保存聚合质量指标，不包含 Private sanggan 的人物姓名、引文、章节文本、密钥或任一私人研究档案。** 源文件通过已授权的 GitHub 连接在内存中读取并进行独立结构比对；**未在本轮运行完整 Python adapter + 真实私有源的同进程端到端校验**，不能声称其已通过。

## 源数据实测

| 指标 | 实际记录 | 文件头部宣称 | 处理策略 |
|---|---:|---:|---|
| 人物索引 | 78 | 78（manifest） | 无重复 ID |
| 人物 kernel 索引 | 78 | 79 | 作为 header 漂移提示；不能删除人名来凑数 |
| 地点 | 41 | 41 | 保持原样 |
| 事件 | 124 | 124 | 无重复 ID |
| 关系 | 123 | 124（relation_graph header）；123（manifest） | 作为 header 漂移提示，不更改原记录 |

- 事件参与者引用：4 次引用指向 3 个缺失的源实体 ID。
- 关系端点：3 次引用指向 2 个缺失的源实体 ID。
- 两组缺失 ID 无重叠：共 **5 个待核验来源 ID**（不是 5 个已确证人物）。
- 78 人物的 Kernel 索引文件指针全有，实际 Kernel 条目与 Person ID 集合一致；仅头部 79 不一致。
- 53 / 78 条人物的 evidence 是章节/叙事注释而非枚举；106 / 124 条事件也是此类来源注释。此前 v0.1 会将它们标记 UNKNOWN，现保留为 **BOOK（source_record_only，未直接回原著核验）**，且不复制注释内容。
- 123 关系中 110 条为 observed、13 条为 inferred；96 条没有结构化章节列表，不能将“无章节列表”解释为关系不存在。
- 事件章节号全部位于 manifest 58 章范围内，已记录的首次出场章节也未发现超界。

## 本轮 adapter 加固

1. 修正 `unresolved_entity` 的证据唯一性：同一个缺失 ID 出现在事件和关系源中时，保留两个不同证据锚点；重复引用不会产生重复 Evidence。
2. 事件缺失参与者指针应指向 `world/event_graph/events.json` 而非误指关系文件。
3. 将 `evidence` 的枚举与章节注释两种历史形态兼容起来；使用 source_record_only 显式说明尚未从原文独立确认。
4. 对 Kernel header/实际条目/人物索引、关系 header、事件 header、manifest 总数分别审计；**不修改私人真源**。
5. 新增完全合成的回归测试，不含真实私有姓名、文本、关系内容。

## 验收边界

本轮真实私有输入只经过**独立只读结构审计**；由于公共 GitHub Actions 无权拉取 Private sanggan，CI 仅运行公开明朝真实数据与合成 Sanggan 数据。实际私有 Python 适配器全链路仍需在有该私有 checkout 的授权运行环境执行：

`python src/export_world.py --book sanggan --source-root /path/to/private/sanggan --check-only`

它不写文件、不上传私人数据；输出的汇总可用于与此表核对。发现差异须保留 audit，不自动修复源数据。
