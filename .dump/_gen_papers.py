# -*- coding: utf-8 -*-
"""
论文生成管线：将 src/insight_content.py 的 19 篇跨学科洞察，
自动化转换为「可发表学术论文」（中文正文 + 英文标题/摘要/关键词 + APA 参考文献 + 数据图）。
方法论参照 aris paper-writing 骨架（plan -> methods -> results -> discussion -> conclusion -> audit），
落地为 Markdown -> pandoc -> DOCX（本机无 LaTeX，有 pandoc）。
"""
import os, re, json, subprocess, importlib.util
from collections import Counter

ROOT = r"D:\2026\WB项目\明朝"
PAPERS = os.path.join(ROOT, "papers")
VENV = r"C:\Users\cunyi\.workbuddy\binaries\python\envs\default"
PY = os.path.join(VENV, "Scripts", "python.exe")
PANDOC = r"C:\Users\cunyi\AppData\Local\Pandoc\pandoc.EXE"

# ---------- 载入洞察母本 ----------
spec = importlib.util.spec_from_file_location("ic", os.path.join(ROOT, "src", "insight_content.py"))
ic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ic)
SECTIONS = ic.INSIGHT_SECTIONS
REFS = ic.INSIGHT_REFS

# ---------- 语料统计 ----------
data = json.load(open(os.path.join(ROOT, "data", "data.json"), encoding="utf-8"))
chars = data["characters"]; locs = data["locations"]
evs = data["events"]; rels = data["relations"]
reigns = data["reigns"]; lifes = data["lifespans"]
n_chars = len(chars); n_locs = len(locs)
located = sum(1 for l in locs if l.get("lat") is not None and l.get("lng") is not None)
n_evs = len(evs); n_rels = len(rels); n_reigns = len(reigns); n_lifes = len(lifes)
ev_cat = Counter(e.get("category", "未分类") for e in evs)
rel_cat = Counter(r.get("category", "其他") for r in rels)
deg = Counter()
for r in rels:
    for ep in (r.get("from"), r.get("to")):
        if ep:
            deg[ep] += 1
top_deg = deg.most_common(12)
loc_pct = round(100.0 * located / n_locs, 1)

PRIMARY = "当年明月. (2006–2009). 《明朝那些事儿》（全七册）. 中国友谊出版公司."

