# 引用核验报告（局部加强版） · synthesis

- 共享 `_lib/verify_refs.py` 对 monograph 几乎全判 UNVERIFIED（只查第一作者 + OpenAlex 429 限流）；试点篇 11 条仅 1 条通过。本版放宽为「整条记录任作者命中 + 退避重试」，判据其余不变。
- 判据：标题词元重叠 ≥0.5 且 作者姓命中 且 出版年容差 ≤2。

| key | 状态 | 标题 | 命中记录 | DOI |
|---|---|---|---|---|
| moretti2005 | `UNVERIFIED` | Graphs, Maps, Trees: Abstract Models for a Literary  | — | — |
| michel2011 | `VERIFIED` | Quantitative analysis of culture using millions of d | Quantitative Analysis of Culture Using M | 10.1126/science.1199644 |
| jockers2013 | `UNVERIFIED` | Macroanalysis: Digital Methods and Literary History | — | — |
| underwood2019 | `UNVERIFIED` | Distant Horizons: Digital Evidence and Literary Chan | — | — |
| da2019 | `VERIFIED` | The Computational Case against Computational Literar | The Computational Case against Computati | 10.1086/702594 |
| blei2003 | `UNVERIFIED` | Latent Dirichlet Allocation | — | — |
| ramsay2011 | `UNVERIFIED` | Reading Machines: Toward an Algorithmic Criticism | — | — |
| white1987 | `VERIFIED` | The Content of the Form: Narrative Discourse and His | The Content of the Form: Narrative Disco | 10.2307/2905318 |
| stone1971 | `UNVERIFIED` | Prosopography | — | — |
| ginzburg1980 | `VERIFIED` | The Cheese and the Worms: The Cosmos of a Sixteenth- | The Cheese and the Worms: The Cosmos of  | 10.2307/3104820 |
| mote1988 | `VERIFIED` | The Cambridge History of China, Volume 7: The Ming D | The Cambridge History of China. Volume 7 | 10.2307/2162852 |
| huang1981 | `UNVERIFIED` | 1587, A Year of No Significance: The Ming Dynasty in | — | — |
| manovich2020 | `UNVERIFIED` | Cultural Analytics | — | — |
| piper2018 | `UNVERIFIED` | Enumerations: Data and Literary Study | — | — |
| dangnian2009 | `UNVERIFIED` | 明朝那些事儿 | — | — |
| mingkg2026 | `UNVERIFIED` | Ming Knowledge Graph: structured extraction of a pop | — | — |
