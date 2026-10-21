# 拆书项目 Handoff（给接手方）

> 这是一份自包含交接单。接手方不需要本会话历史，读完即可继续工作。
> 最后更新：2026-10-20。项目根目录：`D:\2026\WB项目\拆书`

---

## 1. 项目是什么

把中文小说抽成「人物 / 地点 / 事件 / 关系 / 其他事件」五元组知识图谱（KG），
各产出一份**单文件离线 HTML 报告**（12 个视图，含地图、人物扑克牌卡、关系力导向图、故事长文、多学科视角分析、论文体系）。
报告之外还有一份**跨书共用**的论文产物：`papers/`（15 篇独立论文 + 15 张数据图 + 25 条 Crossref 核验文献）。

> 例外：`swdw`《小说维度晋升，我在天幕当评委》为**独立报告**（世界级精读 KG，非五元组，由回收站找回，见 §7-9 / README v3.17）。

| book_id | 书名 | 作者 | 章数 | kind | 字数 | 状态 |
|---|---|---|---|---|---|---|
| `tiancai` | 《天才基本法》 | 长洱 | 221 | modern_real | 69.5 万 | 100% 抽取完成 |
| `feitu` | 《我在废土世界扫垃圾》 | 有花在野 | 439 | fictional_world | 203.3 万 | 100% 抽取完成 |
| `swdw` | 《小说维度晋升，我在天幕当评委》 | 白水瓶子 | 202 | fictional_world | 48.7 万 | 独立报告（世界级 KG，回收站找回） |

---

## 2. 当前进度（已完成，均已验证）

- 抽取：两书 100% 覆盖（天才 221/221，废土 439/439）。
- 报告：`out/tiancai.html`（0.95 MB）、`out/feitu.html`（2.33 MB）、`out/swdw.html`（**独立报告**，92 KB，世界级精读 KG）、
  `out/index.html`（**书库入口页**：卡片网格 + 总览 + 类型筛选，从 config 现算指标，含 ming 外部书 + swdw 独立报告）。
- 视图：**12 个**——总览 / 分布 / 人物 / 地点 / 地图 / 事件 / 关系 / 阶段轴 / 金句 / 故事 / **学科视角** / **论文**。
- 故事长文：`docs/story_*.md` 已挂入（章号链接全部可点，`verify_story_refs.py` 回算通过）。
- 多学科视角：`docs/perspectives_*.md` 已挂入，**明察式**（结论先行 + 证据 + 来源 + 可信度标注 + 实测/推断分隔），
  `verify_perspectives.py` 全通过（36 项 canonical + 阶段级核对：57 个阶段字符串覆盖 / 16 行 spot / 28 锚点 / 11 旧值黑名单）。
- 阶段引用可点：学科视角正文「阶段名（起–止）」→ 虚线链接，点击跳阶段轴并高亮该段
  （天才 29 个 / 废土 88 个，`probe_phase_refs.js` 点击验证全部正确；同名多段的合计不设链）。
- 工程治理：`src/core/` 共享核心已建（阶段派生 + 章号换算唯一真源），
  `verify_core.py` 守阶段回归 / 章号不变量 / 唯一真源治理（exit 0）。
- ui_audit 遗留四项收尾（v3.7）：事件表「年份」列（两书 100% 空）改「阶段」列
  （构建期 `stage_of` first_no 口径）；亮色 `--ink-3` 调深至 #6f6a5f（全背景过 AA）；
  新增回顶按钮 `#back-top`（探针双书过）；废土地图 + 入口页补审无问题。
- 人物卡深度（v3.9）：卡背加本人语录（A4，天才 5 人 / 废土 46 人）；`role` 裸串经
  `src/role_parse.py` 解析成 身份/关系/在场 三类标签（A5，命中 25/140、66/379），原串保留可回查。
  顺带修了金句章号双口径 bug（见 §6-17）。
- 学科视角扩到 **14 学科**（v3.10，A1 第一步）：新增地理 / 网络科学 / 语言学 / 传播学 /
  法学·秩序 / 伦理学 / 性别研究 / 医学·身体，每科都有 data.json 可复算指标；
  `verify_perspectives.py` 扩到 **56 项 canonical**（新增 19 项）。两项如实降级：
  性别研究只报缺口（覆盖 10.0% / 6.1%，样本不可比）、系统科学并入网络科学不单列。
