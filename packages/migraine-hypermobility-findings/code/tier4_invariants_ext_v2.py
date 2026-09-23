"""Invariant 9, Tier-4 — authority/prefix AGREEMENT under the recorded-minting shape.

Extends tier3_invariants.py (checks 1-8) and supersedes tier3_invariants_ext.py.

WHAT THIS CHECKS
    An identifier's prefix must AGREE with what its provenance actually CLAIMS -- not
    merely that a provenance tag exists. The Tier-3 8-check suite verified existence
    only, which is why 49 rows tagged `authority_lookup_ols_hp` while holding
    GO/PATO/MPATH/NBO/UBERON ids passed QA, 29 of them across two corpus builds.

WHAT CHANGED FOR TIER 4
    tier4_resolver.py adopts option (b): the id keeps its native prefix and the MINTING
    ontology is recorded, both in the source tag (`..._ols_hp_via_pato_exact`, or
    `..._ols_hp_via_go+pato_synonym` when a multi-id row imports from several) and in a
    sibling column `<id_col>_minting_ontology`. This check therefore permits a foreign
    prefix ONLY when the provenance declares that exact minting ontology. Anything the
    tag does not declare still FAILS -- including every one of the 49 Tier-3 rows under
    their original bare tag.

    Three ways provenance may license a prefix:
      1. the queried authority's own prefix                      (always)
      2. a `_via_<mint>[+<mint>...]` infix naming the minter      (Tier-4 shape)
      3. the legacy `_crossontology[GO+PATO]` declaration         (Tier-3 shape, kept)
    A `<id_col>_minting_ontology` column, when present, is ALSO cross-checked against the
    ids: a column that disagrees with the prefixes it describes is itself a mismatch.
    The column is corroboration, never a licence -- it cannot excuse an undeclared tag,
    otherwise the check would launder the defect it exists to catch.

NEGATIVE CONTROL
    run_unit_tests() asserts the check FIRES on the real Tier-3 offenders and STAYS
    SILENT on clean rows. A check that passes everything is not a check.
"""

import re

AUTH_PREFIX = {"hp": "HP", "chebi": "CHEBI", "cl": "CL", "uberon": "UBERON",
               "ncbitaxon": "NCBITaxon", "uniprot": "UniProt"}

# id prefix (upper) for a minting-ontology tag; unknown tags fall back to tag.upper()
_MINT_PREFIX = {"hp": "HP", "pato": "PATO", "go": "GO", "mpath": "MPATH", "nbo": "NBO",
                "uberon": "UBERON", "chebi": "CHEBI", "cl": "CL",
                "ncbitaxon": "NCBITaxon", "uniprot": "UniProt"}

_TAG_RE = re.compile(r"authority_lookup_(?:ols_([a-z]+?)(?:_via_([a-z0-9+]+))?"
                     r"(?:_(?:exact|synonym))?|(uniprot))(?:_(?:exact|synonym))?$")


def _mint_prefix(tag):
    return _MINT_PREFIX.get(tag, tag.upper())


def declared_prefixes(source):
    """-> set of id prefixes this provenance string LICENSES, or None if it names no authority."""
    s = str(source or "")
    m = _TAG_RE.search(s)
    if not m:
        m = re.search(r"authority_lookup_(?:ols_([a-z]+)|(uniprot))", s)
        if not m:
            return None
        auth = m.group(1) or m.group(2)
        via = None
    else:
        auth = m.group(1) or m.group(3)
        via = m.group(2)
    want = AUTH_PREFIX.get(auth)
    if not want:
        return None
    allowed = {want}
    if via:
        allowed |= {_mint_prefix(t) for t in via.split("+") if t}
    for grp in re.findall(r"crossontology\[([^\]]+)\]", s):
        allowed |= {t.strip() for t in grp.split("+") if t.strip()}
    return allowed


def _split(v):
    return [x.strip() for x in str(v).split(";") if x.strip()]


