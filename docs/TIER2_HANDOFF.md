# Tier-2 Process Handoff — what Tier 1 taught us, and the machinery that fixes it

## The diagnosis

Six numbers in the Tier-1 briefing were wrong. **None was a hallucination.** Every one was a value that is
correct under some counting basis and wrong under the one stated:

| Question | Defensible answers | Basis that distinguishes them |
|---|---|---|
| norepinephrine papers? | 176 / 177 / 194 / 195 | canonical_pmid vs raw pmid x direct-only vs including split-derived |
| entity coverage? | 29.8% / 52.0% / 53.0% | canonical col vs original col x post-split vs pre-split rows |
| strings folded into `hf power`? | 36 / 25 | strings seen in findings table vs vocabulary rows |
| duplicate papers? | 9 / 8 | groups examined vs groups merged |

Prose cannot carry a basis. Quoting from memory silently picks one. That is the whole failure mode, and it
recurred **while writing the report about itself** — the strings-merged column was wrong in the very summary
meant to document the fix. Discipline alone demonstrably does not work here; the fix has to be mechanical.

## The machinery (built, tested, in this repo)

### 1. `tier1_golden_facts.json` — 36 facts, each with its expression and basis
Every fact stores the pandas expression that produced it plus a human-readable basis string. Numbers are
never stored alone.

### 2. `tier2_facts.py` — an accessor that refuses to yield a bare number
```python
facts = Facts("tier1_golden_facts.json", M=findings, V=vocab, ...)
facts.cite("papers_canonical")      # -> "3,121 [canonical_pmid]"
int(facts["pct_entity_canonical"])  # -> BasisError: refusing to yield a bare int
```
Two guarantees:
- **Basis travels with the number.** `.cite()` is the only sanctioned path into prose; `int()` raises.
- **No stale numbers.** Every read re-evaluates against the live table. If a value has drifted from frozen,
  you get `DriftError` naming both values — verified to fire on a simulated merge that dropped papers.

Where competing bases exist, both are named facts (`strings_folded::hf_power` = 36,
`vocab_rows::hf_power` = 25). The ambiguity is represented rather than resolved by guesswork.

### 3. `tier2_invariants.py` — 14 checks, run after every merge step
Verified to catch **7/7 planted regressions**, each mimicking a real Tier-1 failure mode:

| Planted bug | Caught by |
|---|---|
| Over-merge gene into molecule (the cheap-model failure) | `no_canonical_spans_two_kinds` |
| Canonical spanning two entity kinds | `no_canonical_spans_two_kinds` |
| Quote exceeding 200 chars | `quote_cap_200` |
| Full verbatim column leaking into export | `no_full_quote_in_export` |
| Tier 2 silently dropping Tier-1 papers | 5 checks incl. `monotonic_papers_canonical` |
| Null canonical_pmid from a bad join | `no_orphan_canonical_pmid` |
| A "split" that produced only one entity | `split_groups_have_ge2_entities` |

Note one check was itself wrong on first write (it assumed a split leaves an unsplit survivor; splits
*replace* the source row, so all siblings are flagged). Caught by running it against real data. **Assert
against the data, not against your model of the data.**

## Rules for Tier 2

1. **Never state a count without its basis.** Use `facts.cite()`. Default basis for papers is
   `canonical_pmid.nunique()`, direct-only.
2. **Run the invariants after every merge/canonicalization step**, not once at the end. A `DriftError` or
   failed monotonicity check blocks the step.
3. **EXTEND the vocabulary, never recompute it.** Recomputing shifts existing marker counts for reasons
   unrelated to new evidence, which breaks any published number.
4. **Append-only embedding shards.** Existing shards and row offsets never change; new tiers add shards and
   bump the manifest version.
5. **Sonnet-class or stronger for every judgment call.** Type discipline (molecule vs transporter gene vs
   drug class) is real biomedical reasoning, and the cheap-model failure mode is over-merging — exactly the
   error that destroys count integrity. Volume is small (one call per distinct string), so cost is not a
   consideration.
6. **Re-freeze deliberately.** When Tier 2 legitimately changes a fact, re-freeze with a version bump and
   record the old value. Never edit a frozen number to make a test pass.
7. **Schema trim, decided from measured fill rates:** drop `anatomical_study` and `entity_ontology_id_note`
   (0.0%). Demote `pathway_id` (0.1%), `dataset_accession` (0.7%), `phenotype_hpo` (2.8%) to opportunistic —
   they are thin because papers rarely state them, not because extraction failed, and no amount of
   re-extraction fixes that. They need external DB joins keyed on canonical entities.

## Scale expectations

**Corrected projection (the earlier ~99,500/~135,600 figures were carried from the pre-canonicalization
audit and are superseded — an error made inside this very document, logged rather than quietly patched):**

Tier-1 basis, canonical_pmid and direct-only: 3,121 papers / 36,459 findings = **11.68 findings/paper**.
Tier-1 yield fraction: 3,129 of 3,794 attempted papers produced findings = **82.5%**.

| Quantity | Value | Basis |
|---|---:|---|
| Tier-2 papers to attempt | 7,238 | chunk_order tier==2, excluding chunk 75 already done |
| Expected yielding papers | ~5,973 | 82.5% of attempted |
| New findings (expected) | **~69,732** | 7,238 x 0.825 x 11.68 |
| New findings (upper bound) | ~84,553 | if every paper yielded |
| Corpus total | **~106,191** | 2.9x current |

Do not quote a single number here without saying which of the two yield assumptions it uses.

Budget by **LLM-call volume, not data volume** — the per-frame token ceiling is what bit the Tier-1 canonicalization track, and the existing
50-papers-per-chunk x 6-concurrent driver architecture exists for exactly this reason. Canonicalization
should shard the head upfront rather than discovering the ceiling mid-run.

## One thing the machinery cannot do

None of this validates biomedical correctness. It guarantees numbers are internally consistent and that
merges preserve evidence — not that a merge is *scientifically* right. That still needs a domain expert
reading entity pages, which is why every entity page lists its folded-in original strings, and why the
the 51 low-confidence entity MAPPINGS (240 medium) are flagged rather than hidden — they affect 232 finding ROWS; quote the mapping count for review workload and the row count for data impact.

### Superseded projections — do not reuse

Three different figures circulated for this one quantity before the basis was pinned down:

| Figure | Basis | Status |
|---|---|---|
| ~99,500 new / ~135,600 total | pre-canonicalization audit | **superseded** |
| ~83,000 new / ~119,400 total | raw pmid, 36,067/3,129 = 11.53 f/paper | **superseded** |
| **~69,732 new / ~106,191 total** | canonical_pmid, 36,459/3,121 = 11.68 f/paper, x 82.5% yield | **use this** |

The spread between the first and last is ~30%. This is the same basis-ambiguity failure the rest of this
document exists to prevent, and it happened three times in this quantity alone — which is why projections
now live in the fact registry rather than in prose.
