# POTS/Dysautonomia Literature Map - Tier-2 Companion Bundle

**Version:** tier2-v1 · frozen 2026-07-30
**Relationship to tier 1:** ADDITIVE COMPANION. The tier-1 bundle (`pots_tier1_publishable.zip`) is
**unmodified**. Nothing in this bundle edits, replaces, or recomputes a tier-1 artifact. Tier-1 numbers
remain valid at tier-1 scope; combined figures are registered here under new names with their own bases.

## What tier 2 is

Tier 1 covered the core POTS/dysautonomia literature. Tier 2 covers the **related-conditions
expansion**: EDS/hypermobility, ME/CFS, MCAS/mast-cell, RCCX, fibromyalgia, IBS/GI, small-fiber
neuropathy, and patient-reported evidence.

**Scope limit - read this before quoting any number.** Tier-2 extraction covers
**81 of 146 tier-2 chunks (~55%)**. Every tier-2 figure here is a
subset figure, not the complete tier-2 corpus. Per-condition coverage ranges from ~50% to ~57%.

## Headline numbers (each with its basis)

| Quantity | Value |
|---|---|
| Findings (rows) | 36,611 [rows, tier-2 pooled (81 chunks)] |
| Distinct finding text | 36,559 [distinct text] |
| Papers | 3,123 [canonical_pmid] |
| Canonical entities | 2,329 [distinct canonical, post-canonicalization] |
| Entities in >=2 condition literatures | 1,139 [canonical entities in >=2 source literatures, tier-1+2 pooled] |
| Explicit comorbidity claims | 355 [adjudicated rows labeled explicit_comorbidity] |
| Condition pairs | 50 [distinct unordered condition pairs] |
| Combined tier-1+2 papers | 6,244 [canonical_pmid, both sides] |

Never quote a number from this table without its bracketed basis. `tier2_golden_facts.json` carries the
expression that produced each one; re-evaluate rather than restating from memory.

## The two crossover tables are DIFFERENT CLAIMS - do not merge them

**1. Shared biology** (`crossover_shared_biology.csv`) - a canonical entity with findings in two or
more condition literatures. This is *convergence*, not comorbidity: it says researchers in several
fields independently measured the same molecule, not that patients have both conditions.

**2. Explicit comorbidity** (`crossover_explicit_comorbidity_claims.csv`) - findings whose text
asserts that patients with condition A also have condition B. Every row was adjudicated by a
strong model against a strict rubric; **151 of
644 candidates (23.4%) were REJECTED** as passing
mentions, differential-diagnosis lists, exclusion criteria, or methods notes.

A third file, `crossover_shared_mechanism_claims.csv`, holds
138 findings that link two conditions via shared
biology *without* asserting co-occurrence - the middle category.

## Scope honesty: `evidence_scope`

Every row of the shared-biology detail table carries three columns that keep the asymmetry visible:

- `source_literature` - which condition's literature the paper belongs to
- `about_condition` - which condition the finding is about
- `evidence_scope` - `within-literature` when they match, `cross-mention` when they differ

A `cross-mention` row is **an EDS paper's statement about POTS**, which is weaker evidence about POTS
than a POTS paper would be. Filter on `evidence_scope == 'within-literature'` for primary evidence.
The caveat lives in the data, not in prose someone has to remember.

## Public export note

The current public finding files omit the undocumented `_blob` processing helper. No supplied website,
verification script, or documented analysis consumes it, and it reproduced complete provenance text in some
rows. Before a later tier reintroduces it, document what it was intended to support, how it was generated, and
which downstream step requires it.

The working `provenance_quote` exists to check extraction accuracy and locate the source passage. The website
uses excerpts capped at 200 characters. Verbatim source text remains third-party material outside the project's
CC BY license.

## Known undercount (stated, not hidden)

Canonicalization mapped the **head** of the tier-2 entity distribution: 2,200
strings appearing >=2 times, covering 12,951 of
21,264 entity-bearing rows (60.9%). The unmapped tail is
8,296 rows of strings that each appear exactly once.

We verified this cannot distort the crossover analysis: **zero of the 8,296 singleton strings span two
or more conditions**, so none could have become a convergence hit. A fuzzy-match audit found ~3.8% of
singletons are near-duplicates of a head string (~315 strings), each capable of adding at most one
paper of support. That residual is the known undercount.

## Files

**Data**
- `tier2_findings_canonical.parquet` - 36,611 findings, canonicalized, with
  `canonical_entity`, `canonical_kind`, `canonical_pmid`, `source_literature`, `vocab_version_used`
- `entity_vocabulary_v2.parquet` - 2,019 v1 rows (**unchanged**) +
  2,200 v2 rows
- `crossover_shared_biology.csv` / `_detail.csv` - convergence, entity level / entity x condition
- `crossover_explicit_comorbidity_pairs.csv` / `_claims.csv` - adjudicated comorbidity
- `crossover_shared_mechanism_claims.csv` - shared-mechanism middle category
- `crosswalk_entities_tier1_tier2.csv` / `crosswalk_papers_tier1_tier2.csv` - join tier 1 to tier 2

**QA**
- `tier2_qa_report.json`, `tier2_invariants.csv`, `tier2_field_fill_rates.csv`
- `floor12_gate_summary.csv`, `push6_gate_summary.csv` + per-chunk stats

**Provenance**
- `tier2_golden_facts.json` - 31 basis-explicit facts
- `METHODS.md`, `LIMITATIONS.md`, `DATA_DICTIONARY_tier2.md`

## Not in this bundle

**Figures are deliberately absent.** Regenerating the tier-1 figure set on combined data was scoped
out rather than half-done. The tier-1 figures remain valid at tier-1 scope in their original bundle.