- **论文体系（v3.11，A1 第二步，最大的形态差距已闭合）**：`papers/` 下 **15 篇独立论文**，
  每篇中英双语题录 + 摘要 + 关键词 + 五节正文（引言/数据与方法/分析与发现/讨论/结论）+
  一张数据图（`figures/fig1.png`，每图单一量纲）+ APA-7 参考文献。
  **25 条文献 25/25 经 Crossref 四道闸核验**（类型族 / 标题 Dice ≥ 0.85 / 年份差 ≤ 1 / 姓氏命中），
  APA-7 由元数据自动生成不手抄，每条带可点开 DOI。正文**零手写数字**（`{{tc.ev}}` 占位符现算）。
  六道闸 `verify_papers.py` 全过：指标独立复算（并查集 vs BFS 两套实现）/ 与 canonical 对齐 /
  结构完整 / 引用闭合 / 数字可溯源 / 文献带 DOI。报告新增**第 12 视图「论文」**，
  深链 `#view=papers&paper=<slug>` 直达单篇。
- 质量门：两书 ERROR 均为 0（WARNING 天才 5 / 废土 4，已定性）。
- **论文正文实体联动（v3.12）**：`insight_link.extend_linked()` 把 15 篇论文文本并进 `linked`
  （只扩可点表面形式，不动 `sections`/`byPerson`——论文没有 sid 锚点，塞进去会点出假入口）。
  实测论文正文可点：**天才 14 处 / 废土 15 处**；跨书边界如实处理：tiancai 报告里「祝宁」不可点
  （不在本 payload），不做假链接。同一轮把 `alias_index` 里「普通词 → 某个具体人」的别名
  （`系统`→祝宁、`新世界`→祝宁、`主任`→教务主任、`清理者`→祝宁…）全部加入 `GENERIC_BLOCK`，
  学科视角链接因此 31→**27** / 39→**35**（宁可少链，不留错链）。探针 `probe_paper_links.js` 双书 PROBE-OK。
- **单元测试 + CI 脚手架（v3.13，C3+C4）**：`tests/` 零依赖 **28 例**（`test_core_books` /
  `test_core_chapters` / `test_core_phases` / `test_insight_link` / `test_gates`），覆盖章号口径、
  阶段基线、实体链接纪律、门禁脚本；`pytest tests` 全绿。`run_checks.py` 本地一键跑 6 步门禁；
  `.github/workflows/ci.yml` 已就绪（语法→单测→重建派生产物→深审→构建→无头冒烟）。
  顺手消除版权风险：`core/phases._derive_tiancai` 不再读含原文的 `chapters.json`，构建只依赖
  可入库的 `data.json` + `extract_raw.json`；`.gitignore` 据此排除 TXT / `chapters.json` 等原文文件。
  **尚未 `git init` / 无 GitHub 远程**，CI 待你确认后接管（部署 Pages 同属这一步）。

---

## 3. 目录 / 文件地图

