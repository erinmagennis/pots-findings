# Tier 1 — POTS and dysautonomia core literature

**36,067 findings · 3,129 papers · 76 chunks (0–75) · 2019–2026**

This package stands alone. It contains its slice of the corpus, the documentation needed to
read it, the QA evidence behind every number below, and the code to re-derive all of it.
Nothing here requires another download or a network connection.

```
python code/verify_package.py              # re-derive every number in this README
python code/verify_package.py --self-test  # prove the checker still catches regressions
```

---

## What changed in v1.2

**v1.2 (2026-10-21): every model-emitted identifier in this package was looked up by id at its minting
authority (HGNC via MyGene, ChEBI via OLS4, MeSH via NLM) and its label and full synonym list compared with the
entity name; names were also resolved forward to obtain the correct id where one exists. No model was involved.**

Of the 4,373 rows that carried a model-emitted id in v1.1: **2,385 denoted their entity** and are now tagged
`authority_verified_retrospective` with the match mode recorded (compound_partial 110, exact 1,255, exact_relaxed 398, synonym 622); **1,161 ids were replaced** by the id the
entity name resolves to (exact label or authority synonym; `ontology_id_source` says so); **827 were withheld** (`id_withheld_unverified_v1.2`:
the id denoted a different entity and the name did not resolve). The original model id is preserved on every affected row in
`ontology_id_v11_model_emitted`; on replaced rows `entity_ontology_label` / `ontology_label_final` carry the NEW id's label, fetched by id from the authority. Nothing else changed: no row was added or removed and no other column was edited.

Measured on this package's full population: **54.5% of the model-emitted ids denoted their entity**; the
rest existed but pointed at a neighbouring gene, a related compound or a sibling concept — near-miss assignment, not fabrication.
The v1.1 figure quoted below was an adjudicated SAMPLE and is kept for the record. Full method and corpus-wide numbers: `annotations/POTS_MODEL_ID_BENCHMARK.md`.

---

## Read this before you query

1. **Ontology identifiers were re-grounded in v1.2 — filter on `ontology_id_verification`.**
   Of 4,373 rows that carried a model-emitted id in v1.1, 2,385 denoted their entity at the authority and are tagged `authority_verified_retrospective`; 1,161 ids were replaced by the id the name resolves to; 827 were withheld (`id_withheld_unverified_v1.2`) because the id denoted another entity and the name did not resolve. The model's id is kept in `ontology_id_v11_model_emitted` for the record and must not be used for joins. Measured here: 54.5% of the model-emitted ids were correct; the rest were near-miss assignments (a neighbouring gene, a related compound), not fabrications. See `annotations/POTS_MODEL_ID_BENCHMARK.md`.
2. **Paper count is 3,129 here, not the 3,121 of the Tier 1 v1 release.**
   The v1 release counted `canonical_pmid.nunique()`, which merged 8 duplicate-title records. That column does not exist in the harmonized corpus. Both numbers are correct under their own basis; this package uses `pmid.nunique()` throughout.
3. **`canonical_entity` is empty in this package.**
   Cross-tier canonicalization was applied to Tiers 3 and 4 only. The lookup covering all five packages ships as `data/entity_vocabulary_crosstier.parquet` — join on `entity` to canonicalize Tier 1 yourself. It mutates no rows by design.
4. **Scientific fidelity is UNMEASURED.**
   Everything verified in `qa/` is well-formedness: quotes trace to source, identifiers carry authority provenance, invariants hold. **Nobody has checked that the extracted science is correctly interpreted.** That needs a human reader — an LLM adjudicator shares the extractor's blind spots. Treat every row as a pointer to a paper you should read, not as a fact.
5. **`condition` is a coarse POPULATION bucket, and the `MCAS` bucket is mostly not MCAS.**
   `condition` means the patient population the paper studied — not a diagnosis, not a mechanism-relevance tag. Its bucket definitions were written down only on 2026-09-16 (`annotations/CONDITION_BUCKET_DEFINITIONS.md`). A stratified census of the 1,083 `MCAS`-labelled papers corpus-wide projects ~69% study mast-cell biology with no mast-cell-disorder population, ~10% MCAS as defined, ~5% mastocytosis (a distinct clonal neoplasm). The shipped column is unchanged; `annotations/condition_annotations.parquet` (pmid-keyed) carries a per-paper verdict, all classifier-derived and `human_confirmed == False`. In this package 90 papers (231 rows) carry `condition == 'MCAS'`: 9 verified `in_bucket`, 4 `bucket_violation`, 77 unassessed.

