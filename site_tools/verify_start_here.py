#!/usr/bin/env python3
"""verify_start_here.py: check site/start.html against site/data. check(site_dir) -> list of failure strings ([] = pass).

Checks
  1. build stamp: <meta name="pots-data-build"> equals meta.version + meta.generated_utc (page rebuilt for this data)
  2. every <!--n:KEY--> marker equals meta.counts (same rule as apply_counts.py)
  3. every <span data-k> value is recomputed here, independently of build_start_here.py, and the page shows exactly the
     expected set of keys (no missing, no extra items)
  4. no other digit appears in the visible page text (so no number is hand-typed); the example finding's text, quote and
     citation are matched to the data row instead
  5. every link resolves: pages exist, entity?e= names exist in entities.json, condition?c= labels exist in the facets,
     #anchors exist on the target page (About ids from about.html / page-about.js, Signals views from page-discover.js)
  6. no em dash or en dash anywhere in the file; no hand-typed number >= 1000 by verify_site_v12's own rule
Usage: python site_tools/verify_start_here.py [site_dir] [--self-test]
  7. disagreement examples have at least MIN_SIDE papers on each side; entity names show with the display rule
"""
import html as H, json, os, re, sys, urllib.parse
from collections import defaultdict

SELF = {"pots", "postural orthostatic tachycardia syndrome", "postural tachycardia syndrome"}
NONCOND = {"general", "multiple", "other patient group"}
MEASURED = {"physiological-measure", "gene/protein", "cell-type"}
MIN_SIDE = 3  # a shown disagreement needs at least this many papers on each side


def display(name):  # visible entity name rule (first letter up unless capital/digit start or gene-like first word)
    w = name.split(" ")[0]
    if not name or not name[0].islower() or any(ch.isupper() or ch.isdigit() for ch in w[1:]): return name
    return name[0].upper() + name[1:]
TIERS = ["meta-analysis", "systematic-review/meta-analysis", "systematic review", "RCT", "cohort", "case-control", "cross-sectional"]


