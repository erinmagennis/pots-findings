# Changelog: POTS findings, migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS

## v1.2 (2026-10-26): paper flags, documentation pass, Zenodo DOIs

- Added `annotations/paper_flags.csv` and `.parquet`: 44 rows marking retracted papers
  (0), expressions of concern (0), correction notices extracted as papers
  (0), papers with corrections (19), preprints (22, of which
  9 have their published version in the dataset) and same-work duplicates (2 records). Sources: PubMed
  publication types and linked notices, Crossref update notices, both read 2026-10-26; title-match pairs adjudicated in `qa/paper_flags_adjudication.json`.
  No finding row was removed or edited; flagged rows are flagged. `data/pmid_dedup_map.parquet` (v1.0, package 1 only) is superseded by the flags file.
- Added `verify_package.py` checks: every flagged record is in the package, every flag is in the vocabulary, linked records marked in-dataset exist,
  README per-flag counts equal the file, no `canonical_pmid` points to a retracted record.
- Documentation pass before Zenodo: record titles name the content, not the build stage; Zenodo DOIs filled in everywhere; identifier prose describes
  the v1.2 re-grounding; local machine paths scrubbed from QA files; em dashes removed from prose.
- Identifier re-grounding (v1.2 data change, 2026-10): every model-emitted ontology id in build stages 1 and 2 looked up at its authority;
  confirmed ids kept, resolvable names re-assigned, the rest withheld (`ontology_id_verification`; the old id kept in `ontology_id_v11_model_emitted`).

## v1.1 (2026-09-16): additive annotations, no data changed

- Quote-source retrofit for build stages 1 to 3 (`annotations/quote_retrofit_*.parquet`), condition-bucket annotations, nullable boolean dtypes,
  documentation corrections (`condition`, `provenance_quote`, `code/README.md`).

## v1.0 (2026-09-02): first packaged release

- Five self-contained packages with data, docs, QA evidence, pinned code and a verifier with planted regressions.

