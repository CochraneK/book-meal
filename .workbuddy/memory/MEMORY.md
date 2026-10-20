# 明朝项目长期记忆（MEMORY.md）

## 项目身份
- **Ming**：本地 `D:\2026\WB项目\明朝`；GitHub `CochraneK/ming`（public）；在线 https://cochranek.github.io/ming/ 。
- **参考实现**：通用流程在 `~/.workbuddy/skills/novel-spacetime-knowledge-graph/`（做同类小说**复制本项目 `src/` 再改**）；项目专属细节在 `.workbuddy/skills/ming-report-engineering/`。两者勿混用。

## 现状与规模（2026-09-14 自查轮）
- **规模**：章节 156 / 地点 583（定位 553=**94.9%**，未定位 30）/ 人物 1231 / 事件 1106（待考 **2**）/ 关系 2324 / 在位 17 帝 / 年谱 165 人。`data.json` 地点 563（`event_places.json` 注入 +20，非 bug）。
- **视图 12 个**：总览/分布/图谱/地点/地图/人物/事件/关系/时间轴/王朝/年谱/洞察。洞察 19 节 = 18 学科 + 综合（素材已饱和，**勿再立新学科**）。
- **构建**：`python src/build.py`（`--scope full|p1..p7`、`--target standalone|web`、`--check`、`--json`）全量 **≈2 秒**，单文件 **5.27 MB**。前端模板/CSS/JS 在 `web/`，**改前端只动 `web/`**；单文件由 `compose_document()` 唯一注入。
- **校验四层**：`build.py --check`（`validators.py` 12 组，ERROR→退出码 2）→ `src/audit_final.py`（深审，ERROR→1；当前 **INFO 17 / WARNING 1 / ERROR 0**，唯一 WARNING = 有意保留的 2 件待考事件）→ `tests/run_tests.py`（**55 例**，纯标准库）→ `.dump/_browser_check.py`（Chrome `--dump-dom`，**14 场景**）。
- **CI**：`.github/workflows/ci.yml`（版权巡检→语法→单测→构建门禁→深审→产物+无头自检），实测 green；**不需要 `data/chapters.json`**。

