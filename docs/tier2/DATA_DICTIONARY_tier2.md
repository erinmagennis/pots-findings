# DATA DICTIONARY - Tier-2 Companion Bundle

## tier2_findings_canonical.parquet - 36,611 rows x 76 cols

Tier-2 findings with canonicalization applied. Inherits the tier-1 schema (see the tier-1
DATA_DICTIONARY.md for the 65 shared extraction fields) plus these tier-2 additions:

| Column | Type | Meaning |
|---|---|---|
| `_chunk` | int | Chunk id (76–220) the finding was extracted from. Provenance; every row has one. |
| `entity_norm` | str | Lowercased/stripped `entity`. The join key into the vocabulary. Null on entity-free findings. |
| `canonical_entity` | str | Canonical name from vocabulary v1+v2. **Null for unmapped singleton-tail strings** - null means unmapped, NOT absent. |
| `canonical_kind` | str | One of: clinical-sign-or-condition, drug-or-drug-class, gene-or-protein, molecule-or-analyte, other, physiological-measure. |
| `canonical_qualifier` | str | Distinction preserved outside the name (e.g. "supine" vs "standing" for HRV). |
| `vocab_version_used` | str | `v1` (mapped by frozen tier-1 vocab), `v2` (mapped by the tier-2 extension), `v1-compound-unmapped` (v1 lists the string but assigns no canonical because it names several entities), or null (no vocab entry - singleton tail). |
| `canonical_pmid` | str | Paper identity for counting. In tier-2 == raw `pmid` (0 title merges). **Default basis for all paper counts.** |
| `source_literature` | str | Corpus theme of the paper - which condition's literature it came from. |
| `tier` | int | 2 for all rows in this file. |

**Counting note.** `canonical_pmid.nunique()` is the paper basis. `len(df)` is the row basis. A paper
contributes many rows; a sentence may contribute several rows (distinct entities/relations). These are
different questions with different answers - state which you used.

## entity_vocabulary_v2.parquet - 4,219 rows

Same 16 columns as tier-1's `entity_vocabulary.parquet`. Filter on `vocab_version`:
- `v1` - 2,019 rows, **byte-identical to tier-1**, asserted
- `v2` - 2,200 rows added for tier-2 head strings

| Column | Meaning |
|---|---|
| `entity_norm` | Surface string (the join key) |
| `canonical_name` | Canonical entity this string maps to |
| `entity_kind` | Type. No canonical name spans >1 kind (asserted). |
| `entity_qualifier` | Preserved distinction |
| `map_confidence` | high / medium / low - low means the mapper declined to guess |
| `is_compound` | True when the string genuinely lists several distinct entities |
| `rows` / `papers` | Usage counts for this string in tier-2 |
| `map_source` | `sonnet5-tier2-batch` for v2 rows |
| `vocab_version` | `v1` or `v2` |

## crossover_shared_biology.csv - 1,139 entities
Entity-level convergence. `n_conditions`, `n_papers`, `n_findings`, `conditions` (pipe-joined),
`tiers` (`1`, `2`, or `1|2`), `cross_mention_rows`, `within_rows`.

## crossover_shared_biology_detail.csv - 4,820 rows
One row per (entity, source_literature, about_condition). **The scope columns live here:**

| Column | Meaning |
|---|---|
| `source_literature` | Which literature the paper belongs to |
| `about_condition` | Which condition the finding is about |
| `evidence_scope` | `within-literature` (source == about) or `cross-mention` (source != about) |
| `papers` / `findings` | Support at this scope |
| `tiers` | Which tier(s) contributed |

Filter `evidence_scope == 'within-literature'` for primary evidence.

## crossover_explicit_comorbidity_claims.csv - 355 claims
Adjudicated positives. `cand_id`, `pmid`, `condition_a`, `condition_b`, `condition_pair` (sorted, so
A+B == B+A), `direction_adjudicated`, `confidence`, `rationale` (quotes the decisive phrase),
`finding_text`, `provenance_quote`.

## crossover_explicit_comorbidity_pairs.csv - 50 pairs
Rollup: `condition_pair`, `claims`, `papers`, `high_conf`. **`papers` is the honest basis** - `claims`
double-counts a paper making the same assertion twice.

## crossover_shared_mechanism_claims.csv - 138 claims
Same schema as the explicit-comorbidity claims. Shared biology asserted WITHOUT patient co-occurrence.

## crosswalk_entities_tier1_tier2.csv - 2,803 entities
`canonical_entity`, `entity_kind`, `t1_papers`, `t1_findings`, `t2_papers`, `t2_findings`,
`combined_papers`, `presence` (`both` / `tier1_only` / `tier2_only`).
`combined_papers` is **exact** - the tiers share 0 papers.

## crosswalk_papers_tier1_tier2.csv: 6,244 canonical papers
`canonical_pmid`, `in_tier1`, `in_tier2`, `source_literature`, `year`, `journal`.
The repaired crosswalk excludes eight Tier 1 raw PMID aliases that merge into other canonical papers. The
6,252 figure in invariant I4b uses the pre-merge raw-PMID basis and is not the canonical paper count.

## tier2_golden_facts.json - 31 facts
Each fact is `{value, expr, basis, note?}`. **Re-evaluate `expr` rather than quoting `value` from
memory** - that is the whole point of the registry.
