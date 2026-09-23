# Website integration guide — Tier 2 Part A — comorbid-condition literatures, first extraction wave

What is new for the site from this package, and what breaks if you load it carelessly.
This guide assumes the three-layer contract in `SITE_CONTRACT.md`: **Layer 1 THE RECORD**
(never edited), **Layer 2 regenerable** `site/data/*.json` + `emb/*.bin`, **Layer 3
presentation** (edit freely).

## Where this package stands relative to the deployed site

The site currently serves **73,070 findings / 6,244 papers /
2,803 canonical entities**, `meta.json` version `combined-t1t2-1`,
13 shards.

**This package is already deployed** — it is the site's tier-2 layer, rows
36,459–73,069. The arithmetic is exact: 73,070 − 36,459 =
**36,611**, which is this package's row count to the row.

**This resolves an ambiguity in the site's own copy.** The deployed scope caveat reads
*"Tier-2 covers 81 of 146 chunks (~55%)"*. That is precisely this package: Part A, 81
chunks. The missing ~45% is **Tier 2 Part B**, which exists, is complete, and is simply not
loaded.

**Nothing new to load from this package.** Its value to the site is that the caveat can now
name what is missing instead of gesturing at a percentage.

### Recommended copy change (Layer 3, no rebuild)

Replace the `~55%` framing in `framingBanner()` with something a reader can act on:

> Tier 2 was extracted in two waves. This site currently shows the first wave — 81 of 145
> chunks, 36,611 findings from 3,123 papers. The second wave (64 chunks, 33,830 findings,
> 2,589 papers) is complete and published separately, but is not loaded here. The two waves
> share no papers and cover the same nine themes.

## Rebuild checklist (applies to any load)

- [ ] Append to Layer 1 in row order; never edit existing rows.
- [ ] Regenerate **all** of Layer 2 — partial regeneration desynchronizes shards from facets.
- [ ] Bump `meta.json` version; the loader keys cache on it.
- [ ] Re-run `site_tools/` verification.
- [ ] Re-check every hardcoded number in Layer 3 copy. Counts in prose go stale silently.
- [ ] Confirm `loadTextShard` / `loadDetailShard` / `shardOf(row)` still agree with the new
      shard count.

## What must not be presented as a bare number

Three site-wide honesty rules, unchanged by which package you load:

1. **Never show an identifier without its verification status** once packages of both kinds
   are loaded. 0.578 and 0.998 must not render identically.
2. **Never present an entity-keyed count as a total.** Roughly half of all findings name no
   entity by design.
3. **Never imply a quote is verified unless `cap_quote_source_retained` is true.** True for
   tier 4 only.

Package data: 36,611 findings, 3,123 papers, 81 chunks, 2019–2026.
