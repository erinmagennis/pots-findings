#!/usr/bin/env python3
"""verify_connections.py: check the Connections page data (site/data/conn_*.json) against the site projection.

check(site_dir) -> list[str] of failures (empty list = pass). It recomputes from findings_facets.json, papers.json and
paper_flags.json, without importing the builder:
  1. every conn_* file parses; per-paper arrays all have n_papers entries and line up across files
  2. region paper counts sum to the total shown; each region count equals its papers; sub-regions sum to their region
  3. every pmid exists in papers.json, once; no exclude-flagged pmid appears anywhere (map, examples, flow)
  4. n_papers / n_findings equal the papers with findings and the findings left after the default exclusion
  5. disagreement tallies (higher / lower / no difference paper counts) recomputed from findings with the shared rule in
     signals_rules.py match, map-wide and per region; whole-map tallies equal every direction-flip row of
     contradictions.json and the whole-map count equals meta contra_flip_total; a sample also matches
     signals_rules.Facets.tally; region and band sizes in conn_flow match conn_map
  6. the POTS subtype count shown in Flow equals the papers with a named subtype; meta records the UMAP versions
Run: python site_tools/verify_connections.py [--site site]
"""
import argparse, json, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from signals_rules import HIGHER, LOWER, NODIFF, Facets as RuleFacets, flip_sides, DISEASE_REF  # noqa: E402

FILES = ('conn_map.json', 'conn_papers.json', 'conn_ents.json', 'conn_splits.json', 'conn_flow.json')


def _tally(idx, cls, E, C, P, ename, cname, pm_of, ok):
    dd = defaultdict(lambda: [set(), set(), set(), set()])
    for i in idx:
        if not ok[i]: continue
        g = dd[(E[i], C[i])]; g[3].add(P[i])
        c = cls[i]
        if c:
            g[c - 1].add(P[i])
    out = {}
    for (e, c), (u, d, n, a) in dd.items():
        if len(a) >= 2 and u and d:
            out[(ename[e], cname[c])] = (len(u), len(d), len(n), {pm_of(p) for p in u}, {pm_of(p) for p in d}, {pm_of(p) for p in n})
    return out


