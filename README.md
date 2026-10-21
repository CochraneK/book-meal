# Book-Meal · 拆书知识库

**把一本长篇小说，拆成一份能查、能点、能离线带走的知识库。**

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-在线书库-8a2f2f?logo=githubpages)](https://cochranek.github.io/book-meal/)
[![CI](https://github.com/CochraneK/book-meal/actions/workflows/ci.yml/badge.svg)](https://github.com/CochraneK/book-meal/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.13-3776ab?logo=python)](https://www.python.org/)
[![依赖](https://img.shields.io/badge/dependencies-none-brightgreen)]()
[![形态](https://img.shields.io/badge/报告-单文件离线-blueviolet)]()

**4 本书 · 1,018 章 · 1,805 人物 · 6,938 事件 · 4,426 关系**

[打开书库 →](https://cochranek.github.io/book-meal/)

---

## 这是什么

一个**多书拆解聚合平台**。每本书从原文抽取实体与关系，聚合成知识图谱，
最终产出一份**单文件 HTML 报告**：不引任何 CDN、不需要服务端，双击就能打开，
断网也能用。

根路径是书库门户，点卡片进各书报告。新增一本书 = 放一个目录 + 一份
`manifest.json`，平台代码和 CI 都不用改。

## 在线入口

| 入口 | 地址 | 说明 |
|---|---|---|
| 书库门户 | [`https://cochranek.github.io/book-meal/`](https://cochranek.github.io/book-meal/) | 全部书目卡片，按类型筛选 |
| 《明朝那些事儿》 | [`https://cochranek.github.io/book-meal/ming/`](https://cochranek.github.io/book-meal/ming/) | 拆得最深的一本，12 个视图 |
| 离线单文件 | [`https://cochranek.github.io/book-meal/standalone.html`](https://cochranek.github.io/book-meal/standalone.html) | 约 5 MB，右键另存即可带走 |

## 书单

<!-- 下表由 src/sync_readme.py 从 books/*/manifest.json 生成，勿手改 -->

| 书名 | 作者 | 类型 | 章 | 人物 | 事件 | 关系 | 报告 |
|---|---|---|--:|--:|--:|--:|---|
| **明朝那些事儿** | 当年明月 | 历史 | 156 | 1,231 | 1,106 | 2,324 | [打开](https://cochranek.github.io/book-meal/ming/index.html) |
| **天才基本法** | 长洱 | 现代现实 | 221 | 140 | 1,399 | 482 | [打开](https://cochranek.github.io/book-meal/books/tiancai/index.html) |
| **我在废土世界扫垃圾** | 有花在野 | 幻想世界 | 439 | 379 | 4,386 | 1,606 | [打开](https://cochranek.github.io/book-meal/books/feitu/index.html) |
| **小说维度晋升，我在天幕当评委** | 白水瓶子 | 幻想世界 | 202 | 55 | 47 | 14 | [打开](https://cochranek.github.io/book-meal/books/swdw/index.html) |

合计 **4 本 · 1,018 章 · 1,805 人物 · 6,938 事件 · 4,426 关系**。
门户只读各书的 `manifest.json`，不加载任何一本书的 payload，因此永远轻量。

## 为什么不一样

- **坐标落在真实世界**——书里的地名解析到真实经纬度，可直接做「圣地巡礼」；
  未定位的一律标「待核验」而不硬填坐标：对巡礼场景，错误坐标比缺失更有害。
- **关系网络有两个口径**——`人物图` 只画人物↔人物，`实体图` 把地点/机构/政权
  也画进来。两者规模不同、图例不同，页面按当前模式分别渲染，绝不混读。
- **地址栏即状态**——`person=` `event=` `place=` `era=` `from/to=` 全部写进 URL，
  复制地址就能分享到同一张卡；搜索支持别名（`崇祯` → 朱由检）。
- **失败必须可见**——地图瓦片、CDN、Service Worker 任一步失败，页面底部弹出
  统一提示条（说明故障 + 重试 + 可关闭），不再静默白屏。
- **离线优先**——CSS/JS/数据全内联进单文件；地图在瓦片全失败时自动退回 SVG 点位图，
  点位仍可点击查看书中介绍。
- **数据诚实披露**——未知年份的事件单独成组，未定位地点如实标注，覆盖率与
  缺口都写在页面上，不拿推断充数据。

## 《明朝那些事儿》：目前拆得最深的一本

七部 **156 章**全文抽取，产出 **1,231 人物 / 1,106 事件 /
2,324 关系 / 583 地点（已定位 553，94.9%）**，
其中 66 位人物的书内语录逐条经原文核实。12 个视图：

**全局叙事** `总览` `分布` `时间轴` `帝王` `年谱`　·　**实体索引** `人物` `地点` `事件` `关系`　·　**探索分析** `图谱` `地图` `洞察`

- **地图**：圣地巡礼底图 + 郑和下西洋航线子视图，离线降级为 SVG 点位图。
- **人物**：扑克牌尺寸卡片（63×88mm，可翻面），三套主题，可一键生成打印页。
- **洞察**：18 学科 + 1 综合收束的跨学科长文，文内引用 APA 7，参考文献经检索核实。
- **分布**：三层诊断（分部 → 章节 → 结果），同时给出总量与每万字密度。

## 快速开始

```powershell
python -m http.server 8765 --bind 127.0.0.1   # 起个静态服务
# 打开 http://127.0.0.1:8765/index.html      # 书库门户
```

报告是单文件静态 HTML，直接双击也能开（本地服务可避开个别浏览器对 `file://` 的限制）。

重新生成全部交付物：

```powershell
python src/merge.py            # 聚合（增量勘误层不会被覆盖）
python src/build.py            # 构建明书离线单文件 standalone.html
python src/build_hub.py        # 重建书库门户 index.html
python tests/run_tests.py      # 单元测试（纯标准库，无第三方依赖）
```

## 仓库结构

```
index.html            书库门户（src/build_hub.py 生成，勿手改）
standalone.html       明书完整离线单文件（src/build.py 生成）
sw.js                 Service Worker（同源 stale-while-revalidate）
books/                每本书一个目录
  <id>/manifest.json  书目名片：书名/作者/类型/指标/入口/更新时间
  <id>/index.html     该书报告（单文件）
ming/                 《明朝那些事儿》分层版报告（index.html + assets/，CI 生成）
src/                  平台与构建脚本
  build_hub.py        门户生成器（扫 books/*/manifest.json）
  build.py            统一构建入口（--target standalone|web、--check）
  merge.py            数据聚合 / generate_report.py 最终模型
  audit_final.py      深审（ERROR 即退出非 0）
  validators.py       结构不变量（12 组规则）
  core/               共享核心：年份解析/经纬度校验/势力结构化/图布局
web/                  前端真源：template/index.html + css/app.css + js/app.js
data/                 聚合数据源与增量勘误层（data.json 是单一数据源）
tests/                单元测试 + tests/browser_check.py（无头浏览器自检）
                      check_copyright.py 是版权巡检，两条 CI 共用
docs/                 文档：docs/add_a_book.md（新增一本书）、docs/history/
legacy/               已停用脚本归档（分片时代遗留，见 legacy/README.md）
teardown/             拆书工程：其余三本书的抽取与报告生成
  src/                流水线脚本（generate_report.py / build_swdw_report.py …）
    publish_books.py  把 out/<id>.html 同步到 books/<id>/index.html（并可 --check）
  web/                拆书报告前端真源（与上面的 web/ 是两套，别混）
  data/<id>/          各书抽取数据（原文 TXT 不入库，见下）
  out/                构建产物（不入版本控制）
```

> **为什么有个 `teardown/`：**
> 这个仓库最初只装《明朝那些事儿》报告，其余三本书是在另一个独立工程里拆的，
> 每次发新版都要手动跨目录拷贝——忘了拷就出现「门户卡片是新的、点进去是旧的」。
> 2026-10-21 把那个工程整体搬成子目录后，两边共用同一份版权规则、同一条 CI，
> `publish_books.py --check` 也让「忘了同步」变成 CI 会报错的事。
>
> 两套前端没有合并：视图集合完全不同（那边是年号/航海/关系图，这边是阶段轴/
> 引用/学科论文），强融的代价远大于收益。

## 一本书是怎么拆出来的

```
原文 → 分章 → 抽取（人物/地点/事件/关系/时间）→ 聚合 → 校验 → 报告
```

1. **分章**：按目录切分，保留章节长度用于密度诊断；
2. **抽取**：逐章产出五元组候选，`data/extract_raw.json` 存原始结果；
3. **聚合**：`src/merge.py` 合并为 `data/data.json`，叠加人工勘误层
   （`manual_corrections.json` / `manual_lifespans.json` / `geo_annotations.json` …）；
4. **校验**：三层门禁（下表）；
5. **报告**：`src/build.py` 把 `web/` 的模板/样式/脚本内联成单文件。

重跑聚合不会丢人工层——那几个 `manual_*.json` 与 `geo_annotations.json` 是可持续维护的增量。

## 质量门禁

| 层 | 命令 | 拦什么 |
|---|---|---|
| 构建门禁 | `python src/build.py --check` | 结构不变量 12 组规则 + 内存渲染自检；有 ERROR 直接退出码 2，不产半成品 |
| 深审 | `python src/audit_final.py` | 业务规则：geo 对账、同名异地、在位区间衔接、分部子图 |
| 单元测试 | `python tests/run_tests.py` | 共享核心、数据不变量、模板拆分等价性、占位符唯一性、错误 UI 锚点 |
| 浏览器自检 | `python tests/browser_check.py <产物>` | 本机 Chrome `--dump-dom` 跑 11 个场景（deep link、搜索高亮、地图、双模式图…）+ 启动守卫兜底 |

CI 每次 push/PR 还会先跑**版权合规巡检**（原书全文一旦入库即失败）与
**模块遮蔽巡检**（任何 `.py` 与标准库同名都会污染 `sys.path[0]`，仅存在就能让 Python 崩掉）。

## 数据纪律

三条铁律，写在代码里也写在流程里：

1. **只用工件数据**——不凭记忆补情节，不臆造坐标与年份，**宁可留空不可猜错**；
2. **引语必须原文命中**——人物语录先在原书全文里检索到原句才收录，0 命中即弃用；
3. **文献未核实不写入**——跨学科解读的每条参考文献都经检索核实。

**版权**：原书全文与含正文的中间产物**不入库、不发布**（`.gitignore` 已排除，
CI 有巡检）。仓库只发布脱敏后的章节索引与聚合结果。换机接续时这两个文件需手动拷贝。

## 新增一本书

放 `books/<id>/` + 一份 `manifest.json`，跑一次 `python src/build_hub.py` 即可，
平台代码与 CI 都不用改。完整手册见 [`docs/add_a_book.md`](docs/add_a_book.md)。

## 路线图

- [ ] 明书按需加载恢复（2026-10-01 单体 `data.js` 重构后暂停，现状首屏约 5 MB）
- [ ] 人物卡语录扩面（现 66 人 → 目标覆盖高频人物，须原文命中）
- [ ] 洞察长文与图谱实体互跳
- [ ] 未定位地点与未知年份事件的人工考据（按提及频次排序推进）

历史过程与踩坑记录在 `.workbuddy/`（工程笔记）与 `docs/history/`（重构方案、自查与验收清单）。

## 说明

本项目是个人知识工程：书籍版权归原作者与出版社所有，报告仅作结构化索引与
学习笔记用途，不分发原文，不用于任何商业场景。

<!-- README_GENERATED_BY src/sync_readme.py -->
