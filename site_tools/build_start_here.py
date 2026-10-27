#!/usr/bin/env python3
"""build_start_here.py: write site/start.html, the plain-language "Start here" page, from site/data/*.

Usage:  python site_tools/build_start_here.py [site_dir]      (default: site)
        then  python site_tools/apply_counts.py site            (fills the <!--n:KEY--> markers; already filled here)
        and   python site_tools/verify_start_here.py [site_dir]

Every number on the page comes from the data at build time:
  * meta.json counts appear inside <!--n:KEY-->...<!--/n--> markers (same contract as apply_counts.py / verify_site_v12.py);
  * every other number sits in <span data-k="KEY">...</span>, and verify_start_here.py recomputes each KEY on its own.
Default exclusion matches the site: findings from papers whose paper flag has recommended_use (u) = "exclude"
(retracted papers, correction notices) are left out. Output is deterministic for the same data (no clock reads).
"""
import html, json, os, sys, urllib.parse
from collections import Counter, defaultdict

SITE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
D = os.path.join(SITE, "data")
CANON = "https://pots.erinmagennis.com/start"

# ---- selection rules (documented here, mirrored in verify_start_here.py) ----
FOCUS = "POTS"                                         # condition label the page is about
SELF_NAMES = {"pots", "postural orthostatic tachycardia syndrome", "postural tachycardia syndrome"}  # the condition itself, not a topic
NOT_A_CONDITION = {"general", "multiple", "other patient group"}  # labels that name no condition
MEASURED_KINDS = {"physiological-measure", "gene/protein", "cell-type"}  # kinds where "higher/lower" reads plainly
DIR_WORDS = {"elevated": "higher", "depleted/reduced": "lower", "no significant difference": "no clear difference"}
DIR_KEY = {"elevated": "up", "depleted/reduced": "down", "no significant difference": "nodiff"}  # data-k key slugs
TIER_ORDER = ["meta-analysis", "systematic-review/meta-analysis", "systematic review", "RCT", "cohort", "case-control", "cross-sectional"]
N_TOPICS, N_CONDS, N_EACH = 6, 5, 2
MIN_SIDE = 3  # a disagreement needs at least this many papers on each side

CONDITION_LABELS = {  # mirrors site/js/labels.js CONDITION_LABELS
    "long_COVID": "Long COVID", "general": "Not condition-specific", "dysautonomia": "Dysautonomia", "ME_CFS": "ME/CFS",
    "EDS_hypermobility": "EDS and hypermobility", "MCAS": "MCAS", "fibromyalgia": "Fibromyalgia", "migraine": "Migraine",
    "multiple": "Several conditions", "POTS": "POTS", "IBS_gut": "IBS and gut", "small_fiber_neuropathy": "Small fiber neuropathy",
    "autism": "Autism", "other patient group": "Other patient group", "orthostatic_hypotension": "Orthostatic hypotension", "IBD_gut": "IBD"}
KIND_WORDS = {"physiological-measure": "a body measure", "gene/protein": "a gene or protein", "chemical/metabolite": "a chemical or drug",
              "cell-type": "a cell type", "anatomical-structure": "a body part", "pathogen": "a germ", "device": "a device",
              "procedural": "a procedure"}


def load(name):
    with open(os.path.join(D, name), encoding="utf-8") as fh:
        return json.load(fh)


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def enc(s):  # same as JS encodeURIComponent
    return urllib.parse.quote(str(s), safe="-_.!~*'()")


def display(name):
    """visible entity name: first letter capitalised, unless it already starts with a capital or digit, or its first
    word looks like a gene or symbol (any capital or digit after the first letter: HLA-DQB1, mRNA, IL-6). Links keep the raw name."""
    first = name.split(" ")[0]
    if not name or not name[0].islower() or any(ch.isupper() or ch.isdigit() for ch in first[1:]):
        return name
    return name[0].upper() + name[1:]


def cond_label(c):
    return CONDITION_LABELS.get(c, str(c).replace("_", " "))


def fmt(n):
    return f"{n:,}"