---

## What is in this package

**Topic:** dysautonomia, POTS, dysautonomia subtypes, hyperadrenergic POTS

### Themes

| theme | findings | papers |
|---|---:|---:|
| `dysautonomia` | 16,032 | 1,433 |
| `POTS` | 9,246 | 711 |
| `dysautonomia_subtype` | 8,653 | 787 |
| `hyperadrenergic` | 2,112 | 194 |
| `patient_evidence` | 19 | 1 |
| `ME_CFS` | 5 | 3 |

### Conditions the findings are about

`condition` is a coarse bucket for the **patient population studied**, which is not the same as which
literature the paper came from (`source_literature`). A POTS paper reporting on a fibromyalgia
cohort has `source_literature` of the POTS/dysautonomia literature and `condition == 'fibromyalgia'`.
Bucket definitions: `annotations/CONDITION_BUCKET_DEFINITIONS.md`. Read warning 5 above before
counting anything by `condition` — only the `MCAS` bucket has been censused, and it is mostly not MCAS.

| condition | findings | papers |
|---|---:|---:|
| `dysautonomia` | 18,066 | 2,339 |
| `general` | 5,805 | 853 |
| `POTS` | 5,030 | 750 |
| `long_COVID` | 2,578 | 324 |
| `multiple` | 1,124 | 345 |
| `ME_CFS` | 835 | 136 |
| `fibromyalgia` | 748 | 103 |
| `small_fiber_neuropathy` | 633 | 202 |
| _6 more_ | | |

### Evidence quality

| | |
|---|---|
| findings per paper (overall) | 11.53 |
| findings per paper — `abstract-only` | 5.4 (1,207 papers, 6,522 findings) |
| findings per paper — `blocked` | 2.8 (5 papers, 14 findings) |
| findings per paper — `retrieved-fulltext` | 15.4 (1,917 papers, 29,531 findings) |

**Never compare findings-per-paper across packages without stratifying by
`fulltext_status`.** Yield is driven roughly 3× by whether full text was retrieved, and the
full-text mix differs sharply between packages. An unstratified comparison mostly measures
retrieval success, not extraction productivity.

| evidence tier | findings |
|---|---:|
| `cohort` | 8,146 |
| `cross-sectional` | 6,948 |
| `review/expert-opinion` | 6,434 |
| `case-report` | 3,754 |
| `case-series` | 3,219 |
| `case-control` | 3,139 |
| `mechanistic/in-vitro` | 2,747 |
| `RCT` | 854 |
| `meta-analysis` | 826 |

### Quote provenance

Every one of the 36,067 rows carries a `provenance_quote` — the span of source
text the finding was drawn from. Median 179 characters, 90th percentile
298, longest 746.

**6,536 of 36,067 rows (18.12%) are verifiable** — meaning the
quote's own source text still exists and can be re-read.

Abstract-derived rows only; body text was discarded after extraction, so full-text-derived quotes have no surviving source.

The unverifiable remainder is a **retention** failure, not an extraction failure. Where
source text is available, traceability across the corpus measures 94–99% with **0%
wrong-paper false positives in every stratum**. The body text was simply discarded after
extraction. `qa/` carries the census with its negative control.

**v1.1 retrofit:** the source of every paper in this package was re-fetched from Europe PMC and every quote
re-checked — **35,949 of 36,067 rows (99.67%) now have a checkable source**; full-text quotes trace at
97.43% (27,390/28,113), wrong-paper control 0/400.
This checks Europe PMC's *current* text, not the bytes the model read, and the text is not shipped; the figure above
is the shipped-source figure. Row-level results: `annotations/quote_retrofit_*.parquet` (see the Annotations section).

### Ontology grounding

| | |
|---|---|
| rows with a resolved ontology id | 3,546 (9.8% of rows) |
| rows naming an entity at all | 18,915 |
| id coverage among entity-naming rows | 18.8% |
| rows with both an id and an authority label | 3,546 |

**Verification status** — this is the column to filter on, not `ontology_id_source`:

| `ontology_id_verification` | rows |
|---|---:|
| `no_id` | 31,694 |
| `authority_verified_retrospective` | 3,546 |
| `id_withheld_unverified_v1.2` | 827 |

| identifier prefix | rows |
|---|---:|
| `None` | 31,694 |
| `HGNC` | 1,814 |
| `CHEBI` | 1,709 |
| `MESH` | 847 |
| `GO` | 3 |