def check_authority_prefix_match(df, pairs=None):
    """INVARIANT 9. Every id prefix must be one its provenance declares.

    pairs: [(id_col, source_col)] -- defaults to the corpus's two id-bearing column pairs.
    Returns a dict; ok=True only when nothing mismatched. Counts are computed, not typed.
    """
    pairs = pairs or [("hpo_ids_verified", "hpo_id_source"),
                      ("entity_ontology_id_resolved", "ontology_id_source")]
    out = {"name": "authority_prefix_match_v4", "mismatches": {}, "n_mismatched_rows": 0,
           "n_mismatched_ids": 0, "n_rows_checked": 0, "n_ids_checked": 0,
           "n_undeclared_tag_rows": 0, "n_minting_column_disagreements": 0,
           "columns_checked": []}
    for idc, srcc in pairs:
        if idc not in df.columns or srcc not in df.columns:
            continue
        out["columns_checked"].append(idc)
        mintc = f"{idc}_minting_ontology"
        has_mint = mintc in df.columns
        sub = df[df[idc].notna() & df[srcc].notna()]
        mint_vals = sub[mintc] if has_mint else [None] * len(sub)
        for ids, s, mv in zip(sub[idc].astype(str), sub[srcc].astype(str), mint_vals):
            allowed = declared_prefixes(s)
            if allowed is None:
                continue
            id_list = _split(ids)
            out["n_rows_checked"] += 1
            out["n_ids_checked"] += len(id_list)
            # A per-id tag list (one tag per id, semicolon-joined) declares each id's
            # OWN minting ontology; unioning them into one allowed set would reject a
            # truthful positional declaration. Compare positionally when lengths align.
            tag_list = _split(s)
            if len(tag_list) == len(id_list) and len(id_list) > 1:
                bad = []
                for x, tg in zip(id_list, tag_list):
                    per = declared_prefixes(tg)
                    if per is not None and x.split(":")[0] not in per:
                        bad.append(x)
            else:
                bad = [x for x in id_list if x.split(":")[0] not in allowed]
            if bad:
                out["n_mismatched_rows"] += 1
                out["n_mismatched_ids"] += len(bad)
                out["n_undeclared_tag_rows"] += 1
                key = f"{idc}|{s}"
                out["mismatches"].setdefault(key, set()).update(x.split(":")[0] for x in bad)
            # corroboration: a minting column must agree with the prefixes it describes
            if has_mint and mv is not None and str(mv).strip() and str(mv) != "None":
                col_mints = _split(mv)
                if len(col_mints) == len(id_list):
                    off = [(x, m) for x, m in zip(id_list, col_mints)
                           if m and x.split(":")[0] != _mint_prefix(m)]
                    if off:
                        out["n_minting_column_disagreements"] += 1
                        if not bad:
                            out["n_mismatched_rows"] += 1
                            out["n_mismatched_ids"] += len(off)
                        out["mismatches"].setdefault(f"{idc}|minting_column_disagrees", set()) \
                                         .update(x.split(":")[0] for x, _ in off)
    out["mismatches"] = {k: sorted(v) for k, v in out["mismatches"].items()}
    out["ok"] = out["n_mismatched_rows"] == 0
    return out