class Facts:
    """collects every derived number; num() renders it in a data-k span. Numbers >= 1000 that are not
    meta.counts keys would break verify_site_v12's hand-typed-number check, so they stop the build."""
    def __init__(self):
        self.k = {}

    def num(self, key, n):
        if n >= 1000:
            raise SystemExit(f"build_start_here: derived number {key}={n} is >= 1000 and is not a meta.counts key; "
                             "rephrase the sentence or add the value to meta.counts and use an <!--n:KEY--> marker")
        self.k[key] = n
        return f'<span data-k="{esc(key)}">{fmt(n)}</span>'


def marker(meta, key):
    v = meta["counts"][key]
    return f"<!--n:{key}-->{fmt(v) if isinstance(v, int) else v}<!--/n-->"


def compute():
    meta = load("meta.json")
    fac = load("findings_facets.json")
    papers = load("papers.json")
    flags = load("paper_flags.json")["flags"]
    ents = {e["name"]: e for e in load("entities.json")["entities"]}
    cols, dic = fac["cols"], fac["dicts"]
    pmid_i = papers["fields"].index("pmid")
    pmids = [str(r[pmid_i]) for r in papers["rows"]]
    excluded = {pm for pm, fl in flags.items() if any(x.get("u") == "exclude" for x in fl)}
    ex_idx = {i for i, pm in enumerate(pmids) if pm in excluded}
    P, E, Cc, TR = cols["p"], cols["e"], cols["c"], cols["tr"]
    focus_code = dic["c"].index(FOCUS)
    rows = [i for i in range(fac["n"]) if P[i] not in ex_idx and Cc[i] == focus_code]
    focus_papers = {P[i] for i in rows}

    # topics most studied in POTS findings: distinct papers per named entity
    reach, nfind = defaultdict(set), Counter()
    for i in rows:
        e = dic["e"][E[i]]
        if e in ("—", "") or e.lower() in SELF_NAMES:
            continue
        reach[e].add(P[i]); nfind[e] += 1
    topics = sorted(reach, key=lambda e: (-len(reach[e]), -nfind[e], e.lower()))[:N_TOPICS]
    topics = [(e, len(reach[e]), nfind[e]) for e in topics]

    # conditions studied in the same papers: papers with a POTS finding that also have a finding with another label
    co = defaultdict(set)
    for i in range(fac["n"]):
        if P[i] in focus_papers and P[i] not in ex_idx:
            c = dic["c"][Cc[i]]
            if c != FOCUS and c not in NOT_A_CONDITION:
                co[c].add(P[i])
    conds = sorted(co, key=lambda c: (-len(co[c]), c))[:N_CONDS]
    conds = [(c, len(co[c])) for c in conds]

    def kind_of(name, row_kind=None):
        return row_kind or (ents.get(name) or {}).get("kind")

    def clean(r, keys):  # Signals tables already leave out exclude-flagged papers; re-check here
        return not any(str(p) in excluded for k in keys for p in (r.get(k) or []))

    # where studies disagree: real two-way splits. POTS direction-flip rows (higher vs lower), both sides >= MIN_SIDE papers,
    # on measured things (body measures, genes/proteins, cell types, chemicals that are not mostly studied as a treatment),
    # ranked by the smaller side, then total papers, then Signals rank. No-difference papers: distinct papers with a POTS
    # finding on the entity whose direction is "no significant difference" (same facet counting as the two sides).
    def treatment_share(code):
        ids = [i for i in rows if E[i] == code]
        return sum(dic["ft"][cols["ft"][i]] == "treatment/intervention" for i in ids) / max(1, len(ids))
    nodiff_code = dic["d"].index("no significant difference")
    best = {}
    for r in load("contradictions.json")["rows"]:
        e = r["canonical_entity"]
        if r["condition"] != FOCUS or r["conflict_type"] != "direction-flip" or not clean(r, ("pmids_A", "pmids_B")):
            continue
        if {r["side_A_direction"], r["side_B_direction"]} != {"elevated", "depleted/reduced"}:
            continue
        if min(r["n_papers_A"], r["n_papers_B"]) < MIN_SIDE or e not in dic["e"]:
            continue
        kind = kind_of(e, r.get("entity_kind")); code = dic["e"].index(e)
        if kind not in MEASURED_KINDS and not (kind == "chemical/metabolite" and treatment_share(code) <= 0.5):
            continue
        hi, lo = (r["n_papers_A"], r["n_papers_B"]) if r["side_A_direction"] == "elevated" else (r["n_papers_B"], r["n_papers_A"])
        key = (-min(hi, lo), -(hi + lo), r["rank"])
        if e not in best or key < best[e][0]:
            nd = len({P[i] for i in rows if E[i] == code and cols["d"][i] == nodiff_code})
            best[e] = (key, {"entity": e, "higher": hi, "lower": lo, "nodiff": nd})
    disagree = [x for _, x in sorted(best.values(), key=lambda x: x[0])][:N_EACH]

    # tested and found nothing: POTS null results, one treatment and one marker, most distinct papers
    idx = load("null_results.json")
    nul = []
    for sh in idx["shards"]:
        nul += [dict(zip(idx["fields"], x)) for x in load(sh["file"])["rows"]]
    nulls = []
    shown = {d["entity"] for d in disagree}   # an entity already in the disagree list would show a second, differently counted "no difference"
    for cls in ("treatment null", "biomarker/mechanism null"):
        g, gf = defaultdict(set), Counter()
        for r in nul:
            if r["condition"] == FOCUS and r["null_class"] == cls and r["canonical_entity"] and r["canonical_entity"] not in shown and str(r["canonical_pmid"]) not in excluded:
                g[r["canonical_entity"]].add(str(r["canonical_pmid"])); gf[r["canonical_entity"]] += 1
        if g:
            e = sorted(g, key=lambda e: (-len(g[e]), -gf[e], e.lower()))[0]
            nulls.append((cls, e, len(g[e]), gf[e]))

    # barely studied: POTS understudied rows with the Signals page defaults (thin, 2+ papers, not case-report-only), by rank
    us = load("understudied.json")
    under = [r for r in sorted(us["rows"], key=lambda r: r["rank"])
             if r["condition"] == FOCUS and r["is_thin"] and r["n_papers"] >= 2 and not r["case_report_only"] and clean(r, ("pmids",))][:N_EACH]
    under = [dict(r, _kind=kind_of(r["canonical_entity"], r.get("entity_kind"))) for r in under]

    # example finding: top topic, POTS label, strongest study type, has a quote, readable length, lowest row
    ex = None
    if topics:
        top = topics[0][0]; tcode = dic["e"].index(top)
        cand = [i for i in rows if E[i] == tcode]
        rank_t = {t: n for n, t in enumerate(TIER_ORDER)}
        cand.sort(key=lambda i: (rank_t.get(dic["tr"][TR[i]], 99), i))
        cache = {}
        for i in cand:
            s = i // fac["shard_rows"]
            if s not in cache:
                cache[s] = (load(f"text_{s:02d}.json"), load(f"detail_{s:02d}.json"))
            t, d = cache[s]
            text, quote = t["t"][i - t["start"]], d["quote"][i - d["start"]]
            if text and quote and 60 <= len(text) <= 240:
                p = dict(zip(papers["fields"], papers["rows"][P[i]]))
                ex = {"row": i, "text": text, "quote": quote, "entity": top, "tier": dic["tr"][TR[i]],
                      "dir": dic["d"][cols["d"][i]], "paper": p}
                break
    return meta, dict(n_focus_papers=len(focus_papers), topics=topics, conds=conds, disagree=disagree,
                      nulls=nulls, under=under, example=ex)


