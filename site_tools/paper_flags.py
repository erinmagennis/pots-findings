#!/usr/bin/env python3
"""paper_flags.py: the one loader for paper flags (retractions, corrections, preprints, linked records).

Source preference:
  1. FINAL  : packages/<pkg>/annotations/paper_flags.csv (any package has one -> all present ones are read and concatenated).
  2. FALLBACK: releases/v1.2/paper_flags/paper_flags_candidates.csv mapped to the final schema, plus the 8 title merges
     from data/pmid_dedup_map.parquet (merge_applied) re-expressed as linked records, since the site no longer merges them.
So the site switches to the final files with a rebuild and no code change.

Final schema (FINAL_COLUMNS) and flag vocabulary (FLAGS) follow the release plan.  recommended_use:
  exclude    -> retracted, partially_retracted, erratum_notice (left out of default counts, charts and tables)
  count_once -> the preprint side of a preprint/published pair
  note       -> everything else
"""
import glob, os
from datetime import datetime, timezone
import pandas as pd

FINAL_COLUMNS = ["pmid", "flag", "flag_label", "linked_pmid", "linked_in_dataset", "linked_package", "linked_title", "relation_note",
                 "recommended_use", "canonical_pmid", "n_findings", "title", "journal", "year", "doi", "source", "checked_utc"]
FLAGS = {  # flag -> reader label
    "retracted": "Retracted", "partially_retracted": "Partially retracted", "expression_of_concern": "Expression of concern",
    "erratum_notice": "Correction notice", "has_correction": "Correction published",
    "preprint_with_published_version": "Preprint with published version", "published_version_of_preprint": "Published version of a preprint",
    "preprint": "Preprint", "same_work_other_record": "Same work, other record", "update_of": "Update of an earlier record",
    "publisher_removal_notice": "Publisher removal notice"}
EXCLUDE = {"retracted", "partially_retracted", "erratum_notice"}
CANDIDATE_MAP = {"retracted": "retracted", "expression_of_concern": "expression_of_concern", "erratum_notice": "erratum_notice",
                 "has_correction": "has_correction", "earlier_version_of": "preprint_with_published_version",
                 "later_version_of": "published_version_of_preprint", "preprint": "preprint"}   # possible_same_work: ignored (needs review)
MERGE_REASON = {  # merged_reason -> (flag on the merged record, flag on the canonical record, note)
    "preprint_of_canonical": ("preprint_with_published_version", "published_version_of_preprint", "Preprint and its published version"),
    "simultaneous_co_publication": ("same_work_other_record", "same_work_other_record", "Same article published at the same time in another journal"),
    "short_companion_or_correction": ("same_work_other_record", "same_work_other_record", "Short companion record with the same title"),
    "erratum_of_canonical": ("erratum_notice", "has_correction", "Correction notice for this paper")}


def recommended_use(flag):
    if flag in EXCLUDE: return "exclude"
    if flag == "preprint_with_published_version": return "count_once"
    return "note"


def _pmid(x):
    if x is None or (isinstance(x, float) and x != x) or x == "": return None
    return str(int(float(x)))


def final_files(root):
    return sorted(glob.glob(os.path.join(root, "packages", "*", "annotations", "paper_flags.csv")))


