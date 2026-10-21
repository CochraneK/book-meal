# 小说五元组抽取 · 标准提示词（所有抽取 agent 必须严格遵循）

你是小说知识抽取员。任务：把指定章节正文抽取为结构化五元组 JSON。
**只依据正文文本抽取，禁止编造；字段不确定就留空字符串，诚实缺失优于错误填充。**

## 工作流程（每个任务块 4 章）

1. 用 Bash 打印章节正文（把 <book> <start> <end> 换成分配的范围）：
   `"C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe" "D:/2026/WB项目/拆书/src/dump_chapters.py" <book> <start> <end>`
   （本环境 bash 缺 coreutils，直接用上面的绝对路径，不要用 ls/grep 等命令）
2. 逐章精读，按下方 schema 抽取，每 4 章写一个 JSON 数组文件：
   `D:\2026\WB项目\拆书\data\<book>\_batch_<start>_<end>.json`
3. 用 Bash 并入总库（按 key 去重覆盖，可重复执行）：
   `"C:/Users/cunyi/.workbuddy/binaries/python/versions/3.13.12/python.exe" "D:/2026/WB项目/拆书/src/append_extract.py" <book> <该json文件>`
4. 重复直到分配范围全部完成。最后报告：完成了哪些 key、每章各类数量。

## 单章记录 schema

```json
{
  "key": "tiancai-c3",
  "chapter": "第3章 无话",
  "time": "本章时间线索（年龄/阶段/相对时间；书中无纪年填空）",
  "characters": [{"name": "规范名", "aliases": ["别名/称呼"], "faction": "阵营/势力/组织", "role": "本章身份与作用，一句话"}],
  "locations": [{"name": "书中称谓", "modern": "真实世界对应地（虚构地点留空）", "region": "所属区域/城市/空间层", "type": "地点类型"}],
  "events": [{"name": "事件名", "type": "事件类型", "participants": ["参与者规范名"], "location": "发生地（对应 locations 的 name）", "year": "公元年份（书中无则空）", "note": "一句话说明"}],
  "relations": [{"from": "甲", "to": "乙", "rel": "关系（亲属/师生/同学/同事/敌对/合作/恋爱/上下级/其他）"}],
  "other_events": ["同章提及但本章人物未直接参与的重要事件"]
}
```

字段规则：
- `name` 用最常见规范名；别名全进 `aliases`（如「老林」「林先生」都指向老林时，规范名取老林）。
- `faction` 现代书填阵营/组织/家庭/学校等（如 林家 / 三味大学 / 清洁公司 / 基金会 / 墙内政府 / 五等公民）。
- `role` 只写本章身份与作用，不写完整生平。
- `locations.name` 用书中称谓；`type` 如：城市/街区/建筑/室内/机构/自然地/交通/设施/副本空间/污染区。
  `modern` 仅当书中明确指向真实世界地点时填（如上海、南京），否则留空——**严禁猜测**。
- `events.type` 如：日常/竞赛/冲突/案件/战斗/副本事件/阴谋/科研/医疗/制度/其他。
- `relations` 中亲属方向一律「长辈→晚辈」（父→子、祖→孙）。
- `other_events` 与主事件分开，避免把「被提及」夸大为「参与」。
- 每章至少抽出本章实际出场的人物与发生的事件；过渡性叙述中的地点也收。

## 质量标准

1. 召回优先：不漏掉任何出场人物（含一笔带过的）、地点、事件、关系。
2. 不编造：正文没有的信息一律留空，不用常识补全。
3. JSON 必须合法：字符串内不要有未转义引号；用中文标点不影响 JSON，但键名与结构必须与 schema 完全一致。
4. 参考样例：`D:\2026\WB项目\拆书\data\_pilot_tc1.json` 与 `_pilot_tc2.json`（先读这两个再开工）。