def expected(site):
    j = lambda n: json.load(open(os.path.join(site, "data", n), encoding="utf-8"))
    meta, fac, pap, fl = j("meta.json"), j("findings_facets.json"), j("papers.json"), j("paper_flags.json")["flags"]
    names = {e["name"]: e.get("kind") for e in j("entities.json")["entities"]}
    bad_pm = {p for p, v in fl.items() if any(x.get("u") == "exclude" for x in v)}
    pi = pap["fields"].index("pmid")
    bad_row = {k for k, r in enumerate(pap["rows"]) if str(r[pi]) in bad_pm}
    c, d = fac["cols"], fac["dicts"]
    pots = d["c"].index("POTS")
    keep = [i for i, (p, cc) in enumerate(zip(c["p"], c["c"])) if cc == pots and p not in bad_row]
    want = {}
    pp = {c["p"][i] for i in keep}
    want["focus_papers"] = len(pp)
    per, nf = defaultdict(set), defaultdict(int)
    for i in keep:
        name = d["e"][c["e"][i]]
        if name and name != "—" and name.lower() not in SELF:
            per[name].add(c["p"][i]); nf[name] += 1
    tops = sorted(per.items(), key=lambda kv: (-len(kv[1]), -nf[kv[0]], kv[0].lower()))[:6]
    for name, s in tops: want[f"topic_papers:{name}"] = len(s)
    co = defaultdict(set)
    for i, p in enumerate(c["p"]):
        if p in pp:
            lab = d["c"][c["c"][i]]
            if lab != "POTS" and lab not in NONCOND: co[lab].add(p)
    for lab, s in sorted(co.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:5]: want[f"co_papers:{lab}"] = len(s)
    # disagreements: POTS direction flips (higher vs lower), each side >= MIN_SIDE papers, measured things or non-treatment
    # chemicals; ranked by the smaller side, then total, then rank. No-difference = distinct POTS papers with that direction.
    cand = {}
    for r in j("contradictions.json")["rows"]:
        e = r["canonical_entity"]
        if r["condition"] != "POTS" or r["conflict_type"] != "direction-flip": continue
        if sorted([r["side_A_direction"], r["side_B_direction"]]) != ["depleted/reduced", "elevated"]: continue
        if set(map(str, (r.get("pmids_A") or []) + (r.get("pmids_B") or []))) & bad_pm: continue
        up = r["n_papers_A"] if r["side_A_direction"] == "elevated" else r["n_papers_B"]
        dn = r["n_papers_B"] if r["side_A_direction"] == "elevated" else r["n_papers_A"]
        if up < MIN_SIDE or dn < MIN_SIDE or e not in d["e"]: continue
        kind = r.get("entity_kind") or names.get(e); ec = d["e"].index(e)
        if kind not in MEASURED:
            if kind != "chemical/metabolite": continue
            mine = [i for i in keep if c["e"][i] == ec]
            if sum(d["ft"][c["ft"][i]] == "treatment/intervention" for i in mine) > 0.5 * max(1, len(mine)): continue
        rk = (-min(up, dn), -(up + dn), r["rank"])
        if e in cand and cand[e][0] <= rk: continue
        nd = len({c["p"][i] for i in keep if c["e"][i] == ec and d["d"][c["d"][i]] == "no significant difference"})
        cand[e] = (rk, up, dn, nd)
    for e, (_, up, dn, nd) in sorted(cand.items(), key=lambda kv: kv[1][0])[:2]:
        want[f"contra_higher:{e}"], want[f"contra_lower:{e}"] = up, dn
        if nd: want[f"contra_nodiff:{e}"] = nd
    idx = j("null_results.json"); F = idx["fields"]
    rows = [dict(zip(F, x)) for s in idx["shards"] for x in j(s["file"])["rows"]]
    if len(rows) != idx["n"]: want["__null_rows"] = (len(rows), idx["n"])
    shown = {k.split(":", 1)[1] for k in want if k.startswith("contra_higher:")}   # null examples skip entities shown as disagreements
    for cls in ("treatment null", "biomarker/mechanism null"):
        g, n = defaultdict(set), defaultdict(int)
        for r in rows:
            if r["condition"] == "POTS" and r["null_class"] == cls and r["canonical_entity"] and r["canonical_entity"] not in shown and str(r["canonical_pmid"]) not in bad_pm:
                g[r["canonical_entity"]].add(str(r["canonical_pmid"])); n[r["canonical_entity"]] += 1
        if g:
            e = min(g, key=lambda e: (-len(g[e]), -n[e], e.lower()))
            want[f"null_findings:{cls}|{e}"], want[f"null_papers:{cls}|{e}"] = n[e], len(g[e])
    u = sorted(j("understudied.json")["rows"], key=lambda r: r["rank"])
    u = [r for r in u if r["condition"] == "POTS" and r["is_thin"] and r["n_papers"] >= 2 and not r["case_report_only"]
         and not set(map(str, r.get("pmids") or [])) & bad_pm][:2]
    for r in u: want[f"under_findings:{r['canonical_entity']}"], want[f"under_papers:{r['canonical_entity']}"] = r["n_findings"], r["n_papers"]
    V = meta.get("verification_stats") or {}
    if V.get("sample_n"): want["sample_n"], want["sample_found"] = V["sample_n"], V["sample_found"]
    C = meta["counts"]; want["year_min"], want["year_max"] = C["year_min"], C["year_max"]
    want["generated_utc"] = meta["generated_utc"]
    # example finding row (same rule as the build) for check 4
    ex = None
    if tops:
        code = d["e"].index(tops[0][0]); rk = {t: n for n, t in enumerate(TIERS)}
        for i in sorted((i for i in keep if c["e"][i] == code), key=lambda i: (rk.get(d["tr"][c["tr"][i]], 99), i)):
            s = i // fac["shard_rows"]; t = j(f"text_{s:02d}.json"); dd = j(f"detail_{s:02d}.json")
            tx, q = t["t"][i - t["start"]], dd["quote"][i - dd["start"]]
            if tx and q and 60 <= len(tx) <= 240:
                ex = {"text": tx, "quote": q, "paper": dict(zip(pap["fields"], pap["rows"][c["p"][i]]))}; break
    if ex and ex["paper"].get("year"): want["example_year"] = int(ex["paper"]["year"])
    excl = C.get("flag_retracted", 0) + C.get("flag_partially_retracted", 0) + C.get("flag_erratum_notice", 0)
    return meta, fac, names, want, ex, len(bad_pm), excl


def norm(v, key=""):
    if key in ("year_min", "year_max", "example_year"): return str(v)
    return f"{v:,}" if isinstance(v, int) else str(v)


