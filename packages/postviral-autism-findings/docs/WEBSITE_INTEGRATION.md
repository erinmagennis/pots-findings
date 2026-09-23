# Website integration guide — Tier 3 — long COVID, post-viral and autism intersections

What is new for the site from this package, and what breaks if you load it carelessly.
This guide assumes the three-layer contract in `SITE_CONTRACT.md`: **Layer 1 THE RECORD**
(never edited), **Layer 2 regenerable** `site/data/*.json` + `emb/*.bin`, **Layer 3
presentation** (edit freely).

## Where this package stands relative to the deployed site

The site currently serves **73,070 findings / 6,244 papers /
2,803 canonical entities**, `meta.json` version `combined-t1t2-1`,
13 shards.

**This package is NOT on the site.** It is the first content from the post-tier-2
pipeline, and it changes what the site can honestly claim about identifiers.

| | current site | after adding this package |
|---|---:|---:|
| findings | 73,070 | **99,102** |
| papers | 6,244 | **7,831** |
| shards @ 6,000 rows | 13 | **17** |

### What is genuinely new for the site

1. **Authority-verified identifiers — 4,113 rows.** Everything on the site today is
   model-emitted. These are resolver-derived and score 0.986 on denotation. This is the
   first time the site could show a *verified* badge that means something.
2. **`canonical_entity` populated in-row — 17,828 rows.** The site's 2,803 canonical
   entities were computed at build time from a vocabulary join. Tier 3 carries
   canonicalization in the data itself.
3. **`entity_kind`** — gene / protein / chemical / anatomical. A facet the site cannot
   currently offer at all. Absent (null, not false) for tiers 1–2.
4. **`certainty_derived`** — hedge detection over finding text *and* quote. Enables a
   confidence filter that does not exist today.
5. **Long COVID becomes the site's largest condition** — this package is long-COVID
   dominated, and pooling shifts the corpus's centre of gravity.

### Two traps specific to loading tier 3

**Trap A — `entity_kind` and `certainty_derived` are null for every row already on the
site.** A facet built on either will silently show only tier-3 rows. Gate on the `cap_*`
flags, and label the facet as tier-3-onward, or a reader will read *"12 genes"* as a
corpus-wide count when it is a tier-3 count.

**Trap B — mixing verified and unverified identifiers in one entity view.** Once tier 3 is
loaded the site holds both kinds. An entity page pooling them presents 0.986-grade and
0.578-grade identifiers identically. **Split them in the UI, or badge every one.**

**Also filter `query_contamination`** — 40 rows from 6 papers pulled in by the ambiguous
abbreviation *ASD* (adult spinal deformity / atrial septal defect, not autism). They should
not surface in an autism view. `scope/tier3_offtopic_pmids.csv` lists the 28 PMIDs.

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

Package data: 26,032 findings, 1,587 papers, 35 chunks, 2020–2026.
