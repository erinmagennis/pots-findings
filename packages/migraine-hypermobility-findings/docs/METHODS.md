# Methods: POTS findings v1.2, package 5 of 5: migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS (15,646 findings, 1,091 papers)

## What this package is

15,646 structured findings extracted from 1,091 papers by a large language
model reading each paper's abstract or full text, one paper at a time, into a pinned schema.

The corpus was assembled by keyword query against PubMed and Europe PMC across the POTS,
dysautonomia and comorbid-condition literatures, deduplicated, and split into 286
50-paper chunks. Chunks were assigned to four tiers by topic. This package holds
chunks 256–285.

## Pipeline

| | |
|---|---|
| extraction model | `claude-sonnet-5` |
| prompt | `code/tier4_prompt.txt` (pinned, shipped) |
| pipeline | `code/tier4_pipeline.py` (pinned, shipped) |
| driver | `code/tier4_driver.py` (pinned, shipped) |
| full-text source | Europe PMC REST |
| fetch pacing | 0.9 s at 3 concurrent workers (~3.3 req/s) |
| papers per chunk | 50 |

**Do not raise the fetch concurrency.** Europe PMC rate-limits on aggregate concurrency:
3 workers at 0.9 s produced ~0–3% blocked papers, while 8.5 req/s produced up to 92%
blocked. That is the whole reason for the pacing constant.

### Specific to this pass

- **Body text RETAINED** in gzipped chunk archives. This is why Tier 4 is the only package with 100% quote verifiability.
- Papers pre-screened by a rule+LLM instrument before extraction, because Tier 4's themes sit at the corpus boundary.
- Screening instrument was itself repaired mid-run: a closed in-scope condition list read as exhaustive and the model excluded familial dysautonomia from a dysautonomia corpus (303 off-topic vs the rule arm's 20). The 303-vs-20 disagreement was the tell that the instrument was broken, not the papers.
- All 9 invariants pass.

## Identifier grounding

The extraction model was **never asked for an identifier**. It emitted entity names and gene
symbols; a multi-authority resolver (OLS4 + UniProt, `code/multi_authority_resolver.py`)
looked every identifier up afterwards from the name, storing the authority's own label
alongside it so that correctness could be audited offline with zero API calls.

This is why this package scores
**0.998** on `id_denotes_entity_rate` against Tier 1's 0.578.

Fuzzy matches were **adjudicated, never accepted**: 59% of fuzzy OLS4 HPO matches were
wrong, and accepting them would have reproduced the fabrication defect with a false
'authority verified' provenance.

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

Body text was retained, so this package's census covers **all** rows against their own
source. Every other package could only census its abstract-derived rows.

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

**On this package: 9 of 9 pass.**

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

