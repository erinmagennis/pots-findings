# Integrating the Tier 1 plus partial Tier 2 site

## Current checkpoint

| Measure | Value |
|---|---:|
| Findings | 73,070 |
| Canonical papers | 6,244 |
| Canonical entities | 2,803 |
| Tier 2 coverage | 81 of 146 chunks, or 55.5% |
| Site shards | 13 |

Every Tier 2 and combined figure is a subset figure. Absence is not evidence of absence.

## Compatibility correction

The original overlay said the existing HTML and JavaScript would consume the combined files without changes.
That was incorrect. The combined discovery tables changed field names and shapes, the metadata omitted values
used by the Tier 1 About page, and several pages still described the site as POTS-only.

The corrected integration:

- preserves the existing loader API and append-only row order
- activates the 13-shard combined data layer
- updates site copy to Tier 1 plus partial Tier 2
- adds extraction-tier and source-literature filters
- adapts all five discovery views to the supplied combined schemas
- keeps visitor-supplied chat keys on the visitor's device
- verifies source-row order, shard alignment, page schemas, canonical counts, and stale scope language

## Check before preview or deployment

From the repository root:

```bash
python site_tools/prepare_public_tier2.py
python site_tools/rebuild_site.py --check
python site_tools/verify_site.py --self-test
```

All commands must pass. Then serve the site locally:

```bash
python -m http.server 8000 --directory site
```

Inspect every page in a browser before requesting publication approval.

## Full-rebuild limitation

The supplied overlay omitted the complete combined generator, the upstream combined discovery inputs, and the
Tier 2 embedding-generation input. `rebuild_site.py` therefore checks the supplied projection but refuses to
overwrite it. The exact missing inputs are listed in
`_intake/FUTURE_TIER_PUBLIC_EXPORT_HANDOFF.md` for the next extraction handoff.

## Rollback and Tier 1 access

Tier 1 remains independently usable in `data/` and in its immutable release ZIP and tag. The repository does not
carry a second 50 MB Tier 1 site-data backup. A release ZIP is the rollback source, which avoids maintaining two
copies of the same generated site files on `main`.

Do not deploy or publish without Erin's explicit approval.
