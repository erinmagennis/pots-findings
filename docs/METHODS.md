# Methods

How the Tier 1 database was built, and the exact filters behind every derived number.

> ### Scope: this is Tier 1 — POTS and dysautonomia only
>
> This release covers **POTS/dysautonomia literature only** (chunks 0–75 of a 286-chunk corpus):
> **~3,121 of ~14,263 corpus papers**.
>
> ME/CFS (136 papers), fibromyalgia (103), EDS/hypermobility (146), MCAS (90), IBS (64),
> migraine (61) and autism (18) appear here **only as incidental mentions inside
> POTS/dysautonomia papers**. Those conditions' own literatures are in Tiers 2–4 and are
> **not yet extracted**. This is **not** a cross-condition resource, and a count of
> "fibromyalgia papers" here means "POTS/dysautonomia papers that mention fibromyalgia."
>
> ### Not medical advice
>
> This is machine-extracted research information, not clinical guidance. It contains no
> diagnostic or treatment recommendations. Nothing here should be used to start, stop, or
> change any treatment. Bring personal health questions to a qualified clinician.
>
> ### Attribution
>
> Every finding links to its source paper with authors and journal. These are **automated
> summaries of other researchers' work** — the credit belongs to them, and the original paper
> is the authority. Read it before citing anything you find here.


---

## 1. Corpus construction

PubMed/PMC searches across POTS and dysautonomia, expanded along two augmentation axes —
**subtype** (hyperadrenergic, hypovolemic, neuropathic, neurogenic) and **theme** — plus
trial-registry and omics-dataset augmentation. Result: a corpus of **~14,263 papers**.
`source_stream` records which stream brought each paper in:
(base 23,952,
augmentation_subtype 8,191,
augmentation_theme 2,043,
patient_registry 19 findings).

## 2. Tiering

The corpus was ordered into **286 chunks** by condition focus, so extraction could proceed
core-outward. **Tier 1 = chunks 0–75**, the POTS/dysautonomia core, **~3,121 papers**. Tiers 2–4
(the related-condition literatures) are **not extracted**. `chunk_id` on each finding records its
source chunk (76 distinct values present).

## 3. Extraction

Each paper's text was extracted against a fixed schema by an LLM, one pass per paper.

**Full text where available.** `fulltext_status`:
retrieved-fulltext 29,910 findings,
abstract-only 6,535, blocked 14.
A subset (2,254 findings) came through a dedicated PMC-XML route
(`source_route = poolC1-pmc-xml`, `pmcid` populated).

**Grounding is mandatory.** Every finding carries a `provenance_quote` (verbatim source text) and
a `provenance_section` locating it in the paper — results
(20,163),
discussion, abstract, and so on. This is what makes any individual row auditable in under a
minute, and it is the core claim of the method: **extraction you can check**.

**Relation typing.** Each finding is typed with a `relation_type` (12 values) over a
`relation_subject`/`relation_object` pair, alongside a `direction`, a `certainty` (confirmed /
hedged / mixed) and a `causal_or_correlational` label. Both `evidence_tier` (9 values) and
`evidence_stratum` (7 values) are recorded, so study design and publication venue class can be
filtered independently.

**Negative results were extracted deliberately**, not discarded — `null_or_failed_result`
distinguishes positive-effect, null-no-effect, failed-to-replicate, and tried-and-abandoned.
This is why the null-results table exists at all; most literature-mining efforts drop this
information.

## 4. Canonicalization

Entity surface strings (19,307 filled rows = **53.0%** of findings, 9,582 distinct normalized
strings) were processed as below. Note the endpoint before reading further: **`canonical_entity`
ends up on 10,858 rows = 29.8%**, spanning 2,185 of 3,121 papers. The 53.0% figure describes the
original string column; the 29.8% figure is what entity-keyed analysis actually covers. The steps:

1. **Normalized** — case, punctuation, whitespace, common variant spellings.
2. **Split** where a string named several entities ("IL-6 and TNF-alpha"). **216 compound
   strings** were split, producing **696 `split_derived` rows**. This is
   the only reason the row count grew from 36,067 to **36,459**; the
   **36,032 distinct `finding_text` values are unchanged**.
