#!/usr/bin/env python3
"""build_connections_data.py: data for the Connections page (Map and Flow views).

Reads only the built site projection in <site>/data/ (findings_facets.json, papers.json, paper_flags.json,
emb/*.bin) and writes:

  conn_map.json     first paint for the Map view: regions, sub-regions, region text, per-paper position/region/year/condition
  conn_papers.json  lazy: per-paper short citation, title (cut to 110 chars) and label priority, same order as conn_map
  conn_ents.json    lazy: entity names and the distinct entities each paper names (for "find a paper or topic")
  conn_splits.json  lazy: every map-wide disagreement (same entity, same condition, papers both higher and lower)
  conn_flow.json    Flow view: per-paper body system / POTS subtype / claim type bitmasks and per-band summaries

Rules
  * Papers whose paper_flags entry has recommended use "exclude" (retractions, correction notices) are left out of
    everything, the same default as applyFilters in site/js/data.js.
  * Paper position: mean of its findings' MiniLM embeddings (emb/, dequantised and L2-normalised), UMAP to 2D for the
    layout and to 10D for KMeans regions. Sub-regions: KMeans on the 2D layout inside each region.
  * Disagreement (direction flip): the shared rule in site_tools/signals_rules.py, the same one contradictions.json, the
    home page and the Start page use. Entity name as stored in findings_facets, same condition, every finding type
    (treatment included), distinct papers with an "elevated" finding (higher) and with a "depleted/reduced" finding
    (lower); a flip needs both and at least two distinct papers on that entity and condition, as in
    build_v12_projection.py. No difference = distinct papers with a "no significant difference" finding for the same
    entity and condition. Exclude-flagged papers are out. Region and band tallies are the same rule restricted to the
    papers of that region or band.

Deterministic: fixed random_state everywhere, sorted tie-breaks, no timestamps in output. UMAP results depend on the
umap-learn / numba / numpy versions; they are written into conn_map.json meta.

Run (about 1-2 minutes on an M-series laptop; needs umap-learn and scikit-learn):
  <venv>/bin/python site_tools/build_connections_data.py --site site
"""
import argparse, json, math, sys, time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from signals_rules import HIGHER, LOWER, NODIFF, excluded_pmids, display  # noqa: E402

K_REGIONS = 16
SEED = 7
Q = 4095  # layout coordinates are quantised to integers 0..Q

SYS = ['autonomic', 'vascular', 'immune', 'neuro', 'endocrine', 'GI', 'musculoskeletal', 'connective-tissue', 'other']
SYS_LABEL = {'autonomic': 'Autonomic', 'vascular': 'Blood vessels', 'immune': 'Immune', 'neuro': 'Nervous system',
             'endocrine': 'Hormones', 'GI': 'Gut', 'musculoskeletal': 'Muscle and bone',
             'connective-tissue': 'Connective tissue', 'other': 'Other systems', 'small': 'Smaller systems'}
PS_LABEL = {'hyperadrenergic': 'Hyperadrenergic', 'neurogenic': 'Neurogenic', 'hypovolemic': 'Hypovolemic',
            'immune-related': 'Immune-related', 'autoimmunogenic': 'Autoimmunogenic', 'neuropathic': 'Neuropathic'}
CA_LABEL = {'causal-claim': 'Claims a cause', 'correlational-only': 'Correlation only',
            'mechanistic/in-vitro': 'Mechanistic or lab study', 'mechanism': 'Mechanism'}
NULL_NC = ('null-no-effect', 'failed-to-replicate', 'tried-and-abandoned')  # region "no-effect results" line only
FT_LABEL = {'mechanism/biomarker': 'Mechanism or biomarker', 'treatment/intervention': 'Treatment',
            'comorbidity': 'Co-occurring conditions', 'diagnostic/screening': 'Diagnosis or screening',
            'symptom-burden': 'Symptom burden'}
FOLD_MIN = 10  # a subtype or claim type with fewer papers than this is folded into one "Other" band


def dump(obj, path):
    s = json.dumps(obj, separators=(',', ':'), ensure_ascii=False, sort_keys=False)
    path.write_text(s, encoding='utf-8')
    print(f'  {path.name}: {len(s.encode()) / 1e6:.2f} MB')
    return len(s.encode())




