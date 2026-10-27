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
import html, json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signals_rules as SR  # noqa: E402  shared example picks (Start page and home cards)
from collections import Counter, defaultdict

SITE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
D = os.path.join(SITE, "data")
CANON = "https://pots.erinmagennis.com/start"

# ---- selection rules (documented here, mirrored in verify_start_here.py) ----
FOCUS = "POTS"                                         # condition label the page is about
SELF_NAMES = {"pots", "postural orthostatic tachycardia syndrome", "postural tachycardia syndrome"}  # the condition itself, not a topic
NOT_A_CONDITION = {"general", "multiple", "other patient group"}  # labels that name no condition
DIR_WORDS = {"elevated": "higher", "depleted/reduced": "lower", "no significant difference": "no clear difference"}
DIR_KEY = {"elevated": "up", "depleted/reduced": "down", "no significant difference": "nodiff"}  # data-k key slugs
TIER_ORDER = ["meta-analysis", "systematic-review/meta-analysis", "systematic review", "RCT", "cohort", "case-control", "cross-sectional"]
N_TOPICS, N_CONDS, N_EACH = 6, 5, 2
# example selection rules live in signals_rules.py (clear_splits, null_examples, under_examples)
SPLIT_YEAR = 2021   # "most were published in SPLIT_YEAR or later" (meta counts papers_2021_on / papers_before_2021)

CONDITION_LABELS = {  # mirrors site/js/labels.js CONDITION_LABELS
    "long_COVID": "Long COVID", "general": "Not condition-specific", "dysautonomia": "Dysautonomia", "ME_CFS": "ME/CFS",
    "EDS_hypermobility": "EDS and hypermobility", "MCAS": "MCAS", "fibromyalgia": "Fibromyalgia", "migraine": "Migraine",
    "multiple": "Several conditions", "POTS": "POTS", "IBS_gut": "IBS and gut", "small_fiber_neuropathy": "Small fiber neuropathy",
    "autism": "Autism", "other patient group": "Other patient group", "orthostatic_hypotension": "Orthostatic hypotension", "IBD_gut": "IBD"}
