"""signals_rules.py: shared counting rules so a fact shows the same number on every page.

Disagreement rule (same as contradictions.json "rule", build_v12_projection.py): only findings the model tagged as a
comparison between groups count, i.e. facet `dr` (direction_reference, typos normalised) == "vs-disease-state".  That tag
covers people with vs without the condition and also comparisons with another patient group or a subgroup; no person has
checked the tags.  A change after a treatment (vs-intervention) or a finding with no reference (not-applicable) is never a
disagreement.
Higher / lower papers for an entity in a condition: the entity name as stored in findings_facets (no merging of spellings),
the condition label, vs-disease-state findings only, distinct papers per side, side "higher" = direction "elevated", side
"lower" = "depleted/reduced", findings from exclude-flagged papers left out. No-difference papers: distinct papers with a
vs-disease-state finding on the same entity and condition whose direction is "no significant difference" or whose
null_or_failed_result starts with "null" (the null side of contradictions.json), same exclusion.
Checked against every direction-flip row of contradictions.json by verify_home.py.
A disagreement (direction flip) also needs at least 2 distinct papers with vs-disease-state findings for that entity and
condition, as build_v12_projection.py does: one paper reporting both directions is not a disagreement between studies. Pages that list
flips apply this (build_connections_data.py; contra_flip_total in meta.json counts the same set).

Example picks shared by the Start page (build_start_here.py) and the home "What stands out" cards (build_home_data.py), so
one rule chooses every example; verify_start_here.py recomputes them on its own and verify_home.py compares the home cards:
  clear_splits     the disagreement examples shown on the Start page and the home card: same entity (site entity name,
                   lower case) and condition label; only findings tagged vs-disease-state whose comparator mentions
                   "healthy"; findings with a review study type and papers that are reviews (review_papers) left out; a
                   paper on both sides counts on neither; at least MIN_SIDE papers higher and MIN_SIDE lower; labels that
                   name no condition (general, multiple, other patient group) left out; exclude-flagged papers out.
                   Ranked by the smaller side, then both sides together, then name.
  null_examples    POTS null results from primary studies (evidence tier RCT / cohort / case-control / cross-sectional),
                   papers that are reviews left out (review_papers), a treatment example has a treatment kind
                   (TREATMENT_KINDS, so an outcome such as supine heart rate is not one), never an entity that defines
                   POTS or names POTS, never
                   one whose papers also report an effect for it; at least 2 separate studies (linked records are one). If no
                   treatment qualifies, one randomized trial may be shown, worded as one trial.
  under_examples   understudied rows with 2+ papers, not case-report-only, 2+ separate non-review studies, and no more
                   POTS papers mentioning the topic (topic_stems, in any entity name or finding text) than the papers shown,
                   and no contiguous sub-phrase of 2+ words of the name (e.g. "stroke volume" in "stroke volume index")
                   mentioned, as plain lower-case text in an entity name or finding text, by more POTS papers than shown.
"""
import json
from pathlib import Path

import numpy as np

# kinds where "higher/lower" reads plainly; same set and rule as build_start_here.py picks disagreement examples
MEASURED_KINDS = {'physiological-measure', 'gene/protein', 'cell-type'}
TREATMENT_SHARE_MAX = 0.5   # a chemical/metabolite counts as measured only when at most half its findings are treatment findings

HIGHER, LOWER, NODIFF = 'elevated', 'depleted/reduced', 'no significant difference'
DISEASE_REF = 'vs-disease-state'   # facet `dr`: the only direction_reference that counts for higher / lower / no difference


def null_side_mask(dicts, cols):
    """findings on the no-difference side of contradictions.json: direction "no significant difference" or a null flag"""
    nd = dicts['d'].index(NODIFF) if NODIFF in dicts['d'] else -1
    null_codes = [i for i, v in enumerate(dicts['nc']) if str(v).startswith('null')]
    return (np.asarray(cols['d']) == nd) | np.isin(np.asarray(cols['nc']), null_codes)


def disease_ref_mask(fac):
    """numpy bool mask over findings: True where facet `dr` is vs-disease-state (the disagreement rule)."""
    if 'dr' not in fac['dicts']:
        raise SystemExit('findings_facets.json has no `dr` facet (direction_reference): rebuild with build_v12_projection.py')
    code = fac['dicts']['dr'].index(DISEASE_REF) if DISEASE_REF in fac['dicts']['dr'] else -1
    return np.asarray(fac['cols']['dr']) == code


