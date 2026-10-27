# POTS findings v1.2, package 4 of 5: long COVID, post-viral and autism intersections (26,032 findings, 1,587 papers)

**26,032 findings · 1,587 papers · 35 chunks (221–255) · 2020–2026**

Build stage tier3 of the corpus. Where "tier" appears in file and column names (`data/tier3_findings.parquet`,
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

1. **Identifiers here are authority-derived and score 0.986.**
   The extraction model emitted names only; a resolver looked every identifier up afterwards. This is the property Tiers 1 and 2 lack. All nine invariants pass.
2. **40 rows are flagged `query_contamination`.**
   Six papers were pulled in by the ambiguous abbreviation 'ASD', adult spinal deformity and atrial septal defect, not autism. Filter with `df[~df.query_contamination.fillna(False)]`. The 28 wrong-ASD PMIDs are listed in `scope/tier3_offtopic_pmids.csv`. Note that `query_contamination` means something DIFFERENT in Tier 4, see COMPARABILITY.md.
3. **Shipped-source verifiability is the lowest in the corpus at 12.22%.**
   Tier 3 had the highest full-text retrieval success (69% of papers), and full text was discarded after extraction, so its very success is why so few of its quotes have a shipped source. The v1.1 retrofit re-fetched every paper and re-checked every quote (99.96% now have a checkable source; see the Annotations section and `annotations/quote_retrofit_tier3.parquet`), against Europe PMC's current text rather than a retained archive.
4. **Scientific fidelity is UNMEASURED.**
   Everything verified in `qa/` is well-formedness: quotes trace to source, identifiers carry authority provenance, invariants hold. **Nobody has checked that the extracted science is correctly interpreted.** That needs a human reader, an LLM adjudicator shares the extractor's blind spots. Treat every row as a pointer to a paper you should read, not as a fact.
5. **`condition` is a coarse POPULATION bucket, and the `MCAS` bucket is mostly not MCAS.**
   `condition` means the patient population the paper studied, not a diagnosis, not a mechanism-relevance tag. Its bucket definitions were written down only on 2026-09-16 (`annotations/CONDITION_BUCKET_DEFINITIONS.md`). A stratified census of the 1,083 `MCAS`-labelled papers corpus-wide projects ~69% study mast-cell biology with no mast-cell-disorder population, ~10% MCAS as defined, ~5% mastocytosis (a distinct clonal neoplasm). The shipped column is unchanged; `annotations/condition_annotations.parquet` (pmid-keyed) carries a per-paper verdict, all classifier-derived and `human_confirmed == False`. In this package 18 papers (27 rows) carry `condition == 'MCAS'`: 0 verified `in_bucket`, 2 `bucket_violation`, 16 unassessed.

---

## What is in this package

**Topic:** long COVID autonomic, autism intersection, post-viral syndromes

### Themes

| theme | findings | papers |
|---|---:|---:|
| `long_covid_auto` | 18,904 | 1,147 |
| `autism_intersection` | 4,048 | 270 |
| `post_viral` | 3,039 | 164 |
| `sjogrens` | 15 | 3 |
| `author_augment` | 13 | 1 |
| `migraine_intersection` | 8 | 1 |
| `hypermobility_spectrum` | 5 | 1 |

### Conditions the findings are about

`condition` is a coarse bucket for the **patient population studied**, which is not the same as which
literature the paper came from (`source_literature`). A POTS paper reporting on a fibromyalgia
cohort has `source_literature` of the POTS/dysautonomia literature and `condition == 'fibromyalgia'`.
Bucket definitions: `annotations/CONDITION_BUCKET_DEFINITIONS.md`. Read warning 5 above before
counting anything by `condition`: only the `MCAS` bucket has been censused, and it is mostly not MCAS.

| condition | findings | papers |
|---|---:|---:|
| `long_COVID` | 19,121 | 1,290 |
| `general` | 2,681 | 345 |
| `autism` | 2,286 | 222 |
| `multiple` | 556 | 200 |
| `dysautonomia` | 384 | 123 |
| `ME_CFS` | 293 | 101 |
| `fibromyalgia` | 200 | 41 |
| `EDS_hypermobility` | 144 | 24 |
| _5 more_ | | |

### Evidence quality

| | |
|---|---|
| findings per paper (overall) | 16.4 |
| findings per paper: `abstract-only` | 6.48 (468 papers, 3,033 findings) |
| findings per paper: `blocked` | 6.48 (23 papers, 149 findings) |
| findings per paper: `retrieved-fulltext` | 20.85 (1,096 papers, 22,850 findings) |

**Never compare findings-per-paper across packages without stratifying by
`fulltext_status`.** Yield is driven roughly 3× by whether full text was retrieved, and the
full-text mix differs sharply between packages. An unstratified comparison mostly measures
retrieval success, not extraction productivity.

| evidence tier | findings |
|---|---:|
| `cohort` | 9,005 |
| `cross-sectional` | 5,970 |
| `review/expert-opinion` | 3,392 |
| `case-series` | 2,011 |
| `case-control` | 1,617 |
| `mechanistic/in-vitro` | 1,601 |
| `RCT` | 922 |
| `meta-analysis` | 900 |
| `case-report` | 595 |
| `systematic-review/meta-analysis` | 17 |
| `systematic review` | 2 |

### Quote provenance

Every one of the 26,032 rows carries a `provenance_quote`: the span of source
text the finding was drawn from. Median 184 characters, 90th percentile
305, longest 880.

**3,182 of 26,032 rows (12.22%) are verifiable**: meaning the
quote's own source text still exists and can be re-read.

Abstract-derived rows only; body text was discarded after extraction, so full-text-derived quotes have no surviving source.

The unverifiable remainder is a **retention** failure, not an extraction failure. Where
source text is available, traceability across the corpus measures 94–99% with **0%
wrong-paper false positives in every stratum**. The body text was simply discarded after
extraction. `qa/` carries the census with its negative control.

**v1.1 retrofit:** the source of every paper in this package was re-fetched from Europe PMC and every quote
re-checked: **26,021 of 26,032 rows (99.96%) now have a checkable source**; full-text quotes trace at
98.04% (22,402/22,850), wrong-paper control 0/400.
This checks Europe PMC's *current* text, not the bytes the model read, and the text is not shipped; the figure above
is the shipped-source figure. Row-level results: `annotations/quote_retrofit_*.parquet` (see the Annotations section).

### Ontology grounding

| | |
|---|---|
| rows with a resolved ontology id | 4,113 (15.8% of rows) |
| rows naming an entity at all | 17,828 |
| id coverage among entity-naming rows | 23.1% |
| rows with both an id and an authority label | 4,113 |

**Verification status**: this is the column to filter on, not `ontology_id_source`:

| `ontology_id_verification` | rows |
|---|---:|
| `no_id` | 21,919 |
| `authority_verified` | 4,113 |

| identifier prefix | rows |
|---|---:|
| `None` | 21,919 |
| `CHEBI` | 1,648 |
| `HP` | 902 |
| `UNIPROT` | 759 |
| `NCBITAXON` | 361 |
| `UBERON` | 300 |
| `CL` | 143 |

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

19 rows (0.073%) carry a value outside the pinned enum for
their column. The extraction prompt pinned both vocabularies; the model drifted past the
constraint anyway. **These values are shipped verbatim.** Silently remapping them would
destroy the evidence that the drift happened, and two of them are arguments that the enum is
deficient rather than the output wrong.

| column | value | rows |
|---|---|---:|
| `evidence_tier` | `systematic-review/meta-analysis` | 17 |
| `evidence_tier` | `systematic review` | 2 |

- `systematic-review/meta-analysis` and `systematic review` are the model splitting a distinction the enum collapses into `meta-analysis`. Arguably the enum is the deficient one, a systematic review without a pooled estimate is not a meta-analysis.

---

## Contents

| path | what it is |
|---|---|
| `data/tier3_findings.parquet` | **THE DATA.** 26,032 rows × 108 columns. Start here. |
| `data/tier3_findings.csv.gz` | Identical content as CSV, for tools without parquet support. |
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
| `figures/*` | Per-chunk yield and QA figures. |
| `annotations/*` | ADDITIVE annotation tables keyed to this package's rows/papers, see below. |

## Quickstart

```python
import pandas as pd
df = pd.read_parquet('data/tier3_findings.parquet')

# 1. Findings you can independently verify against source text
verifiable = df[df.fulltext_status.isin(['abstract-only', 'blocked'])]
#  -> 3,182 rows (12.22%)

# 2. Ontology identifiers you can trust, filter on VERIFICATION, never on coverage
grounded = df[df.ontology_id_verification == 'authority_verified']
#  -> 4,113 rows in this package

# 3. Highest-confidence evidence
#    certainty_derived is hedge-detection over BOTH finding_text and the quote;
#    it never overwrites the extractor's own `certainty` judgment.
strong = df[df.evidence_tier.isin(['meta-analysis', 'RCT'])
            & df.certainty_derived.eq('confirmed')]
#  -> 1,595 rows

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
| `annotations/quote_retrofit_tier3.parquet` | 26,032 | `row_idx` = 0-based row of `data/<pkg>_findings.parquet` (+ `pmid`, `quote_sha1` as checks) | Per-row quote traceability against source text re-fetched from Europe PMC on 2026-09-16, with source depth, fetch status and the wrong-paper control. Null `retrofit_traceable` means no source exists today. |
| `annotations/retrofit_fetch_log.parquet` | 10,428 | `pmid` | One row per Tier 1–3 paper attempted in the retrofit: abstract/full-text availability, PMCID, HTTP outcome, fetch date. |
| `annotations/retrofit_summary.json` | — | — | Machine-readable retrofit numbers for all four Tier 1–3 packages, every rate with numerator, denominator and basis. |
| `annotations/paper_flags.csv` | 60 | pmid, flag | Retracted, corrected, preprint and duplicate records, one row per (record, flag), with the recommended use. See the Paper flags section. |
| `annotations/paper_flags.parquet` | 60 | pmid, flag | Parquet twin of paper_flags.csv (same content). |

### Quote source retrofit (2026-09-16)

The body text this tier was extracted from was discarded after extraction, so the `quotes verifiable`
figure above (12.22%) is what the shipped data alone supports. On 2026-09-16 the
source text of every paper was re-fetched from Europe PMC at the pinned pacing and every quote re-checked
with the shipped comparator (`code/quote_trace.py`, `code/retrofit_census.py`). The fetched text is
**not** shipped (see LICENSE); the row-level result is `annotations/quote_retrofit_tier3.parquet`.

| | rows | of | rate | basis |
|---|---:|---:|---:|---|
| verifiable before | 3,182 | 26,032 | 12.22% | shipped data: abstract-derived rows only |
| verifiable after | 26,021 | 26,032 | 99.96% | rows whose own re-fetched source exists |
| traceable, full-text rows vs re-fetched full text | 22,402 | 22,850 | 98.04% | control 0/400 wrong-paper false positives |
| traceable, abstract-stratum rows vs re-fetched abstract | 3,039 | 3,171 | 95.84% | control 0/400 |
| traceable, all verifiable rows | 25,441 | 26,021 | 97.77% | **stratify on `retrofit_source_depth × fulltext_status` before quoting** |

11 rows have no source in Europe PMC today (neither abstract nor body) and stay unverifiable. Europe PMC's *current* text was used, so a
paper revised since extraction registers as untraceable. Traceability is well-formedness, not correctness:
a traceable quote can still support a misread finding.

### Condition bucket annotations

`annotations/condition_annotations.parquet` covers the 18 papers (27 rows) in this
package labelled `condition == 'MCAS'`: **0 `in_bucket`, 2 `bucket_violation`**
(0 mastocytosis, 0 mast-cell biology without a disorder population,
2 neither), **16 `NEEDS_HUMAN`**. Verdicts are classifier-derived against
`CONDITION_BUCKET_DEFINITIONS.md` v1 under population-studied semantics and none is human-confirmed.
Other buckets are not yet censused. See `annotations/CONDITION_ANNOTATIONS_README.md`.

### Paper flags (checked 2026-10-26)

`annotations/paper_flags.csv` (and `.parquet`, same content) marks every PubMed record in this package that a reader
must be able to see and filter: 60 rows over 58 of the package's 1,587 records, one row per
(record, flag). Flags come from PubMed publication types and linked notices and from Crossref update notices
(Retraction Watch data), both read on 2026-10-26, plus a recorded adjudication of every title-match pair
(`qa/paper_flags_adjudication.json`). Flagged rows are flagged, never removed.

| flag | papers | findings | recommended use |
|---|---:|---:|---|
| `retracted` | 2 | 46 | exclude |
| `has_correction` | 31 | 485 | note |
| `preprint_with_published_version` | 4 | 49 | count_once |
| `published_version_of_preprint` | 7 | 186 | note |
| `preprint` | 11 | 304 | note |
| `same_work_other_record` | 4 | 55 | note on the canonical record, count_once on the duplicate |
| `update_of` | 1 | 3 | note |

How to use it: exclude `retracted` records and `erratum_notice` records (a correction notice whose text was
extracted as if it were a study); count each duplicate group once, on its `canonical_pmid` (the peer-reviewed
version over a preprint, the original over a reprint or notice); read the linked notice before quoting a number
from a `has_correction` or `expression_of_concern` record. `recommended_use` carries that rule per row.

The package's paper count (1,587) is a count of PubMed records. Derived from the flags, it holds
**1,582 distinct works**: records minus correction notices minus duplicate records (`recommended_use == count_once`).
Retracted papers remain works and remain in the data; exclude them yourself with the flag.

```python
flags = pd.read_csv('annotations/paper_flags.csv', dtype=str)
drop = set(flags.loc[flags.recommended_use.isin(['exclude', 'count_once']), 'pmid'])
clean = df[~df.pmid.astype(str).isin(drop)]        # retracted and notice rows out, each work counted once
```

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
| POTS findings v1.2, package 4 of 5: long COVID, post-viral and autism intersections (26,032 findings, 1,587 papers) ← | 26,032 | 1,587 | 35 | authority-derived | 12.22% |
| POTS findings v1.2, package 5 of 5: migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS (15,646 findings, 1,091 papers) | 15,646 | 1,091 | 30 | authority-derived | 100.0% |
| **corpus total** | **148,186** | **11,519** | **286** | | **26.75%** |

Pooling any subset is safe for row and paper counts, paper metadata, quote presence, the
harmonized verification columns, and the capability flags. Eleven other metrics are **not**
comparable across all five: `docs/COMPARABILITY.md` lists each with its reason.

Tier 2 Part A and Part B are the two waves of a single extraction pass with one pipeline and
one prompt; pool those two freely.

---

Built 2026-10-22T12:15:40Z from harmonized corpus `f0b86f9a-f688-48c4-a08f-94e946afb9af`.
Data CC BY 4.0. Machine-extracted research information: **not medical advice.**