CONDITION_NOTES = {"MCAS": ' <span class="kv">(this label also covers mast-cell lab studies)</span>'}  # README: most MCAS-labelled papers study mast-cell biology
KIND_WORDS = {"physiological-measure": "a body measure", "gene/protein": "a gene or protein", "chemical/metabolite": "a chemical, hormone or drug",
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


ABBR = re.compile(r"\s*\(([A-Za-z0-9\-/]{1,10})\)$")   # trailing bracketed abbreviation, e.g. "(HR)", "(NE)"


def topic_key(name):
    """spelling-variant key: lower case, no trailing period, no trailing bracketed abbreviation (2+ capitals, no spaces)"""
    s = name.strip().rstrip(".").strip()
    m = ABBR.search(s)
    if m and sum(ch.isupper() for ch in m.group(1)) >= 2:
        s = s[:m.start()].strip()
    return s.lower()


def topic_groups(names):
    """{key: set of names}; a key ending in "s" folds into the same key without it when both exist (plural)"""
    g = defaultdict(set)
    for n in names:
        g[topic_key(n)].add(n)
    for k in sorted(g):
        if k.endswith("s") and len(k) > 3 and k[:-1] in g and k in g:
            g[k[:-1]] |= g.pop(k)
    return g


def with_ties(ordered, count, n):
    """first n items, plus any further items whose count ties with the n-th (so a cut never splits a tie)"""
    out = list(ordered[:n])
    for x in ordered[n:]:
        if out and count(x) == count(out[-1]): out.append(x)
        else: break
    return out


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

    # topics most studied in POTS findings: distinct papers per topic. The facet entity (site_entity) already groups spellings
    # that share a verified id or cross-tier canonical name; on top of that, names that are spelling variants of the SAME
    # name are counted together (topic_key: case, a trailing period, a trailing abbreviation in brackets such as "(HR)",
    # a plural "s"). Different measures (orthostatic heart rate, supine heart rate, heart rate variability) stay separate.
    # The topic is shown and linked under its member name with the most papers.
    byname, nfind = defaultdict(set), Counter()
    for i in rows:
        e = dic["e"][E[i]]
        if e in ("—", ""):
            continue
        byname[e].add(P[i]); nfind[e] += 1
    groups = topic_groups(byname)
    reach, gfind, shown_as = {}, Counter(), {}
    for k, members in groups.items():
        if k in SELF_NAMES:
            continue
        shown_as[k] = min(members, key=lambda n: (-len(byname[n]), n.lower(), n))
        reach[k] = set().union(*(byname[n] for n in members)); gfind[k] = sum(nfind[n] for n in members)
    order = with_ties(sorted(reach, key=lambda k: (-len(reach[k]), -gfind[k], k)), lambda k: len(reach[k]), N_TOPICS)
    topics = [(shown_as[k], len(reach[k]), gfind[k]) for k in order]

    # conditions studied in the same papers: papers with a POTS finding that also have a finding with another label
    co = defaultdict(set)
    for i in range(fac["n"]):
        if P[i] in focus_papers and P[i] not in ex_idx:
            c = dic["c"][Cc[i]]
            if c != FOCUS and c not in NOT_A_CONDITION:
                co[c].add(P[i])
    conds = with_ties(sorted(co, key=lambda c: (-len(co[c]), c)), lambda c: len(co[c]), N_CONDS)
    conds = [(c, len(co[c])) for c in conds]

    def kind_of(name, row_kind=None):
        return row_kind or (ents.get(name) or {}).get("kind")

    # the three example lists use the shared picks in signals_rules.py (one rule for the Start page and the home cards):
    # clear_splits (papers vs healthy people, no reviews, a paper on both sides counts on neither, >= MIN_SIDE each side),
    # null_examples (primary non-review studies, see its docstring), under_examples (clear barely studied topics)
    kinds = SR.entity_kinds(D)
    # clear_splits is a check only: the page says how many POTS cells pass it and never shows an automatic example
    n_pots_splits = sum(1 for x in SR.clear_splits(D) if x["c"] == FOCUS)
    nulls = SR.null_examples(D, FOCUS, kinds)
    under = [dict(r, _kind=kind_of(r["canonical_entity"], r.get("entity_kind"))) for r in SR.under_examples(D, FOCUS, n=N_EACH)]

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
    return meta, dict(n_focus_papers=len(focus_papers), topics=topics, conds=conds, n_pots_splits=n_pots_splits,
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
        f'<li><a href="condition?c={enc(c)}">{esc(cond_label(c))}</a>{CONDITION_NOTES.get(c, "")}<span class="start-count">{f.num(f"co_papers:{c}", n)} papers</span></li>'
        for c, n in F["conds"])

    if F["n_pots_splits"]:
        dis = (f'<p class="kv">Among papers that compare people with POTS to healthy people, {f.num("pots_clear_splits", F["n_pots_splits"])} '
               f'{"topic has" if F["n_pots_splits"] == 1 else "topics have"} a clear split: three or more such papers on each side. '
               'We do not pick one as an example, so read both sides in the list.</p>')
    else:
        dis = ('<p class="kv">Among papers that compare people with POTS to healthy people, no topic has a clear split yet: none has three such '
               'papers on each side. In related conditions, the splits we found mix different diseases, animal studies or different '
               'measures, so we do not show one as an example.</p>')

    nul = []
    for cls, e, nst, _ in F["nulls"]:
        what = "as a treatment for POTS" if cls == "treatment null" else "as a marker in POTS"
        res = "no effect" if cls == "treatment null" else "no difference"
        unit = "outcome" if cls == "treatment null" else "measure"
        who = "one randomized trial" if nst == 1 else f'{f.num(f"null_studies:{cls}|{e}", nst)} studies'
        nul.append(f'<li><b>{ent(e)}</b>, {what}: {who} found {res} on at least one {unit}.</li>')
    if not nul:
        nul.append('<li class="start-none">No clear example right now.</li>')

    und = []
    for r in F["under"]:
        e = r["canonical_entity"]; kw = KIND_WORDS.get(r["_kind"] or "")
        und.append(f'<li><b>{ent(e)}</b>{f" ({kw})" if kw else ""} in POTS: {f.num(f"under_findings:{e}", r["n_findings"])} findings '
                   f'from only {f.num(f"under_papers:{e}", r["n_papers"])} papers.</li>')
    if not und:
        und.append('<li class="start-none">No clear example right now.</li>')

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

    ver = (f'In a check of {m("quote_trace_checked")} quotes from the first four data packages, {m("quote_trace_found")} '
           f'were found in the paper. ') if "quote_trace_checked" in C else ""
    years = f'<span data-k="year_min">{C["year_min"]}</span> to <span data-k="year_max">{C["year_max"]}</span>'
    f.k["year_min"], f.k["year_max"] = C["year_min"], C["year_max"]
    f.k["trace_base"] = 100
    old_years = sorted(int(k.rsplit("_", 1)[1]) for k in C if k.startswith("papers_year_") and int(k.rsplit("_", 1)[1]) < SPLIT_YEAR)
    for y in old_years: f.k[f"year_old:{y}"] = y
    old_txt = " and ".join(f'<span data-k="year_old:{y}">{y}</span>' for y in old_years)
    f.k["year_split"] = SPLIT_YEAR
    yrs = (f'Most were published in <span data-k="year_split">{SPLIT_YEAR}</span> or later ({m("papers_2021_on")} papers). '
           + (f'Only {m("papers_before_2021")} are older, from {old_txt}.' if old_years else ""))
    def more(listed, total):  # say when the Signals table lists fewer rows than the total
        return f' (the table lists the {m(listed)} {"strongest" if listed == "contradictions" else "with the most findings"})' if C[listed] < C[total] else ""
    trace = (f'The quote should be copied from the paper. In our check, about {m("quote_trace_per_100")} in <span data-k="trace_base">100</span> quotes were found '
             f'in the paper, word for word or nearly. A few are the model\'s rewording, so check the paper.') if "quote_trace_per_100" in C else \
            "The quote should be copied from the paper. Some are the model's rewording, so check the paper."

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
    <nav class="nav-pill" id="primaryNav" aria-label="Primary navigation"><a href="search" class="">Search</a><a href="signals" class="">Signals</a><a href="connections" class="">Connections</a><a href="analyze" class="">Analyze</a><a href="ask" class="">Ask</a><a href="about" class="">About</a></nav>
  </div></header>'''

    body = f'''
<main><div class="wrap"><div class="about-grid start"><nav class="section-index" aria-label="Start here sections"><a href="#what">What this is</a><a href="#do">What you can do</a><a href="#most">Studied most</a><a href="#signals">Disagree, nothing, barely</a><a href="#read">Read a finding</a><a href="#limits">Limits</a></nav><div class="about-content">

<div class="page-intro" id="what">
  <h1>Start here</h1>
  <p class="lede">This site collects research findings about POTS, dysautonomia and related conditions. A language model read {m("papers")} papers
  found through PubMed and Europe PMC, published {years}. It read the full text of {m("papers_fulltext")} papers and only the abstract of the
  other {m("papers_abstract_only")}. It pulled out {m("findings")} short findings. Each finding comes with a quote from its paper and a link to it.
  No person has checked each finding yet. It is a map of what papers report, not medical advice.</p>
</div>

<section class="panel" id="do" aria-labelledby="do-h">
  <h2 id="do-h">What you can do here</h2>
  <ul class="start-do">
    <li><a href="search">Search</a> Look up a symptom, drug, test or gene and read the findings that name it.</li>
    <li><a href="connections">Connections</a> See a map of every paper, grouped by what it reports, and follow papers from topic to finding.</li>
    <li><a href="signals">Signals</a> See where papers disagree, what was tested and found nothing, and what has barely been studied.</li>
    <li><a href="analyze">Analyze</a> Count findings by year, condition or study type, and make your own chart.</li>
    <li><a href="ask">Ask</a> Ask a question in plain words and get an answer that cites the papers. You need your own AI key.</li>
  </ul>
</section>

<section class="panel" id="most" aria-labelledby="most-h">
  <h2 id="most-h">What the papers study most</h2>
  <div class="start-two">
    <div>
      <h3>Topics in POTS findings</h3>
      <p class="kv">Papers with a POTS finding that names the topic. Spellings of the same name are counted together. A related measure, such as orthostatic heart rate, is counted on its own.</p>
      <ol class="start-list">{topics}</ol>
    </div>
    <div>
      <h3>Conditions in the same papers</h3>
      <p class="kv">Of the {f.num("focus_papers", F["n_focus_papers"])} papers with a POTS finding, how many also have findings labelled with each condition.</p>
      <ol class="start-list">{conds}</ol>
    </div>
  </div>
  <p class="kv">A count shows how often something was studied. It does not show that it works, that it matters most, or that one condition causes another.</p>
</section>

<section class="panel" id="signals" aria-labelledby="signals-h">
  <h2 id="signals-h">Where the papers do not line up</h2>
  <div class="start-three">
    <div>
      <h3>Possible splits</h3>
      <p class="start-big"><a href="signals#contra">{m("contradictions_total")}</a></p>
      <p>possible splits, for every condition: papers that report the same thing higher in some and lower in others, or an effect in some and none in others.
      They count any result the model tagged as a comparison between groups. Many answer different questions, so read both sides.
      <a href="signals#contra">See all possible splits</a>{more("contradictions", "contradictions_total")}</p>
      {dis}
    </div>
    <div>
      <h3>Tested and found nothing</h3>
      <ul class="start-ex">{"".join(nul)}</ul>
      <p class="kv">A study that finds nothing may have been small, or used a different dose or group. It is still worth knowing.
      Examples here come from trials and other studies of patients, not case reports or reviews.
      <a href="signals#nulls">All {m("nulls")} null results, for every condition</a></p>
    </div>
    <div>
      <h3>Barely studied</h3>
      <ul class="start-ex">{"".join(und)}</ul>
      <p class="kv">With so few papers, a result could be chance. It could also be a lead that needs testing again.
      <a href="signals#under?all">All {m("understudied_total")} barely studied topics, for every condition</a>{more("understudied", "understudied_total")}</p>
    </div>
  </div>
  <p class="kv">These examples come from the Signals tables for findings labelled POTS, with extra checks so each one is a clear case. Retracted papers and correction notices are left out.</p>
</section>

<section class="panel" id="read" aria-labelledby="read-h">
  <h2 id="read-h">How to read a finding</h2>
  <div class="start-two">
    {excard}
    <ul class="start-how">
      <li>The first line is the model's short summary of one result from one paper.</li>
      <li>The tags show the topic, which way it went, the condition and the type of study.</li>
      <li>{trace}</li>
      <li>The link at the bottom opens the paper. Read it before you rely on a finding. It says who was studied, how many people, and how.</li>
    </ul>
  </div>
</section>

<section class="panel" id="limits" aria-labelledby="limits-h">
  <h2 id="limits-h">Limits</h2>
  <ul class="start-how">
    <li>A language model pulled out every finding, and it makes mistakes. {ver}No person has yet checked that each finding says what its paper found.</li>
    <li>Papers were found by searches of PubMed and Europe PMC. {yrs} If a finding is missing, its paper may not be in this set.</li>
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
<footer class="site"><div class="wrap"><span class="brand-footer">POTS &amp; Dysautonomia Findings</span><span>pots-findings {esc(meta["version"])} · {m("findings")} findings / {m("papers")} papers · data generated {esc(meta["generated_utc"])} · <a href="about#limits">Scope, methods and limits</a> · Not medical advice.</span></div></footer>
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
