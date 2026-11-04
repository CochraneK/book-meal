# 新增一本书（runbook）

本仓库是**多书拆解聚合平台**。新增一本书不需要改平台代码、不需要改 CI——
平台只认 `books/<id>/manifest.json` 这一份「书目名片」。书单的单一真源是
`src/book_registry.py`：门户书卡、README 书单表、各报告顶部的书库导航条都从这里读，
因此新增一本只需放 manifest，三处自动同步。

## 端到端流水线（标准顺序）

```
抓取源文本 → 分章 → 逐章抽取五元组 → 聚合 → 质量校验 → 主题皮肤 → 报告构建
→ 登记 manifest → 门户重建 → 导航条注入 → 交付断言 → 提交发布
```

| 阶段 | 落点 | 命令 / 工具 |
|---|---|---|
| 抓取 + 字体反混淆 | `data/<id>/`（不入版本控制） | `.workbuddy/skills/fanqie-novel-scrape/scripts/fanqie.py`、`font_deobf.py`、`qa.py`、`make_manifest.py` |
| 分章 | `teardown/data/<id>/chapters.json` | `teardown/src/split_chapters.py` |
| 抽取 | `extract_raw.json` | 用户级 skill `book-teardown-pipeline` 六阶段流水线 |
| 聚合 | `data.json` | `teardown/src/merge.py` |
| 校验 | — | `teardown/src/quality_checkup.py` + `verify_*.py` + `pytest tests -q` |
| 主题皮肤 | `teardown/web/css/theme-<id>.css` | 书影工坊 SOP；按书气质换肤 + 母题 + 局部重构 |
| 报告 | `teardown/out/<id>.html` | `teardown/src/generate_report.py` / `build_swdw_report.py` |
| 发布同步 | `books/<id>/index.html` | `teardown/src/publish_books.py <id>`（会自动注入导航条） |
| 门户 + 导航条 | `index.html` 与 6 份报告 | `python src/build_hub.py` → `python src/sync_shelf.py` |
| 交付断言 | — | `python src/check_delivery.py`、`python src/sync_shelf.py --check` |
| README | `README.md` | `python src/sync_readme.py`（勿手改） |

> 顺序里最容易漏的是 **`sync_shelf.py` 必须排在所有会重写报告产物的命令之后**。
> 导航条是发布层生成装饰，重建 `standalone.html` / `ming/` / `books/` 会覆盖它；
> 漏跑时 `python src/sync_shelf.py --check` 与 CI 的「书库导航条一致性」会直接报红。

> **源文本从哪来**：番茄（fanqienovel.com）的书用仓内 skill
> `.workbuddy/skills/fanqie-novel-scrape/`——`scripts/fanqie.py` 抓取并还原 PUA 字体混淆，
> 正文落 `data/<id>/`（已 gitignore），`scripts/make_manifest.py` 写书目名片。
> 其它站点（带 Cloudflare 的聚合站）见用户级 skill `novel-cloudflare-scrape`。
> 两者产出一致（`chapters/NNNN.txt`），下游流程通用。

## 一、准备报告产物

把该书的报告做成**单文件离线 HTML**（不引任何 CDN，双击可开），放到：

```
books/<id>/index.html
```

> 本书库对应一份用户级 skill：`book-teardown-pipeline`（六阶段流水线 + 纪律 + 踩坑清单），
> 从「拿到源文本」到「登记进书库」的完整流程见它，本文档只讲本仓的登记步骤。

`<id>` 用小写英文字母 / 数字 / 连字符（如 `tiancai`、`feitu`、`swdw`）。
若报告是「骨架 + 分层资源」形态，则放 `books/<id>/index.html` + `books/<id>/assets/`。

> 版权红线：报告只含**脱敏后的聚合结果**。原书全文（TXT）与含正文的中间产物
> （如 `chapters.json`）**绝不入库**——CI 有版权巡检，命中即失败。

## 二、写 manifest

一键脚手架（建目录 + 拷报告 + 算 order + 写 manifest，来自 `book-teardown-pipeline` skill）：

```bash
python "C:/Users/cunyi/.workbuddy/skills/book-teardown-pipeline/scripts/new_book.py" \
  --hub . --id <id> --title "书名" --author "作者" --kind <kind> \
  --report "D:/…/out/<id>.html" --chapters N
```