def render(meta, F):
    f = Facts(); C = meta["counts"]; V = meta.get("verification_stats", {})
    stamp = f'{meta["version"]} {meta["generated_utc"]}'
    m = lambda k: marker(meta, k)

    def ent(name):
        return f'<a href="entity?e={enc(name)}">{esc(display(name))}</a>'

    topics = "".join(
        f'<li>{ent(e)}<span class="start-count">{f.num(f"topic_papers:{e}", n)} papers</span></li>' for e, n, _ in F["topics"])
    conds = "".join(
        f'<li><a href="condition?c={enc(c)}">{esc(cond_label(c))}</a><span class="start-count">{f.num(f"co_papers:{c}", n)} papers</span></li>'
        for c, n in F["conds"])

    dis = []
    for x in F["disagree"]:
        e = x["entity"]
        nd = f', {f.num(f"contra_nodiff:{e}", x["nodiff"])} found no difference' if x["nodiff"] else ""
        dis.append(f'<li><b>{ent(e)}</b> in POTS: {f.num(f"contra_higher:{e}", x["higher"])} papers report higher, '
                   f'{f.num(f"contra_lower:{e}", x["lower"])} report lower{nd}.</li>')

    nul = []
    for cls, e, npap, nf in F["nulls"]:
        what = "as a treatment for POTS" if cls == "treatment null" else "as a marker in POTS"
        res = "no effect" if cls == "treatment null" else "no difference"
        nul.append(f'<li><b>{ent(e)}</b>, {what}: {f.num(f"null_findings:{cls}|{e}", nf)} findings from '
                   f'{f.num(f"null_papers:{cls}|{e}", npap)} papers report {res}.</li>')

    und = []
    for r in F["under"]:
        e = r["canonical_entity"]; kw = KIND_WORDS.get(r["_kind"] or "")
        und.append(f'<li><b>{ent(e)}</b>{f" ({kw})" if kw else ""} in POTS: {f.num(f"under_findings:{e}", r["n_findings"])} findings '
                   f'from only {f.num(f"under_papers:{e}", r["n_papers"])} papers.</li>')

    ex = F["example"]; excard = ""
    if ex:
        p = ex["paper"]; url = p.get("doi_url") or p.get("pubmed_url") or p.get("pmc_url")
        who = esc((p.get("first_author") or "Source paper").split(";")[0].strip()) + (" et al." if (p.get("author_count") or 0) > 1 or ";" in (p.get("first_author") or "") else "")
        cite = f'<a href="{esc(url)}" target="_blank" rel="noopener">{who}</a>' if url else who
        yr = f' (<span data-k="example_year">{int(p["year"])}</span>)' if p.get("year") else ""
        f.k["example_year"] = int(p["year"]) if p.get("year") else None
        dirw = DIR_WORDS.get(ex["dir"])
        tags = [f'<a class="tag ent" href="entity?e={enc(ex["entity"])}">{esc(display(ex["entity"]))}</a>']
        if dirw: tags.append(f'<span class="tag">{esc(dirw)}</span>')
        tags += [f'<a class="tag" href="condition?c={enc(FOCUS)}">{esc(cond_label(FOCUS))}</a>', f'<span class="tag tier">{esc(ex["tier"])}</span>']
        pm = (f' \u00b7 <a href="{esc(p["pubmed_url"])}" target="_blank" rel="noopener">PubMed</a>') if p.get("pubmed_url") else ""
        excard = (f'<figure class="card start-example"><p class="ftext">{esc(ex["text"])}</p>'
                  f'<div class="tags">{"".join(tags)}</div><blockquote class="quote">\u201c{esc(ex["quote"])}\u201d</blockquote>'
                  f'<figcaption class="cite">{cite}: <span class="jr">{esc(p.get("journal") or "")}</span>{yr}{pm}</figcaption></figure>')

    ver = (f'In a check of {f.num("sample_n", V["sample_n"])} findings, the quote was found word for word in the paper for '
           f'{f.num("sample_found", V["sample_found"])}. ') if V.get("sample_n") else ""
    years = f'<span data-k="year_min">{C["year_min"]}</span> to <span data-k="year_max">{C["year_max"]}</span>'
    f.k["year_min"], f.k["year_max"] = C["year_min"], C["year_max"]

    head = f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Start here: a plain guide to POTS research findings</title>
