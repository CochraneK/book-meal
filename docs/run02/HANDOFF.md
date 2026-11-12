# Run 02 · 接管与验证

- 依赖 Run 01 的 PR #22；本轮分支 `feat/run02-sanggan-audit`，目标是 Run 01 分支，不直接改 main。
- 现已通过私有 GitHub 连接对 78 人物、41 地点、124 事件、123 关系和 Kernel 索引进行了内存结构审计，结论在 `docs/run02/PRIVATE_SOURCE_STRUCTURAL_AUDIT.md`，Public 只保存聚合统计。
- `src/world_contract.py` 补齐 Evidence 的多来源引用与幂等处理；`src/world_adapters/sanggan.py` 修复 source 文件指针、章节注释证据分类和头部数值漂移检查。
- `tests/test_world_contract.py` 增加合成测试；用旧的 `tests/run_tests.py` 在 PR CI 内完成验收，保持旧版 HTML、书架和自动化构建不变。
- 如有授权的私有 Sanggan clone，只需运行 `python src/export_world.py --book sanggan --source-root <私有仓库目录> --check-only` 做真正的 Python 端到端验证；**不要复制 private 目录到公共 Book-Meal**。
- 不合并 PR #22 或本轮 PR，待用户审查；进入 Run 03 前先解决来源证据等级的歧义、待核验源 ID 和原始关系缺少章节锚点的问题。