## 口径与契约（有测试守，数字绝不能串）
- **人物关系图（方案 A）**：节点只允许人物表内实体；**686 人 / 1403 边 / 孤立 545（44.3%）/ 排除 72 条任一端点非人物的关系**。审计 R-REL-00 与 R-GRAPH-00 的「72」必须一致（曾因死表达式漂移）。
- **双模式图**：`activeGraph()` 是唯一分发入口；`net=entity` 实体图 **741 实体 / 1467 条**（人物 694 + 机构 12 + 其他 16 + 地点 15 + 政权 4）。**契约：1403 ⊆ 1467**。实体图不能说「N 名人物」。
- **关系范围**：全书=all，分部(p1~p7)=**induced**（判据=「两端人物在不在范围」，**不是** source 章节在不在）。亲属「长辈→晚辈」；端点类型按 人物→地点→政权→派系机构→其他。
- **统一 ID**：`entity_id()`→`person:朱由检`；`relation_id()`=`relation:<sha1[:12]>`；payload 带 `model{schemaVersion:3,…}`。
- **共享核心**：`src/core/{year_parser,geo,faction_profile,graph_layout,insight_link,place_mentions}.py`。**生产与审计必须共用，勿各写一份**。`geo` **禁止 `if not lat`**（0 是合法值）。
- **势力结构化**：`core/faction_profile.py` 解析 `characters[].faction` → `profile{…}`。政权 1161/1231（94.3%）、官职 426、身份类别 320、派系 109、籍贯 26、科举 16，未归类 16。前端 `cleanCardFields()` **优先读 profile**、正则兜底。**必须用完整 role 原串**（`_roleRaw`，`clean_role()` 会截断失真）。
- **人物卡**：卡背「书内语录」（**66 人**，全部原文核实）；搜索命中姓名**或别名**（`aliasIndex` 444）。
- **洞察联动**：构建期 `core/insight_link.py` 出 `insightIndex`（正向 `sections{sid:{p,l,e}}` + 反向 `byPerson/byPlace/byEvent` + `alias/placeAlias/titles`）；渲染期 `linkifyInsight()` **只改文本节点**（TreeWalker+SHOW_TEXT，跳过 `a/button/script/style/code`），不碰标签属性。命中：人物 207 次/97 人、地点 92/57、事件 17/14。`GENERIC_BLOCK` 滤通称，绰号与庙号保留。**正向存的是「表面形式」，反查必须先过 `alias`/`placeAlias` 归一**。
- **地点别称分级**：`core/place_mentions.py` 把 `mentionedAs` 拆成 `altNames`（真别称 142）+ `mentionContext`（说明片段 1235）；`mentionedAs` **原样保留**（深链 `?place=` 与列表搜索依赖它）。规则=形状约束（2~8 字、无标点、以地名尾字收尾）+ 排除（描述词/其他实体名/「今」开头）；**判不准一律归 context，只换标题不丢数据**。
- **地图**：Leaflet 懒加载 + 首屏空闲后台预热（**用户明确要求，勿改成仅 hover**）+ hover/touchstart 即时预热；瓦片 Esri 主源 + `tileerror≥6` 回退 OSM；SW 只拦同源、`cache:'no-cache'`、后台更新 `event.waitUntil` 保活。**CACHE `ming-report-v9`**。
- **统一错误 UI**：`failBar(key,msg,{level})/dismissFail()/reportRuntimeError()`；5 类接入（数据缺失/主脚本未初始化/渲染异常/Leaflet 失败/瓦片全失败）。**启动守卫是独立 `<script>` 且排在主脚本之前**（主脚本解析失败时它仍能跑）；`app.js` **禁止静默空 catch**（有测试断言），**点击交互找不到目标也必须给 `failBar` 反馈**（别静默 return）。
- **URL deep link**：`#view=&person=&detail=1&event=&place=&era=&map=&q=&net=&from=&to=`；`person=` 支持别名 + 闪烁定位；打开详情写回地址栏；`mark.hl` 高亮；tabs `role=tablist/tab/tabpanel` + 方向键；canvas/热力图/网络 SVG 均有 `role="img"` + 描述性 `aria-label`。

## 方法学与发布纪律
- **写作**：不硬凑字数；观点挂文献且必须核实；书内情节/语录**必须先在原书 txt 命中原文**（0 命中即弃用）。「宁可留空不可猜错」。
- **版权硬约束**：`明朝那些事儿.txt` 与 `data/chapters.json` **绝不发布**（换电脑私拷）。历史 commit `7190215d` 仍含该 blob，用户明确「不用管了」。发布后必跑巡检：`gh api "/repos/CochraneK/ming/git/trees/main?recursive=1" --jq '.tree[]|select(.type=="blob")|.path' | grep -Ei 'chapters\.json|明朝那些事儿'`，期望无输出。
- **发布**：`.dump/_sync_docs.py` 是**超集**（FILES 已含 index.html/sw.js/README.md，走 `POST /git/blobs`，无 1MB 限制）→ **只跑它即可完成发布**（`MING_SYNC_MESSAGE=` 可覆盖）。`_deploy_index_now.py` 仅作「只改前端」轻量通道，重复跑只多一个空提交。**新增文件必须补 FILES 清单**。差异检查 `_diff_remote.py`（期望「过时 0」）。**发布后体检 `.dump/_post_publish_check.py`**：合规巡检（线上文件树）+ 线上产物逐字节 sha1 核对 + 解出 `CACHE` 名 + CI 结论，一条命令跑完。
  - **核验线上必须绕 CDN**：Pages 边缘 `max-age=600`，**不要用固定查询串**（会被按该 URL 缓存住），用**时间戳 cache-buster** 或读 `raw.githubusercontent.com/<owner>/<repo>/main/<path>`。SW 更新检查本身绕过 HTTP 缓存，别据此误判。
  - **记忆/skill 文档也在发布清单里** → 先写完文档再同步，否则 `_diff_remote.py` 立刻又报「过时」。
