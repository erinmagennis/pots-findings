# Comparability, what you may pool, and what will mislead you

This corpus was extracted in five passes over four years of literature, with the pipeline
improving between passes. That makes some columns comparable across packages and some
**actively misleading** when pooled. This document is the difference between the two.

If you only read one section, read [The three traps](#the-three-traps).

---

## The three traps

### Trap 1, the metric that looks like grounding quality ranks the packages BACKWARDS

`id_resolved_frac` (the share of rows carrying a non-null ontology id) is a **coverage**
metric. It answers "is a string present?" It does not answer "is the string right?"

| package | `id_resolved_frac` (all rows) | `id_denotes_entity_rate` |
|---|---:|---:|
| Tier 1 | 0.121 | **0.578** |
| Tier 2 (A+B pooled) | 0.175 | **0.708** |
| Tier 3 | 0.158 | **0.986** |
| Tier 4 | 0.103 | **0.998** |

**`id_denotes_entity_rate` is a TIER-level measurement, not a package-level one.** It comes
from adjudicated samples (t1 n=276, t2 n=270, t3 n=199, t4 n=56) drawn per tier. Tier 2's
sample spans both waves pooled, so **Tier 2 Part A and Part B both carry 0.708 by inheritance
and neither has a rate of its own.** Coverage is genuinely per-package (Part A 18.3%, Part B
16.5%); correctness is not. Where a table in this corpus shows both side by side for a Tier-2
part, the coverage figure is measured and the correctness figure is inherited.

The pre-adjudication signal that can be computed per wave puts them close: exact string
agreement between `entity` and the authority label, under one consistent normalizer, is 40.25%
for Part A (6,716 rows) and 41.58% for Part B (5,573 rows): 1.33 points apart. That measure
counts synonyms as disagreements so its absolute level is not comparable to 0.708, but it is
computed identically for both waves and gives no reason to expect them to diverge.

Coverage ranks **Tier 2 best and Tier 4 worst**. Correctness ranks them in almost the
opposite order. Tier 4 carries the fewest identifiers and nearly all of them are right;
Tier 2 carries the most and roughly 29% of them do not denote the entity on their own row.

**Why:** Tier 1/2 identifiers are **model-emitted**: the extraction model wrote them, and they
were checked only for *existence* in the authority, never for *denotation*. Tier 3/4
identifiers are **authority-derived**: the model emitted a name only, and a resolver looked the
identifier up afterwards.

Proof this is a real distinction and not a metric artifact: **zero rows in Tiers 1 or 2 carry a
resolved id without a model-emitted id.** No Tier 1/2 identifier was ever independently derived
from an entity name. The `ids_repaired` step applied to those tiers was **syntactic**: case
normalization and namespace fixes touching 4.8% of rows, and re-derived nothing from names.

**Rule: never pool `id_resolved_frac` across packages. Always stratify by
`ontology_id_verification`.**

Stated caveat, so you can calibrate: the adjudicator that measured `id_denotes_entity_rate`
over-calls DIFFERENT by roughly 17%, so the Tier 1/2 rates are **lower bounds**. The direction
is unaffected, a shuffled-pair negative control scored 0.003–0.010 against 0.42–0.89 observed,
a 40–90× separation.

### Trap 2: 73% of the corpus can never be checked against its source

Only Tier 4 retained body text after extraction. Everywhere else, the full text was discarded
once findings were extracted, so a finding drawn from a paper's Results section has a quote
that cannot be re-checked against anything.

| package | rows | verifiable (abstract-derived) | share | census-checked | census share |
|---|---:|---:|---:|---:|---:|
| Tier 1 | 36,067 | 6,536 | 18.12% | 6,488 | 17.99% |
| Tier 2 Part A | 36,611 | 7,713 | 21.07% | — | — |
| Tier 2 Part B | 33,830 | 6,560 | 19.39% | — | — |
| Tier 3 | 26,032 | 3,182 | 12.22% | 3,177 | 12.2% |
| Tier 4 | 15,646 | 15,646 | **100.0%** | 15,646 | **100.0%** |

Summing the recomputed column: **39,637 of 148,186 rows (26.75%) are verifiable; 108,549 are
not.** The shipped census reported 26.64% corpus-wide on its own narrower basis, which excludes
rows whose paper is absent from the draw corpus. The two bases differ by 165 rows, use 26.75%
when your denominator is the shipped data, since that is what `code/verify_package.py`
re-derives.

Two denominators appear above and they differ by a handful of rows. **Verifiable
(abstract-derived)** counts every row whose quote came from an abstract, recomputed from the
shipped data by `code/verify_package.py`. **Census-checked** is the subset the shipped quote
census actually re-read, which excludes rows whose paper is absent from the draw corpus (48
rows in Tier 1, 5 in Tier 3). The Tier 2 census was reported over both waves pooled: 14,161
verifiable rows at 20.1%, covering Parts A and B together, and is not split by wave, so the
per-part census columns are blank. Cite the recomputed column for a single Part.

Both bases are internally consistent: the census figures sum to 39,472 (26.64%), the recomputed
figures to 39,637 (26.75%). They differ only in whether rows with no reachable source text are
counted in the numerator.

**Traceability, measured where source text survives**: this is the extraction-quality number,
and it is high everywhere:

| package | checked | traceable | wrong-paper control |
|---|---:|---:|---:|
| Tier 1 | 6,488 | 94.57% | 0.0% |
| Tier 2 (A+B pooled) | 14,161 | 94.24% | 0.0% |
| Tier 3 | 3,177 | 96.79% | 0.0% |
| Tier 4 | 15,646 | **99.09%** | 0.0% |

**This is a retention failure, not an extraction-quality failure.** Where source text *is*
available, traceability is high and consistent across every package: 94.57% / 94.24% / 96.79%
/ 99.09%, with **0% wrong-paper false positives in every stratum**. The extraction was sound;
the evidence was thrown away.

**Rule: `provenance_quote` non-null does not mean verifiable.** A quote is verifiable only when
its own source text still exists. Filter on `cap_quote_source_retained`, and read
`fulltext_status`: rows with `retrieved-fulltext` in Tiers 1–3 have quotes whose source is
gone.

The v1.1 retrofit re-fetched every Tier 1–3 paper from Europe PMC and re-checked every quote:
132,295 of 132,540 rows now have a checkable source (99.8%), full-text quotes trace at 97.9%, 0/400
wrong-paper false positives in every stratum (`annotations/quote_retrofit_<pkg>.parquet`,
`annotations/RETROFIT_REPORT.md`). **Do not pool this with Tier 4's figure**: Tier 4 traces against a
retained, shipped archive of the bytes the model read; the retrofit traces against Europe PMC's current
text, which is not shipped. `cap_quote_source_retained` is still the only column that means "the source
is in this package".

### Trap 3, the same column name means opposite things in different packages

`ontology_id_source == 'unresolved_nulled'` means:

- **Tier 2: identifier KEPT.** All 2,242 such rows carry a non-null identifier.
- **Tiers 3 and 4: identifier NULLED.** Zero such rows carry an identifier.

So the obvious filter for resolved identifiers.
`df[df.ontology_id_source != 'unresolved_nulled']`: silently drops **2,242 Tier-2 rows that do
carry identifiers**.

The value vocabularies are near-disjoint: 19 distinct values across the union, exactly **1**
shared by all three packages that hold the column. Tier 2 uses opaque `authority_lookup_B/C/D`
tags that record neither the ontology nor the match mode; Tiers 3/4 encode both.

**Rule: use `ontology_id_verification` and `ontology_id_match_mode`, which were added by the
harmonization step with consistent semantics across all five packages. `ontology_id_source` is
kept verbatim and uncoerced, it is provenance, not a filter.**

---

## Safe four-package aggregates

These five things may be pooled across all packages without qualification:

1. **Row and paper counts.** The partition is verified: zero pmid overlap across all ten
   sibling pairs, 11,519 papers, 148,186 rows, per-package counts summing exactly.
2. **Paper metadata**: `pmid`, `doi`, `title`, `journal`, `year`, `chunk_id`.
3. **`provenance_quote` presence and length.** The same extraction schema field throughout,
   with an identical matcher used for every census (`code/quote_trace.py`, unmodified).
4. **`ontology_id_verification` and `ontology_id_match_mode`**: added by harmonization
   specifically so that a cross-package grounding question has a consistent answer.
5. **The capability flags** `cap_entity_kind`, `cap_hpo_verified`, `cap_number_in_quote`,
   `cap_quote_source_retained`: computed, not extracted, and true exactly where the
   underlying evidence exists.

## Metrics that are NOT comparable across all five packages

Eleven remain. Each is listed with the reason in `qa/comparability_report.json` under
`metrics_not_comparable_summary`. Summarized:

| metric | comparable across | why not otherwise |
|---|---|---|
| `id_resolved_frac` | nothing, see Trap 1 | conflates coverage with correctness; denominator choice reorders packages |
| `id_denotes_entity_rate` | all five, per package only | never pool: Tier 2's 12,289 rows dominate and hide a 30–40 point gap |
| quote verifiability | Tier 4 only measurable as a census | Tiers 1–3 discarded body text |
| findings per paper | within a `fulltext_status` stratum only | yield is driven ~3× by full-text availability, and the mix differs by package |
| `entity_kind` | Tiers 3, 4 | absent in Tiers 1, 2, null means NOT PRESENT, not "unknown" |
| canonicalization rate | Tiers 3, 4 | `canonical_entity` is undefined in Tiers 1, 2 |
| `evidence_tier` distribution | with drift flagged | enum drift between passes; values flagged, never coerced |
| `condition` distribution | with drift flagged | enum evolved; `other patient group` and `IBD_gut` unadjudicated |
| `theme` | never | theme vocabularies are package-specific by construction |
| `ontology_id_source` | never, see Trap 3 | inverted semantics |
| `query_contamination` | never | 40 abbreviation-collision rows in Tier 3 vs 1,960 screening-uncertain rows in Tier 4, two different concepts |

## Denominators

Every rate in this package states its denominator, because several are defensible and they
disagree:

- **Papers** are counted as `pmid.nunique()`. Tier 1's earlier releases used a `canonical_pmid`
  column that merged 8 duplicate-title records; that column is not in the harmonized corpus, so
  Tier 1 here reports 3,129 papers where the Tier 1 v1 release reported 3,121.
- **Coverage** has two true values. Tier 4 covers 85.97% of *screened* papers and 74.57% of the
  *pre-screening universe*. Both are correct; neither is "the" coverage. State which you mean.
- **Verifiability** denominators are rows-with-a-quote, not all rows, though in this corpus
  every row has a quote, so they coincide.

## Negative controls

Every quality metric in `qa/` has one, because a metric without a control can be measuring your
own code. This is not hypothetical: a traceability check once read 100% because the caller did
`if tr:` on a truthy tuple, and the wrong-paper control read 400/400, exposing it.

- **Quote matcher:** quotes paired against a *different* paper's text. Reports ~0% in every
  stratum of every package.
- **Identifier denotation:** shuffled entity/label pairs. 0.003–0.010 against 0.42–0.89
  observed.
- **Entity canonicalization:** 25 planted should-not-merge pairs (0 false merges) and 2,460
  should-merge pairs (2,459 correct, 0.9996).
- **The invariant suite itself:** verified against planted regressions, not just against data
  that happened to pass. `code/verify_package.py --self-test` re-plants six of them and asserts
  each is still caught.
