---
slug: 01-sociology
zh: 关系的两种写法：社交资本、孤立点与被重复计数的边
en: Two Ways of Writing Relations: Social Capital, Isolates, and Repeated Edges
kzh: 关系社会学；社会资本；弱关系；孤立点；双文本对照
ken: sociology of relations; social capital; weak ties; isolates; comparative reading
refs: granovetter1973, lin2001, scott1990
abstract_zh: 两本长篇小说的关系表分别有 {{tc.rel}} 条与 {{ft.rel}} 条记录，但去重后只剩 {{tc.pairs}} 对与 {{ft.pairs}} 对——同一对人物被跨章重复记录，平均每对 {{tc.repeat_ratio}} 条与 {{ft.repeat_ratio}} 条。本文先纠正这个计数事实，再比较两书的关系结构：天才基本法是单星网络（{{tc.comps}} 个连通分量、{{tc.iso_pct}}% 的人物零关系边），我在废土世界扫垃圾是有组织的多团块（{{ft.comps}} 个分量、最大分量占 {{ft.max_comp_pct}}%）。同一套社会资本理论在两种结构里兑现方式完全不同：一个只能通过单一枢纽兑现，一个可以绕过枢纽。
abstract_en: The two novels yield {{tc.rel}} and {{ft.rel}} relation records, but only {{tc.pairs}} and {{ft.pairs}} unique undirected pairs remain after de-duplication. We first correct this counting artefact, then compare relational structure: Tiancai Jibenfa is a single-star network, while Wozai Feitu Shijie Sao Laji is a multi-cluster organisation. Social capital theory cashes out very differently in the two shapes.
---

## 1. 引言

把小说读成社会，最容易被误读的一个数字是「关系条数」。{{tc.rel}} 与 {{ft.rel}} 这两个数字看起来像社交广度，实际上它们是**跨章重复计数**的产物：同一对人物在第 1 章、第 37 章、第 108 章各被抽取一次，就会产生三条记录。格兰诺维特（Granovetter, 1973）讨论弱关系时，关心的是「谁与谁相连」这个拓扑，而不是「相连被记录了几次」。本文因此先做一件不讨好的事：把重复去掉，再看结构。

## 2. 数据与方法

### 2.1 语料

《天才基本法》（长洱，{{tc.ch}} 章）与《我在废土世界扫垃圾》（有花在野，{{ft.ch}} 章）。两书经同一套抽取流程构建知识图谱：章节切分 → 人物/地点/事件/关系结构化 → 类型归约 → 校验。规模为人物 {{tc.chars}} / {{ft.chars}}，事件 {{tc.ev}} / {{ft.ev}}，关系 {{tc.rel}} / {{ft.rel}}，地点 {{tc.locs}} / {{ft.locs}}。

### 2.2 去重口径

关系表按「无向对」去重：`(A,B)` 与 `(B,A)` 视为同一对，只保留一次。所有拓扑量（度、平均度、连通分量、孤立点）一律用去重口径；原始条数并列给出以便回查。这一步不是修饰，而是**结论方向会被它改写**：按原始条数排名，党爱萍会以 59 条边进入核心圈；按去重口径，她只有 3 个邻居。

### 2.3 边界

孤立点大多是只出场一章的龙套，这属于**抽取值域**问题，不能读作「书中人物孤僻」。本文只对「有边人物」的内部结构下结论。

## 3. 分析与发现

### 3.1 关系表的条数不是社交广度

**结论**：天才 {{tc.rel}} 条关系只覆盖 {{tc.pairs}} 个唯一对（平均每对 {{tc.repeat_ratio}} 条）；废土 {{ft.rel}} 条覆盖 {{ft.pairs}} 对（{{ft.repeat_ratio}} 条/对）。

> 可信度：高 ｜ 性质：实测 ｜ 证据：`relations[].from/to` 无向去重，分母 {{tc.rel}} / {{ft.rel}} ｜ 来源：`relations.json`

两书的重复强度差了近一倍。天才的重复来自「平行世界重演」——草莓世界与芝士世界的同一场景被各记一次，因此同一对关系反复出现；废土的重复更接近「长期同行」——队友关系在数百章里持续存在，每章各记一次。**同一个计数现象，背后是两种叙事机制**（此句为推断，可信度中）。

### 3.2 一个星，与六个团块

**结论**：天才的关系图是 {{tc.comps}} 个连通分量、最大分量 {{tc.max_comp}} 人（{{tc.max_comp_pct}}%），中心是{{tc.top1_name}}（度 {{tc.top1_deg}}），度=1 的节点占 {{tc.deg1_pct}}%；废土是 {{ft.comps}} 个分量、最大分量 {{ft.max_comp}} 人（{{ft.max_comp_pct}}%），中心是{{ft.top1_name}}（度 {{ft.top1_deg}}），度=1 占 {{ft.deg1_pct}}%。

> 可信度：高 ｜ 性质：实测 ｜ 证据：去重后建图，节点 {{tc.nodes}} / {{ft.nodes}}，平均度 {{tc.avg_deg}} / {{ft.avg_deg}} ｜ 来源：`relations[]` + `characters[]`

天才有 {{tc.iso}} 人（{{tc.iso_pct}}%）完全没有关系边，废土 {{ft.iso}} 人（{{ft.iso_pct}}%）。这组差距比中心度更能说明体裁差异：校园叙事把绝大多数人写成「同班同学」这种**无差别背景**，组织叙事则必须给每个人一个位置（队友、上下级、交易对象）。废土的关系基类里出现了天才完全没有的三类：交易 40、支配 48、寄生 8。

### 3.3 别名是关系位置的标记，不是同义词

**结论**：天才 {{tc.alias_total}} 个别名覆盖 {{tc.alias_pct}}% 的人物；废土 {{ft.alias_total}} 个覆盖 {{ft.alias_pct}}%。

> 可信度：高 ｜ 性质：实测 ｜ 证据：`characters[].aliases` 长度统计 ｜ 来源：`characters.json`

一个人被叫「老林」「林爸爸」「公园看门老大爷」，不是三个名字，是三个**关系位置**。林（Lin, 2001）把这种可动员的关系称为社会资本：它的价值不在名单长度，而在「谁能以什么名义调用谁」。天才的别名密度低于废土，但别名的**跨度**更大（从亲属称谓到职业称谓），这与单星结构一致——所有关系都要经过同一个枢纽，于是枢纽必须拥有多种身份。

## 4. 讨论

斯科特（Scott, 2017）区分公开文本与隐藏文本：弱者在大人物面前表演顺从，在背后另有一套话语。这套框架在废土比在天才更适用——废土有 267 条上下级关系与 48 条支配关系，等级是明写的；天才的等级是分数排名，明写但可推翻。**当等级可以被考试推翻时，隐藏文本的需求就下降了**，这或许是天才的「冲突」多为公开竞争的原因。

本研究的边界很清楚：图谱记录的是「书里写了谁与谁有关」，不是「人物在虚构世界里真实的社会网」。抽取偏向有名字、有台词、有互动的人，沉默者会被系统性漏掉。

## 5. 结论

两本书的关系结构不能用一个「关系条数」概括。去掉重复计数之后，一个是围绕单一枢纽的星形网络，一个是多团块的组织网络；同样叫「社会资本」，前者只能通过枢纽兑现，后者可以绕过枢纽自组织。**计数口径的纠正不是技术细节，它决定了我们看见的是一个人，还是一个社会。**
