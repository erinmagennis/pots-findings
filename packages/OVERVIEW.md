# Five uploadable packages, index

Built 2026-10-22T12:15:40Z from harmonized corpus `f0b86f9a-f688-48c4-a08f-94e946afb9af`.

Each package stands alone: data (parquet + gzipped CSV), documentation, QA evidence, the
pinned extraction and validation code, and a verifier that re-derives every documented number
from the shipped data. No package requires another download or a network connection.

## The partition

Five blocks of one corpus. **Zero papers are shared between any two packages**: verified by
pmid set intersection across all ten pairs at build time.

| package | findings | papers | chunks | identifiers | id correctness † | quotes verifiable | invariants |
|---|---:|---:|---:|---|---:|---:|---:|
| `dysautonomia-core-findings-v1.2` | 36,067 | 3,129 | 76 | model-emitted | 0.5784 | 18.12% | 8/9 |
| `comorbid-conditions-findings-a-v1.2` | 36,611 | 3,123 | 81 | model-emitted | 0.7082 | 21.07% | 7/9 |
| `comorbid-conditions-findings-b-v1.2` | 33,830 | 2,589 | 64 | model-emitted | 0.7082 | 19.39% | 7/9 |
| `postviral-autism-findings-v1.2` | 26,032 | 1,587 | 35 | authority-derived | 0.9857 | 12.22% | 9/9 |
| `migraine-hypermobility-findings-v1.2` | 15,646 | 1,091 | 30 | authority-derived | 0.998 | 100.0% | 9/9 |
| **total** | **148,186** | **11,519** | **286** | | | **26.75%** | |

Per-package counts sum exactly to the corpus totals.

† **`id correctness` (`id_denotes_entity_rate`) is a TIER-level measurement.** It comes from
adjudicated samples drawn per tier (t1 n=276, t2 n=270, t3 n=199, t4 n=56). Tier 2's sample
spans both waves, so **Part A and Part B both show 0.7082 by inheritance, neither has a rate
of its own.** Every other figure in the table, coverage included, is measured on each
package's own slice (Part A 15.63%, Part B 14.15%). A per-wave proxy, exact string agreement
against the authority label, puts the waves 1.11 points apart (65.51% vs 66.62%), so they are
unlikely to diverge materially, but the adjudicated rate was never split.

## Tier 2 is split into the two extraction waves

- **Part A**: 81 chunks, 36,611 findings, 3,123 papers
- **Part B**: 64 chunks, 33,830 findings, 2,589 papers

The waves share zero papers and their chunk ids **interleave** (Part B spans 126–219), so the
split is operational, not topical. Both cover the same nine themes, from one pipeline with one
prompt, pool them freely.

Part A is exactly the tier-2 layer currently deployed on the website: 73,070 − 36,459 =
36,611. The site's *"~55% of tier 2"* caveat means precisely
"Part A only".

## Five things that will mislead you across packages

1. **`id_resolved_frac` ranks the packages backwards.** It measures identifier *coverage*, not
   *correctness*. Tier 2 has the most identifiers and nearly the worst; Tier 4 the fewest and
   the best. Stratify on `ontology_id_verification`.
2. **108,549 of 148,186 rows have no shipped source text.** Only Tier 4 retained
   body text. The v1.1 retrofit re-fetched Tier 1–3 source from Europe PMC and re-checked every quote
   (99.8% of the corpus now has a checkable source; 0/400 false positives): against
   *current* text, not the bytes the model read. The `quotes verifiable` column below is the shipped-source
   figure; the retrofit figures are additive, in each package's `annotations/`.
3. **`ontology_id_source == 'unresolved_nulled'` has inverted meanings.** Identifier KEPT in
   Tier 2, identifier NULLED in Tiers 3–4. The obvious filter silently drops 2,242 Tier-2 rows.

Each package's `docs/COMPARABILITY.md` covers these in full, plus the five safe aggregates and
the eleven metrics that are not comparable.

4. **`condition` is a coarse population bucket and the `MCAS` bucket is ~69% mechanism-only papers.**
   Use `annotations/condition_annotations.parquet`; see the root README, item 4.

Each package's `annotations/` folder (v1.1) also carries the row-level quote-retrofit results for Tiers
1–3, verifiability 18.1% → 99.8% against re-fetched Europe PMC text, as additive tables. No `data/` row
changed between v1 and v1.1.

5. **316 paper-flag rows across the packages (`annotations/paper_flags.csv`).** 10 retracted papers (139 findings) are kept and flagged, not removed; 5 correction notices were extracted as papers; 30 preprints have their published version in the dataset. Apply `recommended_use` before any count; the 11,519 records are 11,478 distinct works. Checked against PubMed and Crossref on 2026-10-26.

## Above all

**Scientific fidelity is unmeasured.** Every QA check verifies well-formedness, quotes trace
to source, identifiers carry provenance, invariants hold. Nothing verifies that a finding
correctly *interprets* its source. That needs a human reader. Treat every row as a pointer to
a paper worth reading, not as a fact.

## Verify any package

```
tar -xzf pots-findings-<pkg>-v1.2.tar.gz && cd pots-findings-<pkg>-v1.2
shasum -a 256 -c CHECKSUMS.sha256
python code/verify_package.py --self-test
```

All five currently report 19/19 headline numbers re-derived, 6/6 planted regressions caught,
and invariant results matching each README's declaration, including the three packages that
correctly declare failures.

## Deposit sidecars

Every package carries `.zenodo.json`, `deposit/osf_metadata.json` and
`deposit/github_release_notes.md`, `deposit/ZENODO_FORM.md` (the values to paste into a manual
Zenodo upload), plus `CITATION.cff`. Each package's DOI is filled in below and in its `CITATION.cff`, `.zenodo.json` and `deposit/` files; the four sibling references in every package carry the real DOIs.

| package | DOI |
|---|---|
| `dysautonomia-core-findings-v1.2` | https://doi.org/10.5281/zenodo.23671720 |
| `comorbid-conditions-findings-a-v1.2` | https://doi.org/10.5281/zenodo.23671722 |
| `comorbid-conditions-findings-b-v1.2` | https://doi.org/10.5281/zenodo.23671724 |
| `postviral-autism-findings-v1.2` | https://doi.org/10.5281/zenodo.23671726 |
| `migraine-hypermobility-findings-v1.2` | https://doi.org/10.5281/zenodo.23671728 |

## Website

Each package carries `docs/WEBSITE_INTEGRATION.md` describing what is new for the site from
that package and what breaks on a careless load. In value order: **Tier 2 Part B** is the
largest content addition (retires the ~55% caveat, 73,070 → 106,900 findings); **Tier 3**
brings the first authority-verified identifiers and three facets the site cannot currently
offer; **Tier 4** brings the only fully verifiable quotes.