def excluded_pmids(data_dir):
    fl = json.load(open(Path(data_dir) / 'paper_flags.json'))['flags']
    return {str(pm) for pm, xs in fl.items() if any(x.get('u') == 'exclude' for x in xs)}


def display(name):
    """visible entity name: first letter capitalised, unless it already starts with a capital or digit, or its first
    word looks like a gene or symbol (any capital or digit after the first letter: HLA-DQB1, mRNA, IL-6). Links keep the
    raw name. Same rule as build_start_here.display and displayName() in site/js/home-v2.js."""
    first = name.split(' ')[0] if name else ''
    if not name or not name[0].islower() or any(ch.isupper() or ch.isdigit() for ch in first[1:]):
        return name
    return name[0].upper() + name[1:]


class Facets:
    """findings_facets columns as numpy arrays, plus a keep mask (False for findings of exclude-flagged papers)."""
    def __init__(self, data_dir):
        data = Path(data_dir)
        fac = json.load(open(data / 'findings_facets.json'))
        self.n = fac['n']; self.D = fac['dicts']
        self.cols = {k: np.asarray(v) for k, v in fac['cols'].items() if k in ('e', 'c', 'd', 'p', 'ft', 'nc')}
        self.pmids = [str(r[0]) for r in json.load(open(data / 'papers.json'))['rows']]
        self.excluded = excluded_pmids(data)
        self.keep = ~np.array([pm in self.excluded for pm in self.pmids])[self.cols['p']]
        self.ref = disease_ref_mask(fac)   # vs-disease-state findings: the only ones counted by tally()
        self._d = {w: (self.D['d'].index(w) if w in self.D['d'] else -1) for w in (HIGHER, LOWER, NODIFF)}

    def tally(self, entity, cond):
        """{'e','c','up','dn','nu'}: distinct papers higher / lower / no difference for entity in cond (vs-disease-state only)."""
        D, C = self.D, self.cols
        e = D['e'].index(entity) if entity in D['e'] else -1
        c = D['c'].index(cond) if cond in D['c'] else -1
        base = self.keep & self.ref & (C['e'] == e) & (C['c'] == c)
        n = lambda w: len(set(C['p'][base & (C['d'] == self._d[w])].tolist()))
        nu = len(set(C['p'][base & null_side_mask(self.D, self.cols)].tolist()))
        return {'e': entity, 'c': cond, 'up': n(HIGHER), 'dn': n(LOWER), 'nu': nu}

    def treatment_share(self, entity, cond):
        """share of the entity's findings in cond (exclude-flagged papers out) that are treatment/intervention findings"""
        D, C = self.D, self.cols
        e = D['e'].index(entity) if entity in D['e'] else -1
        c = D['c'].index(cond) if cond in D['c'] else -1
        t = D['ft'].index('treatment/intervention') if 'treatment/intervention' in D['ft'] else -1
        base = self.keep & (C['e'] == e) & (C['c'] == c)
        return float((base & (C['ft'] == t)).sum()) / max(1, int(base.sum()))


def entity_kinds(data_dir):
    return {e['name']: e.get('kind') for e in json.load(open(Path(data_dir) / 'entities.json'))['entities']}


def is_measured(F, kinds, entity, cond='POTS', row_kind=None):
    """build_start_here.py rule: kind from the contradictions row if given, else entities.json; measured kinds pass,
    chemical/metabolite passes when at most half of its findings in cond are treatment/intervention findings."""
    kind = row_kind or kinds.get(entity)
    if kind in MEASURED_KINDS: return True
    return kind == 'chemical/metabolite' and F.treatment_share(entity, cond) <= TREATMENT_SHARE_MAX


def flip_sides(row):
    """(higher, lower) papers from a contradictions.json direction-flip row."""
    a, b = row['n_papers_A'], row['n_papers_B']
    return (a, b) if row['side_A_direction'] == HIGHER else (b, a)


# ---------------- example picks (Start page and home cards) ----------------
MIN_SIDE = 3
PRIMARY_TIERS = {'RCT', 'cohort', 'case-control', 'cross-sectional'}
DEFINING = {'blood pressure', 'systolic blood pressure', 'diastolic blood pressure', 'heart rate', 'orthostatic heart rate'}
SELF_NAMES = {'pots', 'postural orthostatic tachycardia syndrome', 'postural tachycardia syndrome'}
TREATMENT_KINDS = {'chemical/metabolite', 'procedural', 'device', 'other'}  # kinds a treatment example may have
REVIEW_TYPES = {'review/narrative', 'systematic-review/meta-analysis'}
LINKED_FLAGS = {'preprint_with_published_version', 'published_version_of_preprint', 'same_work_other_record', 'update_of'}
import re as _re
REVIEW_TITLE = _re.compile(r'review|meta-analys', _re.I)