```
D:\2026\WB项目\拆书\
├─ config.json                 # 书库配置（kinds 类型映射 + 每本书 title/author/kind/accent/report/data_json/external/missing）a_json/external）
├─ HANDOFF.md                  # 本文件
├─ README.md                   # 项目文档（含视图说明、方法论、历次改造记录）
├─ data/<book>/
│  ├─ data.json                # ★主 KG（characters/locations/events/relations/other_events/chapters/meta）
│  ├─ chapters.json            # 章节表（key/index/no/title）
│  ├─ extract_raw.json         # 逐章原始抽取（含 time_hint）
│  ├─ quotes.json              # 金句（对白 + 叙述）
│  ├─ geo_annotations.json     # 地点地理标注（真实/示意/待核验）
│  ├─ geo_zones.json           # 地点分区
│  ├─ manual_corrections.json  # 人工命名校正（含 _why + 原文出处）
│  ├─ duplicate_report.json    # 源文本重复章节检测结果
│  └─ _batch_*.json            # 抽取批次（原始素材，勿删）
├─ data/swdw/                  # ★独立报告书：data.json 为「世界级 schema」（meta/mechanism/worlds/rule_evolution/yu_arc/chapter_index），非五元组
│  ├─ analysis/{_t,_page,_smoke}.js  # 回收站找回的上一版渲染器（_t.js 内含完整图谱 D）
│  ├─ chapters/ + source_combined.txt  # 源文本存档（181/202 章，缺 160–165、188–202）
│  └─ fetch_status.txt
├─ docs/
│  ├─ KG_SPEC.md               # ★KG 规格（节点/边清单、④′ 按学科实测值、⑤缺口、⑥纪律）
│  ├─ story_<book>.md          # 故事长文（源）
│  ├─ perspectives_<book>.md   # ★多学科视角（明察式，源）
│  ├─ _material_<book>.md      # 故事素材包（由 story_material.py 生成）
│  └─ _persp_<book>.md         # 学科素材包（由 perspectives_prep.py 生成）
├─ tests/                      # ★零依赖单元测试（28 例；见 §5）
│  ├─ test_core_books.py       #   书目常量 / load_data 契约
│  ├─ test_core_chapters.py     #   章号口径（no_of 强转 int / 废土 index==no / 天才伪影 index=no+3）
│  ├─ test_core_phases.py       #   阶段派生 vs 基线（天才 14 / 废土 43）/ phase_key / stage_of
│  ├─ test_insight_link.py      #   通称黑名单 / 别名归一 / 长名优先 / 歧义放弃
│  └─ test_gates.py             #   门禁固化（verify_* + sync_readme + 无头冒烟）
├─ .github/workflows/ci.yml    # CI（6 步；待 git init + push 后接管）
├─ requirements.txt            # CI 依赖（仅 matplotlib + pytest）
├─ pytest.ini                  # pythonpath=src，testpaths=tests
├─ run_checks.py               # 本地一键门禁（复刻 CI 6 步）
├─ src/                        # 全部脚本（见 §5）
│  └─ core/                    # ★共享核心 · 唯一真源（阶段划分 / 章号换算）
│     ├─ books.py              #   根路径、JSON 读写、书目常量
│     ├─ chapters.py           #   章号唯一换算入口（no_of / build_key2no / build_idx2no / first_no）
│     ├─ phases.py             #   阶段派生唯一真源 + phases_to_no + phase_key + stage_of
│     └─ baseline_phases.json  #   阶段回归基线（重构前固化，天才 14 段 / 废土 43 段）
├─ web/
│  ├─ template/index.html      # 报告骨架（<section id="view-*"> 在此）
│  ├─ css/app.css              # 样式（含 .badge.cred-* / .nature-* 徽章 / .paper-list）
│  └─ js/app.js                # 前端逻辑（VIEWS 数组 + 各 render* 函数）
├─ papers/                     # ★论文体系（两书共用，非按书分）
│  ├─ README.md                #   论文索引（人工维护）
│  ├─ _metrics.json            #   全部论文指标（papers_prep.py 现算，占位符从这里取值）
│  ├─ references.json          #   25 条文献（verify_refs.py 从 Crossref 拉，含 DOI/相似度/证据）
│  ├─ _src/*.md                #   ★15 篇源（带 front matter：slug/zh/en/kzh/ken/refs/摘要）
│  └─ <slug>/<slug>.md + figures/fig1.png   # 渲染产物（报告只内嵌 md，PNG 不内嵌）
├─ out/                        # ★交付产物（单文件 HTML）
└─ .workbuddy/memory/          # 项目日志（每日 .md），有历次踩坑
```

---

## 4. 常用命令（全部在项目根目录跑，Windows 用 Git Bash / 正斜杠路径）

```bash
python src/generate_report.py     # 重建 out/*.html + 书库入口页（external / missing / standalone 书跳过本地 build，仅入口页收录）
node extract_swdw_d.js && "C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe" src/flatten_swdw_metrics.py && "C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe" src/build_swdw_report.py   # 重建 swdw 独立报告（从回收站 _t.js 重跑亦可）
python src/check_report.py        # 12 视图无头冒烟（需本机 Chrome；--headless=new）
python src/verify_perspectives.py # 复核学科视角文档数字 == KG_SPEC ④′ == 文档（含阶段级核对；退出码非 0 即不一致）
python src/verify_story_refs.py   # 复核故事长文章号链接越界
python src/verify_core.py         # 共享核心自检：阶段回归 + 章号口径 + 唯一真源治理（退出码非 0 即有问题）
python src/verify_refs.py         # 逐条检索 Crossref 核验 26 条候选文献 → papers/references.json（四道闸）
python src/papers_prep.py         # 从 data.json 现算论文指标 → papers/_metrics.json
python src/papers_render.py       # 15 篇源 + 指标 + 文献 → papers/<slug>/（含 matplotlib 数据图）
python src/verify_papers.py       # 论文六道闸：独立复算 / canonical 对齐 / 结构 / 引用闭合 / 数字溯源 / DOI
python src/perspectives_prep.py   # 现算学科素材包 → docs/_persp_<book>.md
python src/graph_spec.py          # KG 规格 → docs/KG_SPEC.md
python src/sync_readme.py         # README 规模表 vs 实算（默认 --check，不一致退出码 1；--write 写回）
python -m pytest tests -q          # 单元测试（28 例，零依赖）
python run_checks.py               # 本地一键门禁（复刻 CI 6 步；--no-headless 跳过浏览器）
node src/probe_phase_refs.js tiancai "第6段（107–141）"   # 点阶段引用链接，核对跳转阶段轴
node src/probe_insight_links.js feitu     # 点学科视角实体名→弹窗；点「相关分析」→跳回并高亮
node src/probe_back_top.js feitu          # 滚到长文中部，验证「回顶」按钮出现且点击发起回顶
node src/probe_deeplink.js tiancai        # 深链 9 条用例（含 #view=papers&paper=13-gender）
node src/probe_paper_links.js feitu       # 论文正文实体可点 + 切篇再切回链接数复原
```

