# 引用核验报告（局部加强版） · info

- 共享 `_lib/verify_refs.py` 对 monograph 几乎全判 UNVERIFIED（只查第一作者 + OpenAlex 429 限流）；试点篇 11 条仅 1 条通过。本版放宽为「整条记录任作者命中 + 退避重试」，判据其余不变。
- 判据：标题词元重叠 ≥0.5 且 作者姓命中 且 出版年容差 ≤2。

| key | 状态 | 标题 | 命中记录 | DOI |
|---|---|---|---|---|
| shannon1948 | `UNVERIFIED` | A Mathematical Theory of Communication | — | — |
| kuran1995 | `VERIFIED` | Private Truths, Public Lies: The Social Consequences | Private Truths, Public Lies: The Social  | 10.2307/2076660 |
| foucault1977 | `UNVERIFIED` | Discipline and Punish: The Birth of the Prison | — | — |
| habermas1989 | `VERIFIED` | The Structural Transformation of the Public Sphere:  | The Public's Fear, or Media as Monster i | 10.2307/466251 |
| scott1990 | `UNVERIFIED` | Domination and the Arts of Resistance: Hidden Transc | — | — |
| sunstein2009 | `UNVERIFIED` | On Rumors: How Falsehoods Spread, Why We Believe The | — | — |
| goffman1959 | `UNVERIFIED` | The Presentation of Self in Everyday Life | — | — |
| mote1988 | `VERIFIED` | The Cambridge History of China, Volume 7: The Ming D | The Cambridge History of China. Volume 7 | 10.2307/2162852 |
| huang1981 | `UNVERIFIED` | 1587, A Year of No Significance: The Ming Dynasty in | — | — |
| brook1998 | `UNVERIFIED` | The Confusions of Pleasure: Commerce and Culture in  | — | — |
| robinson2013 | `UNVERIFIED` | Bandits, Eunuchs, and the Son of Heaven: Rebellion a | — | — |
| lu1998 | `UNVERIFIED` | The Ming Court and the Inner Court | — | — |
| dangnian2009 | `UNVERIFIED` | 明朝那些事儿 | — | — |
| mingkg2026 | `UNVERIFIED` | Ming Knowledge Graph: structured extraction of a pop | — | — |