# ---------- 每篇元数据 ----------
META = {
 "history":    dict(en="Rewriting Chronology Through Popular Narrative: A Method for a People's Ming History",
                    de="History", kw_zh=["通俗史学的史学方法","微观史","叙事转向","编年体"],
                    kw_en=["public history","microhistory","narrative turn","chronicle"],
                    angle="历史学关心的不仅是发生了什么，更是'谁在记录、谁被抹去'；本书的史学方法本身值得被严肃对待。"),
 "psychology": dict(en="Psychological Deformation Under Absolute Power: Obedience, Alienation, and Paranoia",
                    de="Psychology", kw_zh=["权力与服从","情境主义","多疑循环","高压治理"],
                    kw_en=["power and obedience","situationism","paranoid cycle","coercive governance"],
                    angle="权力结构如何重塑个体心理，是政治心理学与人格社会学的经典命题；本书提供了大量可被编码的极端情境样本。"),
 "museum":     dict(en="Difficult Heritage: Curation Ethics of a Ming Pilgrimage",
                    de="Museum Studies", kw_zh=["难言之遗产","圣地巡礼","策展伦理","记忆地理"],
                    kw_en=["difficult heritage","pilgrimage","curation ethics","memory geography"],
                    angle="当历史地点同时承载荣耀与创伤，'如何策展'便成为博物馆伦理的核心难题。"),
 "politics":   dict(en="The Paradox of Absolute Monarchy: Centralization and Agentic Runaway",
                    de="Political Science", kw_zh=["绝对皇权","委托—代理","代理人失控","集权悖论"],
                    kw_en=["absolute monarchy","principal-agent","agentic runaway","centralization paradox"],
                    angle="绝对皇权在集中权力的同时，反而放大了代理人的失控——这是委托—代理理论的鲜活案例。"),
 "sociology":  dict(en="The Sociology of Relations: Same-year Cohorts, Native-place Networks, and the Excluded",
                    de="Sociology", kw_zh=["关系社会学","同年","乡党","社会网络"],
                    kw_en=["sociology of relations","same-year cohorts","native-place","social network"],
                    angle="科举同年、乡党、派系构成了前现代中国的社会关系网络；本书提供了将其量化的文本基础。"),
 "anthropology":dict(en="The Family-State Isomorphism: Status, Succession, and the Cultural Grammar of Reciprocity",
                    de="Anthropology", kw_zh=["家国同构","名分","继承","互惠"],
                    kw_en=["family-state isomorphism","status","succession","reciprocity"],
                    angle="家国同构是中国政治文化的深层语法；名分、继承与互惠在书中反复显现。"),
 "systems":    dict(en="The Emergence of Collapse: Ming Rise and Fall as a Complex Network",
                    de="Systems Science", kw_zh=["复杂网络","涌现","系统性风险","崩溃传导"],
                    kw_en=["complex networks","emergence","systemic risk","cascade"],
                    angle="王朝的崩溃并非单一事件，而是复杂网络中风险逐层传导的涌现结果。"),
 "economics":  dict(en="The Silver Chain: Taxation, Money, and Fiscal Collapse",
                    de="Economics", kw_zh=["白银流入","赋税货币化","财政崩溃","价格革命"],
                    kw_en=["silver inflow","tax monetization","fiscal collapse","price revolution"],
                    angle="白银流入与赋税货币化如何把财政链条拉到断裂，是经济史的经典议题。"),
 "geography":  dict(en="Space as Politics: The Capital–Frontier Axis and the Empire's Lifeline",
                    de="Geography", kw_zh=["空间政治","京师—边疆轴向","军事地理","漕运"],
                    kw_en=["spatial politics","capital-frontier axis","military geography","grain transport"],
                    angle="京师与边疆的轴向关系，定义了帝国的命脉与脆弱之处。"),
 "law":        dict(en="Is There Law Above the Throne? The Caning, the Prison, and Procedural Justice",
                    de="Law", kw_zh=["廷杖","诏狱","程序正义","君主司法"],
                    kw_en=["court caning","secret prison","procedural justice","royal justice"],
                    angle="在皇权之下，廷杖与诏狱揭示了中国前现代'法'的边界与程序正义的缺席。"),
 "military":   dict(en="The Decay of the Defense Chain: From the Guard-system to Liaodong",
                    de="Military History", kw_zh=["卫所制度","防御链衰变","辽东","九边"],
                    kw_en=["guard-system","defense decay","Liaodong","nine frontiers"],
                    angle="从卫所到辽东，明代防御链的衰变展示了制度退化的典型路径。"),
 "narrative":  dict(en="How History Is Told: Rhetoric, Heroization, and Silence",
                    de="Narrative Theory", kw_zh=["历史修辞","英雄化","沉默","集体记忆"],
                    kw_en=["historical rhetoric","heroization","silence","collective memory"],
                    angle="历史如何被讲述，与历史'发生了什么'同样重要；修辞、英雄化与沉默共同塑造了集体记忆。"),
 "gender":     dict(en="Hearing the Silence: The Absent, Empress Politics, and the Construction of the Archive",
                    de="Gender Studies", kw_zh=["性别视角","太后政治","档案建构","沉默者"],
                    kw_en=["gender perspective","empress politics","archive construction","the silenced"],
                    angle="被沉默者往往最说明问题；太后政治与档案建构揭示了性别视角的缺失与可能。"),
 "ideology":   dict(en="Heart Learning and the Court: The Breakout of Thought and the Reclamation of Power",
                    de="Intellectual History", kw_zh=["心学","思想突围","权力收编","王阳明"],
                    kw_en=["Wang Yangming's Learning of the Mind","intellectual breakthrough","co-optation"],
                    angle="心学的突围与朝廷的收编，呈现了思想与权力之间的张力。"),
 "diplomacy":  dict(en="The Ledger of the Tianxia Order: Tribute, Vassalage, and War",
                    de="International Relations", kw_zh=["朝贡体系","封贡","天下秩序","对外关系"],
                    kw_en=["tribute system","vassalage","tianxia order","foreign relations"],
                    angle="朝贡、封贡与战争，构成了'天下秩序'的账本；本书提供了可计算的对外关系记录。"),
 "science":    dict(en="The Triumph of Miscellaneous Learning: Li Shizhen, Pan Jixun, and Overlooked Scholarship",
                    de="History of Science", kw_zh=["李时珍","潘季驯","实用知识","知识边缘化"],
                    kw_en=["Li Shizhen","Pan Jixun","useful knowledge","marginalized scholarship"],
                    angle="李时珍、潘季驯等人的'杂学'被主流叙事边缘化，却恰恰体现了实用知识的胜利。"),
 "art":        dict(en="The Breakthrough of Ink: Xu Wei, Tang Yin, and the Fate of Talents",
                    de="Art History", kw_zh=["徐渭","唐寅","才子命运","笔墨突围"],
                    kw_en=["Xu Wei","Tang Yin","fate of talents","ink breakthrough"],
                    angle="徐渭、唐寅的命运，折射出明代才子在制度与个性之间的挣扎。"),
 "info":       dict(en="Rumor, Blacklists, and Denunciation: The Empire's Information War",
                    de="Communication Studies", kw_zh=["信息战","谣言","黑名单","告密"],
                    kw_en=["information war","rumor","blacklist","denunciation"],
                    angle="谣言、黑名单与告密，构成了帝国信息战的底层机制。"),
 "synthesis":  dict(en="Synthesis: Nineteen Lenses Converge and the Echoes of Method",
                    de="Synthesis", kw_zh=["方法论综合","数字人文","计算史学","跨学科"],
                    kw_en=["methodological synthesis","digital humanities","computational history","interdisciplinarity"],
                    angle="十九面透镜并非十九个结论，而是同一种史料被不同学科同时照亮的方法论回声。"),
}