def from_candidates(root, candidates_csv=None, dedup_parquet=None):
    cp = candidates_csv or os.path.join(root, "releases", "v1.2", "paper_flags", "paper_flags_candidates.csv")
    C = pd.read_csv(cp)
    C = C[(~C.needs_review.astype(bool)) & C.candidate_flag.isin(CANDIDATE_MAP)]
    checked = datetime.fromtimestamp(os.path.getmtime(cp), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for r in C.itertuples():
        flag = CANDIDATE_MAP[r.candidate_flag]
        pm, lp = _pmid(r.pmid), _pmid(r.linked_pmid)
        yr = str(r.pubdate)[:4] if isinstance(r.pubdate, str) and str(r.pubdate)[:4].isdigit() else None
        rows.append(dict(pmid=pm, flag=flag, linked_pmid=lp, linked_in_dataset=bool(r.linked_in_corpus) if lp else False,
                         linked_package=r.linked_package if isinstance(r.linked_package, str) else None, linked_title=None,
                         relation_note=(r.evidence if isinstance(r.evidence, str) else None),
                         canonical_pmid=(lp if flag == "preprint_with_published_version" and lp else pm), n_findings=int(r.n_findings),
                         title=r.pubmed_title if isinstance(r.pubmed_title, str) else None, journal=r.journal if isinstance(r.journal, str) else None,
                         year=int(yr) if yr else None, doi=None, source=r.source, checked_utc=checked))
    dp = dedup_parquet or os.path.join(root, "data", "pmid_dedup_map.parquet")
    if os.path.exists(dp):
        DM = pd.read_parquet(dp)
        DM = DM[DM.merge_applied.astype(bool) & (DM.pmid.astype(str) != DM.canonical_pmid.astype(str))]
        for r in DM.itertuples():
            a, b = _pmid(r.pmid), _pmid(r.canonical_pmid)
            fa, fb, note = MERGE_REASON.get(r.merged_reason, ("same_work_other_record", "same_work_other_record", str(r.merged_reason).replace("_", " ")))
            src = f"data/pmid_dedup_map.parquet ({r.merged_reason})"
            for pm, flag, lp, can in [(a, fa, b, b if fa == "preprint_with_published_version" else a), (b, fb, a, b)]:
                rows.append(dict(pmid=pm, flag=flag, linked_pmid=lp, linked_in_dataset=True, linked_package=None, linked_title=None,
                                 relation_note=note, canonical_pmid=can, n_findings=None, title=None, journal=None, year=None, doi=None,
                                 source=src, checked_utc=checked))
    F = pd.DataFrame(rows)
    F = F.drop_duplicates(["pmid", "flag", "linked_pmid"], keep="first")   # candidates win over the merge map
    F["flag_label"] = F.flag.map(FLAGS); F["recommended_use"] = F.flag.map(recommended_use)
    return F[FINAL_COLUMNS].reset_index(drop=True)


def load_paper_flags(root, candidates_csv=None, dedup_parquet=None):
    """Return (DataFrame in FINAL_COLUMNS, source description)."""
    files = final_files(root)
    if files:
        F = pd.concat([pd.read_csv(f, dtype={"pmid": str, "linked_pmid": str, "canonical_pmid": str}) for f in files], ignore_index=True)
        for c in FINAL_COLUMNS:
            if c not in F.columns: F[c] = None
        # a cell can link several records ("33532785; 33688642"): one row per link, titles filled from the papers table
        multi = F.linked_pmid.fillna("").astype(str).str.contains(";")
        F.loc[multi, "linked_title"] = None
        F["linked_pmid"] = F.linked_pmid.fillna("").astype(str).str.split(";")
        F = F.explode("linked_pmid", ignore_index=True); F["linked_pmid"] = F.linked_pmid.str.strip()
        F["pmid"] = F.pmid.map(_pmid); F["linked_pmid"] = F.linked_pmid.map(_pmid)
        F["flag_label"] = F.flag_label.where(F.flag_label.notna(), F.flag.map(FLAGS))
        F["recommended_use"] = F.recommended_use.where(F.recommended_use.notna(), F.flag.map(recommended_use))
        return F[FINAL_COLUMNS].drop_duplicates(["pmid", "flag", "linked_pmid"]).reset_index(drop=True), "final: " + ", ".join(os.path.relpath(f, root) for f in files)
    return from_candidates(root, candidates_csv, dedup_parquet), "candidates fallback (releases/v1.2/paper_flags/paper_flags_candidates.csv + pmid_dedup_map merges)"


if __name__ == "__main__":
    import sys
    F, src = load_paper_flags(sys.argv[1] if len(sys.argv) > 1 else ".", *(sys.argv[2:3] or [None]))
    print(src); print(F.groupby(["flag", "recommended_use"]).pmid.nunique().to_string())
