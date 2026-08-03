# METHODS - Tier-2 Extraction, Canonicalization, and Crossover Analysis

## 1. Corpus and chunking
Tier-2 spans chunk_ids 76–220 of the chunk order (146 chunks, ~50 papers each), drawn from the
augmentation streams for EDS/hypermobility, ME/CFS, MCAS, RCCX, fibromyalgia, IBS, small-fiber
neuropathy, and patient registries. **81 chunks were extracted** (3,123 papers).

## 2. Extraction
Per-chunk extraction with a schema-v5 prompt. Model **claude-sonnet-5** for every extraction call,
max_tokens 32,000 (full text) / 8,000 (abstract). No haiku-class model was used anywhere in the
extraction path: cheaper models over-merge entities (collapsing a molecule, its transporter gene, and
its drug class), which destroys count integrity.

Full text was fetched where available (~58% of papers); the remainder are abstract-only. Truncated
responses entered a continuation loop (up to 3 continuations).

### Extraction gate
Every chunk had to clear four metrics before acceptance. Truncation is reported on **two bases** that
must not be collapsed:

| Metric | Floor | Floor-12 run | Push-6 run |
|---|---|---|---|
| Findings per yielding paper | >=8.0 | 12.52 | 13.89 |
| Yield fraction (distinct pmid / 50) | >=0.60 | 0.847 | 0.817 |
| Truncation - continuation-trigger rate | informational | 0.148 | 0.130 |
| Truncation - **data-loss** rate (parse_fail/papers) | ~0.00 | **0.000** | **0.000** |
| Grounding resolution | >=0.90 | 0.971 | 0.967 |

The trigger rate says how many papers hit the token ceiling and continued; the data-loss rate says how
many findings were actually lost. Both runs lost nothing.

## 3. QA invariants
Eight invariants, all passing: text conservation on pooling, no orphaned pmids, complete chunk
provenance, monotonicity of combined counts vs tier-1, full-row duplicate absence, findings-per-paper
band, and a text-sharing check.

The suite was **verified live** by planting deliberate regressions (injected duplicate rows, nulled
provenance, an orphan pmid); it caught all of them. An invariant that has never failed has not been tested.

**One invariant was corrected during QA.** A duplicate check keyed on `(pmid, finding_text, chunk)`
flagged 47 groups. Inspection showed **all 47 differ in >=1 field** (entity, relation subject/object,
pathway) - they are distinct findings extracted from one summary sentence, not duplicates. The key was
corrected to the full row. Reporting the original 47 as duplicates would have been a false defect.

## 4. Entity canonicalization (additive)
Tier-2 introduced 10,969 distinct raw entity strings, of which
only 473 already existed in vocabulary v1.

**Head-only mapping.** The 2,200 strings appearing >=2 times were mapped
by 25 parallel sub-agents on claude-sonnet-5, each given the type-discipline rule explicitly. The
8,296 single-occurrence strings were left unmapped by design.

**Validation before writing:** 2,200/2,200 strings returned, 0 missing, 0 invented, 0 duplicated,
0 collisions with v1. Fold ratio **1.1017** strings per canonical entity, versus
tier-1's 2.34 - the workers under-merged, which is the safe direction of error.

**Type discipline enforced mechanically.** After mapping, 4 canonical names spanned more than one
`entity_kind`; all four were a protein/analyte-activity pair and were unified with the distinction moved
to `entity_qualifier`. A further 6 rows disagreed with v1's kind for a shared canonical name; **v2
deferred to frozen v1 in every case** (e.g. CoQ10 stays `molecule-or-analyte`). Final state: **0 canonical
names span more than one kind** across the combined vocabulary.

**v1 immutability asserted twice** with `pandas.testing.assert_frame_equal` - before and after the
realignment - confirming all 2,019 v1 rows are byte-identical.

## 5. Crossover analysis
Two independent analyses, deliberately kept separate.

**Shared biology.** Canonical entities with findings in >=2 `source_literature` values, pooled across
tier 1 and tier 2: **1,139 entities**
(299 span >=4 conditions;
389 appear in both tiers). Each row carries
`source_literature`, `about_condition`, and the derived `evidence_scope` flag.

**Explicit comorbidity.** Rows naming >=2 conditions AND carrying a co-occurrence cue
(644 candidates) were adjudicated by 23 sub-agents on
claude-sonnet-5 against a three-way rubric (explicit_comorbidity / shared_mechanism / neither), with
instructions to treat passing mentions, differential-diagnosis lists, and exclusion criteria as
`neither`. Result: 355 explicit claims,
138 shared-mechanism,
151 rejected (23.4%).

**19% of comorbidity-type findings carry no entity**, so an
entity-keyed analysis would have missed most of this signal. The candidate screen therefore ran on
finding text, not on the entity column.

## 6. Models used
- Extraction: claude-sonnet-5 (mandated; no cheaper model in the extraction path)
- Entity canonicalization: claude-sonnet-5 x 25 sub-agents
- Comorbidity adjudication: claude-sonnet-5 x 23 sub-agents
- Orchestration/QA/analysis: deterministic pandas in-kernel (no model cost)
