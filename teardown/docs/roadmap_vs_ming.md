# 对照 CochraneK/book-meal（原 CochraneK/ming）的系统改进清单

> 参照系：`D:\2026\WB项目\明朝`（GitHub `CochraneK/book-meal`，2026-10-21 由 `ming` 改名，在线 https://cochranek.github.io/book-meal/ ）
> ——同一方法论下的姊妹项目：《明朝那些事儿》156 章 / 1231 人物 / 1106 事件 / 2324 关系。
> 本文只写「还差什么」，每条都带**当前实测状态**与**工作量**，按性价比排序。
> 生成日期：2026-10-19 ｜ 总表与 A1/A2/B1/C5 已于 v3.11–v3.12 后按实测刷新

## 结论先行

1. **丰富度差距已基本填平**（v3.11 后更新）：ming 是 **19 篇可发表论文体系**（18 学科 + 综合，md + docx + 数据图 + 英文元数据 + APA-7 参考文献 71 条全部检索核实）；本项目 **15 篇独立论文 + 15 张数据图 + 25 条 Crossref 核验文献**，形态对齐，规模略小（学科 15 vs 19，文献 25 vs 71）。
2. **UI 差距集中在「可分享」与「失败可见」**：ming 有 10 类深链参数（view/person/detail/event/place/era/map/q/net/from/to）与统一错误提示条 + 启动守卫；本项目已扩到 **7 类**（含 `paper`），仍**没有任何运行时错误提示**（`fail-bar`/`__READY`/`onerror` 计数均为 0）。
3. **工程治理差距在「唯一真源」**：ming 有 `src/core/` 共享核心 + `validators.py` 单一规则源被四处共用 + 55 例单元测试 + CI；本项目已建 `src/core/`（阶段/章号口径收敛完成，见 C1）+ **28 例零依赖单元测试** + **CI 脚手架**（见 C3/C4，待 `git init`+push 接管），但仍缺 `validators.py` 单一规则源；C6 部署与 git 初始化同源，待你确认。

## 对照总表

> 表中「本项目」列已按 **v3.11 实测**刷新（原表为 2026-10-19 早期状态，多处已闭合）。

| 维度 | ming（明朝） | 拆书（本项目） | 差距 |
|---|---|---|---|
| 报告视图 | 12 | 12（含「论文」视图） | 持平 ✓ |
| 学科长文 | 19 篇独立论文 | **15 篇独立论文**（中英双语题录） | 小 |
| 参考文献 | APA-7 × 71 条，逐条检索核实 | **APA-7 × 25 条，25/25 Crossref 四道闸核验** | 小（量差，质同） |
| 数据图 | 每篇配 figures/ | **15 张**（每篇一张，单一量纲） | 小 |
| 长文↔实体联动 | 双向（正文可点 + 详情反向 chip） | 视角 27/35 处双向 + **论文正文 14/15 处可点**（单向） | 小 |
| 深链参数 | 10 类 | 7 类（view / q / person+detail / place / event / phase / paper） | 小 |
| 错误可见 | failBar + 启动守卫 | 无 | 中 |
| 搜索 | bindSearch + 高亮 | bindSearch + 高亮 | 持平 ✓ |
| 关系端点类型 | `.ep-tag` 徽标 | `from_kind`/`to_kind` 已有 | 持平 ✓ |
| 主题 | 3 套（墨玉/宣纸/朱砂） | 2 套（dark/light） | 小 |
| 单元测试 | 55 例零依赖 | 28 例零依赖（`pytest` 全绿；覆盖章号/阶段/链接纪律/门禁） | 小 |
| 共享核心 | `src/core/` 6 模块 | 3 模块（books/chapters/phases，2026-10-19 完成） | 中 |
| CI | GitHub Actions 6 步 | 脚手架就绪（`.github/workflows/ci.yml` + `run_checks.py`；待 `git init`+push 接管） | 小 |
| README 统计 | `sync_readme.py` 自动刷新 | `sync_readme.py --check` 自动校验（2026-10-19 完成） | 持平 ✓ |
| 部署 | Pages 已上线 + SW | 未部署 | 中 |

---

## A. 丰富度（内容深度）

### A1. 学科论文体系 `papers/`【✅ 两步均已完成 2026-10-19（v3.11）】
ming：`papers/` 19 篇，每篇 `xx.md` + `xx.docx` + `figures/`，带英文标题/摘要/关键词与 APA-7 参考。
本项目：`docs/perspectives_{tiancai,feitu}.md`，**14 学科**合并一篇。

