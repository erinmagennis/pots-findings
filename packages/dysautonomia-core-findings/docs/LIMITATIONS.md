# Limitations: POTS findings v1.2, package 1 of 5: POTS and dysautonomia core literature (36,067 findings, 3,129 papers)

Ordered by how much they should change what you conclude. Nothing here is hedging: each item
is a measured property with its measurement.

## 1. Scientific fidelity is unmeasured

**This is the largest limitation and it applies to every package.**

Everything in `qa/` verifies well-formedness, a quote is real text from the right paper, an
identifier carries authority provenance, counts are conserved, enum drift is flagged. **No
check asks whether a finding correctly interprets its source.**

A finding can be perfectly well-formed and still misread the paper: reverse a direction,
attribute a control-group result to the case group, or state a correlation as causal where
the source hedged. Nothing here would catch that.

Measuring it needs a human domain reader. An LLM adjudicator shares the extractor's blind
spots and cannot substitute. A 200-row worksheet with pre-registered thresholds is drawn and
unscored.

**Practical consequence: treat every row as a pointer to a paper you should read, not as a
fact you can cite.** The `provenance_quote` and `pmid` columns exist to make that cheap.

## 2. Ontology identifiers were model-emitted; in v1.2 they are re-grounded, and a share is withheld

**v1.2 (2026-10-21): every model-emitted identifier in this package was looked up by id at its minting
authority (HGNC via MyGene, ChEBI via OLS4, MeSH via NLM) and its label and full synonym list compared with the
entity name; names were also resolved forward to obtain the correct id where one exists. No model was involved.**

Of the 4,373 rows that carried a model-emitted id in v1.1: **2,385 denoted their entity** and are now tagged
`authority_verified_retrospective` with the match mode recorded (compound_partial 110, exact 1,255, exact_relaxed 398, synonym 622); **1,161 ids were replaced** by the id the
entity name resolves to (exact label or authority synonym; `ontology_id_source` says so); **827 were withheld** (`id_withheld_unverified_v1.2`:
the id denoted a different entity and the name did not resolve). The original model id is preserved on every affected row in
`ontology_id_v11_model_emitted`; on replaced rows `entity_ontology_label` / `ontology_label_final` carry the NEW id's label, fetched by id from the authority. Nothing else changed: no row was added or removed and no other column was edited.

Measured on this package's full population: **54.5% of the model-emitted ids denoted their entity**; the
rest existed but pointed at a neighbouring gene, a related compound or a sibling concept, near-miss assignment, not fabrication.
The v1.1 figure quoted below was an adjudicated SAMPLE and is kept for the record. Full method and corpus-wide numbers: `annotations/POTS_MODEL_ID_BENCHMARK.md`.

What remains limited: (a) `compound_partial` matches mean the entity string named several entities and the id denotes one of
them, read the `entity` string; (b) `exact_relaxed` tolerates case, plural, Greek letters and punctuation, never string similarity;
(c) the 827 withheld rows have an entity NAME but no identifier, resolve the name yourself if you need one;
(d) correctness was established by label correspondence at the authority, which is the same standard Tiers 3-4 used, but it was
applied retrospectively to ids the model chose, so coverage here is still the model's coverage, not the resolver's.

For the record, v1.1 reported `id_denotes_entity_rate` = **0.578** from an adjudicated sample; the full-population
figure in v1.2 is 54.5% once authority synonyms and spelling variants are credited.

**Practical consequence: join on `entity_ontology_id_resolved` only where `ontology_id_verification` is
`authority_verified` or `authority_verified_retrospective`.** Never use `ontology_id_v11_model_emitted` for joins; it is history.

## 3. Most quotes cannot be re-checked

**29,531 of 36,067 rows (81.88%) have a quote whose source text no
longer exists.** The body text was discarded after extraction, so a finding drawn from a
paper's Results section has a quote nobody can verify without re-fetching the paper.