### Invariants

The pinned nine-check suite, run unmodified on this exact slice: **8 of 9 pass.**

| check | result |
|---|---|
| `schema_completeness` | pass |
| `conservation` | pass |
| `monotonicity` | pass |
| `no_model_emitted_ids` | pass |
| `id_provenance` | **fail — see below** |
| `enum_drift` | pass |
| `duplicates` | pass |
| `hpo_multivalue` | pass |
| `authority_prefix_match` | pass |

#### Why these fail, and why they are not repaired

**`id_provenance`** — 4,373 rows carry a resolved ontology id and 2,681 carry an HGNC id, with no source tag. Tier 1 predates the provenance-tag convention entirely — `ontology_id_source` is null for every Tier 1 row. The identifiers are model-emitted and existence-checked only; the harmonized columns `ontology_id_verification` and `ontology_id_match_mode` record that fact explicitly. This is a KNOWN, DOCUMENTED property of Tier 1, not a defect introduced by packaging.

The suite was written during Tier 3 and encodes conventions Tiers 1 and 2 predate. These are
**pre-existing, characterized properties of the earlier extraction passes**, not damage from
packaging. They are shipped as failures rather than suppressed because the project rule is to
flag and never silently repair — a suite tuned until it passes is not a suite. The harmonized
`ontology_id_verification` / `ontology_id_match_mode` columns exist precisely so that a query
can respect this without reading the invariant output.

### Enum drift — flagged, never coerced

4 rows (0.0111%) carry a value outside the pinned enum for
their column. The extraction prompt pinned both vocabularies; the model drifted past the
constraint anyway. **These values are shipped verbatim.** Silently remapping them would
destroy the evidence that the drift happened, and two of them are arguments that the enum is
deficient rather than the output wrong.

| column | value | rows |
|---|---|---:|
| `condition` | `orthostatic_hypotension` | 4 |

- `orthostatic_hypotension` is a real and clinically distinct condition that the enum omits; it is adjacent to but not the same as POTS.

---

## Contents

| path | what it is |
|---|---|
| `data/tier1_findings.parquet` | **THE DATA.** 36,067 rows × 108 columns. Start here. |
| `data/tier1_findings.csv.gz` | Identical content as CSV, for tools without parquet support. |
| `data/entity_vocabulary_crosstier.parquet` | Canonicalization lookup, 39,128 raw strings → 36,173 canonical. Mutates no rows. |
| `data/chunk_order.parquet` | Paper → chunk → tier assignment for all 14,263 corpus papers. |
| `docs/README.md` | This file. |
| `docs/DATA_DICTIONARY.md` | Every column, with its measured fill rate in this package. |
| `docs/COMPARABILITY.md` | What may be pooled with the sibling packages and what will mislead you. |
| `docs/METHODS.md` | How the extraction ran, with the pinned parameters. |
| `docs/LIMITATIONS.md` | What is not known, not measured, and known wrong. |
| `docs/WEBSITE_INTEGRATION.md` | What is new for the site from this package, and what breaks on a careless load. |
| `qa/package_stats.json` | Every number in this README, machine-readable, with its basis. |
| `qa/invariants.json` | The nine-check suite output on this slice. |
| `qa/comparability_report.json` | The full cross-package alignment analysis. |
| `qa/*` | The original QA evidence from this tier's extraction run. |
| `code/verify_package.py` | Re-derives every number above from the shipped data. |
| `code/tier3_invariants*.py` | The pinned invariant modules, byte-identical to the build. |
| `code/quote_trace.py` | The quote matcher — refuses to report a rate without its negative control. |
| `code/*` | The extraction pipeline, prompt and driver used for this tier. |
| `code/README.md` | The role of every file in `code/` — including why a Tier-1 package carries `tier3_*` modules. |
| `code/comparator_symmetry_tests.py` | Pins that the quote matcher decodes entities and folds whitespace on BOTH sides. |
| `MANIFEST.json` | File inventory with SHA-256 for every file. |
| `CHECKSUMS.sha256` | `shasum -a 256 -c CHECKSUMS.sha256` to verify the download. |
| `LICENSE` | CC BY 4.0 for the data; the quote column is separately described. |
| `CITATION.cff` | How to cite this package. |
| `annotations/*` | ADDITIVE annotation tables keyed to this package's rows/papers — see below. |

## Quickstart