- **前端验真**：断言**必须正则匹配渲染标签**（产物内联 JS，裸串会假通过）；`--dump-dom` 把布尔属性序列化成 `key=""`；属性顺序不可假设（`id="x"[^>]*value="…"`）；区分「渲染出来」与「源码里写着」用 `scoped`；兜底路径注入语法错误副本验证。
- **增量勘误层**（重跑 merge 不丢）：`manual_corrections.json` / `manual_lifespans.json` / `manual_persons.json` / `derived_chapter_persons.json` / `event_places.json`（注入须在归一化循环**之前**）/ `geo_annotations.json` / `manual_event_years.json`。
- **同名异地两级拆分**（`merge.py`）：`location_splits`（键=**原始地点串**）+ `location_splits_by_chapter`（键=**章节 key**）。判据必须落在「章节」或「原始串」上（两处同名地点的片段名本来就相同）。**两处 splits 必须在地点归一化循环之前加载**，归一化后才走 `location_fixes`/geo 坐标。已拆：延安府（陕西/朝鲜）、龙山（浙江/朝鲜）。
- **补年两级**：空 `year` → `manual_event_years.json`（**只回填**）；非空但不可解析（「万历末年」）→ `manual_corrections.event_years`（**覆盖式**）。

## 踩坑速查（都是本项目实际栽过的）
- **`window.DATA` 恒 undefined**：`DATA` 是脚本作用域 `const`，不是 window 属性；写 `window.DATA` **不抛错**，表现为「新功能静默失效、0 个节点」。**一律用裸标识符** `typeof DATA!=='undefined' && DATA.x`。
- **骨架（含注释）里绝不书写数据占位符名**：字符串替换会把 payload 注入两遍（实测 5.6→11.4 MB）。改注入代码后跑 `doc.count('"scopeLabel"')==1`。
- **`data/chapters.json` 是 list（168 条）不是 dict**：`isinstance(...,dict)` 分支写错会**静默返回 0 条**（已栽两次）→ 一律 `else [(str(i),c) for i,c in enumerate(chapters)]` 并先 `print(type(),len())`。
- **正文含 `\n`，中间产物不能用 TSV**（会被撑裂，假象「只新增 2 条」）→ 抽完就地合并或存 JSON。
- **统计「恒 0/恒真」自查**：`"person" not in (a, b, "person")` 这类条件永假；写完条件先问「有没有可能恒真/恒假」。
- **Chrome `--dump-dom` 偶发返回 0 字符**（同场景第一次挂、重跑就过）→ `_browser_check.py` 已内置**空结果重试 3 次**。别把这种噪声当真回归。
- **Bash PATH 被裁**（`ls`/`tail`/`dirname`/`env`/`rm`/`head`/`grep` 消失）→ 外部程序**一律绝对路径**（python `C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe`、node `…/node/versions/22.22.2-3/node.exe`、Chrome），列目录用 `os.listdir`，管线过滤用 Python。
- **Bash 会把反引号与 `${}` 当命令替换**（`Bad substitution` / `command not found`）→ 长脚本、含反引号的文本**一律写成 `.py` 文件执行**，别塞进 `python -c "…"`。
- **编辑工具偶发「报成功但没落盘」** → 改完复核。CSS 单行模板查 `count('{')-count('}')`；改 JS 后 `node --check web/js/app.js`；`load_json()` 只收 Path；`Path.as_uri()` 需绝对路径；`.dump/` 必发脚本记得进 FILES。
- **召回探测**：`src/discover_persons.py` 三信号，用 merge 后规范名口径（别名未归一是伪影）。