**改 `docs/*.md` 后必须重跑 `generate_report.py`**，否则 HTML 里还是旧内容。
**改 `papers/_src/*.md` 后必须先 `papers_render.py` 再 `generate_report.py`**，顺序反了报告里是旧论文。

本地预览（稳定地址，非一次性临时预览）：
```bash
cd out && python -m http.server 8765 --bind 127.0.0.1
# 打开 http://127.0.0.1:8765/index.html
```

---

## 5. 脚本职责速查（src/）

| 脚本 | 作用 |
|---|---|
| `split_chapters.py` / `dump_chapters.py` / `append_extract.py` | 拆章 / 落盘 / 追加抽取 |
| `merge.py` | 聚合归一（含「弱名不吞强名」防护） |
| `normalize_chapters.py` | 还原真实章号（天才 index 108 后 +3 的修正） |
| `type_reduce.py` | 事件/地点/关系归约到基类 |
| `enrich_geo.py` | 地理增强 |
| `dedup_check.py` | 源文本重复章节检测（difflib 必须 autojunk=False） |
| `src/core/{books,chapters,phases}.py` | ★共享核心 · 唯一真源（阶段派生 + 章号换算）。**任何脚本要阶段/章号都必须从这里 import，禁止再抄一份** |
| `verify_core.py` | 核心自检：阶段回归（对 baseline_phases.json）+ 章号不变量 + 唯一真源治理 |
| `generate_report.py` | ★单文件报告组装（payload 构建 + md 内嵌 + 自检；含 `standalone` 支持位：跳过本地 build、门户正常计数） |
| `extract_swdw_d.js` | ★从回收站 `_t.js` 用 vm 沙箱抽出整本图谱 `D` → `data/swdw/data.json`（一次性恢复脚本，勿删） |
| `build_swdw_report.py` | ★swdw 独立报告生成：世界级精读 → `out/swdw.html`（**不走五元组模板**） |
| `flatten_swdw_metrics.py` | 给 swdw `data.json` 补顶层 `characters/events/relations`，仅供门户 `metrics()` 计数（55/47/14） |
| `graph_spec.py` | 生成 KG_SPEC（④′ 实测值口径的权威来源） |
| `story_material.py` / `perspectives_prep.py` | 故事/学科素材包现算（阶段已改走 core；v3.10 起 14 学科指标） |
| `insight_link.py` | ★学科视角 ↔ 实体双向联动索引（长名优先 / 通称过滤 / 只下发命中项） |
| `verify_refs.py` | ★文献核验：逐条打 Crossref，四道闸（类型族 / 标题 Dice / 年份 / 姓氏）→ `papers/references.json`，APA-7 自动生成 |
| `papers_prep.py` | ★论文指标现算（去重无向对 / 连通分量 / 度 / 对白率 / 性别可判率 / 事件基类占比 / 关键词）→ `papers/_metrics.json` |
| `papers_render.py` | ★论文渲染：front matter → 占位符替换 → matplotlib 数据图 → APA-7 文献装配 |
| `verify_papers.py` | ★论文六道闸（独立复算 / canonical 对齐 / 结构 / 引用闭合 / 数字可溯源 / DOI） |
| `sync_readme.py` | README 规模表自动核对（防手写数字漂移） |
| `md_to_html.py` | Markdown 子集 → 内嵌 HTML（先转义再套行内格式） |
| `check_report.py` | 12 视图冒烟（VIEWS + MARKERS 需与 app.js 同步；含 D′ 论文集成检查） |
| `verify_story_refs.py` / `verify_perspectives.py` | 独立复核（退出码语义化） |
| `audit_final.py` | 质量门（E/W/I 三级） |
| `role_parse.py` | `characters[].role` 裸串 → 身份/关系/在场 结构化（A5，词表驱动） |
| `probe_*.js` / `probe_quotes.py` | 交互态探针（现有 **11 个**：dialog / story_refs / phase_refs / phase_table / chapter_chip / print_cards / insight_links / back_top / deeplink / person_depth / **paper_links**） |
| `evidence.py` / `progress.py` / `quality_checkup.py` | 取证 / 覆盖率 / 脏数据量化辅助 |
| `tests/*.py` | ★零依赖单元测试（28 例）：章号口径 / 阶段基线 / 实体链接纪律 / 门禁脚本 |
| `run_checks.py` | 本地一键门禁（复刻 CI 6 步：语法→单测→重建派生物→深审→构建→无头冒烟） |
| `.github/workflows/ci.yml` | CI（6 步；待 `git init` + 推送到 GitHub 后接管；部署 Pages 同属这一步） |

---

## 6. 硬性约定与坑（接手方 MUST 读）

