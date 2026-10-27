# Methods: POTS findings v1.2, package 1 of 5: POTS and dysautonomia core literature (36,067 findings, 3,129 papers)

## What this package is

36,067 structured findings extracted from 3,129 papers by a large language
model reading each paper's abstract or full text, one paper at a time, into a pinned schema.

The corpus was assembled by keyword query against PubMed and Europe PMC across the POTS,
dysautonomia and comorbid-condition literatures, deduplicated, and split into 286
50-paper chunks. Chunks were assigned to four tiers by topic. This package holds
chunks 0–75.

## Pipeline

| | |
|---|---|
| extraction model | `claude-sonnet-5` |
| prompt | `code/schema_v5_extraction_prompt.txt` (pinned, shipped) |
| pipeline | `code/extraction_pipeline.py` (pinned, shipped) |
| driver | `code/driver.py` (pinned, shipped) |
| full-text source | Europe PMC REST |
| fetch pacing | 0.9 s at 3 concurrent workers (~3.3 req/s) |
| papers per chunk | 50 |

**Do not raise the fetch concurrency.** Europe PMC rate-limits on aggregate concurrency:
3 workers at 0.9 s produced ~0–3% blocked papers, while 8.5 req/s produced up to 92%
blocked. That is the whole reason for the pacing constant.

### Specific to this pass

- Identifiers were requested FROM THE MODEL. This is the defect that Tiers 3-4 fixed.
- Full text discarded after extraction.
- Accept-header bug present: some papers silently downgraded to abstract-only.

## Identifier grounding

**The extraction model was asked to emit ontology identifiers directly. This was a mistake,
and it is the central quality limitation of this package.**

There is no reasoning path from an entity name to an arbitrary integer (only recall) and a
model has no introspective signal for 'do I know this integer?'. The prompt said not to
invent identifiers, which cannot work. Measured outcome: `anaphylaxis` → *Liver abscess*,
`IgE` → *Iguanas*.

A later repair pass normalized case and namespaces on 4.8% of rows. **That pass was
syntactic and re-derived nothing from names**: zero rows in this package carry a resolved
identifier without a model-emitted one, so no identifier here was ever independently
derived from an entity name.

Measured `id_denotes_entity_rate`: **0.578** (a lower bound, the
adjudicator over-calls DIFFERENT by ~17%). Tiers 3 and 4, which emit names only and resolve
afterwards, score 0.986 and 0.998.

The sentences above describe v1.0/v1.1 and are kept as history. In v1.2 the model-emitted ids were
re-grounded against their authorities row by row:

**v1.2 (2026-10-21): every model-emitted identifier in this package was looked up by id at its minting
authority (HGNC via MyGene, ChEBI via OLS4, MeSH via NLM) and its label and full synonym list compared with the
entity name; names were also resolved forward to obtain the correct id where one exists. No model was involved.**

Of the 4,373 rows that carried a model-emitted id in v1.1: **2,385 denoted their entity** and are now tagged
`authority_verified_retrospective` with the match mode recorded (compound_partial 110, exact 1,255, exact_relaxed 398, synonym 622); **1,161 ids were replaced** by the id the
entity name resolves to (exact label or authority synonym; `ontology_id_source` says so); **827 were withheld** (`id_withheld_unverified_v1.2`:
the id denoted a different entity and the name did not resolve). The original model id is preserved on every affected row in
`ontology_id_v11_model_emitted`; on replaced rows `entity_ontology_label` / `ontology_label_final` carry the NEW id's label, fetched by id from the authority. Nothing else changed: no row was added or removed and no other column was edited.

Measured on this package's full population: **54.5% of the model-emitted ids denoted their entity**; the
rest existed but pointed at a neighbouring gene, a related compound or a sibling concept, near-miss assignment, not fabrication.
The v1.1 figure quoted below was an adjudicated SAMPLE and is kept for the record. Full method and corpus-wide numbers: `annotations/POTS_MODEL_ID_BENCHMARK.md`.


## Quote provenance

Every finding carries the verbatim source span it was drawn from. Traceability is measured by
`code/quote_trace.py`: exact substring match, or ≥60% 8-shingle overlap after normalization.

**The matcher refuses to report a rate without its negative control.** The control pairs each
quote with a *different* paper's text; a working matcher scores ~0%. Every stratum of every
package scored 0.0% wrong-paper false positives.

This is not a formality. A traceability check once read 100% because the caller did `if tr:`
on a truthy tuple, the wrong-paper control read 400/400 and exposed it.

**Superscripts are deliberately not normalized.** Normalizing `I2` against `I-squared` drops
the census from 99.52% to 99.04%, so the raw form is retained.

Body text was discarded after extraction, so only abstract-derived rows
(6,536, 18.12%) could be censused against their own
source. In v1.1 every paper's source was re-fetched from Europe PMC (3 workers, 0.9 s pacing) and every quote
re-checked with the same comparator, each stratum with its own wrong-paper control; results ship as
`annotations/quote_retrofit_*.parquet` and `annotations/RETROFIT_REPORT.md`. The fetched text was deleted after the census.

## Validation

Four families of check, run after every merge step, shipped in `code/tier3_invariants.py` and
`code/tier3_invariants_ext.py` and re-runnable via `code/verify_package.py`:

1. **Schema completeness**: required columns present.
2. **Conservation**: no chunk silently absent, no chunk exceeding its paper allotment.
3. **Monotonicity**: a pass that adds must never shrink counts.
4. **No model-emitted identifiers**: no id-shaped string in any name field.
5. **Identifier provenance**: every non-null identifier carries a source tag.
6. **Enum drift**: flagged, never coerced.
7. **Duplicates**: on the FULL row. A loose key flags legitimate distinct findings drawn from
   one summary sentence, which was a false defect reading in Tier 2.
8. **HPO multi-value consistency**: `hpo_id_count` equals the delimiter count.
9. **Authority/prefix agreement**: an identifier's prefix must match the authority its
   provenance names. Added after an audit found 49 rows claiming `authority_lookup_ols_hp`
   while holding GO/PATO/MPATH ids: the ids were right, the provenance CLAIM was wrong, and
   the eight-check suite could not see it because it only verified that a source tag exists,
   never that it agrees with the identifier it labels.

**On this package: 8 of 9 pass.**
The failures are pre-existing properties of this extraction pass, characterized in the
README. They are shipped as failures rather than suppressed: a suite tuned until it passes
is not a suite.

**The suite was verified by planting regressions**, not by running it on data that happened to
pass. `verify_package.py --self-test` re-plants six and asserts each is still caught.

## What validation does NOT cover

Everything above tests **well-formedness**: quotes are real text from the right paper,
identifiers carry authority provenance, counts are conserved, enums are flagged. **None of it
tests whether a finding correctly interprets its source.**

That requires a human reader. An LLM adjudicator shares the extractor's blind spots, so it
cannot substitute. A 200-row fidelity worksheet with pre-registered thresholds is drawn and
unscored.

## Reproducing

```
python code/verify_package.py --self-test     # validate the shipped slice
```

Re-running extraction requires network access to Europe PMC and an API key for the
extraction model. The pinned pipeline, prompt and driver are in `code/`; `data/chunk_order.parquet`
carries the paper→chunk→tier assignment for all 14,263 corpus papers, so any chunk range can
be re-dispatched. Hold the pacing constants.

