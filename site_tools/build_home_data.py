#!/usr/bin/env python3
"""build_home_data.py: data for the home page constellation and the "What stands out" band.

Reads ONLY <site>/data/*.json (the built site projection) and writes:
  <site>/data/home_map.json    POTS, conditions, POTS-specific and bridge topics, condition pairs
  <site>/data/home_stand.json  three stand-out counts (from meta.json) and one real example row each

Default view, same as the rest of the site: findings from papers whose paper flag has
recommended_use == "exclude" (retracted, correction notices) are left out of every count and example.

Run after every projection build:   python site_tools/build_home_data.py site
Checked by site_tools/verify_home.py (check(site_dir)).
"""
import json, math, re, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from signals_rules import Facets, flip_sides, entity_kinds, is_measured, MEASURED_KINDS, TREATMENT_SHARE_MAX  # noqa: E402  shared counting rules (one number per fact)

# Generic covariates: measured in almost every study, so raw counts make them look central.
GENERIC = ['age', 'female sex', 'sex', 'male sex', 'gender', 'female', 'male', 'heart rate', 'blood pressure',
           'systolic blood pressure', 'diastolic blood pressure', 'mean arterial pressure', 'body mass index',
           'BMI', 'body weight', 'weight', 'height', 'resting heart rate', 'education', 'smoking']
# Condition names that show up as entities. They are the map's nodes, not topics.
CONDNAMES = ['postural orthostatic tachycardia syndrome', 'POTS', 'dysautonomia', 'Ehlers-Danlos syndrome',
             'hypermobile Ehlers-Danlos syndrome', 'Mast cell activation syndrome', 'MCAS', 'fibromyalgia', 'migraine',
             'long COVID', 'Long COVID', 'post-COVID-19 condition', 'myalgic encephalomyelitis/chronic fatigue syndrome',
             'ME/CFS', 'Irritable bowel syndrome', 'autism', 'autism spectrum disorder', 'small fiber neuropathy',
             'Small fiber neuropathy', 'COVID-19', 'chronic fatigue syndrome', 'hypermobility spectrum disorder',
             'Generalized joint hypermobility', 'joint hypermobility']
# No merging of spelling variants: every topic uses the entity name exactly as stored, so its counts match the entity
# page and the Signals tables (one number per fact).
ALIAS = {}
# Condition keys that are not drawn as nodes (buckets, POTS itself, and groups too small to size).
SKIPC = ['general', 'multiple', 'other patient group', 'orthostatic_hypotension', 'IBD_gut', 'POTS']
RULES = {'floor': 6, 'lift': 2, 'top_specific': 10, 'bridges_per_cond': 2, 'max_topics': 16,
         'bridge_min_cond_papers': 5, 'topic_link_min': 5, 'pair_min_papers': 3, 'pairs_drawn': 8}
BLANK = '—'  # the facet dictionary's "no entity" value

GEN_L = {g.lower() for g in GENERIC}; CND_L = {g.lower() for g in CONDNAMES}


def kind(nm):
    l = nm.lower()
    return 'generic' if l in GEN_L else 'cond' if l in CND_L else 'ok'


def ok(nm):
    return kind(nm) == 'ok' and len(nm) <= 40 and ',' not in nm and ';' not in nm