1. **章号两套编号**：`index`（抽取位置）与 `no`（正文标题章号）。天才 index 112 之后 `index = no + 3`
   （防盗章伪影）。**一切对外展示用 `no`**；`data.json` 里 `chapters` 字段存的是 **key**（如 `tiancai-c126`），
   前端以整数 `index` 为键 → `generate_report.py` 里 `key2idx` 统一转；构建期自检 5 若发现裸 key 会 raise。
   **换算只走 `src/core/chapters.py`**（`build_key2no` / `build_idx2no`，强制 `int()`）——
   曾因一处转 int 一处不转导致阶段统计对不上（v3.3）。
2. **阶段划分唯一真源 = `src/core/phases.py`**。此前 `generate_report.py` 与 `perspectives_prep.py`
   各存一份拷贝、写法不一，`verify_perspectives.py` 又复刻第三份 → v3.3 学科文档 4 处结论级
   数字漂移。现在 `src/*.py` 里若再出现 `def derive_phases` 或 `def build_*2no`，
   `verify_core.py` 直接 FAIL。阶段名**不唯一**（芝士世界×8、第一卷·主线×11），凡做键/链接/文档引用
   一律用 `core.phases.phase_key()` 产出的「名（起–止）」。
3. **明察方法论**（用户否决 v1 的原话是「脏 / 像数据库导出 / 没吸收明察精髓」）：
   - 结论先行；每条结论标 **可信度**（高/中/低）与 **性质**（实测/推断）；**推断不得冒充事实**。
   - 证据一律带 **分子·分母** 可回 `data.json` 复算；**来源**指向具体字段（如 `relations[].rel_base`）。
   - **兜底桶不参与排行榜**（其他/其他场所/其他关系只做脚注披露）。
   - **不假装归类**（无命中就标 unzoned/其他，别硬塞）。
   - 解读性结论要给**边界/阈值**（如「若占比跌破 X% 则结论弱化」），不要用一个数字硬套结论。
4. **同把尺子口径**（`graph_spec.py` line 218/221 是权威）：
   - 支配+上下级 = `rel_base` 的「支配」+「上下级」；
   - 生产+商业 = 地点 `type_base` 的「生产处理」+「商业服务」；
   - 其余学科指标用事件 `type_base`。
   - 事件阶段归属用 `first_no`（事件所有章的最小 no 落到的阶段）。
   - 人物 tier：core≥20 章 / major≥5 / minor≥2 / cameo=1。
5. **前端徽章**：`app.js` 的 `badgeify()` 把正文「可信度：X / 性质：X」转成徽章；
   **正则里冒号必须是全角 `：`**（已用 `[：:]` 兼容，别改回半角）。
6. **报告单文件离线**：不引 CDN、不加依赖；`md_to_html.py` 只支持 Markdown 子集
   （标题/加粗/斜体/行内代码/引用/表格/列表/分割线/段落）。故事长文 `ref=True` 挂章号链接，
   学科视角 `ref=False`（避免把「第6段」误判成章号）——阶段跳转不走 md 层，由前端
   `linkifyPhases()` 在渲染时把「阶段名（起–止）」文本节点替换为链接实现。
7. **阶段名唯一性纪律**（错挂比不链更糟）：payload 的阶段名**不唯一**（天才「芝士世界（高中线）」8 段、
   「现实线」2 段；废土「第一卷·主线」11 段、「第二卷·主线」12 段）。所以：
   - 文档里单段引用一律写「名（起–止）」区间形式（可链、无歧义）；
   - 同名多段的合计数字**不设链接**（如「芝士世界（高中线）62（八段合计）」）；
   - `linkifyPhases` 的裸名模式只对全书唯一的阶段名生效。
8. **文档数字漂移是真实发生过的坑**：v1 学科文档手写时抄了旧版素材包，写出「密度 32–84 件/章」
   （实测 2.00–5.17）、「第一卷·主线 41」（实测 17+6）等与现算差一个数量级的句子，而 canonical
   全对、36 项复核全绿——因为旧复核不覆盖阶段级数字。现 `verify_perspectives.py` v2 已补：
   阶段字符串覆盖 / 区间防虚构 / 逐行 spot / 锚点数字 / **已证伪旧值黑名单**（84.20、98.57、48–113 等）。
   **手写文档数字必须从当前 `docs/_persp_<book>.md` 抄，抄完重跑 verify。**
9. **无头测试**：Chrome 必须 `--headless=new`；`--dump-dom` 拿不到「点开才渲染」的内容 →
   交互态用 `probe_*.js` 探针（现有 10 个，见 §5）。
   注入式探针要检测 `document.title` 而非整个 dom，并给内容纯文本结束哨兵。
