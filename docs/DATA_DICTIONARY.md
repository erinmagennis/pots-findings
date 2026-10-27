# Data Dictionary — `data/tier1_findings.parquet`

> **Archived: Tier 1 (July 2026).** This document describes the first release (36,459 findings from 3,121 papers).
> The current data is v1.2: 148,186 findings from 11,519 papers in five packages with Zenodo DOIs. See the
> repository [README](../README.md) ("Download and cite"), each package's own docs, and the plain-language guide at
> https://pots.erinmagennis.com/start.

**89 columns × 36,459 rows.** Every retained field is documented below with its **measured** fill
rate, computed directly from the shipped parquet (see `data/field_fill_rates.csv` for the machine-readable
version, and `notebooks/01_load_and_explore.ipynb` to recompute them yourself).

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

## Read these five rules before you query

1. **Count papers with `canonical_pmid.nunique()` → 3,121.** Using `pmid` gives 3,129 and
   double-counts the 8 merged duplicate records. **The dedup was validated, not blind:** 9
   duplicate-title groups (18 PMIDs, 179 findings) were examined, 8 merged (53 findings
   reattributed via `canonical_pmid`, none deleted, fully reversible), and **1 deliberately
   retained** — two genuinely distinct papers sharing the generic title "Post-COVID-19 Postural
   Orthostatic Tachycardia Syndrome" with disjoint author lists (`author_jaccard = 0.0`):
   PMID 34053992 (Ishibashi et al., *Internal Medicine*, 2021) and PMID 35470419 (Savytskyi
   et al., *Cardiology Journal*, 2022). Title-only matching would have merged them and destroyed
   a real independent replication. Audit all 9 groups in `data/pmid_dedup_map.parquet` via
   `merge_applied` / `merged_reason`.
