# PHASE 0 - FIDELITY GATE REPORT

**Verdict: PASSED.** The reconstructed generator reproduces the shipped tier-1 site JSON exactly.
Phase 1 (combined data) is cleared to proceed.

## Method

Regenerate the **tier-1-only** site JSON from the immutable canonical parquet, then diff against the
JSON currently shipped inside `pots_tier1_publishable.zip`. Exact reproduction was the pass
condition - the same logic as planted-regression QA: prove the tool on the known answer before
trusting it on new data.

Nothing was written to the record or to the live site. Read-only against Layer 1.

## Results

| Output | Result |
|---|---|
| `findings_facets.json` | **EXACT** - 21/21 dictionaries, 26/26 columns, all scalars |
| `text_NN.json` | **EXACT** - 7/7 shards |
| `detail_NN.json` | **EXACT** - 84/84 arrays (7 shards x 12 fields) |
| `papers.json` | **EXACT** - 3,121/3,121 rows |

All 26 facet columns were traced to their source column by exhaustive matching against the parquet,
not assumed from the field names.

## Four rules the gate caught

Each of these broke a first attempt and would have silently corrupted the combined site. This is
what the gate bought:

1. **Dictionary order is first-appearance, not sorted.** Sorting yields the same value set but
   different integer codes - every column mismatches while looking superficially fine.
2. **Truncation is `s[:cap-1].rstrip() + "…"`**, caps 200 (`quote`) / 300 (`lim`, `fut`, `symp`).
   Without `.rstrip()`: 541 mismatches in one shard. A word-boundary cut matched only ~56%.
3. **The paper index uses CANONICAL pmid.** Indexing by raw pmid leaves the 53 merged-duplicate
   rows unmapped.
4. **Null serialization is field-dependent** - `""` for URL/text fields, `False` for
   `is_open_access`, `0` for `cited_by_count`, `null` elsewhere. And a null `finding_text` becomes
   a placeholder built from the relation triple, not a null.

Four detail fields were also mapped to the wrong source column on the first pass
(`limitations_stated` not `limitation_noted`, `comparator` not `comparison_group`,
`provenance_section` not `source_section`, `canonical_ontology_id` not `entity_ontology_id`).
The `quote`, `fut` and `symp` diffs were NOT wrong columns - those were already correct and were
resolved entirely by rule 2 above (the `.rstrip()` truncation).

## Deliverable

`site_generator.py` - the verified emitters, with each gotcha documented at its call site. Ready for
Phase 1 to call on combined tier-1+2 data.

## Not yet reproduced (Phase 1 scope)

`entities.json`, `meta.json`, and the five discovery tables (`associations`, `convergence`,
`contradictions`, `understudied`, `null_results`) plus the embedding shards. Their generator code
was confirmed recoverable from lineage; they were not part of this gate because they are rollups
rather than row-level projections, and a row-level failure was the real risk to retire first.
