# 新增一本书（runbook）

本仓库是**多书拆解聚合平台**。新增一本书不需要改平台代码、不需要改 CI——
平台只认 `books/<id>/manifest.json` 这一份「书目名片」。

## 一、准备报告产物

把该书的报告做成**单文件离线 HTML**（不引任何 CDN，双击可开），放到：

```
books/<id>/index.html
```

`<id>` 用小写英文字母 / 数字 / 连字符（如 `tiancai`、`feitu`、`swdw`）。
若报告是「骨架 + 分层资源」形态，则放 `books/<id>/index.html` + `books/<id>/assets/`。

> 版权红线：报告只含**脱敏后的聚合结果**。原书全文（TXT）与含正文的中间产物
> （如 `chapters.json`）**绝不入库**——CI 有版权巡检，命中即失败。

## 二、写 manifest

新建 `books/<id>/manifest.json`：

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

## 三、本地生成并验证门户

```bash
python src/build_hub.py --check     # 只校验不落盘
python src/build_hub.py             # 生成根 index.html
```

打开根 `index.html` 应看到：新卡片、总览数字已累加、类型筛选 chip 已更新。

## 四、提交并推送

```bash
git add books/<id>/ src/build_hub.py README.md
git commit -m "feat(books): 新增《书名》拆解报告"
git push
```

推送到 `main` 会触发 `refresh-index.yml`：重建明书分层版与 `standalone.html`、
重跑门户生成，并在产物确有变化时自动回写一个 commit。**门户本身也会被 CI 重新生成**，
所以第③步在本地跑只为提前验证，不必提交它（提交也无妨，CI 会覆盖成同一内容）。

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