3. **Mapped** to a canonical name with a typed `entity_kind`. Mapping was **head-only, by
   deliberate scope decision**: the vocabulary holds 2,019 normalized strings of which **1,803
   are typed**, covering **1,977 of the 9,582 distinct** surface strings in the findings and
   yielding **863 canonical entities**. The remaining **7,605 distinct strings (8,449 rows) were
   left unmapped** — 6,761 of them occur exactly once and none occurs more than twice, so the
   unmapped tail cannot distort entity counts. Those rows keep their original string and stay
   findable by keyword search; they are excluded only from canonical-entity rollups.
   `map_source` records how the mapped ones were resolved:
   curated-opus 5,179,
   sonnet-adjudicated 4,780,
   alias-rule 899 rows.
4. **Resolved** against external ontologies where a confident match existed: **368 entities with
   ontology IDs** — 145 HGNC genes, 189 ChEBI chemicals, 34 MeSH conditions.
5. **Scored** — every mapping carries `map_confidence`. Typed vocabulary entries:
   **1,512 high, 240 medium, 51 low**.

### Duplicate-title handling: 9 groups examined, 8 merged, 1 retained

Nine normalized titles span more than one PMID (**18 PMIDs, 179 findings**). All nine groups were
**examined**, not merged on title match alone — each was validated against its author lists.

- **8 groups merged.** 8 PMIDs were folded into their canonical record and **53 findings
  reattributed** via `canonical_pmid`. **No findings were deleted** and the operation is fully
  reversible from `data/pmid_dedup_map.parquet`. The merges were 5 preprint→published pairs
  (bioRxiv / Research Square), 1 guideline co-published in two journals simultaneously, 1
  single-page companion/correction, and 1 erratum stub.
- **1 group deliberately not merged** — a false positive caught by author-list validation.
  "Post-COVID-19 Postural Orthostatic Tachycardia Syndrome" is a generic title shared by two
  genuinely **distinct** papers with fully disjoint author lists (`author_jaccard = 0.0`):
  PMID 34053992 (Ishibashi et al., *Internal Medicine*, 2021) and PMID 35470419 (Savytskyi et al.,
  *Cardiology Journal*, 2022). Merging them would have destroyed a real independent replication.

**Net: 3,129 PMIDs → 3,121 distinct canonical papers.** Write it as "9 duplicate-title groups
examined, 8 merged, 1 retained as genuinely distinct" — not "8 duplicate papers." The distinction
matters: it shows the dedup was validated rather than applied blindly, and title-only matching
would have been wrong here. `data/pmid_dedup_map.parquet` records all 9 groups with a
`merge_applied` flag and a `merged_reason` so a reader can audit every decision.


## 5. Discovery tables — exact filters

Every number below is reproducible from the shipped parquet files;
`notebooks/03_associations_and_contradictions.ipynb` recomputes them.

### Associations — `association_table.parquet` (555 rows)

- **Entity filter:** entities with **≥3 papers** in the direct (non-`split_derived`) incidence
  set — 524 entities qualify.
- **Pair enumeration:** all **137,026** unordered entity pairs, via a sparse
  entity × paper incidence matrix.
- **Test:** hypergeometric on papers-co-mentioning vs expected, over a
  2,176-paper universe. Reported as `lift`, `jaccard`,
  `p_hypergeom`.
- **Multiple testing:** Benjamini-Hochberg FDR at α=0.05 over the **547 non-trivial** pairs
  (`included_in_primary`). **456 are significant at q<0.05.**
- **Cross-kind, non-trivial:** `entity_kind_a != entity_kind_b`, significant, in the primary set,
  and excluding `trivial_component_link`, `name_level_nested` and `surface_string_linked` →
  **101 pairs**. These are where the scientifically non-obvious rows live.
- **Not filtered on `map_confidence`** by design — `map_confidence_a`/`_b` are exposed so you can
  apply your own bar.

