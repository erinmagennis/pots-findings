# Limitations

Read this before drawing a conclusion from this data. None of the items below are hypothetical;
each is measured or structural.

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

## 1. Coverage: Tier 1 is a slice, and absence means nothing

Tier 1 is **chunks 0–75 of a 286-chunk corpus — ~3,121 of ~14,263 papers**. A negative result
against this database ("no papers link X to POTS") is **not** evidence about the literature. It
is evidence about Tier 1.

The related conditions are the sharpest version of this trap. The row counts look substantial —
ME/CFS 136 papers, EDS/hypermobility 146, fibromyalgia 103, MCAS 90, IBS/gut 64, migraine 61,
autism 18 — but each of those numbers counts **POTS/dysautonomia papers that mention the
condition**, not that condition's literature. Any cross-condition statement built on them
describes what POTS researchers say about neighbouring conditions, which is a real but very
different object.

## 2. Extraction is automated and has errors

Findings were extracted by an LLM against a fixed schema, with a `provenance_quote` and
`provenance_section` recorded for each. Grounding makes errors **checkable**; it does not make
them absent. Expect mis-parsed directions, entities attributed to the wrong comparison, effect
sizes lifted from the wrong row of a table, and review articles' descriptions of *other*
studies recorded as findings of the reviewing paper.

**Mitigation available to you:** `provenance_quote_trunc` + `provenance_section` +
`pubmed_url`/`doi_url` on every row. Any finding you intend to rely on can and should be checked
against the source in under a minute. `fulltext_status` tells you whether the extraction saw the
full text (29,910 rows) or only an abstract
(6,535 rows); abstract-only rows are thinner and more
error-prone.

## 3. Entity coverage is 29.8%, not half — and the gap has two separate causes

`canonical_entity` is present on **10,858 of 36,459 rows = 29.8%**. The original `entity`
string is present on **19,307 rows = 53.0%**. These are two different columns with two
different coverage figures, and conflating them overstates entity coverage by about a factor
of two.

The 23.2-point gap between them is **not** one phenomenon:

1. **17,152 rows (47.0%) carry no entity at all.** Symptom-burden, phenotype,
   quality-of-life and study-level findings that name no single measurable entity. Expected
   by design, not a failure.
2. **A further 8,449 rows carry an entity string that got no canonical mapping.**
   Canonicalization was head-only by deliberate scope decision: 2,019 normalized strings in
   the vocabulary (1,803 typed, resolving to 863 canonical entities) against **9,582 distinct
   normalized strings in the findings** — so **7,605 distinct strings were left unmapped**.

The unmapped tail is genuinely a tail: of those 7,605 strings, 6,761 occur exactly once and
**none occurs more than twice**. No unmapped string reaches 3 findings, so the omission does
not distort entity counts — there is no high-frequency entity hiding in the tail.

**Consequences you must respect:**

- **Entity-keyed views cover ~30% of findings, spanning 2,185 of 3,121 papers.** 936 papers
  contribute no canonically-mapped entity at all. Never present an entity-keyed count as a
  total, and always state the denominator.
- **The 8,449 unmapped-string findings are real results and must remain findable** by keyword
  search on `entity` / `entity_norm_original`. An entity-rollup query excludes them; a keyword
  query does not. They must not silently vanish.
- **Absence from an entity rollup is not absence from the literature.** Search the original
  string before concluding the corpus is silent on a marker.

## 4. Entity mappings carry confidence, and some are wrong

Of the typed canonical mappings: **1,512 high, 240 medium, 51 low** confidence. Row-level:
9,627 high, 999 medium,
232 low.

Filter on `map_confidence == "high"` for anything load-bearing. The under-studied table already
applies this filter to its headline flag; the association table deliberately does **not** —
it exposes `map_confidence_a`/`_b` as columns so you can filter yourself.

## 5. Co-occurrence is not causation, and often not even biology

The association table measures one thing: **two entities being mentioned in the same paper**,
tested against a hypergeometric null with BH-FDR correction. A significant pair means the
co-mention is more frequent than chance. It does **not** mean the entities interact.

