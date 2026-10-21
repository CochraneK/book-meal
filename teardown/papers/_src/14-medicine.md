---
slug: 14-medicine
zh: 疾病作为情节装置：两种身体叙事
en: Illness as Plot Device: Two Narratives of the Body
kzh: 医学人文；疾病叙事；身体；照护；双文本对照
ken: medical humanities; illness narrative; the body; care; comparative reading
refs: bury1982, held2006, haraway1985
abstract_zh: 天才基本法把疾病写成记忆问题：事件名中「阿尔茨海默」{{tc.kw.alzheimer}} 次、「病」{{tc.kw.illness}} 次，但医疗场所只有 {{tc.loctb.医疗场所}} 处。我在废土世界扫垃圾把身体写成可改造、可污染的对象：「污染」{{ft.kw.pollution}} 次、「尸体」{{ft.kw.corpse}} 次，医疗场所 {{ft.loctb.医疗场所}} 处。本文用比里的「传记性断裂」与哈拉威的赛博格说明：一种身体是被时间侵蚀的，一种身体是被技术改造的。
abstract_en: Illness in Tiancai Jibenfa is a problem of memory ({{tc.kw.alzheimer}} mentions of Alzheimer's, only {{tc.loctb.医疗场所}} medical sites), whereas the wasteland novel treats the body as modifiable and contaminable ({{ft.kw.pollution}} pollution, {{ft.kw.corpse}} corpse mentions, {{ft.loctb.医疗场所}} medical sites). We read the two through biographical disruption and cyborg theory.
---

## 1. 引言

医学人文的核心问题是：疾病如何改变一个人对自己的叙述。比里（Bury, 1982）把慢性病的影响概括为「传记性断裂」——原有的生活叙事被打断，人必须重写自己。两本小说都写了身体，但写法相反：一本写身体如何被时间侵蚀，一本写身体如何被技术改造。

## 2. 数据与方法

### 2.1 语料

天才 {{tc.ev}} 事件 / {{tc.locs}} 地点；废土 {{ft.ev}} 事件 / {{ft.locs}} 地点。医疗相关指标取自事件基类「科研医疗」「危机伤亡」与地点基类「医疗场所」。

### 2.2 关键词口径

只统计**事件名**中的关键词出现次数，不读正文。词表：天才「阿尔茨海默」「病」；废土「污染」「尸体」。这是下限估计——正文里的病症描述未计入。

### 2.3 边界

「科研医疗」既包含治疗也包含实验，两类在伦理上完全不同，本文不做拆分。医疗场所的数量受地点抽取粒度影响（家中的病榻可能未被登记为医疗场所）。

## 3. 分析与发现

### 3.1 疾病在事件里，不在医院里

**结论**：天才科研医疗 {{tc.tb.科研医疗}} 件（{{tc.tbp.科研医疗}}%），医疗场所仅 {{tc.loctb.医疗场所}} 处（{{tc.locp.医疗场所}}%）；事件名含「阿尔茨海默」{{tc.kw.alzheimer}} 次、含「病」{{tc.kw.illness}} 次。

> 可信度：高 ｜ 性质：实测（关键词口径）｜ 证据：`events[].type_base`、`events[].name`、`locations[].type_base` ｜ 来源：`events.json` / `locations.json`

疾病在这本书里几乎不发生在医院。它发生在家里、在记忆里、在一个人忽然认不出女儿的瞬间。医疗场所只有 {{tc.loctb.医疗场所}} 处，而「阿尔茨海默」在事件名里出现 {{tc.kw.alzheimer}} 次——**病是被叙述的，不是被治疗的**。这与比里的观察一致：慢性病对当事人的意义，主要不在临床，而在日常秩序的瓦解。

### 3.2 身体作为可改造对象

**结论**：废土科研医疗 {{ft.tb.科研医疗}} 件（{{ft.tbp.科研医疗}}%）、危机伤亡 {{ft.tb.危机伤亡}} 件（{{ft.tbp.危机伤亡}}%）、医疗场所 {{ft.loctb.医疗场所}} 处；事件名含「污染」{{ft.kw.pollution}} 次、含「尸体」{{ft.kw.corpse}} 次。

> 可信度：高 ｜ 性质：实测（关键词口径）｜ 证据：同 3.1 ｜ 来源：`events.json` / `locations.json`

废土的身体是**边界模糊**的：污染会进入身体，改造会替换器官，尸体是需要处理的对象。「尸体」{{ft.kw.corpse}} 次的出现频率说明死亡在这里是常态化的物质，而不是事件。哈拉威（Haraway, 1987）的赛博格宣言讨论的正是这种边界崩塌——人与机器、人与动物、人与污染之间不再有清晰分界。废土几乎是把这篇宣言写成了世界观。

### 3.3 照护的两种组织方式

**结论**：天才危机伤亡 {{tc.tb.危机伤亡}} 件（{{tc.tbp.危机伤亡}}%），废土 {{ft.tb.危机伤亡}} 件（{{ft.tbp.危机伤亡}}%）；天才救助关系去重 {{tc.rescue}} 对，废土 {{ft.rescue}} 对。

> 可信度：高 ｜ 性质：实测 ｜ 证据：`events[].type_base`、`relations[].rel_base` 去重 ｜ 来源：`events.json` / `relations.json`

照护在天才里是长期的、少数人对一个人的（{{tc.rescue}} 对关系承担了全部救助记录）；在废土里是短期的、多点分布的（{{ft.rescue}} 对关系）。赫尔德（Held, 2005）指出关怀伦理要求对具体他者的持续回应，这种持续性在天才是可能的，因为伤亡率极低；在废土，照护必须被制度化才能覆盖需求。

## 4. 讨论

两种身体叙事的政治含义不同。天才的身体是**不可替换**的：记忆一旦流失就无法恢复，因此照护的意义在于陪伴而非修复。废土的身体是**可替换**的：器官、义体、意识都能被改造，因此照护的意义转向维护与升级。前者接近医学人文的传统议题（尊严、叙事、临终），后者接近生物政治的新议题（可改造性、污染、去人性化）。

边界在于：本文的关键词只覆盖事件名，正文中的病症描写、身体感受、医疗场景对话都没有进入统计。这些恰恰是医学人文最看重的质地，量化方法在这里只能提供骨架。

## 5. 结论

天才基本法写的是被时间侵蚀的身体，我在废土世界扫垃圾写的是被技术改造的身体。前者把疾病写成记忆的丧失，后者把疾病写成边界的溃散。两种写法都指向同一个问题：**当身体不再可靠，人靠什么确认自己还是自己。**