10. **两种链接的渲染顺序不能反**：`renderPerspectives()` 里必须**先 `linkifyPhases()`、
   后 `linkifyEntities()`**。反过来实体链接会把「第一卷·主线（220–232）」从中间切碎
   （「主线」被包成 button），阶段引用再也匹配不到——实测废土 88 → 60，丢 28 个。
   阶段名内部的词本就不该链成实体，先阶段后实体恰好是正确取舍。
11. **payload 只下发「文档里真命中的」实体表面形式**：`insight_link.py` 的 `linked`
    （v3.5 时废土 4380 → 19；v3.12 并入 15 篇论文后 4332 → 37）。若把整份实体表
    （人物 + 地点 + 事件数千个）下发，单文件会从 2.04 MB 涨到 2.56 MB（+25%）。
12. **实体链接三条纪律**：长名优先（「假祝宁」不被「祝宁」切走）/ 通称一律不链
    （`GENERIC_BLOCK`；`alias_index` 里有「学姐→林朝夕」这类归约）/ 歧义名不链。
    实测规模：v3.5 天才 8 处 / 废土 13 处 → v3.10 扩科 31 / 39 → **v3.12 清理通称后 27 / 35**，
    比 ming 少一个量级——因为我们的分析是聚合型表格而非叙事散文，属文档性质，如实披露即可，
    不要为了凑数放宽过滤。
    **v3.12 补充第四条：普通词当别名的，一律不链。** 论文正文把链路推到更多文本后，
    `alias_index` 里「`系统`→祝宁、`新世界`/`恶魔`/`火种`/`真神`→祝宁、`武器`/`领袖`→苏何、
    `主任`→教务主任、`部长`→霍文溪、`清理者`/`净化器`→祝宁」这类映射才被发现。
    判据很简单：**这个表面形式在正文里是否可能指别的东西**——「系统」讲的是系统、
    「主任」是职务、「清理者」是职业（废土里不止一人），链到某一个人就是错。
    判不准就进 `GENERIC_BLOCK`（分职务 / 亲属称呼 / 泛称群体 / 隐喻绰号四组）。
13. **「打印/主题」两个控件踩过的坑（v3.4）**：① `printCards()` 曾按 `id="card-grid"` 找容器，
   实际是 `class="card-grid"` 且按 tier 分段——id 选择器恒 null，「打印卡片」一张都没打出来过；
   查选择器前先 grep 产出侧确认是 id 还是 class。② `@media print` 曾输出全部 11 个视图
   （Ctrl+P 实测 69 页 / 10.8MB）——打印作用域要么全收要么显式二态（现：按钮→仅卡片，Ctrl+P→手册模式）。
   ③ 主题命名曾用 ink(暗)/xuan(亮，靠 :root 兜底)，刷新丢失——现为 dark/light + localStorage + 系统偏好。
14. **verify 脚本退出码语义**：0=一致，非 0=有漂移。改 `data.json` / `docs/*.md` 后必须重跑对应 verify + `check_report.py`。
15. **版权**：两本小说 TXT 仅本地留存，**不随报告分发**；报告只含脱敏聚合结果。
16. **无头环境的两个限制 + 探针纪律（v3.7 实测）**：① `--dump-dom` 模式下程序化
    `window.scrollTo` 只改 `scrollY`、**不派发 scroll 事件**（无渲染帧，实测 fired=0），
    探针要手动 `dispatchEvent(new Event("scroll"))` 补；② `requestAnimationFrame`
    在无头模式下不执行——所以滚动处理**不要包 rAF**（浏览器对 scroll 事件本就已节流，
    直接同步切类即可，还保住可测性）。③ **注入式探针必须确认 Chrome 加载的是注入过的
    tmp 副本**，不是 `out/` 原件：`probe_back_top.js` 首跑把原始 feitu.html 传进去，
    读到原始标题还一度以为探针没跑。断言的输入必须是干预后的产物。
17. **关系边有跨章重复计数，拓扑量必须先对去重（v3.10 实测）**：天才 482 条边只覆盖
    **80 个唯一对**（平均每对 6.03 条，党爱萍 59 条边只连 3 个邻居）；废土 1606 → 492 对
    （3.26 条/对）。直接拿边数算度中心性＝把重复计数当社交广度。凡涉及「关系网络」的
    统计（度、平均度、连通分量、救助对数）**一律先用无向对去重**，并把原始条数并列给出。
    同一坑的另一个形态：`§1.3 人均关系边数` 仍是混合口径（关系边 + 事件参与），不能与
    网络科学的度数直接比较。
