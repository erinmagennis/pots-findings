# v1.2 paper flags: spec for the pre-Zenodo rebuild

Purpose: before the five v1.2 packages are published on Zenodo (permanent, never editable), add a searchable
"paper flags" table to every package. An audit on 2026-10-26 (Claude Code) checked all 11,519 PubMed records in the
packages against PubMed and found records that a reader must be able to see and filter:

| Candidate flag | Papers | Findings | Source |
|---|---|---|---|
| retracted | 10 | 139 | PubMed "Retraction in" links and the "Retracted Publication" type |
| expression_of_concern | 1 | 4 | PubMed "Expression of concern in" |
| erratum_notice (a correction notice that had findings extracted) | 6 | 37 | PubMed "Erratum for" / "Published Erratum" |
| has_correction (the paper has a published correction) | 179 | 2,589 | PubMed "Erratum in" |
| earlier / later version pairs (preprint and published version both in the corpus) | 29 pairs | 508 + 649 | PubMed "Update in" / "Update of" |
| preprint (any) | 70 | 1,395 | PubMed "Preprint" type |
| possible_same_work (title match, NOT yet decided) | 42 rows | 352 | title and author matching, needs a decision per pair |

The earlier `data/pmid_dedup_map.parquet` (9 title groups, 8 merges) covered only package 1, only exact titles, and no
retractions. This spec replaces it as the source of truth for duplicates.

Inputs prepared for you in `releases/v1.2/paper_flags/`:
- `paper_flags_candidates.csv`: one row per candidate (pmid, package, n_findings, candidate_flag, linked_pmid,
  linked_package, source, evidence, needs_review, PubMed title, journal, date).
- `pubmed_esummary_2026-10-26.json`: the PubMed esummary snapshot for all 11,519 PMIDs (publication types and
  linked notices), fetched 2026-10-26. Treat it as a declared build input so a rebuild reproduces the flags.

## Hard constraints (same as DOC_PASS_SPEC.md)

1. **Existing data is frozen.** Every existing file under `data/`, `annotations/*.parquet`, `annotations/*.csv` and
   every QA table value stays byte-identical to commit 7e031f6. No finding row is removed or edited in v1.2, including
   rows from retracted papers: they are flagged, not deleted. Only new files plus prose and metadata change. Prove it
   with a file-level sha256 diff against 7e031f6.
2. Keep the reserved DOIs and the five exact record titles (the per-package counts stay PubMed-record counts:
   36,067 / 3,129 and so on). The total stays 11,519 PubMed records; that is the one headline number.
3. Deterministic tarballs (same `make_tarball`, epoch 2026-10-22T12:15:40Z), refreshed `CHECKSUMS.sha256` and
   `MANIFEST.json`, `code/verify_package.py --self-test` PASS for all five, and the three audit greps from
   DOC_PASS_SPEC.md still return 0. No em dashes in new prose.
4. Fix it at the generator (`condition-findings-builder`) so a rebuild reproduces everything.
5. Never touch `.env` or any secret file. Do not push, publish or upload anything.

## Deliverable

### 1. `annotations/paper_flags.csv` (and `.parquet`) in every package

One row per (pmid, flag) for that package's own PMIDs. A paper can have several rows. Columns, all plain text so the
file is searchable with grep, a spreadsheet or the site:

| Column | Meaning |
|---|---|
| `pmid` | the flagged record |
| `flag` | one of the vocabulary below |
| `flag_label` | the flag in plain words, e.g. "Retracted paper", "Preprint; published version also in this dataset" |
| `linked_pmid` | the related record (retraction notice, original paper, other version), blank if none |
| `linked_in_dataset` | true if `linked_pmid` is one of the 11,519 records |
| `linked_package` | package that holds `linked_pmid`, blank if none |
| `linked_title` | title of the linked record |
| `relation_note` | one short sentence a reader can act on |
| `recommended_use` | `exclude` (retracted, erratum_notice), `count_once` (a duplicate of another record in the dataset), `note` (everything else) |
| `canonical_pmid` | for duplicate groups, the record to count once (the peer-reviewed version over a preprint; the original over a notice or reprint) |
| `n_findings` | finding rows this record has in the package |
| `title`, `journal`, `year`, `doi` | from PubMed |
| `source` | `pubmed_link`, `pubmed_type`, `crossref_retraction`, or `adjudicated_title_match` |
| `checked_utc` | when the source was read |

Flag vocabulary: `retracted`, `partially_retracted`, `expression_of_concern`, `erratum_notice`, `has_correction`,
`preprint_with_published_version`, `published_version_of_preprint`, `preprint`, `same_work_other_record`
(co-publication in two journals, reprint, second record of one paper), `update_of` (a later update article by the
same authors, kept as its own paper but linked).

### 2. Work to do on the candidates

1. **Retractions, a second source.** Check every record with a DOI against Crossref retraction and correction
   notices (Crossref now carries the Retraction Watch data), not only PubMed. Add any retraction PubMed has not
   tagged, with `source = crossref_retraction`.
2. **Decide each `possible_same_work` pair** using PubMed authors, abstract, DOI and journal. Several are known
   to be different papers that share a title (for example two different reviews titled "Small fiber neuropathy",
   a knee and a hip arthroplasty study, the two "Post-COVID-19 POTS" papers with disjoint authors). Record every
   decision, accepted or rejected, with a one-line reason, in `qa/paper_flags_adjudication.json`.
3. **Preprints:** for each of the 70 preprints, find whether its published version is in the dataset (PubMed
   version links first, then title and author search). Flag both sides of each pair.
4. Fold in the 8 merges from `data/pmid_dedup_map.parquet` and confirm each.

### 3. Prose and metadata

- Each package README and `docs/README.md`: a short "Paper flags" section with counts per flag for that package,
  how to use the file (exclude retracted records and erratum notices; count each `count_once` group once), and
  one line saying the dataset's paper counts are PubMed records, with the number of distinct works derived from the
  flags. Same section, totals across all five, in `packages/README.md` and `OVERVIEW.md`.
- `.zenodo.json` description and `deposit/ZENODO_FORM.md`: one or two plain sentences, e.g. "Includes
  annotations/paper_flags.csv, which marks N retracted papers, N correction notices and N duplicate records
  (preprint and published versions). Exclude or count them as the file recommends." Titles unchanged.
- `LIMITATIONS` (or the README limitations): say retracted records are kept and flagged, and that flags reflect
  PubMed and Crossref on the check date.
- `CHANGELOG.md`: a dated entry.

### 4. Checks to add to `verify_package.py`

Every flagged pmid is in the package; every flag is in the vocabulary; every `linked_pmid` marked
`linked_in_dataset` is one of the 11,519; per-flag counts in the README equal the file; no `canonical_pmid` points to
a retracted record.

## Acceptance (report each with evidence)

- sha256 diff against 7e031f6: only new files plus prose and metadata changed; zero existing data or annotation files.
- All five verifiers PASS (including the new checks); `CHECKSUMS.sha256` OK; the three audit greps return 0.
- Counts table: per package and total, papers and findings per flag; number of `possible_same_work` pairs accepted
  and rejected; any Crossref-only retractions.
- New deterministic tarballs in `releases/v1.2/tarballs/`, `TARBALL_CHECKSUMS_WITH_DOI.sha256` updated.
- Commit on `release/v1.2-doi` (and the builder repo). Do not push, publish or upload.
