# Data Dictionary — `data/tier3_findings.parquet`

**26,032 rows × 107 columns.** Every fill rate below is **measured on
this package's own slice**, not inherited from another tier. Recompute them with
`python code/verify_package.py`.

> **Scope: Tier 3 — long COVID, post-viral and autism intersections**
>
> 1,587 papers, chunks 221–255, of an 11,519-paper five-package corpus.
> Four sibling packages hold the rest and share zero papers with this one.
>
> **Not medical advice.** Machine-extracted research information with no diagnostic or
> treatment recommendations.
>
> **Attribution.** Every row links to its source paper. These are automated summaries of
> other researchers' work; the original paper is the authority.

## Four rules before you query

1. **Count papers with `pmid.nunique()`.** Every paper figure in this package uses that basis.
2. **Filter identifiers on `ontology_id_verification`, never on `ontology_id_source`.** The
   latter has inverted semantics between tiers — see `COMPARABILITY.md`, Trap 3.
3. **Stratify on `fulltext_status` before comparing any per-paper rate.** It drives yield ~3×.
4. **A null in a `cap_*` or tier-specific column means NOT PRESENT, not unknown.** This
   package has 19 entirely-null columns, listed at the bottom — they are retained for
   schema compatibility with its siblings, so a pooled read has a stable column set.

## Columns

Ordered as in the parquet. `fill` is the percentage of rows with a non-null value.

