# Tier 4 — migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS — `migraine-hypermobility-findings-v1.2`

**15,646 findings · 1,091 papers · 30 chunks · 2020–2026**

Package 5 of 5. Self-contained: data, documentation, QA evidence and the code to
re-derive every number. No other download required.

## At a glance

| | |
|---|---|
| topic | migraine intersection, author-augmented papers, hypermobility spectrum, Sjögren's, PANS/PANDAS |
| ontology identifiers | authority-derived (`id_denotes_entity_rate` 0.998) |
| identifier coverage | 1,614 rows (10.3%) |
| quote verifiability | 100.0% |
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
- **Every quote is re-checkable** — the only package where that is true. Corpus-wide the figure is 26.75% (39,637 of 148,186 rows).
- **Absence of a finding is not evidence of absence.** Yield depends ~3× on full-text
  availability.

Data CC BY 4.0. `provenance_quote` holds verbatim source excerpts and is not CC BY — see
`LICENSE`. **Not medical advice.**
