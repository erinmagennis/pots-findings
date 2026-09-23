# Limitations — Tier 2 Part B — comorbid-condition literatures, second extraction wave

Ordered by how much they should change what you conclude. Nothing here is hedging: each item
is a measured property with its measurement.

## 1. Scientific fidelity is unmeasured

**This is the largest limitation and it applies to every package.**

Everything in `qa/` verifies well-formedness — a quote is real text from the right paper, an
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

## 2. Ontology identifiers are model-emitted and largely wrong

`id_denotes_entity_rate` = **0.708** — roughly **29% of identifiers do not denote the entity on
their own row.** That is a lower bound; the adjudicator over-calls DIFFERENT by ~17%.

**This rate is INHERITED from Tier 2 as a whole, not measured on this wave.** It comes from a
270-row adjudicated sample drawn across both waves pooled (12,289 rows with an id and an
authority label). No per-wave rate was ever measured, so the true value for this package
alone is unknown.

The pre-adjudication signal that *can* be computed per wave suggests they are close. Exact
string agreement between `entity` and the authority's own `entity_ontology_label`, under one
consistent normalizer: **Part A 40.25%** (6,716 rows) versus **Part B 41.58%** (5,573 rows) — 1.33 points apart.
That is a weaker measure than the adjudicated rate (it counts synonyms as disagreements, so
the absolute numbers are not comparable to 0.708), but it is computed identically for both
waves and gives no reason to expect them to differ materially.

Coverage, by contrast, IS measured on this package's own slice and does differ between the
waves: Part A 18.3%, Part B 16.5%.

5,573 rows carry an identifier, all tagged
`unverified_model_emitted`. The comparison that matters:

| package | id coverage | id correctness |
|---|---:|---:|
| Tier 1 | 12.1% | 0.578 |
| Tier 2 (A+B pooled) | 17.5% | 0.708 |
| Tier 3 | 15.8% | **0.986** |
| Tier 4 | 10.3% | **0.998** |

Coverage and correctness rank the packages in *opposite* orders. The high-coverage packages
are the low-correctness ones.

**Practical consequence: do not use this package's identifiers as an entity mapping.** Use
the `entity` string with the shipped vocabulary, or resolve names yourself against OLS4 /
UniProt — `code/multi_authority_resolver.py` is the resolver Tiers 3-4 used.

This is the largest correctness gap in the corpus and it is fixable: re-grounding Tiers 1-2
through the hardened resolver is the second-highest-value outstanding action.

## 3. Most quotes cannot be re-checked

**27,270 of 33,830 rows (80.61%) have a quote whose source text no
longer exists.** The body text was discarded after extraction, so a finding drawn from a
paper's Results section has a quote nobody can verify without re-fetching the paper.

**This is a retention failure, not an extraction failure.** Where source text survives,
traceability is 94–99% with 0% wrong-paper false positives in every stratum. The extraction
was sound; the evidence was thrown away.

**The v1.1 retrofit recovered most of it, with a weaker guarantee.** Every paper's source was re-fetched from
Europe PMC and every quote re-checked: 33,778 of 33,830 rows (99.85%) now have a checkable source,
full-text quotes trace at 98.12%, wrong-paper control 0/400. Weaker because it checks
Europe PMC's text *today*, not the bytes the model read, and because the fetched text is not shipped (LICENSE) —
so it is not reproducible offline the way Tier 4's retained archive is. `annotations/quote_retrofit_*.parquet`

## 4. Yield depends on full-text availability, not on the literature

Findings per paper by stratum in this package:

| stratum | papers | findings | per paper |
|---|---:|---:|---:|
| `abstract-only` | 1,052 | 6,253 | 5.94 |
| `blocked` | 56 | 307 | 5.48 |
| `retrieved-fulltext` | 1,481 | 27,270 | 18.41 |

The full-text stratum yields roughly 3× the abstract-only stratum. **An unstratified
comparison of yield between packages mostly measures Europe PMC retrieval success.**

A related consequence that is easy to miss: **absence of a finding is not evidence of
absence.** A marker may be missing because no paper reported it, because the paper was
abstract-only, or because retrieval failed. These are indistinguishable in the data.

## 5. Entity coverage, and what a null entity means

20,115 of 33,830 rows (59.5%) name an entity. The remainder name
**none by design** — symptom-burden, phenotype, quality-of-life and study-characteristic
findings have no marker to name.

