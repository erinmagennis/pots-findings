# POTS and dysautonomia literature findings

A public, machine-extracted research dataset and static browser covering the completed Tier 1 record plus the
current Tier 2 checkpoint.

## Findings packages v1.2 (the full corpus)

The complete harmonised corpus — **148,186 findings from 11,519 papers** across Tiers 1–4 — ships as five
self-contained packages under [`packages/`](packages/) (start at [`packages/README.md`](packages/README.md) and
[`packages/OVERVIEW.md`](packages/OVERVIEW.md)). Each package carries its data (Parquet + CSV), documentation,
QA tables, the code that built it and `CHECKSUMS.sha256`; `code/verify_package.py --self-test` re-checks a package end to end.

| version | tag | what changed |
|---|---|---|
| v1.2 | `v1.2` | Every model-emitted ontology identifier in Tiers 1–2 was looked up by id at its minting authority (HGNC, ChEBI, MeSH) and compared with the entity name. 14,055 rows are now `authority_verified_retrospective` (10,879 confirmed, 3,176 replaced by the id the name resolves to); 2,607 ids that denoted a different entity were withheld. The original model id is preserved in `ontology_id_v11_model_emitted`. No finding text, quote, direction, condition or paper changed. |
| v1.1 | `v1.1` | Five harmonised packages; Tier 1–2 identifiers flagged `unverified_model_emitted`. |

Join on `entity_ontology_id_resolved` only where `ontology_id_verification` is `authority_verified` or
`authority_verified_retrospective` (19,782 rows). **Scientific fidelity — whether each finding states what its paper
found — has not yet been checked by a human reader**; that audit is open and its result will be posted here and on the
site's About page. The browser below still serves the Tier 1 + Tier 2 checkpoint; it will move to v1.2 next.

## Current checkpoint

| Measure | Current value | Basis |
|---|---:|---|
| Combined findings | 73,070 | Tier 1 rows followed by current Tier 2 rows |
| Combined papers | 6,244 | Distinct canonical PMID |
| Canonical entities | 2,803 | Distinct canonical entity across both tiers |
| Tier 2 progress | 81 of 146 chunks | 55.5% |

Every Tier 2 and combined figure is a subset figure. Absence of a finding is not evidence of absence.

This is machine-extracted research information, not medical advice. Read and cite the original paper before
relying on a finding.

## Download and browse

The repository keeps the data available as individual files:

- `data/`: independently usable Tier 1 record
- `data/tier2/`: additive Tier 2 checkpoint and cross-tier tables
- `site/`: combined static browser
- `validation/`: frozen facts and verification rules

Each public checkpoint uses an immutable Git tag and release ZIP so `main` can continue into later Tier 2 batches
and Tiers 3 and 4. The completed Tier 1 documentation is preserved in
[`docs/TIER1_README.md`](docs/TIER1_README.md). Tier 2 starts at
[`docs/tier2/README_tier2.md`](docs/tier2/README_tier2.md).

## Quick start

```python
import pandas as pd

tier1 = pd.read_parquet("data/tier1_findings.parquet")
tier2 = pd.read_parquet("data/tier2/tier2_findings_canonical.parquet")

assert tier1.canonical_pmid.nunique() == 3121
assert tier2.canonical_pmid.nunique() == 3123
```

Run the website locally:

```bash
python -m http.server 8000 --directory site
```

Then open `http://localhost:8000/`.

## Verification

Before publishing any checkpoint:

```bash
python site_tools/verify_site.py --self-test
```

The gate checks frozen counts, canonical accounting, row order, shard alignment, site schemas, scope language,
and public-export structure. Browser review is the final rendered-site step.

## Important distinctions

- Co-mention is not interaction or causation.
- Shared biology across literatures is not the same as patient comorbidity.
- A condition label is not the same as the source literature that supplied the paper.
- Entity-based views cover 32.6% of current finding rows, not the whole dataset.
- A null result does not by itself establish ineffectiveness.

## Citation and license

Derived structured data is licensed under CC BY 4.0. Verbatim provenance text remains the copyright of its
respective authors and publishers and is not licensed by this project. See [`NOTICE.md`](NOTICE.md) and
[`CITATION.cff`](CITATION.cff).