18. **`ch` 有两套口径，别混（v3.9 真 bug）**：全站 `data-ch` 的契约是**内部索引**
    （`gotoChapter(i)` 按 `chapterById[i]` 找章），而 `quotes.json` 的 `ch` 存的是**书中章号**。
    金句页把 `ch` 直接塞进 `data-ch`，天才 112 章之后点击就会错位 3 章（点「第221章」开 218）。
    判定靠 `chapter_title` 逐条比对（天才 105/105、废土 251/251 → 确认 `ch == no`），不是猜的。
    现由 `idxByNo` 在产出侧换算。**探针不变量**：每个 `data-ch` 链上显示的章号必须等于
    `chapterById[data-ch].n`（`probe_person_depth.js` 的 QUOTE-CH，金句页 135 / 259 条全扫）。
19. **Crossref 里「书评」会冒充「专著」（v3.11 最险的一次）**：Foucault《Discipline and Punish》、
    Scott《Seeing Like a State》、Bauman、Illich 的医学书，在 Crossref 搜到的命中**全是别人的
    book review**——题名很像、年份也接近，直接入库就是伪造引用。`verify_refs.py` 因此有**类型族闸**
    （`expect.type` 必须与记录的 `type` 同族：article/book/chapter），这四本加闸后全部落榜。
    **凡引书必查 `type`，不能只看标题相似度。**
20. **注册题名常省略副标题**：`expect.title` 必须用**Crossref 注册的那一版题名**，否则 token-Dice
   卡在阈值下白落榜——`lin2001`（"Social Capital" 而非全称）0.57、`ostrom1990` 0.44、`brown1987` 0.33。
    同理**年份以注册记录为准**（`held2006` 实为 2005，正文三处跟着改）。
21. **渲染器「缺键即 0」是隐形的造假**：`papers_render.py` 早期对任何缺失指标返回 0，
    13 号论文因此印出「性别可判定 0/221 人」（实数 14）。被 `verify_papers.py` ①号闸抓住
    （现算 14 ≠ 记录 None）。现规则：**只有计数表（`tb`/`tbp`/`rb`/`appel`）缺键才允许返回 0，
    普通标量缺键必须抛错**——宁可渲染失败，不许文档里出现一个漂亮的零。
22. **一张图只能有一种量纲**：01 号图曾把「关系条数 1606」和「孤立率 58.6%」画在同一横轴，
    1606 把 58.6% 压成看不见的一截。饼/条别混百分比与绝对数，**两个量纲就画两张图或两个子图**。

---

## 7. 待办 / 下一步（按优先级，均可选）

1. ~~**故事长文人名/地名可点**~~ ✅ 部分完成（v3.5 学科视角已实现实体联动；故事长文本身仍只有章号链接，可后续按同思路补）。
2. ~~**事件表「年份」列**~~ ✅ 已改为「阶段」列（v3.7，构建期 `stage_of` first_no 口径；13 个卷间过渡章事件显示「—」）。
3. ~~**亮色 `--ink-3` 对比度**~~ ✅ 已调深至 #6f6a5f（全背景过 AA，v3.7）。
4. ~~**A1 第二步：论文化 + APA-7 参考文献**~~ ✅ 已完成（v3.11：15 篇独立成文 + 15 张图 +
   25 条 Crossref 核验文献 + 六道闸；报告升到 12 视图，深链 `#view=papers&paper=<slug>`）。
   ~~剩余可选项「论文正文接入实体联动」~~ ✅ 也已完成（v3.12：论文 14/15 处可点，
   并顺带清理 `GENERIC_BLOCK` 的必错别名）。A1 已完全闭环。
5. ~~**C3 + C4 单元测试 + CI**~~ ✅ 脚手架已完成（v3.13：28 例零依赖单测 + `run_checks.py` +
   `.github/workflows/ci.yml` + `requirements.txt` + `pytest.ini`；`pytest` 与 `run_checks.py` 全绿）。
   **待办（需你确认）**：`git init` + 建 GitHub 远程 + push 后，CI 才真正接管、才能部署 Pages——
   这一步涉及外部仓库，我不会擅自执行。
6. **GitHub Pages 部署**：README ⑦ 用 `gh api` Git Database API 上传 `out/*`；当前未真正部署。
   注意版权硬约束（已由 `.gitignore` 强制）：两本 TXT 与 `chapters.json` **绝不上传**；
   构建现只依赖 `data.json` + `extract_raw.json`，CI/部署不再触碰原文。
7. **WARNING 收尾**：天才 5 / 废土 4 条已定性（多数是龙套无关系、残差等结构事实），非缺陷，可不动。
8. 已知遗留（如实披露，非缺陷）：类型归约残差（废土事件 14.6% / 关系 20.9%，天才事件 4.8% / 关系 23.4%）；
   废土示意地图非现实地理；源文本重复 57 对（天才，已半透明披露）；废土章 250/414 为卷间过渡章不入阶段区间。
