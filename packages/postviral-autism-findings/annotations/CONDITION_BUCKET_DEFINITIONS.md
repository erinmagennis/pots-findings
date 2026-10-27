# Condition bucket definitions, v1, and the MCAS census that prompted them

Written 2026-09-16. The `condition` field is a **coarse bucket enum**, not a
precise diagnosis. Until now its inclusion rules were never written down, which is why an AI
scorer applying a strict-diagnosis reading flagged 10 of 24 clean rows and a bucket-aware reading
flagged 0 of 24 — the same rows, the same data, a 42-point swing from wording alone. These
definitions are the thing a condition label is judged against. **Version them, and re-run any
label audit when they change.**

## MCAS — decided

`MCAS` means **mast cell activation syndrome specifically**: the non-clonal activation syndrome,
including idiopathic MCAS and MCAS comorbid with POTS/hEDS. **Mastocytosis does NOT belong** — it
is a clonal neoplasm and a distinct diagnosis. Rationale: "markers of MCAS" must remain an
answerable question, and pooling a clonal neoplasm with an activation syndrome makes it
unanswerable.

## What that decision reveals — the census

1,083 papers across four tiers carry `condition == 'MCAS'` (t1 90, t2 939, t3 18, t4 36;
8,336 of the 8,834 rows are Tier 2). Two strata, classified against **freshly fetched** abstracts
by a single-question classifier requiring a verbatim deciding span.

**Instrument checks:** 15 migraine-labelled papers as a specificity control -> **14/14 assessed
came back `neither`**, zero false mast-cell calls. Deciding spans verified verbatim in **98.5%**
(191/194). One paper's classification collapsed on a duplicate pmid; 6 papers had no fetchable
abstract.

| stratum | N papers | assessed | mastocytosis | both (kept distinct) | MCAS | mast-cell general | neither |
|---|---:|---:|---:|---:|---:|---:|---:|
| title contains "mastocytos" | 66 | 62 | **49 (79.0%)** | 12 (19.4%) | 1 | 0 | 0 |
| all other titles | 1,017 | 118 | **0 (0%)** | 6 (5.1%) | 13 (11.0%) | 87 (73.7%) | 12 (10.2%) |

Projected over all 1,083 labelled papers:

| category | papers | share |
|---|---:|---:|
| mast-cell biology, no mast-cell-disorder population | **~750** | 69.3% |
| MCAS as defined above | **~113** | 10.4% |
| neither | ~103 | 9.5% |
| both, kept as distinct entities | ~65 | 6.0% |
| mastocytosis | ~52 | 4.8% |

903 papers were not individually assessed (unsampled `title_other` plus fetch gaps); the numbers
above are stratified projections with 95% intervals in `mcas_bucket_census.csv`, **not** a census
of every paper.

## Two findings, and the second is the bigger one

**1. The mastocytosis conflation is real but small and almost perfectly screenable.**
~52 papers (4.8%), and **0 of 118** sampled non-"mastocytos" titles were mastocytosis. The title
keyword is a near-complete screen for this defect, so the repair is bounded: 66 papers to
adjudicate, not 1,083.

**2. The `MCAS` bucket is dominated by papers with no mast-cell-disorder population at all** —
~750 papers (69.3%, 95% CI 65.1–80.8% within its stratum) are mast-cell biology, mediators, or
mast cells in some other disease. **A "markers of MCAS" count computed from this bucket is
mostly a count of markers of mast cells in general.** Only ~10% of the bucket is MCAS as now
defined.

That is a second definitional question, and it is not the one just answered: **does `condition`
mean the patient population studied, or the condition the finding informs?** If the former, ~750
papers belong in `general` and the MCAS bucket is ~113 papers. If the latter, they are correctly
placed and the bucket is a mechanism-relevance tag rather than a population tag — in which case
the data dictionary must say so, prominently, because the intuitive reading is the population one.

## How a relabel gets recorded — never by mutation

`condition` is not edited. Tier 4 is packaged with checksums and `condition` underpins published
statistics; more to the point, this corpus already carries the scar of a column whose meaning
differs between tiers (`ontology_id_source == 'unresolved_nulled'` means *id kept* in one tier and
*id nulled* in another, so the obvious filter silently drops 2,242 valid rows). Editing `condition`
in a later version would manufacture exactly that.

Instead, a lookup table keyed on `pmid`, mutating nothing:

```
condition_specific          free text, as the paper states it ("systemic mastocytosis")
condition_bucket_verdict    in_bucket | bucket_violation | bucket_definition_disputed | NEEDS_HUMAN
condition_population_kind   disorder_population | mechanism_only | not_applicable
condition_relabel_basis     who decided, against which definitions version (this file, v1)
```

`bucket_violation` and `bucket_definition_disputed` stay separate columns-worth of meaning —
one name never carries two concepts.

## Definitions for the other buckets, as currently understood

Written from the flag evidence; each needs the same confirmation `MCAS` just got.

- **`EDS_hypermobility`** — includes Ehlers-Danlos syndromes, hypermobility spectrum disorder, and
  generalized joint hypermobility assessed by Beighton score **without** an EDS diagnosis. The
  corpus draw had a dedicated `hypermobility_spectrum` theme, so hypermobility-without-EDS appears
  to be deliberately in scope. Two flagged rows are correct under this reading.
- **`dysautonomia`** — any autonomic disorder, including MSA, syncope, orthostatic intolerance and
  autonomic neuropathy, where POTS is not the specific subject. Two flagged rows are correct.
- **`general`** — the correct answer when no listed condition is the paper's subject. It is a
  catch-all by design; "too vague" is not a defect. Three flagged rows are correct.
- **`multiple`** — several listed conditions are subjects.

Under these definitions, 7 of the 10 flagged rows are correctly labelled and 3 are violations —
all `MCAS`, all mastocytosis.


## Undefined values present in the data (added 2026-09-16, v1.1)

Three `condition` values occur in the shipped findings but have no definition above and were never
intended as buckets: `IBD_gut` (1 paper), `orthostatic_hypotension` (1 paper), `other patient group`
(2 papers). They are extraction-time enum drift. Read them as `general` for population counts. The
data is not repaired; each package's LIMITATIONS §6 lists any that fall in that package.

Eight of the thirteen defined buckets (POTS, ME_CFS, long_COVID, fibromyalgia, small_fiber_neuropathy,
autism, migraine, IBS_gut) carry PROVISIONAL definitions in the method repository's
`config/pots_dysautonomia.yaml`; only MCAS, EDS_hypermobility, dysautonomia, multiple and general were
written and confirmed here. The adjudication packet of 2026-09-16 (sheet C) is where those get confirmed.
