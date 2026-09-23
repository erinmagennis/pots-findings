"""Tier-2 controlled-vocabulary validator.

The extraction prompt ALREADY pins both enums; measured drift past that constraint
is 20 rows / 0.055% of the 81-chunk pool. A prompt edit therefore cannot fix this —
only a hard post-extraction gate can. Run per chunk, before the chunk counts as done.

Policy: FLAG, never silently coerce. Out-of-enum values are reported and quarantined
for adjudication. Deterministic remaps below are PROPOSALS applied only on explicit
opt-in (apply_remap=True), never by default -- consistent with the project rule that
frozen data changes only via adjudicated correction.
"""
import pandas as pd

EVIDENCE_TIER = ["meta-analysis", "RCT", "cohort", "case-control", "cross-sectional",
                 "case-series", "case-report", "mechanistic/in-vitro", "review/expert-opinion"]

CONDITION = ["POTS", "ME_CFS", "long_COVID", "EDS_hypermobility", "fibromyalgia", "MCAS",
             "dysautonomia", "small_fiber_neuropathy", "autism", "migraine", "IBS_gut",
             "multiple", "general"]

# Adjudicated remap proposals for the drift measured on chunks 76-220.
# 'systematic-review/meta-analysis' -> 'meta-analysis'  (same design, verbose label)
# 'case-report/case-series'         -> 'case-series'    (conservative: the broader of the two)
# 'IBD_gut'                         -> REVIEW           (IBD != IBS; a real distinct disease,
#                                                        NOT remappable -- needs human call)
# 'other patient group'             -> 'general'        (free-text escape from the enum)
REMAP_EVIDENCE_TIER = {
    "systematic-review/meta-analysis": "meta-analysis",
    "case-report/case-series": "case-series",
}
REMAP_CONDITION = {}   # "other patient group" REMOVED: see ENUM_ADJUDICATION_other_patient_group.md
NEEDS_HUMAN = {"condition": ["IBD_gut", "other patient group"]}   # never auto-remapped

CATCHALL_CONDITIONS = ["general", "multiple"]


def validate(df):
    """Return (ok, report). ok=False if any out-of-enum value is present."""
    rep = {}
    for col, allowed in [("evidence_tier", EVIDENCE_TIER), ("condition", CONDITION)]:
        if col not in df.columns:
            continue
        bad = df[~df[col].isin(allowed) & df[col].notna()]
        rep[col] = {
            "n_bad_rows": int(len(bad)),
            "bad_values": bad[col].value_counts().to_dict(),
            "chunks": sorted(int(c) for c in bad["chunk_id"].unique()) if "chunk_id" in bad else [],
        }
    ok = all(v["n_bad_rows"] == 0 for v in rep.values())
    return ok, rep


def apply_remap(df, apply_remap=False):
    """Opt-in only. Returns (df, n_changed, unresolved)."""
    if not apply_remap:
        raise RuntimeError("apply_remap=False: remaps are proposals, not defaults. "
                           "Enable explicitly and log the adjudication.")
    d, n = df.copy(), 0
    for col, mp in [("evidence_tier", REMAP_EVIDENCE_TIER), ("condition", REMAP_CONDITION)]:
        if col in d.columns:
            hit = d[col].isin(mp)
            n += int(hit.sum())
            d.loc[hit, col] = d.loc[hit, col].map(mp)
    unresolved = {c: [v for v in vals if (d[c] == v).any()] for c, vals in NEEDS_HUMAN.items()}
    return d, n, unresolved


def condition_key(df):
    """Hierarchical condition key for convergence analysis.

    Measured on the 81-chunk pool: 21.3% of rows carry a catch-all condition
    ('general'/'multiple') and 8.5% of papers have NO specific-condition finding,
    so keying convergence on finding-level `condition` alone drops those papers.
    Falls back to the paper-level acquisition stream, and records which basis was used
    so the two are never silently pooled.
    """
    spec = df["condition"].where(~df["condition"].isin(CATCHALL_CONDITIONS))
    key = spec.fillna(df["source_literature"])
    basis = pd.Series("finding_condition", index=df.index).where(spec.notna(), "paper_source_literature")
    return key, basis
