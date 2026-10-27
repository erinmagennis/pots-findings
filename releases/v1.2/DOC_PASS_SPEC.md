# v1.2 pre-Zenodo documentation pass: spec

Purpose: the five v1.2 packages are about to be published on Zenodo, where files can never be changed.
An audit on 2026-10-26 of the DOI-backfilled tarballs (branch `release/v1.2-doi`, commit 9c5de3e) found the
problems below. Fix them at the generator (`condition-findings-builder/build_packages.py`, its templates and
`packaging/package_config.pots_dysautonomia.json`) so a rebuild reproduces the fix, then rebuild.

## Hard constraints

1. **Data is frozen.** Every file under `data/`, `annotations/*.parquet`, `annotations/*.csv` and every QA table
   value must stay byte-identical to commit 9c5de3e. Only prose and metadata change. Prove it: list every file
   whose sha256 changed; none may be a data or annotation file.
2. **Keep the reserved DOIs** (already in CITATION.cff, .zenodo.json, deposit/ZENODO_FORM.md):
   dysautonomia-core 10.5281/zenodo.23671720 · comorbid-a 10.5281/zenodo.23671722 · comorbid-b 10.5281/zenodo.23671724 ·
   postviral-autism 10.5281/zenodo.23671726 · migraine-hypermobility 10.5281/zenodo.23671728.
3. Deterministic tarballs (same `make_tarball`, same pinned epoch 2026-10-22T12:15:40Z), refreshed
   `CHECKSUMS.sha256` and `MANIFEST.json`, and `code/verify_package.py --self-test` PASS for all five.
4. Never touch `.env` or any secret file.

## Must fix (P1)

1. **Local machine paths.** `migraine-hypermobility-findings/qa/tier4_provenance_audit.json` has two
   local machine paths into the Claude Science artifact store (`path`, `source`). Replace with the bare
   file name (and the artifact version id if it matters for provenance). Add a builder check that fails the
   build if any shipped text file contains `/Users/`, `/private/tmp`, `/home/` or `.claude-science`.
2. **Stale v1.1 identifier claims stated as current.** These still say the ids are "model-emitted,
   existence-checked only" or "do not use them as an entity mapping", which v1.2 superseded:
   - `MANIFEST.json` `quality.id_provenance` in dysautonomia-core, comorbid-a, comorbid-b
   - `README.md` and `docs/README.md` in dysautonomia-core (the `id_provenance` paragraph, ~line 175)
   - `deposit/ZENODO_FORM.md` in dysautonomia-core, comorbid-a, comorbid-b (description block)
   - `qa/comparability_report.json` in all five (check whether it states current status or is a dated
     v1.1 record; if a record, label it as v1.1 history; if current, update)
   Current truth per package is in each README's v1.2 paragraph (lines ~18-30). Already corrected:
   `.zenodo.json` descriptions.
3. **Titles: drop "Tier" naming** in `README.md` H1, `CITATION.cff` `title` and `references[].title`,
   `.zenodo.json` `title`, `deposit/ZENODO_FORM.md`. Use exactly the Zenodo record titles:
   - `POTS findings v1.2, package 1 of 5: POTS and dysautonomia core literature (36,067 findings, 3,129 papers)`
   - `POTS findings v1.2, package 2 of 5: EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 1 of 2 (36,611 findings, 3,123 papers)`
   - `POTS findings v1.2, package 3 of 5: EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 2 of 2 (33,830 findings, 2,589 papers)`
   - `POTS findings v1.2, package 4 of 5: long COVID, post-viral and autism intersections (26,032 findings, 1,587 papers)`
   - `POTS findings v1.2, package 5 of 5: migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS (15,646 findings, 1,091 papers)`
   Column names and file names that contain `tier` (e.g. `tier1_findings.parquet`, `tier_source`) stay as they are;
   say once in each README that "tier" in file and column names is the build stage.
4. **Top-level repo docs** (`packages/README.md:279`, `packages/OVERVIEW.md:92`, `packages/PUBLISHING.md`) still say
   the DOI fields hold placeholders. Replace with the five DOIs. These are not in the tarballs but are public on GitHub.

## Should fix (P2)

5. **Em dashes in prose.** About 6,000 across 169 text files. Replace in prose only (README, docs/*.md,
   LIMITATIONS, LICENSE text, CITATION, .zenodo.json, deposit/*). Use a colon, comma, period or parentheses as
   the sentence needs. **Do not change `—` where it is a data value** (it is an enum value in
   `condition_annotations.csv` and in facet values such as `pots_subtype`), and do not change it inside quoted source text.
6. Any remaining "v1.1" text that reads as current state rather than history.

## Acceptance (report each with evidence)

- File-level sha256 diff vs 9c5de3e: only prose/metadata files changed.
- All five `verify_package.py --self-test` PASS; `shasum -a 256 -c CHECKSUMS.sha256` OK.
- Re-run this audit on the extracted new tarballs; every count must be 0 except em dashes that are data values:
  ```
  grep -rlE "/Users/|/private/tmp|\.claude-science" .
  grep -rlE "existence-checked only|Do not use them as an entity mapping|PLACEHOLDER|Replace with" .
  grep -rlE "^# .*Tier [1-4]|title: .Tier" .
  ```
- New tarballs written to `pots/releases/v1.2/tarballs/` (gitignored) with `TARBALL_CHECKSUMS_WITH_DOI.sha256` updated.
- Commit on branch `release/v1.2-doi`. Do not push, publish or upload anything.