class Linked:
    """union of PubMed records that are one study (preprint and published version, same work, update)"""
    def __init__(self, data_dir):
        self.root = {}
        fl = json.load(open(Path(data_dir) / 'paper_flags.json'))['flags']
        for pm, xs in sorted(fl.items()):
            for x in xs:
                if x.get('f') in LINKED_FLAGS and x.get('lp'): self.root[self.find(str(pm))] = self.find(str(x['lp']))

    def find(self, x):
        while self.root.setdefault(x, x) != x: x = self.root[x]
        return x


def review_papers(data_dir):
    """pmids of papers that are reviews: title says review or meta-analysis, or most of the paper's findings have a review
    study type (the per-finding evidence tier is not used: a review reporting a trial carries the trial's tier)."""
    data = Path(data_dir); fac = json.load(open(data / 'findings_facets.json')); pj = json.load(open(data / 'papers.json'))
    ti = pj['fields'].index('title'); pms = [str(r[0]) for r in pj['rows']]
    st_rev = np.isin(np.asarray(fac['cols']['st']), [i for i, v in enumerate(fac['dicts']['st']) if v in REVIEW_TYPES])
    P = np.asarray(fac['cols']['p'])
    tot = np.bincount(P, minlength=len(pms)); rev = np.bincount(P[st_rev], minlength=len(pms))
    return {pms[i] for i in range(len(pms)) if (pj['rows'][i][ti] and REVIEW_TITLE.search(pj['rows'][i][ti])) or (tot[i] and rev[i] * 2 > tot[i])}


def null_examples(data_dir, cond, kinds, skip=()):
    """[(null_class, entity, n_studies, pmids)] one per class: most separate studies, then findings, then name"""
    data = Path(data_dir); excluded = excluded_pmids(data); reviews = review_papers(data); L = Linked(data)
    fac = json.load(open(data / 'findings_facets.json')); D = fac['dicts']; C = fac['cols']
    pms = [str(r[0]) for r in json.load(open(data / 'papers.json'))['rows']]
    cc = D['c'].index(cond); eff = {D['d'].index(w) for w in (HIGHER, LOWER) if w in D['d']}
    pos = D['nc'].index('positive-effect') if 'positive-effect' in D['nc'] else -1
    effect = {(pms[C['p'][i]], D['e'][C['e'][i]]) for i in range(fac['n']) if C['c'][i] == cc and (C['d'][i] in eff or C['nc'][i] == pos)}
    idx = json.load(open(data / 'null_results.json'))
    rows = [dict(zip(idx['fields'], x)) for sh in idx['shards'] for x in json.load(open(data / sh['file']))['rows']]
    out = []
    for cls in ('treatment null', 'biomarker/mechanism null'):
        g, nf, rct = {}, {}, set()
        for r in rows:
            e, pm = r['canonical_entity'], str(r['canonical_pmid'])
            if r['condition'] != cond or r['null_class'] != cls or not e or e in skip or pm in excluded or pm in reviews: continue
            if r['evidence_tier'] not in PRIMARY_TIERS or e.lower() in SELF_NAMES or e.lower() in DEFINING: continue
            if cls == 'treatment null' and kinds.get(e) not in TREATMENT_KINDS: continue   # an outcome is not a treatment
            g.setdefault(e, set()).add(pm); nf[e] = nf.get(e, 0) + 1
            if r['evidence_tier'] == 'RCT': rct.add(e)
        clean = {e: s for e, s in g.items() if not any((p, e) in effect for p in s)}
        ok = {e: s for e, s in clean.items() if len({L.find(p) for p in s}) >= 2}
        if not ok and cls == 'treatment null':   # fallback: one randomized trial, shown as one trial, never as a paper count
            ok = {e: s for e, s in clean.items() if e in rct}
        if ok:
            e = min(ok, key=lambda e: (-len({L.find(p) for p in ok[e]}), -nf[e], e.lower()))
            out.append((cls, e, len({L.find(p) for p in ok[e]}), sorted(ok[e])))
    return out


