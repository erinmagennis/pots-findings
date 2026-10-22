#!/usr/bin/env python3
"""build_v12_projection.py — project the five pots-findings v1.2 packages into the site/data contract.

Reads  : packages/*/data/<tier>_findings.parquet (corpus order t1, t2a, t2b, t3, t4),
         packages/dysautonomia-core-findings/data/entity_vocabulary_crosstier.parquet,
         data/corpus_augmented.parquet (paper metadata: authors, journal, OA, citations),
         data/paper_metadata.parquet (Tier-1 PMC urls), data/pmid_dedup_map.parquet (9 title merges).
Writes : site/data/{meta,findings_facets,papers,entities,autocomplete}.json, text_NN/detail_NN shards,
         discovery tables (associations/contradictions/understudied/null_results/convergence.json),
         validation/v12_golden_facts.json.  Embeddings are produced by embed_v12.py (separate env).

Contract: SITE_CONTRACT.md "File shapes". Encoding rules (first-appearance dictionaries, em-dash missing
token, truncate = s[:cap-1].rstrip()+ellipsis, placeholder text for null finding_text) are inherited
from site_generator.py and reproduced here so the frontend needs no change.

Entity identity (site_entity): the authority-verified ontology id where the row has one
(ontology_id_verification in {authority_verified, authority_verified_retrospective}); otherwise the
cross-tier canonical name from entity_vocabulary_crosstier (raw entity -> canonical_entity); otherwise
the raw entity string.  Rows sharing a verified id are merged under one display name.

Tiers are provenance only: emitted as facet `ti` (tier_source) for the download/explain pages, never a headline.
"""
import argparse, json, math, os, re, sys, time
from datetime import datetime, timezone
import numpy as np, pandas as pd
from scipy.stats import hypergeom

MISS = "\u2014"; SHARD_ROWS = 6000
VERIFIED = {"authority_verified", "authority_verified_retrospective"}
ORDER = ["tier1", "tier2a", "tier2b", "tier3", "tier4"]
PKG = {"tier1": "dysautonomia-core-findings", "tier2a": "comorbid-conditions-findings-a", "tier2b": "comorbid-conditions-findings-b",
       "tier3": "postviral-autism-findings", "tier4": "migraine-hypermobility-findings"}
FACET_MAP = {"e": "site_entity", "c": "condition", "d": "direction", "tr": "evidence_tier", "ce": "certainty", "ft": "finding_type",
             "ek": "entity_kind", "mc": "id_status", "nc": "null_or_failed_result", "st": "study_type", "ca": "causal_or_correlational",
             "an": "anatomical_system", "ps": "pots_subtype", "ag": "population_age_group", "sx": "sex_hormonal", "th": "theme",
             "sr": "source_stream", "es": "evidence_stratum", "rt": "relation_type", "cv": "is_covid_associated", "ti": "tier_source",
             "sl": "source_literature"}
DETAIL_SPEC = {"quote": ("provenance_quote", 200), "quant": ("quantitative_detail", None), "eff": ("effect_size", None),
               "path": ("pathway_or_mechanism", None), "lim": ("limitations_stated", 300), "fut": ("future_direction", 300),
               "npart": ("n_participants", None), "comp": ("comparator", None), "symp": ("symptom_correlate", 300),
               "treat": ("treatment_class", None), "sec": ("provenance_section", None), "ont": ("site_primary_id", None)}
PAPER_FIELDS = ["pmid", "first_author", "authors", "author_count", "journal", "year", "doi_url", "pubmed_url", "pmc_url",
                "citation_short", "n_findings", "is_open_access", "cited_by_count", "title"]
_STR_EMPTY = {"pmc_url", "doi_url", "pubmed_url", "citation_short", "authors", "first_author", "journal", "title"}
_DEFAULTS = {"is_open_access": False, "cited_by_count": 0}
TIER_RANK = ["meta-analysis", "RCT", "cohort", "case-control", "cross-sectional", "case-series", "case-report",
             "mechanistic/in-vitro", "review/expert-opinion"]
UP = {"elevated", "increased", "higher", "present", "improved"}; DOWN = {"depleted/reduced", "decreased", "lower", "reduced", "worsened"}
ID_STATUS = {"authority_verified": "verified at authority", "authority_verified_retrospective": "verified at authority",
             "id_withheld_unverified_v1.2": "id withheld (unverified)", "no_id": "no identifier"}


def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)
def jdump(path, obj):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
def fmtnum(x): return f"{int(x):,}"
def encode_column(series, missing=MISS):
    vals = series.astype(object).where(series.notna(), missing).astype(str)
    seen, codes, dic = {}, np.empty(len(vals), dtype=np.int32), []
    for i, v in enumerate(vals.values):
        c = seen.get(v)
        if c is None: c = len(dic); seen[v] = c; dic.append(v)
        codes[i] = c
    return dic, codes.tolist()
