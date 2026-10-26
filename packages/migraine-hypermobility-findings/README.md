# POTS findings v1.2, package 5 of 5: migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS (15,646 findings, 1,091 papers)

**15,646 findings · 1,091 papers · 30 chunks (256–285) · 2020–2026**

Build stage tier4 of the corpus. Where "tier" appears in file and column names (`data/tier4_findings.parquet`,
`tier_source`, `MANIFEST.tier`) it names the build stage in which these rows were extracted, not a rank or a quality grade.

This package stands alone. It contains its slice of the corpus, the documentation needed to
read it, the QA evidence behind every number below, and the code to re-derive all of it.
Nothing here requires another download or a network connection.

```
python code/verify_package.py              # re-derive every number in this README
python code/verify_package.py --self-test  # prove the checker still catches regressions
```

---

## Read this before you query

1. **Every quote in this package is verifiable, the only package where that is true.**
   Body text was retained in gzipped chunk archives, so all 15,646 rows can be re-checked against their own source. Corpus-wide the figure is 26.75% (39,637 of 148,186 rows). Traceability measured 99.09% with 0% wrong-paper false positives.
2. **Identifiers are authority-derived and score 0.998, the highest in the corpus.**
   Note that Tier 4 also has the LOWEST identifier coverage (10.3% of rows). Coverage and correctness rank the packages in opposite orders; see COMPARABILITY.md, Trap 1.
