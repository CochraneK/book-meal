# Book-Meal · 拆书知识库

**把一本长篇小说，拆成一份能查、能点、能离线带走的知识库。**

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-在线书库-8a2f2f?logo=githubpages)](https://cochranek.github.io/book-meal/)
[![CI](https://github.com/CochraneK/book-meal/actions/workflows/ci.yml/badge.svg)](https://github.com/CochraneK/book-meal/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.13-3776ab?logo=python)](https://www.python.org/)
[![依赖](https://img.shields.io/badge/dependencies-none-brightgreen)]()
[![形态](https://img.shields.io/badge/报告-单文件离线-blueviolet)]()

**5 本书 · 1,076 章 · 1,883 人物 · 7,062 事件 · 4,549 关系**

[打开书库 →](https://cochranek.github.io/book-meal/)

---

## 这是什么

一个**多书拆解聚合平台**。每本书从原文抽取实体与关系，聚合成知识图谱，
最终产出一份**单文件 HTML 报告**：样式、脚本与数据全部内联，不需要服务端，
双击就能打开，断网也能用。**唯一的可选联网项是「真实地图底图」**——
Leaflet 与地图瓦片按需从 CDN 加载，拿不到时自动退回离线点位图，
点位、点击详情等所有其它功能都不受影响。

根路径是书库门户，点卡片进各书报告。新增一本书 = 放一个目录 + 一份
`manifest.json`，平台代码和 CI 都不用改。

## 仓库速览（不迷失版）

一个目录里混着四类东西，**先认层再动手**：真正受版本控制的只是源码与成品，
其余体积都是本机工作区，clone 拿不到。精确数字跑
`python src/repo_hygiene.py --report`，不写进文档以免数字悄悄失真。

| 层 | 主要路径 | 怎么对待 |
|---|---|---|
| 真源 | `data/`、`teardown/data/`、`src/`、`web/`、`tests/`、`.github/`、`books/*/manifest.json` | **改这里才有意义** |
| 成品 | `index.html`、`standalone.html`、`sw.js`、`ming/`、`books/*/index.html` | 生成物，别手改；Pages 只发这 5 类 |
| 本机私有输入 | 3 本原著 TXT、`chapters.json`（含正文）、`tiancai/feitu` 的 `quotes.json` | 不入库、本机唯一、**绝不删**；删了报告无法重建 |
| 本地临时产物 | `.ci/`、`_site/`、`dist/`、`.dump/`、`papers_pilot/`、各 `__pycache__/` | 不入库，可归档；用 `src/repo_hygiene.py` 体检 / 移动 / 回滚 |

**改哪里 → 跑什么**：改内容动 `data/*.json` 再 `merge.py` + `build.py`；
改外观动 `web/` 再跑 `sync_*.py` 镜像器；加书放 `books/<id>/manifest.json`
再跑 `build_hub.py` + `sync_shelf.py`。拿不准就跑
`python src/repo_hygiene.py --report` 看分层体积与可归档清单。

**两条红线**：`teardown/out/` 是本机 `publish_books.py --check` 的输入，移走会让
门禁变红；`papers_pilot/` 与 `.dump/git-sync/` 是**没有远程的独立 git 仓库**，
删除前必须先备份。归档一律是移动不是删除，`--restore` 可一键回滚。

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
| **太阳照在桑乾河上** | 丁玲 | 现代现实 | 58 | 78 | 124 | 123 | [打开](https://cochranek.github.io/book-meal/books/sanggan/index.html) |

合计 **5 本 · 1,076 章 · 1,883 人物 · 7,062 事件 · 4,549 关系**。
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
- **每本书有自己的皮肤**——三本现代/架空小说分别是方格纸、废土 CRT 扫描线、
  深空星幕；明书则是宣纸纤维 + 朱砂印章 + 年号刻度。主题真源
  `web/css/theme-<book>.css`，由 `sync_ming_theme.py` / `generate_report.py` 在构建期
  注入，standalone 与分层版自动同步，不靠手改产物。
- **书库不是五个孤岛**——每份报告顶部都有同一条书库导航：一键回门户、下拉切到
  另外四本；书单来自 `books/*/manifest.json` 的单一真源，新增一本自动纳入。
  离线双击下载的报告时，导航链接自动改指线上书库，正文仍完全离线。
- **数据诚实披露**——未知年份的事件单独成组，未定位地点如实标注，覆盖率与
  缺口都写在页面上，不拿推断充数据。

## 《明朝那些事儿》：目前拆得最深的一本

七部 **156 章**全文抽取，产出 **1,231 人物 / 1,106 事件 /
2,324 关系 / 583 地点（已定位 553，94.9%）**，
其中 73 位人物的书内语录逐条经原文核实。12 个视图：

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
python src/sync_ming_theme.py  # 母题主题 CSS → 模板（改了 theme-ming.css 才需要）
python src/build.py --scope full --target standalone --out standalone.html
python src/build.py --scope full --target web --out .ci/publish
python src/build_hub.py        # 重建书库门户 index.html
python src/build_geo_backlog.py   # 重建地点/年份考据队列
python src/build_quote_backlog.py  # 重建语录扩面考据队列
python src/sync_shelf.py       # 给 6 份报告注入/刷新书库导航条（幂等）
python src/sync_readme.py      # 重建 README
python tests/run_tests.py      # 单元测试（纯标准库，无第三方依赖）
python src/check_delivery.py   # 交付能力断言（按需加载/洞察互跳/导航条/门户）
```

`sync_shelf.py` 必须排在**所有会重写报告产物的命令之后**：导航条是发布层的
生成装饰，重建 `standalone.html` / `ming/` / `books/` 会把它覆盖掉。CI 在
`refresh-index.yml` 里也是按这个顺序跑，并有 `--check` 兜底。

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
  book_registry.py    统一书单单一真源：门户/README/各报告导航条都读它
  sync_shelf.py       把书库导航条幂等注入 6 份报告（--check 可入 CI）
  sync_ming_theme.py  明书母题主题 CSS 镜像（真源 → 模板，--check 可入 CI）
  check_delivery.py   交付能力断言：把路线图「已完成」变成机器可验事实
  verify_quotes.py    书内语录原文命中门禁（有原著 TXT 时逐条校验）
  backlog_common.py   人工考据队列共享口径层：排序/章节 key/待考筛选
  build_geo_backlog.py 生成地点 + 年份考据队列 docs/geo_backlog.md
  build_quote_backlog.py 生成语录扩面队列 docs/quote_backlog.md
  repo_hygiene.py     仓库分层体检 / 非破坏归档 / 忽略边界门禁
  build_hub.py        门户生成器（书单来自 book_registry.py）
  sync_readme.py      README 生成/校验器（改文案改这里，勿手改 README）
  build.py            统一构建入口（--target standalone|web、--check）
  merge.py            数据聚合 / generate_report.py 最终模型
  audit_final.py      深审（ERROR 即退出非 0）
  validators.py       结构不变量（12 组规则）
  build_dist.py       组装 Pages 发布目录（只挑成品，工程文件不进站点）
  core/               共享核心：年份解析/经纬度校验/势力结构化/图布局
web/                  前端真源：template/index.html + css/app.css + css/theme-ming.css + js/app.js
data/                 聚合数据源与增量勘误层（data.json 是单一数据源）
                      quote_backlog_status.json 只登记「已核对结论」，不是事实来源
tests/                单元测试 + tests/browser_check.py（无头浏览器自检）
                      check_copyright.py 是版权巡检，两条 CI 共用
docs/                 文档：add_a_book.md（新增一本书）、geo_backlog.md（地点/年份考据队列）、
                      quote_backlog.md（语录扩面队列）、history/
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

## 站点发布面

Pages 用 **Actions 部署**（不是「从分支发布」），站点内容 = `src/build_dist.py`
挑出的白名单，仓库里其余文件根本不上传：

```
发布：  index.html  standalone.html  sw.js  ming/  books/
不发布：src/ data/ web/ tests/ docs/ legacy/ teardown/ README.md …
```

改白名单请改 `build_dist.py` 顶部的 `PUBLISH_FILES` / `PUBLISH_DIRS`；新增一本书
只要落在 `books/<id>/` 下就自动包含。产物组装完还会过一道禁忌闸
（`.txt` / `.py` / `quotes.json` / `data.json` 出现即失败），CI 与部署前各跑一次。

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
| 书库连通 | `python src/sync_shelf.py --check` | 6 份报告的导航条是否都是最新版（回门户 / 书间切换不至于退化成死链） |
| 交付能力 | `python src/check_delivery.py` | 按需加载、洞察互跳、离线单文件、门户工具栏的 11 项结构断言 |
| 语录纪律 | `python src/verify_quotes.py` | 幽灵人物卡 / 空值；本机有原著 TXT 时逐条校验「原文命中」（0 命中即失败） |
| 语录扩面队列 | `python src/build_quote_backlog.py --check` | Top 20 滚动队列与 `data.json` / `character_quotes.json` / 结论登记表同步，登记结论后要重生成 |
| 考据队列 | `python src/build_geo_backlog.py --check` | 未定位地点 + 未知年份事件队列与 `data.json` 同步，补了坐标 / 年份就要重生成 |
| 仓库卫生 | `python src/repo_hygiene.py --check` | 私有原文与缓存目录是否仍在 gitignore 内、真源与发布成品是否齐全；体检用 `--report`，归档用 `--archive` |

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

放 `books/<id>/` + 一份 `manifest.json`，跑一次
`python src/build_hub.py` + `python src/sync_shelf.py` 即可，平台代码与 CI 都不用改
——书库导航条的目标清单由 manifest 派生，新书自动获得回门户与书间切换能力。
完整手册见 [`docs/add_a_book.md`](docs/add_a_book.md)。

## 路线图

**已结清**（2026-11-04 复核，结论由 `python src/check_delivery.py` 常驻断言守护）：

- [x] 明书按需加载——此前把两种交付形态混为一谈了。`ming/` 分层版首屏只下
  约 279 KB 的 boot 元数据，10 个数据分块（共 5.3 MB）按视图懒加载，实测
  点「洞察」才请求 `data-insight.js`；`standalone.html`（5.28 MB）是**有意保留**
  的完整离线单文件，按定义不能拆，不在该项范围内。
- [x] 洞察长文与图谱实体互跳——正向：洞察正文里的实体名可点开人物/地点/事件卡
  （实测 466 个可点实体）；反向：卡片内「相关洞察」跳回对应章节并高亮，
  弹窗先行关闭。双向钩子 `linkifyInsight` / `insightBlock` 均有断言覆盖。

**待办**（都需要原文考据，不能凭记忆或推断补齐）：

- [ ] 人物卡语录扩面（现 73 人）：**门禁 + 可勾选队列均已建立**。
  `src/verify_quotes.py` 守原文命中（2026-11-05 修正了 2 条改写词序/加字的漂移，
  补入 7 条归属经上下文核对的引语，现 73 条全部命中、0 失败）；
  [`docs/quote_backlog.md`](docs/quote_backlog.md) 是覆盖章节最多的
  **Top 20 滚动队列**——核对结论登记在
  `data/quote_backlog_status.json` 后该人退出、下一名自动补位，
  「确实没有合适台词」也能销账。**必须逐条核对说话人再入库**：
  自动抽取不可靠，实测 15 条候选里 13 条把「A 对 B 说：…」误归到了 B 名下。
- [ ] 未定位地点与未知年份事件的人工考据（583 个地点中
  553 个已定位）：**两份队列均已生成**
  [`docs/geo_backlog.md`](docs/geo_backlog.md)——30 个冷门古地名
  按提及章数排序，逐条附出处章节 key、书中提及形式与核验路径；另有
  2 个年份待考事件逐条列出（类别 / 相关人员 / 出处章节），
  数字全部从 `data.json` 派生。两份队列都**只列证据，不填推断坐标或年份**；
  剩余的是**逐条查证**本身，不是梳理工作。

历史过程与踩坑记录在 `.workbuddy/`（工程笔记）与 `docs/history/`（重构方案、自查与验收清单）。

## 说明

本项目是个人知识工程：书籍版权归原作者与出版社所有，报告仅作结构化索引与
学习笔记用途，不分发原文，不用于任何商业场景。

<!-- README_GENERATED_BY src/sync_readme.py -->