def truncate(value, cap):
    if value is None: return None
    s = str(value)
    if not cap or len(s) <= cap: return s
    return s[:cap - 1].rstrip() + "\u2026"
def text_or_placeholder(t, rs, rt, ro):
    if pd.notna(t): return str(t)
    return f"[no summary sentence extracted] {rs} \u2014 {rt} \u2014 {ro}"
def tier_best(vals):
    v = [x for x in vals if isinstance(x, str) and x in TIER_RANK]
    return min(v, key=TIER_RANK.index) if v else None
def first_nn(s):
    s = s.dropna(); return None if len(s) == 0 else s.iloc[0]
def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); r = np.empty(n); r[o] = np.arange(1, n + 1)
    q = p * n / r; qs = np.minimum.accumulate(q[o][::-1])[::-1]; out = np.empty(n); out[o] = np.minimum(qs, 1.0); return out


def load(root):
    D = pd.concat([pd.read_parquet(f"{root}/packages/{PKG[t]}/data/{t}_findings.parquet").assign(package=PKG[t]) for t in ORDER], ignore_index=True)
    EV = pd.read_parquet(f"{root}/packages/{PKG['tier1']}/data/entity_vocabulary_crosstier.parquet")
    CA = pd.read_parquet(f"{root}/data/corpus_augmented.parquet")
    PM = pd.read_parquet(f"{root}/data/paper_metadata.parquet")
    DM = pd.read_parquet(f"{root}/data/pmid_dedup_map.parquet")
    return D, EV, CA, PM, DM


PREFIX_PREF = ["HGNC", "CHEBI", "MeSH", "UniProt", "HP", "UBERON", "CL", "NCBITaxon", "GO"]


def add_site_entity(D, EV):
    """site_entity = one display name per CONCEPT group.

    Groups: (1) every verified ontology id is a group; (2) id groups are merged when their dominant lower-cased
    surface form or their authority label coincide (IL-6/HGNC with Interleukin-6/MeSH, aldosterone/ChEBI with
    aldosterone/MeSH); (3) rows without a verified id join the group whose lower-cased cross-tier canonical name
    equals an id group's surface form or label, otherwise form a name group of their own.
    Display name = the most frequent exact surface string in the group. Mechanical throughout; no model."""
    canon = dict(zip(EV.raw_entity.astype(str), EV.canonical_entity.astype(str)))
    raw = D["entity"]
    ce = raw.map(lambda x: canon.get(str(x), str(x)) if pd.notna(x) else None)
    cel = ce.str.lower().str.strip()
    ver = D.ontology_id_verification.isin(VERIFIED) & D.entity_ontology_id_resolved.notna()
    D["site_ontology_id"] = D.entity_ontology_id_resolved.where(ver, None)
    label = D["entity_ontology_label"].astype(object).where(D["entity_ontology_label"].notna(), None) if "entity_ontology_label" in D.columns else pd.Series([None] * len(D))
    # union-find over id groups
    parent = {}
    def find(x):
        while parent.setdefault(x, x) != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b): parent[find(a)] = find(b)
    COMPOUND = re.compile(r"[,;/]| and | or |\+|&|\(")
    mm = D["ontology_id_match_mode"].astype(str) if "ontology_id_match_mode" in D.columns else pd.Series([""] * len(D), index=D.index)
    sub = D[ver].assign(surf=raw[ver].astype(str).str.lower().str.strip(), lab=label[ver].astype(object).map(lambda x: str(x).lower().strip() if x else None), mm=mm[ver])
    key_to_id = {}
    for oid, g in sub.groupby("site_ontology_id"):
        find(oid)
        # keys that may merge id groups: the dominant surface form of SINGLE-entity rows (no compound strings, no
        # compound_partial matches) and the authority label.  A compound string like "serotonin, norepinephrine"
        # must never become a merge key — it would fuse two real concepts.
        single = g[(g.mm != "compound_partial") & ~g.surf.str.contains(COMPOUND)]
        keys = set(g.lab.dropna().unique())
        if len(single): keys.add(single.surf.value_counts().index[0])
        keys = {k for k in keys if k and not COMPOUND.search(k)}
        for k in keys:
            if k in key_to_id: union(oid, key_to_id[k])
            else: key_to_id[k] = oid
    # group id per row: id-root for verified rows; for name rows, the id-root whose key matches the canonical name, else the name
    grp = pd.Series([None] * len(D), index=D.index, dtype=object)
    grp[ver] = D.loc[ver, "site_ontology_id"].map(find)
    nm = (~ver) & ce.notna()
    rawl = raw.astype(str).str.lower().str.strip()
    def _name_key(k_canon, k_raw):
        for k in (k_raw, k_canon):
            if k in key_to_id and not COMPOUND.search(k): return find(key_to_id[k])
        return "name:" + k_canon
    grp[nm] = [_name_key(a, b) for a, b in zip(cel[nm], rawl[nm])]
    D["concept_group"] = grp
    # display name = most frequent exact surface string per group
    has = grp.notna()
    def _disp(s):
        single = s[~s.str.contains(COMPOUND)]
        return (single if len(single) else s).value_counts().index[0]
    disp = D[has].assign(s=raw[has].astype(str)).groupby("concept_group")["s"].agg(_disp)
    D["site_entity"] = grp.map(disp)
    # primary id per group (preference order) and all ids
    ids_by_grp = D[ver].groupby(D.loc[ver, "concept_group"])["site_ontology_id"].agg(lambda s: sorted(set(s), key=lambda i: (PREFIX_PREF.index(i.split(":")[0]) if i.split(":")[0] in PREFIX_PREF else 99, i)))
    D["group_ids"] = grp.map(ids_by_grp)
    D["site_primary_id"] = D["group_ids"].map(lambda l: l[0] if isinstance(l, list) and l else None)
    D["id_status"] = D.ontology_id_verification.map(ID_STATUS).fillna("no identifier")
    in_id_group = has & grp.map(lambda g: isinstance(g, str) and not g.startswith("name:"))
    D["entity_basis"] = np.where(ver, "verified ontology id", np.where(in_id_group, "name matched to verified id group", np.where(nm & (cel != raw.astype(str).str.lower().str.strip()), "cross-tier canonical name", np.where(nm, "entity string", None))))
    return D