**第一步（中）✅**：学科 6 → 14（v3.10）。原计划 8 科全部落地，无一凑数：
社会学 / 心理学 / 经济学 / 政治学 / 叙事学 / 教育学 + **地理学 / 网络科学 / 语言学 /
传播学 / 法学·秩序 / 伦理学 / 性别研究 / 医学·身体**。
每科都有 data.json 可复算指标，`verify_perspectives.py` 扩到 56 项 canonical。
两项如实降级：① **性别研究只报缺口**（词表覆盖 10.0% / 6.1%，样本不可比，不给结论）；
② **系统科学/人类学未单列**——现有字段（连通分量、度分布）已并入「网络科学」，
再拆一节会变成同一批数字换说法。

**第二步（大）✅ 已完成（v3.11）**：论文化 —— 15 篇独立成文，每篇带数据图、中英元数据、APA-7 参考文献。
> 纪律红线：参考文献必须逐条检索核实后才写入（ming 的硬纪律）；书内情节/语录必须先在原文命中再引用（0 命中即弃用）。

产物：`papers/_src/*.md`（15 篇源）→ `src/papers_render.py` → `papers/<slug>/<slug>.md` + `figures/fig1.png`。
参考文献 **25 条，25/25 经 Crossref 四道闸核验**（类型族 / 标题 Dice ≥ 0.85 / 年份差 ≤ 1 / 姓氏命中），
APA-7 由元数据自动生成、不手抄，每条带可点开 DOI。
15 篇：社会学 / 心理学 / 经济学 / 政治学 / 叙事学 / 教育学 / 地理学 / 网络科学 / 语言学 /
传播学 / 法学·秩序 / 伦理学 / 性别研究 / 医学·身体 / 方法论。

**三条硬约束**（v3.11 立）：
1. 正文**零手写数字**——一律 `{{tc.ev}}` / `{{ft.tbp.战斗}}` 占位，渲染时从 `papers/_metrics.json` 取值；
2. 文献必须**机器核验**——`src/verify_refs.py` 逐条打 Crossref，不通过不入库；
3. 每张图**只允许一种量纲**——条数图不混百分比（v3.10 曾把 1606 和 58.6% 画在同一横轴，58.6% 被压成看不见的一截）。

**六道闸**（`src/verify_papers.py`）：① 指标独立复算（并查集 vs BFS，两套实现故意不共用）
② 与 `verify_perspectives.CANON` 对齐 ③ 结构完整（摘要/Abstract/关键词/Keywords/五节/参考文献/图存在）
④ 引用闭合（正文 Author-Year ↔ 条目双向，姓氏 NFKD 去重音）⑤ 数字可溯源（正文每个百分比和
三位以上整数都要能指到指标来源）⑥ 每条文献带 DOI。

**如实披露的三处取舍**：① 人文经典无原版 DOI（Hart / Genette / Tuan / Lefebvre / Butler 1990）
→ 只保留能在 Crossref 定位真实版本的文献，无法核验的经典用同主题有 DOI 文献替代
（Gieryn 2000 替 Tuan、Bury 1982 替 Kleinman、Cover 1986 + Ewick & Silbey 1995 替 Foucault/Hart）；
② 四本专著在 Crossref 只有**书评**记录（Foucault / Scott 1998 / Bauman / Illich 医学书），
加类型族闸后全部落榜，不是「引了但没查」；③ OpenLibrary / Google Books / Wikidata 在本机网络下
全 502 或空响应，OpenAlex 对人文专著同样只收书评——**Crossref 是唯一可用源，这是外部约束不是选择**。

**剩余可做（已完成 v3.12）**：论文正文实体联动已接入——`insight_link.extend_linked()` 只扩
`linked`、不动 `sections`/`byPerson`（论文没有 sid 锚点，塞进去会点出跳不过去的假入口）。
实测论文正文可点：天才 14 处（15 篇中 8 篇有）、废土 15 处（7 篇有）。
同一轮把 `alias_index` 里「普通词 → 某个具体人」的别名（`系统`→祝宁、`主任`→教务主任、
`清理者`→祝宁…）全部加进 `GENERIC_BLOCK`，学科视角链接因此 31→27 / 39→35（宁少不错）。