def load_embeddings(data):
    man = json.load(open(data / 'emb' / 'manifest.json'))
    qp = json.load(open(data / 'emb' / 'quant_params.json'))
    dims, n = man['dims'], man['total_rows']
    qmin = np.asarray(qp['qmin'], dtype=np.float32); scale = np.asarray(qp['scale'], dtype=np.float32)
    M = np.empty((n, dims), dtype=np.float32)
    for sh in man['shards']:
        q = np.fromfile(data / 'emb' / sh['file'], dtype=np.uint8).reshape(sh['rows'], dims)
        v = q.astype(np.float32) * scale + qmin
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        M[sh['start']:sh['end']] = v
    return M, man


def dedupe(names):
    out = []
    for nm in names:
        a = nm.lower().split(' (')[0]
        if any(a in b.lower() or b.lower().split(' (')[0] in a for b in out):
            continue
        out.append(nm)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default=str(Path(__file__).resolve().parent.parent / 'site'))
    args = ap.parse_args()
    t0 = time.time()
    site = Path(args.site); data = site / 'data'
    import umap, sklearn, numba
    from sklearn.cluster import KMeans

    meta = json.load(open(data / 'meta.json'))
    fac = json.load(open(data / 'findings_facets.json'))
    D = fac['dicts']; C = fac['cols']; nF = fac['n']
    col = {k: np.asarray(C[k]) for k in ('e', 'c', 'd', 'nc', 'ft', 'an', 'ps', 'ca', 'p')}
    pj = json.load(open(data / 'papers.json'))
    pidx = {n: i for i, n in enumerate(pj['fields'])}; rows = pj['rows']
    excl = excluded_pmids(data)
    ex_paper = np.array([str(r[pidx['pmid']]) in excl for r in rows])
    print(f'papers {len(rows)}, findings {nF}, excluded papers {int(ex_paper.sum())}')

    E, Cc, Dd, NC, FT, AN, PS, CA, P = (col[k] for k in ('e', 'c', 'd', 'nc', 'ft', 'an', 'ps', 'ca', 'p'))
    f_keep = ~ex_paper[P]
    blank_e = {i for i, v in enumerate(D['e']) if v in ('—', '')}
    up_d = D['d'].index(HIGHER); dn_d = D['d'].index(LOWER); nsd_d = D['d'].index(NODIFF)
    null_nc = np.array([v in NULL_NC for v in D['nc']])
    # per finding direction class (signals_rules): 1 higher, -1 lower, 2 no difference, 0 not counted
    dcls = np.zeros(nF, dtype=np.int8)
    dcls[Dd == up_d] = 1; dcls[Dd == dn_d] = -1; dcls[Dd == nsd_d] = 2
    dcls[np.isin(E, list(blank_e))] = 0
    dcls[~f_keep] = 0

    # ---------- paper embeddings, UMAP, regions ----------
    M, man = load_embeddings(data)
    assert M.shape[0] == nF, 'embedding rows != findings'
    npap = len(rows)
    Pm = np.zeros((npap, M.shape[1]), dtype=np.float32)
    np.add.at(Pm, P[f_keep], M[f_keep]); del M
    cnt = np.bincount(P[f_keep], minlength=npap)
    keep = cnt > 0
    Pm[keep] /= np.linalg.norm(Pm[keep], axis=1, keepdims=True)
    paper_ids = np.where(keep)[0]
    print(f'papers on the map {len(paper_ids)} (excluded {int(ex_paper.sum())}, no findings {int((~keep & ~ex_paper).sum())})')
    X = Pm[keep]
    t1 = time.time()
    xy = umap.UMAP(n_neighbors=30, min_dist=0.08, metric='cosine', random_state=SEED).fit_transform(X)
    x10 = umap.UMAP(n_neighbors=30, min_dist=0.0, n_components=10, metric='cosine', random_state=SEED).fit_transform(X)
    print(f'  umap {time.time() - t1:.0f}s')
    lab = KMeans(n_clusters=K_REGIONS, n_init=10, random_state=SEED).fit_predict(x10)
    order = sorted(Counter(lab.tolist()).items(), key=lambda kv: (-kv[1], kv[0]))
    remap = {c: i for i, (c, _) in enumerate(order)}
    lab = np.array([remap[c] for c in lab])
    # quantised layout
    lo = xy.min(0); span = float((xy.max(0) - lo).max())
    qx = np.round((xy[:, 0] - lo[0]) / span * Q).astype(int); qy = np.round((xy[:, 1] - lo[1]) / span * Q).astype(int)
    k_of = np.full(npap, -1); k_of[paper_ids] = lab
    pos = {int(p): j for j, p in enumerate(paper_ids)}

    # ---------- per paper facts ----------
    ename = D['e']
    p_ents = defaultdict(set); p_conds = defaultdict(set)
    for i in np.where(f_keep)[0]:
        p = int(P[i]); p_conds[p].add(D['c'][Cc[i]])
        if int(E[i]) not in blank_e:
            p_ents[p].add(int(E[i]))
    cited = lambda p: rows[p][pidx['cited_by_count']] or 0
    pm_of = lambda p: str(rows[p][pidx['pmid']])

    def tally(find_idx):
        """splits over a set of finding indices -> sorted list of dicts"""
        dd = defaultdict(lambda: ([set(), set(), set(), set()]))   # higher, lower, no difference, any finding
        for i in find_idx:
            if not f_keep[i] or int(E[i]) in blank_e:
                continue
            g = dd[(int(E[i]), int(Cc[i]))]; g[3].add(int(P[i]))
            dc = int(dcls[i])
            if dc:
                g[{1: 0, -1: 1, 2: 2}[dc]].add(int(P[i]))
        out = []
        for (e, c), (u, d, n, a) in dd.items():
            # contradictions.json rule: the entity and condition need at least two papers, one higher and one lower
            if len(a) < 2 or not u or not d:
                continue
            pick = lambda s, o: [pm_of(p) for p in sorted(s, key=lambda p: (p in o, -cited(p), pm_of(p)))[:2]]
            out.append({'e': ename[e], 'c': D['c'][c], 'up': len(u), 'dn': len(d), 'nu': len(n),
                        'pu': pick(u, d), 'pd': pick(d, u), 'pn': pick(n, u | d)})
        out.sort(key=lambda r: (-min(r['up'], r['dn']), -(r['up'] + r['dn'] + r['nu']), r['e'], r['c']))
        return out

    # ---------- regions ----------
    N = len(paper_ids)
    cl_papers = defaultdict(list)
    for p in paper_ids:
        cl_papers[int(k_of[p])].append(int(p))
    cl_find = defaultdict(list)
    for i in np.where(f_keep)[0]:
        cl_find[int(k_of[P[i]])].append(int(i))
    all_ent = Counter(); cl_ent = defaultdict(Counter)
    for p, es in p_ents.items():
        for e in es:
            all_ent[e] += 1; cl_ent[int(k_of[p])][e] += 1

    def distinctive(counter, n, base_counter, base_n, top=8, min_c=5):
        out = []
        for e, c in counter.items():
            if c < max(min_c, 0.02 * n):
                continue
            frac = c / n; base = base_counter[e] / base_n
            out.append((frac * math.log(frac / base), c, ename[e], e))
        out.sort(key=lambda t: (-t[0], -t[1], t[2]))
        return out[:top]

    regions = []
    for k in range(K_REGIONS):
        ps_ = cl_papers[k]; n = len(ps_); fi = cl_find[k]
        dist = distinctive(cl_ent[k], n, all_ent, N)
        cond = Counter(c for p in ps_ for c in p_conds[p])
        ft = Counter(D['ft'][FT[i]] for i in fi)
        an = Counter(s.strip() for i in fi for s in D['an'][AN[i]].split(',') if s.strip() and s.strip() != '—')
        nullp = {int(P[i]) for i in fi if null_nc[NC[i]]}
        splits = tally(fi)
        mask = lab == k
        regions.append({
            'id': k, 'n': n, 'nf': len(fi),
            'label': [display(x) for x in (dedupe([t[2] for t in dist])[:3] or [ename[e] for e, _ in cl_ent[k].most_common(2)])],
            'dist': [[t[2], t[1]] for t in dist[:6]],
            'top': [[ename[e], c] for e, c in sorted(cl_ent[k].items(), key=lambda kv: (-kv[1], ename[kv[0]]))[:8]],
            'conds': [[c, v] for c, v in sorted(cond.items(), key=lambda kv: (-kv[1], kv[0]))[:5]],
            'fts': [[f, round(v / max(1, len(fi)), 3)] for f, v in sorted(ft.items(), key=lambda kv: (-kv[1], kv[0]))[:3]],
            'an': [[a, v] for a, v in sorted(an.items(), key=lambda kv: (-kv[1], kv[0]))[:4]],
            'nullf': int(sum(1 for i in fi if null_nc[NC[i]])), 'nullp': len(nullp),
            'ns': len(splits), 'splits': splits[:8],
            'cx': int(np.median(qx[mask])), 'cy': int(np.median(qy[mask])),
        })
    idf = {e: math.log(N / c) for e, c in all_ent.items()}
    frac = [{e: c / len(cl_papers[k]) for e, c in cl_ent[k].items()} for k in range(K_REGIONS)]
    for k in range(K_REGIONS):
        rel = []
        for j in range(K_REGIONS):
            if j == k:
                continue
            sh = [(min(frac[k][e], frac[j][e]) * idf[e], ename[e], e) for e in frac[k]
                  if e in frac[j] and cl_ent[k][e] >= 3 and cl_ent[j][e] >= 3]
            sh.sort(key=lambda t: (-t[0], t[1]))
            rel.append((sum(t[0] for t in sh), j, [[t[1], cl_ent[k][t[2]], cl_ent[j][t[2]]] for t in sh[:4]]))
        rel.sort(key=lambda t: (-t[0], t[1]))
        regions[k]['rel'] = [{'j': j, 'shared': s} for _, j, s in rel[:3]]

    # ---------- sub-regions (level-of-detail labels) ----------
    subs = []; sub_of = np.full(N, -1)
    for k in range(K_REGIONS):
        idx = np.where(lab == k)[0]; n = len(idx)
        m = max(2, min(8, round(n / 140)))
        sl = KMeans(n_clusters=m, n_init=10, random_state=SEED).fit_predict(np.c_[qx[idx], qy[idx]])
        reg_counter = cl_ent[k]
        used = {t[2] for t in distinctive(cl_ent[k], n, all_ent, N)[:3]}
        for s in range(m):
            mem = idx[sl == s]
            sid = len(subs); sub_of[mem] = sid
            sc = Counter(e for j in mem for e in p_ents[int(paper_ids[j])])
            dist = distinctive(sc, len(mem), reg_counter, n, top=6, min_c=3)
            names = [t[2] for t in dist if t[2] not in used] or [t[2] for t in dist]
            if not names:
                names = [ename[e] for e, _ in sorted(sc.items(), key=lambda kv: (-kv[1], ename[kv[0]]))[:1]]
            # a group too small to name is kept (its papers still belong to it) but gets no label
            small = len(mem) < max(12, 0.03 * n)
            subs.append({'k': k, 'n': int(len(mem)), 'label': [] if small else [display(x) for x in dedupe(names)[:2]],
                         'cx': int(np.median(qx[mem])), 'cy': int(np.median(qy[mem]))})

    # ---------- conditions present (same minor rule as labels.js MINOR_LABEL_MAX) ----------
    cond_papers = Counter(c for p in paper_ids for c in p_conds[int(p)])
    cond_rows = Counter(D['c'][Cc[i]] for i in np.where(f_keep)[0])
    conds = [c for c, _ in sorted(cond_papers.items(), key=lambda kv: (-kv[1], kv[0])) if cond_rows[c] >= 10]
    cbit = {c: i for i, c in enumerate(conds)}

    # ---------- write map ----------
    pm = [pm_of(int(p)) for p in paper_ids]
    years = [int(rows[int(p)][pidx['year']] or 0) for p in paper_ids]
    cmask = []
    for p in paper_ids:
        m = 0
        for c in p_conds[int(p)]:
            if c in cbit:
                m |= 1 << cbit[c]
        cmask.append(m)
    gl_splits = tally(np.where(f_keep)[0])
    versions = {'umap-learn': umap.__version__, 'scikit-learn': sklearn.__version__, 'numpy': np.__version__,
                'numba': numba.__version__, 'python': sys.version.split()[0]}
    out = data
    sizes = {}
    sizes['conn_map.json'] = dump({
        'meta': {'source_version': meta.get('version'), 'source_generated_utc': meta.get('generated_utc'),
                 'embedding_model': man.get('model'), 'q': Q, 'seed': SEED, 'k': K_REGIONS, 'versions': versions,
                 'method': 'Mean MiniLM finding embedding per paper; UMAP (cosine, 30 neighbours) to 2D for the layout and '
                           f'to 10D for KMeans (k={K_REGIONS}) regions; sub-regions are KMeans on the 2D layout inside each region.',
                 'excluded_papers': int(ex_paper.sum()), 'papers_without_findings': int((~keep & ~ex_paper).sum())},
        'n_papers': N, 'n_findings': int(f_keep.sum()), 'n_splits': len(gl_splits),
        'conds': conds, 'regions': regions, 'subs': subs, 'top_splits': gl_splits[:8],
        'papers': {'pmid': pm, 'x': qx.tolist(), 'y': qy.tolist(), 'k': lab.tolist(), 's': sub_of.tolist(),
                   'year': years, 'cm': cmask}}, out / 'conn_map.json')
    # label priority: rank by citations (0 = most cited)
    rk = sorted(range(N), key=lambda j: (-cited(int(paper_ids[j])), pm[j]))
    prio = [0] * N
    for r, j in enumerate(rk):
        prio[j] = r
    def short_title(t):
        t = (t or '').strip()
        return t if len(t) <= 110 else t[:107].rstrip() + '…'
    sizes['conn_papers.json'] = dump({'cite': [rows[int(p)][pidx['citation_short']] or '' for p in paper_ids],
                                      'title': [short_title(rows[int(p)][pidx['title']]) for p in paper_ids],
                                      'nf': [int(cnt[int(p)]) for p in paper_ids], 'rank': prio}, out / 'conn_papers.json')
    used_e = sorted({e for p in paper_ids for e in p_ents[int(p)]}, key=lambda e: (-all_ent[e], ename[e]))
    eid = {e: i for i, e in enumerate(used_e)}
    sizes['conn_ents.json'] = dump({'names': [ename[e] for e in used_e], 'np': [all_ent[e] for e in used_e],
                                    'paper': [sorted(eid[e] for e in p_ents[int(p)]) for p in paper_ids]}, out / 'conn_ents.json')
    sizes['conn_splits.json'] = dump({'n': len(gl_splits), 'splits': gl_splits}, out / 'conn_splits.json')

    # ---------- flow ----------
    small_seen = Counter()
    sysm = np.zeros(npap, dtype=np.int64); psm = np.zeros(npap, dtype=np.int64); cam = np.zeros(npap, dtype=np.int64); ftm = np.zeros(npap, dtype=np.int64)
    ft_vals = list(D['ft'])
    ps_vals = [v for v in D['ps'] if v not in ('—', 'not specified')]
    ca_vals = [v for v in D['ca'] if v != 'not-stated']
    slices = defaultdict(list)
    for i in np.where(f_keep)[0]:
        p = int(P[i])
        for s in {x.strip() for x in D['an'][AN[i]].split(',')}:
            if not s or s == '—':
                continue
            if s in SYS:
                sysm[p] |= 1 << SYS.index(s); slices['s:' + s].append(i)
            else:
                sysm[p] |= 1 << len(SYS); small_seen[s] += 1; slices['s:small'].append(i)
        v = D['ps'][PS[i]]
        if v in ps_vals:
            psm[p] |= 1 << ps_vals.index(v); slices['p:' + v].append(i)
        v = D['ca'][CA[i]]
        if v in ca_vals:
            cam[p] |= 1 << ca_vals.index(v); slices['c:' + v].append(i)
        v = D['ft'][FT[i]]
        ftm[p] |= 1 << ft_vals.index(v); slices['f:' + v].append(i)

    def fold(vals, mask_arr, prefix, labels):
        counts = {v: int(sum(1 for p in paper_ids if (mask_arr[p] >> j) & 1)) for j, v in enumerate(vals)}
        keep_v = [v for v in vals if counts[v] >= FOLD_MIN and v in labels]
        other = [v for v in vals if v not in keep_v and counts[v] > 0]
        return keep_v, other, counts
    ps_keep, ps_other, ps_counts = fold(ps_vals, psm, 'p', PS_LABEL)
    ca_keep, ca_other, ca_counts = fold(ca_vals, cam, 'c', CA_LABEL)
    ft_keep, ft_other, ft_counts = fold(ft_vals, ftm, 'f', FT_LABEL)
    for v in ft_other:
        slices['f:other'] += slices.get('f:' + v, [])
    for v in ps_other:
        slices['p:other'] += slices.get('p:' + v, [])
    for v in ca_other:
        slices['c:other'] += slices.get('c:' + v, [])
    for k in range(K_REGIONS):
        slices[f'k{k}'] = cl_find[k]

    find_of_paper = defaultdict(list)
    for i in np.where(f_keep)[0]:
        find_of_paper[int(P[i])].append(int(i))
    def describe(idx):
        ep = defaultdict(set); pp = set()
        for i in idx:
            p = int(P[i]); pp.add(p)
            if int(E[i]) not in blank_e:
                ep[int(E[i])].add(p)
        top = sorted(ep, key=lambda e: (-len(ep[e]), ename[e]))[:8]
        sp = tally([i for p in sorted(pp) for i in find_of_paper[p]])  # every finding of the band's papers
        return {'np': len(pp), 'nf': len(idx), 'top': [[ename[e], len(ep[e])] for e in top], 'ns': len(sp), 'splits': sp[:5]}
    info = {}
    for key in sorted(slices):
        if key.startswith('p:') and key[2:] in ps_other or key.startswith('c:') and key[2:] in ca_other \
                or key.startswith('f:') and key[2:] in ft_other:
            continue
        info[key] = describe(slices[key])

    def remask(mask_arr, vals, keep_v, other):
        out = []
        for p in paper_ids:
            m = 0; v = int(mask_arr[p])
            for j, name in enumerate(vals):
                if (v >> j) & 1:
                    m |= 1 << (keep_v.index(name) if name in keep_v else len(keep_v))
            out.append(m)
        return out
    sizes['conn_flow.json'] = dump({
        'n_papers': N,
        'sys': [[s, SYS_LABEL[s]] for s in SYS] + [['small', SYS_LABEL['small']]],
        'small_members': sorted(small_seen.items(), key=lambda kv: (-kv[1], kv[0])),
        'ps': [[v, PS_LABEL[v]] for v in ps_keep] + ([['other', 'Other subtypes']] if ps_other else []),
        'ps_other': [[v, PS_LABEL.get(v, v), ps_counts[v]] for v in ps_other],
        'ca': [[v, CA_LABEL[v]] for v in ca_keep] + ([['other', 'Other claim types']] if ca_other else []),
        'ca_other': [[v, CA_LABEL.get(v, v), ca_counts[v]] for v in ca_other],
        'ft': [[v, FT_LABEL[v]] for v in ft_keep] + ([['other', 'Other finding types']] if ft_other else []),
        'ft_other': [[v, FT_LABEL.get(v, v), ft_counts[v]] for v in ft_other],
        'fold_min': FOLD_MIN,
        'sysm': [int(sysm[p]) for p in paper_ids],
        'psm': remask(psm, ps_vals, ps_keep, ps_other),
        'cam': remask(cam, ca_vals, ca_keep, ca_other),
        'ftm': remask(ftm, ft_vals, ft_keep, ft_other),
        'info': info}, out / 'conn_flow.json')

    print('regions:')
    for r in regions:
        print(f"  {r['id']:2d} {r['n']:5d}  {' | '.join(r['label'])}  splits {r['ns']}")
    print('subtype papers', ps_counts, 'kept', ps_keep, 'folded', ps_other)
    print('finding type papers', ft_counts, 'kept', ft_keep, 'folded', ft_other)
    print('claim papers', ca_counts, 'kept', ca_keep, 'folded', ca_other)
    print('papers naming a subtype', int(sum(1 for p in paper_ids if psm[p])))
    print('global splits', len(gl_splits), gl_splits[:3])
    print(f'total {sum(sizes.values()) / 1e6:.2f} MB, runtime {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
