#!/usr/bin/env python3
"""verify_home.py: check the home page data (site/data/home_map.json, home_stand.json) against the site data.

check(site_dir) -> list of failure strings (empty list = pass). It does not import build_home_data.py: every count
on the map is recounted here straight from findings_facets.json + papers.json + paper_flags.json, with findings from
exclude-flagged papers left out (the site's default view), and every stand-out example must be a real row of its
Signals table with matching numbers and no exclude-flagged paper.

Usage: python site_tools/verify_home.py [site]
"""
import json, sys
from pathlib import Path

import numpy as np

MAX_BYTES = 150_000


def check(site_dir):
    site = Path(site_dir); data = site / 'data'; f = []
    try:
        hm = json.load(open(data / 'home_map.json')); hs = json.load(open(data / 'home_stand.json'))
    except Exception as e:  # missing or unreadable file
        return [f'home data unreadable: {e}']
    size = sum((data / n).stat().st_size for n in ('home_map.json', 'home_stand.json'))
    if size > MAX_BYTES: f.append(f'home json total {size} bytes > {MAX_BYTES}')
    meta = json.load(open(data / 'meta.json')); m = meta['counts']
    for name, obj in (('home_map', hm), ('home_stand', hs)):
        if obj.get('version') != meta['version']: f.append(f'{name}.version {obj.get("version")} != meta {meta["version"]}')

    fac = json.load(open(data / 'findings_facets.json')); D = fac['dicts']; C = fac['cols']
    E, Cc, Dd, P, FT = (np.asarray(C[k]) for k in ('e', 'c', 'd', 'p', 'ft'))
    pm_of = [str(r[0]) for r in json.load(open(data / 'papers.json'))['rows']]
    flags = json.load(open(data / 'paper_flags.json'))['flags']
    excl = {str(pm) for pm, xs in flags.items() if any(x.get('u') == 'exclude' for x in xs)}
    keep = ~np.array([pm in excl for pm in pm_of])[P]
    # disagreement rule (contradictions.json "rule"): higher / lower / no difference count only findings that compare people
    # with the condition to people without it (facet dr == vs-disease-state)
    if 'dr' not in D: return f + ['findings_facets.json has no dr facet (direction_reference)']
    nullnc = np.isin(np.asarray(C['nc']), [i for i, v in enumerate(D['nc']) if str(v).startswith('null')])
    ref = np.asarray(C['dr']) == (D['dr'].index('vs-disease-state') if 'vs-disease-state' in D['dr'] else -1)
    if hm.get('excluded_papers') != m.get('excluded_papers'):
        f.append(f'excluded_papers {hm.get("excluded_papers")} != meta {m.get("excluded_papers")}')

    cidx = {c: i for i, c in enumerate(D['c'])}
    alias = hm.get('alias', {})
    canon = np.array([alias.get(n, n) for n in D['e']], dtype=object)
    dcode = {w: (D['d'].index(w) if w in D['d'] else -1) for w in ('elevated', 'depleted/reduced', 'no significant difference')}

    def papers(mask): return set(P[mask & keep].tolist())
    def cmask(c): return Cc == cidx.get(c, -1)
    ent_cache = {}
    def emask(nm):
        if nm not in ent_cache: ent_cache[nm] = np.isin(E, np.nonzero(canon == nm)[0])
        return ent_cache[nm]

    # one number per fact: tallies use the raw entity name, every finding type, distinct papers per direction
    # (contradictions.json rule), and must equal the contradictions.json direction-flip row when one exists
    con_rows = json.load(open(data / 'contradictions.json'))['rows']
    partial_list = len(con_rows) < json.load(open(data / 'contradictions.json')).get('total', 0)  # table lists the strongest rows only
    flips = {(r['canonical_entity'], r['condition']): r for r in con_rows if r['conflict_type'] == 'direction-flip'}
    raw_code = {nm: i for i, nm in enumerate(D['e'])}
    kinds = {e['name']: e.get('kind') for e in json.load(open(data / 'entities.json'))['entities']}
    treat = D['ft'].index('treatment/intervention') if 'treatment/intervention' in D['ft'] else -1
    def tally_check(what, tt, ent, cond):
        base = keep & ref & (E == raw_code.get(ent, -1)) & cmask(cond)   # vs-disease-state findings only (disagreement rule)
        up, dn = (len(set(P[base & (Dd == dcode[w])].tolist())) for w in ('elevated', 'depleted/reduced'))
        nu = len(set(P[base & ((Dd == dcode['no significant difference']) | nullnc)].tolist()))   # null side of contradictions.json
        if (tt['e'], tt['c']) != (ent, cond): f.append(f'{what} tally names {tt["e"]}/{tt["c"]} != {ent}/{cond}')
        if (tt['up'], tt['dn'], tt['nu']) != (up, dn, nu): f.append(f'{what} tally {tt["up"]},{tt["dn"]},{tt["nu"]} != recount {up},{dn},{nu}')
        r = flips.get((ent, cond))
        if r:
            hi, lo = (r['n_papers_A'], r['n_papers_B']) if r['side_A_direction'] == 'elevated' else (r['n_papers_B'], r['n_papers_A'])
            if (tt['up'], tt['dn']) != (hi, lo): f.append(f'{what} tally {tt["up"]} higher, {tt["dn"]} lower != contradictions.json {hi}, {lo}')
        elif up and dn and not partial_list: f.append(f'{what}: papers split both ways but no contradictions.json row for {ent}/{cond}')

    pots = papers(cmask('POTS'))
    if hm['pots']['n'] != len(pots): f.append(f'POTS papers {hm["pots"]["n"]} != recount {len(pots)}')
    skip = set(hm.get('skip_conds', []))
    cond_sets = {}
    for c in hm['conds']:
        s = cond_sets[c['c']] = papers(cmask(c['c']))
        if c['c'] in skip: f.append(f'condition {c["c"]} is in the skip list')
        if c['n'] != len(s): f.append(f'condition {c["c"]} papers {c["n"]} != recount {len(s)}')
        if c['both'] != len(s & pots): f.append(f'condition {c["c"]} both {c["both"]} != recount {len(s & pots)}')
        for nm, a, b in c['shared']:
            ra, rb = len(papers(emask(nm) & cmask('POTS'))), len(papers(emask(nm) & cmask(c['c'])))
            if (a, b) != (ra, rb): f.append(f'{c["c"]} shared {nm} {a},{b} != recount {ra},{rb}')
        if c.get('split'): tally_check(f'{c["c"]} split', c['split'], c['split']['e'], c['c'])
    # every condition key with papers and not skipped is drawn
    drawn = {c['c'] for c in hm['conds']}
    for c in D['c']:
        if c not in skip and c not in drawn and papers(cmask(c)): f.append(f'condition {c} has papers but is not on the map')
    sizes = [c['n'] for c in hm['conds']]
    if sizes != sorted(sizes, reverse=True): f.append('conditions not ordered by papers')

    R = hm['rules']
    blank = D['e'].index('—') if '—' in D['e'] else -1
    ent_rows = keep & (E != blank)
    n_ent_papers = len(set(P[ent_rows].tolist()))
    pots_ent = len(set(P[ent_rows & cmask('POTS')].tolist()))
    bad = {g.lower() for g in hm.get('generic', [])} | {g.lower() for g in hm.get('condnames', [])}
    for t in hm['topics']:
        nm = t['e']; em = emask(nm)
        if nm.lower() in bad: f.append(f'topic {nm} is a generic covariate or a condition name')
        np_ = len(papers(em & cmask('POTS')))
        if t['np'] != np_: f.append(f'topic {nm} POTS papers {t["np"]} != recount {np_}')
        if np_ < R['floor']: f.append(f'topic {nm} below floor {R["floor"]}')
        lift = (np_ / pots_ent) / (len(papers(em)) / n_ent_papers)
        if abs(round(lift, 2) - t['lift']) > 0.011: f.append(f'topic {nm} lift {t["lift"]} != recount {lift:.2f}')
        if t['kind'] == 'specific' and lift < R['lift']: f.append(f'specific topic {nm} lift {lift:.2f} < {R["lift"]}')
        for c, k in t['links']:
            rk = len(papers(em & cmask(c)))
            if k != rk or rk < R['topic_link_min']: f.append(f'topic {nm} link {c} {k} != recount {rk}')
        tally_check(f'topic {nm}', t['tally'], t['ent'], 'POTS')
        # ring rule (Start page rule): split both ways, and a measured kind, or a chemical with <= half treatment findings
        fr = flips.get((t['ent'], 'POTS')) or {}
        knd = fr.get('entity_kind') or kinds.get(t['ent'])
        base = keep & (E == raw_code.get(t['ent'], -1)) & cmask('POTS')
        tshare = float((base & (FT == treat)).sum()) / max(1, int(base.sum()))
        measured = knd in set(R.get('measured_kinds', [])) or (knd == 'chemical/metabolite' and tshare <= R.get('treatment_share_max', 0.5))
        if set(R.get('measured_kinds', [])) != {'physiological-measure', 'gene/protein', 'cell-type'}: f.append('measured kinds differ from the Start page rule')
        if t.get('measured') != measured: f.append(f'topic {nm} measured flag {t.get("measured")} != recount {measured}')
        if t['disagree'] != (t['tally']['up'] > 0 and t['tally']['dn'] > 0 and measured): f.append(f'topic {nm} disagree ring flag wrong')
        if t['ent'] not in D['e']: f.append(f'topic {nm} entity link {t["ent"]} is not an entity name')
    if len(hm['topics']) > R['max_topics']: f.append(f'{len(hm["topics"])} topics > max {R["max_topics"]}')
    for r in hm['cc']:
        both = len(cond_sets.get(r['a'], set()) & cond_sets.get(r['b'], set()))
        if r['both'] != both: f.append(f'pair {r["a"]}/{r["b"]} both {r["both"]} != recount {both}')
        for nm, a, b in r['shared']:
            ra, rb = len(papers(emask(nm) & cmask(r['a']))), len(papers(emask(nm) & cmask(r['b'])))
            if (a, b) != (ra, rb): f.append(f'pair {r["a"]}/{r["b"]} shared {nm} {a},{b} != recount {ra},{rb}')

    # ---------- What stands out ----------
    for k, mk in (('contra_total', 'contradictions_total'), ('nulls', 'nulls'), ('under_total', 'understudied_total')):
        if hs[k] != m[mk]: f.append(f'stand {k} {hs[k]} != meta {mk} {m[mk]}')
    con = json.load(open(data / 'contradictions.json'))
    if con.get('total') != m['contradictions_total']: f.append('contradictions.json total != meta')
    # disagree and barely studied cards use the Start page picks: compare with verify_start_here's own recompute
    sys.path.insert(0, str(Path(__file__).resolve().parent)); import verify_start_here as VS
    _, _, _, want_s, _, _, _, picks = VS.expected(str(site))
    c = hs['cex']
    if (c['e'] if c else None) != (picks['contra'][0] if picks['contra'] else None):
        f.append(f'disagree example {c and c["e"]} != Start page pick {picks["contra"][:1]}')
    elif c:
        got = {k: v for k, v, _ in c['parts']}
        exp = {k.split(':', 1)[0][7:]: v for k, v in want_s.items() if k.startswith('contra_') and k.split(':', 1)[1] == c['e']}
        if got != exp: f.append(f'disagree example counts {got} != contradictions.json {exp}')
        for k, v, w in c['parts']:
            word = {'hi': 'higher', 'lo': 'lower', 'nu': 'no difference'}[k]
            if word not in w: f.append(f'disagree example part {k} worded {w!r}')
    nul = json.load(open(data / 'null_results.json')); fl = nul['fields']; ix = {k: fl.index(k) for k in fl}
    if nul['n'] != m['nulls']: f.append('null_results.json n != meta nulls')
    n = hs['nex']; hit = None
    for sh in nul['shards']:
        for r in json.load(open(data / sh['file']))['rows']:
            if (str(r[ix['canonical_pmid']]) == n['pmid'] and r[ix['canonical_entity']] == n['e'] and r[ix['provenance_quote_trunc']] == n['q']
                    and r[ix['year']] == n['year'] and r[ix['condition']] == n['c'] and r[ix['null_class']] == n['nc']):
                hit = r; break
        if hit: break
    if not hit: f.append(f'null example {n["e"]} ({n["pmid"]}) is not a row of the null results')
    if n['pmid'] in excl: f.append('null example is an exclude-flagged paper')
    und = json.load(open(data / 'understudied.json'))
    if und.get('total') != m['understudied_total']: f.append('understudied.json total != meta')
    u = hs['uex']
    if (u['e'] if u else None) != (picks['under'][0] if picks['under'] else None): f.append(f'understudied example {u and u["e"]} != Start page pick {picks["under"][:1]}')
    if u:
        row = next((r for r in und['rows'] if r['canonical_entity'] == u['e'] and r['condition'] == u['c'] and r['n_papers'] == u['n']
                    and r['n_findings'] == u['nf'] and [str(x) for x in r['pmids']] == u['pmids']), None)
        if not row: f.append(f'understudied example {u["e"]} is not a row of understudied.json')
        if set(u['pmids']) & excl: f.append('understudied example cites an exclude-flagged paper')
    js = (site / 'js' / 'home-v2.js').read_text(encoding='utf-8')
    if 'href="discover#under?all"' not in js: f.append('home barely studied card does not link to discover#under?all (the set its total describes)')

    # page wiring: the home script reads these files, and the hero counts are apply_counts markers
    js = (site / 'js' / 'home-v2.js').read_text(encoding='utf-8'); html = (site / 'index.html').read_text(encoding='utf-8')
    for need in ('data/home_map.json', 'data/home_stand.json'):
        if need not in js: f.append(f'home-v2.js does not read {need}')
    for key in ('findings', 'papers'):
        if f'<!--n:{key}-->' not in html: f.append(f'index.html lacks the {key} count marker')
    return f


if __name__ == '__main__':
    site = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / 'site')
    fails = check(site)
    print('\n'.join(fails) if fails else 'verify_home: PASS')
    sys.exit(1 if fails else 0)
