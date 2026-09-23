# code/ — pinned build and verification code for this package

Every file here is byte-identical to what produced or verified the shipped data. Files are named for
the tier whose build **introduced** them, so a Tier-1 package legitimately carries `tier3_invariants.py`:
the invariant suite written for Tier 3 is the one run against every package. Shared modules are
identical across all five packages (sha256-verified at build).

| file | role |
|---|---|
| `build_report.py` | Builds RETROFIT_REPORT.md and retrofit_summary.json from the census outputs. |
| `comparator_symmetry_tests.py` | Pins that the matcher decodes HTML entities and folds whitespace/superscripts on BOTH sides (8 cases). Run before any retrofit census. |
| `crosstier_vocab.py` | Cross-tier entity canonicalization; refuses to case-fold gene symbols (MECP2 vs Mecp2). |
| `driver_tier3_parts.py` | Part-aware chunk driver for Tier 3. |
| `extraction_pipeline_v6.py` | Schema-v6 pipeline (Tier 3): names only, identifiers resolved afterwards. |
| `multi_authority_resolver.py` | Name → identifier resolution against real authorities (HGNC, OLS4/HPO/MONDO, MeSH, QuickGO); records authority and match mode. Exact-label only. |
| `normalizer_tests.py` | Unit tests for the source-text normalizer — one case per bug that once produced a false quality number. |
| `quote_trace.py` | Quote traceability matcher (`normalize`, `quote_traceability`) with its MANDATORY wrong-paper negative control. Read element [1] of the tuple. |
| `resolution_cache.py` | Persistent cache for resolver look-ups so re-runs make zero API calls. |
| `retrofit_census.py` | 2026-09-16 retrofit census: re-checks every quote against re-fetched source with the pinned comparator and wrong-paper control; emits annotations/quote_retrofit_<pkg>.parquet. |
| `retrofit_fetch.py` | 2026-09-16 retrofit fetcher: re-fetches abstract + JATS body from Europe PMC at the pinned pacing (3 × 0.9 s); logs per paper. |
| `schema_v6_extraction_prompt.txt` | The exact prompt used for Tier 3. |
| `tier3_invariants.py` | Nine-check invariant suite written for Tier 3; the suite run on every package's QA. |
| `tier3_invariants_ext.py` | Extensions to the Tier-3 suite: id provenance tags, quote/number checks. |
| `tier3_merge.py` | Part merge with conflicting-scheme guard (Tier 3). |
| `tier3_qa.py` | Tier-3 QA: quote census, field fill, enum drift. |
| `verify_package.py` | Re-derives every number in README/DATA_DICTIONARY from the shipped data; `--self-test` plants six regressions and asserts each is caught. Exits non-zero on disagreement. |

Run order for a reader: `python verify_package.py --self-test` (re-derives every documented number and
plants six regressions), then `python normalizer_tests.py` and `python comparator_symmetry_tests.py` (the
quote matcher's unit tests — one case per historical bug). Nothing here needs the network except the
extraction pipeline and the retrofit fetcher, which are shipped as the record of what ran, not as tools
you are expected to re-run.

