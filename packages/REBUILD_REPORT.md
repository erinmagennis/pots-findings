# REBUILD_REPORT — pots-corpus v1 → v1.1

Built 2026-09-16T08:30:00Z with `build_packages.py` (reconstructed this session) from the same harmonized
corpus as v1 (`findings_all_tiers.parquet`, artifact `f0b86f9a…`). Every number below was re-derived
from the built tree or the shipped QA JSON in this session, not copied from prose.

## What v1.1 is

**No data row changed.** Every `data/<tier>_findings.parquet` has the same shape (107 columns), the same
values and the same row order as v1; the only difference is that three columns
(`is_covid_associated`, `query_contamination`, `screen_verdict_uncertain`) are now stored as pandas
nullable `boolean` everywhere instead of drifting between `bool` and all-null `object` across packages
(value-by-value equality checked, all five tiers). v1.1 adds **additive annotation tables**, a
**documentation revision**, and four **v1 corrections**.

| | v1 (2026-09-09) | v1.1 (2026-09-16) |
|---|---:|---:|
| files in repo tree (incl. `.gitignore`, `.zenodo.json`) | 220 | 286 |
| files per tier | 36 / 39 / 39 / 43 / 45 | 52 / 55 / 55 / 59 / 57 |
| working tree | 102.6 MB | 113.3 MB |
| largest file | 18.9 MB (tier1 CSV) | 18.9 MB — no Git LFS needed |
| checksums (`shasum -c`) | clean ×5 | clean ×5 |
| `verify_package.py --self-test` | PASS ×5 | PASS ×5 (32/32/32/32/29 headline numbers; 6/6 planted regressions each) |
| verifier scope | data + docs numbers | + annotation manifest membership, row alignment, null rule, MCAS coverage |
| unverifiable rows, Tiers 1–3 (shipped data) | 108,549 | 108,549 (unchanged — the data is the data) |
| verifiable rows, Tiers 1–3 **after retrofit** | — | **132,295 / 132,540 (99.82%)** |

File-level diff of the non-hidden tree: 149 unchanged (sha256), 65 changed,
66 added, 0 removed. Changed in tier1 (the same set in every tier):
`CHECKSUMS.sha256`, `CITATION.cff`, `MANIFEST.json`, `README.md`, `code/verify_package.py`, `data/tier1_findings.csv.gz`, `data/tier1_findings.parquet`, `deposit/github_release_notes.md`, `docs/DATA_DICTIONARY.md`, `docs/LIMITATIONS.md`, `docs/README.md`, `qa/package_stats.json`. The parquet/csv.gz change is the dtype cast only.

## 1. Quote source retrofit (Tiers 1–3)

Only Tier 4 retained the text it extracted from. On 2026-09-16 the Retrofit track re-fetched the source
text of all 10,428 Tier 1–3 papers from Europe PMC (16,653 requests, 118 min at
2.34 req/s — the pinned 3 × 0.9 s pacing; every search call HTTP 200) and re-checked every quote with the
shipped comparator (`quote_trace.py`, sha256 `0a66bf6e1087`), after `comparator_symmetry_tests.py` passed 8/8.

| tier | verifiable before (shipped) | verifiable after | full-text rows traceable vs re-fetched full text | wrong-paper control |
|---|---|---|---|---|
| tier1 | 6,536 / 36,067 (18.12%) | 35,949 / 36,067 (99.67%) | 27,390 / 28,113 (97.43%) | 0/400 |
| tier2a | 7,713 / 36,611 (21.07%) | 36,547 / 36,611 (99.83%) | 28,353 / 28,895 (98.12%) | 0/400 |
| tier2b | 6,560 / 33,830 (19.39%) | 33,778 / 33,830 (99.85%) | 26,739 / 27,250 (98.12%) | 0/400 |
| tier3 | 3,182 / 26,032 (12.22%) | 26,021 / 26,032 (99.96%) | 22,402 / 22,850 (98.04%) | 0/400 |