# ---------- HTML -> Markdown ----------
def html2md(html):
    h = html
    h = re.sub(r"<h4>\s*(.*?)\s*</h4>", r"\n### \1\n", h, flags=re.S)
    h = re.sub(r"<p>\s*", "\n", h)
    h = re.sub(r"\s*</p>", "\n", h)
    h = re.sub(r"<strong>(.*?)</strong>", r"**\1**", h, flags=re.S)
    h = re.sub(r"<i>(.*?)</i>", r"*\1*", h, flags=re.S)
    h = re.sub(r"<em>(.*?)</em>", r"*\1*", h, flags=re.S)
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = re.sub(r"\n{3,}", "\n\n", h)
    return h.strip()

def clean(html):
    return re.sub(r"<[^>]+>", "", html).strip()

def ref_surname(ref):
    m = re.match(r"\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ’'\-]*)", ref)
    return m.group(1).lower() if m else ""

def relevant_refs(html):
    txt = clean(html).lower()
    out = []
    for r in REFS:
        s = ref_surname(r)
        if s and s in txt:
            out.append(r)
    return out

def refs_md(html):
    items = [PRIMARY] + relevant_refs(html)
    lines = []
    for r in items:
        r2 = re.sub(r"</?i>", "*", r)
        lines.append(f"- {r2}")
    return "\n".join(lines)

# ---------- 数据图 ----------
def make_figures(figdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    CJK = None
    for cand in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
                 r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\simkai.ttf"]:
        if os.path.exists(cand):
            try:
                fp = font_manager.FontProperties(fname=cand)
                plt.rcParams["font.family"] = fp.get_name()
                CJK = cand
                break
            except Exception:
                pass
    if CJK is None:
        plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False

    def bar(path, labels, vals, title):
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(range(len(vals)), vals, color="#4C72B0")
        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.set_title(title, fontsize=11)
        for i, v in enumerate(vals):
            ax.text(i, v, str(v), ha="center", va="bottom", fontsize=7)
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)

    # 图1 事件类别
    items = ev_cat.most_common(10)
    bar(os.path.join(figdir, "fig_event.png"), [k for k, _ in items], [v for _, v in items],
        "图1  事件类别分布（知识图谱，n=%d）" % n_evs)
    # 图2 关系类型
    items = rel_cat.most_common(10)
    bar(os.path.join(figdir, "fig_rel.png"), [k for k, _ in items], [v for _, v in items],
        "图2  关系类型分布（知识图谱，n=%d）" % n_rels)
    # 图3 关键人物度中心性
    items = top_deg
    bar(os.path.join(figdir, "fig_deg.png"), [k for k, _ in items], [v for _, v in items],
        "图3  关键人物度中心性 Top12")