```python
import pandas as pd
df = pd.read_parquet('data/tier1_findings.parquet')

# 1. Findings you can independently verify against source text
verifiable = df[df.fulltext_status.isin(['abstract-only', 'blocked'])]
#  -> 6,536 rows (18.12%)

# 2. Ontology identifiers — filter on VERIFICATION, never on coverage (v1.2 re-grounding)
df.ontology_id_verification.value_counts()
#  -> no_id, authority_verified_retrospective, id_withheld_unverified_v1.2
grounded = df[df.ontology_id_verification.isin(['authority_verified', 'authority_verified_retrospective'])]
#  -> 3,546 rows whose id was confirmed at its authority (1,161 of them replaced by the id the name resolves to)
withheld = df[df.ontology_id_verification == 'id_withheld_unverified_v1.2']
#  -> 827 rows: the model-emitted id denoted another entity; it is kept in ontology_id_v11_model_emitted, not in entity_ontology_id_resolved

# 3. Highest-confidence evidence
#    NOTE: `certainty_derived` is EMPTY in this package - it was introduced in Tier 3.
#    Use `certainty`, the extractor's own judgment, which is populated here.
strong = df[df.evidence_tier.isin(['meta-analysis', 'RCT'])
            & df.certainty.eq('confirmed')]
#  -> 1,113 rows

# 4. Marker frequency — case-fold, or canonicalize with the shipped vocabulary
vocab = pd.read_parquet('data/entity_vocabulary_crosstier.parquet')
df = df.merge(vocab[['raw_entity', 'canonical_entity']]
              .rename(columns={'raw_entity': 'entity',
                               'canonical_entity': 'canon'}),
              on='entity', how='left')
top = df.canon.value_counts().head(20)
```

**Never lowercase entity names to merge them.** `MECP2` and `Mecp2` are the human and mouse
genes and must stay apart. The shipped vocabulary holds every mandated ortholog pair apart
(CNTNAP2/Cntnap2, IL6/Il6, TH/Th, PIEZO2/Piezo2, …) and scored 0 false merges against 25
planted should-not-merge controls, with 2,459 of 2,460 should-merge pairs correct.

### A note on `certainty_derived` and other Tier-3-onward columns

Several columns were introduced partway through the project and are **entirely empty** in the
earlier packages: `certainty_derived`, `entity_kind`, `number_in_quote`, `canonical_entity`,
`hpo_ids_verified`, `phenotype_terms`. In those packages a null means **the property was never
captured**, not that it was measured and found absent.

The `cap_*` flags exist so a query can tell the difference without consulting documentation:

```python
df.cap_entity_kind.iloc[0]   # False -> this tier does not carry entity_kind at all
```

`docs/DATA_DICTIONARY.md` lists every empty column in this package.

---

## Annotations (additive)

The tables below were produced AFTER the tier data was frozen and ship as separate, ADDITIVE
files. No row of `data/` was modified. Join them on the stated key; every rate they carry states
its numerator, denominator and basis. They are covered by `MANIFEST.json` and `CHECKSUMS.sha256`.

| file | rows | keyed on | what it is |
|---|---:|---|---|
| `annotations/COMPARATOR_GATE.json` | — | — | Regression gate run before the retrofit: the shipped comparator reproduces Tier 4's 99.09% and is entity-code symmetric (42/42). |
| `annotations/CONDITION_ANNOTATIONS_README.md` | — | — | Schema and coverage of condition_annotations, and how to join it. |
| `annotations/CONDITION_BUCKET_DEFINITIONS.md` | — | — | v1 written definitions of the `condition` buckets (MCAS decided; others provisional) and the MCAS census that prompted them. |
| `annotations/POTS_MODEL_ID_BENCHMARK.json` | — | see file | additive annotation table |
| `annotations/POTS_MODEL_ID_BENCHMARK.md` | — | see file | additive annotation table |
| `annotations/RETROFIT_REPORT.md` | — | — | The retrofit report: deviations, per-stratum rates with controls, itemised permanent losses, untraceable examples. |
| `annotations/condition_annotations.csv` | 1,083 | `pmid` | CSV twin of condition_annotations.parquet. |
| `annotations/condition_annotations.parquet` | 1,083 | `pmid` | Per-paper verdict on the `condition == 'MCAS'` bucket under population-studied semantics (`in_bucket` / `bucket_violation` / `NEEDS_HUMAN`), classifier-derived, none human-confirmed. |
| `annotations/quote_retrofit_tier1.parquet` | 36,067 | `row_idx` = 0-based row of `data/<pkg>_findings.parquet` (+ `pmid`, `quote_sha1` as checks) | Per-row quote traceability against source text re-fetched from Europe PMC on 2026-09-16, with source depth, fetch status and the wrong-paper control. Null `retrofit_traceable` means no source exists today. |
| `annotations/retrofit_fetch_log.parquet` | 10,428 | `pmid` | One row per Tier 1–3 paper attempted in the retrofit: abstract/full-text availability, PMCID, HTTP outcome, fetch date. |
| `annotations/retrofit_summary.json` | — | — | Machine-readable retrofit numbers for all four Tier 1–3 packages, every rate with numerator, denominator and basis. |