def check(site_dir):
    site = Path(site_dir); data = site / 'data'; f = []
    try:
        J = {n: json.load(open(data / n, encoding='utf-8')) for n in FILES}
    except Exception as e:  # noqa: BLE001
        return [f'conn data missing or unreadable: {e}']
    M, TP, EN, SP, FL = (J[n] for n in FILES)
    fac = json.load(open(data / 'findings_facets.json')); D = fac['dicts']; cols = fac['cols']; nF = fac['n']
    pj = json.load(open(data / 'papers.json')); pidx = {n: i for i, n in enumerate(pj['fields'])}; rows = pj['rows']
    try:
        flags = json.load(open(data / 'paper_flags.json'))['flags']
    except FileNotFoundError:
        flags = {}
    excl = {str(pm) for pm, xs in flags.items() if any(x.get('u') == 'exclude' for x in xs)}
    pm_of = lambda p: str(rows[p][pidx['pmid']])
    row_of = {pm_of(i): i for i in range(len(rows))}

    # 1. alignment
    N = M['n_papers']; PP = M['papers']
    for k, v in PP.items():
        if len(v) != N: f.append(f'conn_map papers.{k} has {len(v)} entries, expected {N}')
    for name, obj, keys in (('conn_papers', TP, ('cite', 'title', 'nf', 'rank')), ('conn_ents', EN, ('paper',)), ('conn_flow', FL, ('sysm', 'psm', 'cam', 'ftm'))):
        for k in keys:
            if len(obj[k]) != N: f.append(f'{name}.{k} has {len(obj[k])} entries, expected {N}')
    if FL['n_papers'] != N: f.append(f"conn_flow n_papers {FL['n_papers']} != conn_map {N}")

    # 2. region totals
    R = M['regions']; kc = defaultdict(int); sc = defaultdict(int)
    for k in PP['k']: kc[k] += 1
    for s in PP['s']: sc[s] += 1
    if sum(r['n'] for r in R) != N: f.append(f"region paper counts sum to {sum(r['n'] for r in R)}, total shown is {N}")
    for r in R:
        if kc[r['id']] != r['n']: f.append(f"region {r['id']} says {r['n']} papers, {kc[r['id']]} papers carry it")
        subn = sum(s['n'] for s in M['subs'] if s['k'] == r['id'])
        if subn != r['n']: f.append(f"region {r['id']} sub-regions sum to {subn}, region has {r['n']}")
    for i, s in enumerate(M['subs']):
        if sc[i] != s['n']: f.append(f'sub-region {i} says {s["n"]} papers, {sc[i]} carry it')
    for j in range(N):
        if M['subs'][PP['s'][j]]['k'] != PP['k'][j]: f.append(f'paper {PP["pmid"][j]} sub-region is outside its region'); break

    # 3. pmids
    pms = PP['pmid']
    if len(set(pms)) != len(pms): f.append('conn_map has duplicate pmids')
    missing = [p for p in pms if p not in row_of]
    if missing: f.append(f'{len(missing)} conn_map pmids not in papers.json, e.g. {missing[:3]}')
    bad = [p for p in pms if p in excl]
    if bad: f.append(f'{len(bad)} exclude-flagged papers on the map, e.g. {bad[:3]}')
    def ex_pmids(splits):
        for s in splits:
            for k in ('pu', 'pd', 'pn'):
                yield from s.get(k, [])
    refs = list(ex_pmids(SP['splits'])) + list(ex_pmids(M['top_splits']))
    for r in R: refs += list(ex_pmids(r['splits']))
    for v in FL['info'].values(): refs += list(ex_pmids(v['splits']))
    if [p for p in refs if p in excl]: f.append(f'exclude-flagged pmid used as an example: {sorted({p for p in refs if p in excl})[:3]}')
    if [p for p in refs if p not in row_of]: f.append(f'example pmid not in papers.json: {[p for p in refs if p not in row_of][:3]}')
    if len(TP['cite']) == N and len(pms) == N:
        wrong = [j for j in range(N) if pms[j] in row_of and TP['cite'][j] != (rows[row_of[pms[j]]][pidx['citation_short']] or '')]
        if wrong: f.append(f'{len(wrong)} conn_papers citations do not match papers.json')

    # 4. totals
    P = cols['p']; ex_row = [pm_of(i) in excl for i in range(len(rows))]
    keepF = [not ex_row[P[i]] for i in range(nF)]
    with_f = {P[i] for i in range(nF) if keepF[i]}
    if len(with_f) != N: f.append(f'n_papers {N} != papers with findings after the default exclusion {len(with_f)}')
    if sum(keepF) != M['n_findings']: f.append(f"n_findings {M['n_findings']} != {sum(keepF)} findings after the default exclusion")
    if {pm_of(p) for p in with_f} != set(pms): f.append('map papers differ from the papers with findings after exclusion')

    # 5. tallies
    E, Cc, Dd = cols['e'], cols['c'], cols['d']
    blank = {i for i, v in enumerate(D['e']) if v in ('—', '')}
    up, dn, nsd = D['d'].index(HIGHER), D['d'].index(LOWER), D['d'].index(NODIFF)
    if 'dr' not in D: return f + ['findings_facets.json has no dr facet (direction_reference)']
    ref_code = D['dr'].index(DISEASE_REF) if DISEASE_REF in D['dr'] else -1; DR = cols['dr']   # only vs-disease-state findings count
    ok = [keepF[i] and E[i] not in blank and DR[i] == ref_code for i in range(nF)]
    cls = [0] * nF  # 1 higher, 2 lower, 3 no difference (signals_rules)
    for i in range(nF):
        if ok[i]: cls[i] = 1 if Dd[i] == up else 2 if Dd[i] == dn else 3 if Dd[i] == nsd else 0
    want = _tally(range(nF), cls, E, Cc, P, D['e'], D['c'], pm_of, ok)
    if SP['n'] != len(want) or M['n_splits'] != len(want): f.append(f"map-wide disagreements: data says {SP['n']}/{M['n_splits']}, recomputed {len(want)}")
    def cmp(label, shown, ref):
        for s in shown:
            r = ref.get((s['e'], s['c']))
            if not r: f.append(f"{label}: {s['e']} / {s['c']} is not a disagreement when recomputed"); continue
            if (s['up'], s['dn'], s['nu']) != r[:3]: f.append(f"{label}: {s['e']} / {s['c']} shows {s['up']}/{s['dn']}/{s['nu']}, recomputed {r[:3]}")
            for key, pool in (('pu', r[3]), ('pd', r[4]), ('pn', r[5])):
                if not set(s.get(key, [])) <= pool: f.append(f"{label}: {s['e']} example in {key} is not on that side")
    cmp('conn_splits', SP['splits'], want); cmp('top_splits', M['top_splits'], want)
    # one number per fact: whole-map tallies equal contradictions.json direction-flip rows and the Signals flip total
    try:
        CJ = json.load(open(data / 'contradictions.json'))
        shown = {(s['e'], s['c']): s for s in SP['splits']}
        nrow = 0
        for row in CJ['rows']:
            if row['conflict_type'] != 'direction-flip': continue
            nrow += 1; hi, lo = flip_sides(row); s = shown.get((row['canonical_entity'], row['condition']))
            if not s: f.append(f"contradictions.json flip {row['canonical_entity']} / {row['condition']} missing from conn_splits")
            elif (s['up'], s['dn']) != (hi, lo): f.append(f"{row['canonical_entity']} / {row['condition']}: Connections {s['up']}/{s['dn']}, contradictions.json {hi}/{lo}")
        if nrow == 0: f.append('contradictions.json has no direction-flip rows to compare')
        flip_total = json.load(open(data / 'meta.json'))['counts'].get('contra_flip_total', CJ.get('flip_total'))
        if SP['n'] != flip_total: f.append(f"whole-map direction flips {SP['n']} != Signals flip total {flip_total}")
    except FileNotFoundError:
        f.append('contradictions.json missing, cannot compare tallies')
    RF = RuleFacets(data)
    for s in SP['splits'][:25] + [x for x in SP['splits'] if (x['e'], x['c']) == ('Mast cells', 'MCAS')]:
        t = RF.tally(s['e'], s['c'])
        if (t['up'], t['dn'], t['nu']) != (s['up'], s['dn'], s['nu']):
            f.append(f"{s['e']} / {s['c']}: Connections {s['up']}/{s['dn']}/{s['nu']}, signals_rules.Facets.tally {t['up']}/{t['dn']}/{t['nu']}")
    k_of_row = {row_of[pms[j]]: PP['k'][j] for j in range(N) if pms[j] in row_of}
    by_k = defaultdict(list)
    for i in range(nF):
        if keepF[i]: by_k[k_of_row.get(P[i], -1)].append(i)
    for r in R:
        ref = _tally(by_k[r['id']], cls, E, Cc, P, D['e'], D['c'], pm_of, ok)
        if r['ns'] != len(ref): f.append(f"region {r['id']}: {r['ns']} disagreements shown, recomputed {len(ref)}")
        cmp(f"region {r['id']}", r['splits'], ref)
        info = FL['info'].get(f"k{r['id']}")
        if not info or info['np'] != r['n'] or info['ns'] != r['ns']: f.append(f"conn_flow band k{r['id']} does not match region {r['id']}")
        elif info['nf'] != r['nf']: f.append(f"conn_flow band k{r['id']} findings {info['nf']} != region {r['nf']}")

    # 6. flow subtype count, meta
    PS = cols['ps']; named = {i for i, v in enumerate(D['ps']) if v not in ('—', 'not specified')}
    sub_p = {P[i] for i in range(nF) if keepF[i] and PS[i] in named}
    shown_sub = sum(1 for m in FL['psm'] if m)
    if shown_sub != len(sub_p): f.append(f'Flow says {shown_sub} papers name a POTS subtype, recomputed {len(sub_p)}')
    v = M.get('meta', {}).get('versions', {})
    if not v.get('umap-learn') or not v.get('scikit-learn'): f.append('conn_map meta does not record the umap-learn / scikit-learn versions')
    return f


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--site', default=str(Path(__file__).resolve().parent.parent / 'site'))
    a = ap.parse_args(); fails = check(a.site)
    for x in fails: print('FAIL', x)
    print('verify_connections:', 'PASS' if not fails else f'{len(fails)} failure(s)')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