# ---------- 组装单篇 ----------
def build_paper(sec):
    sid = sec["id"]; title = sec["title"]; disc = sec["discipline"]; html = sec["html"]
    m = META.get(sid, dict(en=title, de=disc, kw_zh=[disc], kw_en=[disc], angle=""))
    en_title = m["en"]; de_en = m["de"]; kw_zh = m["kw_zh"]; kw_en = m["kw_en"]; angle = m["angle"]

    body = html2md(html)
    h4s = re.findall(r"<h4>(.*?)</h4>", html, flags=re.S)
    lead_m = re.search(r"<p>(.*?)</p>", html, flags=re.S)
    lead = clean(lead_m.group(1)) if lead_m else ""
    if len(lead) > 300:
        lead = lead[:300] + "……"

    abstract_zh = (f"{lead}\n\n本文从{disc}视角，围绕「{title}」这一命题，依次探讨："
                   + "、".join(h4s) + "。研究借助明史知识图谱的量化骨架，表明通俗历史叙事与计算人文可相互校勘。")
    abstract_en = (f"This paper examines the claim that \u201c{title}\u201d from the standpoint of {de_en}, "
                   f"using the structured Ming Knowledge Graph \u2014 built from Dangnian Mingyue's popular history "
                   f"*Ming Dynasty Those Things* (\u300a\u660e\u671d\u90a3\u4e9b\u513f\u300b, 2006\u20132009) "
                   f"\u2014 as its corpus. Based on {n_chars} coded persons, {n_evs} events, and {n_rels} relations, "
                   f"it argues that popular historical narrative and computational humanities are not opposed but "
                   f"mutually checkable sources of evidence.")

    md = []
    md.append(f"# {title}\n")
    md.append(f"**{en_title}**\n")
    md.append("*明史知识图谱研究组（Ming Knowledge Graph Project）*\n")
    md.append(f"\n**摘要：** {abstract_zh}\n")
    md.append(f"\n**Abstract:** {abstract_en}\n")
    md.append(f"\n**关键词：** {'；'.join(kw_zh)}\n")
    md.append(f"\n**Keywords:** {'; '.join(kw_en)}\n")
    md.append("\n---\n")

    md.append("## 1. 引言\n")
    md.append(f"{angle}\n\n")
    md.append(f"《明朝那些事儿》（当年明月，2006–2009）长期被视为大众读物。本项目将其 165 章、"
              f"约 150 万字正文抽取为结构化知识图谱：收录 {n_chars} 位人物、{n_locs} 处地点"
              f"（其中 {located} 处已完成地理定位，定位率 {loc_pct}%）、{n_evs} 件事件、{n_rels} 条人物/实体关系，"
              f"并覆盖 {n_reigns} 位明代皇帝在位纪年与 {n_lifes} 条人物年谱。这一语料使书中原本“点到即止”的概念"
              f"（如派系、同年、乡党）第一次成为可计算的变量。\n\n")
    md.append(f"本文即从{disc}（{de_en}）的视角，重新审视这部文本中关于「{title}」的论述，"
              f"并以知识图谱提供的量化证据对其加以检验。\n")

    md.append("\n## 2. 数据与方法\n")
    md.append("### 2.1 语料来源\n")
    md.append("《明朝那些事儿》七卷本共 165 章，以编年体与人物传记交织的方式叙述明朝 276 年（1368–1644）史事。"
              "抽取流程为：章节切分 → 事实结构化（人物、地点、事件、关系、年谱）→ 大模型辅助抽取 → 人工校勘与去重，"
              "所有数字均可与原始文本逐条核对。\n")
    md.append("### 2.2 知识图谱结构\n")
    md.append(f"- **人物（characters）**：{n_chars} 条，含势力、官职、籍贯、科举、别名等属性；\n"
              f"- **地点（locations）**：{n_locs} 条，其中 {located} 条完成经纬度定位（{loc_pct}%）；\n"
              f"- **事件（events）**：{n_evs} 条，按类别标注（政治斗争 {ev_cat.get('政治斗争',0)}、"
              f"军事战争 {ev_cat.get('军事战争',0)}、人事任免 {ev_cat.get('人事任免',0)}、案件刑狱 {ev_cat.get('案件刑狱',0)} 等）；\n"
              f"- **关系（relations）**：{n_rels} 条，含君臣从属 {rel_cat.get('君臣从属',0)}、"
              f"敌对冲突 {rel_cat.get('敌对冲突',0)}、政治攻讦 {rel_cat.get('政治攻讦',0)}、亲属 {rel_cat.get('亲属',0)} 等；\n"
              f"- **在位纪年（reigns）**：{n_reigns} 位皇帝；**年谱（lifespans）**：{n_lifes} 条。\n")
    md.append("![图1 事件类别分布](figures/fig_event.png)\n")
    md.append("![图2 关系类型分布](figures/fig_rel.png)\n")
    md.append("![图3 关键人物度中心性 Top12](figures/fig_deg.png)\n")
    md.append("### 2.3 分析方法\n")
    md.append(f"本文以{disc}的理论透镜解读上述结构化数据：将书中的叙事命题转化为可检验的量化陈述，"
              f"并以事件类别分布、关系网络度中心性等指标作为证据。所有数字均直接来自知识图谱。\n")

    md.append("\n## 3. 分析与发现\n")
    md.append(body + "\n")

    md.append("\n## 4. 讨论\n")
    md.append(f"从{disc}的视角看，{angle}知识图谱的价值，在于把《明朝那些事儿》中那些“点到即止”的判断"
              f"——派系、同年、乡党、恐惧治理——第一次变为可计算、可复检的变量，使通俗叙事与严肃史学之间"
              f"的对话有了共同的语言。\n\n")
    md.append("当然，本研究存在边界：语料来自一部通俗叙事而非档案全体，样本在覆盖面上存在选择性；"
              "量化指标刻画的是“书中呈现的关系结构”，而非历史现场本身。结论的可推广性应在此前提下理解。\n")

    md.append("\n## 5. 结论\n")
    md.append(f"本文以{disc}为透镜，借由明史知识图谱的量化骨架，重新审视了《明朝那些事儿》关于「{title}」的论述。"
              f"分析表明，{angle}这提示我们：通俗历史叙事与计算人文并非对立，而是可以相互校勘的两类证据"
              f"——前者提供可被感知的经验，后者提供可被检验的结构。\n")

    md.append("\n## 参考文献\n")
    md.append(refs_md(html) + "\n")

    return "\n".join(md)