> Co-occurrence is co-mention in one paper, **not interaction**. The strongest pairs include the
> standard POTS drug ladder, which co-occurs because management reviews list those drugs
> together. Significance there validates the pipeline; it is not a discovery.

### Under-studied signals — `understudied_signals.parquet` (329 rows)

- **Candidates:** 329 entity × condition × direction records, 262 distinct entities.
- **Thin:** `is_thin` = entity has ≤15 total papers corpus-wide (247 candidates).
- **Headline-eligible:** thin **and** `map_confidence == "high"` → **226**. 21 thin candidates
  were dropped by the confidence filter.
- **Replication-target subset:** headline-eligible **and** `n_distinct_last_authors >= 2`
  **and not** `case_report_only` → **198 rows**. Requiring two independent last authors is the
  guard against single-lab artifacts; it does not eliminate them.
- **Scoring:** `replication_score` combines `understudy_factor`, `recency_factor`,
  `independence_factor` and a `case_only_penalty`. `direction_agreement` and
  `n_papers_disagreeing` expose internal consistency.

### Contradictions — `contradictions.parquet` (532 rows)

- **268 hard direction flips** (side A and side B
  claim opposite directions) + **264 null-vs-positive**
  conflicts.
- A same-paper filter removed 61 candidate hard flips and 97 null-vs-positive candidates where
  both "sides" came from one paper — internal hedging, not literature controversy.
- **127 rows have a `has_visible_moderator`** signal — a subtype,
  age group, sex, comparator or assay difference that plausibly explains the disagreement
  (`moderator_candidates`, `moderator_detail`).
- **376 of 532 carry `broad_condition_flag`** — the conflict sits
  under an umbrella condition label and may reflect pooled distinct diseases rather than a
  replication failure. This is the single most important column in the table.
- Both sides expose `n_papers` and `n_papers_direct` so `split_derived` inflation is visible.

### Null results — `null_results.parquet` (5,324 rows)

Rows where `null_or_failed_result` is null-no-effect, failed-to-replicate or tried-and-abandoned,
classified into: **3,076 biomarker/mechanism nulls**,
**1,340 treatment/intervention failures**
(of which **315 at RCT or meta-analysis tier**), and
**908 diagnostic nulls**. `negative_strength` grades how
firmly the negative was stated. The RCT/meta-tier treatment failures are the most
decision-relevant subset in the whole repository.

### Convergence — `convergence_tier1.parquet` (308 rows)

Entities pointing the **same direction across multiple conditions**. Because Tier 1 contains only
POTS/dysautonomia papers, non-POTS support here is **incidental mention**, and the table is
gated hard:

- `passes_nonpots_bar` = `n_papers_other_condition >= 2` → **106 records / 92 distinct entities**.
  Required before any shared-mechanism language.
- `headline_eligible` = passes the bar **and** not contested (`n_papers_opposite_direction < 2`) →
  **45 records / 45 entities**.
- Notably, **none of the highest-scoring entities are headline-eligible** — heart rate, HRV,
  norepinephrine, RMSSD, SDNN and IL-6 all fail on contestation. Every row carries a
  `scope_note`/`scope_warning` stating that non-POTS support is incidental.

## 6. Embeddings

`all-MiniLM-L6-v2`, 384 dimensions, over all 36,459 findings. Quantized to **uint8** with
per-dimension min/scale; dequantize as `q * scale + qmin`, then L2-normalize. Fidelity is
**mean cosine 0.99997** against float32. Stored as **7 shards of 6,000 rows** (last 459),
**14.0 MB total**. The shard layout is append-only by design: Tiers 2–4 add shards and bump the
version; **existing shards and row offsets never change**, so an index built today stays valid.

## 7. Reproducibility

`data/CHECKSUMS.txt` gives sha256 for every shipped file; `data/VERSION.txt` states `tier1-v1`
and row counts. The four notebooks recompute every published figure and derived number from the
parquet files alone, using only pandas / numpy / matplotlib / pyarrow.
