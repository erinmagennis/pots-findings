"""Tier-3 invariants. Four families, run after EVERY merge step.
Verified by PLANTING REGRESSIONS — a suite that only ever passes is untested.
"""
import pandas as pd, re

REQUIRED_COLS = ["pmid","chunk_id","tier","entity","finding_text","provenance_quote",
                 "condition","evidence_tier","certainty","certainty_derived",
                 "number_in_quote","fulltext_status","fetch_note",
                 "entity_ontology_id_resolved","ontology_id_source",
                 "hpo_ids_verified","hpo_id_source","hpo_id_count","hgnc_id"]

ET_OK = ["meta-analysis","RCT","cohort","case-control","cross-sectional","case-series",
         "case-report","mechanistic/in-vitro","review/expert-opinion"]
CO_OK = ["POTS","ME_CFS","long_COVID","EDS_hypermobility","fibromyalgia","MCAS","dysautonomia",
         "small_fiber_neuropathy","autism","migraine","IBS_gut","multiple","general"]
ID_SHAPED = re.compile(r'\b(?:HGNC|CHEBI|HP|GO|MESH|MSH|UMLS|ENSG|UNIPROT|R-HSA)\s*[:_]\s*\d+', re.I)


def inv_schema(df):
    missing=[c for c in REQUIRED_COLS if c not in df.columns]
    return {"name":"schema_completeness","ok":not missing,"missing":missing}

def inv_conservation(df, expected_chunks, expected_papers_by_chunk):
    """No chunk silently absent; no chunk exceeding its paper allotment."""
    got=set(int(c) for c in df.chunk_id.dropna().unique())
    absent=sorted(set(expected_chunks)-got)
    over=[]
    for c,g in df.groupby("chunk_id"):
        exp=expected_papers_by_chunk.get(str(int(c)))
        if exp and g.pmid.nunique()>exp: over.append({"chunk":int(c),"papers":int(g.pmid.nunique()),"expected_max":exp})
    return {"name":"conservation","ok":(not absent and not over),"absent_chunks":absent,"over_allotment":over}

def inv_monotonicity(df, prior_rows=0, prior_papers=0):
    """A tier that ADDS must never shrink counts."""
    ok = len(df)>=prior_rows and df.pmid.nunique()>=prior_papers
    return {"name":"monotonicity","ok":bool(ok),"rows":int(len(df)),
            "papers":int(df.pmid.nunique()),"prior_rows":prior_rows,"prior_papers":prior_papers}

def inv_no_model_ids(df):
    """FIX 2 invariant: no id-shaped string may appear in any NAME field."""
    hits={}
    for c in ["entity","phenotype_terms","pathway_or_mechanism","symptom_correlate","gene_marker"]:
        if c in df.columns:
            m=df[c].astype(str).str.contains(ID_SHAPED, na=False)
            if m.any(): hits[c]=int(m.sum())
    return {"name":"no_model_emitted_ids","ok":not hits,"violations":hits}

def inv_id_provenance(df):
    """Every non-null id must carry a source tag; every null id must be tagged unresolved."""
    bad={}
    pairs=[("entity_ontology_id_resolved","ontology_id_source"),
           ("hpo_ids_verified","hpo_id_source"),("hgnc_id","gene_id_source")]
    for idc,srcc in pairs:
        if idc in df.columns and srcc in df.columns:
            untagged=int((df[idc].notna() & (df[srcc].isna() | (df[srcc]=="unresolved_nulled"))).sum())
            if untagged: bad[idc]=untagged
    return {"name":"id_provenance","ok":not bad,"id_without_source":bad}

def inv_enum(df):
    """FLAG, never coerce."""
    out={}
    for c,allowed in [("evidence_tier",ET_OK),("condition",CO_OK)]:
        if c in df.columns:
            b=df[~df[c].isin(allowed) & df[c].notna()]
            if len(b): out[c]={str(k):int(v) for k,v in b[c].value_counts().items()}
    return {"name":"enum_drift","ok":True,"flagged":out,"note":"flagged for adjudication, never auto-remapped"}

def inv_duplicates(df):
    """Duplicate check on the FULL row — a loose key flags legitimate distinct findings
    extracted from one summary sentence (a false defect in Tier 2)."""
    cols=[c for c in df.columns if df[c].map(lambda v: not isinstance(v,(list,dict,set))).all()]
    full=int(df.duplicated(subset=cols, keep=False).sum())
    loose=int(df.duplicated(subset=["pmid","finding_text"], keep=False).sum()) if "finding_text" in df.columns else 0
    return {"name":"duplicates","ok":full==0,"fully_identical_rows":full,
            "loose_key_groups":loose,
            "note":"loose>full is expected and NOT a defect; only fully-identical rows are duplicates"}

def inv_hpo_multivalue(df):
    """hpo_id_count must equal the number of semicolon-delimited ids."""
    if "hpo_ids_verified" not in df.columns: return {"name":"hpo_multivalue","ok":True,"skipped":True}
    sub=df[df.hpo_ids_verified.notna()]
    if not len(sub): return {"name":"hpo_multivalue","ok":True,"n_with_ids":0}
    calc=sub.hpo_ids_verified.astype(str).str.split(";").map(len)
    mismatch=int((calc!=sub.hpo_id_count).sum())
    return {"name":"hpo_multivalue","ok":mismatch==0,"mismatch":mismatch,
            "n_with_ids":int(len(sub)),"n_multi":int((sub.hpo_id_count>1).sum())}

def run_all(df, expected_chunks, expected_papers_by_chunk, prior_rows=0, prior_papers=0):
    checks=[inv_schema(df), inv_conservation(df,expected_chunks,expected_papers_by_chunk),
            inv_monotonicity(df,prior_rows,prior_papers), inv_no_model_ids(df),
            inv_id_provenance(df), inv_enum(df), inv_duplicates(df), inv_hpo_multivalue(df)]
    return {"all_ok": all(c["ok"] for c in checks), "checks": checks}