def check(site_dir):
    site = str(site_dir); f = []
    path = os.path.join(site, "start.html")
    if not os.path.exists(path): return ["start.html missing: run site_tools/build_start_here.py"]
    raw = open(path, encoding="utf-8").read()
    meta, fac, names, want, ex, n_bad, n_excl_flags = expected(site)
    if n_bad != n_excl_flags:
        f.append(f"limits sentence names retracted + correction notices = {n_excl_flags}, but {n_bad} papers are exclude-flagged: reword it")
    # 1 stamp
    m = re.search(r'<meta name="pots-data-build" content="([^"]*)">', raw)
    stamp = f'{meta["version"]} {meta["generated_utc"]}'
    if not m or H.unescape(m.group(1)) != stamp: f.append(f"build stamp {m and m.group(1)!r} != meta {stamp!r}: rebuild the page")
    # 2 markers
    src = dict(fac["coverage"]); src.update(meta["counts"]); src["version"] = meta["version"]
    for k, v in re.findall(r"<!--n:([a-z_0-9]+)-->(.*?)<!--/n-->", raw, flags=re.S):
        if k not in src: f.append(f"marker {k}: no such meta key")
        elif v != norm(src[k]): f.append(f"marker {k}: page {v} != meta {norm(src[k])}")
    # 3 data-k values
    got = {H.unescape(k): H.unescape(v) for k, v in re.findall(r'<span data-k="([^"]*)">([^<]*)</span>', raw)}
    for k in sorted(set(want) | set(got)):
        if k not in got: f.append(f"missing on page: {k} = {want[k]}")
        elif k not in want: f.append(f"on page but not expected from data: {k} = {got[k]}")
        elif got[k] != norm(want[k], k): f.append(f"{k}: page {got[k]} != data {norm(want[k], k)}")
    for k, v in got.items():  # rule on the page itself, independent of the recompute
        if k.startswith(("contra_higher:", "contra_lower:")) and int(v.replace(",", "")) < MIN_SIDE:
            f.append(f"disagree example {k} has {v} papers on one side; each side needs at least {MIN_SIDE}")
    # 4 no other digits in visible text
    body = raw[raw.index("<body>"):]
    body = re.sub(r"<!--n:[a-z_0-9]+-->.*?<!--/n-->", " ", body, flags=re.S)
    body = re.sub(r'<span data-k="[^"]*">[^<]*</span>', " ", body)
    exm = re.search(r'<figure class="card start-example">(.*?)</figure>', body, flags=re.S)
    if ex:
        if not exm: f.append("example finding missing")
        else:
            blk = exm.group(1)
            if f'<p class="ftext">{H.escape(ex["text"], quote=True)}</p>' not in blk: f.append("example finding text does not match its data row")
            if H.escape(ex["quote"], quote=True) not in blk: f.append("example quote does not match its data row")
            url = ex["paper"].get("doi_url") or ex["paper"].get("pubmed_url") or ex["paper"].get("pmc_url")
            if url and f'href="{H.escape(url, quote=True)}"' not in blk: f.append("example citation link does not match its paper")
            body = body.replace(exm.group(0), " ")
    # entity names are data (checked against entities.json in check 5); drop link text that equals its entity
    body = re.sub(r'<a (?:class="[^"]*" )?href="entity\?e=([^"]*)">([^<]*)</a>',
                  lambda mm: " " if display(urllib.parse.unquote(H.unescape(mm.group(1)))) == H.unescape(mm.group(2)) else mm.group(0), body)
    for e_raw, shown in re.findall(r'href="entity\?e=([^"]*)">([^<]*)</a>', raw):
        e = urllib.parse.unquote(H.unescape(e_raw))
        if H.unescape(shown) != display(e): f.append(f"entity {e!r} shown as {H.unescape(shown)!r}, expected {display(e)!r}")
    text = H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<!--.*?-->", " ", re.sub(r"<script.*?</script>", " ", body, flags=re.S), flags=re.S)))
    text = text.replace(meta["generated_utc"], " ").replace(meta["version"], " ")
    for dgt in re.findall(r"\S*\d\S*", text): f.append(f"number not tied to data: {dgt!r}")
    # 5 links
    ids_here = set(re.findall(r'\sid="([^"]+)"', raw))
    about_ids = set(re.findall(r'\sid="([^"]+)"', open(os.path.join(site, "about.html"), encoding="utf-8").read()))
    pa = os.path.join(site, "js", "page-about.js")
    if os.path.exists(pa): about_ids |= set(re.findall(r'\sid="([^"]+)"', open(pa, encoding="utf-8").read()))
    pdsc = os.path.join(site, "js", "page-discover.js")
    views = set(re.findall(r"(\w+):view\w+", open(pdsc, encoding="utf-8").read())) if os.path.exists(pdsc) else set()
    conds = set(fac["dicts"]["c"])
    for href in sorted(set(H.unescape(h) for h in re.findall(r'href="([^"]*)"', raw))):
        if href.startswith(("http://", "https://", "mailto:")): continue
        u = urllib.parse.urlsplit(href); pg = u.path; q = urllib.parse.parse_qs(u.query)
        if pg == "":
            if u.fragment not in ids_here: f.append(f"link {href}: no id on this page")
            continue
        fp = os.path.join(site, "index.html" if pg == "/" else pg.lstrip("/"))
        if not os.path.exists(fp) and not os.path.exists(fp + ".html"): f.append(f"link {href}: no such page"); continue
        if pg == "entity" and q.get("e", [None])[0] not in names: f.append(f"link {href}: no such entity")
        if pg == "condition" and q.get("c", [None])[0] not in conds: f.append(f"link {href}: no such condition label")
        if u.fragment:
            if pg == "about" and u.fragment not in about_ids: f.append(f"link {href}: no id {u.fragment!r} on About")
            if pg == "discover" and u.fragment not in views: f.append(f"link {href}: no Signals view {u.fragment!r}")
    # 6 dashes and verify_site_v12's hand-typed number rule
    for ch, nm in (("—", "em dash"), ("–", "en dash"), ("&mdash;", "em dash entity"), ("&ndash;", "en dash entity")):
        if ch in raw: f.append(f"{nm} in start.html")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import verify_site_v12 as v12
        t = v12.strip_code_noise(raw, False)
        for mm in re.finditer(r"(?<![\w.\-(,])([1-9]\d{0,2}(?:,\d{3})+|\d{4,})(?![\w.\-])", t):
            v = mm.group(1)
            if v in v12.ALLOW or ("," not in v and 1900 <= int(v) <= 2099): continue
            f.append(f"hand-typed number by verify_site_v12 rule: {v}")
    except ImportError as e:
        f.append(f"could not import verify_site_v12 for the numbers rule: {e}")
    return f