def paper_table(D, CA, PM, DM):
    dedup = {str(a): str(b) for a, b, ap in zip(DM.pmid, DM.canonical_pmid, DM.merge_applied) if ap and str(a) != str(b)}
    D["cpmid"] = D.pmid.astype(str).map(lambda x: dedup.get(x, x))
    nf = D.groupby("cpmid").size()
    c = CA.drop_duplicates("pmid").set_index(CA.drop_duplicates("pmid").pmid.astype(str))
    pm1 = PM.drop_duplicates("pmid").set_index(PM.drop_duplicates("pmid").pmid.astype(str))
    rows = []
    for p in D.cpmid.drop_duplicates():
        ca = c.loc[p] if p in c.index else None
        d = D[D.cpmid == p].iloc[0]
        au = (str(ca.authors) if ca is not None and pd.notna(ca.authors) else "").rstrip(".")
        names = [x.strip() for x in au.split(",") if x.strip()]
        yr = int(d.year) if pd.notna(d.year) else (int(ca.year) if ca is not None and pd.notna(ca.year) else None)
        journal = d.journal if pd.notna(d.journal) else (ca.journal if ca is not None else None)
        title = d.title if pd.notna(d.title) else (ca.title if ca is not None else None)
        doi = d.doi if pd.notna(d.doi) else (ca.doi if ca is not None and pd.notna(ca.doi) else None)
        pmc = pm1.loc[p].pmc_url if p in pm1.index and pd.notna(pm1.loc[p].pmc_url) else (f"https://www.ncbi.nlm.nih.gov/pmc/articles/{d.pmcid}/" if "pmcid" in D.columns and pd.notna(d.pmcid) else None)
        fa = names[0] if names else None
        rows.append(dict(pmid=p, first_author=fa, authors=au or None, author_count=len(names) or None, journal=journal, year=yr,
                         doi_url=f"https://doi.org/{doi}" if doi else None, pubmed_url=f"https://pubmed.ncbi.nlm.nih.gov/{p}/", pmc_url=pmc,
                         citation_short=(f"{fa} et al. ({yr}) {journal}" if fa and yr and journal else None), n_findings=int(nf[p]),
                         is_open_access=bool(ca is not None and str(ca.isOA) == "Y"), cited_by_count=(int(ca.cites) if ca is not None and pd.notna(ca.cites) else 0), title=title))
    P = pd.DataFrame(rows)
    return P, dedup


def build_papers(P):
    def ser(v, f):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return _DEFAULTS.get(f, "" if f in _STR_EMPTY else None)
        if isinstance(v, (np.integer,)): return int(v)
        if isinstance(v, (np.floating,)): return float(v)
        if isinstance(v, (np.bool_,)): return bool(v)
        return v
    return {"fields": PAPER_FIELDS, "rows": [[ser(r[f], f) for f in PAPER_FIELDS] for r in P.to_dict("records")]}