def run_unit_tests(positive_df=None, negative_df=None):
    """-> dict of results. POSITIVE control must FAIL the check; NEGATIVE must PASS.

    positive_df: real Tier-3 offender rows under their ORIGINAL bare tags.
    negative_df: clean rows (native-prefix ids, correctly tagged).
    Both default to small synthetic frames built from real Tier-3 id/label pairs so the
    module is testable offline; pass the real frames to test against the corpus.
    """
    import pandas as pd
    res = {}
    if positive_df is None:
        positive_df = pd.DataFrame({
            "hpo_ids_verified": ["PATO:0001815", "MPATH:196;HP:0011123", "GO:0070527"],
            "hpo_id_source": ["authority_lookup_ols_hp",
                              "authority_lookup_ols_hp_synonym",
                              "authority_lookup_ols_hp"],
        })
    if negative_df is None:
        negative_df = pd.DataFrame({
            "hpo_ids_verified": ["HP:0002315", "HP:0012432;HP:0002094", "HP:0004409"],
            "hpo_id_source": ["authority_lookup_ols_hp",
                              "authority_lookup_ols_hp_synonym",
                              "authority_lookup_ols_hp_exact"],
        })

    p = check_authority_prefix_match(positive_df)
    res["positive_old_tag"] = {"ok": p["ok"], "n_mismatched_rows": p["n_mismatched_rows"],
                               "n_rows": int(len(positive_df)),
                               "passes_test": (not p["ok"]) and p["n_mismatched_rows"] == len(positive_df)}

    n = check_authority_prefix_match(negative_df)
    res["negative_clean"] = {"ok": n["ok"], "n_mismatched_rows": n["n_mismatched_rows"],
                             "n_rows": int(len(negative_df)),
                             "n_ids_checked": n["n_ids_checked"],
                             "passes_test": n["ok"] and n["n_ids_checked"] > 0}

    # SAME rows, retagged truthfully by tier4_resolver -> must now PASS
    fixed = positive_df.copy()
    fixed_tags, fixed_mints = [], []
    for ids, s in zip(fixed["hpo_ids_verified"].astype(str), fixed["hpo_id_source"].astype(str)):
        mints = [x.split(":")[0].lower() for x in _split(ids)]
        foreign = sorted({m for m in mints if m != "hp"})
        path = "synonym" if s.endswith("synonym") else "exact"
        fixed_tags.append(f"authority_lookup_ols_hp_via_{'+'.join(foreign)}_{path}"
                          if foreign else f"authority_lookup_ols_hp_{path}")
        fixed_mints.append(";".join(mints))
    fixed["hpo_id_source"] = fixed_tags
    fixed["hpo_ids_verified_minting_ontology"] = fixed_mints
    fx = check_authority_prefix_match(fixed)
    res["positive_retagged_truthful"] = {"ok": fx["ok"], "n_mismatched_rows": fx["n_mismatched_rows"],
                                         "n_rows": int(len(fixed)), "passes_test": fx["ok"]}

    # ADVERSARIAL 1: truthful-looking tag that declares the WRONG minter -> must FAIL
    adv = pd.DataFrame({
        "hpo_ids_verified": ["PATO:0001815"],
        "hpo_id_source": ["authority_lookup_ols_hp_via_go_exact"],
        "hpo_ids_verified_minting_ontology": ["pato"],
    })
    a = check_authority_prefix_match(adv)
    res["adversarial_wrong_minter_declared"] = {"ok": a["ok"], "n_mismatched_rows": a["n_mismatched_rows"],
                                                "passes_test": not a["ok"]}

    # ADVERSARIAL 2: a minting COLUMN must not launder an undeclared bare tag -> must FAIL
    adv2 = pd.DataFrame({
        "hpo_ids_verified": ["MPATH:196"],
        "hpo_id_source": ["authority_lookup_ols_hp"],
        "hpo_ids_verified_minting_ontology": ["mpath"],
    })
    a2 = check_authority_prefix_match(adv2)
    res["adversarial_column_cannot_launder_tag"] = {"ok": a2["ok"],
                                                    "n_mismatched_rows": a2["n_mismatched_rows"],
                                                    "passes_test": not a2["ok"]}

    # ADVERSARIAL 3: minting column contradicting its own ids -> must FAIL
    adv3 = pd.DataFrame({
        "hpo_ids_verified": ["HP:0002315"],
        "hpo_id_source": ["authority_lookup_ols_hp_exact"],
        "hpo_ids_verified_minting_ontology": ["pato"],
    })
    a3 = check_authority_prefix_match(adv3)
    res["adversarial_minting_column_contradicts_ids"] = {
        "ok": a3["ok"], "n_mismatched_rows": a3["n_mismatched_rows"], "passes_test": not a3["ok"]}

    res["all_passed"] = all(v["passes_test"] for v in res.values() if isinstance(v, dict))
    return res
