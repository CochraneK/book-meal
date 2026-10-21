# -*- coding: utf-8 -*-
"""故事长文 Markdown → HTML（供单文件报告内嵌）
=============================================
为什么自己写而不用现成库
------------------------
报告必须是**单文件离线 HTML**，不能引外部 CDN，也不能在构建时多装一个依赖。
长文只用到一个很小的 Markdown 子集（标题/加粗/斜体/行内代码/引用/列表/表格/分割线/段落），
所以这里写一个聚焦的转换器，并且**先整体转义再套行内格式**——
顺序反了会让正文里的 `<` `>` `&` 直接变成 HTML，长文里有大量「P/NP」「E=mc²」之类
的尖括号与比较符，不转义会静默吃掉内容甚至注入标签。

章号引用会被改成可点链接（class="ch-ref" + data-no），前端点击后弹窗列出该章的
KG 事件，让「每条可回原文核对」在报告里真的能点。这一步是长文挂进报告的关键：
否则它只是一段漂亮的静态文字，和数据库仍然是两张皮。

用法：
    from md_to_html import md_to_html
    html, headings = md_to_html(open(path, encoding="utf-8").read())
"""
import html as _html
import re

__all__ = ["md_to_html", "slugify"]

_ESC = _html.escape

# 章号引用：先匹配区间（第 1–249 章），再匹配枚举（第 12、13、51 章）。
# 顺序不能反——区间里的数字也会被枚举模式吃掉一半。
_REF_RANGE = re.compile(r"第\s*(\d+)\s*[–—~～]\s*(\d+)\s*章")
_REF_LIST = re.compile(r"第\s*(\d+(?:\s*、\s*\d+)*)\s*章")


def slugify(text, used):
    """标题 → 稳定 id（中文原样保留，只做去重）。"""
    s = re.sub(r"\s+", "-", str(text).strip())
    s = re.sub(r"[^\w一-鿿-]", "", s) or "sec"
    base, i = s, 2
    while s in used:
        s = "%s-%d" % (base, i)
        i += 1
    used.add(s)
    return s


def _inline(text, ref):
    """行内格式：先转义，再代码、加粗、斜体，最后章号链接。"""
    s = _ESC(text)

    # 行内代码（先做，避免代码里的 * 被当成强调）
    def code_sub(m):
        return "<code>" + m.group(1) + "</code>"
    s = re.sub(r"`([^`]+)`", code_sub, s)

    # 加粗 / 斜体
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)

    # 章号引用（在已转义的文本上做；数字与「第/章/、」不受转义影响）
    if ref:
        def range_sub(m):
            a, b = m.group(1), m.group(2)
            return ('<a class="ch-ref" href="javascript:void(0)" data-no="%s">第%s–%s章</a>'
                    % (a, a, b))
        s = _REF_RANGE.sub(range_sub, s)

        def list_sub(m):
            nums = [x for x in re.split(r"[、\s]+", m.group(1)) if x]
            if not nums:
                return m.group(0)
            links = "".join(
                '<a class="ch-ref" href="javascript:void(0)" data-no="%s">%s</a>' % (n, n)
                for n in nums)
            return "第" + links + "章"
        s = _REF_LIST.sub(list_sub, s)
    return s


def _split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_sep_row(line):
    cells = _split_row(line)
    return bool(cells) and all(re.match(r"^:?-{2,}:?$", c) for c in cells)


def md_to_html(md, ref=True):
    """Markdown → (html, headings)。headings = [(level, text, id)]，供前端建目录。"""
    lines = (md or "").replace("\r\n", "\n").split("\n")
    out = []
    headings = []
    used_ids = set()
    i, n = 0, len(lines)

    def flush_para(buf):
        if buf:
            out.append("<p>" + _inline(" ".join(buf), ref) + "</p>")
            del buf[:]

    para = []
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 空行 → 段落结束
        if not stripped:
            flush_para(para)
            i += 1
            continue

        # 分割线
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            flush_para(para)
            out.append("<hr>")
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para(para)
            lv = len(m.group(1))
            txt = m.group(2).strip()
            hid = slugify(txt, used_ids)
            headings.append((lv, txt, hid))
            out.append('<h%d id="%s">%s</h%d>' % (lv, hid, _inline(txt, ref), lv))
            i += 1
            continue

        # 引用块（连续行合并；空 > 行分段，避免把题注和正文糊成一句）
        if stripped.startswith(">"):
            flush_para(para)
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            paras, cur = [], []
            for x in buf:
                if x:
                    cur.append(x)
                elif cur:
                    paras.append(" ".join(cur))
                    cur = []
            if cur:
                paras.append(" ".join(cur))
            out.append("<blockquote>" +
                       "".join("<p>%s</p>" % _inline(p, ref) for p in paras) +
                       "</blockquote>")
            continue

        # 表格
        if stripped.startswith("|") and i + 1 < n and _is_sep_row(lines[i + 1].strip()):
            flush_para(para)
            head = _split_row(stripped)
            i += 2
            body = []
            while i < n and lines[i].strip().startswith("|"):
                body.append(_split_row(lines[i].strip()))
                i += 1
            t = ["<div class='table-wrap'><table class='data'><thead><tr>"]
            t += ["<th>%s</th>" % _inline(c, ref) for c in head]
            t.append("</tr></thead><tbody>")
            for row in body:
                t.append("<tr>" + "".join("<td>%s</td>" % _inline(c, ref) for c in row) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        # 无序列表
        if re.match(r"^[-*+]\s+", stripped):
            flush_para(para)
            items = []
            while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*+]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % _inline(x, ref) for x in items) + "</ul>")
            continue

        # 有序列表
        if re.match(r"^\d+[.、]\s+", stripped):
            flush_para(para)
            items = []
            while i < n and re.match(r"^\d+[.、]\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+[.、]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % _inline(x, ref) for x in items) + "</ol>")
            continue

        # 普通段落行（合并连续行）
        para.append(stripped)
        i += 1

    flush_para(para)
    return "\n".join(out), headings


if __name__ == "__main__":
    import os
    import sys
    for p in sys.argv[1:]:
        src = open(p, encoding="utf-8").read()
        h, heads = md_to_html(src)
        print("=== %s → %d 字符, %d 个标题" % (p, len(h), len(heads)))
        print(h[:600])
        print("...")