def topic_stems(name):
    """loose match for "is this topic mentioned": the name without a bracketed part, Greek beta spelled out, each word of 4+
    letters cut to its first 5 letters, "auto" dropped from the start of a word (autoantibody -> antibody). A row mentions
    the topic when every stem is in its entity name or in its finding text."""
    s = name.split(' (')[0].lower().replace('\u03b2', 'beta')
    words = [w[4:] if w.startswith('auto') and len(w) > 7 else w for w in _re.findall(r'[a-z]{4,}', s)]
    return sorted({w[:5] for w in words}) or [s.strip()]


def sub_phrases(name):
    """every contiguous run of 2+ words of the name (without a bracketed part), lower case, shorter than the whole name"""
    w = name.split(' (')[0].lower().split()
    return [' '.join(w[a:b]) for a in range(len(w)) for b in range(a + 2, len(w) + 1) if b - a < len(w)]


NOT_A_CONDITION = {'general', 'multiple', 'other patient group'}


def clear_splits(data_dir):
    """[{'e','c','hi','lo'}] every clear split (module docstring), best first. 'e' is the most common spelling in those findings."""
    from collections import Counter, defaultdict
    data = Path(data_dir); fac = json.load(open(data / 'findings_facets.json')); D = fac['dicts']; C = fac['cols']
    pms = [str(r[0]) for r in json.load(open(data / 'papers.json'))['rows']]
    excluded = excluded_pmids(data); reviews = review_papers(data)
    comp = []
    for s in range(fac['n_shards']):
        comp += json.load(open(data / f'detail_{s:02d}.json'))['comp']
    ref = D['dr'].index(DISEASE_REF); up = D['d'].index(HIGHER); dn = D['d'].index(LOWER)
    st_rev = {i for i, v in enumerate(D['st']) if v in REVIEW_TYPES}
    H, L, spell = defaultdict(set), defaultdict(set), defaultdict(Counter)
    for i in range(fac['n']):
        if C['dr'][i] != ref or C['d'][i] not in (up, dn) or C['st'][i] in st_rev: continue
        pm = pms[C['p'][i]]; e = D['e'][C['e'][i]]; c = D['c'][C['c'][i]]
        if pm in excluded or pm in reviews or e in ('\u2014', '') or c in NOT_A_CONDITION: continue
        if 'healthy' not in str(comp[i] or '').lower(): continue
        k = (e.lower(), c); spell[k][e] += 1
        (H if C['d'][i] == up else L)[k].add(pm)
    out = []
    for k in set(H) & set(L):
        hi, lo = len(H[k] - L[k]), len(L[k] - H[k])
        if hi >= MIN_SIDE and lo >= MIN_SIDE:
            e = sorted(spell[k].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            out.append({'e': e, 'c': k[1], 'hi': hi, 'lo': lo})
    out.sort(key=lambda x: (-min(x['hi'], x['lo']), -(x['hi'] + x['lo']), x['e'].lower(), x['c']))
    return out


def under_examples(data_dir, cond, n=2):
    """understudied.json rows that are clear examples (see module docstring), in Signals rank order"""
    data = Path(data_dir); excluded = excluded_pmids(data); reviews = review_papers(data); L = Linked(data)
    fac = json.load(open(data / 'findings_facets.json')); D = fac['dicts']; C = fac['cols']
    pms = [str(r[0]) for r in json.load(open(data / 'papers.json'))['rows']]
    cc = D['c'].index(cond)
    rows = [i for i in range(fac['n']) if C['c'][i] == cc and pms[C['p'][i]] not in excluded]
    text = {}
    for s in sorted({i // fac['shard_rows'] for i in rows}):
        t = json.load(open(data / f'text_{s:02d}.json'))
        text.update({i: t['t'][i - t['start']].lower() for i in range(t['start'], t['end'])})
    ename_l = [str(v).lower() for v in D['e']]
    out = []
    for r in sorted(json.load(open(data / 'understudied.json'))['rows'], key=lambda r: r['rank']):
        e = r['canonical_entity']; own = set(map(str, r['pmids']))
        if r['condition'] != cond or r['n_papers'] < 2 or r['case_report_only'] or own & excluded or e not in D['e']: continue
        if len({L.find(p) for p in own}) < 2 or len({L.find(p) for p in own if p not in reviews}) < 2: continue
        stems = topic_stems(e)
        mention = {pms[C['p'][i]] for i in rows if all(st in ename_l[C['e'][i]] for st in stems) or all(st in text[i] for st in stems)}
        if len(mention) > r['n_papers']: continue
        if any(len({pms[C['p'][i]] for i in rows if ph in ename_l[C['e'][i]] or ph in text[i]}) > r['n_papers'] for ph in sub_phrases(e)): continue
        out.append(r)
        if len(out) == n: break
    return out
