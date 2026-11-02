---
name: fanqie-novel-scrape
description: >
  番茄小说（fanqienovel.com）抓取 + 字体反混淆 + 接入 book-meal 书库的完整 skill。
  覆盖目录 API 批量取章、PUA 私用区乱码还原（woff2 子集字形比对）、付费章边界处理、
  断点续传、抓后质检、books/<slug>/manifest.json 生成。
  在以下场景务必使用：用户说"抓番茄""番茄小说下载""fanqie""把这本书抓下来"
  "PUA 乱码""正文是方块/乱码""字体反混淆""woff2 解不出来""续抓""只抓免费章"
  "接进书库""生成 manifest"，或给出 fanqienovel.com 链接要求落地成文本 / 书库条目。
version: 1.0.0
agent_created: true
allowed-tools: Bash,Read,Write,Edit,Grep,Glob
---

# 番茄小说抓取与字体反混淆

把 fanqienovel.com 的章节抓成本地 UTF-8 文本，并接进 book-meal 书库
（正文留 `data/<id>/`，书目名片进 `books/<id>/manifest.json`）。

**这份文档的价值集中在两处**：① 正文是 PUA 乱码，必须靠字形比对还原（第 3 节，含三个致命坑）；
② 番茄有付费墙，脚本只在合法边界内工作（第 4 节，先读再动手）。

---

## 0. 最短路径

```bash
PY="C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe"
REPO="D:/2026/WB项目/book-meal"
cd "$REPO/.workbuddy/skills/fanqie-novel-scrape/scripts"

# ① 先看目录，确认免费章有多少
$PY fanqie.py --book 7143038691944959011 --out /tmp/t --toc-only

# ② 试抓 5 章，确认解码通顺
$PY fanqie.py --book 7143038691944959011 --out /tmp/t --limit 5

# ③ 正式抓 → 落 data/<id>/（已 gitignore，不入库）
$PY fanqie.py --book 7143038691944959011 --out "$REPO/data/riye"

# ④ 质检
$PY qa.py "$REPO/data/riye"

# ⑤ 登记进书库（只写 manifest，不搬正文）
$PY make_manifest.py "$REPO/data/riye" --slug riye --repo "$REPO"
```

`--book` 接受三种写法：纯 book_id、`/page/<id>` 链接、`/reader/<itemId>?bookId=<id>` 链接。

> **版权红线**：本仓 `tests/check_copyright.py` 会拦下任何入库的原书正文
> （名单 / >200 KB 的 .txt / 单个字符串 >8000 字的 json / `data/` 下的 txt）。
> 所以正文只能待 `data/<id>/`，`books/<id>/` 只放脱敏报告 + manifest。
> `make_manifest.py` 遇到 `--out` 在 `books/` 下会直接报错退出。

---

## 1. 运行环境（Windows 沙箱硬约束）

| 项 | 值 |
|---|---|
| Python | `C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe`（**别用系统 `python`**） |
| 依赖 | `fonttools`、`numpy`（其余全是标准库）；缺了跑 `$PY -m pip install fonttools numpy` |
| 路径 | 用 `D:/...` / `C:/...` 正斜杠绝对路径；Windows 原生 Python 不认 `/d/` |
| 网络 | 番茄**可直连**，不需要代理（这点与 cn.zhys.tw 那类 Cloudflare 站完全不同） |
| 编码 | 抓取全程 UTF-8；输出无 BOM |

已验证：本机 `fontTools 4.62.1` + `numpy` + `Noto Sans SC (TrueType).otf` 可用。

---

## 2. 站点结构（三个稳定入口）

| 用途 | 请求 | 说明 |
|---|---|---|
| 目录（全量） | `GET /api/reader/directory/detail?bookId=<bid>` | 返回 `data.chapterListWithVolume`（二维：卷 → 章），含 `itemId`、`title`、`volume_name`、`isChapterLock`。**这是唯一可靠的枚举方式** |
| 书籍元数据 | `GET /page/<bid>` | 书名 `info-name > h1`、作者 `author-name-text`、简介 `page-abstract-content`、标签 `info-label-grey`、状态 `info-label-yellow` |
| 正文 | `GET /reader/<itemId>` | 正文在 `div.muye-reader-content.noselect` 的 `<p>` 里；标题在 `h1.muye-reader-title` |

**不要**从目录页 `<a href="/reader/...">` 枚举章节——页面只渲染前若干章，拿不全（本书 1496 章，页面只给十几条）。

`needPay` 在这本书里全是 0，**不能**拿它判断付费；真正有效的是 `isChapterLock`。

---

## 3. 字体反混淆（核心）

### 3.1 现象

正文 HTML 里是 `U+E000–U+F8FF` 私用区字符，复制出来是空白/方块。页面同时挂一个 woff2：

