# -*- coding: utf-8 -*-
"""
生成「人物卡语录扩面」人工考据队列（docs/quote_backlog.md）
============================================================
README 路线图里这条待办原先只有 `verify_quotes.py --stats` 的一次性控制台输出：
既不能勾选，也没有「已经核对过但确实没有合适台词」的记录位置——那样的人会
永远卡在 Top 20，队列无法前进。本脚本把它变成一份可推进的队列：

  - 队列 = 覆盖章节最多、仍无语录、**且尚未登记结论**的前 20 人；
  - 核对结论写在 `data/quote_backlog_status.json`，登记后该人退出队列，
    下一名自动补位；无论「已入库」还是「无可靠台词」都能销账；
  - `verify_quotes.py --stats` 复用同一份 `backlog_common.quote_gaps()`，
    控制台与文档不会给出两份互相矛盾的名单。

**纪律（与 README「数据纪律」一致）**：
  - 只读取聚合工件 `data/data.json` / `data/character_quotes.json`；
  - **不写任何原文片段**：原书 TXT 与章节正文按版权红线不入库；
  - **不推断说话人、不自动入库**：自动抽取归属实测 15 条里 13 条把
    「A 对 B 说：…」误归到 B 名下，必须回原书逐条人工核对；
  - 章节正文不入库，本脚本只读章节 key，任何环境生成结果一致，
    因此 `--check` 可以直接进 CI。

用法：
    python src/build_quote_backlog.py           # 生成 docs/quote_backlog.md
    python src/build_quote_backlog.py --check   # 只校验，不一致返回 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import backlog_common as BC  # noqa: E402

OUT = BASE / "docs" / "quote_backlog.md"

STATUS_LABELS = {
    "已入库": "已写入 `character_quotes.json`",
    "无可靠台词": "回书未找到可确证的引号内原话",
    "归属存疑": "有候选原话但说话人无法确证",
}


def render() -> str:
    data = BC.load_data()
    quotes = BC.load_json(BC.QUOTES)
    status = BC.load_status()
    entries = BC.quote_entries(quotes)
    gaps = BC.quote_gaps(data, quotes, status)
    reviewed = status.get("entries") or {}
    total_chars = len(data.get("characters", []))

    rows = []
    for i, c in enumerate(gaps, 1):
        name = c.get("name", "")
        chapters = c.get("chapters") or []
        aliases = "、".join(str(a) for a in (c.get("aliases") or [])[:4]) or "—"
        role = str(c.get("role") or "—")
        if len(role) > 36:
            role = role[:36] + "…"
        rows.append(
            "| %d | **%s** | %d | %s | %s | %s | 待核对 |"
            % (i, BC.esc(name), len(chapters), BC.esc(aliases),
               BC.esc(role), BC.esc(BC.chapters_text(chapters)))
        )
    if not rows:
        rows.append("| — | *高频缺口已全部核对完毕* | — | — | — | — | — |")

    reviewed_rows = []
    for name, rec in sorted(reviewed.items(), key=lambda kv: str(kv[0])):
        if name.startswith("_"):
            continue
        rec = rec if isinstance(rec, dict) else {}
        st = str(rec.get("status") or "（未填）")
        reviewed_rows.append("| %s | %s | %s |"
                             % (BC.esc(name), BC.esc(st),
                                BC.esc(rec.get("note")) or "—"))
    if not reviewed_rows:
        reviewed_rows.append("| — | *暂无已核对记录* | — |")

    return (
        "# 人物卡语录扩面 · 人工考据队列\n\n"
        "> 本文件由 `src/build_quote_backlog.py` 从 `data/data.json` 与\n"
        "> `data/character_quotes.json` 生成，**勿手改**；排序、章节 key 与待考口径\n"
        "> 统一由 `src/backlog_common.py` 提供，与 `verify_quotes.py --stats`、\n"
        "> `docs/geo_backlog.md`、README 同源。\n\n"
        "## 口径与纪律\n\n"
        "- 语录已收录 **%(quoted)d 人**，实体表共 %(chars)d 人。本表列出覆盖章节最多、\n"
        "  仍无语录、且尚未登记结论的 **Top %(gaps)d**（滚动队列，不是固定名单）。\n"
        "- 入选口径：`characters` 按提及章数降序（单键稳定排序，与 `--stats` 完全一致），\n"
        "  排除已收录者，再排除 `data/quote_backlog_status.json` 里已登记结论者。\n"
        "- **自动抽取归属不可靠**：2026-11-05 实测 15 条自动候选里 13 条把\n"
        "  「A 对 B 说：…」误归到了 B 名下。本表因此**不提供任何自动候选原话**。\n"
        "- **本表不写原文片段**：原书 TXT 与章节正文按版权红线不入库，只列聚合工件的\n"
        "  元数据与出处章节 key（`p<部>-c<章序>`）供回书检索。\n"
        "- **不推断说话人**：必须回原书确认「引号内原话 + 说话人 + 说话场景」三者一致；\n"
        "  写进 `character_quotes.json` 后还要过 `src/verify_quotes.py` 的原文命中门禁。\n"
        "- 状态登记在 `data/quote_backlog_status.json`；**未登记即视为待核对**。\n"
        "  登记后该人退出队列、下一名自动补位，所以「确实没有合适台词」也能销账。\n\n"
        "## 待核对队列（%(gaps)d 条）\n\n"
        "| # | 人物 | 提及章数 | 别名 | 书中身份 | 出处章节 | 状态 |\n"
        "|--:|---|--:|---|---|---|---|\n"
        "%(rows)s\n\n"
        "## 建议核验路径（方法论，不是语录结论）\n\n"
        "- 优先找「人物名 + 说道 / 答道 / 喝道 / 曰 / 说」**直接前缀**的引号内原话；\n"
        "- 排除「A 对 B 说：…」这类句式里 B 被误当成说话人的情况，也排除叙述者转述；\n"
        "- 诗句、遗言、民间歌谣本来就没有「某某说道」前缀，需另找归属证据\n"
        "  （谁写的、谁引的、上下文主语是谁），找不到就登记「归属存疑」；\n"
        "- 确认原句后可跑 `python src/verify_quotes.py --strict-attribution`\n"
        "  查看引号前 90 字的前缀证据，但最终仍以人工读上下文为准；\n"
        "- 收录时用实体表**正名**作 key，别用别名；0 原文命中即弃用。\n\n"
        "## 已核对记录（%(reviewed)d 条）\n\n"
        "| 人物 | 结论 | 备注（回书章节与判断依据） |\n"
        "|---|---|---|\n"
        "%(reviewed_rows)s\n\n"
        "结论取值：`已入库` / `无可靠台词` / `归属存疑`。\n\n"
        "## 完成后怎么回填\n\n"
        "1. 找到原话 + 说话人 → 写进 `data/character_quotes.json`\n"
        "   （key 必须是实体表正名）；\n"
        "2. **无论是否入库**，都在 `data/quote_backlog_status.json` 的 `entries` 里\n"
        "   登记 `{status, note}`，否则同一个人会一直占着队列名额；\n"
        "3. 跑 `python src/verify_quotes.py`（本机有原著 TXT 时逐条校验原文命中）；\n"
        "4. 跑 `python src/build_quote_backlog.py` 重生成队列，\n"
        "   README 的语录人数由 `src/sync_readme.py` 同步。\n"
    ) % {
        "quoted": len(entries),
        "chars": total_chars,
        "gaps": len(gaps),
        "rows": "\n".join(rows),
        "reviewed": len(reviewed_rows) if reviewed else 0,
        "reviewed_rows": "\n".join(reviewed_rows),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成人物卡语录扩面人工考据队列")
    ap.add_argument("--check", action="store_true", help="只校验文档是否与数据一致")
    args = ap.parse_args(argv)
    doc = render()
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if doc == old:
        print("[check] OK：docs/quote_backlog.md 与数据一致" if args.check
              else "[done] 已是最新，无需写入")
        return 0
    if args.check:
        print("[check] 失败：docs/quote_backlog.md 落后，"
              "请跑 python src/build_quote_backlog.py", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    print("[done] 已生成 %s（%d 字符）" % (OUT.relative_to(BASE), len(doc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
