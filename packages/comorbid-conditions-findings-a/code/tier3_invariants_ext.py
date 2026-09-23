"""Invariant 9 — authority/prefix agreement. Extends tier3_invariants.py (8 checks).
Found by an independent audit of the 35-chunk corpus: 49 rows claimed provenance
"authority_lookup_ols_hp" while holding GO/PATO/MPATH/NBO/UBERON ids. The ids and
labels are CORRECT -- OLS4 hp-scoped search returns terms imported into HPO, keeping
their native prefixes, and the resolver stored obo_id verbatim. The defect was the
PROVENANCE CLAIM, and the 8-check suite could not see it because it only verified that
a source tag EXISTS, never that it AGREES with the id it labels.
Pre-existing: 29 of the 49 rows are in the 22-chunk corpus and went unreported there.
"""

import re, pandas as pd

AUTH_PREFIX = {'hp': 'HP', 'chebi': 'CHEBI', 'cl': 'CL', 'uberon': 'UBERON', 'ncbitaxon': 'NCBITaxon', 'uniprot': 'UniProt'}

def check_authority_prefix_match(df):
    """INVARIANT 9. An ID's prefix must match the authority its provenance tag names.
    Gap this closes: OLS4 searched with ontology=hp returns terms IMPORTED into HPO
    (GO, PATO, MPATH, NBO, UBERON) carrying their native prefixes. The resolver stored
    obo_id verbatim, so 49 rows claimed source 'authority_lookup_ols_hp' while holding a
    non-HP id -- IDs and labels correct, PROVENANCE CLAIM wrong.
    A source may DECLARE imported prefixes as '..._crossontology[GO+PATO]'; those are
    then permitted, because the tag no longer misstates who minted the id."""
    out={"name":"authority_prefix_match","mismatches":{},"n_mismatched_rows":0}
    for idc, srcc in [("hpo_ids_verified","hpo_id_source"),
                      ("entity_ontology_id_resolved","ontology_id_source")]:
        if idc not in df.columns or srcc not in df.columns: continue
        sub=df[df[idc].notna() & df[srcc].notna()]
        for ids, s in zip(sub[idc].astype(str), sub[srcc].astype(str)):
            m=re.search(r'ols_([a-z]+)|(uniprot)', s)
            if not m: continue
            want=AUTH_PREFIX.get((m.group(1) or m.group(2)))
            if not want: continue
            declared={want} | set(re.findall(r'crossontology\[([^\]]+)\]', s)[0].split("+")) if "crossontology[" in s else {want}
            for x in [y.strip() for y in ids.split(";") if y.strip()]:
                if x.split(":")[0] not in declared:
                    out["mismatches"].setdefault(s, set()).add(x.split(":")[0]); out["n_mismatched_rows"]+=1
    out["mismatches"]={k:sorted(v) for k,v in out["mismatches"].items()}
    out["ok"]=out["n_mismatched_rows"]==0
    return out