def build_facets(D, pmid_order):
    out = {"n": int(len(D)), "shard_rows": SHARD_ROWS, "n_shards": int(math.ceil(len(D) / SHARD_ROWS)), "dicts": {}, "cols": {}}
    for k, col in FACET_MAP.items(): out["dicts"][k], out["cols"][k] = encode_column(D[col])
    out["dicts"]["es_str"], es_col = encode_column(D["entity"], missing="")
    pos = {p: i for i, p in enumerate(pmid_order)}
    out["cols"]["y"] = D["year"].fillna(0).astype(int).tolist()
    out["cols"]["p"] = D["cpmid"].map(pos).astype(int).tolist()
    out["cols"]["q"] = D["quantitative_detail"].notna().astype(int).tolist()
    out["cols"]["sd"] = [0] * len(D)
    out["cols"]["es_str"] = es_col
    out["cols"]["has_can"] = D["site_entity"].notna().astype(int).tolist()
    m = D.site_entity.notna() & D.entity.notna() & (D.entity.astype(str) != D.site_entity.astype(str))
    out["orig_entity"] = {str(i): v for i, v in zip(np.where(m.values)[0], D.entity[m].astype(str))}
    out["facet_fields"] = dict(FACET_MAP)
    n = len(D); ver = D.site_ontology_id.notna()
    out["coverage"] = {"entity_string_rows": int(D.entity.notna().sum()), "entity_string_pct": round(D.entity.notna().mean() * 100, 1),
                       "canonical_rows": int(D.site_entity.notna().sum()), "canonical_pct": round(D.site_entity.notna().mean() * 100, 1),
                       "entity_unmapped_rows": int((D.entity.notna() & D.site_entity.isna()).sum()),
                       "papers_with_canonical": int(D.cpmid[D.site_entity.notna()].nunique()), "papers_total": int(D.cpmid.nunique()),
                       "verified_id_rows": int(ver.sum()), "verified_id_pct": round(ver.mean() * 100, 1), "verified_ids_distinct": int(D.site_ontology_id.nunique()), "concept_groups_with_id": int(D.loc[D.site_primary_id.notna(), "concept_group"].nunique()), "rows_in_id_groups": int(D.site_primary_id.notna().sum()),
                       "strings_mapped": int(D.loc[D.entity_basis == "cross-tier canonical name", "entity"].astype(str).str.lower().nunique()),
                       "strings_total": int(D.entity.dropna().astype(str).str.lower().nunique())}
    return out


def build_entities(D):
    s = D[D.site_entity.notna()]
    npu = s.groupby("site_entity", sort=False).cpmid.nunique()
    order = npu.sort_values(ascending=False, kind="quicksort").index.tolist()
    out = {}
    for n, g in s.groupby("site_entity", sort=False):
        gids = first_nn(g.group_ids); oid = gids[0] if isinstance(gids, list) and gids else None
        out[n] = {"name": n, "kind": first_nn(g.entity_kind), "mapc": ("verified ontology id" if oid else first_nn(g.entity_basis)),
                  "oid": oid, "osrc": (oid.split(":")[0] if isinstance(oid, str) and ":" in oid else None), "ids": gids if isinstance(gids, list) else [],
                  "olabel": first_nn(g.entity_ontology_label) if "entity_ontology_label" in g else None,
                  "basis": first_nn(g.entity_basis),
                  "nf": int(len(g)), "np_": int(g.cpmid.nunique()), "npd": int(g.cpmid.nunique()),
                  "origs": sorted(set(x for x in g.entity.dropna().astype(str) if x != n))[:60],
                  "dirs": {k: int(v) for k, v in g.direction.value_counts().items()},
                  "tiers": {k: int(v) for k, v in g.evidence_tier.value_counts().items()},
                  "conds": {k: int(v) for k, v in g.condition.value_counts().items()}}
    return {"n": len(order), "entities": [out[n] for n in order]}