def build(site):
    data = Path(site) / 'data'
    meta = json.load(open(data / 'meta.json'))
    F = Facets(data)
    D = F.D; E, Cc, P = F.cols['e'], F.cols['c'], F.cols['p']
    pm_of, excl, keep = F.pmids, F.excluded, F.keep

    ename = [ALIAS.get(nm, nm) for nm in D['e']]
    blank = D['e'].index(BLANK) if BLANK in D['e'] else -1

    ent_pc = defaultdict(lambda: defaultdict(set))                          # topic -> cond -> papers
    cond_papers = defaultdict(set)
    for i in np.nonzero(keep)[0]:
        p = int(P[i]); cond = D['c'][Cc[i]]; cond_papers[cond].add(p)
        e = int(E[i])
        if e == blank: continue
        nm = ename[e]
        ent_pc[nm][cond].add(p)
    ent_all = {nm: set().union(*d.values()) for nm, d in ent_pc.items()}
    n_ent_papers = len(set().union(*ent_all.values()))
    cond_univ = defaultdict(set)
    for nm, d in ent_pc.items():
        for c, ps in d.items(): cond_univ[c] |= ps
    NP = len(cond_univ['POTS'])
    pots_p = cond_papers['POTS']
    conds = [c for c in sorted(cond_papers, key=lambda c: (-len(cond_papers[c]), c)) if c not in SKIPC]
    R = RULES

    # POTS-specific topics: floor POTS papers, lift >= rule, top by POTS papers x log(lift)
    topics, hidden = [], []
    for nm, d in sorted(ent_pc.items()):
        n_p = len(d.get('POTS', ()))
        if n_p < R['floor']: continue
        lift = (n_p / NP) / (len(ent_all[nm]) / n_ent_papers)
        if not ok(nm):
            if kind(nm) == 'generic': hidden.append([nm, n_p])
            continue
        if lift < R['lift']: continue
        topics.append({'e': nm, 'np': n_p, 'lift': round(lift, 2), 'score': n_p * math.log(lift)})
    topics.sort(key=lambda t: (-t['score'], t['e']))
    topics = topics[:R['top_specific']]
    for t in topics: t['kind'] = 'specific'
    # bridge topics: for each condition, the topics it shares most with POTS
    have = {t['e'] for t in topics}
    for c in conds:
        cand = []
        for nm, d in ent_pc.items():
            if not ok(nm): continue
            a, b = len(d.get('POTS', ())), len(d.get(c, ()))
            if a < R['floor'] or b < R['bridge_min_cond_papers']: continue
            cand.append((min(a / NP, b / len(cond_univ[c])) * math.log(n_ent_papers / len(ent_all[nm])), nm, a))
        cand.sort(key=lambda x: (-x[0], x[1]))
        for _, nm, a in cand[:R['bridges_per_cond']]:
            if nm in have or len(topics) >= R['max_topics']: continue
            have.add(nm)
            topics.append({'e': nm, 'np': a, 'lift': round((a / NP) / (len(ent_all[nm]) / n_ent_papers), 2), 'score': 0, 'kind': 'bridge'})
    kinds = entity_kinds(data)
    flips = {(r['canonical_entity'], r['condition']): r for r in json.load(open(data / 'contradictions.json'))['rows'] if r['conflict_type'] == 'direction-flip'}
    dict_names = defaultdict(list)
    for i, nm in enumerate(D['e']): dict_names[ALIAS.get(nm, nm)].append(nm)
    for t in topics:
        nm = t['e']
        t['links'] = [[c, len(ent_pc[nm].get(c, ()))] for c in conds if len(ent_pc[nm].get(c, ())) >= R['topic_link_min']]
        t['ent'] = nm if nm in D['e'] else dict_names[nm][0]   # name the entity page knows
        t['tally'] = F.tally(t['ent'], 'POTS')
        # ring: papers split both ways AND the topic is a measured kind (same rule as the Start page's disagreements)
        t['measured'] = is_measured(F, kinds, t['ent'], 'POTS', (flips.get((t['ent'], 'POTS')) or {}).get('entity_kind'))
        t['disagree'] = t['tally']['up'] > 0 and t['tally']['dn'] > 0 and t['measured']
        del t['score']

    idf = {nm: math.log(n_ent_papers / len(s)) for nm, s in ent_all.items()}

    def shared(c1, c2, k=3):
        out = []
        for nm, d in ent_pc.items():
            if not ok(nm): continue
            a, b = len(d.get(c1, ())), len(d.get(c2, ()))
            if a >= R['pair_min_papers'] and b >= R['pair_min_papers']:
                out.append((min(a / len(cond_univ[c1]), b / len(cond_univ[c2])) * idf[nm], nm, a, b))
        out.sort(key=lambda x: (-x[0], x[1]))
        return sum(o[0] for o in out), [[nm, a, b] for _, nm, a, b in out[:k]]

    # where papers split, per condition: the contradictions.json direction-flip row with the largest smaller side
    con_rows = json.load(open(data / 'contradictions.json'))['rows']
    cnodes = []
    for c in conds:
        _, sh = shared('POTS', c)
        best = None
        for r in con_rows:
            e = r['canonical_entity']
            if r['condition'] != c or r['conflict_type'] != 'direction-flip' or not ok(e) or e not in D['e']: continue
            if (set(map(str, r['pmids_A'])) | set(map(str, r['pmids_B']))) & excl: continue
            hi, lo = flip_sides(r)
            key = (min(hi, lo), hi + lo, -r['rank'])
            if best is None or key > best[0]: best = (key, e)
        cnodes.append({'c': c, 'n': len(cond_papers[c]), 'both': len(cond_papers[c] & pots_p), 'shared': sh,
                       'split': F.tally(best[1], c) if best else None})
    cc = []
    for i, c1 in enumerate(conds):
        for c2 in conds[i + 1:]:
            s, sh = shared(c1, c2)
            cc.append({'a': c1, 'b': c2, 's': round(s, 3), 'both': len(cond_papers[c1] & cond_papers[c2]), 'shared': sh})
    cc.sort(key=lambda r: (-r['s'], r['a'], r['b']))

    alias_used = {k: v for k, v in ALIAS.items() if k in D['e']}
    home_map = {'version': meta['version'], 'pots': {'n': len(pots_p)}, 'conds': cnodes, 'topics': topics,
                'cc': cc[:R['pairs_drawn']], 'hidden': sorted(hidden, key=lambda r: (-r[1], r[0])),
                'rules': dict(R, measured_kinds=sorted(MEASURED_KINDS), treatment_share_max=TREATMENT_SHARE_MAX), 'alias': alias_used, 'skip_conds': SKIPC, 'generic': GENERIC, 'condnames': CONDNAMES,
                'excluded_papers': len(excl & set(pm_of))}

    # ---------- What stands out ----------
    m = meta['counts']
    topic_names = [t['e'].lower() for t in topics]
    con = json.load(open(data / 'contradictions.json'))
    cex = next(r for r in con['rows'] if r['condition'] == 'POTS' and r['conflict_type'] == 'direction-flip'
               and not (set(map(str, r['pmids_A'])) | set(map(str, r['pmids_B']))) & excl)
    nul = json.load(open(data / 'null_results.json')); f = nul['fields']; ix = {k: f.index(k) for k in f}
    nex = None
    for sh in nul['shards']:
        for r in json.load(open(data / sh['file']))['rows']:
            ent, q = r[ix['canonical_entity']], r[ix['provenance_quote_trunc']] or ''
            if (r[ix['condition']] == 'POTS' and r[ix['null_class']] == 'treatment null' and ent and str(r[ix['canonical_pmid']]) not in excl
                    and 40 <= len(q) <= 170 and re.search(r'\b[Pp]\s*[=<>]', q)
                    and any(re.search(r'\b' + re.escape(t) + r'\b', ent.lower()) for t in topic_names)):
                nex = r; break
        if nex: break
    und = json.load(open(data / 'understudied.json'))
    uex = next(r for r in und['rows'] if r['condition'] == 'POTS' and r['n_papers'] >= 2 and not set(map(str, r['pmids'])) & excl)
    home_stand = {
        'version': meta['version'],
        'contra_total': m['contradictions_total'], 'nulls': m['nulls'], 'under_total': m['understudied_total'],
        'cex': {'e': cex['canonical_entity'], 'c': cex['condition'], 'a': cex['n_papers_A'], 'b': cex['n_papers_B'],
                'da': cex['side_A_direction'], 'db': cex['side_B_direction'], 'rank': cex.get('rank')},
        'nex': {'e': nex[ix['canonical_entity']], 'pmid': str(nex[ix['canonical_pmid']]), 'year': nex[ix['year']],
                'q': nex[ix['provenance_quote_trunc']], 'nc': nex[ix['null_class']], 'c': nex[ix['condition']]},
        'uex': {'e': uex['canonical_entity'], 'c': uex['condition'], 'n': uex['n_papers'], 'nf': uex['n_findings'],
                'dir': uex['direction'], 'pmids': [str(x) for x in uex['pmids']]},
    }
    return home_map, home_stand


def main():
    site = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'site')
    hm, hs = build(site)
    for name, obj in (('home_map.json', hm), ('home_stand.json', hs)):
        s = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
        (site / 'data' / name).write_text(s, encoding='utf-8')
        print(name, f'{len(s.encode()) / 1e3:.1f} KB')
    print('POTS papers', hm['pots']['n'], '| conditions', [c['c'] for c in hm['conds']])
    print('topics', [(t['e'], t['np'], t['kind'], t['disagree']) for t in hm['topics']])
    print('stand', hs['cex']['e'], '|', hs['nex']['e'], '|', hs['uex']['e'])


if __name__ == '__main__':
    main()
