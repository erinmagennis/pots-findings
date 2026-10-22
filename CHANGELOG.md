# Changelog

## v1.2: 2026-10-22 (packages)
- Tiers 1–2 ontology identifiers re-grounded at their authorities (HGNC via MyGene, ChEBI via OLS4, MeSH via NLM): 14,055 rows `authority_verified_retrospective` (10,879 confirmed, 3,176 replaced), 2,607 withheld (`id_withheld_unverified_v1.2`). Original ids preserved in `ontology_id_v11_model_emitted`.
- On the 3,176 replaced rows the label columns (`entity_ontology_label`, `ontology_label_final`) now carry the NEW id's label fetched by id from its authority (960 ids); in the first v1.2 build they still carried the old wrong id's label (e.g. Trazodone → id corrected to CHEBI:9654, label still "tramadol"). Caught while building the site; fixed before publication.
- Documentation regenerated from measured per-package counts; v1.1 text kept as history. Benchmark: `packages/*/annotations/POTS_MODEL_ID_BENCHMARK.md`.
- No change to any finding, quote, direction, condition label or paper. Tier 3–4 data identical to v1.1.
- Verification status note added to the site About page.

## v1.1: 2026-09-23 (packages)
- Five harmonised packages covering Tiers 1–4 (148,186 findings / 11,519 papers); condition-bucket annotations and quote retrofit census shipped as additive tables.

## Site checkpoint: 2026-08-03
- Tier 1 complete + Tier 2 at 55.5% (tags `tier1-v1`, `tier2-55pct-2026-08-03`).
