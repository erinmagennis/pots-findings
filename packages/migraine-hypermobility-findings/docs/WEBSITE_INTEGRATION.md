# Website integration guide: POTS findings v1.2, package 5 of 5: migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS (15,646 findings, 1,091 papers)

What is new for the site from this package, and what breaks if you load it carelessly.
This guide assumes the three-layer contract in `SITE_CONTRACT.md`: **Layer 1 THE RECORD**
(never edited), **Layer 2 regenerable** `site/data/*.json` + `emb/*.bin`, **Layer 3
presentation** (edit freely).

## Where this package stands relative to the deployed site

The site currently serves **73,070 findings / 6,244 papers /
2,803 canonical entities**, `meta.json` version `combined-t1t2-1`,
13 shards.

**This package is NOT on the site.** It is small, but it is the only package whose quotes
are all verifiable, which is a *feature the site cannot currently offer for any row*.

| | current site | after adding this package |
|---|---:|---:|
| findings | 73,070 | **88,716** |
| papers | 6,244 | **7,335** |
| shards @ 6,000 rows | 13 | **15** |

### What is genuinely new for the site

1. **100% quote verifiability: 15,646 rows.** Body text was retained, so every quote can
   be re-checked against its own source. Every other row on the site has a quote whose
   source is gone. This supports a *"verified against source"* badge that is true.
2. **The highest identifier correctness in the corpus**: 0.998, though at the lowest
   coverage (10.3%).
3. **Four themes absent from the site**: migraine intersection, hypermobility spectrum,
   Sjögren's, PANS/PANDAS.
4. **`screen_verdict_uncertain`**: 1,960 rows the screening instrument was unsure about.
   Surfacing this honestly is better than hiding it.

### Traps specific to loading tier 4

**`query_contamination` means something different here.** In tier 3 it marks abbreviation
collisions (40 rows); in tier 4 it marks screening uncertainty (1,960 rows). **A single
site-wide filter on this column would conflate two unrelated concepts.** Read
`screen_verdict_uncertain` for tier 4 instead.

**Coverage has two true values**: 85.97% of screened papers, 74.57% of the pre-screening
universe. If the site states a tier-4 coverage figure it must say which.

## Rebuild checklist (applies to any load)

- [ ] Append to Layer 1 in row order; never edit existing rows.
- [ ] Regenerate **all** of Layer 2, partial regeneration desynchronizes shards from facets.
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

Package data: 15,646 findings, 1,091 papers, 30 chunks, 2020–2026.