def self_test(site):
    """plant one fault per rule in a copy of start.html (other files symlinked) and require each to be caught"""
    import shutil, tempfile
    src = open(os.path.join(site, "start.html"), encoding="utf-8").read()
    def first_span(prefix):
        return re.search(r'(<span data-k="' + re.escape(prefix) + r'[^"]*">)([^<]*)(</span>)', src)
    def low_side(s):
        m = first_span("contra_lower:"); return s.replace(m.group(0), m.group(1) + "2" + m.group(3), 1)
    def lower_name(s):
        m = re.search(r'(href="entity\?e=[^"]*">)([A-Z][a-z][^<]*)(</a>)', s)
        return s.replace(m.group(0), m.group(1) + m.group(2)[0].lower() + m.group(2)[1:] + m.group(3), 1)
    cases = {
        "changed count": lambda s: s.replace(first_span("topic_papers:").group(0), first_span("topic_papers:").group(1) + "999" + first_span("topic_papers:").group(3), 1),
        "hand-typed number": lambda s: s.replace("<h1>Start here</h1>", "<h1>Start here 42</h1>"),
        "stale stamp": lambda s: re.sub(r'(name="pots-data-build" content=")[^"]*', r"\1v0 2000-01-01", s),
        "bad entity link": lambda s: s.replace('href="entity?e=', 'href="entity?e=zz', 1),
        "bad anchor": lambda s: s.replace("about#download", "about#nowhere"),
        "em dash": lambda s: s.replace("Limits</h2>", "Limits \u2014</h2>"),
        "stale marker": lambda s: re.sub(r"(<!--n:nulls-->)[^<]*", r"\g<1>1", s),
        "dropped item": lambda s: re.sub(r'<li><a href="condition\?c=[^"]*">.*?</li>', "", s, count=1),
        "disagree side below 3": low_side,
        "entity name not capitalised": lower_name,
    }
    tmp = tempfile.mkdtemp(); ok = True
    try:
        for x in os.listdir(site):
            if x != "start.html": os.symlink(os.path.abspath(os.path.join(site, x)), os.path.join(tmp, x))
        for name, fn in cases.items():
            planted = fn(src)
            if planted == src: print("SELF-TEST could not plant:", name); ok = False; continue
            open(os.path.join(tmp, "start.html"), "w", encoding="utf-8").write(planted)
            got = check(tmp); print(f"self-test {name}: {'caught' if got else 'MISSED'} {got[:1]}"); ok &= bool(got)
    finally:
        shutil.rmtree(tmp)
    return ok


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--self-test"]
    site = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
    if "--self-test" in sys.argv:
        good = self_test(site); print("self-test:", "PASS" if good else "FAIL"); sys.exit(0 if good else 1)
    fails = check(site)
    for x in fails: print("FAIL", x)
    print("verify_start_here:", "PASS" if not fails else f"{len(fails)} failure(s)")
    sys.exit(1 if fails else 0)
