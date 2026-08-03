"""site_generator.py — verified-faithful emitters for the POTS literature-map site data layer.

PHASE 0 STATUS: every function here was validated by regenerating the TIER-1-ONLY site JSON and
diffing it against the JSON shipped in pots_tier1_publishable.zip. All outputs reproduced EXACTLY:

    findings_facets.json   21/21 dicts, 26/26 cols, scalars   EXACT
    text_NN.json           7/7 shards                          EXACT
    detail_NN.json         84/84 arrays (7 shards x 12 fields) EXACT
    papers.json            3121/3121 rows                      EXACT

Encoding rules were reverse-engineered from the shipped JSON, not guessed. The non-obvious ones —
each of which broke an initial attempt — are documented inline below.
"""
import numpy as np
import pandas as pd

MISS = "\u2014"          # em dash: the missing-value token in facet dictionaries
SHARD_ROWS = 6000

# facet key -> source column in the canonical findings parquet
FACET_MAP = {
    "e": "canonical_entity", "c": "condition", "d": "direction", "tr": "evidence_tier",
    "ce": "certainty", "ft": "finding_type", "ek": "entity_kind", "mc": "map_confidence",
    "nc": "null_or_failed_result", "st": "study_type", "ca": "causal_or_correlational",
    "an": "anatomical_system", "ps": "pots_subtype", "ag": "population_age_group",
    "sx": "sex_hormonal", "th": "theme", "sr": "source_stream", "es": "evidence_stratum",
    "rt": "relation_type", "cv": "is_covid_associated",
}

# detail key -> (source column, character cap or None)
DETAIL_SPEC = {
    "quote": ("provenance_quote", 200), "quant": ("quantitative_detail", None),
    "eff": ("effect_size", None), "path": ("pathway_or_mechanism", None),
    "lim": ("limitations_stated", 300), "fut": ("future_direction", 300),
    "npart": ("n_participants", None), "comp": ("comparator", None),
    "symp": ("symptom_correlate", 300), "treat": ("treatment_class", None),
    "sec": ("provenance_section", None), "ont": ("canonical_ontology_id", None),
}

# papers.json serialization conventions
_STR_EMPTY = {"pmc_url", "doi_url", "pubmed_url", "citation_short", "authors",
              "first_author", "journal", "title", "pmc_id"}
_DEFAULTS = {"is_open_access": False, "cited_by_count": 0}


def encode_column(series, missing=MISS):
    """Dictionary-encode in FIRST-APPEARANCE order.

    GOTCHA: the shipped dictionaries are ordered by first appearance in the data, NOT sorted.
    Sorting produces the same value set but different integer codes, so every col mismatches.
    """
    vals = series.astype(object).where(series.notna(), missing).astype(str)
    seen, codes, dic = {}, np.empty(len(vals), dtype=np.int32), []
    for i, v in enumerate(vals.values):
        c = seen.get(v)
        if c is None:
            c = len(dic)
            seen[v] = c
            dic.append(v)
        codes[i] = c
    return dic, codes.tolist()


def truncate(value, cap):
    """Cap a string field the way the site does: s[:cap-1].rstrip() + ellipsis.

    GOTCHA: the .rstrip() is load-bearing. A plain s[:cap-1] + ellipsis differs on every value
    whose cut lands on whitespace, and a word-boundary cut matches only ~56%. With rstrip: 100%.
    """
    if value is None:
        return None
    s = str(value)
    if not cap or len(s) <= cap:
        return s
    return s[:cap - 1].rstrip() + "\u2026"


def finding_text_or_placeholder(text, subject, rtype, obj):
    """Synthesize display text when finding_text is null.

    GOTCHA: rows with no extracted summary sentence are NOT null in the site JSON — they carry a
    placeholder built from the relation triple, joined with a spaced em dash.
    """
    if pd.notna(text):
        return str(text)
    return f"[no summary sentence extracted] {subject} \u2014 {rtype} \u2014 {obj}"


def build_facets(df, papers_pmid_order, dedup_map, shard_rows=SHARD_ROWS):
    """Emit findings_facets.json.

    papers_pmid_order: pmid strings in papers.json row order.
    dedup_map: raw pmid -> canonical pmid.

    GOTCHA: the 'p' column indexes papers.json by CANONICAL pmid. Using the raw pmid leaves the
    merged-duplicate rows unmapped (53 of them in tier-1).
    """
    out = {"n": int(len(df)), "shard_rows": shard_rows,
           "n_shards": int(np.ceil(len(df) / shard_rows)), "dicts": {}, "cols": {}}
    for key, col in FACET_MAP.items():
        out["dicts"][key], out["cols"][key] = encode_column(df[col])
    # the raw entity string uses "" as its missing token, not the em dash
    out["dicts"]["es_str"], out["cols"]["es_str"] = encode_column(df["entity"], missing="")
    pos = {pm: i for i, pm in enumerate(papers_pmid_order)}
    canon = df["pmid"].astype(str).map(lambda x: dedup_map.get(x, x))
    out["cols"]["y"] = df["year"].fillna(0).astype(int).tolist()
    out["cols"]["p"] = canon.map(pos).astype(int).tolist()
    out["cols"]["q"] = df["quantitative_detail"].notna().astype(int).tolist()
    out["cols"]["sd"] = df["split_derived"].fillna(0).astype(int).tolist()
    out["cols"]["has_can"] = df["canonical_entity"].notna().astype(int).tolist()
    return out


def build_text_shard(df, s, shard_rows=SHARD_ROWS):
    """Emit text_NN.json for shard s."""
    a, b = s * shard_rows, min((s + 1) * shard_rows, len(df))
    sl = df.iloc[a:b]
    return {"start": a, "end": b,
            "t": [finding_text_or_placeholder(t, rs, rt, ro) for t, rs, rt, ro in
                  zip(sl.finding_text, sl.relation_subject, sl.relation_type, sl.relation_object)]}


def build_detail_shard(df, s, shard_rows=SHARD_ROWS):
    """Emit detail_NN.json for shard s (12 parallel arrays)."""
    a, b = s * shard_rows, min((s + 1) * shard_rows, len(df))
    out = {"start": a, "end": b}
    for key, (col, cap) in DETAIL_SPEC.items():
        if col in df.columns:
            out[key] = [truncate(None if pd.isna(v) else v, cap) for v in df[col].iloc[a:b].values]
        else:
            out[key] = [None] * (b - a)
    return out


def build_papers(paper_meta, fields, pmid_order):
    """Emit papers.json as {fields, rows}.

    GOTCHA: nulls are not uniform. URL/text fields serialize to "", is_open_access to False, and
    cited_by_count to 0 — not to null.
    """
    sub = paper_meta.set_index(paper_meta.pmid.astype(str)).loc[[str(p) for p in pmid_order]]

    def ser(v, field):
        if pd.isna(v):
            if field in _DEFAULTS:
                return _DEFAULTS[field]
            return "" if field in _STR_EMPTY else None
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            return int(v) if field == "cited_by_count" else float(v)
        if isinstance(v, np.bool_):
            return bool(v)
        return v

    return {"fields": list(fields),
            "rows": [[ser(v, f) for v, f in zip(row, fields)] for row in sub[fields].values]}
