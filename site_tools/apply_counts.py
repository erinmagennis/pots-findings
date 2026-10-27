#!/usr/bin/env python3
"""apply_counts.py — fill <!--n:KEY-->…<!--/n--> markers in static HTML from site/data/meta.json (counts, then facets.coverage).
Run after every projection build so no count in static copy is ever typed by hand."""
import json, re, sys, glob, os
site = sys.argv[1]; meta = json.load(open(f"{site}/data/meta.json")); cov = json.load(open(f"{site}/data/findings_facets.json"))["coverage"]
src = dict(cov); src.update(meta["counts"]); src["version"] = meta["version"]
def fmt(v): return f"{v:,}" if isinstance(v, int) else str(v)
n = 0
extra = sys.argv[2:]
for p in glob.glob(f"{site}/*.html") + extra:
    s = open(p, encoding="utf-8").read()
    def rep(m):
        k = m.group(1)
        if k not in src: raise SystemExit(f"{os.path.basename(p)}: no value for marker {k}")
        return f"<!--n:{k}-->{fmt(src[k])}<!--/n-->"
    s2 = re.sub(r"<!--n:([a-z_0-9]+)-->.*?<!--/n-->", rep, s, flags=re.S)
    # attributes cannot hold comment markers (search engines would read them), so a tag carries a template instead:
    # data-n-content="Search {findings} findings" and apply_counts writes the filled text into content="..."
    def fill_attr(m):
        tpl = m.group(1)
        for k in re.findall(r"[{]([a-z_0-9]+)[}]", tpl):
            if k not in src: raise SystemExit(f"{os.path.basename(p)}: no value for template key {k}")
        return f'data-n-content="{tpl}" content="{re.sub(r"[{]([a-z_0-9]+)[}]", lambda x: fmt(src[x.group(1)]), tpl)}"'
    s2 = re.sub(r'data-n-content="([^"]*)" content="[^"]*"', fill_attr, s2)
    if s2 != s: open(p, "w", encoding="utf-8").write(s2); n += 1
print("files filled:", n)
