# Limitations — Tier 4 — migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS

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

## 2. Identifier coverage is low, even though correctness is high

Identifiers here are authority-derived and score 0.998 on
`id_denotes_entity_rate`. But only 1,614 rows
(10.3%) carry one at all.

The resolver leaves a name unmatched rather than guessing, and fuzzy matches were
adjudicated rather than accepted (59% of fuzzy OLS4 HPO matches were wrong). **Low coverage
is the price of the high correctness, and it was the right trade** — but it means an
identifier-keyed analysis covers a minority of rows.

**Practical consequence: identifier-keyed views cover a fraction of the findings. Never
present an identifier-keyed count as a total.** Keyword search on `entity` reaches the rest.

## 3. Verifiability is complete here but not corpus-wide

Every row in this package is verifiable — body text was retained. **But corpus-wide
verifiability is 26.75%**, because Tiers 1-3 discarded theirs. If you pool this package
with its siblings, the pooled verifiability is not 100%.

## 4. Yield depends on full-text availability, not on the literature

Findings per paper by stratum in this package:

| stratum | papers | findings | per paper |
|---|---:|---:|---:|
| `abstract-only` | 505 | 3,347 | 6.63 |
| `blocked` | 3 | 20 | 6.67 |
| `retrieved-fulltext` | 583 | 12,279 | 21.06 |

The full-text stratum yields roughly 3× the abstract-only stratum. **An unstratified
comparison of yield between packages mostly measures Europe PMC retrieval success.**

A related consequence that is easy to miss: **absence of a finding is not evidence of
absence.** A marker may be missing because no paper reported it, because the paper was
abstract-only, or because retrieval failed. These are indistinguishable in the data.

## 5. Entity coverage, and what a null entity means

11,259 of 15,646 rows (72.0%) name an entity. The remainder name
**none by design** — symptom-burden, phenotype, quality-of-life and study-characteristic
findings have no marker to name.

**Practical consequence: an entity-keyed view covers roughly half these findings, and that is
correct behavior, not missing data.** Never present an entity-keyed count as a total.

Entity strings are **not canonicalized in-row** for Tiers 1-2. Case variants
(`Interleukin-6` / `interleukin-6`) are distinct strings. Join
`data/entity_vocabulary_crosstier.parquet`, or case-fold at query time — but **never
lowercase to merge**, which would collapse human and mouse gene symbols (`MECP2`/`Mecp2`).

## 6. Enum drift

8 rows (0.0511%) carry a value outside the pinned enum. **Shipped
verbatim, never coerced.** Two of the drifted values are arguments that the enum is
deficient rather than the output wrong — `other patient group` (findings about another
disease used as a mechanistic analogy, which the enum has no slot for) and `IBD_gut`
(probably an `IBS_gut` typo, but IBD and IBS are different diseases so correcting it would
change what the row claims). Both are formally unadjudicated.

The `condition` column carries three values that appear in the shipped data but have no written
definition in `annotations/CONDITION_BUCKET_DEFINITIONS.md`: `IBD_gut`, `orthostatic_hypotension` and
`other patient group` — 4 papers corpus-wide, none in this package.
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
records a per-paper verdict against the definitions. In this package: 0 papers `in_bucket`,
22 `bucket_violation`, 14 `NEEDS_HUMAN` — all classifier-derived and unconfirmed. The
other buckets have not been censused and may carry the same defect at an unknown rate. Eight of the
thirteen bucket definitions are provisional.

## 11. Quotes are verbatim to model input, not to the rendered paper

42 quotes in this package carry raw HTML entity codes (`&#x202f;`, `&#xa0;`, …) because the pipeline
did not decode Europe PMC text before extraction. They match their source under the shipped comparator,
which normalizes both sides symmetrically (`code/comparator_symmetry_tests.py`, 8 cases); a naive substring
check against a clean copy of the paper will miss them. This is a presentation defect, not a fabrication,
and it is not repaired in place.

## What would most improve this package

1. **Score the fidelity worksheet** with a human reader — the only way to learn whether the
   extracted science is right. The AI-scorer calibration (Q7/Q8 machine-extendable, Q3/Q10 human) cuts it to ~2–4 h.
2. **Human-confirm the `condition` annotations** — start with the 66 papers whose title contains "mastocytos",
   then census the remaining buckets against the written definitions.
3. **Extend identifier coverage** — 10.3% is the corpus low, though what is there is right.
4. **Adjudicate the 2,257 `screen_verdict_uncertain` rows** with a human reader (v1 docs said 1,960; the data says 2,257).