Corpus-wide Tiers 1–3: verifiable 23,991 → 132,295 of 132,540 (18.1% → 99.82%);
full-text-depth traceability 104,884 / 107,108 = 97.92% (pilot of 97 papers read 98.65%).
Abstract-stratum rows trace at 92–96% against today's `abstractText`.

Losses, flagged not repaired: **245 rows** have no source in Europe PMC today; **1,391 `retrieved-fulltext`
rows** (1,371 tier1, 20 tier2b) could only be checked against the abstract and trace at ≈0% for
source-depth reasons — so the "all verifiable rows" rate (96.03% corpus-wide, 92.89% for tier1) must be
stratified on `retrofit_source_depth × fulltext_status` before it is quoted. The retrofit checks Europe
PMC's *current* text, not the bytes the model read; the Tier-4 retained-archive guarantee is not
reproduced, and each package's LIMITATIONS §12 says so. Fetched text was deleted after the census
(LICENSE); the row-level result ships as `annotations/quote_retrofit_<tier>.parquet` (keyed on `row_idx`,
validated against the shipped parquet: length, `row_idx`, `pmid`, `sha1(provenance_quote)` all match —
and the shipped verifier now re-checks this).

## 2. Condition bucket annotations

Decision recorded 2026-09-16: `condition` = **the patient population the paper studied**. Against
`CONDITION_BUCKET_DEFINITIONS.md` v1, `annotations/condition_annotations.parquet` (pmid-keyed, all five
packages) gives every one of the 1,083 `MCAS`-labelled papers (8,834 rows) a verdict:
**32 `in_bucket`, 148 `bucket_violation`** (49 mastocytosis, 87 mast-cell biology only,
12 neither), **903 `NEEDS_HUMAN`**. Every verdict is classifier-derived, `human_confirmed == False`.
The stratified projection (~69% mechanism-only, ~10% MCAS, ~5% mastocytosis) stays in
`mcas_bucket_census.csv` and is not copied into per-paper rows. Other buckets are not censused; 8 of 13
bucket definitions are provisional. The 66 papers with "mastocytos" in the title are the bounded
human-adjudication set.

## 3. Documentation revision (every package)

- README: a new "will mislead you" item on `condition` (numbered per package: 5 in tiers 1/3/4, 6 in
  tiers 2a/2b), rewritten `condition` paragraph, an "Annotations (additive)" section with the retrofit
  table and condition counts for that package, `code/README.md` in the contents table.
- DATA_DICTIONARY: `condition` redefined as a population bucket with a pointer to the definitions;
  `provenance_quote` now states that quotes are verbatim to model input and that 128 corpus-wide
  (2 / 82 / 2 / 0 / 42 per package) carry raw HTML entity codes that trace under the symmetric comparator.
- LIMITATIONS: §10 condition bucket, §11 entity codes, §12 retrofitted-not-retained (tiers 1–3); the
  "what would most improve" list now names the annotation adjudication and, for Tier 4, the corrected
  uncertain-row count.
- `code/README.md`: one line per file, explaining why a Tier-1 package carries `tier3_*` modules.
- `code/comparator_symmetry_tests.py` in every package; `retrofit_fetch.py`, `retrofit_census.py`,
  `build_report.py` in tiers 1–3.
- Root README/OVERVIEW: fourth mislead item and a "What changed in v1.1" section.

## 4. v1 corrections surfaced by the rebuild

1. `PACKAGE_INDEX.csv` file counts in v1 (38/41/41/45/47) were two too high per tier — two stale
   `code/__pycache__/*.pyc` files were counted when the index was written and never regenerated after
   the purge. v1.1 emits the manifest-consistent counts.
2. Tier 4 docs said "1,960 `screen_verdict_uncertain` rows" in eight places; the data has **2,257**
   (identical in v1 and v1.1 `package_stats.json`). v1.1 prose uses 2,257 and notes the change.
