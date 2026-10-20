import re, os, io

ROOT = r"D:/2026/WB项目/明朝/papers_pilot/narrative"
sec = os.path.join(ROOT, "paper", "sections")

issues = []
allref = set()
for fn in sorted(os.listdir(sec)):
    p = os.path.join(sec, fn)
    s = io.open(p, encoding="utf-8").read()
    if "@@" in s:
        issues.append("%s 残留 @@ 哨兵" % fn)
    n = s.count("\\item")
    # 统计连续两个 \item
    if re.search(r"\\item\s*\\item", s):
        issues.append("%s 双 \\item" % fn)
    for m in re.finditer(r"\\ref\{([^}]*)\}", s):
        allref.add(m.group(1))
    for m in re.finditer(r"\\ref\{([^}]*)\}", s):
        pass
    # 乱码特征
    if "\ufffd" in s:
        issues.append("%s 含替换字符" % fn)

BODY = []
for f in os.listdir(sec):
    BODY.append(io.open(os.path.join(sec, f), encoding="utf-8").read())
main = io.open(os.path.join(ROOT, "paper", "main.tex"), encoding="utf-8").read()
if "@@" in main:
    issues.append("main.tex 残留 @@")
if "?" in main and "??" in main:
    issues.append("main.tex 含 ?? ref")
mainrefs = set(re.findall(r"\\ref\{([^}]*)\}", main)) | set(re.findall(r"\\ref\{([^}]*)\}", "".join(BODY)))

# labels
labels = set(re.findall(r"\\label\{([^}]*)\}", main + "".join(BODY)))
dangling = sorted(mainrefs - labels)

# 双反斜杠数学
dbl = []
for f in os.listdir(sec):
    s = io.open(os.path.join(sec, f), encoding="utf-8").read()
    for m in re.finditer(r"\\+\\[A-Za-z]+", s):
        if m.group(0).startswith("\\\\"):
            dbl.append("%s: %s" % (f, m.group(0)))

print("labels      :", sorted(labels))
print("refs        :", sorted(mainrefs))
print("悬空 ref    :", dangling if dangling else "无")
print("双反斜杠命令 :", dbl if dbl else "无")
print("问题        :", issues if issues else "无")
