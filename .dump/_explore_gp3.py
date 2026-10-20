# -*- coding: utf-8 -*-
import sys, json, collections
sys.path.insert(0, r"D:\2026\WB项目\明朝\papers_pilot\_lib")
import mingdata as md

chars = md.characters()
rels = md.relations()
evs = md.events()
print("counts", len(chars), len(rels), len(evs))

print("\n-- sample character --")
for c in chars[:3]:
    print(json.dumps(c, ensure_ascii=False)[:600])

print("\n-- sample relation --")
for r in rels[:5]:
    print(json.dumps(r, ensure_ascii=False)[:400])

print("\n-- relation categories --")
for x in md.relation_categories():
    print(x)

print("\n-- relation keys --")
ks = collections.Counter()
for r in rels:
    ks[tuple(sorted(r.keys()))] += 1
for k, v in ks.most_common():
    print(v, k)

print("\n-- character keys --")
ks = collections.Counter()
for c in chars:
    ks[tuple(sorted(c.keys()))] += 1
for k, v in ks.most_common():
    print(v, k)

print("\n-- role values sample --")
roles = collections.Counter()
for c in chars:
    r = c.get("role")
    roles[str(r)] += 1
print(len(roles))
for k, v in roles.most_common(40):
    print(v, repr(k[:60]))

print("\n-- event sample --")
for e in evs[:5]:
    print(json.dumps(e, ensure_ascii=False)[:400])
