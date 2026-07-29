# Tier-2 Runbook — start here

## Step 0: the pilot (do this first)

**18 chunks, 888 papers, ~1.5 hours.** Chunks: 76, 84, 93, 101, 110, 118, 127, 135, 144, 152, 161, 169,
178, 186, 195, 203, 212, 220.

Chosen spread across the full tier-2 range rather than contiguous, because `chunk_order` is
condition-ordered — a contiguous block would test only ME/CFS and tell you nothing about MCAS, EDS,
fibromyalgia, IBS, small-fiber, gastroparesis, rccx or patient-registry papers.

### Go/no-go gate

| Metric | Tier-1 measured | Pilot must clear | If it fails |
|---|---:|---:|---|
| Findings per yielding paper | 11.68 | **>= 8.0** | prompt needs condition-specific tuning |
| Yield fraction (papers with >=1 finding) | 82.5% | **>= 0.60** | check full-text availability, not the prompt |
| Truncation rate | ~0% at 1500 tok | **<= 2%** | raise max_tokens |
| Grounding resolution | 97-100% | **>= 90%** | resolver drift — check API responses |

The 0.60 yield floor is the same `MIN_YIELD` gate `driver.py` already enforces per chunk, so a bad chunk
halts itself. The gate above is for the pilot **as a whole**.

Non-POTS literature genuinely differs — more case series, different journals, different open-access rates.
The pilot exists to measure that before committing 7,238 papers.

## Step 1: run it

    # driver.py is already tuned: N_INFLIGHT=6, MAX_ATTEMPTS=3, MIN_YIELD=0.60,
    # BUDGET_HALT_STREAK=2, papers_per_chunk=50, max_tokens=1500
    # Resumable per chunk — a killed run loses at most one chunk.

Dispatch in waves of ~3 chunks (the Pool C1 lesson: 7 x 8 concurrent LLM calls risks rate-limit errors
being silently counted as parse failures, and batch-level resumability means a lossy batch does not
self-heal).

## Step 2: check the gate

    import pandas as pd, glob
    d = pd.concat([pd.read_parquet(f) for f in glob.glob("chunk_*_findings.parquet")])
    print("findings/paper:", len(d)/d.pmid.nunique())
    print("yield:", d.pmid.nunique()/888)

## Step 3: validate before merging anything

    cd validation
    python -c "
    import pandas as pd, tier2_invariants as inv
    M = pd.read_parquet('../data/tier1_findings.parquet')   # or the merged tier1+2 table
    V = pd.read_parquet('../data/entity_vocabulary.parquet')
    inv.report(inv.check(M, V))"

14 invariants; **all must pass**. `monotonic_*` checks catch a merge that silently drops Tier-1 papers.
`no_canonical_spans_two_kinds` catches the over-merge failure mode.

## Step 4: extend the vocabulary — never recompute it

This is the rule whose violation is hardest to notice. Recomputing shifts existing marker counts for
reasons unrelated to new evidence, silently invalidating anything already published.

    # correct: map only NEW strings, append to the existing vocabulary
    new_strings = set(t2_entities) - set(V.original_string)
    # then append rows; never regenerate mappings for strings already present

Type discipline still needs Sonnet-class or stronger. The failure mode of cheap models here is
over-merging (molecule + its transporter gene + its drug class collapsing into one entity), which is
exactly what destroys count integrity. One call per distinct string, so cost is negligible.

## Step 5: re-freeze the facts, deliberately

    python -c "
    import json, pandas as pd
    # after a legitimate Tier-2 merge, values SHOULD change. Re-freeze with a version bump
    # and record the superseded value. Never edit a frozen number to make a test pass."

Then bump `embeddings_manifest.json` version and **append** new shards — existing shards and row offsets
never change.

## What changes for published numbers

Tier-1 numbers are already citable if you publish the site. When Tier 2 lands they change legitimately.
Decide now: publish Tier 1 and accept a correction obligation, or hold until Tier 2 merges. Either is
defensible; drifting between them is not.

## Full-run projection (after the pilot passes)

145 remaining chunks, 7,238 papers, ~11 hours wall time at the measured ~11 papers/min sustained.
Expected ~69,732 new findings (7,238 x 0.825 yield x 11.68 per paper); upper bound ~84,553 if every
paper yields. Corpus total ~106,191, about 2.9x current. State which yield assumption any quoted number uses.
