import json, re
html = open("index.html", encoding="utf-8").read()
m = html.find("const DATA=")
start = m + len("const DATA=")
end = html.rfind("</script>")
js = html[start:end].strip()
if js.endswith(";"):
    js = js[:-1]
DATA = json.JSONDecoder().raw_decode(js)[0]

def show(n):
    c = next((x for x in DATA["characters"] if x["name"] == n), None)
    if not c:
        print(n, "=> NOT FOUND"); return
    print("\n=== %s  relations(%d) ===" % (n, len(c["relations"])))
    for r in c["relations"][:6]:
        print("  dir=%s other=%s rel=%s ok=%s" % (r.get("dir"), r.get("other"), r.get("rel"), "·" not in str(r.get("rel"))))

for n in ["丁普郎","俞通海","傅友德","朱元璋"]:
    show(n)

net = DATA["visualizations"]["relationNetwork"]["byName"].get("朱元璋")
if net:
    print("\n=== 朱元璋 ego neighbors(%d) ===" % len(net["neighbors"]))
    for nb in net["neighbors"][:8]:
        print("  %s dir=%s keyRel=%s cat=%s" % (nb["name"], nb["direction"], nb.get("relation"), nb["category"]))

bad = 0
for name, g in DATA["visualizations"]["relationNetwork"]["byName"].items():
    for nb in g["neighbors"]:
        if nb.get("relation") and re.search(r"(主动|反向)·", nb["relation"]):
            bad += 1
print("\nego edges with 主动/反向 prefix:", bad)
print("total characters:", len(DATA["characters"]), "relations:", len(DATA["relations"]))
