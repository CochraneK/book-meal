with open('src/generate_report.py', encoding='utf-8') as f:
    lines = f.readlines()
for num in (1106, 1169):
    ln = lines[num-1]
    print("===== line", num, "=====")
    for tok in ['network-link', "item.direction==='反向'", 'esc(item.category) ·', '同章另有', "item.relatedEventCount", "item.status==='已定位'", 'class="status']:
        i = ln.find(tok)
        if i >= 0:
            print("[" + tok + "] ->", repr(ln[i:i+95]))