## 方案落地终态（`report/Ming_重构验收清单.md`）
- **25 项：✅23 / 🟡1（P2-02 `from`/`to` 保留显示名是有意决策）/ ⏸1（P2-09 `.workbuddy/memory` 有意入库做接续指南）**。**方案项已全部闭环，不要再当 TODO 找**；唯一「不必做」是移动端详情抽屉（dialog 已自适应）。
- 量化：构建 109.7s→≈2s；单文件 11.39MB→5.27MB（−54%）；测试 0→55；validators 10→12 组；浏览器自检 0→14 场景。

## 剩余待办（内容层，低优先）
1. **未定位地点 30 个**：多为漠北蒙古草原地名（15 世纪定位困难且有争议），按纪律不动；`车迟国` 已标 `status:"非实地"`。
2. **未知年份事件 2 件**：「严世蕃论天下三人」「朱棣生母碽妃之谜」，无可靠纪年，有意保留。
3. **数据清洁**：端点别名归一（`aliasIndex` 11 条自引用、2 条跨名冲突）、张瑾→张軏方向。44.3% 无人物间关系者**不建议强补**。
4. **有意不做的压缩**（别当 TODO）：`relations[].endpointKind`/`sourceId/targetId` 可推导（≈3%）；`characters[].relations` **不是** `DATA.relations` 的纯投影（168/1231 人卡上更少，是设计子集），**不能改客户端推导**。
5. `R-REIGN-01` 3 处年号重叠（1457/1567/1620）已确认史实，现报 INFO——无需处理。

## 伪遗留（勿再当 bug 排查）
- `data/chapters_index.json`（**线上独有**，≈40 KB，仅分部/章标题/键名，无正文）是自 2026-08-26 起**有意发布**的脱敏目录替代品；`_diff_remote.py` 已白名单放行，合规巡检过滤串故意不匹配它。
- `R-GEO-04` 93 条「旧称」= 应天→南京、濠州→凤阳、平江→苏州…已由 `mentioned_as` 合并；判 stale 必须**先查原名再查别名**。
- 「明朝·福建进士」类无年份表述，`jinshi_year` 为空是**正确**的。
- `renderPrint` 游离反引号已根治；OmniRoute 重抽已放弃（用户明确）。

## 历史明细
逐日见 `.workbuddy/memory/YYYY-MM-DD.md`；重点：`2026-09-13.md`（一~六轮：Phase 1+2 → Phase 3~6 + CI green → 方案逐条验收 → 剩余项补齐 + 体积 −55% → 线上一致性复核 → 同名异地/补年/考据）、`2026-09-14.md`（语录扩面 + 洞察联动上线 + **自查轮修 6 项**）、`2026-08-28.md`（交叉审计）、`2026-09-04.md`（洞察终版/地图）。

## 论文试点（aris 流程，2026-10-01 收口）
- **TeX 已落地**：`E:\tex\tectonic.exe`（0.17 单文件，XeTeX，联网拉包）；参数 `--keep-logs`、`--outdir` 须先建目录。中文 ctex 编译通。
- **中文论文必须 `\setCJKmainfont{STSong}`**：ctex 默认 FandolSong **缺「濙」U+6FD9 等字**（PDF 出方框）；`NotoSerifSC-VF.ttf` 是可变字体，xdvipdfmx 以 `Invalid TTC index` 拒收，勿用。缺字自查 = 扫编译 log 的 `could not represent character`。
- **试点 venue = IEEEtran.cls [conference]**（aris 自带模板里唯一双栏+数字引用+参考文献计页数），中英双语（正文中文/摘要英文）。试点成品：`papers_pilot/history/`（PAPER_PLAN.md / AUDIT.md / paper/ 7 节 + 3 矢量图 + references.bib / out/main.pdf，6 页编译全绿）。
- **口径坑（每篇复用）**：`relations[].from/to` 存**裸人物名**不是 `person:名字`；`characters[]` **无 id**；叙事热度 = `len(characters[].chapters)`。按 `person:` 前缀查会得 ρ=0.00。
- **统计底稿的 `min(v,10)` 截断桶坑**：桶键被截断（如 10）却标成「恰为 10」，会造「143 人」假象（真值 7）。截断必须改名或另立 `geN` 汇总桶。
- **数页数**：tectonic log 不打页数、PDF 对象流全 Flate 压缩 → 用 `zlib` 解流后取 `/Count N` 或数 `/Type/Page`（`papers_pilot/_build.py` 已实现）。
- **边界（每次交付须声明）**：tectonic ≠ aris 的 latexmk+pdflatex；同模型自审 ≠ aris 跨模型对抗评审。