**Practical consequence: an entity-keyed view covers roughly half these findings, and that is
correct behavior, not missing data.** Never present an entity-keyed count as a total.

Entity strings are **not canonicalized in-row** for Tiers 1-2. Case variants
(`Interleukin-6` / `interleukin-6`) are distinct strings. Join
`data/entity_vocabulary_crosstier.parquet`, or case-fold at query time — but **never
lowercase to merge**, which would collapse human and mouse gene symbols (`MECP2`/`Mecp2`).

## 6. Enum drift

16 rows (0.0473%) carry a value outside the pinned enum. **Shipped
verbatim, never coerced.** Two of the drifted values are arguments that the enum is
deficient rather than the output wrong — `other patient group` (findings about another
disease used as a mechanistic analogy, which the enum has no slot for) and `IBD_gut`
(probably an `IBS_gut` typo, but IBD and IBS are different diseases so correcting it would
change what the row claims). Both are formally unadjudicated.

The `condition` column carries three values that appear in the shipped data but have no written
definition in `annotations/CONDITION_BUCKET_DEFINITIONS.md`: `IBD_gut`, `orthostatic_hypotension` and
`other patient group` — 4 papers corpus-wide, of which 1 in this package (`other patient group` 1).
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
mentions — a count of `condition == 'fibromyalgia'` in the Tier 1 package means
*POTS/dysautonomia papers that mention fibromyalgia*, not the fibromyalgia literature.

Publication bias is inherited wholesale and unmeasured. Null results are retained where the
source reported them (`null_or_failed_result`), which partially offsets this — but only
partially, since unpublished nulls are absent by construction.

## 9. All adjudicated error rates are LLM-judged

The identifier-denotation rates, the HPO fuzzy-match verdicts, and the quote-residual
classifications were adjudicated by a model, not a human. Each has a negative control
establishing that the instrument discriminates, and controls are reported alongside every
rate — but a control proves the instrument is not random, not that it is right.

## 10. The `condition` bucket is a population label, and one bucket is mostly mislabelled

`condition` is a coarse enum for the population studied. Its inclusion rules were written down only on
2026-09-16 (`annotations/CONDITION_BUCKET_DEFINITIONS.md` v1), after extraction. A stratified census of
the `MCAS` bucket found ~69% of its papers study mast-cell biology with no MCAS population and ~5% study
mastocytosis, a different disease. The shipped column is not edited; `annotations/condition_annotations.parquet`
records a per-paper verdict against the definitions. In this package: 7 papers `in_bucket`,
57 `bucket_violation`, 379 `NEEDS_HUMAN` — all classifier-derived and unconfirmed. The
other buckets have not been censused and may carry the same defect at an unknown rate. Eight of the
thirteen bucket definitions are provisional.

## 11. Quotes are verbatim to model input, not to the rendered paper

48 quotes in this package carry raw HTML entity codes (`&#x202f;`, `&#xa0;`, …) because the pipeline
did not decode Europe PMC text before extraction. They match their source under the shipped comparator,
which normalizes both sides symmetrically (`code/comparator_symmetry_tests.py`, 8 cases); a naive substring
check against a clean copy of the paper will miss them. This is a presentation defect, not a fabrication,
and it is not repaired in place.

## 12. Verifiability was retrofitted, not retained

Section 3 above describes the shipped data: 19.39% of rows verifiable. The 2026-09-16 retrofit
re-fetched source text and lifted that to 99.85% (`annotations/quote_retrofit_tier2b.parquet`,
README §Annotations). The retrofit checked quotes against Europe PMC's *current* text, not the text the model
read; the retained-archive guarantee Tier 4 has is not reproducible here. Stratify on `retrofit_source_depth`
before quoting any traceability rate from it.

## What would most improve this package

1. **Re-ground the identifiers** through the resolver Tiers 3-4 used. This is the single
   largest correctness gap and the machinery already exists.
2. **Score the fidelity worksheet** with a human reader — the only way to learn whether the
   extracted science is right. The AI-scorer calibration (Q7/Q8 machine-extendable, Q3/Q10 human) cuts it to ~2–4 h.
3. **Human-confirm the `condition` annotations** — start with the 66 papers whose title contains "mastocytos",
   then census the remaining buckets against the written definitions.
4. **Re-fetch and RETAIN the source text** so the retrofit's verifiability holds against a frozen archive, as in Tier 4.

