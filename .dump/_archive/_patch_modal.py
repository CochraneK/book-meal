# -*- coding: utf-8 -*-
"""一次性：人物详情弹窗补「出场口径」透明标注。"""
p = 'src/generate_report.py'
s = open(p, encoding='utf-8').read()
anchor = ('<div class="detail-block detail-wide"><strong>来源章节</strong>'
          '<div class="source-row">${chapterChips(x.chapters.map(k=>({key:k,...DATA.chapters[k]})))}</div></div>')
note = ('<div class="detail-block detail-wide"><strong>出场口径</strong>'
        '<p>共 ${x.chapters.length} 章，其中 ${x.derivedCount} 章为文本反查推导'
        '（本章正文出现至少 6 次自动登记，与 LLM 抽取区分）</p></div>')
add = anchor + "${x.derivedCount?`" + note + "`:''}"
n = s.count(anchor)
print('锚点出现次数:', n)
assert n >= 1, '锚点未找到'
s = s.replace(anchor, add)
open(p, 'w', encoding='utf-8').write(s)
print('人物详情弹窗已加出场口径说明')
