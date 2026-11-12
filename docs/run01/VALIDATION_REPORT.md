# Book-Meal Run 01 / 验收报告

- 日期：2026-11-13（本地）
- 主仓：CochraneK/book-meal
- PR：https://github.com/CochraneK/book-meal/pull/22
- 分支：feat/run01-world-contract
- 测试工作流：https://github.com/CochraneK/book-meal/actions/runs/43265631171
- 结果：该次 CI completed / success；所有工作流步骤 success（包括单测、语法、发布目录、版权、数据审计、书库导航、明书构建、无头浏览器检查）。

## 本次已完成（有实际提交）

1. 只读 World Contract v0.1 及 Python referential validator，既不重新定义人类本体，也不调用云端 LLM。
2. Ming 公共的 data/data.json → canonical projection，来源、章节、时序、非人物节点与保留的专有字段。
3. Sanggan 私有本地 source → canonical projection，独立适配器只包含读取和映射代码；Kernel 使用本地文件指针，不包含私人人物详情。
4. 合成 Sanggan fixture（包含悬空 actor/relation、observed/inferred 区分）与真实 Ming 文件回归测试，CI 确认全部通过。
5. 现有能力矩阵、重复/缺口审计、ADR、交接与迁移计划。

## 非破坏性审计

- 变更属于新增文件；未修改既有的 HTML / JavaScript / 书库 manifest / data.json / build.py / GitHub Actions YAML。
- 本轮主分支未被修改，仍由既有 Pages 发布逻辑负责。
- Public PR 中没有上传真实的 Sanggan person/kernel/events/relations JSON、SecondMe 私人画像或任何原著正文。
- 检查工具 --check-only 不写文件；若显式输出 Sanggan 结果到 Book-Meal 公共 checkout，工具拒绝。

## 验收精度与限制

- **已验证（自动化）**：Ming 真实公开源转换与 graph/ID/evidence/time 校验；Sanggan 合成数据的 schema 转换；所有旧站 CI 步骤含 headless 浏览器自检、静态资源发布检查和链接导航检查。
- **尚未验证（需授权环境）**：完整私有 Sanggan 数据通过本 Python 适配器的端到端执行；源中已知未解人物端点和 kernel 数量不一致须等私有本机测试后复核。当前不会误称完成。
- **未验证（真实设备）**：手机浏览器人工点击、不同系统离线文件体验。旧网页在本 PR 中未更改，不能以此推断已完成跨设备人工测试。
- **GitHub Pages**：本轮是 Draft PR、主站尚未部署此 PR 代码；main 仍为原站。测试通过不等于新功能已上线。
- **科学有效性**：本次仅解决模型之间的结构与血缘互操作，不宣称心理、社会演化和历史政策预测有真实效度。
- **来源精度**：明朝部分原有关系仍只有 chapters 或 curated 标签；补人/机构/事件证据要回源审查，不能因为 schema 校验通过就当作历史事实得到证实。

## 完成定义

Run 01 的代码与 CI 已完成；完整真实 Sanggan 转换和移动端人工验收仍列为后续专门验证项。此 PR 保持 Draft，不合并；建议先查阅 docs/run01/ADR-001.md 与 docs/run01/MIGRATION_PLAN.md。

## 核心验收命令

python tests/run_tests.py
python src/export_world.py --book ming --check-only
python src/build.py --check
python src/build_hub.py --check
python src/sync_shelf.py --check

授权本机私有 Sanggan：
python src/export_world.py --book sanggan --source-root /private/path/sanggan --check-only