3. **1,960 rows are flagged `screen_verdict_uncertain`, and coverage has two true values.**
   Tier 4 papers passed an LLM+rule screen because its themes (migraine, Sjögren's, PANS/PANDAS, hypermobility spectrum) sit at the corpus boundary. Coverage is 85.97% of screened papers and 74.57% of the pre-screening universe. Both are true; state which you mean. Excluded PMIDs with reasons are in `scope/`.
4. **Scientific fidelity is UNMEASURED.**
   Everything verified in `qa/` is well-formedness: quotes trace to source, identifiers carry authority provenance, invariants hold. **Nobody has checked that the extracted science is correctly interpreted.** That needs a human reader, an LLM adjudicator shares the extractor's blind spots. Treat every row as a pointer to a paper you should read, not as a fact.
5. **`condition` is a coarse POPULATION bucket, and the `MCAS` bucket is mostly not MCAS.**
   `condition` means the patient population the paper studied, not a diagnosis, not a mechanism-relevance tag. Its bucket definitions were written down only on 2026-09-16 (`annotations/CONDITION_BUCKET_DEFINITIONS.md`). A stratified census of the 1,083 `MCAS`-labelled papers corpus-wide projects ~69% study mast-cell biology with no mast-cell-disorder population, ~10% MCAS as defined, ~5% mastocytosis (a distinct clonal neoplasm). The shipped column is unchanged; `annotations/condition_annotations.parquet` (pmid-keyed) carries a per-paper verdict, all classifier-derived and `human_confirmed == False`. In this package 36 papers (240 rows) carry `condition == 'MCAS'`: 0 verified `in_bucket`, 22 `bucket_violation`, 14 unassessed.

---

## What is in this package

**Topic:** migraine intersection, author-augmented papers, hypermobility spectrum, Sjögren's, PANS/PANDAS

### Themes

| theme | findings | papers |
|---|---:|---:|
| `migraine_intersection` | 9,503 | 589 |
| `author_augment` | 3,334 | 286 |
| `sjogrens` | 1,197 | 68 |
| `hypermobility_spectrum` | 1,086 | 101 |
| `pans_pandas` | 526 | 47 |

### Conditions the findings are about

`condition` is a coarse bucket for the **patient population studied**, which is not the same as which
literature the paper came from (`source_literature`). A POTS paper reporting on a fibromyalgia
cohort has `source_literature` of the POTS/dysautonomia literature and `condition == 'fibromyalgia'`.
Bucket definitions: `annotations/CONDITION_BUCKET_DEFINITIONS.md`. Read warning 5 above before
counting anything by `condition`: only the `MCAS` bucket has been censused, and it is mostly not MCAS.

| condition | findings | papers |
|---|---:|---:|
| `migraine` | 6,259 | 543 |
| `general` | 3,591 | 386 |
| `dysautonomia` | 1,877 | 243 |
| `fibromyalgia` | 952 | 182 |
| `EDS_hypermobility` | 934 | 109 |
| `multiple` | 743 | 159 |
| `long_COVID` | 493 | 41 |
| `MCAS` | 240 | 36 |
| _5 more_ | | |

### Evidence quality

| | |
|---|---|
| findings per paper (overall) | 14.34 |
| findings per paper: `abstract-only` | 6.63 (505 papers, 3,347 findings) |
| findings per paper: `blocked` | 6.67 (3 papers, 20 findings) |
| findings per paper: `retrieved-fulltext` | 21.06 (583 papers, 12,279 findings) |

**Never compare findings-per-paper across packages without stratifying by
`fulltext_status`.** Yield is driven roughly 3× by whether full text was retrieved, and the
full-text mix differs sharply between packages. An unstratified comparison mostly measures
retrieval success, not extraction productivity.

| evidence tier | findings |
|---|---:|
| `cross-sectional` | 3,491 |
| `cohort` | 3,452 |
| `review/expert-opinion` | 2,702 |
| `case-control` | 1,297 |
| `case-series` | 1,241 |
| `mechanistic/in-vitro` | 1,162 |
| `RCT` | 1,100 |
| `meta-analysis` | 679 |
| `case-report` | 514 |
| `systematic-review/meta-analysis` | 8 |

### Quote provenance

Every one of the 15,646 rows carries a `provenance_quote`: the span of source
text the finding was drawn from. Median 178 characters, 90th percentile
297, longest 1065.

**15,646 of 15,646 rows (100.0%) are verifiable**: meaning the
quote's own source text still exists and can be re-read.

All rows: body text retained in gzipped chunk archives, so every quote is re-checkable.

This is the only package where verifiability is complete. Traceability measured 99.09%
against a 0% wrong-paper negative control. `qa/tier4_quote_census.json` carries the census.

### Ontology grounding

| | |
|---|---|
| rows with a resolved ontology id | 1,614 (10.3% of rows) |
| rows naming an entity at all | 11,259 |
| id coverage among entity-naming rows | 14.3% |
| rows with both an id and an authority label | 1,614 |

**Verification status**: this is the column to filter on, not `ontology_id_source`:

| `ontology_id_verification` | rows |
|---|---:|
| `no_id` | 14,032 |
| `authority_verified` | 1,614 |

| identifier prefix | rows |
|---|---:|
| `None` | 14,032 |
| `CHEBI` | 1,614 |

### Invariants

The pinned nine-check suite, run unmodified on this exact slice: **9 of 9 pass.**

| check | result |
|---|---|
| `schema_completeness` | pass |
| `conservation` | pass |
| `monotonicity` | pass |
| `no_model_emitted_ids` | pass |
| `id_provenance` | pass |
| `enum_drift` | pass |
| `duplicates` | pass |
| `hpo_multivalue` | pass |
| `authority_prefix_match` | pass |

All nine pass. The suite is verified against planted regressions, not merely against data that
happened to pass: `python code/verify_package.py --self-test` re-plants six and asserts each
is caught.

### Enum drift, flagged, never coerced

8 rows (0.0511%) carry a value outside the pinned enum for
their column. The extraction prompt pinned both vocabularies; the model drifted past the
constraint anyway. **These values are shipped verbatim.** Silently remapping them would
destroy the evidence that the drift happened, and two of them are arguments that the enum is
deficient rather than the output wrong.

| column | value | rows |
|---|---|---:|
| `evidence_tier` | `systematic-review/meta-analysis` | 8 |

- `systematic-review/meta-analysis` and `systematic review` are the model splitting a distinction the enum collapses into `meta-analysis`. Arguably the enum is the deficient one, a systematic review without a pooled estimate is not a meta-analysis.

---

## Contents

| path | what it is |
|---|---|
| `data/tier4_findings.parquet` | **THE DATA.** 15,646 rows × 108 columns. Start here. |
| `data/tier4_findings.csv.gz` | Identical content as CSV, for tools without parquet support. |
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
| `code/quote_trace.py` | The quote matcher, refuses to report a rate without its negative control. |
| `code/*` | The extraction pipeline, prompt and driver used for this tier. |
| `code/README.md` | The role of every file in `code/`: including why a Tier-1 package carries `tier3_*` modules. |
| `code/comparator_symmetry_tests.py` | Pins that the quote matcher decodes entities and folds whitespace on BOTH sides. |
| `MANIFEST.json` | File inventory with SHA-256 for every file. |
| `CHECKSUMS.sha256` | `shasum -a 256 -c CHECKSUMS.sha256` to verify the download. |
| `LICENSE` | CC BY 4.0 for the data; the quote column is separately described. |
| `CITATION.cff` | How to cite this package. |
| `scope/*` | Excluded and no-yield PMIDs with reasons. |
| `annotations/*` | ADDITIVE annotation tables keyed to this package's rows/papers, see below. |

## Quickstart

```python
import pandas as pd
df = pd.read_parquet('data/tier4_findings.parquet')

# 1. Findings you can independently verify against source text
verifiable = df                      # all of them, in this package

# 2. Ontology identifiers you can trust, filter on VERIFICATION, never on coverage
grounded = df[df.ontology_id_verification == 'authority_verified']
#  -> 1,614 rows in this package

# 3. Highest-confidence evidence
#    certainty_derived is hedge-detection over BOTH finding_text and the quote;
#    it never overwrites the extractor's own `certainty` judgment.
strong = df[df.evidence_tier.isin(['meta-analysis', 'RCT'])
            & df.certainty_derived.eq('confirmed')]
#  -> 1,598 rows

# 4. Marker frequency, case-fold, or canonicalize with the shipped vocabulary
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
| `annotations/retrofit_fetch_log.parquet` | 10,428 | `pmid` | One row per Tier 1–3 paper attempted in the retrofit: abstract/full-text availability, PMCID, HTTP outcome, fetch date. |
| `annotations/retrofit_summary.json` | — | — | Machine-readable retrofit numbers for all four Tier 1–3 packages, every rate with numerator, denominator and basis. |

### Condition bucket annotations

`annotations/condition_annotations.parquet` covers the 36 papers (240 rows) in this
package labelled `condition == 'MCAS'`: **0 `in_bucket`, 22 `bucket_violation`**
(22 mastocytosis, 0 mast-cell biology without a disorder population,
0 neither), **14 `NEEDS_HUMAN`**. Verdicts are classifier-derived against
`CONDITION_BUCKET_DEFINITIONS.md` v1 under population-studied semantics and none is human-confirmed.
Other buckets are not yet censused. See `annotations/CONDITION_ANNOTATIONS_README.md`.

---

## The other four packages

This is one block of a five-way partition of a single corpus. **Zero papers are shared
between any two packages**: verified by pmid set intersection across all ten pairs at build
time. Per-package counts sum exactly to the corpus totals.

| package | findings | papers | chunks | identifiers | quotes verifiable |
|---|---:|---:|---:|---|---:|
| POTS findings v1.2, package 1 of 5: POTS and dysautonomia core literature (36,067 findings, 3,129 papers) | 36,067 | 3,129 | 76 | model-emitted | 18.12% |
| POTS findings v1.2, package 2 of 5: EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 1 of 2 (36,611 findings, 3,123 papers) | 36,611 | 3,123 | 81 | model-emitted | 21.07% |
| POTS findings v1.2, package 3 of 5: EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 2 of 2 (33,830 findings, 2,589 papers) | 33,830 | 2,589 | 64 | model-emitted | 19.39% |
| POTS findings v1.2, package 4 of 5: long COVID, post-viral and autism intersections (26,032 findings, 1,587 papers) | 26,032 | 1,587 | 35 | authority-derived | 12.22% |
| POTS findings v1.2, package 5 of 5: migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS (15,646 findings, 1,091 papers) ← | 15,646 | 1,091 | 30 | authority-derived | 100.0% |
| **corpus total** | **148,186** | **11,519** | **286** | | **26.75%** |

Pooling any subset is safe for row and paper counts, paper metadata, quote presence, the
harmonized verification columns, and the capability flags. Eleven other metrics are **not**
comparable across all five: `docs/COMPARABILITY.md` lists each with its reason.

Tier 2 Part A and Part B are the two waves of a single extraction pass with one pipeline and
one prompt; pool those two freely.

---

Built 2026-10-22T12:15:40Z from harmonized corpus `f0b86f9a-f688-48c4-a08f-94e946afb9af`.
Data CC BY 4.0. Machine-extracted research information: **not medical advice.**
