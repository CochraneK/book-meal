#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""组装 GitHub Pages 的发布目录：只放成品，工程文件一律不进站点。

背景
────
Pages 的 legacy 模式（Deploy from a branch）会把**整个仓库**当站点根目录
发布，于是 src/、data/、teardown/、README.md 这些工程文件都能被任何人
直接下载。改成 Actions 部署（build_type=workflow）后，站点内容只来自本
脚本挑出的白名单，仓库里其余的东西根本不会被上传。

白名单
──────
    index.html        书库门户（src/build_hub.py 生成）
    standalone.html   明书离线版（单文件，双击可开）
    sw.js             Service Worker，必须在站点根，否则 scope 不对
    ming/             明书报告 + assets 分块
    books/            各书报告与 manifest.json

新增一本书只要落在 books/<id>/ 下就自动包含，不需要改本文件。

用法
────
    python src/build_dist.py                 生成/刷新 _site/
    python src/build_dist.py --out <dir>     指定输出目录
    python src/build_dist.py --check         校验已有输出目录与仓库成品一致
"""
import argparse
import hashlib
import os
import shutil
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(BASE, "_site")

PUBLISH_FILES = ("index.html", "standalone.html", "sw.js")
PUBLISH_DIRS = ("books", "ming")

# 兜底闸：站点里绝不该出现的东西。白名单复制理论上碰不到这些，
# 但一旦有人往 books/ 或 ming/ 里误放了原著或脚本，这里会在 CI 上拦下来。
FORBIDDEN_SUFFIX = (".txt", ".py", ".log", ".md")
FORBIDDEN_NAMES = {"quotes.json", "chapters.json", "source_combined.txt", "data.json"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def human(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0


def plan():
    """返回 [(源路径, 相对仓库根的路径), ...]，顺序稳定。"""
    items = []
    for name in PUBLISH_FILES:
        src = os.path.join(BASE, name)
        if os.path.isfile(src):
            items.append((src, name))
        else:
            print(f"[warn] 白名单文件缺失：{name}")
    for d in PUBLISH_DIRS:
        root = os.path.join(BASE, d)
        if not os.path.isdir(root):
            print(f"[warn] 白名单目录缺失：{d}")
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [x for x in dirnames
                           if not x.startswith(".") and x != "__pycache__"]
            for fn in sorted(filenames):
                src = os.path.join(dirpath, fn)
                items.append((src, os.path.relpath(src, BASE)))
    return items


def scan_guard(out):
    """扫一遍产物，命中禁忌就返回清单（CI 里视为失败）。"""
    bad = []
    for dirpath, _dirnames, filenames in os.walk(out):
        for fn in filenames:
            if fn in FORBIDDEN_NAMES or fn.lower().endswith(FORBIDDEN_SUFFIX):
                bad.append(os.path.relpath(os.path.join(dirpath, fn), out))
    return sorted(bad)


def build(out):
    items = plan()
    if os.path.isdir(out):
        try:
            shutil.rmtree(out)
        except OSError as exc:
            print(f"[warn] 旧产物目录删不掉（{exc}），改为覆盖写入")
    os.makedirs(out, exist_ok=True)
    for src, rel in items:
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst) or out, exist_ok=True)
        shutil.copy2(src, dst)
    # 不加 .nojekyll，Jekyll 会跳过下划线开头的目录，并把 .md 渲染成页面。
    with open(os.path.join(out, ".nojekyll"), "w", encoding="utf-8"):
        pass
    return items


def summary(out, items):
    total = 0
    per_top = {}
    for _src, rel in items:
        size = os.path.getsize(os.path.join(out, rel)) if os.path.exists(os.path.join(out, rel)) else 0
        total += size
        top = rel.split(os.sep)[0] if os.sep in rel else "(根目录文件)"
        per_top[top] = per_top.get(top, 0) + size
    print(f"发布目录：{out}")
    print(f"文件数   ：{len(items)}")
    print(f"总体积   ：{human(total)}")
    for top in sorted(per_top):
        print(f"  {top:<16}{human(per_top[top]):>10}")


def check(out):
    if not os.path.isdir(out):
        print(f"[FAIL] 发布目录不存在：{out}（先跑一次不带 --check 的构建）")
        return 1
    items = plan()
    missing, diff = [], []
    for src, rel in items:
        dst = os.path.join(out, rel)
        if not os.path.isfile(dst):
            missing.append(rel)
        elif sha256(src) != sha256(dst):
            diff.append(rel)
    bad = scan_guard(out)
    if missing:
        print("[FAIL] 产物缺失：")
        for r in missing:
            print("  - " + r)
    if diff:
        print("[FAIL] 与仓库不一致（需要重新构建）：")
        for r in diff:
            print("  - " + r)
    if bad:
        print("[FAIL] 产物里出现了不该发布的文件：")
        for r in bad:
            print("  - " + r)
    if missing or diff or bad:
        return 1
    print(f"[OK] {len(items)} 个文件与仓库一致，无禁忌文件")
    return 0


def main():
    ap = argparse.ArgumentParser(description="组装 Pages 发布目录（只发布成品）")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出目录，默认 _site")
    ap.add_argument("--check", action="store_true", help="只校验，不构建")
    args = ap.parse_args()

    if args.check:
        return check(args.out)
    items = build(args.out)
    bad = scan_guard(args.out)
    summary(args.out, items)
    print(f"门禁     ：{'通过' if not bad else '发现 ' + str(len(bad)) + ' 个禁忌文件'}")
    for r in bad:
        print("  ! " + r)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
