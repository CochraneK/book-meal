import sys, json
sys.stdout.reconfigure(encoding="utf-8")
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))


def fmt(o, ind=0):
    pad = "  " * ind
    if isinstance(o, dict):
        out = []
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                out.append("%s%s:\n%s" % (pad, k, fmt(v, ind + 1)))
            else:
                out.append("%s%s = %s" % (pad, k, v))
        return "\n".join(out)
    if isinstance(o, list):
        out = []
        for i, v in enumerate(o):
            if isinstance(v, (dict, list)):
                out.append("%s[%d]:\n%s" % (pad, i, fmt(v, ind + 1)))
            else:
                out.append("%s[%d] = %s" % (pad, i, v))
        return "\n".join(out)
    return pad + str(o)


print(fmt(d))
