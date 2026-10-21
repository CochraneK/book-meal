# -*- coding: utf-8 -*-
"""
拆书流水线 · 阶段② 辅助：把抽取记录安全并入 extract_raw.json
============================================================
用法：
    python src/append_extract.py <book> <rec.json> [rec2.json ...]

- rec.json 可以是「单条记录对象」或「记录数组」
- 按 key 去重覆盖（重抽某章不会产生重复条目）
- 每次写入都是完整重写，保证 JSON 始终合法
- 缺少 key 字段的记录会被拒绝并报告
- 【并发安全】多个抽取 agent 同时写入时，用 .lock 文件串行化，
  并采用「写临时文件 + 原子替换」避免中途崩溃导致 JSON 截断。
"""

import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCK_WAIT_MAX = 180.0   # 最长等锁秒数（多个 agent 同时收尾时可能排长队）
LOCK_STALE = 300.0      # 锁文件超过该秒数视为残留，强制回收


def acquire_lock(lock_path):
    """用 O_CREAT|O_EXCL 抢锁；等待超时或回收残留锁。"""
    start = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            # 残留锁回收：写锁的进程可能已崩溃
            try:
                if time.time() - os.path.getmtime(lock_path) > LOCK_STALE:
                    os.remove(lock_path)
                    continue
            except OSError:
                pass
            if time.time() - start > LOCK_WAIT_MAX:
                return False
            time.sleep(0.25 + (os.getpid() % 7) * 0.05)


def release_lock(lock_path):
    try:
        os.remove(lock_path)
    except OSError:
        pass


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    book = sys.argv[1]
    data_dir = os.path.join(BASE, "data", book)
    os.makedirs(data_dir, exist_ok=True)
    raw_path = os.path.join(data_dir, "extract_raw.json")
    lock_path = os.path.join(data_dir, ".extract_raw.lock")

    # 先把输入文件全部读进内存（等锁期间不做 IO，缩窄临界区）
    incoming = []
    bad = 0
    for p in sys.argv[2:]:
        obj = json.load(open(p, encoding="utf-8"))
        items = obj if isinstance(obj, list) else [obj]
        for it in items:
            if not it.get("key"):
                bad += 1
                continue
            incoming.append(it)

    if not acquire_lock(lock_path):
        print(f"[fail] {book}: 等待写锁超时（{LOCK_WAIT_MAX}s），本次未写入", file=sys.stderr)
        sys.exit(2)

    try:
        records = json.load(open(raw_path, encoding="utf-8")) if os.path.exists(raw_path) else []
        by_key = {r.get("key"): r for r in records if r.get("key")}
        added = 0
        for it in incoming:
            if it["key"] not in by_key:
                added += 1
            by_key[it["key"]] = it

        merged = [by_key[k] for k in sorted(by_key)]
        tmp_path = raw_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, raw_path)   # 原子替换，避免半截文件
    finally:
        release_lock(lock_path)

    print(f"[done] {book}: 新增 {added} 条，现有 {len(merged)} 条"
          + (f"；跳过无 key 记录 {bad} 条" if bad else ""))


if __name__ == "__main__":
    main()
