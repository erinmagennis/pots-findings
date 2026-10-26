# Website integration guide: POTS findings v1.2, package 1 of 5: POTS and dysautonomia core literature (36,067 findings, 3,129 papers)

What is new for the site from this package, and what breaks if you load it carelessly.
This guide assumes the three-layer contract in `SITE_CONTRACT.md`: **Layer 1 THE RECORD**
(never edited), **Layer 2 regenerable** `site/data/*.json` + `emb/*.bin`, **Layer 3
presentation** (edit freely).

## Where this package stands relative to the deployed site

The site currently serves **73,070 findings / 6,244 papers /
2,803 canonical entities**, `meta.json` version `combined-t1t2-1`,
13 shards.

**This package is already deployed**: it is the site's tier-1 layer, rows 0–36,458.

**But the row counts differ: this package has 36,067 rows, the site's tier-1 layer has
36,459.** A 392-row delta. The site was built from the pre-harmonization
tier-1 export (89 columns); this package is the harmonized slice (107 columns). Do **not**
assume row *i* here is row *i* on the site. If you rebuild the site from this package, you
rebuild the whole row-order contract and every embedding shard with it.

**Nothing new to load.** What this package offers the site is *corrections*, not content:

| what | site today | this package |
|---|---|---|
| columns | 89 | 107 |
| identifier honesty | id present or absent | `ontology_id_verification` distinguishes model-emitted from authority-verified |
| quote verifiability | not surfaced | `cap_quote_source_retained` per row |
| paper count basis | `canonical_pmid` (3,121) | `pmid` (3,129) |

### The one change worth making for tier 1

The site presents tier-1 ontology identifiers with no signal that **~42% of them do not
denote their entity**. That is the most misleading thing on the site today. A reader
clicking an entity gets an identifier that looks authoritative.

Minimum fix, Layer 3 only, no rebuild: badge tier-1 identifiers as unverified wherever they
render. `ui.js` already exports `framingBanner()` and `entityCoverageNote()`; add a third
export in the same style.

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

Package data: 36,067 findings, 3,129 papers, 76 chunks, 2019–2026.
