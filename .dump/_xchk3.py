import os, re, glob
base = r"d:\2026\WB项目\明朝\papers_pilot\anthropology\paper"
out = []
labs, refs, cites = set(), set(), set()
for f in sorted(glob.glob(os.path.join(base, "sections", "*.tex"))):
    s = open(f, encoding="utf-8").read()
    t = os.path.basename(f)
    labs |= set(re.findall(r"\\label\{([^}]+)\}", s))
    refs |= set(re.findall(r"\\ref\{([^}]+)\}", s))
    cites |= set(re.findall(r"\\cite[a-z]*\{([^}]+)\}", s))
    if re.search(r"@@\w+@@", s):
        out.append("SENTINEL in " + t)
bib = open(os.path.join(base, "references.bib"), encoding="utf-8").read()
bibkeys = set(re.findall(r"@\w+\{([^,]+),", bib))
out.append("bib keys   : " + " ".join(sorted(bibkeys)))
out.append("cite keys  : " + " ".join(sorted(cites)))
out.append("refs       : " + " ".join(sorted(refs)))
out.append("labels     : " + " ".join(sorted(labs)))
out.append("MISSING ref->label : " + " ".join(sorted(refs - labs)) or "none")
out.append("cites not in bib   : " + (" ".join(sorted(cites - bibkeys)) or "none"))
out.append("bib not cited      : " + (" ".join(sorted(bibkeys - cites)) or "none"))
out.append("sentinel total     : %d" % sum(1 for f in glob.glob(os.path.join(base, "sections", "*.tex")) if re.search(r"@@\w+@@", open(f, encoding="utf-8").read())))
open(r"d:\2026\WB项目\明朝\.dump\_xchk3.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok")
