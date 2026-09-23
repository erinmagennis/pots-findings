# Tier 1 — POTS and dysautonomia core literature — `dysautonomia-core-findings-v1.1`

**36,067 findings · 3,129 papers · 76 chunks · 2019–2026**

Package 1 of 5. Self-contained: data, documentation, QA evidence and the code to
re-derive every number. No other download required.

## At a glance

| | |
|---|---|
| topic | dysautonomia, POTS, dysautonomia subtypes, hyperadrenergic POTS |
| ontology identifiers | model-emitted, unverified (`id_denotes_entity_rate` 0.578) |
| identifier coverage | 4,373 rows (12.1%) |
| quote verifiability | 18.12% |
| invariants | 8/9 pass |
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
- **Ontology identifiers are model-emitted.** Roughly
  42% do not denote the entity on their row. Not usable as a mapping.
- **81.88% of quotes cannot be re-checked** — body text was discarded after extraction.
- **Absence of a finding is not evidence of absence.** Yield depends ~3× on full-text
  availability.

Data CC BY 4.0. `provenance_quote` holds verbatim source excerpts and is not CC BY — see
`LICENSE`. **Not medical advice.**
