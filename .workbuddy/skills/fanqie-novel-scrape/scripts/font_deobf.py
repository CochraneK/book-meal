# -*- coding: utf-8 -*-
"""
番茄小说字体反混淆
==================
番茄（fanqienovel.com）把正文常用字映射到 Unicode 私有区（PUA, U+E000–U+F8FF），
HTML 里直接读到的是乱码（控制台还会看不见）。本模块负责把它还原成汉字。

原理
----
1. 页面加载的 woff2 是 `SourceHanSansSC-Normal` 的**子集**，glyph name 形如 `gid58345`，
   保留了原版字体的 glyph id。
2. 把每个 PUA 字形按 nonzero winding 规则栅格化成 40×40 位图。
3. 与本机静态 **Noto Sans SC Regular**（与思源黑体同源同字重）的常用汉字位图做 IoU 比对。
4. 取 IoU 最高者作为答案，并记录与第二名的差距（margin）作为置信度。
5. 缓存 `gid -> 汉字`。**gid 稳定、PUA 分配才变**，所以同一批字体只需解一次，全书复用。

实测：单份字体 362 个 PUA，357 个高置信命中，解码后残留 0。

踩过的坑（改动前务必读）
------------------------
- 必须用**静态 Regular** 字体作参考。`NotoSansSC-VF.ttf` 默认实例是 wght=100(Thin)，
  笔画细一半，IoU 会掉到 0.5 左右，全盘皆错。
- 必须用 **nonzero winding** 填充。PIL 的 `ImageDraw.polygon` 逐个填会把「口」「日」
  这类字的内腔填实，而番茄与 Noto 的 contour 切分方式不同（番茄常把多个部件合并成
  1–2 条路径，Noto 是 6 条），填实后两边不一致，IoU 虚低。
- 不要比对 contour 数或节点数——番茄重写过路径结构，同字两边差异很大。
- 参考字体首选本机静态 OTF；没有就自动从 CDN 拉一份到缓存目录（约 8 MB）。
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

RASTER = 40  # 栅格边长；40 已足够区分汉字，再大会拖慢匹配

# 本机优先（静态 Regular，勿用 VF）
REF_CANDIDATES = [
    r"C:\Windows\Fonts\Noto Sans SC (TrueType).otf",
    r"C:\Windows\Fonts\NotoSansSC-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJKsc-Regular.otf",
    "/System/Library/Fonts/PingFang.ttc",
]

# 都没有时自动下载（jsDelivr 上的 noto-cjk 官方镜像）
REF_DOWNLOAD = [
    "https://fastly.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf",
    "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf",
]


class _FlattenPen(BasePen):
    """把三次/二次贝塞尔统一采样为折线点，便于后续栅格化。"""

    def __init__(self, glyphSet, upem, samples=8):
        super().__init__(glyphSet)
        self.contours = []
        self._cur = None
        self.upem = float(upem)
        self.n = samples

    def _moveTo(self, pt):
        self._flush()
        self._cur = [(pt[0] / self.upem, pt[1] / self.upem)]

    def _lineTo(self, pt):
        self._cur.append((pt[0] / self.upem, pt[1] / self.upem))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur[-1]
        for i in range(1, self.n + 1):
            t = i / self.n
            mt = 1 - t
            a, b, c = 3 * mt * mt * t, 3 * mt * t * t, t ** 3
            self._cur.append((
                mt ** 3 * p0[0] + a * p1[0] / self.upem + b * p2[0] / self.upem + c * p3[0] / self.upem,
                mt ** 3 * p0[1] + a * p1[1] / self.upem + b * p2[1] / self.upem + c * p3[1] / self.upem,
            ))

    def _qCurveToOne(self, ctrl, p2):
        p0 = self._cur[-1]
        for i in range(1, self.n + 1):
            t = i / self.n
            mt = 1 - t
            self._cur.append((
                mt * mt * p0[0] + 2 * mt * t * ctrl[0] / self.upem + t * t * p2[0] / self.upem,
                mt * mt * p0[1] + 2 * mt * t * ctrl[1] / self.upem + t * t * p2[1] / self.upem,
            ))

    def _closePath(self):
        self._flush()

    def _endPath(self):
        self._flush()

    def _flush(self):
        if self._cur:
            self.contours.append(self._cur)
            self._cur = None


def glyph_contours(font, gname, samples=8):
    pen = _FlattenPen(font.getGlyphSet(), font["head"].unitsPerEm, samples)
    try:
        font.getGlyphSet()[gname].draw(pen)
    except Exception:
        return []
    pen._flush()
    return [c for c in pen.contours if len(c) >= 3]


def rasterize(contours, size=RASTER):
    """nonzero winding 扫描线填充。内腔（如「口」中间）会被正确留空。"""
    grid = np.zeros((size, size), dtype=bool)
    edges = []
    for c in contours:
        m = len(c)
        for i in range(m):
            x1, y1 = c[i]
            x2, y2 = c[(i + 1) % m]
            if y1 != y2:
                edges.append((x1, y1, x2, y2))
    if not edges:
        return grid

    E = np.asarray(edges, dtype=np.float64)
    ys = (size - np.arange(size, dtype=np.float64) - 0.5) / size
    y1, y2 = E[:, 1][None, :], E[:, 3][None, :]
    crosses = (y1 <= ys[:, None]) != (y2 <= ys[:, None])

    dy = np.where(E[:, 3] - E[:, 1] == 0, 1e-9, E[:, 3] - E[:, 1])
    t = (ys[:, None] - y1) / dy[None, :]
    xs = E[:, 0][None, :] + t * (E[:, 2] - E[:, 0])[None, :]
    dirs = np.broadcast_to(np.where(E[:, 3] > E[:, 1], 1, -1)[None, :], xs.shape).astype(np.int16)

    xs = np.where(crosses, xs, np.inf)
    order = np.argsort(xs, axis=1)
    xs_s = np.take_along_axis(xs, order, axis=1)
    d_s = np.take_along_axis(dirs, order, axis=1)
    d_s = np.where(np.isfinite(xs_s), d_s, 0)
    wind = np.cumsum(d_s, axis=1)

    if wind.shape[1] < 2:
        return grid
    x_lo, x_hi = xs_s[:, :-1], xs_s[:, 1:]
    active = (wind[:, :-1] != 0) & np.isfinite(x_lo) & np.isfinite(x_hi)
    lo = np.ceil(x_lo * size - 0.5)
    hi = np.floor(x_hi * size - 0.5)
    cols = np.arange(size)[None, None, :]
    grid = (active[:, :, None] & (cols >= lo[:, :, None]) & (cols <= hi[:, :, None])).any(axis=1)
    return grid


def _download_ref(dest, verbose=True):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    for url in REF_DOWNLOAD:
        try:
            if verbose:
                print(f"  下载参考字体：{url.split('/')[-1]} …")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
            if os.path.getsize(tmp) > 1_000_000:
                os.replace(tmp, dest)
                return dest
        except Exception as e:
            if verbose:
                print(f"    失败：{type(e).__name__} {str(e)[:80]}")
        finally:
            if os.path.exists(tmp) and not os.path.exists(dest):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
    return None


def pick_ref_font(cache_dir=None, auto_download=True, verbose=True):
    """返回 (路径, TTFont)。优先本机静态字体，缺失则下载到 cache_dir。"""
    for p in REF_CANDIDATES:
        if os.path.exists(p):
            try:
                return p, TTFont(p, fontNumber=0)
            except Exception:
                continue

    if cache_dir:
        cached = os.path.join(cache_dir, "NotoSansSC-Regular.otf")
        if not os.path.exists(cached) and auto_download:
            _download_ref(cached, verbose=verbose)
        if os.path.exists(cached):
            return cached, TTFont(cached, fontNumber=0)

    raise FileNotFoundError(
        "找不到参考中文字体（静态 Noto Sans SC / 思源黑体 Regular）。\n"
        "候选路径：" + "\n  ".join(REF_CANDIDATES) + "\n"
        "可将 NotoSansSC-Regular.otf 放到脚本目录的 assets/ 下，或允许联网自动下载。"
    )


def gb2312_chars():
    """GB2312 一二级汉字 6763 字 + 常用全角标点 + 数字字母。"""
    out = []
    for hi in range(0xB0, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                out.append(bytes([hi, lo]).decode("gb2312"))
            except Exception:
                pass
    out.extend("，。！？；：、“”‘’（）《》〈〉【】〔〕—…·～％＃＠＆＊＋－／＜＞＝｜＼＾￥")
    out.extend("0123456789")
    out.extend("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
    return list(dict.fromkeys(out))


def build_reference(ref_font, chars):
    cmap = ref_font.getBestCmap()
    keep, bits = [], []
    for ch in chars:
        if ord(ch) not in cmap:
            continue
        cs = glyph_contours(ref_font, cmap[ord(ch)])
        if not cs:
            continue
        bits.append(rasterize(cs))
        keep.append(ch)
    arr = np.asarray(bits, dtype=bool) if bits else np.zeros((0, RASTER, RASTER), bool)
    return keep, arr


def match_subset(sub_font, ref_chars, ref_bits):
    """返回 {gid: (汉字, iou, margin)}。以 gid 为键，便于跨字体文件复用。"""
    flat_ref = ref_bits.reshape(len(ref_chars), -1)
    ref_area = flat_ref.sum(axis=1).astype(np.float64)
    cmap = sub_font.getBestCmap()
    out = {}
    for cp, gname in sorted(cmap.items()):
        if not (0xE000 <= cp <= 0xF8FF):
            continue
        try:
            gid = int(gname[3:]) if gname.startswith("gid") else -1
        except ValueError:
            gid = -1
        if gid < 0:
            continue
        cs = glyph_contours(sub_font, gname)
        if not cs:
            continue
        flat = rasterize(cs).reshape(-1)
        area = flat.sum()
        if area == 0:
            continue
        inter = flat_ref @ flat.astype(np.int32)
        union = ref_area + area - inter
        iou = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
        k = min(3, len(iou))
        top = np.argpartition(-iou, k - 1)[:k]
        top = top[np.argsort(-iou[top])]
        margin = float(iou[top[0]] - iou[top[1]]) if len(top) > 1 else 1.0
        out[gid] = (ref_chars[int(top[0])], float(iou[top[0]]), margin)
    return out


def build_gid_map(woff_path, cache_path=None, verbose=True, auto_download=True):
    """从字体文件构建/加载 gid -> 汉字 映射。"""
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            raw = json.load(f)
        m = {int(k): v for k, v in raw.items()}
        if verbose:
            print(f"  映射缓存命中：{len(m)} 条 ({os.path.basename(cache_path)})")
        return m

    sub = TTFont(woff_path)
    cache_dir = os.path.dirname(cache_path) if cache_path else None
    ref_path, ref = pick_ref_font(cache_dir, auto_download, verbose)
    if verbose:
        print(f"  参考字体：{os.path.basename(ref_path)}")
    chars = gb2312_chars()
    rc, rb = build_reference(ref, chars)
    if verbose:
        print(f"  参考字库：{len(rc)} 字，开始比对…")
    res = match_subset(sub, rc, rb)

    gid_map = {}
    weak = []
    for gid, (ch, iou, margin) in res.items():
        if ch and iou >= 0.55 and margin >= 0.04:
            gid_map[gid] = ch
        else:
            weak.append((gid, ch, round(iou, 3), round(margin, 3)))
    if verbose:
        print(f"  解码成功 {len(gid_map)}/{len(res)}（低置信 {len(weak)}）")
        if weak:
            print("  低置信示例：", weak[:6])

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in gid_map.items()}, f, ensure_ascii=False, indent=0)
    return gid_map


def map_for_font(woff_path, gid_map):
    """把 gid 映射转成当前字体的 PUA 码点映射。"""
    font = TTFont(woff_path)
    cmap = font.getBestCmap()
    out = {}
    for cp, gname in cmap.items():
        if not (0xE000 <= cp <= 0xF8FF) or not gname.startswith("gid"):
            continue
        try:
            gid = int(gname[3:])
        except ValueError:
            continue
        ch = gid_map.get(gid)
        if ch:
            out[cp] = ch
    return out


def decode(text, pua_map):
    if not pua_map:
        return text
    return "".join(pua_map.get(ord(c), c) for c in text)


def residue(text):
    """未解码的 PUA 字符数，用来做质检。"""
    return sum(1 for c in text if 0xE000 <= ord(c) <= 0xF8FF)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python font_deobf.py <font.woff2> [cache.json]")
        sys.exit(1)
    woff = sys.argv[1]
    cache = sys.argv[2] if len(sys.argv) > 2 else None
    m = build_gid_map(woff, cache)
    print("样本：", "".join(list(m.values())[:60]))