### A2. 学科视角实体联动（双向）【✅ 已完成 2026-10-19】
实现：`src/insight_link.py`（构建期索引）+ `app.js` 的 `linkifyEntities()` / `insightBlock()` /
`gotoInsight()` + `src/probe_insight_links.js`（第 6 个探针，双书 PROBE-OK）。
实测规模（v3.5 时）：**天才 8 处 / 3 人，废土 13 处 / 8 人 + 10 地点，事件 0**；
v3.10 扩科后升到**天才 31 处 / 废土 39 处**（新学科正文提到了更多实体）；
**v3.12 清理通称别名后为 27 / 35**（`系统`→祝宁、`主任`→教务主任 这类必错链全部断开，
代价如实计入）。论文正文另有 14 / 15 处单向链接（v3.12）。
比 ming 的 207 次少一个量级——根因是文档性质：ming 的洞察是叙事散文，我们的是
**聚合型表格**（结论 + 证据表），人名本就稀疏。这个数字如实披露，不粉饰。
两个工程收获：① payload 只下发「文档里真命中的」表面形式（4380 → 19），
否则单文件凭空涨 25%；② **链接顺序不能反**——先阶段后实体，反过来实体会把
「第一卷·主线（220–232）」从中间切碎，废土阶段链接 88 → 60 丢了 28 个。

（以下为原方案描述，留作背景）

ming：`src/core/insight_link.py` 构建 `insightIndex` → `linkifyInsight()` 把正文里的人名/地名/事件名包成可点按钮 → 详情弹窗插「相关洞察」chip 反向跳回。规模参考：19 节 → 人物 207 次 / 97 人，地点 92 次 / 57 个，事件 17 次 / 14 件。
本项目：**只有阶段名可点**（v3.3 `linkifyPhases()`），人名/地名/事件名全是死文字。

本项目已有 70% 基础设施可复用：`linkifyPhases()` 的 TreeWalker（只走文本节点、跳过 `a/code/script`）、`showPerson()`/`showPlace()`/`showChapterRef()`、`data.json` 的 `alias_index`。
新增：构建期索引（~80 行）+ 前端 `linkifyEntities()`（~100 行）+ 反向 chip（~40 行）+ 探针（~60 行）。
> 纪律：≥2 字整名匹配、长名优先、`GENERIC_BLOCK` 滤通称（否则正文里每个「老师」「队员」都会被链成人物卡）。

### A3. 数据图【工作量：中】
两份学科文档目前全是表格。可把阶段密度曲线、类型构成堆叠、关系占比做成内嵌 SVG（单文件离线不允许引 CDN，需手写 SVG 或纯 CSS）。

### A4. 人物卡背放语录【✅ 已完成 2026-10-19】
卡背加本人语录（`by_person` 里归属分数最高的一条，最多 3 行）；详情弹窗给前 3 句，
带可点章号 + 归属依据（`引号后标签`/`句首人名`/`引号前标签`）。
覆盖：天才 5 人 / 废土 46 人（对白归属率是抽取的既有局限，未硬凑）。
固化为 `src/probe_person_depth.js` 的 `A4back` / `A4dlg` 断言。

### A5. `role` 字段结构化（对标 `faction_profile`）【✅ 已完成 2026-10-19】
`src/role_parse.py` 词表驱动解析出 身份 / 关系 / 在场 三类标签，详情弹窗按字段分组，
原串保留可回查，覆盖率构建期 INFO：天才 25/140、废土 66/379。
三条从数据里踩出来的规则：① 只认分句末尾的中心语（「…的领导」不是实习生）；
② 动词开头 / 「…的人」收尾的分句不取身份；③ **在场状态只在单章角色上判定**
（`role` 描述的是该章，`（本章被提及）` 出现在 131 章的裴之身上就是证据）。
剩余可做：扩展词表（当前只收 80 余个高频身份词）。

### A6. `other_events` 是否已被展示【待核实】
`data.json` 有 `other_events` 字段，需确认报告里是否有对应视图——若有富矿未展示，属丰富度漏洞。

---

## B. UI

### B1. 深链参数扩展【✅ 已完成 2026-10-19】
读侧 7 类参数：`view` / `q`（预填搜索框）/ `person`（+`detail=1` 开弹窗，**认别名**，
目标在龙套档时自动放宽显示范围）/ `place` / `event` / `phase`（序号或「名（起–止）」唯一键）/
`paper`（v3.11 新增，篇目 slug，如 `#view=papers&paper=13-gender`）。
写侧用 `history.replaceState` 回写当前状态——**不能用 `location.hash` 赋值**（会触发
hashchange → 再 apply → 死循环）。弹窗参数只在「当前视图与实体同类」时才回写，
地址栏不谎报所在视图。`src/probe_deeplink.js`（第 9 个探针）**9 条用例**双书固化：
person+detail（含别名「学姐→林朝夕」）/ event / place / phase 序号 / q 预填+过滤 /
非法键回退总览 / replaceState 回写 / phase 唯一键 / **paper 篇目切换（断言篇目数 15 且正文切到指定篇）**。

