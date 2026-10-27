# Website integration guide: POTS findings v1.2, package 3 of 5: EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 2 of 2 (33,830 findings, 2,589 papers)

What is new for the site from this package, and what breaks if you load it carelessly.
This guide assumes the three-layer contract in `SITE_CONTRACT.md`: **Layer 1 THE RECORD**
(never edited), **Layer 2 regenerable** `site/data/*.json` + `emb/*.bin`, **Layer 3
presentation** (edit freely).

## Where this package stands relative to the deployed site

The site currently serves **73,070 findings / 6,244 papers /
2,803 canonical entities**, `meta.json` version `combined-t1t2-1`,
13 shards.

**This package is NOT on the site. It is the single largest content addition available.**

The site's *"Tier-2 covers 81 of 146 chunks (~55%)"* caveat exists because of this
package. Loading it retires that caveat.

| | current site | after adding this package |
|---|---:|---:|
| findings | 73,070 | **106,900** |
| papers | 6,244 | **8,833** |
| tier-2 coverage | 81 of 145 chunks | **145 of 145** |
| shards @ 6,000 rows | 13 | **18** |

Because the two waves share no PubMed record, this is a pure append, no dedup pass, no
paper-record merge.

### Load procedure

The row-order contract is **append-only**, so Part B goes after row 73,069 and every
existing row index stays valid:

```
rows      0 – 36,458   tier 1        (unchanged)
rows 36,459 – 73,069   tier 2 part A (unchanged)
rows 73,070 – 106,899  tier 2 part B (new)
```

1. Append this package's rows to the Layer 1 record in that order.
2. Regenerate Layer 2 wholesale: `site/data/*.json`, all shards, `emb/*.bin`. Bump
   `meta.json` version from `combined-t1t2-1` to `combined-t1t2ab-1`.
3. Re-embed. Existing embedding shards stay byte-valid (append-only), so only the new
   shards need computing.
4. Run `site_tools/` verification before publishing.
5. Update `framingBanner()`: the ~55% caveat is now false and must not survive the load.

**Watch the facet keys.** `ti` (tier) and `sl` (source_literature) exist but are documented
as not load-bearing. Both waves are `ti = t2`, so a tier facet will not distinguish them.
If you want the waves separable in the UI, that is a **new facet**, not a reuse of `ti`.

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

Package data: 33,830 findings, 2,589 papers, 64 chunks, 2020–2026.
