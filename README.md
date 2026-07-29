# POTS / Dysautonomia Literature Findings — Tier 1 (v1)

A machine-extracted, structured database of research findings from the POTS and dysautonomia
literature, plus four discovery tables built on top of it (associations, under-studied signals,
contradictions, null results) and a convergence table.

Two things it is meant to be at once: **evidence that the extraction method works**, and a
**working discovery instrument** you can query today.

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

## What is in it

| Table | Rows | What it is |
|---|---|---|
| `data/tier1_findings.parquet` | 36,459 | One row per extracted finding, 89 columns |
| `data/entity_vocabulary.parquet` | 2,019 | Entity surface strings → canonical names, kinds, ontology IDs |
| `data/paper_metadata.parquet` | 3,129 | Source papers with authors, journal, DOI/PubMed links |
| `data/pmid_dedup_map.parquet` | 18 | Duplicate-title paper collapse decisions (8 applied) |
| `data/association_table.parquet` | 555 | Entity co-occurrence pairs with hypergeometric test + BH-FDR |
| `data/understudied_signals.parquet` | 329 | Thin-evidence replication targets |
| `data/contradictions.parquet` | 532 | Direction flips and null-vs-positive conflicts, with moderators |
| `data/null_results.parquet` | 5,324 | Negative, null, and failed results — the usually-invisible half |
| `data/convergence_tier1.parquet` | 308 | Entities pointing the same direction across conditions |
| `data/findings_embeddings_int8.npy` | 36,459 × 384 | Quantized MiniLM-L6-v2 sentence embeddings (14.0 MB) |

CSV mirrors of every table sit alongside the parquet files. `data/field_fill_rates.csv` and
`data/figure_stats.json` hold the measured numbers used in the docs and notebooks.

## Verified numbers

- **36,459 findings** (36,067 pre-split; the growth is compound-entity splitting only — 36,032
  distinct `finding_text` values are unchanged)
- **3,129 paper rows, 3,121 distinct papers.** 9 duplicate-title groups were examined, 8 merged,
  and 1 retained as genuinely distinct papers (see below). Count papers with
  `canonical_pmid.nunique()`, never `pmid.nunique()`.
- **863 canonical entities**, **368 with ontology IDs** (145 HGNC genes, 189 ChEBI chemicals,
  34 MeSH conditions). 1,803 typed vocabulary entries cover 1,977 of the 9,582 distinct entity
  surface strings in the findings — the remaining 7,605 strings were deliberately left unmapped
  (head-only canonicalization); 216 compound strings were split.
- **456 of 547** tested associations significant at BH-FDR q<0.05; **101** cross-kind and
  non-trivial
- **329** under-studied candidates (**198** with ≥2 independent last authors, not
  case-report-only, and headline-eligible)
- **532** contradictions (268 hard direction flips + 264 null-vs-positive; **127** with a
  visible moderator)
- **5,324** null/failed results (3,076 biomarker nulls, 1,340 treatment failures — **315** of
  those at RCT or meta-analysis tier — and 908 diagnostic nulls)
- **308** convergence records, **106** passing the ≥2-non-POTS-paper bar, **45**
  headline-eligible
- Embeddings: int8, 14.0 MB in 7 shards, quantization fidelity mean cosine **0.99997**

### Entity coverage is 29.8%, not half

`entity` and `canonical_entity` are different columns with different coverage, and mixing them
up will make you overestimate entity-based views by about a factor of two:

| Measure | Rows | % of 36,459 | Papers |
|---|---|---|---|
| Original `entity` string present | 19,307 | **53.0%** | 2,494 |
| `canonical_entity` present | 10,858 | **29.8%** | 2,185 |
| Entity string present, no canonical mapping | 8,449 | 23.2% | — |
| No entity at all | 17,152 | 47.0% | — |

Two separate causes: 47.0% of rows name no entity at all (symptom/phenotype findings — by
design), and a further 8,449 rows carry an entity string that was never canonicalized, because
canonicalization was **head-only by deliberate scope decision** (1,803 typed vocabulary entries
against 9,582 distinct strings; 7,605 left unmapped). That tail is genuinely thin — 6,761 of the
unmapped strings occur once and none occurs more than twice — so it does not distort counts.

