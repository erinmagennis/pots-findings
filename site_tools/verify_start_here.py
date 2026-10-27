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
  7. disagreement examples have a split with at least MIN_SIDE papers on each side (higher vs lower, or an effect vs no
     difference); entity names show with the display rule
  8. disagreement examples: direction-flip and null-vs-positive rows, numbers equal contradictions.json; null examples are
     primary studies from papers that are not reviews, never an entity that defines POTS, never one the same papers report
     an effect for, 2+ separate studies (or one randomized trial, worded so); barely studied examples are 2+ separate
     non-review studies and no more POTS papers mention the topic than the papers shown; topic and condition lists never cut a tie; MCAS carries its
     label note; quote-trace numbers equal verification_stats; year split counts add up
"""
import html as H, json, os, re, sys, urllib.parse
from collections import defaultdict

SELF = {"pots", "postural orthostatic tachycardia syndrome", "postural tachycardia syndrome"}
NONCOND = {"general", "multiple", "other patient group"}
MEASURED = {"physiological-measure", "gene/protein", "cell-type"}
MIN_SIDE = 3  # a shown disagreement needs at least this many papers on each side
PRIMARY = {"RCT", "cohort", "case-control", "cross-sectional"}
DEFINING = {"blood pressure", "systolic blood pressure", "diastolic blood pressure", "heart rate", "orthostatic heart rate"}
REVIEWS = {"review/narrative", "systematic-review/meta-analysis"}
LINKED = {"preprint_with_published_version", "published_version_of_preprint", "same_work_other_record", "update_of"}
SPLIT = 2021
TREAT_KINDS = {"chemical/metabolite", "procedural", "device", "other"}
MCAS_NOTE = "(this label also covers mast-cell lab studies)"


def cut_ties(items, n):  # items sorted, (key, count) pairs: keep n plus any further ties with the n-th
    out = items[:n]
    for it in items[n:]:
        if out and it[1] == out[-1][1]: out.append(it)
        else: break
    return out


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
    # topics: spelling variants of the same name count together (lower case, trailing period, trailing bracketed
    # abbreviation with 2+ capitals, plural "s"); different measures stay apart; shown under the member with most papers
    byn, nfn = defaultdict(set), defaultdict(int)
    for i in keep:
        name = d["e"][c["e"][i]]
        if name and name != "—":
            byn[name].add(c["p"][i]); nfn[name] += 1
    def vkey(nm):
        s = nm.strip().rstrip(".").strip()
        m = re.search(r"\s*\(([A-Za-z0-9\-/]{1,10})\)$", s)
        if m and sum(ch.isupper() for ch in m.group(1)) >= 2: s = s[:m.start()].strip()
        return s.lower()
    grp = defaultdict(set)
    for nm in byn: grp[vkey(nm)].add(nm)
    for k in sorted(grp):
        if k.endswith("s") and len(k) > 3 and k[:-1] in grp and k in grp: grp[k[:-1]] |= grp.pop(k)
    per, nf = {}, {}
    for k, mem in grp.items():
        if k in SELF: continue
        disp = sorted(mem, key=lambda nm: (-len(byn[nm]), nm.lower(), nm))[0]
        per[disp] = set().union(*(byn[nm] for nm in mem)); nf[disp] = sum(nfn[nm] for nm in mem)
    tops = cut_ties([(nm, len(s)) for nm, s in sorted(per.items(), key=lambda kv: (-len(kv[1]), -nf[kv[0]], vkey(kv[0])))], 6)
    tops = [(nm, per[nm]) for nm, _ in tops]
    for name, s in tops: want[f"topic_papers:{name}"] = len(s)
    co = defaultdict(set)
    for i, p in enumerate(c["p"]):
        if p in pp:
            lab = d["c"][c["c"][i]]
            if lab != "POTS" and lab not in NONCOND: co[lab].add(p)
    for lab, n_ in cut_ties([(lab, len(s)) for lab, s in sorted(co.items(), key=lambda kv: (-len(kv[1]), kv[0]))], 5): want[f"co_papers:{lab}"] = n_
    # ---- example picks, recomputed here without signals_rules.py (independent of the builders) ----
    pm_row = [str(r[pi]) for r in pap["rows"]]
    study = {}   # linked records (preprint and published version, same work, update) are one study
    def st_of(x):
        while study.setdefault(x, x) != x: x = study[x]
        return x
    for p_, v in sorted(fl.items()):
        for x in v:
            if x.get("f") in LINKED and x.get("lp"): study[st_of(str(p_))] = st_of(str(x["lp"]))
    # review papers: title says review / meta-analysis, or more than half of the paper's findings have a review study type
    ti = pap["fields"].index("title"); tot, rev = defaultdict(int), defaultdict(int)
    for i in range(fac["n"]):
        tot[c["p"][i]] += 1
        if d["st"][c["st"][i]] in REVIEWS: rev[c["p"][i]] += 1
    reviews = {pm_row[k] for k in range(len(pm_row)) if re.search(r"review|meta-analys", pap["rows"][k][ti] or "", re.I) or (tot[k] and 2 * rev[k] > tot[k])}
    # clear splits (disagreement examples): same entity name in lower case and condition; findings tagged vs-disease-state
    # whose comparator mentions "healthy"; no review-typed findings, no review papers; a paper on both sides counts on neither;
    # >= MIN_SIDE papers each side; no-condition labels left out. Best: bigger smaller side, more papers, name, condition.
    comp, quo, txt_all = [], [], []
    for s in range(fac["n_shards"]):
        dd_ = j(f"detail_{s:02d}.json"); comp += dd_["comp"]; quo += dd_["quote"]; txt_all += j(f"text_{s:02d}.json")["t"]
    animal = re.compile(r"\b(mice|mouse|murine|rats?|rodents?|rabbits?|porcine|pigs?|canine|dogs?|animal|zebrafish|primates?)\b", re.I)
    Hs, Ls, spell = defaultdict(set), defaultdict(set), defaultdict(lambda: defaultdict(int))
    for i in range(fac["n"]):
        dirn = d["d"][c["d"][i]]; e = d["e"][c["e"][i]]; lab = d["c"][c["c"][i]]; pm_ = pm_row[c["p"][i]]
        if d["dr"][c["dr"][i]] != "vs-disease-state" or dirn not in ("elevated", "depleted/reduced") or d["st"][c["st"][i]] in REVIEWS: continue
        if pm_ in bad_pm or pm_ in reviews or e in ("—", "") or lab in NONCOND | {"dysautonomia"} or "healthy" not in str(comp[i] or "").lower(): continue
        if d["st"][c["st"][i]] == "mechanistic/in-vitro" or d["tr"][c["tr"][i]] == "mechanistic/in-vitro": continue
        if animal.search(" ".join(str(x or "") for x in (txt_all[i], quo[i], comp[i]))): continue
        k = (e.lower(), lab); spell[k][e] += 1
        (Hs if dirn == "elevated" else Ls)[k].add(pm_)
    splits = []
    for k in Hs:
        hi, lo = len(Hs[k] - Ls[k]), len(Ls[k] - Hs[k])
        if hi >= MIN_SIDE and lo >= MIN_SIDE:
            splits.append(((-min(hi, lo), -(hi + lo), min(spell[k].items(), key=lambda kv: (-kv[1], kv[0]))[0].lower(), k[1]),
                           min(spell[k].items(), key=lambda kv: (-kv[1], kv[0]))[0], k[1], hi, lo))
    splits.sort()
    pots_splits = [x for x in splits if x[2] == "POTS"]   # a check only: the page reports the count, never an example
    if pots_splits: want["pots_clear_splits"] = len(pots_splits)
    contra_picks = []
    # null examples: primary-study rows (evidence tier), papers that are reviews left out, not POTS-defining, not POTS itself,
    # a treatment has a treatment kind, no paper also reports an effect for the entity; 2+ separate studies (else, treatments
    # only, one randomized trial, shown in words)
    idx = j("null_results.json"); F = idx["fields"]
    rows = [dict(zip(F, x)) for s in idx["shards"] for x in j(s["file"])["rows"]]
    if len(rows) != idx["n"]: want["__null_rows"] = (len(rows), idx["n"])
    effect = set()
    for i in keep:
        if d["d"][c["d"][i]] in ("elevated", "depleted/reduced") or d["nc"][c["nc"][i]] == "positive-effect":
            effect.add((pm_row[c["p"][i]], d["e"][c["e"][i]]))
    null_picks = []
    for cls in ("treatment null", "biomarker/mechanism null"):
        g, n, rct = defaultdict(set), defaultdict(int), set()
        for r in rows:
            e, pm_ = r["canonical_entity"], str(r["canonical_pmid"])
            if not (r["condition"] == "POTS" and r["null_class"] == cls and e and e not in contra_picks and pm_ not in bad_pm and pm_ not in reviews): continue
            if r["evidence_tier"] not in PRIMARY or e.lower() in SELF or e.lower() in DEFINING: continue
            if cls == "treatment null" and names.get(e) not in TREAT_KINDS: continue
            g[e].add(pm_); n[e] += 1
            if r["evidence_tier"] == "RCT": rct.add(e)
        okc = {e: s for e, s in g.items() if not any((p_, e) in effect for p_ in s)}
        ok = {e: s for e, s in okc.items() if len({st_of(p_) for p_ in s}) >= 2}
        if not ok and cls == "treatment null": ok = {e: s for e, s in okc.items() if e in rct}
        if ok:
            e = min(ok, key=lambda e: (-len({st_of(p_) for p_ in ok[e]}), -n[e], e.lower()))
            k = len({st_of(p_) for p_ in ok[e]}); null_picks.append((cls, e, k))
            if k > 1: want[f"null_studies:{cls}|{e}"] = k
    # barely studied: understudied rows, 2+ papers, not case-report-only, 2+ separate studies of which 2+ are not reviews,
    # and no more POTS papers mention the topic (every 5-letter stem in an entity name or the finding text) than shown
    texts = {}
    for s in range(fac["n_shards"]):
        t = j(f"text_{s:02d}.json"); texts.update({i: t["t"][i - t["start"]].lower() for i in range(t["start"], t["end"])})
    def stems(nm):
        s0 = nm.split(" (")[0].lower().replace("β", "beta")
        ws = [w[4:] if w.startswith("auto") and len(w) > 7 else w for w in re.findall(r"[a-z]{4,}", s0)]
        return sorted({w[:5] for w in ws}) or [s0.strip()]
    elow = [str(v).lower() for v in d["e"]]
    u = []
    for r in sorted(j("understudied.json")["rows"], key=lambda r: r["rank"]):
        e = r["canonical_entity"]; own = set(map(str, r.get("pmids") or []))
        if r["condition"] != "POTS" or r["n_papers"] < 2 or r["case_report_only"] or own & bad_pm or e not in d["e"]: continue
        if len({st_of(p_) for p_ in own}) < 2 or len({st_of(p_) for p_ in own if p_ not in reviews}) < 2: continue
        sm = stems(e)
        if len({pm_row[c["p"][i]] for i in keep if all(x in elow[c["e"][i]] for x in sm) or all(x in texts[i] for x in sm)}) > r["n_papers"]: continue
        ws = e.split(" (")[0].lower().split()   # every shorter run of 2+ words ("stroke volume" in "stroke volume index")
        subs = [" ".join(ws[a:b]) for a in range(len(ws)) for b in range(a + 2, len(ws) + 1) if b - a < len(ws)]
        if any(len({pm_row[c["p"][i]] for i in keep if ph in elow[c["e"][i]] or ph in texts[i]}) > r["n_papers"] for ph in subs): continue
        second = re.compile(r"et al|\bcit(?:ing|ed)\b|previous stud|prior stud|previously reported|a study by|reported by|earlier stud", re.I)
        ec = d["e"].index(e)
        fh = {st_of(pm_row[c["p"][i]]) for i in keep if c["e"][i] == ec and pm_row[c["p"][i]] in own and pm_row[c["p"][i]] not in reviews
              and not second.search(texts[i] + " " + str(quo[i] or ""))}
        if len(fh) < 2: continue   # 2+ separate studies with a first-hand finding (not retelling earlier work)
        u.append(r)
        if len(u) == 2: break
    for r in u: want[f"under_findings:{r['canonical_entity']}"], want[f"under_papers:{r['canonical_entity']}"] = r["n_findings"], r["n_papers"]
    C = meta["counts"]; want["year_min"], want["year_max"] = C["year_min"], C["year_max"]
    if "quote_trace_per_100" in C: want["trace_base"] = 100
    want["year_split"] = SPLIT
    for k in C:
        if k.startswith("papers_year_") and int(k.rsplit("_", 1)[1]) < SPLIT: want[f"year_old:{k.rsplit('_', 1)[1]}"] = int(k.rsplit("_", 1)[1])
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
    picks = {"contra": contra_picks, "pots_split": bool(pots_splits), "pots_split_entities": {e.lower() for _, e, _, _, _ in pots_splits},  "null": null_picks, "under": [r["canonical_entity"] for r in u]}
    return meta, fac, names, want, ex, len(bad_pm), excl, picks


def norm(v, key=""):
    if key in ("year_min", "year_max", "example_year", "year_split") or key.startswith("year_old:"): return str(v)
    return f"{v:,}" if isinstance(v, int) else str(v)


def check(site_dir):
    site = str(site_dir); f = []
    path = os.path.join(site, "start.html")
    if not os.path.exists(path): return ["start.html missing: run site_tools/build_start_here.py"]
    raw = open(path, encoding="utf-8").read()
    meta, fac, names, want, ex, n_bad, n_excl_flags, picks = expected(site)
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
    for k in got:   # no automatic disagreement example is shown (2026-10-27 reading: the passing cells were not genuine)
        if k.startswith(("split_hi:", "split_lo:", "contra_")): f.append(f"disagreement example shown: {k}")
    if re.search(r"\d[\d,]*</span>(<!--/n-->)? disagreements", raw): f.append("a total of possible splits is labelled as disagreements")
    # 8 rules shown on the page itself
    C, V = meta["counts"], meta.get("verification_stats") or {}
    if "quote_trace_checked" in C:
        if (C["quote_trace_checked"], C["quote_trace_found"]) != (V.get("trace_verifiable"), V.get("trace_found")): f.append("quote trace counts != verification_stats")
        if C.get("quote_trace_per_100") != round(100 * C["quote_trace_found"] / C["quote_trace_checked"]): f.append("quote_trace_per_100 != found / checked")
    yrs = {k: v for k, v in C.items() if k.startswith("papers_year_")}
    if C.get("papers_before_2021") != sum(v for k, v in yrs.items() if int(k[-4:]) < SPLIT) or C.get("papers_2021_on") != sum(v for k, v in yrs.items() if int(k[-4:]) >= SPLIT) \
            or C.get("papers_2021_on", 0) + C.get("papers_before_2021", 0) > C["papers"]:   # a few papers have no year
        f.append("year split counts do not match papers_year_* or exceed papers")
    if C.get("papers_fulltext", 0) + C.get("papers_abstract_only", 0) != C["papers"]: f.append("full text + abstract-only papers != papers")
    if 'href="condition?c=MCAS"' in raw and not re.search(r'href="condition\?c=MCAS">MCAS</a> <span class="kv">' + re.escape(MCAS_NOTE), raw):
        f.append("MCAS in the conditions list without its label note")
    if not picks["pots_split"] and "no topic has a clear split yet" not in raw:
        f.append("POTS has no clear split but the page does not say so")
    if "possible splits, for every condition" not in raw: f.append("the total link does not say possible splits")
    for e_raw, _ in re.findall(r'<li><b><a href="entity\?e=([^"]*)">[^<]*</a></b>, as a (treatment|marker)', raw):
        if urllib.parse.unquote(H.unescape(e_raw)).lower() in DEFINING: f.append(f"null example {e_raw} is part of how POTS is defined")
    for cls, e, k in picks["null"]:
        if k == 1 and not re.search(r'entity\?e=' + re.escape(H.escape(urllib.parse.quote(e, safe="-_.!~*'()"), quote=True)) + r'">[^<]*</a></b>, as a treatment for POTS: one randomized trial found', raw):
            f.append(f"one-trial null example {e} not worded as one randomized trial")
    # 4 no other digits in visible text
    body = raw[raw.index("<body>"):]
    body = re.sub(r"<!--(header|footer)-->.*?<!--/\1-->", " ", body, flags=re.S)   # shared chrome: apply_chrome.py writes it, verify_site_v12.py checks it
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
            frag, _, opt = u.fragment.partition("?")
            if pg == "about" and u.fragment not in about_ids: f.append(f"link {href}: no id {u.fragment!r} on About")
            if pg == "signals" and frag not in views: f.append(f"link {href}: no Signals view {frag!r}")
            if pg == "signals" and opt and f"opt==='{opt}'" not in open(pdsc, encoding="utf-8").read(): f.append(f"link {href}: Signals does not read option {opt!r}")
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
        "entity name not capitalised": lower_name,
        "MCAS note dropped": lambda s: s.replace(' <span class="kv">' + MCAS_NOTE + '</span>', "", 1),
        "unknown Signals option": lambda s: s.replace("signals#under?all", "signals#under?thin", 1),
        "one trial not worded as one": lambda s: s.replace("one randomized trial found", "one study found", 1),
        "automatic split example shown": lambda s: s.replace("so we do not show one as an example.", 'for example <span data-k="split_hi:TNF-alpha|ME_CFS">6</span>.', 1),
        "second-hand barely studied example": lambda s: re.sub(r'data-k="under_(findings|papers):[^"]*"', r'data-k="under_\1:testosterone"', s),
        "POTS no-split sentence dropped": lambda s: s.replace("no topic has a clear split yet", "no topic splits", 1),
        "total called disagreements": lambda s: s.replace("possible splits, for every condition", "disagreements, for every condition", 1),
        "barely studied example fails the sub-phrase guard": lambda s: re.sub(r'data-k="under_findings:[^"]*"', 'data-k="under_findings:Stroke volume index"', s, count=1),
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