<meta name="description" content="New here? A plain-language guide to this index of POTS and dysautonomia research findings: what it holds, what the papers report most, where they disagree, and its limits.">
<link rel="canonical" href="{CANON}">
<meta name="pots-data-build" content="{esc(stamp)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32x32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
<meta name="theme-color" content="#f7f4ee">
<meta property="og:type" content="website">
<meta property="og:site_name" content="POTS &amp; Dysautonomia Literature Findings">
<meta property="og:title" content="Start here: a plain guide to POTS research findings">
<meta property="og:description" content="A plain-language guide to this index of POTS and dysautonomia research findings and its limits.">
<meta property="og:url" content="{CANON}">
<meta property="og:image" content="https://pots.erinmagennis.com/social-preview.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="POTS and Dysautonomia Literature Findings shown above an index of research entities, findings, evidence, and papers.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Start here: a plain guide to POTS research findings">
<meta name="twitter:description" content="A plain-language guide to this index of POTS and dysautonomia research findings and its limits.">
<meta name="twitter:image" content="https://pots.erinmagennis.com/social-preview.png">
<link rel="stylesheet" href="css/app-v2.css">
<link rel="stylesheet" href="css/start.css">
</head><body>
<!-- generated by site_tools/build_start_here.py from site/data; do not edit by hand -->
<header class="site"><div class="wrap">
    <a class="brand" href="/" aria-label="POTS and Dysautonomia Literature Project home"><span class="mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><b></b></span><span class="brand-lockup"><span>POTS &amp; Dysautonomia</span><span>Literature Project</span><small>Research findings, source papers, and connections</small></span></a>
    <button class="mobile-nav-toggle" id="mobileNavToggle" type="button" aria-expanded="false" aria-controls="primaryNav"><span aria-hidden="true">☰</span><span class="sr-only">Menu</span></button>
    <nav class="nav-pill" id="primaryNav" aria-label="Primary navigation"><a href="search" class="">Search</a><a href="discover" class="">Signals</a><a href="connections" class="">Connections</a><a href="builder" class="">Analyze</a><a href="about" class="">About</a><a href="chat" class="">Ask</a></nav>
    <div class="header-rail"><b>{m("findings")} findings</b>{m("papers")} papers · version {esc(meta["version"])}</div>
  </div></header>'''

    body = f'''
