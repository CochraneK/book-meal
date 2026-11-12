# Run 04 · Public Sanggan 数据接入

## 已有公开信息，非私人原始资料迁移

Book-Meal 公开报告 books/sanggan/index.html 的 DATA 中，已有 78 人、124 事件、123 关系。运行时不读取 Private sanggan、SecondMe 私人档案或原始 OCR；只解析现有公开 HTML 内的 JSON 字面量，并投影少量公开字段用于组件。

链路：公开报告 → world_adapters/sanggan_public.py → validate_world → world_components.digest → 构建期 worlds/index.html。

公开投影保留人物 ID、姓名、公开角色描述、首次章节、事件 ID 与公开摘要、关系类型和 observed/inferred 来源；不复制完整人物内核、深描报告、人物心理 trace、原始引文和 OCR 文本。现有示意场景仅包含 15 个地点，不等于私有完整的 41 地点索引或真实地理坐标。

Evidence 使用 source_record_only，BOOK 代表公开报告声称来自书中，不是独立原文复核。无法解析的关系端点保留为 unresolved，不凭空创造人物。

明朝和暖水屯现在均由同一个 world_components.digest 生成真实数据驱动的可折叠人物、事件、关系索引；暖水屯的字符和事件可直达已验证的 #view 路由，并保留原报告的小游戏。

## CI / 验收

运行 python tests/run_tests.py、python src/build_dist.py --out .ci/site、python src/build_dist.py --check --out .ci/site、python tests/browser_check_world.py .ci/site/worlds/index.html。

CI 验证真实公开报告计数、统一契约、稳定 ID、来源、未解析引用、无私有 kernel 内容、无脚本执行，以及新旧构建、网页和手机截图。

需注意：这不是 Private sanggan 原始数据经过 Python adapter 的完整端到端验收，也不是学术效度验证。真实手机触摸交互仍需另行检查。
