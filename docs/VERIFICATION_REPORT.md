# Verification & Limitations Report — Tier-1 MVP

**Date:** 2026-07-29 · **Data version:** tier1-v1 · **Verifier:** independent recomputation from source parquet

## 1. What was verified and how

Every headline number displayed on the site, in the repo docs, and in the write-up was **recomputed from
`tier1_findings.parquet` and the five discovery tables** in a session that did not produce them, then
diffed against what the deliverables assert. This is a reconciliation, not a restatement.

### Result: 23/23 headline numbers reconcile exactly. Zero mismatches.

| Check | Measured | Asserted | Result |
|---|---:|---:|---|
| Findings rows | 36,459 | 36,459 | PASS |
| Distinct finding_text | 36,032 | 36,032 | PASS |
| PMIDs | 3,129 | 3,129 | PASS |
| Distinct canonical papers | 3,121 | 3,121 | PASS |
| Canonical entities | 863 | 863 | PASS |
| canonical_entity coverage | 29.8% | 29.8% | PASS |
| entity (original) coverage | 53.0% | 53.0% | PASS |
| Entity string but no canonical | 8,449 | 8,449 | PASS |
| Non-split rows | 35,763 | 35,763 | PASS |
| Quote field coverage | 100.0% | 100.0% | PASS |
| Max quote length | 200 | 200 | PASS |
| Papers with >=1 canonical entity | 2,185 | 2,185 | PASS |
| POTS findings | 5,078 | 5,078 | PASS |
| RCT-tier findings | 877 | 877 | PASS |
| Significant associations (BH-FDR q<0.05) | 456 | 456 | PASS |
| Under-studied candidates | 329 | 329 | PASS |
| Contradictions | 532 | 532 | PASS |
| Hard direction flips | 268 | 268 | PASS |
| With visible moderator | 127 | 127 | PASS |
| Null/failed results | 5,324 | 5,324 | PASS |
| Treatment failures | 1,340 | 1,340 | PASS |
| Convergence passing non-POTS bar | 106 | 106 | PASS |
| Paper author coverage | 99.9% | 99.9% | PASS |

### Copyright / quote handling — verified
- 17,802 quote fields inspected across all 24 shipped site data files: **max length exactly 200 chars,
  zero violations.**
- The repo's exported findings table carries **`provenance_quote_trunc` only** — the full verbatim
  `provenance_quote` column is NOT in the public export. Truncation was applied to the data, not merely
  to the display layer.
- No file named or structured as a bulk quote export exists in either bundle.
- Every quote surface is adjacent to its citation and a resolvable DOI/PubMed link.

### Site bundle — verified
12 HTML pages, 17 JS modules, 7 int8 embedding shards, 70 files, 23.9 MB zipped.
Semantic search was verified by the build track to reproduce Python `sentence-transformers` query vectors
at **cosine 1.000000** and **10/10 top-10 ranking overlap on all 5 test queries** — i.e. the browser runs
the same all-MiniLM-L6-v2 model, so ranking is exact rather than approximate.

The rejected bag-of-terms approximation was measured across 6 queries at **3, 3, 7, 7, 3 and 8 of 10**
top-10 overlap (mean 5.2/10; query-vector cosine 0.46-0.93). Single-concept queries did well; compositional
ones ("norepinephrine elevated in POTS", "heart rate variability reduced", "ivabradine treatment outcome")
were the 3/10 cases, because a bag of term vectors cannot represent word order or relations. Elsewhere I
summarised this as "3/10", which was the minimum rather than the result — the honest summary is a 5.2/10
mean with a floor of 3/10, still well short of the real model's 10/10. Graceful degradation confirmed:
with the model CDN blocked, keyword search still works and the UI says semantic search is unavailable.

## 2. Corrections made during the build (all propagated)

Four errors originated in **my own briefing** and were caught by verification, not by assumption:

1. **Entity coverage was overstated.** I stated canonical_entity coverage as ~52%. Measured: **29.8%**.
   The 53.0% figure describes the *original* entity string. Two distinct gaps exist — 17,152 rows carry no
   entity at all, and a further 8,449 carry a string that received no canonical mapping. Every surface now
   states both numbers as separate things.
2. **A real bug this surfaced:** the 8,449 unmapped-entity rows were initially **not searchable by their own
   string**. Fixed — they are now keyword-findable and tagged "not canonicalized" in the UI.
3. **Duplicate-collapse phrasing.** "8 duplicate papers" understated the work: **9 groups examined, 8 merged,
   1 retained as genuinely distinct** (a generic title shared by two papers with disjoint author lists —
   merging would have destroyed a real independent replication).
4. **The "strings merged" column in my chat summary was wrong on four rows** — and it is the same class of
   error as #1, appearing in the very summary meant to report on it. I quoted HF power 34 / SDNN 41 /
   RMSSD 34 / LF power 22. Neither of the two defensible bases gives those numbers:

   | Canonical | Distinct strings **in the findings table** | **Vocabulary entries** | What I wrote |
   |---|---:|---:|---:|
   | hf power | 36 | 25 | 34 |
   | sdnn | 44 | 19 | 41 |
   | rmssd | 40 | 18 | 34 |
   | lf power | 23 | 16 | 22 |

   The figures I used came from an earlier HRV reconciliation that counted something else again. The paper
   counts in the same table (49/80/70/28) were correct and reproduce exactly. Corrected basis: **strings
   observed in the findings table**, which is what "how many surface forms did this fold in" means to a
   reader. This is logged rather than quietly fixed because it is direct evidence that the golden-facts
   mechanism in §5 is necessary — I made the identical mistake while writing the report about the mistake.

