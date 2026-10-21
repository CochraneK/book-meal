---
slug: 07-geography
zh: 定点叙事与移动叙事：空间复用率的两种极端
en: Fixed-point versus Mobile Narrative: Two Extremes of Spatial Reuse
kzh: 空间社会学；场所；场景复用；坐标缺失；双文本对照
ken: sociology of space; place; scene reuse; missing coordinates; comparative reading
refs: gieryn2000
abstract_zh: 天才基本法 {{tc.locs}} 处地点只承载 {{tc.ev}} 件事件，前十大场景占 {{tc.top10_loc_pct}}%，单个「院长办公室」就占 {{tc.top1_loc_pct}}%；我在废土世界扫垃圾 {{ft.locs}} 处地点承载 {{ft.ev}} 件事件，前十大场景只占 {{ft.top10_loc_pct}}%，最高的一处仅 {{ft.top1_loc_pct}}%。前者是定点叙事，后者是移动叙事。空间复用率的差距，直接决定了两本书的读者体验与人物关系形态。
abstract_en: With {{tc.locs}} locations and {{tc.ev}} events, Tiancai Jibenfa concentrates {{tc.top10_loc_pct}}% of events in ten scenes, one office alone taking {{tc.top1_loc_pct}}%. The wasteland novel spreads {{ft.ev}} events over {{ft.locs}} locations, with only {{ft.top10_loc_pct}}% in its top ten. The contrast separates fixed-point from mobile narrative.
---

## 1. 引言

吉里恩（Gieryn, 2000）提醒社会学家：地点不是事件的背景板，而是被社会过程生产出来的东西，同时反过来塑造社会关系。两本小说对「地点」的使用几乎相反——一本反复回到同一个房间，一本不断离开。这种差异可以被量化：场景复用率。

## 2. 数据与方法

### 2.1 语料

天才：{{tc.locs}} 处地点 / {{tc.ev}} 件事件；废土：{{ft.locs}} 处地点 / {{ft.ev}} 件事件。地点按功能基类归约（据点驻地、居住空间、教育科研、交通通道、自然地貌、管制边界、遗迹尸骸等）。

### 2.2 指标

- **场景复用率**：前十大地点承载的事件数 / 有地点事件数；
- **单点强度**：承载事件最多的地点所占比例；
- **无地点事件**：`events[].location` 为空的事件数（衡量叙述的空间依附度）。

### 2.3 边界

坐标状态必须说明：天才 {{tc.locs}} 处、废土 {{ft.locs}} 处**全部没有真实经纬度**，报告内地图为示意。因此本文只讨论「场景之间的关系」，不讨论现实地理。地点匹配采用精确名称匹配，别称不计入，复用率因此是**下限**。

## 3. 分析与发现

### 3.1 一个办公室装下了 7.4% 的事件

**结论**：天才事件最集中的地点是「{{tc.top1_loc}}」，{{tc.top1_loc_n}} 件（{{tc.top1_loc_pct}}%）；前十大地点合计 {{tc.top10_loc_n}} 件（{{tc.top10_loc_pct}}%）。废土最集中的是「{{ft.top1_loc}}」，{{ft.top1_loc_n}} 件（{{ft.top1_loc_pct}}%）；前十合计 {{ft.top10_loc_pct}}%。

> 可信度：高 ｜ 性质：实测 ｜ 证据：`events[].location` 与 `locations[].name` 精确匹配，分母 {{tc.ev}} / {{ft.ev}} ｜ 来源：`events.json` / `locations.json`

{{tc.top10_loc_pct}}% 对 {{ft.top10_loc_pct}}%，差了三倍多。天才的空间是**高压复用**的：一个办公室既是办公场所、又是谈话场所、又是秘密被揭穿的地方，同一空间承担多种功能，读者因此获得熟悉感。废土的空间是**低复用**的：每进入一个新区域就换一批场景，读者获得的是探索感。这两种体验对应两种叙事经济——前者省场景、换深度，后者费场景、换广度。

### 3.2 空间类型的两种配方

**结论**：天才的地点以据点驻地（{{tc.loctb.据点驻地}} 处，{{tc.locp.据点驻地}}%）与教育科研（{{tc.loctb.教育科研}} 处，{{tc.locp.教育科研}}%）为主，医疗场所只有 {{tc.loctb.医疗场所}} 处；废土以据点驻地（{{ft.loctb.据点驻地}} 处，{{ft.locp.据点驻地}}%）、居住空间（{{ft.loctb.居住空间}} 处）、交通通道（{{ft.loctb.交通通道}} 处）、自然地貌（{{ft.loctb.自然地貌}} 处）为主，并有天才完全没有的「管制边界」{{ft.loctb.管制边界}} 处与「遗迹尸骸」{{ft.loctb.遗迹尸骸}} 处。

> 可信度：高 ｜ 性质：实测 ｜ 证据：`locations[].type_base` ｜ 来源：`locations.json`

「管制边界」与「遗迹尸骸」这两个类目只在废土出现，它们本身就是世界观声明：一个有边界要守，一个有尸体要清。天才没有这两个类目，因为它的世界不需要用边界与尸体来定义危险。**地点的类型表，就是世界的类型表。**

### 3.3 无地点事件的比例

**结论**：天才 {{tc.ev_noloc}} 件事件没有地点（{{tc.ev_noloc}} / {{tc.ev}}），废土 {{ft.ev_noloc}} 件。

> 可信度：高 ｜ 性质：实测 ｜ 证据：`events[].location` 为空 ｜ 来源：`events.json`

绝对数差距大，但比例都不高。这说明两书的叙述都高度依附于具体场所——即便是废土的移动叙事，事件也总要发生在某个地方。这一点常被忽视：**「移动」不等于「无地点」，只是地点不断更换**。

## 4. 讨论

空间复用率可以解释一个阅读体验上的差异：读天才时，读者脑中会形成一张很小的地图，几个房间反复出现，人物在其中的位置本身就是信息（谁坐在谁的对面）；读废土时，地图不断扩张，读者记住的是「去过哪类地方」而不是「哪个房间」。前者接近舞台剧，后者接近公路片。

边界在于：地点抽取偏向有名字的场所，走廊、街道这类过渡空间大量遗漏。若把它们补上，废土的移动叙事会更明显，天才的定点叙事则变化不大。

## 5. 结论

天才基本法用 {{tc.locs}} 处地点讲一个高度集中的故事，我在废土世界扫垃圾用 {{ft.locs}} 处地点讲一个不断扩张的故事。空间不是背景，它是叙事节奏的物理形态：**复用率高的书，时间在同一个房间里流逝；复用率低的书，时间在移动中流逝。**