```
https://lf6-awef.bytetos.com/obj/awesome-font/c/dc027189e0ba4cd.woff2
```

本书全书**共用同一份字体**（抽查第 1/2/51/501/1496 章，URL 完全一致），所以解一次即可整本复用。

### 3.2 原理

1. 该 woff2 是 `SourceHanSansSC-Normal` 的**子集**，glyph name 形如 `gid58345`——**原始 glyph id 被保留**。
2. 把每个 PUA 字形按 nonzero winding 栅格化成 40×40 位图。
3. 与本机静态 **Noto Sans SC Regular**（与思源黑体同源同字重）的 GB2312 常用字位图做 IoU 比对。
4. 取 IoU 最高者，并记录与第二名的 `margin` 作置信度；阈值 `IoU≥0.55 且 margin≥0.04`。
5. 缓存 `gid → 汉字`。**gid 稳定、PUA 分配才会变**，所以缓存跨书也能复用。

实测（362 个 PUA）：**357 命中**，5 个低置信（都是 `Q/i/y` 这类拉丁字母的近似字形），解码后残留 **0**。

### 3.3 三个致命坑（改代码前必读）

| 坑 | 错法 | 后果 | 正解 |
|---|---|---|---|
| **参考字体用了可变字体** | `NotoSansSC-VF.ttf` | 默认实例是 `wght=100`(Thin)，笔画细一半 | 必须用**静态 Regular**：`Noto Sans SC (TrueType).otf`；无本机字体时脚本自动从 jsDelivr 拉 `noto-cjk/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf`（8.3 MB） |
| **用 PIL `polygon` 逐轮廓填充** | `ImageDraw.polygon` 每 contour 填一次 | 「口」「日」内腔被填实，IoU 掉到 0.5，全盘皆错 | 自己写 **nonzero winding 扫描线**（`rasterize()`），方向符号累加才能留空 |
| **比对 contour 数 / 节点数** | 以为同字结构一致 | 番茄把多个部件合并成 1–2 条路径，Noto 是 6 条，直接误判 | 只比位图 IoU，不比结构 |

另外别用 `margin` 之外的信息做二次过滤——低置信项基本只出现在拉丁字母上，不影响中文正文。

---

## 4. 付费边界（先读，别绕）

番茄的 `isChapterLock=1` 是 **VIP 章**。未登录时 `/reader/<itemId>` 仍返回 200，但正文容器里**只有几百字试读**，后面跟一条「登录 / 购买」提示。实测第 11 章只有 37 字，第 754 章 161 字，而正常章节约 2278 字。

这不是技术问题，是商业边界。脚本的处理方式：

- **默认**：只抓免费章；VIP 章跳过，并在 `meta.jsonl` 标 `status: "vip_skipped"`。
- **合法路径**：用**你自己账号**的 Cookie 抓**你已购买**的章节：

```bash
$PY fanqie.py --book <bid> --out books/xxx --vip --cookie-file cookie.txt
```

Cookie 从浏览器开发者工具复制（`document.cookie` 或 Network → 请求头 `Cookie`），存成一行文本。

- **不要**添加任何绕过付费墙的机制（伪造 token、破解接口、共享账号池）。技能里明确拒绝这类改造请求。
- `looks_preview()` 会二次校验：如果页面同时出现「VIP」和「购买」且正文 < 700 字，判为 `preview`，**不落盘**——防止把试读片段当整章写进语料。

---

## 5. 产出结构

```
<out>/
  chapters/0001.txt        # 每章：第 1 行标题，空行，正文
  <书名>.txt               # 合并全本（书头 + 各章）
  meta.jsonl               # 每章一行：n/item_id/title/volume/need_pay/vip/status/chars
  meta.json                # 书籍级：title/author/abstract/tags/status/chapters/volumes/stats
  .cache/gidmap.json       # gid→汉字 缓存（跨书复用）
  .cache/*.woff2           # 混淆字体原件
```

`<out>` 建议直接指向 `book-meal/data/<id>/`（该目录下 txt 已 gitignore）。
书库名片 `manifest.json` 由 `make_manifest.py` 另写到 `books/<id>/`，**不在这里**。

`status` 取值：`ok` / `preview` / `vip_skipped` / `missing`。**以磁盘文件为准回写**，所以续传后统计仍然准确。

---

## 6. 参数表

| 参数 | 默认 | 说明 |
|---|---|---|
| `--book` | 必填 | book_id 或任意番茄链接 |
| `--out` | `.` | 输出目录 |
| `--start` / `--end` | 1 / 末章 | 章节区间（1-based，含两端） |
| `--limit` | 0 | 只抓前 N 章，试跑用 |
| `--workers` | 3 | 并发。**别超过 4**，会触发风控 |
| `--delay` | 0.25 | 每请求后基础延迟（实际再叠加 0–0.25 随机抖动） |
| `--force` | 关 | 已存在也重抓 |
| `--toc-only` | 关 | 只导目录 |
| `--vip` | 关 | 尝试 VIP 章，**必须**配 `--cookie`/`--cookie-file` |
| `--cookie` / `--cookie-file` | 空 | 你自己的登录凭据 |

