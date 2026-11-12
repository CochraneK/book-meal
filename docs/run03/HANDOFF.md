# Run 03 · 统一书籍世界体验（交接与验证）

状态：独立体验预览，未替换任何旧报告。基于 Run 02 分支叠加，待 PR 审核。

## 已做

1. 通用书籍世界入口采用 book_registry.load()，书目、状态和数字只有一个源。
2. 同一页呈现六本书；移动端横向书单 + 书名搜索；读懂、探索、研究三个真正可点击的入口。
3. 明朝已有页面的 overview/visuals/insight/map/timeline/dynasty 可直接深链；其他书仍打开各自的完整报告，没有捏造新交互。
4. 平凡的世界仍是建档中，指标用未知显示，不生成假图谱或人物。
5. 生成器与 CSS/JS 源都不进入网站；src/build_dist.py 生成单文件自包含 HTML 到 .ci/site/worlds/index.html，继续接受版权与发布目录白名单审查。
6. 新增零依赖单元测试 + CI 无头浏览器真实切换测试（不同 query book）。

## 运行

python tests/run_tests.py world_experience
python src/build_dist.py --out .ci/site
python src/build_dist.py --check --out .ci/site
python tests/browser_check_world.py .ci/site/worlds/index.html

打开 .ci/site/worlds/index.html?book=ming 或 ?book=sanggan 即可查看预览。
这条预览路径只有在最终合并并经 GitHub Pages 部署后才会出现在公开站点；PR 本身不等于线上已上线。

## 保护措施与缺口

- 不直接修改 index.html、ming、books 内任何既有报告；不触碰 Private sanggan 原始源。
- 模块遵循一书一世界；原始数据依旧沿旧构建链，暂未把专有图谱强行压成通用组件。
- World Contract 有数据适配和校验，但 Sanggan 真正的 Private Python 端到端还未通过。
- 老书报告无可靠通用深链时明确显示“打开现有报告”，不能假称直达人物或进入模拟。
- 真正的通用人物卡/关系图/研究组件属于 Run 03B：应先通过真实公共 Ming 和授权 Sanggan 同 schema 的双样本验收，再对比原版视觉与互动后迁移。
- CI 自动无头浏览器不等于真实手机人工体验。