9. **《小说维度晋升，我在天幕当评委》（v3.16→v3.17 已闭环）**：用户记作的「世界升维观测员」实为本书
   （白水瓶子；主角观测员余黎、核心维度晋升，故误记）。v3.15 称「本机未找到」是**漏查回收站**——
   原工程（`C:\Users\cunyi\WorkBuddy\2026-09-28-09-49-03\novel\`，2026-09-28 删除）一直躺在
   `C:\$Recycle.Bin`，已恢复到 `data/swdw/`（分章 TXT 181/202 章，缺 160–165、188–202）。
   **v3.17 关键发现**：回收站的 `data/swdw/analysis/_t.js` 不是抓取脚本，而是上一版工程的
   **渲染器 + 已抽取完整图谱 `D`**（meta / 天幕机制 / 7 世界人物·情节·判定·死亡清单 / 规则演化 14 条 /
   余黎成长弧 7 段 / 全 202 章 `chapter_index`）——**KG 早就是全本，不必补 21 章、不必重跑抽取**。
   处理：`node extract_swdw_d.js`（vm 沙箱抽 `D`）→ `data/swdw/data.json`；`src/flatten_swdw_metrics.py`
   补顶层 `characters/events/relations`（55/47/14，仅供门户计数）；`src/build_swdw_report.py`
   生成 `out/swdw.html`（世界级精读，**不走五元组流水线模板**）。
   `config.json` 的 `swdw` 由 `missing:true` 改为 **`standalone:true`**（保留 `data_json`/`report`）；
   `generate_report.py` 加最小 `standalone` 支持位：`main()` 跳过其本地 build，`build_portal()` 正常计数 + 可点链接。
   **注意**：swdw 的 `data.json` 是**世界级 schema**（meta/mechanism/worlds/rule_evolution/yu_arc/chapter_index），
   **不能**喂给 `build()`（那个要五元组 schema，会 KeyError）；顶层 `characters/events/relations` 仅为门户计数而加。

> 已完成（勿重做）：学科视角挂阶段链接（v3.3）——没走 `ref=True`，用前端 `linkifyPhases()` 链「阶段名（起–止）」。
> 已完成（勿重做）：打印作用域 + 主题持久化（v3.4，见 `docs/ui_audit.md`）——打印按钮修好（曾零卡片）、
> Ctrl+P 保留手册模式、主题改 dark/light + localStorage + 系统偏好；`probe_print_cards.js` 固化验证。
> 已完成（勿重做）：学科视角 ↔ 实体双向联动 + README 自动核对（v3.5）——`insight_link.py` +
> `linkifyEntities()` / `insightBlock()` / `gotoInsight()` + `probe_insight_links.js`；
> `sync_readme.py --check` 守 README 规模表。
> 已完成（勿重做）：`src/core/` 共享核心 + `verify_core.py`（v3.6）——阶段派生与章号换算从
> 「三份口径」收敛到唯一真源，重构前后素材包 diff 零差异、阶段对基线逐格一致；
> 顺手修了 `TC_TIME_HINTS` 死项（`("小时候","童年线")` 永远命中不到，已改为 `("童年","童年线")`，
> 已验证阶段划分结果不变）。
> 已完成（勿重做）：ui_audit 遗留小项打包（v3.7）——事件表年份列改阶段列、`--ink-3` 调深过 AA、
> `#back-top` 回顶按钮（`probe_back_top.js` 双书过）、废土地图与入口页补审；
> 详见 `docs/ui_audit.md` §2.4。
>
> **下一轮的系统改进清单见 `docs/roadmap_vs_ming.md`**（对照姊妹项目 `D:\2026\WB项目\明朝`
> / GitHub `CochraneK/book-meal`（原 `ming`），分 UI / 丰富度 / 工程治理三层，带优先级与工作量）。
> 第一梯队（A2 / C5 / B5）、第二梯队（C1 / B1 / A4+A5）、第三梯队的 **A1 全两步**均已闭环；
> 丰富度已基本追平 ming（15 篇 vs 19 篇，25 条 vs 71 条文献）。**工程治理**里的 **C3+C4 脚手架**
> 已完成（单测 + `run_checks.py` + CI 工作流就绪，仅差 `git init`+push 这一外部动作）；
> 剩 `core/spec.py`（同把尺子口径收敛）与 **C6 部署 Pages**（与 git 初始化同源，待你确认）。

---

## 8. 完成一件事后的标准动作

1. 重跑 `python src/generate_report.py`（重建 HTML）。
2. 重跑 `python src/check_report.py`（12 视图冒烟）+ 相关 `verify_*.py`（数字复核）。
   改论文源则顺序为 `papers_prep.py` → `papers_render.py` → `verify_papers.py` → `generate_report.py`。
3. 若新增视图/改文案：同步 `check_report.py` 的 `VIEWS` / `MARKERS` 与 `app.js` 的 `VIEWS` 数组。
4. 在 `.workbuddy/memory/YYYY-MM-DD.md` 追加当日记录（append-only）。