| # | column | fill | description |
|---:|---|---:|---|
| 0 | `entity` | 68.5% | Marker, gene, protein, metabolite or measure the finding is about. Free text as the model wrote it. Null on 40%+ of rows by design — symptom, phenotype and quality-of-life findings name no entity. |
| 1 | `entity_ontology_id` | 0.0% | Model-emitted ontology identifier. **Tiers 1-2 only.** Never authority-verified. Do not use as a mapping; use `entity_ontology_id_resolved` with `ontology_id_verification`. **[EMPTY in this package]** |
| 2 | `gene_marker` | 3.6% | Gene symbol as written in the source. |
| 3 | `direction` | 100.0% | Direction of the effect (increased / decreased / unchanged / etc.). |
| 4 | `direction_reference` | 100.0% | What the direction is relative to (controls, baseline, another group). |
| 5 | `finding_text` | 100.0% | The extracted finding, one sentence, as the model rendered it. |
| 6 | `pathway_or_mechanism` | 46.7% | Free-text mechanism. Prose, not an ontology term — only 14 of 147 Tier-2 mechanism strings were real ontology terms, which is why `pathway_id` was dropped. |
| 7 | `pathway_id` | 0.0% | **Tiers 1-2 only, 0.1% filled.** Deprecated; no single GO/Reactome term denotes most mechanism prose. **[EMPTY in this package]** |
| 8 | `quantitative_detail` | 62.3% | Numeric detail as stated in the source. |
| 9 | `effect_size` | 39.0% | Effect size as stated. Not harmonized across studies. |
| 10 | `causal_or_correlational` | 100.0% | Whether the source claims causation or correlation. |
| 11 | `evidence_tier` | 100.0% | Study design. Pinned enum; drift is flagged, never coerced — see the README. |
| 12 | `functional_impact` | 31.7% | Stated functional consequence. |
| 13 | `condition` | 100.0% | **Coarse bucket for the patient POPULATION studied** — not a diagnosis, not a mechanism-relevance tag. Definitions: `annotations/CONDITION_BUCKET_DEFINITIONS.md` v1 (`MCAS` excludes mastocytosis; `EDS_hypermobility` includes HSD and Beighton-assessed hypermobility; `general` = no listed condition is the subject). The `MCAS` bucket is ~69% mechanism-only papers by stratified census — see the README's `condition` warning and `annotations/condition_annotations.parquet`. Distinct from `source_literature` (which literature the paper came from). |
| 14 | `pots_subtype` | 0.5% | POTS subtype where the source specifies one. |
| 15 | `population_age_group` | 100.0% | Age group studied. |
| 16 | `sex_hormonal` | 100.0% | Sex or hormonal-status stratification. |
| 17 | `anatomical_system` | 100.0% | Body system. |
| 18 | `is_covid_associated` | 100.0% | Whether the finding concerns a COVID-associated population. Semantics differ subtly by tier — see comparability report. |
| 19 | `finding_type` | 100.0% | Kind of finding (biomarker, mechanism, treatment response, prevalence, …). |
| 20 | `treatment_class` | 17.7% | Treatment class where the finding concerns one. |
| 21 | `symptom_correlate` | 59.0% | Symptom the finding correlates with. |
| 22 | `phenotype_hpo` | 0.0% | **Model-emitted HPO identifier, Tiers 1-2. ~34% were fabricated.** Do not use. Use `hpo_ids_verified`. **[EMPTY in this package]** |
| 23 | `validated_instrument` | 18.3% | Named validated instrument (COMPASS-31, DSQ-SF, Beighton, …). |
| 24 | `adverse_event_note` | 2.7% | Adverse event mentioned alongside the finding. |
| 25 | `certainty` | 100.0% | The extractor's own certainty judgment. Never overwritten. |
| 26 | `cohort_registry` | 24.8% | Registry the cohort came from. |
| 27 | `cohort_name` | 11.2% | Named cohort. |
| 28 | `dataset_accession` | 0.2% | Dataset accession where stated. 0.7% filled — papers rarely state one. |
| 29 | `relation_type` | 100.0% | Relation type for subject-object findings. |
| 30 | `relation_subject` | 100.0% | Relation subject. |
| 31 | `relation_object` | 100.0% | Relation object. |
| 32 | `provenance_quote` | 100.0% | **The verbatim source span the finding was drawn from.** The verification handle for the whole dataset. Present on every row. See LICENSE for terms — this column is not CC BY. **Verbatim with respect to the text the extraction model read, not to the paper as displayed:** 2 rows in this package (128 corpus-wide, 0.09%) contain raw HTML entity codes such as `p&#x202f;<&#x2009;0.001`, because Europe PMC text was fed to the model without entity decoding. They trace to source under the shipped comparator, which decodes entities and folds whitespace-class characters on both sides (`code/quote_trace.py`, `code/comparator_symmetry_tests.py`). They are never repaired in place — a decoded copy would no longer match the retained source. |
| 33 | `provenance_section` | 100.0% | Which section of the paper the quote came from. |
| 34 | `null_or_failed_result` | 100.0% | Set where the finding is a null or failed result — deliberately retained, since these are systematically under-published. |
| 35 | `contradicts_finding_ref` | 4.1% | Reference to a finding this one contradicts. |
| 36 | `evidence_stratum` | 100.0% | Evidence stratum label. |
| 37 | `study_quality` | 100.0% | Stated study quality. |
| 38 | `study_type` | 65.3% | Study type as stated. |
| 39 | `n_participants` | 51.4% | Participant count as stated. |
| 40 | `comparator` | 65.3% | Comparator group. |
| 41 | `demographics` | 53.1% | Demographic detail. |
| 42 | `is_duplicate_or_preprint_note` | 3.0% | Note where the source may be a duplicate or preprint of another record. |
| 43 | `contradicts_or_extends` | 56.2% | Whether the finding contradicts or extends prior work. |
| 44 | `limitations_stated` | 60.7% | Limitations the source itself states. |
| 45 | `future_direction` | 62.9% | Future direction the source proposes. |
| 46 | `pmid` | 100.0% | PubMed ID. **The paper key. Count papers with `pmid.nunique()`.** |
| 47 | `doi` | 100.0% | DOI. |
| 48 | `title` | 100.0% | Paper title. |
| 49 | `year` | 100.0% | Publication year. |
| 50 | `journal` | 100.0% | Journal. |
| 51 | `source_stream` | 100.0% | Which query stream retrieved the paper. |
| 52 | `theme` | 100.0% | Extraction theme. Package-specific vocabulary by construction — never compare across packages. |
| 53 | `fulltext_status` | 100.0% | `retrieved-fulltext` / `abstract-only` / `blocked`. **Drives yield ~3x and determines verifiability.** Always stratify on this. |
| 54 | `contact_note` | 6.0% | Contact note. |
| 55 | `chunk_id` | 100.0% | Extraction chunk. Maps to the tier via `chunk_order.parquet`. |
| 56 | `hgnc_id` | 3.1% | HGNC gene identifier. |
| 57 | `ensembl_id` | 3.1% | Ensembl gene identifier. |
| 58 | `gene_resolved` | 100.0% | Whether the gene symbol resolved against an authority. |
| 59 | `entity_ontology_id_resolved` | 15.8% | Resolved ontology identifier. **Meaning differs by tier: authority-derived in Tiers 3-4, model-emitted in Tiers 1-2.** Always read alongside `ontology_id_verification`. |
| 60 | `entity_ontology_label` | 15.8% | The authority's own label for the identifier. Comparing this to `entity` is how identifier correctness was measured offline. |
| 61 | `pathway_id_resolved` | 0.0% | Resolved pathway identifier. **[EMPTY in this package]** |
| 62 | `pathway_label` | 0.0% | Pathway label. **[EMPTY in this package]** |
| 63 | `phenotype_hpo_resolved` | 0.0% | Resolved HPO identifier. **[EMPTY in this package]** |
| 64 | `phenotype_hpo_label` | 0.0% | HPO label. **[EMPTY in this package]** |
| 65 | `source_fidelity` | 0.0% | Retained for forward compatibility. **Single value on many packages — zero information. Not a quality filter that passed.** **[EMPTY in this package]** |
| 66 | `source_route` | 0.0% | How the source text was obtained. **[EMPTY in this package]** |
| 67 | `pmcid` | 0.0% | PubMed Central ID. **[EMPTY in this package]** |
| 68 | `entity_ontology_id_note` | 0.0% | Note field. Effectively empty. **[EMPTY in this package]** |
| 69 | `anatomical_study` | 0.0% | Note field. Effectively empty. **[EMPTY in this package]** |
| 70 | `tier_source` | 100.0% | Which extraction pass produced the row (`t1`/`t2`/`t3`/`t4`). Constant within a package. **[CONSTANT: `t3`]** |
| 71 | `cap_entity_kind` | 100.0% | **Capability flag** (computed): does this row's tier support `entity_kind`? Null means NOT PRESENT, not unknown. **[CONSTANT: `True`]** |
| 72 | `cap_hpo_verified` | 100.0% | **Capability flag**: does this tier carry authority-verified HPO identifiers? **[CONSTANT: `True`]** |
| 73 | `cap_number_in_quote` | 100.0% | **Capability flag**: does this tier carry the `number_in_quote` check? **[CONSTANT: `True`]** |
| 74 | `cap_quote_source_retained` | 100.0% | **Capability flag**: is the quote's own source text still retained? True only in Tier 4. **[CONSTANT: `False`]** |
| 75 | `ontology_id_verification` | 100.0% | **Added by harmonization. Consistent semantics across all five packages — filter on THIS.** `authority_verified` (Tiers 3-4) / `unverified_model_emitted` (Tiers 1-2) / `no_id`. |
| 76 | `ontology_id_match_mode` | 15.8% | **Added by harmonization.** How the identifier was matched (exact label, synonym, …). |
| 77 | `hpo_verification` | 100.0% | **Added by harmonization.** HPO verification status, consistent across packages. |
| 78 | `hpo_id_count_unified` | 100.0% | Number of verified HPO identifiers on the row, unified across packages. |
| 79 | `ontology_id_prefix` | 15.8% | Ontology namespace of the identifier (HGNC, CHEBI, HP, …). |
| 80 | `ontology_id_repaired` | 0.0% | Whether the syntactic repair pass touched this identifier. **Syntactic only — case and namespace. Re-derived nothing from names.** **[EMPTY in this package]** |
| 81 | `ontology_repair_action` | 0.0% | What the repair pass did. **[EMPTY in this package]** |
| 82 | `ontology_id_final` | 0.0% | Identifier after the repair pass. **[EMPTY in this package]** |
| 83 | `ontology_id_source` | 100.0% | **TRAP: inverted semantics across tiers.** `unresolved_nulled` means identifier KEPT in Tier 2 and identifier NULLED in Tiers 3-4. Provenance only — never a filter. See COMPARABILITY.md. |
| 84 | `entity_clean` | 0.0% | Cleaned entity string. **[EMPTY in this package]** |
| 85 | `ontology_label_final` | 0.0% | Final ontology label. **[EMPTY in this package]** |
| 86 | `entity_kind` | 77.9% | Entity type (gene, protein, chemical/metabolite, …). **Tiers 3-4 only** — null means NOT PRESENT in Tiers 1-2. |
| 87 | `phenotype_terms` | 74.7% | Atomic clinical terms split out of the raw symptom string. |
| 88 | `certainty_derived` | 100.0% | Hedge-detection over both `finding_text` and `provenance_quote`: both hedged -> hedged, neither -> confirmed, disagreement -> mixed. Never overwrites `certainty`. |
| 89 | `number_in_quote` | 61.5% | Is the value in `quantitative_detail`/`effect_size` actually present in the quote? ~9.9% of Tier-2 rows fail. **A genuine open question, not a bug to auto-fix.** |
| 90 | `fetch_note` | 100.0% | HTTP status or exception from the fetch, so `blocked` is diagnosable rather than terminal. |
| 91 | `gene_id_source` | 100.0% | Provenance of the gene identifier. |
| 92 | `hpo_ids_verified` | 43.9% | **Authority-verified HPO identifiers, semicolon-delimited.** Multi-value because 43.2% of mappable symptom strings resolve to more than one HPO term. |
| 93 | `hpo_labels_verified` | 43.9% | Labels for the verified HPO identifiers. |
| 94 | `hpo_id_source` | 100.0% | Provenance of the HPO identifiers. |
| 95 | `hpo_id_count` | 100.0% | Count of semicolon-delimited HPO identifiers. Invariant-checked against the string. |
| 96 | `tier` | 100.0% | Numeric tier. **Partially null — use `tier_source` instead.** |
| 97 | `_source_version_id` | 100.0% | Build provenance: which per-tier artifact the row came from. |
| 98 | `canonical_entity` | 68.5% | Canonical entity name. **Tiers 3-4 only in-row.** Join `entity_vocabulary_crosstier.parquet` to canonicalize Tiers 1-2. |
| 99 | `canonical_source` | 100.0% | Which canonicalization rule fired. |
| 100 | `source_literature` | 100.0% | Which condition literature the paper was drawn FROM. Distinct from `condition` (what the finding is about). |
| 101 | `about_condition` | 100.0% | Condition the finding is about, harmonized. |
| 102 | `evidence_scope` | 100.0% | Scope of the evidence. |
| 103 | `query_contamination` | 100.0% | **TRAP: means different things by tier.** Tier 3: abbreviation-collision rows (40, wrong 'ASD'). Tier 4: screening-uncertain rows (1,960). Two different concepts under one name. |
| 104 | `query_contamination_note` | 0.1% | Why the row was flagged. **[CONSTANT: `ASD abbreviation collision: adult spinal deformity / atrial septal defect, not autism spectrum disorder`]** |
| 105 | `screen_verdict_uncertain` | 0.0% | Tier 4: the screen was uncertain whether the paper is in scope. **[EMPTY in this package]** |
| 106 | `screen_verdict_note` | 0.0% | Screening note. **[EMPTY in this package]** |

