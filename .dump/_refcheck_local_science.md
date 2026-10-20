# 引用核验报告（局部加强版） · science

- 共享 `_lib/verify_refs.py` 对 monograph 几乎全判 UNVERIFIED（只查第一作者 + OpenAlex 429 限流）；试点篇 11 条仅 1 条通过。本版放宽为「整条记录任作者命中 + 退避重试」，判据其余不变。
- 判据：标题词元重叠 ≥0.5 且 作者姓命中 且 出版年容差 ≤2。

| key | 状态 | 标题 | 命中记录 | DOI |
|---|---|---|---|---|
| ginzburg1980 | `VERIFIED` | The Cheese and the Worms: The Cosmos of a Sixteenth- | The Cheese and the Worms: The Cosmos of  | 10.2307/3104820 |
| levi1985 | `UNVERIFIED` | Inheriting the Universe: Life in a Florentine Family | — | — |
| white1987 | `VERIFIED` | The Content of the Form: Narrative Discourse and His | The Content of the Form: Narrative Disco | 10.2307/2905318 |
| carr1961 | `UNVERIFIED` | What Is History? | — | — |
| stone1971 | `UNVERIFIED` | Prosopography | — | — |
| michel2009 | `UNVERIFIED` | No Time to Think: The Limits of Quantitative Analysi | — | — |
| moretti2013 | `UNVERIFIED` | Distant Reading | — | — |
| needham1954 | `VERIFIED` | Science and Civilisation in China, Volume I: Introdu | Science and Civilisation in China. Volum | 10.2307/211829 |
| needham1965 | `UNVERIFIED` | Science and Civilisation in China, Volume IX: The De | — | — |
| clunas2013 | `UNVERIFIED` | Empire of Great Brightness: Visual Culture of the Mi | — | — |
| mote1988 | `VERIFIED` | The Cambridge History of China, Volume 7: The Ming D | The Cambridge History of China. Volume 7 | 10.2307/2162852 |
| huang1981 | `UNVERIFIED` | The 1587 Year: A Key Year in the Decline of Ming Dyn | — | — |
| bai2020 | `UNVERIFIED` | Mapping the Ming: A digital approach to the spatial  | — | — |
| li2015 | `UNVERIFIED` | Knowledge, discipline and the Ming state: the Bureau | — | — |