def discovery(D, P):
    """Five discovery tables over the full corpus, keyed on site_entity. Column names follow the shipped tables."""
    E = D[D.site_entity.notna()].copy()
    universe = E.cpmid.nunique()
    # --- associations: entity pairs co-occurring in papers ---
    per_paper = E.groupby("cpmid").site_entity.agg(lambda s: sorted(set(s)))
    ent_papers = E.groupby("site_entity").cpmid.nunique()
    kind = E.groupby("site_entity").entity_kind.agg(first_nn); mapc = E.groupby("site_entity").id_status.agg(first_nn)
    conds = E.groupby("site_entity").condition.agg(lambda s: sorted(set(s.dropna())))
    from collections import Counter, defaultdict
    pair_n = Counter(); pair_pm = defaultdict(list)
    for pm, ents in per_paper.items():
        if len(ents) > 60: ents = [e for e in ents if ent_papers[e] >= 3][:60]
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                k = (ents[i], ents[j]); pair_n[k] += 1
                if len(pair_pm[k]) < 25: pair_pm[k].append(pm)
    rows = []
    for (a, b), nb in pair_n.items():
        if nb < 3: continue
        na, nb_ = int(ent_papers[a]), int(ent_papers[b])
        exp = na * nb_ / universe; p = float(hypergeom.sf(nb - 1, universe, na, nb_))
        rows.append(dict(entity_a=a, entity_b=b, entity_kind_a=kind[a], entity_kind_b=kind[b], map_confidence_a=mapc[a], map_confidence_b=mapc[b],
                         n_papers_a=na, n_papers_b=nb_, n_papers_both=int(nb), n_papers_both_incl_split_derived=int(nb), expected_papers_both=round(exp, 2),
                         lift=round(nb / exp, 3) if exp else None, jaccard=round(nb / (na + nb_ - nb), 3), p_hypergeom=p,
                         conditions=sorted(set(conds[a]) | set(conds[b])), n_conditions=len(set(conds[a]) | set(conds[b])), n_papers_universe=int(universe),
                         cross_kind=bool(kind[a] != kind[b]), pmids=pair_pm[(a, b)], pmids_truncated=bool(nb > 25)))
    A = pd.DataFrame(rows)
    if len(A):
        A["q_bh"] = bh(A.p_hypergeom); A["significant_fdr05"] = A.q_bh < 0.05
        A["neglog10_q"] = -np.log10(A.q_bh.clip(lower=1e-300)); A["assoc_score_recomputed"] = (A.neglog10_q.clip(upper=50) * 2 * np.log1p(A.lift.fillna(0))).round(3)
        assoc_total, assoc_sig_total = int(len(A)), int(A.significant_fdr05.sum())
        A = A.sort_values(["q_bh", "n_papers_both"], ascending=[True, False]).head(3000).reset_index(drop=True); A["rank"] = A.index + 1
    if not len(A): assoc_total = assoc_sig_total = 0
    assoc = {"n": int(len(A)), "total": assoc_total, "significant_total": assoc_sig_total, "universe_papers": int(universe), "rows": A.to_dict("records")}
    # --- contradictions: direction flips and null-vs-positive within entity x condition ---
    rows = []
    for (e, c), g in E.groupby(["site_entity", "condition"]):
        if g.cpmid.nunique() < 2: continue
        d = g.direction.fillna("")
        sides = [("direction-flip", g[d.isin(UP)], g[d.isin(DOWN)]), ("null-vs-positive", g[d.isin(UP | DOWN)], g[(d == "no significant difference") | g.null_or_failed_result.astype(str).str.startswith("null")])]
        for ct, ga, gb in sides:
            if ga.cpmid.nunique() == 0 or gb.cpmid.nunique() == 0: continue
            pa, pb = set(ga.cpmid), set(gb.cpmid)
            rows.append(dict(conflict_type=ct, canonical_entity=e, entity_kind=first_nn(g.entity_kind), condition=c, ontology_id=first_nn(g.site_primary_id),
                             side_A_direction=ga.direction.value_counts().index[0], n_papers_A=len(pa), n_findings_A=int(len(ga)), top_tier_A=tier_best(ga.evidence_tier), pmids_A=sorted(pa)[:40],
                             side_B_direction=gb.direction.value_counts().index[0], n_papers_B=len(pb), n_findings_B=int(len(gb)), top_tier_B=tier_best(gb.evidence_tier), pmids_B=sorted(pb)[:40],
                             n_papers_total=int(g.cpmid.nunique()), n_papers_both_sides=len(pa & pb), tiers="|".join(sorted(set(g.tier_source))),
                             source_literatures=",".join(sorted(set(g.source_literature.dropna().astype(str)))),
                             conflict_strength=round(100 * min(len(pa), len(pb)) / max(len(pa), len(pb)) * math.log1p(len(pa) + len(pb)), 3), map_confidence_min=first_nn(g.id_status)))
    C = pd.DataFrame(rows)
    c_total = int(len(C)); c_flip = int((C.conflict_type == "direction-flip").sum()) if len(C) else 0; c_nvp = int((C.conflict_type == "null-vs-positive").sum()) if len(C) else 0
    if len(C): C = C.sort_values(["conflict_strength"], ascending=False).head(3000).reset_index(drop=True); C["rank"] = C.index + 1
    contra = {"n": int(len(C)), "total": c_total, "flip_total": c_flip, "null_vs_positive_total": c_nvp, "rows": C.to_dict("records")}
    # --- understudied: entity x condition with few papers ---
    rows = []
    tot = E.groupby("site_entity").cpmid.nunique()
    for (e, c), g in E.groupby(["site_entity", "condition"]):
        npap = g.cpmid.nunique()
        if npap > 3 or len(g) < 2: continue
        bt = tier_best(g.evidence_tier)
        rows.append(dict(canonical_entity=e, entity_kind=first_nn(g.entity_kind), map_confidence=first_nn(g.id_status), condition=c, direction=g.direction.value_counts().index[0] if g.direction.notna().any() else None,
                         n_papers=int(npap), n_findings=int(len(g)), mean_year=round(float(g.year.mean()), 1) if g.year.notna().any() else None, max_year=int(g.year.max()) if g.year.notna().any() else None,
                         min_year=int(g.year.min()) if g.year.notna().any() else None, best_tier=bt, case_report_only=bool(bt == "case-report"), n_papers_entity_total=int(tot[e]),
                         tiers="|".join(sorted(set(g.tier_source))), source_literatures=",".join(sorted(set(g.source_literature.dropna().astype(str)))), is_thin=bool(len(g) < 3),
                         pmids=sorted(set(g.cpmid)), replication_score=round(float(len(g)) / npap + (TIER_RANK.index(bt) if bt else 9) / 3, 4)))
    U = pd.DataFrame(rows)
    u_total = int(len(U))
    if len(U): U = U.sort_values(["n_findings", "mean_year"], ascending=[False, False]).head(5000).reset_index(drop=True); U["rank"] = U.index + 1
    under = {"n": int(len(U)), "total": u_total, "rows": U.to_dict("records")}
    # --- null results ---
    nm = (D.direction == "no significant difference") | D.null_or_failed_result.astype(str).str.startswith("null")
    N = D[nm]
    rows = [dict(canonical_pmid=r.cpmid, tier=r.tier_source, source_literature=r.source_literature,
                 null_class=("treatment null" if pd.notna(r.treatment_class) else "biomarker/mechanism null"),
                 null_source=("both (explicit flag + no-significant-difference direction)" if (r.direction == "no significant difference" and str(r.null_or_failed_result).startswith("null")) else ("explicit flag" if str(r.null_or_failed_result).startswith("null") else "no-significant-difference direction")),
                 null_or_failed_result=r.null_or_failed_result, direction=r.direction, canonical_entity=r.site_entity, entity=r.entity, entity_kind=r.entity_kind,
                 canonical_ontology_id=r.site_primary_id, condition=r.condition, finding_type=r.finding_type, treatment_class=r.treatment_class, evidence_tier=r.evidence_tier,
                 certainty=r.certainty, study_type=r.study_type, n_participants=r.n_participants, comparator=r.comparator, pots_subtype=r.pots_subtype,
                 population_age_group=r.population_age_group, is_covid_associated=r.is_covid_associated, split_derived=False, map_confidence=r.id_status,
                 year=(int(r.year) if pd.notna(r.year) else None), provenance_section=r.provenance_section,                  provenance_quote_trunc=truncate(r.provenance_quote if pd.notna(r.provenance_quote) else None, 200), row_index=int(r.Index))
            for r in N.itertuples()]
    nulls = {"n": len(rows), "rows": rows}
    # --- convergence: same entity, concordant direction across >= 2 source literatures ---
    rows = []
    for e, g in E[E.direction.isin(UP | DOWN)].groupby("site_entity"):
        if g.cpmid.nunique() < 3: continue
        for dirn, gg in g.groupby(g.direction.map(lambda x: "elevated" if x in UP else "depleted/reduced")):
            lits = sorted(set(gg.source_literature.dropna().astype(str)))
            if len(lits) < 2: continue
            opp = g[~g.direction.map(lambda x: "elevated" if x in UP else "depleted/reduced").eq(dirn)]
            rows.append(dict(canonical_entity=e, entity_kind=first_nn(gg.entity_kind), ontology_id=first_nn(gg.site_primary_id), concordant_direction=dirn,
                             n_source_literatures=len(lits), source_literatures=",".join(lits), n_conditions=int(gg.condition.nunique()), conditions=",".join(sorted(set(gg.condition.dropna().astype(str)))),
                             n_papers=int(gg.cpmid.nunique()), n_findings=int(len(gg)), n_papers_opposite=int(opp.cpmid.nunique()), tiers="|".join(sorted(set(gg.tier_source))), cross_tier=bool(gg.tier_source.nunique() > 1),
                             best_tier=tier_best(gg.evidence_tier), map_confidence_min=first_nn(gg.id_status), scope_note="full corpus v1.2"))
    V = pd.DataFrame(rows)
    v_total = int(len(V))
    if len(V): V = V.sort_values(["n_source_literatures", "n_papers"], ascending=False).head(3000).reset_index(drop=True); V["rank"] = V.index + 1
    conv = {"n": int(len(V)), "total": v_total, "rows": V.to_dict("records")}
    return assoc, contra, under, nulls, conv


