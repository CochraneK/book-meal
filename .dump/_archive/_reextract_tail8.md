# 尾端 8 章高密度重抽（本机执行 · host-only）

> 沙箱（WorkBuddy Bash）无法连通本机 OmniRoute 网关 `localhost:20128`（实测
> `WinError 10061`：沙箱 loopback ≠ 宿主 loopback）。因此本任务**只能在你本机
> 装有 OmniRoute 的电脑上运行**，脚本本体已就绪，照本文件执行即可。

## 为什么做
全 156 章已抽取，但按"抽取密度（抽取条目/正文字数）"排序，尾端 8 章密度最低，
信息偏稀。用 `--dense` 高密度模式重抽这 8 章，可补全被首轮漏抽的人物/事件/关系。

目标章（密度最低 8 章）：
`p1-c17 p1-c22 p1-c28 p4-c11 p6-c12 p5-c2 p4-c4 p4-c15`

## 前置条件（本机）
1. 已安装并正在运行 OmniRoute 桌面版（仪表盘 http://localhost:20128）。
2. 网关里配置了可用的免费模型（`importFreeModelsOnly`）。
3. 确认模型 id（不同版本可能变化）：
   ```bash
   curl http://localhost:20128/v1/models
   ```
   若输出里的模型 id 与 `src/extract_auto.py` 第 43 行附近的 `MODEL` 不一致，
   先改 `extract_auto.py` 的 `MODEL` 为新 id。

## 就绪检查
```bash
# 在明朝项目根目录（D:\2026\WB项目\明朝）执行
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:20128/v1/models').status)"
# 期望输出 200；若报连接错误，说明 OmniRoute 未运行或端口不对
```

## 执行重抽（本机）
```bash
cd D:\2026\WB项目\明朝
python src/extract_auto.py --dense --force p1-c17 p1-c22 p1-c28 p4-c11 p6-c12 p5-c2 p4-c4 p4-c15
```
- `--force` 强制重抽这 8 章（即使已抽过也覆盖）。
- `--dense` 高密度模式：抽取更细，条目更多。
- 脚本会自动合并进 `data/extract_raw.json` 并跑 `merge.py`（见脚本尾部）。

## 重抽后收尾（本机，按顺序）
```bash
python src/merge.py                      # 重新聚合 data.json
python src/generate_report.py --scope full   # 重生根目录 index.html
python .dump/_deploy_reports.py          # 增量发布到 GitHub Pages
```

## 验证
- 打开 https://cochranek.github.io/ming/ ，强刷（GitHub Pages 有缓存）。
- 检查这 8 章相关人物/事件/关系是否更丰富（角色卡"涉及事件"、关系索引）。

## 备注
- 沙箱内部署脚本 `.dump/_deploy_reports.py` 已就绪，本机跑完收尾三步即可发布。
- 不要在本机用 `git push` 推大文件（data.json 已通过 Git Database API 发布）；
  收尾用上面的 `_deploy_reports.py` 即可，与本仓库既有发布机制一致。