**So: entity-keyed charts and filters describe ~30% of findings across 2,185 of 3,121 papers,
never "half the corpus."** The 8,449 unmapped-string findings are real results and stay findable
by keyword search on the original string. Absence from an entity rollup is not absence from the
literature. Full per-field fill rates: [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

## How the corpus was built

1. **Search** — PubMed/PMC queries across POTS, dysautonomia and subtype/theme axes, plus
   trial-registry and omics-dataset augmentation, producing a ~14,263-paper corpus.
2. **Tiering** — the corpus was ordered into 286 chunks by condition focus. **Tier 1 is
   chunks 0–75**, the POTS/dysautonomia core. Tiers 2–4 are not extracted.
3. **LLM extraction with grounding** — each paper's full text (or abstract where full text was
   unavailable: `fulltext_status`) was extracted against a fixed schema. Every finding carries a
   `provenance_quote` and `provenance_section` locating it in the source, which is what makes
   spot-checking possible.
4. **Canonicalization** — entity surface strings were normalized, compound strings split
   (`split_derived`), mapped to canonical names with a typed `entity_kind`, and resolved against
   HGNC, ChEBI and MeSH where a confident match existed. Each mapping carries a
   `map_confidence`.
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

5. **Discovery tables** — the four tables were computed from the canonicalized findings with
   explicit, documented statistical filters. See [`docs/METHODS.md`](docs/METHODS.md).

## Quick start

```python
import pandas as pd
f = pd.read_parquet("data/tier1_findings.parquet")
papers = f.canonical_pmid.nunique()          # 3121 — the correct paper count
f[f.evidence_tier.isin(["RCT","meta-analysis"])].finding_type.value_counts()
```

Or open a notebook — they run in Colab with no setup:

- `notebooks/01_load_and_explore.ipynb` — load, shape, fill rates, first look
- `notebooks/02_reproduce_figures.ipynb` — every figure the site shows, numbers printed beside each chart
- `notebooks/03_associations_and_contradictions.ipynb` — associations, under-studied ranking, contradiction moderators, nulls
- `notebooks/04_query_recipes.ipynb` — 12 practical researcher queries with caveats inline

Each notebook has a `DATA_BASE` constant at the top: it points at raw GitHub by default and
falls back to local `data/` when you run inside a clone.

## Limitations

Read [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) before drawing a conclusion. The short version:

- **Automated extraction has errors.** Nothing here has been manually curated end to end.
- **51 low- and ~240 medium-confidence** entity mappings exist. Filter on `map_confidence`.
- **Co-occurrence is not causation.** The association table measures reporting patterns —
  co-mention in the same paper — not biology.
- **Thin evidence includes noise.** The under-studied table is built to surface
  under-replicated signals, so single-lab artifacts and extraction errors are part of what it
  surfaces. That is the point of the table, not a defect, but it means every row needs a human.
- **376 of 532 contradictions** sit under umbrella condition labels and may reflect pooled
  distinct diseases rather than a replication failure (`broad_condition_flag`).
- **Coverage is Tier 1 only.** Absence from this database is not absence from the literature.

## How to cite

**This dataset:**

> POTS/Dysautonomia Literature Findings, Tier 1 v1 (2026). Machine-extracted structured
> findings from 3,121 POTS/dysautonomia papers. [repository URL], accessed [date].

**The underlying papers — please do this.** Every finding row carries `citation_short`,
`authors`, `journal`, `year`, `doi_url` and `pubmed_url`. If a finding matters to your
argument, read and cite the original paper, not this database. This database is a finding aid.

## License

- **Derived structured data** (the extracted fields, canonical entities, discovery tables,
  embeddings): CC-BY-4.0. Attribution required — see [`LICENSE`](LICENSE).
- **`provenance_quote_trunc`**: short verbatim excerpts from the source papers, **copyright of
  their respective publishers**, included for identification and verification only, truncated
  to ≤200 characters and always adjacent to the full citation and link. No license is claimed
  over this text and no bulk quote export is provided.

## Roadmap

Tier 1 is the POTS/dysautonomia core. Tiers 2–4 extend to the related-condition literatures —
ME/CFS, fibromyalgia, EDS/hypermobility, MCAS, IBS, migraine, autism — as their own corpora
rather than as incidental mentions. The embedding shard layout is designed for this: new tiers
append shards and bump the version; existing shards and row offsets never change. Only when a
condition has its own extracted tier can cross-condition claims be made from this data.