手工写也一样，新建 `books/<id>/manifest.json`：

```json
{
  "id": "tiancai",
  "order": 2,
  "title": "天才基本法",
  "subtitle": "奥数·双时间线",
  "author": "长洱",
  "kind": "modern_real",
  "desc": "一句话说明这本书拆解了什么、用什么方法。",
  "accent": "#8c4a2f",
  "metrics": { "characters": 140, "events": 1399, "relations": 482 },
  "chapters": 221,
  "report": "index.html",
  "external": false,
  "updated": "2026-10-20",
  "note": ""
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 必须与目录名一致 |
| `order` | 否 | 卡片排序，小的在前，缺省排最后 |
| `title` / `author` | 是 | 书名 / 作者 |
| `kind` | 是 | `history` / `modern_real` / `fictional_world` / `humanities` / `other`，用于门户类型筛选 |
| `desc` | 否 | 卡片描述，建议一句话说清「拆了什么 + 方法」 |
| `accent` | 否 | 卡片左侧色条，十六进制色 |
| `metrics` | 否 | `characters` / `events` / `relations` 三个计数，进门户总览 |
| `chapters` | 否 | 章数，显示在卡片底部 |
| `report` | 否 | 报告入口，相对 `books/<id>/`，缺省 `index.html` |
| `external` | 否 | `true` 时 `report` 按站外地址处理，卡片打「外链」徽标 |
| `updated` | 否 | 报告更新日期 `YYYY-MM-DD` |
| `note` | 否 | 卡片上的小徽标文字，如「独立报告」 |

## 三、本地生成并验证门户 + 导航条

```bash
python src/book_registry.py         # 确认新书已进入统一书单
python src/build_hub.py --check     # 只校验不落盘（含断链检查）
python src/build_hub.py             # 生成根 index.html
python src/sync_shelf.py --list     # 确认新书报告已被列为注入目标
python src/sync_shelf.py            # 给 6 份报告刷新导航条
python src/sync_shelf.py --check    # 幂等性校验
python src/check_delivery.py        # 交付能力断言
python src/sync_readme.py           # 重建 README（书单表 / 路线图数字）
```

打开根 `index.html` 应看到：新卡片、总览数字已累加、类型筛选 chip 已更新、
搜索「书名」命中 1 本。进入新报告应看到顶部「← 书库 / 书名 / 切换书目 ▾」，
下拉菜单里 6 个入口齐全、当前书高亮。

`sync_shelf.py` 的 `base` 由产物相对仓库根的深度自动算出（`books/<id>/` 是
`../../`，`ming/` 是 `../`，根目录是 `./`），书挪目录不会留下死链；报告用
`file://` 双击打开时，导航链接自动改指线上书库，正文仍完全离线。

## 四、提交并推送

```bash
git add books/<id>/ index.html README.md docs/add_a_book.md
git add standalone.html ming/index.html books/*/index.html   # sync_shelf.py 的回写
git commit -m "feat(books): 新增《书名》拆解报告"
git push
```

推送到 `main` 会触发 `refresh-index.yml`：重建明书分层版与 `standalone.html`、
重跑门户生成、**重放 `sync_shelf.py`**，并在产物确有变化时自动回写一个 commit。
所以第③步在本地跑主要为提前验证；即使漏提交，CI 也会按同一顺序补齐。

## 五、旧深链兼容（仅首次改造时需要注意）

本仓改造前，根路径就是《明朝那些事儿》报告，其深链全部挂在 `#hash` 上。
门户内置一段重定向：带 hash 访问根时自动跳 `ming/<hash>`，既有分享链接不失效。
新书报告若使用 hash 深链，请放在各自的 `books/<id>/` 下，不要占用根 hash。

## 六、指标数字的出处纪律

`metrics` 三个数字必须来自该书自己的数据产物（如 `data.json` 的实体计数），
**不得目测或凭记忆填写**。口径示例：

```bash
python -c "import json;d=json.load(open('data/<id>/data.json',encoding='utf-8'));\
print({k:len(d[k]) for k in ('characters','events','relations')})"
```
