"""Tier-3 QA procedures. Every function reports a BASIS alongside its rate:
a bare percentage with no denominator is the failure mode this file exists to prevent.
"""
import pandas as pd, random, json, re

def quote_census(df, normalize_fn, traceability_fn, corpus=None, subset="abstract-only", seed=11):
    """Quote provenance over a CENSUS of the named subset (not a sample).

    For each row, checks whether the extracted quote is traceable to the SOURCE TEXT
    of the paper it is attributed to. Requires the corpus (pmid -> abstract) because
    the findings frame does not carry source text. Reports:
      traceable / untraceable counts, and the untraceable examples for inspection.
    A quote that is not traceable is NOT automatically a fabrication -- for full-text
    papers the source here is only the abstract, so a quote drawn from the body will
    not match. That is why the default subset is abstract-only, where the abstract IS
    the full source the model saw.
    """
    sub = df[df.fulltext_status == subset] if subset else df
    sub = sub[sub.provenance_quote.notna() & (sub.provenance_quote.astype(str).str.len() > 0)]
    if corpus is None or not len(sub):
        return {"subset": subset, "n_rows_in_subset": int(len(sub)),
                "error": "corpus (pmid->abstract) required to verify quotes",
                "basis": "no verification performed"}
    src = dict(zip(corpus.pmid.astype(str), corpus.abstract.fillna("")))
    ok = bad = nosrc = 0
    examples = []
    for pmid, q in zip(sub.pmid.astype(str), sub.provenance_quote.astype(str)):
        text = src.get(pmid, "")
        if not text:
            nosrc += 1; continue
        try:
            tr = traceability_fn(q, text)
            # quote_traceability returns a TUPLE (exact, traceable, n_shingles).
            # A non-empty tuple is truthy, so bool(tr) would accept everything --
            # verified by a wrong-paper negative control that matched 400/400.
            if isinstance(tr, tuple):
                hit = bool(tr[1]) if len(tr) > 1 else bool(tr[0])
            elif isinstance(tr, dict):
                hit = bool(tr.get("traceable"))
            else:
                hit = bool(tr)
        except Exception:
            hit = normalize_fn(q)[:60] in normalize_fn(text)
        if hit: ok += 1
        else:
            bad += 1
            if len(examples) < 15:
                examples.append({"pmid": pmid, "quote": q[:150]})
    checked = ok + bad
    return {"subset": subset, "n_rows_in_subset": int(len(sub)),
            "n_checked": checked, "n_traceable": ok, "n_untraceable": bad,
            "n_no_source_text": nosrc,
            "traceable_pct": round(100*ok/checked, 2) if checked else None,
            "untraceable_examples": examples,
            "basis": f"CENSUS of every fulltext_status=={subset} row with a non-null quote "
                     f"({checked} verified against the paper's own abstract; "
                     f"{nosrc} rows had no source text available)"}

def id_correspondence_audit(df, sample_n=200, seed=7):
    """OFFLINE audit: does each derived id's authority LABEL correspond to the name
    the model gave? Uses the label captured at resolve time — no network, no LLM.
    A mismatch here is a resolver defect, not a model fabrication."""
    rng = random.Random(seed)
    sub = df[df.entity_ontology_id_resolved.notna() & df.entity_ontology_label.notna()]
    idx = list(sub.index)
    rng.shuffle(idx)
    picks = idx[:min(sample_n, len(idx))]
    rows = []
    for i in picks:
        r = df.loc[i]
        nm = str(r.get("entity") or "").strip().lower()
        lab = str(r.get("entity_ontology_label") or "").strip().lower()
        exact = (nm == lab)
        rows.append({"entity": r.get("entity"), "id": r.get("entity_ontology_id_resolved"),
                     "label": r.get("entity_ontology_label"),
                     "source": r.get("ontology_id_source"), "exact_label_match": exact})
    n = len(rows)
    n_exact = sum(1 for x in rows if x["exact_label_match"])
    return {"n_audited": n, "n_exact_label_match": n_exact,
            "exact_match_pct": round(100*n_exact/n, 1) if n else None,
            "basis": f"{n} of {len(sub)} id-bearing rows, random seed {seed}; "
                     f"non-exact rows are synonym-path resolutions, NOT necessarily errors",
            "rows": rows[:40]}

def hpo_multivalue_report(df):
    sub = df[df.hpo_ids_verified.notna()]
    if not len(sub): return {"n_with_ids": 0}
    multi = sub[sub.hpo_id_count > 1]
    return {"n_rows_total": int(len(df)),
            "n_with_hpo_ids": int(len(sub)),
            "n_multi_id": int(len(multi)),
            "multi_pct_of_id_bearing": round(100*len(multi)/len(sub), 1),
            "multi_pct_of_all_rows": round(100*len(multi)/len(df), 1),
            "basis": "denominators stated explicitly: multi-ID share differs by ~3x "
                     "depending on whether the base is id-bearing rows or all rows",
            "source_breakdown": sub.hpo_id_source.value_counts().to_dict()}

def number_in_quote_report(df):
    s = df.number_in_quote
    checked = s.notna().sum()
    return {"n_rows": int(len(df)), "n_checkable": int(checked),
            "n_true": int((s==True).sum()), "n_false": int((s==False).sum()),
            "fail_pct_of_checkable": round(100*(s==False).sum()/checked, 1) if checked else None,
            "basis": "denominator = rows with BOTH a numeric value and a quote; "
                     "rows with no number are not failures and are excluded"}

def blocked_report(df):
    vc = df.fulltext_status.value_counts().to_dict()
    n_papers = df.pmid.nunique()
    blocked_papers = df[df.fulltext_status=="blocked"].pmid.nunique()
    return {"row_level_status": vc, "n_papers": int(n_papers),
            "blocked_papers": int(blocked_papers),
            "blocked_paper_pct": round(100*blocked_papers/n_papers, 2) if n_papers else None,
            "basis": "paper-level rate (rows are not papers); a paper with many findings "
                     "would otherwise dominate a row-level percentage"}

def guard_report(df):
    ID_SHAPED = re.compile(r'\b(?:HGNC|CHEBI|HP|GO|MESH|UMLS|ENSG|R-HSA)\s*[:_]\s*\d+', re.I)
    hits = {}
    for c in ["entity","phenotype_terms","pathway_or_mechanism","symptom_correlate","gene_marker"]:
        if c in df.columns:
            m = df[c].astype(str).str.contains(ID_SHAPED, na=False)
            if m.any(): hits[c] = int(m.sum())
    return {"n_rows": int(len(df)), "id_shaped_strings_in_name_fields": hits or "NONE",
            "verdict": "Fix 2 holding" if not hits else "Fix 2 BREACHED — investigate",
            "basis": "census of all rows, all five name-bearing columns"}
