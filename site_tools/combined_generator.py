"""combined_generator.py — tier-1 + tier-2 extensions on top of the phase-0-verified site_generator.

The emitters in site_generator.py are NOT rewritten. This module only:
  * extends FACET_MAP with the two new facet fields (tier, source_literature)
  * adds build_entities() — reverse-engineered and validated byte-exact against the
    shipped tier-1 entities.json (863/863 rows identical, all 13 keys)
  * adds tier-2 paper-metadata derivation with the same null conventions as tier-1

ORDERING NOTE (papers.json): site_generator.build_papers takes `pmid_order` as an INPUT.
The tier-1 row order in the shipped papers.json is not reproducible from any table in the
publishable zip (tested: metadata row order, CSV row order, corpus order, chunk_order,
findings first-appearance, n_findings sort, year sort — none match). It is therefore treated
as a given: the combined order is [shipped tier-1 order] + [tier-2 first-appearance order].
This keeps tier-1 indices stable and makes the tier-1 regression a true test of the emitters.
"""
import numpy as np
import pandas as pd
import site_generator as SG

# two NEW facet fields the tier-1 site could not have + evidence_scope (added if present)
FACET_MAP_COMBINED = dict(SG.FACET_MAP)
FACET_MAP_COMBINED["ti"] = "tier"              # 1 or 2
FACET_MAP_COMBINED["sl"] = "source_literature"  # tier-2 literature; tier-1 -> its theme


def first_nn(s):
    s = s.dropna()
    return None if len(s) == 0 else s.iloc[0]


def build_entities(df):
    """Rollup over canonical entities -> entities.json {n, entities:[...]}.

    Validated: reproduces the shipped tier-1 entities.json exactly (863 rows, all keys).
    GOTCHA 1: row order is np_ (distinct canonical papers) DESCENDING with numpy's
              *introsort* tie-break — pandas kind="quicksort". mergesort/stable does NOT match.
    GOTCHA 2: `origs` = sorted distinct raw entity strings EXCLUDING the canonical name itself.
    GOTCHA 3: np_ counts canonical pmids; npd counts canonical pmids of non-split-derived rows.
    GOTCHA 4: scalar fields (kind/mapc/oid/osrc/olabel) are FIRST non-null in row order,
              not the mode — olabel differs between the two for several entities.
    """
    s = df[df.canonical_entity.notna()]
    npu = s.groupby("canonical_entity", sort=False).cpmid.nunique()
    order = npu.sort_values(ascending=False, kind="quicksort").index.tolist()
    out = {}
    for n, g in s.groupby("canonical_entity", sort=False):
        out[n] = {
            "name": n,
            "kind": first_nn(g.entity_kind),
            "mapc": first_nn(g.map_confidence),
            "oid": first_nn(g.canonical_ontology_id),
            "osrc": first_nn(g.canonical_ontology_source),
            "olabel": first_nn(g.entity_ontology_label),
            "nf": int(len(g)),
            "np_": int(g.cpmid.nunique()),
            "npd": int(g[g.split_derived.fillna(False) == False].cpmid.nunique()),
            "origs": sorted(set(x for x in g.entity_norm_original.dropna().astype(str) if x != n)),
            "dirs": {k: int(v) for k, v in g.direction.value_counts().items()},
            "tiers": {k: int(v) for k, v in g.evidence_tier.value_counts().items()},
            "conds": {k: int(v) for k, v in g.condition.value_counts().items()},
        }
    ents = [out[n] for n in order]
    return {"n": len(ents), "entities": ents}