## Entirely empty in this package

19 columns hold no value on any of the 26,032 rows. **Null here means the
property was NOT CAPTURED by this extraction pass — not that it was measured and found
absent.** They are retained so that this package's schema matches its siblings' and a
pooled read needs no column alignment.

- `anatomical_study` — Note field. Effectively empty.
- `entity_clean` — Cleaned entity string.
- `entity_ontology_id` — Model-emitted ontology identifier. **Tiers 1-2 only.** Never authority-verified. Do not use as a mapping; use `entity_ontology_id_resolved` with `ontology_id_verification`.
- `entity_ontology_id_note` — Note field. Effectively empty.
- `ontology_id_final` — Identifier after the repair pass.
- `ontology_id_repaired` — Whether the syntactic repair pass touched this identifier. **Syntactic only — case and namespace. Re-derived nothing from names.**
- `ontology_label_final` — Final ontology label.
- `ontology_repair_action` — What the repair pass did.
- `pathway_id` — **Tiers 1-2 only, 0.1% filled.** Deprecated; no single GO/Reactome term denotes most mechanism prose.
- `pathway_id_resolved` — Resolved pathway identifier.
- `pathway_label` — Pathway label.
- `phenotype_hpo` — **Model-emitted HPO identifier, Tiers 1-2. ~34% were fabricated.** Do not use. Use `hpo_ids_verified`.
- `phenotype_hpo_label` — HPO label.
- `phenotype_hpo_resolved` — Resolved HPO identifier.
- `pmcid` — PubMed Central ID.
- `screen_verdict_note` — Screening note.
- `screen_verdict_uncertain` — Tier 4: the screen was uncertain whether the paper is in scope.
- `source_fidelity` — Retained for forward compatibility. **Single value on many packages — zero information. Not a quality filter that passed.**
- `source_route` — How the source text was obtained.

## Single-valued in this package

These columns carry exactly one distinct value, so they cannot discriminate anything within
this package. **`source_fidelity` in particular is not a quality filter that passed** — it
is a forward-compatibility placeholder.

| column | its only value |
|---|---|
| `cap_entity_kind` | `True` |
| `cap_hpo_verified` | `True` |
| `cap_number_in_quote` | `True` |
| `cap_quote_source_retained` | `False` |
| `query_contamination_note` | `ASD abbreviation collision: adult spinal deformity / atrial septal defect, not autism spectrum disorder` |
| `tier_source` | `t3` |

## Multi-value columns

`hpo_ids_verified` and `hpo_labels_verified` are **semicolon-delimited**, because 43.2% of
mappable symptom strings resolve to more than one distinct verified HPO term and a
one-id-per-row schema cannot express that. `hpo_id_count` is invariant-checked against the
delimiter count on every build.

```python
df['hpo_list'] = df.hpo_ids_verified.fillna('').str.split(';')
df.explode('hpo_list')   # one row per HPO term
```

In this package, 11,417 rows carry at least one verified HPO identifier.

