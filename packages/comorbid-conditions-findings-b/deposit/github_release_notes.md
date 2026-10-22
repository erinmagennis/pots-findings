# Tier 2 Part B — comorbid-condition literatures, second extraction wave — `comorbid-conditions-findings-b-v1.2`

**33,830 findings · 2,589 papers · 64 chunks · 2020–2026**

Package 3 of 5. Self-contained: data, documentation, QA evidence and the code to
re-derive every number. No other download required.

## At a glance

| | |
|---|---|
| topic | EDS/hypermobility, ME/CFS, MCAS, RCCX genes, fibromyalgia, IBS, small-fiber neuropathy, patient-generated evidence, gastroparesis |
| ontology identifiers | model-emitted, unverified (`id_denotes_entity_rate` 0.708) |
| identifier coverage | 4,788 rows (14.1%) |
| quote verifiability | 19.39% |
| invariants | 7/9 pass |
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
  29% do not denote the entity on their row. Not usable as a mapping.
- **80.61% of quotes cannot be re-checked** — body text was discarded after extraction.
- **Absence of a finding is not evidence of absence.** Yield depends ~3× on full-text
  availability.

Data CC BY 4.0. `provenance_quote` holds verbatim source excerpts and is not CC BY — see
`LICENSE`. **Not medical advice.**