> 与 ming 的差距从「1 类 vs 10 类」缩到「7 类 vs 10 类」——ming 多出的 `net`/`from`/`to`
> 是关系图专用参数，待 B3 阶段轴筛选/关系图筛选时再补。

### B2. 统一错误提示条 + 启动守卫【工作量：中】
实测：本项目 `app.js` 里 `fail-bar` / `__READY` / `window.onerror` **计数均为 0**，即脚本解析失败或数据畸形时是静默白屏。
ming 的做法：底部提示条（`role=alert` + `aria-live` + 三级配色 + 重试 + 关闭，按 key 去重）+ **独立成段、排在主脚本之前的启动守卫**（主脚本一旦解析失败，它内部的兜底都不会执行）。
本项目是单文件离线、外部依赖极少，失败面比 ming 小，但「静默白屏」仍是最难排查的用户体验。

### B3. 阶段轴区间筛选 / 深链【工作量：小-中】
对标 ming 时间轴 `from`/`to`（写回地址栏）。本项目阶段轴无筛选，43 个阶段（废土）只能滚。

### B4. 无障碍补口【工作量：小-中】
实测：`web/template/index.html` 有 13 处 `role=`/`aria-`，`web/js/app.js` 只有 2 处——**动态渲染的内容基本没有无障碍属性**。
可补：canvas 图 `role="img"` + 动态 `aria-label`、表格 `aria-live`、tabs 方向键导航。

### B5. ui_audit §3 遗留【✅ 已完成 2026-10-19】
① 事件表「年份」列两书 100% 为空（833/833、2591/2591）→ **改为「阶段」列**（构建期
`core.phases.stage_of` 算好，13 个卷间过渡章事件显示「—」并 INFO 披露）；
② 亮色 `--ink-3` #9a958a（≈3.0:1）→ **#6f6a5f**（白 5.37 / 米 4.89 / panel-2 4.59，全过 AA）；
③ 故事 7 万字视图 **新增 `#back-top` 回顶按钮**（`probe_back_top.js` 双书过）；
④ 废土地图 + 入口页补截图审查（`docs/_shots/`），无版面问题。
⑤ 的 8/9/10 三项经复核判定为设计取舍或暂不触发（二态打印是设计、节点筛选已明示、
Leaflet 分支未启用），保持原状。详见 `docs/ui_audit.md` §2.4。

> 本轮（v3.7）另实测到两个无头环境限制，写入探针注释：`--dump-dom` 下程序化
> `window.scrollTo` 不派发 scroll 事件（无渲染帧，实测 fired=0）；`requestAnimationFrame`
> 不执行。所以前端的滚动处理**不要包 rAF**（可测性 + 无收益）。

### B6. Service Worker / PWA【工作量：中 · 不建议优先】
本项目单文件双击即开，SW 价值远低于 ming（后者 5 MB 在线首页才需要秒开）。若后续真部署 Pages 再考虑。

---

## C. 工程治理

### C1. `src/core/` 共享核心【✅ 已完成 2026-10-19（phases + chapters）】
ming 硬性规定「生产与审计必须共用，禁止各写一份」。
本项目已踩坑：`generate_report.py:derive_phases_*` 与 `perspectives_prep.py` 各有一份阶段派生，v3.3 时发现两处 `key2no` 一个转 `int()` 一个没转；`verify_perspectives.py` 又复刻了第三份。

**已完成**（`src/core/`，三个模块）：
- `core/books.py` —— 根路径 / JSON 读写 / 书目常量
- `core/chapters.py` —— 章号唯一换算入口（`no_of` / `build_key2no` / `build_idx2no` / `first_no`），
  强制 `int()`，并写明 index↔no 两套编号的事实（天才 index>112 时 index=no+3）
- `core/phases.py` —— 阶段派生唯一真源 + `phases_to_no` + `phase_key`（「名（起–止）」）+ `stage_of`

消费者全部改为 import：`generate_report.py` / `perspectives_prep.py` /
`story_material.py` / `verify_perspectives.py` / `verify_story_refs.py`。

