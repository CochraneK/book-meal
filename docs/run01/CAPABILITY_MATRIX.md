# Book-Meal Run 01 / 能力与真源审计

日期：2026-11-13。审计范围：Book-Meal main、七个参考仓库代码、README、主要契约与测试入口。此文件仅记录公共安全的结构和接口，不包含 SecondMe 个人记录、私人文学语料或私人 Agent 内容。

| 仓库 | 真实可复用能力 | 成熟度 / 现有依据 | 权威归属 | 处理 |
|---|---|---|---|---|
| book-meal | 多书 manifest、门户、明朝抽取聚合、人物/事件/关系、地图、静态和离线报告；src/book_registry.py 统一书架 | 主站已上线；tests/run_tests.py、build.py --check、build_hub.py --check、sync_shelf.py --check | 书单和明朝已有聚合数据 | 主仓；本轮只增加边车适配器 |
| sanggan（Private） | 人物内核、事件图、关系图、章节索引、角色扮演 | 2026-10-28 HANDOFF 的 W6 构建验收；private 实际 78 人 / 124 事件 / 123 关系 / 41 地点；未进行新的浏览器实际操作 | 私有原著衍生资料库 | 只读输入；不提交真实导出 |
| AI-persona（Private） | Human Ontology v2、PersonaKernel、life_sim、PersonaTrace；来源层级 | 消费者契约实际代码；PersonaTrace 文档声明仅为变化记录，不是自主行动引擎 | 人物语义与合成人物引擎 | 只用版本化接口；不复制源数据 |
| Secondme-Framework | 可修正的人物理解、来源与竞争解释 | 方法文档和提示词已实现；非已验证真实人预测器 | 人物理解方法 | 仅借鉴原则 |
| SecondMe（Private） | 个人纵向证据与个体特异的建模方法 | Private，严禁带出个人材料 | 私人人物真源 | 方法读、数据禁复制 |
| novel2game | changan 分支引擎、条件选项、结局审计；yidieqian 单文件 | 项目 README 与实际代码目录可核；未重跑其游戏浏览器测试 | 小说游戏引擎 | 未来 UX 层适配，暂不合并 |
| emperor-skill（Private） | 历史人物 Skill、事件和决策处境、Nuwa 审查 | 人物包量大，但质量分层 C0/C1/C2；未证实全部可模拟 | 历史人物语料/研究 | 独立保留，仅复用审计思想 |
| ARIS4C（Private） | 论文编号、交接、研究流程、证据审查 | 研究项目组合，不是可直接拼进页面的 SDK | 独立科研总库 | 保留论文治理界限 |

## 重复与断层

1. **人物记录重叠**：Book-Meal 的 characters、sanggan 的 person/kernel、AI-persona PersonaKernel、emperor-skill 的 Skill 表面上都是人物，但语义不同；绝不能全量合并为一张大人格表。使用 AI-Persona Human Ontology v2 作为人物语义依据，Book-Meal 只保存引用和外部来源。
2. **事件语义错位**：明朝事件按名称聚合，sanggan 事件具有 event:ID 和章节；明朝关系包含非人物端点；需要 typed node + provenance adapter。
3. **图谱重复**：明朝已有关系图、sanggan 有 relation_graph；本轮共享可读数据出口，**不**重写两套图表。
4. **游戏重复**：sanggan 人生分支和 novel2game 剧情条件引擎可以互通，但不等于自主多 Agent 社会演化；待后续分别验收。
5. **审计分散**：Book-Meal CI、sanggan 数据门禁、AI-Persona 人物校验、emperor-skill Nuwa、ARIS4C 科研质量均各自存在，短期先保持专业边界。
6. **自动拆书未闭环**：新增 manifest 与自动生成完整原著知识图谱是两回事；《平凡的世界》目前仅建档。

## 质量与可复用性缺口

- Book-Meal 先前只统一书架（manifest），未定义跨书 World Contract；本轮新增 v0.1。
- sanggan 私有索引人物 78 条，但 kernel 索引自报 count 为 79；不能默默融合。私有关系/事件存在少量无法在人物索引解析的引用，必须作为 unresolved 占位与审查报告，严禁虚构人物。
- 明朝 data/data.json 约 1.9 MB，源字符键不同于 sanggan 的稳定 entity id；适配不得原地修改。
- 当前没有验证私人小说原文的版权、授权、证据内容，也没有跑真实多 Agent、科学有效性或端到端浏览器交互。不能声明这些已完成。

## 功能状态纪律

已实现：书架、明朝可视化、sanggan 静态图谱/分支游戏、AI-Persona 生命历程原型。
实验性：PersonaTrace、复杂心理行为推演、历史/社会反事实玩法。
未实现：通用自主社会世界引擎、自动整本书到研究级证明、跨书通用模拟发布。

## 下一步

先让本 PR 中两个 Adapter 和 World Contract 的 CI 全绿，再选用合法样例增加第三类书的适配器。旧站、旧数据与版权隔离不动。