## papers_pilot（论文子项目，独立于本站构建）
- **产物**：`papers_pilot/<pid>/paper/`（main.tex + sections/ + figures/ + out/main.pdf）；25 个候选目录里**真 pid = 24 个**（判据：目录里真有 `paper/main.tex`，且不是 `_bak_*`/quarantine/snapshot——据此排掉空壳 `d/2026/WB项目/paper`、PNG 预览页 `首页预览`/`paper_preview`）。
- **两道闸**：闸 1 `check_all.py` → 逐篇 `check_one.py --strict`（编译 + 章节 7 / 图 ≥2 / 脚本 ≥2 / 引用 ≥6 / 汉字 ≥3000 / 页数 1–8 / 悬空 `\ref` / 裸回车 / 哨兵残留 / lint_spec）；闸 2 `cross_check_all.py` → 两两 4-gram Jaccard < 0.45、作图脚本 md5 跨篇不复用、引用池区分度。**闸 2 的 PIDS 必须动态扫（曾写死 19 篇漏盖 5 篇）。**
- **去样板化工具**：`papers_pilot/_lib/dup_blocks.py <pid> [--min 25] [--show N]` → 对手 top6 + 本篇被逐字覆盖的连续块（带前后文）。
- **雷同根因**：`_lib/write_generic.py` 里 §1 开场+边界、§3 语料与口径、§4 贡献三点、§6/§7 收束是**写死样板**，凡是有 `_lib/spec_<pid>.py` 的通用 pid（art/diplomacy/economics/gender/geography/military/museum/narrative/systems）全篇逐字相同；手写型 pid（politics/psychology/history/ideology/sociology/law/science/info/synthesis/anthropology/sovereign 等）天然干净。
- **派单铁律**：一个 pid 只有一个 owner；`_lib/` 公共文件（write_generic / check_one / build_one / gen_stats）由 lead 独占，**禁止** worker 改；**严禁用 `write_generic.py --generic`**（会整体重写 `.dump/_stats_<pid>.json` 毁底稿）；`gen_stats.py` 与 `_stats.py` 抢同一个 `.dump/_stats_<pid>.json` 槽位，谁后跑谁赢 → 必须**合并**（通用为骨架、专用键只补缺失），不能二选一。
- **`.py` 里的正文串一律 raw**（`r"""`）：非 raw 串里的 `\r` `\t` 会被 Python 吃掉变真控制字符，把正文改坏（museum 曾出现 `图 \refef` 乱码）。
- **判裸回车必须是 `re.search(r"\r(?!\n)", t)`**：Windows .tex 本来就是 CRLF，裸判 `"\r" in t` 全库假报错。
- **`lint_spec.py` 已进程内接进 `check_one.py --strict`**（`import lint_spec` → FAIL 计入退出码、WARN 只打印）。
- **`check_one.py` 判据 11：正文 cite key ⊆ `references.bib` 的 key 集合。** natbib 对未定义 bibkey **不报** undefined citation（只静默出 `[?]`），所以 und_cit 抓不到——全库唯一一例是 sovereign 的 `freeman1979`（bib 只有 `freeman1978`，中心性三定义出自 1978 那篇，DOI 10.1016/0378-8733(78)90021-7）。
- **剥 LaTeX 注释只能认「前面不是反斜杠的 %」**：`re.sub(r"(?s)%.*?\n","",t)` 会被正文里的**裸 `%`** 骗到，吃掉真内容（我据此误报过「9 篇摘要越界」，真值 4 篇）。
