# -*- coding: utf-8 -*-
"""让 README 的公开规模口径与最终模型 / 当前交付架构保持一致。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_report as G  # noqa: E402

README = BASE / "README.md"
QUOTES = BASE / "data" / "character_quotes.json"


def _replace_one(text: str, pattern: str, replacement: str, label: str) -> str:
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit("README 同步锚点异常（%s）：匹配 %d 处" % (label, count))
    return new


def _quote_count() -> int:
    with QUOTES.open(encoding="utf-8") as f:
        data = json.load(f)
    return sum(1 for key, value in data.items() if not str(key).startswith("_") and str(value).strip())


def render_readme(source: str) -> str:
    model = G.build_scope("full")
    m = model["metrics"]
    chapters = int(m["chapters"]);locations = int(m["locations"]);located = int(m["locatedLocations"])
    events = int(m["events"]);timed = int(m["timedEvents"]);unknown = int(m["unknownEvents"])
    characters = int(m["characters"]);relations = int(m["relations"])
    unlocated = locations - located;located_pct = 100.0 * located / max(locations, 1);quotes = _quote_count()

    text = source
    rows = {
        "来源章节": "| 来源章节 | %d | 七部全部章节，抽取覆盖 100%% |" % chapters,
        "地点": "| 地点 | %d（已定位 %d，%.1f%%） | 未定位的 %d 个如实标为「待核验」，不硬填坐标 |" % (locations, located, located_pct, unlocated),
        "人物": "| 人物 | %d | 含出场章节、别名、势力、身份 |" % characters,
        "事件": "| 事件 | %d（有年份 %d） | 未知年份 %d 件单独保留，不混入历史顺序 |" % (events, timed, unknown),
        "关系": "| 关系 | %d | 含亲属、政治、军事、派系等类别 |" % relations,
    }
    for label, line in rows.items():
        text = _replace_one(text, r"^\| %s \|.*$" % re.escape(label), line, "规模表/%s" % label)

    nav = (
        "**全局叙事**：`总览` `分布` `时间轴` `帝王` `年谱`　·　"
        "**实体索引**：`人物` `地点` `事件` `关系`　·　"
        "**探索分析**：`图谱` `地图` `洞察`"
    )
    text = _replace_one(text, r"^(?:`总览` .*`洞察`|\*\*全局叙事\*\*：.*)$", nav, "V2 导航摘要")
    if "<!-- README_V2_JOURNEYS -->" not in text:
        text = text.replace(nav + "\n", nav + "\n\n<!-- README_V2_JOURNEYS -->\n> V2 首页另提供三条问题导向的探索路径：**人物脉络**、**时间脉络**、**空间与结构**；顶部导航与深链仍使用原有 12 个 view id。\n", 1)

    text = _replace_one(text, r"^- \*\*地点\*\*：\d+ 张地点卡", "- **地点**：%d 张地点卡" % locations, "地点视图数量")
    text = _replace_one(text, r"（\d+ 位(?:核心)?人物的语录均经原文核实，见 `data/character_quotes\.json`）", "（%d 位人物的语录均经原文核实，见 `data/character_quotes.json`）" % quotes, "人物语录覆盖")

    text = re.sub(
        r"^基于《明朝那些事儿》七部 156 章全文抽取整理的.*$",
        "基于《明朝那些事儿》七部 156 章全文抽取整理的静态知识库，报告位于 `/ming/`。本仓库整体是**多书拆解聚合平台**：根路径为书库门户（`src/build_hub.py` 扫 `books/*/manifest.json` 生成），每本书一份自包含报告置于 `books/<id>/`；新增书籍只需放入目录并附一份 `manifest.json`，无需改动平台代码（见 `docs/add_a_book.md`）。",
        text, count=1, flags=re.MULTILINE,
    )
    text = _replace_one(text, r"^GitHub Pages：.*$", "GitHub Pages：`https://cochranek.github.io/ming/`——根 `/` 为书库门户；`/ming/` 为本书报告（分层版）；`/standalone.html` 为本书可下载 / 双击打开的完整离线版", "在线入口")
    text = text.replace("python src/build.py                 # 构建全书单文件 index.html", "python src/build.py                 # 构建全书单文件 standalone.html")
    text = re.sub(
        r"^\| `--target standalone\\\|web` \|.*$",
        "| `--target standalone\\|web` | 默认 `standalone`＝CSS/JS/DATA 全内联到 `standalone.html`；`web`＝输出分层骨架与 `assets/`，由发布流程落到 `ming/`。门户根 `index.html` 不由本脚本产生，而由 `src/build_hub.py` 扫 `books/*/manifest.json` 生成 |",
        text, count=1, flags=re.MULTILINE,
    )
    text = re.sub(
        r"^`standalone` 构建.*$",
        "`standalone` 构建内联完整最终 DATA 为单文件；`web` 构建产出分层骨架 + `assets/`（`app.css` / `app.js` / 单体 `data.js`），由发布同步工作流落到 `ming/` 下。门户与各书报告的聚合关系见 `docs/add_a_book.md`。",
        text, count=1, flags=re.MULTILINE,
    )

    marker = "<!-- README_STATS_SYNC -->"
    note = "> 上表的章节 / 地点 / 人物 / 事件 / 关系统计由 `src/sync_readme.py` 从最终模型自动刷新；发布同步工作流会同时维护书库门户（根 `index.html`）、`ming/` 分层版与 `standalone.html` 离线版。"
    if marker not in text:
        anchor = "| 年谱 | 165 人 | 主要人物生卒横向展开，与年号对位 |\n"
        if anchor not in text: raise SystemExit("README 同步锚点异常（规模表尾部）")
        text = text.replace(anchor, anchor + "\n" + marker + "\n" + note + "\n", 1)
    else:
        text = _replace_one(text, r"^> 上表的章节 / 地点 / 人物 / 事件 / 关系统计由 `src/sync_readme\.py`.*$", note, "V10 发布说明")
    return text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="同步 README 中的最终模型统计与交付说明")
    parser.add_argument("--check", action="store_true", help="只检查 README 是否已同步")
    args = parser.parse_args(argv)
    source = README.read_text(encoding="utf-8");updated = render_readme(source)
    if updated == source:
        print("README 已与最终模型和 V10 交付架构一致");return 0
    if args.check:
        print("README 与最终模型或 V10 交付架构不一致；请运行 python src/sync_readme.py", file=sys.stderr);return 1
    README.write_text(updated, encoding="utf-8")
    print("README 已同步：%d → %d 字符" % (len(source), len(updated)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