**零行为变更已实证**：重构前固化基线 `core/baseline_phases.json`（天才 14 段 / 废土 43 段，
index 与 no 双口径）；重构后 `verify_core.py` 逐格比对通过；两份学科素材包
`docs/_persp_*.md` **diff 零差异**。

**顺手修的真 bug**：旧 `generate_report.py` 的 `TC_TIME_HINTS` 末项是
`("小时候","童年线")`，排在 `("小时候","回忆线")` 之后**永远命中不到**（死项）；
`perspectives_prep.py` 写的是 `("童年","童年线")`（语义正确）。core 统一为正确版本，
已验证两书阶段划分结果不变。

新增 `src/verify_core.py` 守三件事：阶段回归（对基线）、章号不变量（全 int / 对齐关系）、
**唯一真源治理**（`src/*.py` 里再出现 `def derive_phases` 或 `def build_*2no` 即 FAIL）——
防止未来又抄一份。

**未做（可后续补）**：`core/spec.py`（同把尺子口径：支配+上下级、生产+商业…仍是各处手写）、
`core/entity_index.py`（别名与实体索引，目前只在 `insight_link.py`）。

### C2. `validators.py` 单一规则源【工作量：中】
ming：`validators.py` 12 组规则被 `build --check` / `audit_final` / `tests` / CI **四处共用**，ERROR/WARNING/INFO 三档。
本项目：质量门分散在 `audit_final.py`、`quality_checkup.py`、`verify_perspectives.py`、`verify_story_refs.py`、`check_report.py`，口径各自定义。

### C3. `tests/` 单元测试套件【✅ 已完成 2026-10-20（v3.13）】
ming 55 例零依赖。本项目已建 `tests/`（**28 例零依赖**，stdlib `unittest` + pytest 双跑）：
`test_core_books` / `test_core_chapters`（no_of 强转 int / 废土 index==no / 天才 index=no+3 伪影）
/ `test_core_phases`（派生 vs 基线 14/43、phase_key、stage_of 首章归属）
/ `test_insight_link`（通称黑名单 / 别名归一 / 长名优先 / 歧义放弃）
/ `test_gates`（把 verify_* + sync_readme + 无头冒烟固化成断言）。
`pytest tests` 全绿；`run_checks.py` 本地一键复刻 CI 6 步。
规模小于 ming（28 vs 55），但覆盖了本项目**最易漂移、最致命**的不变量（章号口径、阶段基线、链接纪律）。

### C4. CI【✅ 脚手架已完成 2026-10-20（v3.13）；待 git init + push】
已写 `.github/workflows/ci.yml`（6 步：语法 → 单测 → 重建派生产物 → 深审 → 构建 → 无头冒烟）、
`requirements.txt`（仅 matplotlib + pytest）、`pytest.ini`（`pythonpath=src`）。
**未做**：`git init` + 建 GitHub 远程 + push——这一步涉及外部仓库，需你确认后我才执行，CI 才会真正接管。
顺手消除版权风险：`core/phases._derive_tiancai` 不再读含原文的 `chapters.json`，构建只依赖
可入库的 `data.json` + `extract_raw.json`；`.gitignore` 据此排除 TXT / `chapters.json` / `_batch_*.json` /
`quotes.json` 等原文与中间产物，**CI 与未来部署都不会触碰小说原文**（C6 的前置已具备）。

### C5. `sync_readme.py`：README 统计自动刷新【✅ 已完成 2026-10-19】
实现：`src/sync_readme.py`，默认 `--check`（不一致退出码 1），`--write` 写回。
覆盖 7 行可现算项（章节覆盖 / 人物地点 / 事件关系 / 同章上下文事件 / 类型归约 / 金句 / 源文本重复）。
实测首跑：**7 行全部一致**（说明尚无漂移），门禁已立住。
不自动刷新的行（质量门 WARNING 数、视图冒烟、长文引用数）依赖跑完审计才知道，脚本不猜。

不自动刷新的行（质量门 WARNING 数、视图冒烟、长文引用数）依赖跑完审计才知道，脚本不猜。
✅ 原「README 里的人物/事件/关系/地点数是手写的」风险已随本项闭合。

### C6. 部署上线【工作量：中】
README ⑦ 写了 `gh api` Git Database API 方案，但**从未真正部署**。ming 已上线 Pages + SW + `post_publish_check`。
注意版权硬约束：两本小说 TXT 与含正文的 `chapters.json` **绝不上传**。

### C7. 工程 skill 化【工作量：小】
ming 有 `.workbuddy/skills/ming-report-engineering/SKILL.md`（344 行），换会话自动加载。本项目只有 `HANDOFF.md`（需人工读）。可把 HANDOFF 的「硬性约定与坑」转成 skill。