Some of the strongest pairs are pure reporting convention — the standard POTS drug ladder
(fludrocortisone / midodrine / pyridostigmine / droxidopa / ivabradine) co-occurs because
management reviews list those drugs together. Those rows validate that the pipeline and the
statistic work; they are not discoveries. `trivial_component_link`, `name_level_nested` and
`surface_string_linked` flag the mechanically-explained pairs.

## 6. Thin evidence is thin on purpose — it includes noise

The under-studied table exists to surface signals that are **under-replicated**: few papers, few
independent groups. That population necessarily also contains single-lab artifacts, one-off
measurement flukes, and extraction errors that produced a plausible-looking entity. There is no
filter that removes noise while keeping genuinely-neglected findings, because at 2–3 papers the
two are statistically indistinguishable.

Use it as a **hypothesis queue**, ranked for human triage — not as a list of true-but-ignored
facts. `n_distinct_last_authors`, `case_report_only`, `is_thin` and `direction_agreement` are
the triage columns.

## 7. Contradictions may be pooling artifacts, not replication failures

**376 of 532** contradiction rows are flagged `broad_condition_flag` — the conflict sits under
an umbrella label ("dysautonomia", "general") that may pool genuinely distinct diseases. Two
studies disagreeing about "dysautonomia" may both be right about different patient populations.

**127 of 532** have a `has_visible_moderator` signal (subtype, age group, sex, comparator, assay)
that plausibly explains the disagreement. Check that column before calling anything a failure
to replicate.

## 8. Thin enrichment fields: real but sparse, and not fixable by re-extraction

Measured fill rates:

| Field | Fill | Why it is thin |
|---|---|---|
| `pathway_id` | 0.06% | Papers almost never state a GO/Reactome ID |
| `dataset_accession` | 0.72% | Most clinical papers deposit nothing |
| `phenotype_hpo` | 2.78% | HPO terms are not clinical-paper vocabulary |
| `contradicts_finding_ref` | 4.17% | Papers rarely cite a specific contradicted finding |
| `entity_ontology_id` | 12.67% | Ontology IDs are not in the source text |

These are **low because the source papers do not contain the information** — not because of a
pipeline bug, and re-running extraction will not raise them. Raising them requires external
database joins keyed on the canonical entities (HGNC → pathway membership, entity → HPO
crosswalk), which is downstream work, not extraction work. Treat these five fields as
opportunistic bonuses, never as analysis keys.

## 9. `source_fidelity` is uninformative in Tier 1

Every row is `"high"` — a single value across all 36,459 rows. It is retained for
forward-compatibility with later tiers, where lower-fidelity routes are expected. In Tier 1 it
carries **zero** information and must not be presented as a quality filter that passed.

## 10. Counting rules that will bite you

- **Papers:** use `canonical_pmid.nunique()` = **3,121**. Using `pmid` gives 3,129 and
  double-counts the 8 merged duplicate records. Note the dedup was **validated, not blind**:
  9 duplicate-title groups (18 PMIDs, 179 findings) were examined, 8 were merged (53 findings
  reattributed, none deleted), and **1 was deliberately retained** — two genuinely distinct
  papers sharing the generic title "Post-COVID-19 Postural Orthostatic Tachycardia Syndrome"
  with fully disjoint author lists (PMID 34053992 Ishibashi et al. vs PMID 35470419 Savytskyi
  et al.). Title-only matching would have merged them and destroyed a real independent
  replication. Audit all 9 groups in `data/pmid_dedup_map.parquet` via `merge_applied` /
  `merged_reason`.
- **`split_derived`:** 696 rows were generated by splitting compound entity strings. They
  inflate per-entity paper counts. Report `papers_direct` (excluding `split_derived`) separately
  wherever a paper count is the claim. The discovery tables already carry both.
- **Findings vs distinct text:** 36,459 rows, 36,032 distinct `finding_text`. Row counts are not
  distinct-claim counts.
- **Year skew:** 2025 (11,324 findings) and 2026 (8,009) dominate. This is corpus-construction
  recency bias, not a real surge in research volume.

## 11. Publisher text

`provenance_quote_trunc` is verbatim publisher-copyright text, truncated to ≤200 characters and
always paired with its citation. It is present for verification only. Do not build a quote
corpus from it, and do not redistribute the column separately from its citations.
See [`../LICENSE`](../LICENSE).