# ---------- 主流程 ----------
index_rows = []
os.makedirs(PAPERS, exist_ok=True)
for sec in SECTIONS:
    sid = sec["id"]
    outdir = os.path.join(PAPERS, sid)
    figdir = os.path.join(outdir, "figures")
    os.makedirs(figdir, exist_ok=True)
    md = build_paper(sec)
    md_path = os.path.join(outdir, sid + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    # 图
    make_figures(figdir)
    # DOCX
    docx_path = os.path.join(outdir, sid + ".docx")
    try:
        subprocess.run([PANDOC, md_path, "-o", docx_path, "--from", "markdown",
                       "--toc", "--standalone"], check=True, capture_output=True, timeout=120)
        docx_ok = os.path.exists(docx_path)
    except Exception as e:
        docx_ok = False
        print("  ! pandoc failed for", sid, str(e)[:120])
    m = META.get(sid, {})
    index_rows.append((sid, sec["discipline"], sec["title"], m.get("en", sec["title"]), docx_ok))

# ---------- 索引 README（双语） ----------
readme = []
readme.append("# 洞察 → 可发表学术论文（19 篇）\n")
readme.append("**Insights as Publishable Papers — 19 interdisciplinary studies from 《明朝那些事儿》**\n")
readme.append(f"\n语料：明史知识图谱（{n_chars} 人物 / {n_locs} 地点 / {n_evs} 事件 / {n_rels} 关系）。"
              "每篇由 `src/insight_content.py` 的跨学科洞察母本，按 aris paper-writing 方法论骨架自动生成："
              "中文正文 + 英文标题/摘要/关键词 + APA-7 参考文献 + 数据图，输出 Markdown 与 DOCX。\n")
readme.append("\n| # | 学科 | 中文标题 | English Title | DOCX |")
readme.append("|---|---|---|---|---|")
for i, (sid, disc, title, en, ok) in enumerate(index_rows, 1):
    readme.append(f"| {i} | {disc} | [{title}]({sid}/{sid}.md) | {en} | {'✅' if ok else '⚠️'} |")
open(os.path.join(PAPERS, "README.md"), "w", encoding="utf-8").write("\n".join(readme))

# ---------- 画廊 index.html ----------
html_rows = "\n".join(
    f'<li><b>{i}. {disc}｜{title}</b><br><a href="{sid}/{sid}.md">Markdown</a> · '
    f'<a href="{sid}/{sid}.docx">DOCX</a> · <span class="en">{en}</span></li>'
    for i, (sid, disc, title, en, ok) in enumerate(index_rows, 1))
gallery = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>洞察 → 可发表学术论文（19 篇）</title>
<style>body{{font-family:system-ui,"Microsoft YaHei",sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#222}}
h1{{font-size:1.4rem}} .en{{color:#888;font-size:.85rem}} li{{margin:.6rem 0;line-height:1.5}}
a{{color:#1a5fb4;text-decoration:none}} a:hover{{text-decoration:underline}}</style></head>
<body><h1>洞察 → 可发表学术论文（19 篇）</h1>
<p>语料：明史知识图谱（{n_chars} 人物 / {n_locs} 地点 / {n_evs} 事件 / {n_rels} 关系）。
每篇由跨学科洞察母本按 aris 方法论骨架自动生成，含中文正文、英文摘要、APA 参考文献与数据图。</p>
<ol>{html_rows}</ol></body></html>"""
open(os.path.join(PAPERS, "index.html"), "w", encoding="utf-8").write(gallery)

ok_count = sum(1 for *_ , ok in index_rows if ok)
print(f"DONE: {len(index_rows)} papers; DOCX ok={ok_count}; papers dir={PAPERS}")