**This is a retention failure, not an extraction failure.** Where source text survives,
traceability is 94–99% with 0% wrong-paper false positives in every stratum. The extraction
was sound; the evidence was thrown away.

**The v1.1 retrofit recovered most of it, with a weaker guarantee.** Every paper's source was re-fetched from
Europe PMC and every quote re-checked: 35,949 of 36,067 rows (99.67%) now have a checkable source,
full-text quotes trace at 97.43%, wrong-paper control 0/400. Weaker because it checks
Europe PMC's text *today*, not the bytes the model read, and because the fetched text is not shipped (LICENSE).
so it is not reproducible offline the way Tier 4's retained archive is. `annotations/quote_retrofit_*.parquet`

## 4. Yield depends on full-text availability, not on the literature

Findings per paper by stratum in this package:

| stratum | papers | findings | per paper |
|---|---:|---:|---:|
| `abstract-only` | 1,207 | 6,522 | 5.4 |
| `blocked` | 5 | 14 | 2.8 |
| `retrieved-fulltext` | 1,917 | 29,531 | 15.4 |

The full-text stratum yields roughly 3× the abstract-only stratum. **An unstratified
comparison of yield between packages mostly measures Europe PMC retrieval success.**

A related consequence that is easy to miss: **absence of a finding is not evidence of
absence.** A marker may be missing because no paper reported it, because the paper was
abstract-only, or because retrieval failed. These are indistinguishable in the data.

## 5. Entity coverage, and what a null entity means

18,915 of 36,067 rows (52.4%) name an entity. The remainder name
**none by design**: symptom-burden, phenotype, quality-of-life and study-characteristic
findings have no marker to name.

**Practical consequence: an entity-keyed view covers roughly half these findings, and that is
correct behavior, not missing data.** Never present an entity-keyed count as a total.

Entity strings are **not canonicalized in-row** for Tiers 1-2. Case variants
(`Interleukin-6` / `interleukin-6`) are distinct strings. Join
`data/entity_vocabulary_crosstier.parquet`, or case-fold at query time, but **never
lowercase to merge**, which would collapse human and mouse gene symbols (`MECP2`/`Mecp2`).

## 6. Enum drift

4 rows (0.0111%) carry a value outside the pinned enum. **Shipped
verbatim, never coerced.** Two of the drifted values are arguments that the enum is
deficient rather than the output wrong: `other patient group` (findings about another
disease used as a mechanistic analogy, which the enum has no slot for) and `IBD_gut`
(probably an `IBS_gut` typo, but IBD and IBS are different diseases so correcting it would
change what the row claims). Both are formally unadjudicated.

The `condition` column carries three values that appear in the shipped data but have no written
definition in `annotations/CONDITION_BUCKET_DEFINITIONS.md`: `IBD_gut`, `orthostatic_hypotension` and
`other patient group`: 4 papers corpus-wide, of which 1 in this package (`orthostatic_hypotension` 1).
They are extraction-time enum drift, not buckets. Read them as `general` for population counts; they are not
repaired in the data.

## 7. Cross-package traps

Three columns will mislead you if you pool packages naively. Full detail in
`docs/COMPARABILITY.md`; the short form:

- **`id_resolved_frac` ranks the packages backwards.** It measures coverage, not correctness.
- **`ontology_id_source == 'unresolved_nulled'`** means identifier KEPT in Tier 2 and
  identifier NULLED in Tiers 3-4. The obvious filter drops 2,242 Tier-2 rows that do carry
  identifiers.
- **`query_contamination`** means abbreviation collision in Tier 3 (40 rows) and screening
  uncertainty in Tier 4 (1,960 rows). Two concepts, one name.

Eleven metrics are not comparable across all five packages. Five aggregates are safe.

## 8. Corpus construction