def clean_records(obj):
    """json-safe: numpy scalars -> python, NaN -> None."""
    if isinstance(obj, dict): return {k: clean_records(v) for k, v in obj.items()}
    if isinstance(obj, list): return [clean_records(v) for v in obj]
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,)): return None if np.isnan(obj) else float(obj)
    if isinstance(obj, (np.bool_,)): return bool(obj)
    if isinstance(obj, float) and math.isnan(obj): return None
    if obj is pd.NaT: return None
    return obj


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--out", default="site/data")
    ap.add_argument("--version", default="v1.2"); ap.add_argument("--build-utc", default=None); ap.add_argument("--golden", default="validation/v12_golden_facts.json")
    a = ap.parse_args(); root = a.root; out = os.path.join(root, a.out) if not os.path.isabs(a.out) else a.out; os.makedirs(out, exist_ok=True)
    D, EV, CA, PM, DM = load(root); log("loaded", len(D), "rows")
    D = add_site_entity(D, EV); log("site_entity rows", int(D.site_entity.notna().sum()), "verified-id rows", int(D.site_ontology_id.notna().sum()))
    P, dedup = paper_table(D, CA, PM, DM); log("papers", len(P))
    pmid_order = P.pmid.tolist()
    F = build_facets(D, pmid_order); jdump(f"{out}/findings_facets.json", F)
    for s in range(F["n_shards"]):
        a_, b_ = s * SHARD_ROWS, min((s + 1) * SHARD_ROWS, len(D)); sl = D.iloc[a_:b_]
        jdump(f"{out}/text_{s:02d}.json", {"start": a_, "end": b_, "t": [text_or_placeholder(t, rs, rt, ro) for t, rs, rt, ro in zip(sl.finding_text, sl.relation_subject, sl.relation_type, sl.relation_object)]})
        det = {"start": a_, "end": b_}
        for k, (col, cap) in DETAIL_SPEC.items():
            det[k] = [truncate(None if pd.isna(v) else v, cap) for v in sl[col].values] if col in sl.columns else [None] * (b_ - a_)
        jdump(f"{out}/detail_{s:02d}.json", det)
    for old in [f for f in os.listdir(out) if re.match(r"(text|detail)_\d+\.json", f) and int(f.split("_")[1][:2]) >= F["n_shards"]]: os.remove(os.path.join(out, old))
    jdump(f"{out}/papers.json", build_papers(P)); log("facets + shards + papers written")
    ENT = build_entities(D); jdump(f"{out}/entities.json", ENT); log("entities", ENT["n"])
    jdump(f"{out}/autocomplete.json", {"entities": [e["name"] for e in ENT["entities"]], "conditions": sorted(D.condition.dropna().unique().tolist()),
                                        "journals": sorted(set(x for x in P.journal.dropna().astype(str) if x)), "source_literatures": sorted(D.source_literature.dropna().unique().tolist())})
    assoc, contra, under, nulls, conv = discovery(D, P)
    for name, obj in [("associations", assoc), ("contradictions", contra), ("understudied", under), ("convergence", conv)]:
        jdump(f"{out}/{name}.json", clean_records(obj)); log(name, obj["n"])
    # null results: 19k rows. Shipped as an index plus column-oriented shards, newest papers first, only the fields the page
    # and its CSV export use, so the Null tab parses the first shard and loads the rest in the background.
    NULL_FIELDS = ["canonical_pmid", "tier", "source_literature", "canonical_entity", "entity", "null_class", "condition", "finding_type",
                   "treatment_class", "evidence_tier", "certainty", "study_type", "n_participants", "year", "provenance_quote_trunc"]
    NR = sorted(nulls["rows"], key=lambda r: (-(r["year"] or 0), str(r["canonical_pmid"])))
    NSH = 2500
    for old in [f for f in os.listdir(out) if re.match(r"null_results_\d+\.json$", f)]: os.remove(os.path.join(out, old))
    shards_meta = []
    for i in range(0, len(NR), NSH):
        chunk = NR[i:i + NSH]; fn = f"null_results_{i // NSH:02d}.json"
        jdump(f"{out}/{fn}", clean_records({"start": i, "end": i + len(chunk), "rows": [[r.get(k) for k in NULL_FIELDS] for r in chunk]}))
        shards_meta.append({"file": fn, "start": i, "end": i + len(chunk)})
    jdump(f"{out}/null_results.json", {"n": len(NR), "fields": NULL_FIELDS, "shard_rows": NSH, "order": "year descending", "shards": shards_meta})
    log("null_results", len(NR), "in", len(shards_meta), "shards")
    ver = D.site_ontology_id.notna()
    cond_counts = {k: int(v) for k, v in D.condition.value_counts().items()}
    counts = {"findings": int(len(D)), "papers": int(P.pmid.nunique()), "entities": int(ENT["n"]), "conditions": int(D.condition.nunique()),
              "verified_id_rows": int(ver.sum()), "verified_ids_distinct": int(D.site_ontology_id.nunique()), "withheld_id_rows": int((D.ontology_id_verification == "id_withheld_unverified_v1.2").sum()),
              "entity_rows": int(D.entity.notna().sum()), "year_min": int(D.year.min()), "year_max": int(D.year.max()), "journals": int(P.journal.nunique()),
              "quotes": int(D.provenance_quote.notna().sum()), "null_results": nulls["n"], "contradictions": contra["n"], "associations": assoc["n"], "convergence": conv["n"], "understudied": under["n"],
              "associations_total": assoc["total"], "assoc_significant_total": assoc["significant_total"], "contradictions_total": contra["total"],
              "contra_flip_total": contra["flip_total"], "contra_null_vs_pos_total": contra["null_vs_positive_total"], "understudied_total": under["total"],
              "convergence_total": conv["total"],
              "packages": len(ORDER), "per_package": {p: {"findings": int(n), "papers": int(D.loc[D.package == p, "cpmid"].nunique())} for p, n in D.package.value_counts().items()},
              "conditions_rows": cond_counts,
              # legacy key names still read by the pages
              "canonical_entities": int(ENT["n"]), "entities_with_ontology": int(sum(1 for e in ENT["entities"] if e["oid"])),
              "canonical_entity_rows": int(D.site_entity.notna().sum()), "canonical_entity_pct": round(D.site_entity.notna().mean() * 100, 1),
              "entity_string_rows": int(D.entity.notna().sum()), "entity_string_pct": round(D.entity.notna().mean() * 100, 1),
              "papers_with_canonical_entity": int(D.cpmid[D.site_entity.notna()].nunique()), "verified_id_pct": round(ver.mean() * 100, 1),
              "strings_total": int(D.entity.dropna().astype(str).str.lower().nunique()),
              "nulls": nulls["n"], "assoc_significant": int(sum(1 for r in assoc["rows"] if r.get("significant_fdr05"))),
              "contra_flip": int(sum(1 for r in contra["rows"] if r["conflict_type"] == "direction-flip")), "contra_null_vs_pos": int(sum(1 for r in contra["rows"] if r["conflict_type"] == "null-vs-positive")),
              "findings_by_source_literature": {k: int(v) for k, v in D.source_literature.value_counts().items()},
              "id_authority_verified_rows": int((D.ontology_id_verification == "authority_verified").sum()),
              "id_retrospective_rows": int((D.ontology_id_verification == "authority_verified_retrospective").sum()),
              "id_replaced_rows": int(((D.ontology_id_verification == "authority_verified_retrospective") & D.ontology_id_source.astype(str).str.startswith("v1.2 forward")).sum()),
              "id_kept_rows": int(((D.ontology_id_verification == "authority_verified_retrospective") & ~D.ontology_id_source.astype(str).str.startswith("v1.2 forward")).sum()),
              "pmids": int(D.pmid.nunique())}
    vs = {}
    vsp = os.path.join(root, "validation", "verification_stats.json")
    if os.path.exists(vsp): vs = json.load(open(vsp))
    meta = {"version": a.version, "generated_utc": a.build_utc or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "counts": counts, "verification_stats": vs,
            "basis": {"papers": "canonical PMID (9 preprint/duplicate title merges applied from data/pmid_dedup_map.parquet)", "findings": "one row per extracted finding; corpus order = package order (dysautonomia-core, comorbid-a, comorbid-b, postviral-autism, migraine-hypermobility)",
                      "entities": "site_entity: authority-verified ontology id where present, else cross-tier canonical name (entity_vocabulary_crosstier), else entity string"},
            "verification": {"identifiers": "every model-emitted identifier was looked up at its authority in v1.2; see packages/*/annotations/POTS_MODEL_ID_BENCHMARK.md",
                             "fidelity": "whether each finding states what its paper found has not yet been checked by a human reader (audit in progress)"},
            "scope_caveat": "Machine-extracted research information from the published literature, not medical advice. Absence of a finding is not evidence of absence.",
            "model": {"name": "all-MiniLM-L6-v2", "browser_id": "Xenova/all-MiniLM-L6-v2", "dims": 384, "approx_mb": 23}, "quote_max_chars": 200,
            "new_facet_fields": {"ti": "tier_source (provenance only)", "sl": "source_literature", "mc": "id_status (identifier verification)"}, "packages": PKG, "source": "packages/ (pots-findings v1.2)"}
    jdump(f"{out}/meta.json", meta)
    golden = {"generated_from": "build_v12_projection.py over packages/*/data", "version": a.version, "counts": counts,
              "facets": {k: len(v) for k, v in F["dicts"].items()}, "coverage": F["coverage"], "n_shards": F["n_shards"], "shard_rows": SHARD_ROWS,
              "papers_rows": len(P), "entities_rows": ENT["n"], "top_entities": [(e["name"], e["np_"]) for e in ENT["entities"][:10]]}
    gp = os.path.join(root, a.golden); os.makedirs(os.path.dirname(gp), exist_ok=True); jdump(gp, golden)
    if os.path.isdir(f"{root}/_intake"): D[["cpmid", "site_entity", "site_ontology_id", "id_status", "entity_basis", "tier_source", "package", "concept_group", "site_primary_id"]].to_parquet(f"{root}/_intake/site_entity_v12.parquet", index=False)
    log("done; meta.counts:", {k: v for k, v in counts.items() if not isinstance(v, dict)})


if __name__ == "__main__":
    main()