def build_facets_combined(df, papers_pmid_order, dedup_map, facet_map=None,
                          strings_mapped=None, shard_rows=SG.SHARD_ROWS):
    """Same contract as SG.build_facets but over an extensible facet map."""
    fm = facet_map or FACET_MAP_COMBINED
    out = {"n": int(len(df)), "shard_rows": shard_rows,
           "n_shards": int(np.ceil(len(df) / shard_rows)), "dicts": {}, "cols": {}}
    for key, col in fm.items():
        out["dicts"][key], out["cols"][key] = SG.encode_column(df[col])
    # GOTCHA: es_str's DICT sits last in `dicts` but its COL sits between `sd` and `has_can`
    # in `cols`. Dict-equality hides this; byte-equality does not.
    out["dicts"]["es_str"], _es_str_col = SG.encode_column(df["entity"], missing="")
    pos = {pm: i for i, pm in enumerate(papers_pmid_order)}
    canon = df["pmid"].astype(str).map(lambda x: dedup_map.get(x, x))
    out["cols"]["y"] = df["year"].fillna(0).astype(int).tolist()
    out["cols"]["p"] = canon.map(pos).astype(int).tolist()
    out["cols"]["q"] = df["quantitative_detail"].notna().astype(int).tolist()
    out["cols"]["sd"] = df["split_derived"].fillna(0).astype(int).tolist()
    out["cols"]["es_str"] = _es_str_col
    out["cols"]["has_can"] = df["canonical_entity"].notna().astype(int).tolist()
    # --- three top-level keys the shipped facets JSON also carries (SG.build_facets omits them) ---
    # sparse map row_index -> raw normalized entity string, ONLY where it differs from the canonical
    m = (df.canonical_entity.notna() & df.entity_norm_original.notna()
         & (df.entity_norm_original.astype(str) != df.canonical_entity.astype(str)))
    out["orig_entity"] = {str(i): v for i, v in
                          zip(np.where(m.values)[0], df.entity_norm_original[m].astype(str))}
    out["facet_fields"] = dict(fm)
    n = len(df)
    canon_all = df["pmid"].astype(str).map(lambda x: dedup_map.get(x, x))
    out["coverage"] = {
        "entity_string_rows": int(df.entity.notna().sum()),
        "entity_string_pct": round(float(df.entity.notna().sum()) / n * 100, 1),
        "canonical_rows": int(df.canonical_entity.notna().sum()),
        "canonical_pct": round(float(df.canonical_entity.notna().sum()) / n * 100, 1),
        "entity_unmapped_rows": int((df.entity.notna() & df.canonical_entity.isna()).sum()),
        "papers_with_canonical": int(canon_all[df.canonical_entity.notna()].nunique()),
        "papers_total": int(canon_all.nunique()),
        "strings_mapped": int(strings_mapped) if strings_mapped is not None else None,
        "strings_total": int(df.entity.dropna().astype(str).str.lower().nunique()),
    }
    return out


def derive_tier2_paper_meta(corpus, n_findings_by_pmid, pmids):
    """Tier-2 paper rows in paper_metadata schema, from the augmented corpus.

    Same null conventions as tier-1: URL/text fields -> "", is_open_access -> False,
    cited_by_count -> 0 (applied downstream by SG.build_papers via its _STR_EMPTY/_DEFAULTS).
    """
    c = corpus[corpus.pmid.isin(set(pmids))].copy()
    au = c.authors.fillna("").astype(str).str.rstrip(".")
    c["authors"] = au.where(au != "", None)
    c["author_count"] = au.apply(lambda a: len([x for x in a.split(",") if x.strip()]) or None)
    c["first_author"] = au.apply(lambda a: a.split(",")[0].strip() or None)
    yr = c.year
    c["year"] = yr.astype("Int64")
    c["doi_url"] = c.doi.apply(lambda d: f"https://doi.org/{d}" if pd.notna(d) and d else None)
    c["pubmed_url"] = c.pmid.apply(lambda p: f"https://pubmed.ncbi.nlm.nih.gov/{p}/")
    c["pmc_url"] = None
    c["pmc_id"] = None
    c["citation_short"] = [
        (f"{fa} et al. ({int(y)}) {j}" if fa and pd.notna(y) and pd.notna(j) else None)
        for fa, y, j in zip(c.first_author, c.year, c.journal)]
    c["n_findings"] = c.pmid.map(n_findings_by_pmid).astype("Int64")
    c["is_open_access"] = c.isOA.eq("Y")
    c["cited_by_count"] = pd.to_numeric(c.cites, errors="coerce")
    c["canonical_pmid"] = c.pmid
    c["is_canonical"] = True
    c["last_author"] = au.apply(lambda a: (a.split(",")[-1].strip() or None) if a else None)
    c["metadata_source"] = "corpus_augmented"
    return c