The corpus was assembled by keyword query, so it inherits every bias of the queries: it is
**English-language, PubMed/Europe-PMC-indexed, and weighted toward the conditions that were
searched for**. Conditions appear in packages other than their own only as incidental
mentions, a count of `condition == 'fibromyalgia'` in the Tier 1 package means
*POTS/dysautonomia papers that mention fibromyalgia*, not the fibromyalgia literature.

Publication bias is inherited wholesale and unmeasured. Null results are retained where the
source reported them (`null_or_failed_result`), which partially offsets this, but only
partially, since unpublished nulls are absent by construction.

## 9. All adjudicated error rates are LLM-judged

The identifier-denotation rates, the HPO fuzzy-match verdicts, and the quote-residual
classifications were adjudicated by a model, not a human. Each has a negative control
establishing that the instrument discriminates, and controls are reported alongside every
rate, but a control proves the instrument is not random, not that it is right.

## 10. The `condition` bucket is a population label, and one bucket is mostly mislabelled

`condition` is a coarse enum for the population studied. Its inclusion rules were written down only on
2026-09-16 (`annotations/CONDITION_BUCKET_DEFINITIONS.md` v1), after extraction. A stratified census of
the `MCAS` bucket found ~69% of its papers study mast-cell biology with no MCAS population and ~5% study
mastocytosis, a different disease. The shipped column is not edited; `annotations/condition_annotations.parquet`
records a per-paper verdict against the definitions. In this package: 9 papers `in_bucket`,
4 `bucket_violation`, 77 `NEEDS_HUMAN`: all classifier-derived and unconfirmed. The
other buckets have not been censused and may carry the same defect at an unknown rate. Eight of the
thirteen bucket definitions are provisional.

## 11. Quotes are verbatim to model input, not to the rendered paper

2 quotes in this package carry raw HTML entity codes (`&#x202f;`, `&#xa0;`, …) because the pipeline
did not decode Europe PMC text before extraction. They match their source under the shipped comparator,
which normalizes both sides symmetrically (`code/comparator_symmetry_tests.py`, 8 cases); a naive substring
check against a clean copy of the paper will miss them. This is a presentation defect, not a fabrication,
and it is not repaired in place.

## 12. Verifiability was retrofitted, not retained

Section 3 above describes the shipped data: 18.12% of rows verifiable. The 2026-09-16 retrofit
re-fetched source text and lifted that to 99.67% (`annotations/quote_retrofit_tier1.parquet`,
README §Annotations). The retrofit checked quotes against Europe PMC's *current* text, not the text the model
read; the retained-archive guarantee Tier 4 has is not reproducible here. Stratify on `retrofit_source_depth`
before quoting any traceability rate from it.

## 13. Retracted, corrected and duplicate records are kept and flagged

`annotations/paper_flags.csv` marks 1 retracted paper (14 findings),
0 with an expression of concern, 2 correction notices whose text was extracted as a paper,
49 papers with a published correction, 14 preprints and
12 records that duplicate another record in the dataset. None of these rows was removed:
the data is frozen and the flags are additive. Any count that does not first apply `recommended_use` includes retracted
findings and double-counts duplicated works. The flags reflect PubMed and Crossref as read on 2026-10-26; a paper retracted
after that date is not flagged. The title-match decisions (accepted and rejected, with reasons) are in
`qa/paper_flags_adjudication.json`; the v1.0 `data/pmid_dedup_map.parquet` is superseded by this file.

## What would most improve this package

1. **Re-ground the identifiers** through the resolver Tiers 3-4 used. This is the single
   largest correctness gap and the machinery already exists.
2. **Score the fidelity worksheet** with a human reader, the only way to learn whether the
   extracted science is right. The AI-scorer calibration (Q7/Q8 machine-extendable, Q3/Q10 human) cuts it to ~2–4 h.
3. **Human-confirm the `condition` annotations**: start with the 66 papers whose title contains "mastocytos",
   then census the remaining buckets against the written definitions.
4. **Re-fetch and RETAIN the source text** so the retrofit's verifiability holds against a frozen archive, as in Tier 4.

