---
slug: 08-networks
zh: 星形、团块与重复边：小说人物网络的两种拓扑
en: Stars, Clusters, and Repeated Edges: Two Topologies of Fictional Character Networks
kzh: 复杂网络；度分布；连通分量；弱关系；双文本对照
ken: complex networks; degree distribution; connected components; weak ties; comparative reading
refs: watts1998, barabasi1999, moretti2011, granovetter1973
abstract_zh: 去重后，天才基本法的关系网络有 {{tc.nodes}} 个有边节点、{{tc.pairs}} 条边、{{tc.comps}} 个连通分量，最大度 {{tc.top1_deg}}（{{tc.top1_name}}），度=1 的节点占 {{tc.deg1_pct}}%；我在废土世界扫垃圾有 {{ft.nodes}} 个节点、{{ft.pairs}} 条边、{{ft.comps}} 个分量，最大度 {{ft.top1_deg}}（{{ft.top1_name}}），度=1 占 {{ft.deg1_pct}}%。本文讨论两种拓扑对叙事的功能：星形网络制造聚焦，团块网络制造纵深。
abstract_en: After de-duplication, Tiancai Jibenfa forms a star ({{tc.nodes}} nodes, {{tc.pairs}} edges, {{tc.comps}} component, max degree {{tc.top1_deg}}), while the wasteland novel forms {{ft.comps}} clusters ({{ft.nodes}} nodes, {{ft.pairs}} edges, max degree {{ft.top1_deg}}). We discuss what each topology does for narrative.
---

## 1. 引言

莫莱蒂（Moretti, 2011）用网络分析研究《哈姆雷特》时提出一个朴素的洞见：把人物当节点、把互动当边，故事的结构就会显形。这个方法的陷阱在于数据质量——如果同一条边被反复记录，度中心性测到的就不是社交广度，而是「被重复提到的次数」。本文先把这件事说清楚，再谈拓扑。

## 2. 数据与方法

### 2.1 语料

天才 {{tc.rel}} 条关系记录、{{tc.chars}} 位人物；废土 {{ft.rel}} 条、{{ft.chars}} 位。所有关系按无向对去重：`(A,B)` 与 `(B,A)` 合并，同一对只计一次。

### 2.2 指标

度、平均度、度分布、连通分量、最大分量占比、度=1 节点占比。全部基于去重图。

### 2.3 边界

图谱的边来自「书里明确写了的关系」，弱关系（同班同学、路人搭话）大量缺失。因此这里的网络是**叙述网络**，不是**虚构社会网络**。孤立点不等于人物孤僻，只等于「没有被写出关系」。

## 3. 分析与发现

### 3.1 顶点度数背后是重复计数

**结论**：天才 {{tc.rel}} 条记录去重后 {{tc.pairs}} 对（{{tc.repeat_ratio}} 条/对），废土 {{ft.rel}} 条去重后 {{ft.pairs}} 对（{{ft.repeat_ratio}} 条/对）。

> 可信度：高 ｜ 性质：实测 ｜ 证据：`relations[].from/to` 无向去重 ｜ 来源：`relations.json`

这一条必须先讲，因为它会改写所有排名。按原始条数，某些配角会因为「跨 50 章反复出现同一关系」而进入核心圈；按去重口径，他们只有两三个邻居。把重复当强度，是网络分析在文学数据上最常见的错误。

### 3.2 星形与多团块

**结论**：天才 {{tc.comps}} 个连通分量、最大分量 {{tc.max_comp}} 节点（占全部人物 {{tc.max_comp_pct}}%）、平均度 {{tc.avg_deg}}；废土 {{ft.comps}} 个分量、最大分量 {{ft.max_comp}} 节点（{{ft.max_comp_pct}}%）、平均度 {{ft.avg_deg}}。

> 可信度：高 ｜ 性质：实测 ｜ 证据：去重图连通性 ｜ 来源：`relations.json`

天才只有一个分量，意味着所有有关系的人物都连成一片——这是一张**单中心**的图，任何两个人之间最多经过一个枢纽。废土有六个分量，最大者占七成半，其余五成碎片——这是**组织型**的图，存在若干互不相通的小圈子（某些副本队伍、某些据点的人）。瓦茨与斯特罗格茨（Watts & Strogatz, 1998）讨论小世界时强调「局部密集 + 少量长程连接」，天才缺的正是局部密集：它没有次级社团，只有中心与外围。

### 3.3 度分布：没有无标度，只有一颗星

**结论**：天才最大度 {{tc.top1_deg}}（{{tc.top1_name}}），度=1 的节点占 {{tc.deg1_pct}}%；废土最大度 {{ft.top1_deg}}（{{ft.top1_name}}），度=1 占 {{ft.deg1_pct}}%。

> 可信度：中 ｜ 性质：推断（样本量小，未做幂律拟合）｜ 证据：同 3.2 ｜ 来源：`relations.json`

巴拉巴西与阿尔伯特（Barabási & Albert, 1999）的优先连接模型预测度分布呈幂律：少数超级节点、大量长尾。两本书都不符合——它们更像「一个中心和一圈叶子」。这不是模型失效，而是**叙述的选择性**：小说只写推动情节的关系，不写随机社交，于是网络被压成了星形。样本量（{{tc.nodes}} / {{ft.nodes}} 个有边节点）也不足以做分布拟合，所以本条只列为推断。

## 4. 讨论

格兰诺维特（Granovetter, 1973）的弱关系理论在这里有一个有趣的变体：天才的弱关系几乎不存在（度=1 的叶子占 {{tc.deg1_pct}}%），所有信息都必须经过中心；废土的弱关系更多（度=1 占 {{ft.deg1_pct}}%），信息可以在圈子之间横向流动。这可以解释两书情报类事件的差距——天才 {{tc.tbp.情报对话}}%，废土 {{ft.tbp.情报对话}}%。**信息量不是由人物多少决定的，而是由网络的横向连通度决定的。**

边界在于：关系抽取以「明确表述」为准，隐含关系（同校、同乡、曾经见过）没有入图。补上这些边会提高连通度，但两书的相对差异方向不太可能反转。

## 5. 结论

一个是星，一个是团块。星形让故事聚焦，代价是所有人都必须经过同一个人；团块让故事有纵深，代价是读者要记住更多名字。网络拓扑不只是结构描述，它同时也是**叙事成本的分配方案**。
