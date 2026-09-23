# Tier 3 — long COVID, post-viral and autism intersections — `postviral-autism-findings-v1.1`

**26,032 findings · 1,587 papers · 35 chunks · 2020–2026**

Package 4 of 5. Self-contained: data, documentation, QA evidence and the code to
re-derive every number. No other download required.

## At a glance

| | |
|---|---|
| topic | long COVID autonomic, autism intersection, post-viral syndromes |
| ontology identifiers | authority-derived (`id_denotes_entity_rate` 0.986) |
| identifier coverage | 4,113 rows (15.8%) |
| quote verifiability | 12.22% |
| invariants | 9/9 pass |
| paper overlap with siblings | zero |

## Verify the download

```
shasum -a 256 -c CHECKSUMS.sha256
python code/verify_package.py --self-test
```

The second command re-derives every number in the README from the shipped parquet and exits
non-zero if any disagrees. It also re-plants six regressions to prove the checker still bites.

## Read first

- `docs/README.md` — start here
- `docs/COMPARABILITY.md` — what you may pool with the sibling packages, and the three traps
- `docs/LIMITATIONS.md` — what is not known, not measured, and known wrong

## Caveats that change conclusions

- **Scientific fidelity is unmeasured.** QA verifies well-formedness, not correct
  interpretation. Every row is a pointer to a paper you should read.
- **87.78% of quotes cannot be re-checked** — body text was discarded after extraction.
- **Absence of a finding is not evidence of absence.** Yield depends ~3× on full-text
  availability.

Data CC BY 4.0. `provenance_quote` holds verbatim source excerpts and is not CC BY — see
`LICENSE`. **Not medical advice.**