<main><div class="wrap"><div class="about-grid start"><nav class="section-index" aria-label="Start here sections"><a href="#what">What this is</a><a href="#do">What you can do</a><a href="#most">Studied most</a><a href="#signals">Disagree, nothing, barely</a><a href="#read">Read a finding</a><a href="#limits">Limits</a></nav><div class="about-content">

<div class="page-intro" id="what">
  <h1>Start here</h1>
  <p class="lede">This site collects research findings about POTS, dysautonomia and related conditions. A language model read {m("papers")} papers from PubMed,
  published {years}, and pulled out {m("findings")} short findings. Each finding comes with a quote from its paper and a link to it.
  No person has checked each finding yet. It is a map of what papers report, not medical advice.</p>
</div>

<section class="panel" id="do" aria-labelledby="do-h">
  <h2 id="do-h">What you can do here</h2>
  <ul class="start-do">
    <li><a href="search">Search</a> Look up a symptom, drug, test or gene and read the findings that name it.</li>
    <li><a href="connections">Connections</a> See a map of every paper, grouped by what it reports, and follow papers from topic to finding.</li>
    <li><a href="discover">Signals</a> See where papers disagree, what was tested and found nothing, and what has barely been studied.</li>
    <li><a href="builder">Analyze</a> Count findings by year, condition or study type, and make your own chart.</li>
    <li><a href="chat">Ask</a> Ask a question in plain words and get an answer that cites the papers. You need your own AI key.</li>
  </ul>
</section>

<section class="panel" id="most" aria-labelledby="most-h">
  <h2 id="most-h">What the papers study most</h2>
  <div class="start-two">
    <div>
      <h3>Topics in POTS findings</h3>
      <p class="kv">Number of papers with a POTS finding that names the topic.</p>
      <ol class="start-list">{topics}</ol>
    </div>
    <div>
      <h3>Conditions in the same papers</h3>
      <p class="kv">Of the {f.num("focus_papers", F["n_focus_papers"])} papers with a POTS finding, how many also report on each condition.</p>
      <ol class="start-list">{conds}</ol>
    </div>
  </div>
  <p class="kv">A count shows how often something was studied. It does not show that it works, that it matters most, or that one condition causes another.</p>
</section>