### D1. 书库门面聚合（汇聚多书入口）【✅ 已完成 2026-10-20（v3.14 + v3.15）】
用户提出「拆的书越来越多，能否有个汇聚平台（含 ming/feitu/tiancai）」。
探查结论：ming 仓库是**单书单站**而非多书平台；两边 KG 约 70% 兼容（人物/事件/关系/地点），
但时间模型不同（拆书 章→阶段；ming 朝代/年号/航海）。据此选 **门面聚合** 而非 **数据融合内核**
（后者需为 ming 写时间适配器、工程数周级）。

实现：升级 `out/index.html` 从硬编码两卡 → 书库入口页（卡片网格 + 总览 + 类型筛选）。
`config.json` 新增 `kinds` 类型映射 + 每本书 `accent/report/data_json/external`；
`build_portal()` 从 config 现算每本书人物/事件/关系三项指标（零手写，缺失显「—」）；
**明朝作为外部书**录入（report→`../明朝/standalone.html`，data_json→`../明朝/data/data.json`，
构建期现算指标、不含全文）；`main()` 无参只本地构建非 external 书。
**总览实测（现算）**：4 本书（已就绪 3 · 待重建 1）· 人物 1750 · 事件 6891 · 关系 4412。
加书只需 config 加一条；若原数据暂缺，可用 `missing: true` 占位录入（指标显「—」、不计入总览、
打开链接灰显「数据待重建」），找回原文后再补 `data_json`+`report` 并去掉 `missing`
（v3.15 已用《世界升维观测员》验证——该书本机全盘未找到任何数据）。

> 下一步若做 **D2 多书融合内核**：所有书数据归一进本项目 data/，统一模板，支持跨书搜索/对比。
> 主要成本 = 为 ming 写时间模型适配器（朝代/年号 ↔ 章节/阶段）。作为远期规划，非当前必需。

---

## 优先级建议（我的判断）

**第一梯队——性价比最高，立即做**
1. ~~**A2 学科视角实体联动**~~ ✅ 已完成（2026-10-19）
2. ~~**C5 `sync_readme.py`**~~ ✅ 已完成（2026-10-19）
3. ~~**B5 ui_audit 遗留小项**~~ ✅ 已完成（2026-10-19，v3.7：阶段列 / 对比度 / 回顶 / 补审）

**第二梯队——结构性提升**
4. ~~**C1 `src/core/` 共享核心**~~ ✅ 已完成（2026-10-19，phases + chapters；`spec.py`/`entity_index.py` 未抽）
5. ~~**B1 深链参数扩展**~~ ✅ 已完成（2026-10-19，6 类读参数 + replaceState 回写 + 8 用例探针）
6. ~~**A4 卡背语录 + A5 `role` 结构化**~~ ✅ 已完成（2026-10-19，v3.9；顺带修金句章号双口径 bug）

**第三梯队——大工程**
7. ~~**A1 第二步：论文化 + APA-7 参考文献**~~ ✅ 已完成（2026-10-19，v3.11：15 篇独立成文 + 15 张图 + 25 条 Crossref 核验文献 + 六道闸；报告升到 12 视图，深链 `#view=papers&paper=<slug>` 直达单篇）
8. ~~**C3 + C4 单元测试 + CI**~~ ✅ 脚手架已完成（2026-10-20，v3.13：28 例单测 + `run_checks.py` + `ci.yml` + `requirements.txt` + `pytest.ini`；`pytest` 与 `run_checks.py` 全绿）。**仅差 `git init`+push 这一外部动作**。
9. **C6 部署 Pages**（与 git 初始化同源，待你确认后做；版权前置已具备）。

**第四梯队——平台化（汇聚多书）**
10. ~~**D1 书库门面聚合**~~ ✅ 已完成（2026-10-20，v3.14+v3.15：config 驱动的书库入口页 + 明朝外部书 + 世界升维观测员待重建占位卡；现算总览 1750/6891/4412（4 本，1 待重建））。
11. **D2 多书融合内核**（远期：数据归一 + 跨书搜索/对比，需为 ming 写时间适配器）。

**明确不建议做**
- Service Worker / PWA（单文件离线场景价值低）。
- 分部构建（ming 的 `--scope p1..p7`）——本项目按书构建，已足够。
- 废土地图改真实地理——虚构世界用示意地图是正确选择（错误坐标比缺失更有害）。
