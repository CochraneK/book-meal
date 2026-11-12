# Run 01 · 交付 / 接管 / 运行

分支：feat/run01-world-contract；目标：main；审查后才允许合并。

## 最短路径

1. 阅读 docs/UNIFIED_PLATFORM_VISION.md → docs/run01/ADR-001.md → docs/run01/CAPABILITY_MATRIX.md。
2. 检查 schema/world-contract.v0.1.schema.json；运行 python tests/run_tests.py，或只运行 python tests/run_tests.py world_contract。
3. 对公开的明朝数据：python src/export_world.py --book ming --check-only。
4. 只在本机授权存在私有 sanggan checkout 时执行：python src/export_world.py --book sanggan --source-root /private/path/sanggan --check-only。
5. 如需持久化明朝转换数据，显式传 --output /tmp/ming-world.json。私有 sanggan 不允许输出到 Book-Meal checkout 内。
6. 对旧站执行 python src/build.py --check、python src/build_hub.py --check、python src/sync_shelf.py --check；后续以 PR CI 和 Pages 完整交付为准。

## 真实 source 目录

- Ming: book-meal/data/data.json + books/ming/manifest.json，源生成脚本 src/merge.py。
- Sanggan: PRIVATE 仓库 world/index/persons.json、world/index/places.json、world/event_graph/events.json、world/relation_graph/relations.json、world/kernel/index.json、world/index/manifest.json。
- Human Ontology v2: AI-persona/ontology/CONSUMER_CONTRACT.md，AI-persona/ontology/persona_kernel.schema.json。

## 扩展点与边界

- 修改语义必须回 AI-Persona 的权威 Human Ontology 审查。Book-Meal contract 不新增人类语义目录。
- 私有源默认不存在于 CI；fixtures 只能合成，严禁直接复制私人 Person 或原著证据。
- 缺少 source 端点是 unresolved 实体和 audit 项，而不是新建“虚构人物”。
- 先验收 v0.1 的真实明朝导出 + 合成 sanggan 测试；再考虑前端适配或自动拆书。
- 不直接修改主站 HTML、现有 manifest、build.py 或其他仓库。

## 已知限制

- Ming 聚合数据缺少逐关系的原著证据偏移，无法宣称每项都已按正文回源核验。
- Sanggan 存在 kernel index count 与原始人物索引不一致、个别悬空引用等历史差异，转换会保留待审核痕迹。
- 目前 schema 是结构约定；Python 内建 validator 执行跨字段/跨引用检查，不依赖在线下载 JSON Schema validator。
- Python validator 不验证源证据真实性、因果假设和真人心理预测。
- 真实浏览器/移动体验必须在可用浏览器环境中额外进行人工走查；CI 浏览器测试不能替代所有设备测试。
