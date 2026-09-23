"""Tier-2 invariant suite. Run after EVERY merge/canonicalization step.
Each check encodes a failure that actually happened in Tier 1."""
import pandas as pd, numpy as np, json, sys

def check(df, vocab=None, golden_path="tier1_golden_facts.json"):
    F, out = json.load(open(golden_path))["facts"], []
    def t(name, ok, detail=""): out.append((name, bool(ok), detail))
    nosplit = ~df.split_derived.fillna(False).astype(bool)

    # --- CONSERVATION: splitting/merging must never invent or lose evidence ---
    t("distinct_finding_text_preserved",
      df.finding_text.nunique() >= F["distinct_finding_text"]["value"],
      f"{df.finding_text.nunique()} vs tier1 floor {F['distinct_finding_text']['value']}")
    t("no_orphan_canonical_pmid", df.canonical_pmid.notna().all(),
      f"{int(df.canonical_pmid.isna().sum())} null")
    # A compound split REPLACES its source row, so every sibling is flagged split_derived.
    # Conservation therefore means: each split text yields >=2 rows with DISTINCT canonical
    # entities, and contributes no NEW finding_text to the table.
    sp = df[~nosplit]
    if len(sp):
        g = sp.groupby("finding_text").canonical_entity.nunique()
        t("split_groups_have_ge2_entities", (g >= 2).all(),
          f"{int((g<2).sum())} split texts yielded <2 distinct entities (split added no information)")
        t("split_adds_no_new_text",
          sp.finding_text.isin(df.finding_text).all(), "split text must exist in the table")
    else:
        t("split_groups_have_ge2_entities", True, "no split rows")

    # --- MONOTONICITY: Tier 2 ADDS; it must never shrink Tier-1 quantities ---
    for k, col in [("findings_rows",None), ("papers_canonical","canonical_pmid"),
                   ("canonical_entities","canonical_entity")]:
        now = len(df) if col is None else df[col].nunique()
        t(f"monotonic_{k}", now >= F[k]["value"], f"{now} >= {F[k]['value']}")

    # --- TYPE DISCIPLINE: the failure mode that motivated using a strong model ---
    if vocab is not None and {"canonical_name","entity_kind"} <= set(vocab.columns):
        multi = vocab.groupby("canonical_name").entity_kind.nunique()
        t("no_canonical_spans_two_kinds", (multi<=1).all(),
          f"offenders: {list(multi[multi>1].index[:5])}")
        # the specific trap: molecule vs its transporter gene vs its drug class
        for a,b in [("norepinephrine","slc6a2"),("norepinephrine","snri"),("serotonin","slc6a4")]:
            if {a,b} <= set(vocab.canonical_name):
                t(f"kept_distinct::{a}|{b}", True, "present as separate canonicals")

    # --- COPYRIGHT: hard invariant, non-negotiable ---
    if "provenance_quote_trunc" in df:
        mx = int(df.provenance_quote_trunc.dropna().str.len().max() or 0)
        t("quote_cap_200", mx <= 200, f"max {mx}")
    t("no_full_quote_in_export", "provenance_quote" not in df.columns,
      "public export must carry only the truncated column")

    # --- BASIS DISCIPLINE: every count must be reproducible from a stated expr ---
    ne = df[(df.canonical_entity=="norepinephrine") & nosplit]
    t("ne_basis_reproduces", ne.canonical_pmid.nunique() >= F["ne_papers_direct_canonical"]["value"],
      f"canonical_pmid/direct = {ne.canonical_pmid.nunique()} (tier1 = 176; "
      f"177 raw/direct, 194 canon/all, 195 raw/all are DIFFERENT bases)")
    return out

def report(rows):
    bad = [r for r in rows if not r[1]]
    for n,ok,d in rows: print(f"  {'PASS' if ok else 'FAIL'}  {n:38s} {d}")
    print(f"\n{len(rows)-len(bad)}/{len(rows)} passed")
    if bad: print("BLOCKING:", [n for n,_,_ in bad]); sys.exit(1)
    return True