2. **`canonical_entity` covers 29.8% of rows — not half.** `canonical_entity` is present on
   10,858 of 36,459 rows (**29.8%**); the original `entity` string is present on 19,307 rows
   (**53.0%**). **These are two different columns with two different coverage figures.** The gap
   has two separate causes: 17,152 rows (47.0%) name no entity at all (symptom/phenotype
   findings — by design), and a further **8,449 rows carry an entity string that received no
   canonical mapping** because canonicalization was head-only (1,803 typed vocabulary entries
   against 9,582 distinct strings in the findings; 7,605 strings unmapped). **Entity-keyed
   analysis covers ~30% of findings across 2,185 of 3,121 papers — never present an entity-keyed
   count as a total.** The 8,449 unmapped-string rows are real findings and remain findable by
   keyword search on `entity` / `entity_norm_original`. See
   [Entity coverage](#entity-coverage-two-different-gaps-two-different-numbers) below.
3. **`split_derived` (696 rows) inflates per-entity paper counts.** Those rows came from splitting
   compound entity strings ("IL-6 and TNF-alpha"). Wherever a paper count is the claim, report
   `papers_direct` — computed excluding `split_derived` — separately from the total. The
   discovery tables already carry both.
4. **Filter on `map_confidence == "high"` for anything load-bearing.** Typed vocabulary entries:
   **1,512 high, 240 medium, 51 low**. Row-level: 10,857
   rows carry a value (9,627 high /
   999 medium / 232 low).
5. **`source_fidelity` is `"high"` for all 36,459 rows** — a single value, **zero information**.
   It is retained only for forward-compatibility with later tiers. Do not present it as a quality
   filter that passed.

## Entity coverage: two different gaps, two different numbers

`entity` and `canonical_entity` are **not** the same column and do not have the same
coverage. Conflating them will make you overestimate what entity-based views cover by
roughly a factor of two.

| Measure | Rows | % of 36,459 | Papers (canonical_pmid) |
|---|---|---|---|
| Original `entity` string present | 19,307 | **53.0%** | 2,494 |
| `canonical_entity` present | 10,858 | **29.8%** | 2,185 |
| Entity string present but **no** canonical mapping | 8,449 | 23.2% | — |
| No entity of any kind | 17,152 | 47.0% | — |

The gap between 53.0% and 29.8% is made of two distinct causes, and they have different
implications:

1. **47.0% of rows carry no entity at all** (17,152 rows). These are symptom-burden,
   phenotype, quality-of-life and study-level findings that do not name a single measurable
   entity. This is **by design**, not a failure — a finding like "patients reported greater
   fatigue after upright posture" has no gene, drug or analyte to attach.
2. **A further 8,449 rows carry an entity string that received no canonical mapping.**
   Canonicalization was **head-only by deliberate scope decision**: the vocabulary covers
   2,019 normalized strings (1,803 of them typed with an `entity_kind`, resolving to 863
   canonical entities). The findings contain **9,582 distinct normalized entity strings**, so
   **7,605 distinct strings were left unmapped**.

**The unmapped tail is genuinely a tail.** Of those 7,605 unmapped strings, 6,761 occur exactly
once and **none occurs more than twice** — no unmapped string appears in 3 or more findings.
So leaving them unmapped does not distort any entity count: there is no hidden high-frequency
entity in the tail. What it does mean is that those 8,449 findings are real results that are
simply not rolled up under a canonical name.

### What this means for you

- **Entity-based views, filters and charts cover ~30% of findings, not half.** Any chart keyed
  on `canonical_entity` describes 10,858 of 36,459 findings, spanning 2,185 of 3,121 papers.
  936 papers contribute no canonically-mapped entity at all. Every entity-keyed figure in this
  repository states its denominator on the chart.
- **Findings with an unmapped entity string are still real and still findable.** Search them by
  keyword on the original `entity` / `entity_norm_original` string. They must not be treated as
  absent — an entity-rollup query excludes them, a keyword query does not.
- **Absence from an entity rollup is not absence from the literature.** If a marker you care
  about returns nothing under `canonical_entity`, search the original string before concluding
  the corpus is silent on it.

### State which pmid basis a count uses

Paper counts differ slightly depending on the basis, because 8 duplicate pmids were folded into
their canonical records. Use **`canonical_pmid`** and say so; do not mix bases within a table.

| Canonical entity | Papers on raw `pmid` | Papers on `canonical_pmid` |
|---|---|---|
| norepinephrine | 195 | 194 |
| elp1 | 58 | 53 |
| ivabradine | 63 | 62 |

Only **3 of 863** canonical entities are affected at all; `elp1` is the largest single shift
(−5) because three of the merged groups are ELP1 preprint→published pairs. The same entities on
the `papers_direct` basis (excluding `split_derived` rows) give different absolute numbers again
— norepinephrine 177 raw / 176 canonical, elp1 57 / 52, ivabradine 61 / 60 — which is exactly
why the basis must be stated rather than assumed.

## Thin enrichment fields — sparse because the papers don't say it

These five fields are populated at very low rates. **This is not a pipeline bug and re-running
extraction will not improve it** — the information is simply not in the source text. Papers do
not state GO/Reactome IDs, most clinical studies deposit no public dataset, HPO terms are not
clinical-paper vocabulary, and papers rarely name a specific finding they contradict.

| Field | Measured fill | Rows |
|---|---|---|
| `pathway_id` | 0.06% | 22 |
| `dataset_accession` | 0.72% | 263 |
| `phenotype_hpo` | 2.78% | 1,014 |
| `contradicts_finding_ref` | 4.17% | 1,520 |
| `entity_ontology_id` | 12.67% | 4,619 |

Raising these requires **external database joins keyed on the canonical entities** (HGNC →
pathway membership, entity → HPO crosswalk, entity → GEO/SRA lookup), which is downstream
enrichment work, not extraction work. Until then: treat all five as opportunistic bonuses and
**never** as analysis keys. The mechanistic content you actually want is in
`pathway_or_mechanism` (**63.9%** filled), as prose.

## Fill-rate summary by band

| Band | Count | Fields |
|---|---|---|
| 100% | 34 | Structural/always-extracted fields |
| 50–99% | 22 | Commonly stated |
| 15–50% | 9 | Sometimes stated |
| 1–15% | 20 | Rarely stated — use as filters, not keys |
| <1% | 4 | Thin enrichment — effectively unusable |

Two columns present in the internal table were **dropped from this release** because they were
0.00% filled in Tier 1: `entity_ontology_id_note` and `anatomical_study`.

---

## Field reference

### Paper identity and attribution

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `canonical_pmid` | string | 100.0% | PubMed ID of the canonical record for this paper, after duplicate-title merging. **Use this for all paper counts.** | PMID string | 3,121 distinct. 8 PMIDs were folded here from merged duplicates; `pmid` retains the original. |
| `pmid` | string | 100.0% | PubMed ID as originally extracted, before duplicate merging. | PMID string | 3,129 distinct — counting papers with this double-counts the 8 merged records. |
| `title` | string | 100.0% | Source paper title. |  | 3,122 distinct across 3,129 PMIDs — the collision is the 9 duplicate-title groups (see METHODS). |
| `journal` | string | 100.0% | Journal name. |  | 1,123 distinct. |
| `year` | numeric | 99.99% | Publication year. | 2019–2026 | Heavily skewed recent (2025: 11,324 findings; 2026: 8,009) — corpus recency bias, not a research surge. 5 rows lack a year. |
| `citation_short` | string | 100.0% | Pre-formatted short citation for display next to a finding. |  | Always show this (or authors+journal+year) adjacent to any quoted text. |
| `first_author` | string | 99.99% | First author surname/initials. |  |  |
| `last_author` | string | 98.89% | Last author — used as the independence proxy in the under-studied table. |  | Senior-author identity is an imperfect lab proxy; shared last authors across papers indicate non-independent replication. |
| `authors` | string | 99.99% | Full author list. |  | 99.9% filled. |
| `author_count` | integer | 100.0% | Number of authors. | integer |  |
| `doi` | string | 100.0% | DOI of the source paper. |  |  |
| `doi_url` | string | 100.0% | Resolvable DOI link. | URL | Attribution requirement: show this or `pubmed_url` with every finding. |
| `pubmed_url` | string | 100.0% | PubMed record link. | URL |  |
| `pmc_url` | string | 83.77% | PMC full-text link where the paper is in PMC. | URL | Only populated for PMC-indexed papers. |
| `is_open_access` | string | 99.42% | Whether the paper is open access. | boolean/flag |  |
| `cited_by_count` | numeric | 99.42% | Citation count at metadata-fetch time. | integer | A snapshot, not live. Do not treat as current. |

### The finding itself

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `finding_text` | string | 100.0% | The extracted finding, as a sentence. **The primary content field.** |  | 36,032 distinct values across 36,459 rows — duplicates arise from compound-entity splitting (`split_derived`) and from the same claim extracted in two sections. 1 row is empty. |
| `direction` | string | 100.0% | Direction of the reported effect. | `elevated` (11,761); `not applicable` (9,277); `depleted/reduced` (5,763); `dysregulated (unspecified direction)` (5,126); `no significant difference` (4,481); `sex-difference-reported` (50); `mixed` (1) | `not applicable` (9,277) and `no significant difference` (4,481) together are 37.7% of rows — direction-agreement metrics must exclude them, not treat them as agreement. |
| `direction_reference` | string | 100.0% | What the direction is relative to. | `vs-disease-state` (21,988); `vs-intervention` (8,110); `not-applicable` (6,358); `hormonal-axis-implicated` (2); `vas-disease-state` (1) | Two rows carry typo-like values (`vas-disease-state`, and `hormonal-axis-implicated`) — negligible but present. |
| `relation_type` | string | 100.0% | Typed relation asserted by the finding. | `ASSOCIATED_WITH` (15,738); `TARGETED_BY_TREATMENT` (5,897); `NO_ASSOCIATION` (3,832); `DIAGNOSED_BY` (1,613); `PREDICTS` (1,579); `BIOMARKER_FOR` (1,538); `DOWNREGULATED_IN` (1,477); `CO_OCCURS_WITH` (1,147); `CAUSES` (1,061); `UPREGULATED_IN` (890); `DYSREGULATED_IN` (844); `PART_OF_PATHWAY` (843) | `NO_ASSOCIATION` (3,832) is a real relation, not a missing value. |
| `relation_subject` | string | 100.0% | Subject of the relation. |  | Free text, 22,085 distinct — not canonicalized. Do not join on it. |
| `relation_object` | string | 100.0% | Object of the relation. |  | Free text, 20,853 distinct — not canonicalized. |
| `certainty` | string | 100.0% | How firmly the source states the finding. | `confirmed` (23,310); `hedged` (9,347); `mixed` (3,802) | `hedged` (9,347) + `mixed` (3,802) = 36% of rows. |
| `causal_or_correlational` | string | 100.0% | Whether the source claims causation. | `correlational-only` (23,193); `not-stated` (8,893); `causal-claim` (4,373) | Only 4,373 rows (12%) carry a causal claim; 23,193 are explicitly correlational-only. |
| `null_or_failed_result` | string | 100.0% | Whether this is a negative/null/failed result. | `positive-effect` (19,594); `not-applicable` (12,154); `null-no-effect` (4,143); `failed-to-replicate` (452); `tried-and-abandoned` (116) | The basis of `null_results.parquet`. Negatives were extracted deliberately, not dropped. |

### Entities and canonicalization

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `entity` | string | 53.0% | Entity string as it appeared in the source text. |  | Present on 19,307 rows. NULL for 47.0% of rows — those findings name no single entity (symptom-burden, phenotype, study-level). 10,184 distinct raw strings. |
| `entity_norm_original` | string | 53.0% | The normalized form of `entity` before canonicalization. |  | **9,582 distinct strings; 1,977 of them carry a canonical mapping and 7,605 do not.** This is the column to keyword-search when you need the 8,449 findings whose entity string was never canonicalized — they are real findings, just not rolled up. |
| `entity_component_string` | string | 53.0% | For compound entities, the individual component this row was split to. |  | Populated on the same rows as `entity`. |
| `canonical_entity` | string | 29.8% | Canonical entity name after mapping. **The key for all entity-level analysis.** | 863 distinct values | **Present on only 10,858 rows = 29.8%, spanning 2,185 of 3,121 papers — NOT the 53.0% of rows.** Never present an entity-keyed count as covering the whole table. Only 29.8% of rows carry it because mapping additionally requires a confident match. |
| `entity_kind` | string | 29.8% | Type of the canonical entity. | `physiological-measure` (2,812); `molecule-or-analyte` (2,472); `drug-or-drug-class` (1,964); `gene-or-protein` (1,924); `clinical-sign-or-condition` (961); `other` (725) | Only present where `canonical_entity` is. |
| `entity_qualifier` | string | **1.49%** | Modifier retained from the surface string (e.g. a fraction, a site). |  | 1.5% — sparse by nature. |
| `map_source` | string | 29.8% | How the canonical mapping was produced. | `curated-opus` (5,179); `sonnet-adjudicated` (4,780); `alias-rule` (899) | `alias-rule` is deterministic; the two LLM-adjudicated sources carry more risk. Cross-check with `map_confidence`. |
| `map_confidence` | string | 29.8% | Confidence in the canonical mapping. | `high` (9,627); `medium` (999); `low` (232) | **Filter on `high` for anything load-bearing.** Typed vocabulary: 1,512 high / 240 medium / 51 low. |
| `canonical_ontology_id` | string | **11.85%** | Ontology ID for the canonical entity. | HGNC / ChEBI / MeSH / NCBIGene ID | 368 distinct IDs. 11.9% of rows — see thin-enrichment note below. |
| `canonical_ontology_source` | string | **11.85%** | Which ontology resolved the ID. | `ChEBI/OLS4` (2,200); `HGNC/MyGene` (1,796); `MeSH/NLM` (319); `NCBIGene/MyGene` (6) |  |
| `entity_ontology_id` | string | **12.67%** | Ontology ID as extracted/resolved pre-canonicalization. |  | 12.7% — retained for traceability; prefer `canonical_ontology_id`. |
| `entity_ontology_id_resolved` | string | **12.02%** | Ontology ID that validated against a live lookup. |  |  |
| `entity_ontology_label` | string | **12.02%** | Label of the resolved ontology term. |  | Use to sanity-check a mapping visually. |
| `gene_marker` | string | **7.66%** | Gene or protein symbol named by the finding. |  | 7.7% — most findings are not gene-level. |
| `gene_resolved` | boolean | 100.0% | Whether the gene symbol resolved to HGNC/Ensembl. | boolean |  |
| `hgnc_id` | string | **7.43%** | HGNC ID for a resolved gene. | HGNC:n | 7.4% |
| `ensembl_id` | string | **7.42%** | Ensembl gene ID. | ENSG… | 7.4% |

### Clinical and population context

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `condition` | string | 100.0% | Condition the finding is about. | `dysautonomia` (18,293); `general` (5,854); `POTS` (5,078); `long_COVID` (2,608); `multiple` (1,129); `ME_CFS` (845); `fibromyalgia` (756); `small_fiber_neuropathy` (642); `EDS_hypermobility` (625); `migraine` (255); `MCAS` (236); `IBS_gut` (90); `autism` (44); `orthostatic_hypotension` (4) | **Read with the scope limit.** Non-POTS values count POTS/dysautonomia papers that *mention* the condition — not that condition's literature. |
| `pots_subtype` | string | **14.49%** | POTS subtype where stated. | `not specified` (4,600); `hyperadrenergic` (352); `hypovolemic` (174); `neurogenic` (151); `immune-related` (3); `autoimmunogenic` (1); `neuropathic` (1) | 14.5%, and 4,600 of those are `not specified` — only ~682 rows name a real subtype. |
| `theme` | string | 100.0% | Search/augmentation theme that surfaced the paper. | `dysautonomia` (16,203); `POTS` (9,334); `dysautonomia_subtype` (8,744); `hyperadrenergic` (2,154); `patient_evidence` (19); `ME_CFS` (5) | Corpus-construction metadata, not a finding property. |
| `finding_type` | string | 100.0% | What kind of finding this is. | `mechanism/biomarker` (16,348); `treatment/intervention` (7,210); `diagnostic/screening` (4,830); `comorbidity` (4,187); `symptom-burden` (3,884) |  |
| `population_age_group` | string | 100.0% | Age group. | `adult` (22,796); `not-stated` (8,467); `pediatric` (2,972); `mixed` (2,224) | `not-stated` for 8,467 rows. |
| `sex_hormonal` | string | 100.0% | Sex/hormonal specificity. | `none-stated` (30,830); `female-specific` (2,511); `male-specific` (1,621); `sex-difference-reported` (1,280); `hormonal-axis-implicated` (217) | `none-stated` for 30,830 rows. POTS is strongly female-predominant, so the 2,511 female-specific rows under-represent the real picture. |
| `anatomical_system` | string | 100.0% | Body system involved. | 734 distinct | Free-ish text despite 100% fill — treat as a tag, not a controlled vocabulary. |
| `is_covid_associated` | boolean | 100.0% | Whether the finding concerns COVID-associated illness. | boolean |  |
| `symptom_correlate` | string | 53.15% | Symptom the finding relates to. |  | 53.2%, 10,747 distinct — not canonicalized. |
| `phenotype_hpo` | string | **2.78%** | Human Phenotype Ontology term. | HPO:n | **2.8% — thin enrichment.** See note below. |
| `phenotype_hpo_resolved` | string | **2.76%** | HPO ID that validated against a lookup. |  | 2.8% |
| `phenotype_hpo_label` | string | **2.76%** | HPO term label. |  | 2.8% |
| `treatment_class` | string | 21.66% | Treatment or intervention class. |  | 21.7%, 4,382 distinct — not canonicalized; use `canonical_entity` with `entity_kind = drug-or-drug-class` for grouping. |
| `adverse_event_note` | string | **6.54%** | Adverse event mentioned. |  | 6.5% — presence is informative, absence is **not** evidence of safety. |
| `validated_instrument` | string | 16.3% | Validated instrument/questionnaire used. |  | 16.3% (e.g. COMPASS-31). |

### Study design and evidence strength

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `evidence_tier` | string | 100.0% | Study design tier. | `cohort` (8,239); `cross-sectional` (7,009); `review/expert-opinion` (6,507); `case-report` (3,777); `case-series` (3,239); `case-control` (3,184); `mechanistic/in-vitro` (2,787); `RCT` (877); `meta-analysis` (840) | `RCT` (877) + `meta-analysis` (840) = 4.7% of rows. `review/expert-opinion` (6,507) is not primary evidence. |
| `evidence_stratum` | string | 100.0% | Publication/venue class. | `peer-reviewed` (31,806); `case-report` (3,668); `patient-registry` (525); `clinical-trial-registry` (244); `large-survey` (131); `review/expert-opinion` (70); `preprint` (15) | Independent of `evidence_tier` — filter on both. |
| `study_type` | string | 75.51% | Study design as stated by the paper. | `review/narrative` (5,917); `case-report/case-series` (5,708); `cohort/observational` (5,010); `cross-sectional` (5,004); `case-control` (2,095); `mechanistic/in-vitro` (1,365); `systematic-review/meta-analysis` (1,350); `RCT` (673); `other` (407) | 75.5% filled. Overlaps `evidence_tier` but is source-stated rather than assigned. |
| `study_quality` | string | 100.0% | Free-text quality note. |  | 100% filled but 21,230 distinct — free text, not a score. Not usable as a filter. |
| `n_participants` | numeric | 53.86% | Participant count. | numeric | 53.9%. Includes single-case counts; check `evidence_tier` before averaging. |
| `comparator` | string | 75.51% | What the finding compares against. | `other patient group` (7,853); `healthy controls` (5,743); `no comparator` (5,673); `not applicable` (5,477); `pre/post within-subject` (2,728); `other` (55) | `no comparator` (5,673) and `not applicable` (5,477) matter — an uncontrolled finding is flagged here. |
| `demographics` | string | 56.58% | Free-text demographic description. |  | 56.6% |
| `cohort_registry` | string | 17.41% | Registry the cohort came from. |  | 17.4% |
| `cohort_name` | string | **7.83%** | Named cohort. |  | 7.8%, 387 distinct — useful for spotting overlapping cohorts across papers, which is the main independence risk. |

### Mechanism and quantitation

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `pathway_or_mechanism` | string | 63.9% | Mechanism described, as free text. |  | 63.9% — the mechanistic content is here, in prose. Contrast with `pathway_id`. |
| `pathway_id` | string | **0.06%** | GO/Reactome/MeSH pathway ID. |  | **0.06% — 22 rows. Thin enrichment; effectively unusable.** See note below. |
| `pathway_id_resolved` | string | **0.06%** | Validated pathway ID. |  | 0.06% |
| `pathway_label` | string | **0.05%** | Pathway term label. |  | 0.05% |
| `functional_impact` | string | 33.08% | Functional consequence described. |  | 33.1% |
| `quantitative_detail` | string | 63.16% | Numbers as stated in the source. |  | 63.2% — free text ('mean 78 vs 62 bpm'), not parsed. Parsing this is open work. |
| `effect_size` | string | 37.98% | Effect size as stated. |  | 38.0% — free text with mixed units/statistics. Not comparable across rows without parsing. |
| `dataset_accession` | string | **0.72%** | Public dataset accession (GEO/SRA/etc.). |  | **0.72% — 263 rows, 52 distinct. Thin enrichment.** Most clinical papers deposit nothing. |

### Contradiction and self-critique

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `contradicts_or_extends` | string | 59.7% | Free-text note on how the finding relates to prior work. |  | 59.7% |
| `contradicts_finding_ref` | string | **4.17%** | Specific reference the finding contradicts. |  | **4.2% — thin enrichment.** Papers rarely name a specific contradicted finding. Recovery over all ref rows is 20.3%. |
| `limitations_stated` | string | 64.57% | Limitations stated by the source paper. |  | 64.6% — the authors' own caveats, worth reading before trusting a row. |
| `future_direction` | string | 69.68% | Future work stated by the source. |  | 69.7% |

### Provenance and pipeline metadata

| Field | Type | Fill | Meaning | Allowed values | Caveats |
|---|---|---|---|---|---|
| `provenance_quote_trunc` | string | 100.0% | Verbatim excerpt from the source paper supporting the finding, **truncated to ≤200 characters**. |  | **Publisher-copyright text.** Always display adjacent to the citation and link. Never bulk-export. 14,527 of 36,459 quotes were truncated from their original length. |
| `provenance_section` | string | 100.0% | Section of the paper the quote came from. | `results` (20,163); `discussion` (8,398); `abstract` (5,515); `introduction` (1,658); `figure/table` (342); `conclusion` (190); `methods` (115); `title` (69); `unknown` (6); `case-report` (3) | `introduction` (1,658) and `discussion` (8,398) quotes often describe *other* papers' work — a known error mode. `results` (20,163) is the most reliable. |
| `fulltext_status` | string | 100.0% | Whether extraction saw full text or only the abstract. | `retrieved-fulltext` (29,910); `abstract-only` (6,535); `blocked` (14) | 6,535 abstract-only rows are thinner and more error-prone. |
| `source_stream` | string | 93.82% | Which search stream surfaced the paper. | `base` (23,952); `augmentation_subtype` (8,191); `augmentation_theme` (2,043); `patient_registry` (19) | 93.8% — corpus metadata. |
| `source_route` | string | **6.18%** | Extraction route, where a dedicated route was used. | `poolC1-pmc-xml` | 6.2%, single value. |
| `source_fidelity` | string | 100.0% | Fidelity of the source text route. | `high` (all 36,459 rows) | **Single-valued in Tier 1 — carries ZERO information.** Retained for forward-compatibility with later tiers. Must not be presented as a quality filter that passed. |
| `pmcid` | string | **6.18%** | PMC ID where applicable. |  | 6.2% |
| `chunk_id` | numeric | 93.82% | Corpus chunk the paper came from. | 0–75 | Tier 1 is chunks 0–75 of 286. This column is how you verify the scope limit yourself. |
| `split_derived` | boolean | 100.0% | Whether the row was generated by splitting a compound entity string. | boolean — 696 True | **Critical for counting.** These rows inflate per-entity paper counts. Report `papers_direct` (excluding them) separately wherever a paper count is the claim. |
| `is_duplicate_or_preprint_note` | string | **1.76%** | Note flagging a suspected duplicate or preprint. |  | 1.8% — extraction-time flag, distinct from the validated dedup in `pmid_dedup_map.parquet`. |
| `contact_note` | string | **9.29%** | Corresponding-author/contact note. |  | 9.3% |

---

## Companion tables

| File | Rows | Key | Notes |
|---|---|---|---|
| `entity_vocabulary.parquet` | 2,019 | `entity_norm` → `canonical_name` | 1,803 typed; 570 with an ontology ID. `rows`/`papers` give corpus frequency; `is_compound`/`components` record splits. |
| `paper_metadata.parquet` | 3,129 | `pmid`, `canonical_pmid` | Attribution source. `is_canonical` marks the surviving record of each merged group. |
| `pmid_dedup_map.parquet` | 18 | `pmid` | All 9 duplicate-title groups with `merge_applied`, `merged_reason`, `author_jaccard`. The audit trail for rule 1. |
| `association_table.parquet` | 555 | `entity_a` × `entity_b` | 547 tested, 456 significant at BH q<0.05, 101 cross-kind non-trivial. |
| `understudied_signals.parquet` | 329 | `canonical_entity` × `condition` × `direction` | 226 headline-eligible; 198 also have ≥2 independent last authors and are not case-report-only. |
| `contradictions.parquet` | 532 | `canonical_entity` × `condition` | 268 direction flips + 264 null-vs-positive; 127 with a visible moderator; **376 under broad condition labels**. |
| `null_results.parquet` | 5,324 | `canonical_pmid` | 3,076 biomarker nulls, 1,340 treatment failures (315 at RCT/meta tier), 908 diagnostic nulls. |
| `convergence_tier1.parquet` | 308 | `canonical_entity` × direction | 106 pass the ≥2-non-POTS bar, 45 headline-eligible. **Non-POTS support is incidental mention** — read `scope_warning`. |
| `findings_embeddings_int8.npy` | 36,459 × 384 | row order == findings parquet | uint8; dequantize `q*scale+qmin` then L2-normalize, params in `embeddings_quant_params.json`. Mean cosine fidelity 0.99997. |

## Quoted text

`provenance_quote_trunc` is **verbatim publisher-copyright text**, truncated to ≤200 characters
(14,527 of 36,459 rows were truncated). It
exists so a reader can verify a finding against its source. Always render it adjacent to the full
citation and link; never bulk-export the column. See [`../LICENSE`](../LICENSE).