<section class="panel" id="signals" aria-labelledby="signals-h">
  <h2 id="signals-h">Where the papers do not line up</h2>
  <div class="start-three">
    <div>
      <h3>Where studies disagree</h3>
      <ul class="start-ex">{"".join(dis)}</ul>
      <p class="kv">Studies test different people in different ways. A split is a reason to read both sides. It does not prove either side wrong.
      <a href="discover#contra">All <!--n:contradictions_total-->{fmt(C["contradictions_total"])}<!--/n--> disagreements</a></p>
    </div>
    <div>
      <h3>Tested and found nothing</h3>
      <ul class="start-ex">{"".join(nul)}</ul>
      <p class="kv">A study that finds nothing may have been small, or used a different dose or group. It is still worth knowing.
      <a href="discover#nulls">All <!--n:nulls-->{fmt(C["nulls"])}<!--/n--> null results</a></p>
    </div>
    <div>
      <h3>Barely studied</h3>
      <ul class="start-ex">{"".join(und)}</ul>
      <p class="kv">With so few papers, a result could be chance. It could also be a lead that needs testing again.
      <a href="discover#under">All <!--n:understudied_total-->{fmt(C["understudied_total"])}<!--/n--> thin signals</a></p>
    </div>
  </div>
  <p class="kv">These lists use the same rules as the Signals page, for findings labelled POTS. Retracted papers and correction notices are left out.</p>
</section>

<section class="panel" id="read" aria-labelledby="read-h">
  <h2 id="read-h">How to read a finding</h2>
  <div class="start-two">
    {excard}
    <ul class="start-how">
      <li>The first line is the model's short summary of one result from one paper.</li>
      <li>The tags show the topic, which way it went, the condition and the type of study.</li>
      <li>The quote in italics is copied from the paper, so you can find the passage.</li>
      <li>The link at the bottom opens the paper. Read it before you rely on a finding. It says who was studied, how many people, and how.</li>
    </ul>
  </div>
</section>

<section class="panel" id="limits" aria-labelledby="limits-h">
  <h2 id="limits-h">Limits</h2>
  <ul class="start-how">
    <li>A language model pulled out every finding, and it makes mistakes. {ver}No person has yet checked that each finding says what its paper found.</li>
    <li>Papers were found by PubMed searches and published {years}. If a finding is missing, its paper may not be in this set.</li>
    <li>{m("flag_retracted")} retracted papers and {m("flag_erratum_notice")} correction notices are hidden by default. Their {m("excluded_findings")} findings are kept for the record but left out of the lists on this page and the Signals tables.</li>
    <li>Two topics in the same papers are studied together. That does not mean one causes the other.</li>
    <li>Nothing here is medical advice. Take questions about your own care to a clinician who knows you.</li>
  </ul>
  <p class="kv"><a href="about">More on methods and limits</a></p>
</section>

<p class="start-foot kv">Data version {esc(meta["version"])}, generated <span data-k="generated_utc">{esc(meta["generated_utc"])}</span>. This page is rebuilt from that data.
<a href="about#download">Download the data</a>.</p>
</div></div></div></main>
<div class="quiet-support"><div class="wrap"><strong>Grow the map</strong> Help make this public research index easier to extend, check, and reuse. <a href="about#connect">Collaborate with the project</a>.</div></div>
<footer class="site"><div class="wrap"><span class="brand-footer">POTS &amp; Dysautonomia Findings</span><span>pots-findings {esc(meta["version"])} · {m("findings")} findings / {m("papers")} papers · data generated {esc(meta["generated_utc"])} · <a href="about">Scope, methods and limitations</a>.</span></div></footer>
<script type="module" src="js/chrome.js"></script>
</body></html>
'''
    f.k["generated_utc"] = meta["generated_utc"]
    return head + body, f.k


def main():
    meta, F = compute()
    out, keys = render(meta, F)
    if "—" in out or "–" in out:
        raise SystemExit("build_start_here: em or en dash in output")
    path = os.path.join(SITE, "start.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {os.path.relpath(path)}: {len(keys)} derived values, stamp {meta['version']} {meta['generated_utc']}")


if __name__ == "__main__":
    main()
