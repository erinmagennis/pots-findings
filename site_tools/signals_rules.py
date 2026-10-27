"""signals_rules.py: shared counting rules so a fact shows the same number on every page.

Disagreement rule (same as contradictions.json "rule", build_v12_projection.py): only findings that compare people with the
condition to people without it count, i.e. facet `dr` (direction_reference, typos normalised) == "vs-disease-state".  A
change after a treatment (vs-intervention) or a finding with no reference (not-applicable) is never a disagreement.
Higher / lower papers for an entity in a condition: the entity name as stored in findings_facets (no merging of spellings),
the condition label, vs-disease-state findings only, distinct papers per side, side "higher" = direction "elevated", side
"lower" = "depleted/reduced", findings from exclude-flagged papers left out. No-difference papers: distinct papers with a
vs-disease-state finding on the same entity and condition whose direction is "no significant difference", same exclusion.
Checked against every direction-flip row of contradictions.json by verify_home.py.
A disagreement (direction flip) also needs at least 2 distinct papers with vs-disease-state findings for that entity and
condition, as build_v12_projection.py does: one paper reporting both directions is not a disagreement between studies. Pages that list
flips apply this (build_connections_data.py; contra_flip_total in meta.json counts the same set).
"""
import json
from pathlib import Path

import numpy as np

# kinds where "higher/lower" reads plainly; same set and rule as build_start_here.py picks disagreement examples
MEASURED_KINDS = {'physiological-measure', 'gene/protein', 'cell-type'}
TREATMENT_SHARE_MAX = 0.5   # a chemical/metabolite counts as measured only when at most half its findings are treatment findings

HIGHER, LOWER, NODIFF = 'elevated', 'depleted/reduced', 'no significant difference'
DISEASE_REF = 'vs-disease-state'   # facet `dr`: the only direction_reference that counts for higher / lower / no difference


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
        self.cols = {k: np.asarray(v) for k, v in fac['cols'].items() if k in ('e', 'c', 'd', 'p', 'ft')}
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
        return {'e': entity, 'c': cond, 'up': n(HIGHER), 'dn': n(LOWER), 'nu': n(NODIFF)}

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
