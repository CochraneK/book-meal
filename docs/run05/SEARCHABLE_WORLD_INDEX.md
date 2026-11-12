# Run 05 · 全量公开索引浏览器

面向 Book-Meal 统一世界入口的一次渐进增强，旧报告、数据接口和首页无替换。

## 新增能力

- Book-Meal 已公开的暖水屯 78 人物、124 事件、123 关系可以在一套折叠索引中完整浏览。默认不展开，不增加首屏导航噪音。
- 内部提供三种索引切换与实时搜索，选择后跳转到对应的现有完整报告深链（Sanggan 事件可携带原生事件 ID）。
- 明朝源数据体量巨大，初版每类只展示前 40 项，并标明截断与完整报告入口；避免在单文件页面里重复渲染 4,000 多项。
- 同一 world_browse.render 适用于所有 World Contract，现阶段仅使用真实公开 Ming 和 Sanggan。
- 组件只复制已经在公开源中存在的名称、摘要、关系类型和章位索引，不复制 Private 研究档案、逐字原著或未核验心理建模。

## 运行与验收

python tests/run_tests.py
python src/build_dist.py --out .ci/site
python src/build_dist.py --check --out .ci/site
python tests/browser_check_world.py .ci/site/worlds/index.html

站点（部署后）：
https://cochranek.github.io/book-meal/worlds/index.html?book=sanggan

仍然不是模拟引擎或现实社会因果预测。来源证据标记为 source_record_only，不得当成已独立核对的原著事实。