---

## 7. 质检

```bash
$PY qa.py "data/riye" --min 300
$PY qa.py "data/riye" --strict     # 整本抓完后用，缺章也算失败
```

检查：章节文件数、正文总字数与分布、**PUA 残留必须为 0**、标题行是否齐备、`meta.jsonl` 状态分布、缺章清单。

判定分级（避免试抓时误报）：
- PUA 残留 → **失败**
- 偏短章节占比 >20% → **失败**（系统性截断，通常是撞付费墙或选择器失效）
- 零星偏短章、缺标题、缺章 → 只提示；`--strict` 才升级为失败

全绿退出码 0，有问题退 1。

经验阈值：正常章节 2000–2500 字。若均值掉到几百字，八成是遇到了付费墙或容器选择器失效，不是书本身短。

---

## 8. 接入 book-meal 书库

**分工**：正文进 `data/<id>/`（gitignore，不入库）；只有**脱敏报告**和**书目名片**进 `books/<id>/`。

```bash
# ① 抓取直接落到 data/<id>/
$PY fanqie.py --book <bid> --out "$REPO/data/riye"

# ② 写 books/<id>/manifest.json（order 自动取最大值+1，不复制正文）
$PY make_manifest.py "$REPO/data/riye" --slug riye --repo "$REPO" --kind fictional_world
```

manifest 字段：`id/title/author/kind/desc/accent/metrics/chapters/fetched_chapters/report/updated/order/glyph/subtitle/note/external`。

- `chapters` = 全书总章数（目录 API 给的），`fetched_chapters` = 实际落盘数——付费书两者会不等，别混。
- `metrics` 先留 0，等拆书流水线跑完再回填（口径纪律见 `docs/add_a_book.md` 第六节）。
- `accent` 按书名哈希稳定取色（深色书封色域），`glyph` 取书名首个实义词字。
- `kind` 取值：`history` / `modern_real` / `fictional_world` / `humanities` / `other`。

之后按 `docs/add_a_book.md` 走：产出 `books/<id>/index.html` → `python src/build_hub.py` → 提交。
**不要**把 `data/<id>/chapters/`、合并 TXT、`chapters.json` 提交上去——CI 版权巡检会拦。

---

## 9. 故障排查

| 症状 | 原因 | 处置 |
|---|---|---|
| 正文是空白/方块/复制出来没字 | PUA 未解码 | 确认 `.cache/*.woff2` 存在；`ensure_decoder` 是否拿到 `pua_map` |
| 解码后仍有少量怪字 | 低置信项（多为拉丁字母） | 正常，占比 <2%；肉眼核对不影响语义 |
| `找不到参考中文字体` | 本机无静态 Noto | 允许联网自动下载，或把 `NotoSansSC-Regular.otf` 放到 `assets/` |
| 章节均值只有几百字 | 撞上付费墙 / 选择器变了 | 看 `meta.jsonl` 的 `status`；若为 `preview` 说明是 VIP 章 |
| 抓一半断了 | 网络/风控 | 直接重跑同一条命令，自动跳过已有章 |
| `fetch failed ... 403` | 风控或需要登录 | 降 `--workers` 到 1、加 `--delay 0.8`；必要时带 Cookie |
| `Int(directory)` 报错 / 章节数不对 | 用了目录页枚举 | 改回 `directory/detail` API |

---

## 10. 实测基线（2026-11-02，书《十日终焉》1496 章）

- 目录：1 次请求拿全 1496 章 / 10 卷，约 1 秒
- 字体：362 PUA → 357 高置信，比对耗时约 3 秒（首次），之后走缓存
- 正文：免费前 10 章全部抓取，合计 22,785 字，均值 2,278 字/章，PUA 残留 0
- 建议：整本抓取前先 `--toc-only` 看免费章比例，避免白跑付费书

---

## 11. 与其它抓取 skill 的分工

| 站点类型 | 用哪个 | 关键差异 |
|---|---|---|
| 番茄 fanqienovel.com | **本 skill** | 直连；难点是 PUA 字体混淆 |
| 带 Cloudflare 的盗版/聚合站（如 cn.zhys.tw） | `novel-cloudflare-scrape` | 需真实浏览器 + 住宅代理；难点是绕过 JS 挑战 |

两者产出的目录结构一致（`chapters/NNNN.txt` + 合并 TXT），所以下游拆书流水线可以共用。
