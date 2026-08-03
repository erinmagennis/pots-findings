# Tier 2 55% checkpoint verification

Date: 2026-08-03

Status: automated checkpoint and rendered Chrome review passed locally.

## Verified current state

- Tier 1 findings: 36,459
- Tier 2 findings: 36,611
- Combined findings: 73,070
- Tier 1 canonical papers: 3,121
- Tier 2 canonical papers: 3,123
- Combined canonical papers: 6,244
- Combined canonical entities: 2,803
- Tier 2 coverage: 81 of 146 chunks, or 55.5%
- Combined site shards: 13
- No project file outside `_intake` exceeds 50 MB

## Corrections applied

- Removed eight merged Tier 1 raw PMID aliases from the combined paper crosswalk.
- Recomputed canonical paper counts for `elp1`, `ivabradine`, and `norepinephrine` in the entity crosswalk.
- Recomputed the same three paper counts in `crossover_shared_biology.csv`.
- Removed the undocumented `_blob` helper from the public Tier 2 CSV and Parquet finding files.
- Preserved every other CSV cell and Parquet value exactly relative to the supplied overlay.
- Replaced stale Tier 1 scope copy and adapted the five discovery pages to the supplied combined schemas.
- Prevented the Charts entity selector from overflowing the viewport at mobile widths.
- Added the missing local favicon so browser requests no longer fail with a 404.
- Corrected the Tier 2 data dictionary from the raw-PMID union of 6,252 to the canonical crosswalk count of
  6,244, and added a verification assertion for that heading.

The current Tier 2 finding record still contains complete `provenance_quote` values. The longest is 718
characters and 14,870 rows exceed the website's 200-character excerpt limit. The website projection continues
to display excerpts capped at 200 characters. Quote accuracy was not checked, by instruction.

## Passed checks

`python site_tools/verify_site.py --self-test`

- PASS: 73,246 checkpoint assertions
- PASS: all three planted failures were caught
- Verified source-row order against both canonical CSV files
- Verified Tier 1 rows precede Tier 2 rows
- Verified text shards, detail shards, paper indices, and embedding shard boundaries
- Verified combined discovery schemas used by the site
- Verified stale Tier 1 scope phrases are absent from site presentation files
- Verified site and Tier 2 checksum manifests
- Verified all 26 Tier 1 files in `data/CHECKSUMS.txt`, including the restored corpus and chunk-order files

Additional checks:

- All site JavaScript files passed `node --check`.
- Public Tier 2 preparation passed with `_blob` absent from CSV and Parquet.
- The public CSV matches the supplied CSV exactly after deleting only `_blob`.
- The public Parquet table matches the supplied Parquet table exactly after deleting only `_blob` and stale
  pandas schema metadata.
- Copy lint passed for the public site and current checkpoint documentation.

## Rendered Chrome review

Chrome was exercised against the local site server at 1,440 by 900 and 390 by 844 pixels. The review covered
all 12 page types, for 24 rendered page views:

- Search
- Entities and entity detail
- Conditions and condition detail
- Papers and paper detail
- Discover
- Charts
- Chart builder
- Ask
- About and limits

Every view showed the combined Tier 1 and partial Tier 2 state: 73,070 findings, 6,244 papers, and the visible
81-of-146 Tier 2 coverage warning. After the mobile Charts fix, all 24 views had no document-level horizontal
overflow, broken images, empty chart canvases, browser console errors, or loading failures.

Interaction checks passed:

- Navigation opened the Search page from About.
- Keyword search for `norepinephrine` returned 54 matches from 30 papers; pagination advanced to page 2 of 3,
  and Clear restored the unfiltered result set.
- All five Discover tabs rendered. The Associations cross-kind filter changed the significant result count from
  291 to 909 and reset correctly.
- Discovery CSV, Charts PNG and CSV, and Chart builder PNG and CSV downloads completed locally.
- A Charts canvas accepted pointer input without an error.
- Chart builder filters rendered a six-slice Tier 2 doughnut chart for distinct papers by entity kind.
- Semantic search loaded `all-MiniLM-L6-v2` in Chrome and returned 300 ranked matches from 182 papers for
  `norepinephrine levels in POTS`; the first result had cosine similarity 0.808.

One compatibility defect was verified and fixed during the review. At 390 pixels wide, `#entSel` on Charts
extended 22.5 pixels past the viewport because its flex item retained its content-based minimum width. Setting
`min-width: 0` and `max-width: 100%` reduced the selector to the available 328 pixels and restored a 390-pixel
document width. A repeated 404 for `/favicon.ico` was also fixed by adding a local icon generated from the
existing approved favicon asset.

## Still unverified

- Visitor-supplied chat provider requests were not exercised because no visitor API key was provided.
- Provenance quotes were not compared with the source papers.
- Biomedical interpretation was not independently reviewed.
- A complete site rebuild cannot currently run because the supplied overlay omitted the full combined generator,
  combined discovery inputs, and Tier 2 embedding-generation input. The checker refuses to overwrite the verified
  projection until those inputs are supplied.

Nothing was deployed, pushed, tagged, released, or otherwise made public during this checkpoint.