### Quote source retrofit (2026-09-16)

The body text this tier was extracted from was discarded after extraction, so the `quotes verifiable`
figure above (18.12%) is what the shipped data alone supports. On 2026-09-16 the
source text of every paper was re-fetched from Europe PMC at the pinned pacing and every quote re-checked
with the shipped comparator (`code/quote_trace.py`, `code/retrofit_census.py`). The fetched text is
**not** shipped (see LICENSE); the row-level result is `annotations/quote_retrofit_tier1.parquet`.

| | rows | of | rate | basis |
|---|---:|---:|---:|---|
| verifiable before | 6,536 | 36,067 | 18.12% | shipped data: abstract-derived rows only |
| verifiable after | 35,949 | 36,067 | 99.67% | rows whose own re-fetched source exists |
| traceable, full-text rows vs re-fetched full text | 27,390 | 28,113 | 97.43% | control 0/400 wrong-paper false positives |
| traceable, abstract-stratum rows vs re-fetched abstract | 6,001 | 6,465 | 92.82% | control 0/400 |
| traceable, all verifiable rows | 33,393 | 35,949 | 92.89% | **stratify on `retrofit_source_depth × fulltext_status` before quoting** |

118 rows have no source in Europe PMC today (neither abstract nor body) and stay unverifiable. 1,371 full-text rows whose body could not be re-fetched were checked against the abstract only and trace at ≈0% for source-depth reasons, not because the quote is wrong. Europe PMC's *current* text was used, so a
paper revised since extraction registers as untraceable. Traceability is well-formedness, not correctness:
a traceable quote can still support a misread finding.

### Condition bucket annotations

`annotations/condition_annotations.parquet` covers the 90 papers (231 rows) in this
package labelled `condition == 'MCAS'`: **9 `in_bucket`, 4 `bucket_violation`**
(0 mastocytosis, 0 mast-cell biology without a disorder population,
4 neither), **77 `NEEDS_HUMAN`**. Verdicts are classifier-derived against
`CONDITION_BUCKET_DEFINITIONS.md` v1 under population-studied semantics and none is human-confirmed.
Other buckets are not yet censused. See `annotations/CONDITION_ANNOTATIONS_README.md`.

---

## The other four packages

This is one block of a five-way partition of a single corpus. **Zero papers are shared
between any two packages** — verified by pmid set intersection across all ten pairs at build
time. Per-package counts sum exactly to the corpus totals.

| package | findings | papers | chunks | identifiers | quotes verifiable |
|---|---:|---:|---:|---|---:|
| Tier 1 ← | 36,067 | 3,129 | 76 | model-emitted | 18.12% |
| Tier 2 Part A | 36,611 | 3,123 | 81 | model-emitted | 21.07% |
| Tier 2 Part B | 33,830 | 2,589 | 64 | model-emitted | 19.39% |
| Tier 3 | 26,032 | 1,587 | 35 | authority-derived | 12.22% |
| Tier 4 | 15,646 | 1,091 | 30 | authority-derived | 100.0% |
| **corpus total** | **148,186** | **11,519** | **286** | | **26.75%** |

Pooling any subset is safe for row and paper counts, paper metadata, quote presence, the
harmonized verification columns, and the capability flags. Eleven other metrics are **not**
comparable across all five — `docs/COMPARABILITY.md` lists each with its reason.

Tier 2 Part A and Part B are the two waves of a single extraction pass with one pipeline and
one prompt; pool those two freely.

---

Built 2026-10-22T12:15:40Z from harmonized corpus `f0b86f9a-f688-48c4-a08f-94e946afb9af`.
Data CC BY 4.0. Machine-extracted research information — **not medical advice.**