Additional reconciliations found by the build tracks:
- **1,803 vs 1,977 mapped strings**: 1,803 is a vocabulary-level count (2,019 entries = 1,803 typed + 216
  compound); **1,977 distinct strings** actually resolve to a canonical, and 7,605 do not (sums to 9,582).
- **198 vs 297 under-studied**: 297 rows satisfy ">=2 independent last authors and not case-report-only";
  198 is that predicate *plus* headline_eligible. Both are surfaced and labelled.
- **Ontology sources were pooled**: corrected to per-source counts — 189 ChEBI, 144 HGNC, 34 MeSH,
  1 NCBIGene (sums to 368). HGNC and NCBIGene are distinct databases and are no longer merged.
- **Paper-count basis**: norepinephrine is 177 papers on raw pmid / 176 on canonical_pmid (direct-only),
  and 195/194 including split-derived rows. All four are real; the basis is now always stated.

## 3. Limitations — read before using this

### Scope (the big one)
Tier 1 is **POTS/dysautonomia only** — chunks 0-75 of a 286-chunk corpus, **3,121 of ~14,263 papers (~22%)**.
ME/CFS (136 papers), EDS (146), fibromyalgia (103), MCAS (90), IBS (64), migraine (61), and autism (18)
appear **only as incidental mentions inside POTS/dysautonomia papers**. A count of "ME/CFS findings" here is
a count of what POTS researchers said about ME/CFS in passing. **This is not yet a cross-condition resource**,
and the cross-condition convergence question the project exists to answer requires Tier 2.

### Entity coverage
`canonical_entity` covers **29.8% of findings across 2,185 of 3,121 papers**. Entity-based charts, filters,
and rollups describe that subset only. Rows without an entity (47%) are symptom/phenotype findings — real
findings, deliberately not entity-typed.

The unmapped tail is defensible: of 7,605 unmapped strings, **6,761 occur exactly once and no unmapped string
exceeds 2 rows**. The head-only decision therefore cannot distort entity counts.

### Evidence quality
Bottom-heavy: cohort 8,239 · cross-sectional 7,009 · review/expert-opinion 6,507 · case-report 3,777 ·
case-series 3,239 · case-control 3,184 · mechanistic 2,787 · **RCT 877** · **meta-analysis 840**.
Only 226 papers contribute a meta-analysis-tier finding and 189 an RCT-tier finding. The high-tier layer is
thin — and it is the layer to trust.

### Method-specific caveats
- **Associations are largely reporting convention.** The top of the list (HF/LF power, systolic/diastolic BP,
  fludrocortisone/midodrine) reflects what gets measured or prescribed together — 136 drug-drug and 118
  measure-measure pairs. The informative layer is the **101 cross-kind pairs**. Recovering known pharmacology
  (tafamidis-transthyretin, hemin-HMBS, L-serine-SPTLC1) is a validation signal, not a discovery.
- **61 of the 127 contradiction moderators are `fulltext_status`** — an extraction artifact (one side read
  from full text, the other from an abstract), never a patient difference. **73 have a non-artifact moderator.**
- **376 of 532 contradictions sit under umbrella condition labels** where opposing directions may reflect
  pooled distinct diseases (diabetic autonomic neuropathy vs Parkinson's dysautonomia vs POTS) rather than
  replication failure.
- **Under-studied signals are hypothesis generation, not results.** Median support 3 papers. Thin evidence
  includes noise and single-lab artifacts.
- **51 low- and 240 medium-confidence entity mappings** exist; filter on `map_confidence` for load-bearing work.
- **Ontology IDs are enrichment, not a key** — 368 of 863 canonicals. All 170 physiological-measure canonicals
  have none by design: HRV indices and orthostatic BP deltas have no genuine ChEBI/HGNC/MeSH term, and forcing
  a match would be worse than leaving them unresolved.
- **Machine extraction has errors.** Direction labels, evidence tiers, and effect descriptions are model
  judgments over source text, not human-adjudicated per row.

### Not medical advice
Research information only. No diagnostic or treatment guidance, nothing tailored to any individual. Decisions
about care belong to a qualified clinician with the full clinical picture.

## 4. Next step, and how it extends without breaking anything

**Tier 2 extraction (7,243 papers: ME/CFS, MCAS, EDS, fibromyalgia, IBS, small-fiber, gastroparesis) is the
single highest-value next action** — it is what turns this from a POTS resource into the cross-condition
instrument the project is for. Projected at Tier-1 rates: ~+99,500 findings, ~135,600 total. **[SUPERSEDED — see docs/TIER2_HANDOFF.md: the canonical-basis projection is ~69,700 new / ~106,200 total; this figure used a pre-canonicalization basis.]**

The build is designed so Tier 2 extends rather than rebuilds:
- **`entity_vocabulary.parquet` is versioned and extensible.** Tier 2 must EXTEND it, not recompute it —
  recomputing would shift existing marker counts for reasons unrelated to new evidence.
- **Embedding shards are append-only.** Existing shards and row offsets never change; new tiers add shards
  and bump the manifest version. Tier-1 is 14 MB / 7 shards; full corpus projects to ~52 MB / ~23 shards.
- **Schema trim already decided:** drop `anatomical_study` and `entity_ontology_id_note` (both 0.0% filled);
  demote `pathway_id` (0.1%), `dataset_accession` (0.7%), `phenotype_hpo` (2.8%) to opportunistic enrichment.
  These are thin because papers rarely state them — not a pipeline bug, and not fixable by re-extraction.
  They require external database joins keyed on canonical entities.