3. CORPUS_HANDOFF / tier handoff documents (108,714 unverifiable rows; 173 no-yield papers) disagreed
   with the README (108,549; 162). All nine handoff artifacts are re-saved with a SUPERSEDED banner
   pointing at `OVERVIEW.md`, this report and `qa/package_stats.json`.
4. CALIBRATION_REPORT v7's statement that unescaping the quote gives 0/42 traceable applied to the AI
   judge harness's raw-text view, not to the census comparator (42/42 in every configuration —
   `annotations/COMPARATOR_GATE.json`). The harness is patched (`QUOTE_LIKE_FIELDS` normalized).

## 5. Reproducibility

- `build_packages.py` (reconstructed from the 2026-09-02 session's 128 code cells) reproduces v1
  **219/220 files byte-identical** with `--build-utc 2026-09-02T11:10:50Z --pin-gzip-mtime`; the one
  difference is correction 1 above. All five v1 verifiers pass on the reproduction.
- v1.1 command: `python build_packages.py --config package_config_v11.json --corpus findings_all_tiers.parquet
  --inputs-dir inputs --templates templates_v11 --out out_v11 --version v1.1 --docs-revision v1.1
  --dtype-fix --annotations annotations_v11 --build-utc 2026-09-16T08:30:00Z`.
- Inputs: 63 declared files by artifact id (`package_config_v11.json`), 12 annotation files.
- The builder, its templates and the POTS config also ship inside `condition-corpus-builder` under
  `packaging/`, so the method repository is complete.

## 6. Still for a human (unchanged from the review, now bounded)

| item | size | where |
|---|---|---|
| adjudicate the 25 AI-scorer calibration flags | ~1 h | `calib_flags_to_adjudicate.csv` |
| confirm the 66 mastocytosis-title papers, then set `human_confirmed` | ~30 min | `condition_annotations.csv`, `title_mastocytosis == True` |
| confirm/replace the 8 PROVISIONAL bucket definitions | ~30 min | `condition-corpus-builder/config/pots_dysautonomia.yaml` |
| score the fidelity worksheet (Q3, Q10 human) | 2–4 h | `fidelity_worksheet_tier4.csv`, `FIDELITY_PROTOCOL_TIER4.md` |
| reserve DOIs, run `--backfill-doi`, `git init`, push, attach the five tarballs as Release assets | ~1 h | `PUBLISHING.md` |
| verbatim-quote licensing question | — | `PUBLISHING.md` |

## Naming (2026-09-16, after the v1.1 build)

Packages are named for their content, not their extraction tier, because POTS is the seed literature,
not the subject of most papers: POTS as `condition` is 13.7% / 0.1% / 0.2% / 0.1% / 1.1% of papers in
tiers 1 / 2a / 2b / 3 / 4 (POTS in the title: 14.2 / 0.0 / 0.0 / 0.0 / 0.8%). The tier is kept as
`MANIFEST.tier`, in the data file names (`tier2a_findings.parquet`) and in `tier_source`.

| tier | package |
|---|---|
| tier1 | `dysautonomia-core-findings` |
| tier2a | `comorbid-conditions-findings-a` |
| tier2b | `comorbid-conditions-findings-b` (same literatures as A; second extraction wave) |
| tier3 | `postviral-autism-findings` |
| tier4 | `migraine-hypermobility-findings` |

Repository: `erinmagennis/pots-findings`. Sibling DOIs are related as `references` (a sibling is not a
part of its sibling). `deposit/ZENODO_FORM.md` in each package carries the values to paste into a manual
Zenodo upload, since Zenodo does not read `.zenodo.json` from an uploaded archive. Data, checksums logic
and annotations are unchanged by the rename; 3 rows of enum drift in `condition` (`IBD_gut`,
`orthostatic_hypotension`, `other patient group`; 4 papers) are now documented in LIMITATIONS §6.
