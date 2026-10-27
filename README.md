# POTS and dysautonomia literature findings

A public, machine-extracted research dataset and static browser: findings from the POTS, dysautonomia and related-condition literature, with verbatim source quotes, released as five verifiable data packages.
Built with [condition-findings-builder](https://github.com/erinmagennis/condition-findings-builder). Project index:
[condition-findings](https://github.com/erinmagennis/condition-findings). Sister dataset: [eds-findings](https://github.com/erinmagennis/eds-findings).

## Findings packages v1.2 (the full corpus)

The complete harmonised corpus: **<!--n:findings-->148,186<!--/n--> findings from <!--n:pmids-->11,519<!--/n--> papers** across Tiers 1–4: ships as five
self-contained packages under [`packages/`](packages/) (start at [`packages/README.md`](packages/README.md) and
[`packages/OVERVIEW.md`](packages/OVERVIEW.md)). Each package carries its data (Parquet + CSV), documentation,
QA tables, the code that built it and `CHECKSUMS.sha256`; `code/verify_package.py --self-test` re-checks a package end to end.

### Download and cite

Each package is archived on Zenodo with its own DOI. The "all versions" DOI always resolves to the newest version.

| package | contents | size | DOI (v1.2) | DOI (all versions) |
|---|---|---|---|---|
| 1 of 5 | POTS and dysautonomia core literature | 33.6 MB | [10.5281/zenodo.23671720](https://doi.org/10.5281/zenodo.23671720) | [10.5281/zenodo.23671719](https://doi.org/10.5281/zenodo.23671719) |
| 2 of 5 | EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 1 | 22.9 MB | [10.5281/zenodo.23671722](https://doi.org/10.5281/zenodo.23671722) | [10.5281/zenodo.23671721](https://doi.org/10.5281/zenodo.23671721) |
| 3 of 5 | the same conditions, part 2 | 20.5 MB | [10.5281/zenodo.23671724](https://doi.org/10.5281/zenodo.23671724) | [10.5281/zenodo.23671723](https://doi.org/10.5281/zenodo.23671723) |
| 4 of 5 | long COVID, post-viral and autism intersections | 16.8 MB | [10.5281/zenodo.23671726](https://doi.org/10.5281/zenodo.23671726) | [10.5281/zenodo.23671725](https://doi.org/10.5281/zenodo.23671725) |
| 5 of 5 | migraine, hypermobility spectrum, Sjögren's, PANS/PANDAS | 10.5 MB | [10.5281/zenodo.23671728](https://doi.org/10.5281/zenodo.23671728) | [10.5281/zenodo.23671727](https://doi.org/10.5281/zenodo.23671727) |

The same five files are attached to the [v1.2 GitHub release](https://github.com/erinmagennis/pots-findings/releases/tag/v1.2.0).
Each package's `CITATION.cff` gives the citation for that package.

**Paper flags.** Every package carries `annotations/paper_flags.csv`, which marks retracted papers (10 across the
corpus, 139 findings), correction notices extracted as papers, papers with a published correction, and preprints
whose published version is also in the dataset. Rows are flagged, never removed: exclude or count them once as the
file recommends. Checked against PubMed and Crossref on 2026-10-26.

| version | tag | what changed |
|---|---|---|
| v1.2 | `v1.2.0` | Paper flags added (retractions, correction notices, duplicate versions; see above). Every model-emitted ontology identifier in Tiers 1–2 was looked up by id at its minting authority (HGNC, ChEBI, MeSH) and compared with the entity name. <!--n:id_retrospective_rows-->14,055<!--/n--> rows are now `authority_verified_retrospective` (<!--n:id_kept_rows-->10,879<!--/n--> confirmed, <!--n:id_replaced_rows-->3,176<!--/n--> replaced by the id the name resolves to); <!--n:withheld_id_rows-->2,607<!--/n--> ids that denoted a different entity were withheld. The original model id is preserved in `ontology_id_v11_model_emitted`. No finding text, quote, direction, condition or paper changed. |
| v1.1 | `v1.1` | Five harmonised packages; Tier 1–2 identifiers flagged `unverified_model_emitted`. |

Join on `entity_ontology_id_resolved` only where `ontology_id_verification` is `authority_verified` or
`authority_verified_retrospective` (<!--n:verified_id_rows-->19,782<!--/n--> rows). **Scientific fidelity: whether each finding states what its paper
found: has not yet been checked by a human reader**; that audit is open and its result will be posted here and on the
site's About page. The browser at pots.erinmagennis.com serves this release.

## Browser

The findings browser at [pots.erinmagennis.com](https://pots.erinmagennis.com) is a static projection of the packages above
(search, entity and condition pages, derived tables, chart builder). It is regenerated from `packages/` by
`site_tools/build_v12_projection.py`; every count shown on the site and in this README is read from the generated
`site/data/meta.json`, never typed. Run it locally:

```bash
python -m http.server 8000 --directory site      # then open http://localhost:8000/
```

Naming prefix: `pots_`. Browser storage keys start with `pots_`, and every analytics event carries
`app: 'pots_findings'` (Ask page events are `ask_provider_selected`, `ask_key_saved`, `ask_question_sent`; they never
include a key, a question or an answer).

## Quick start with the data

```python
import pandas as pd
t1 = pd.read_parquet("packages/dysautonomia-core-findings/data/tier1_findings.parquet")
ok = t1.ontology_id_verification.isin(["authority_verified", "authority_verified_retrospective"])
grounded = t1[ok]            # rows whose entity identifier was confirmed at its authority
```

Each package's `README.md` has a quickstart, `docs/DATA_DICTIONARY.md` every column, `docs/LIMITATIONS.md` what the
data cannot support, and `code/verify_package.py --self-test` re-checks the package end to end.

## Verification

```bash
python site_tools/verify_site_v12.py --self-test     # site projection vs packages, hand-typed-number scan, checksums
for p in packages/*/; do (cd "$p" && python code/verify_package.py --self-test && shasum -a 256 -c CHECKSUMS.sha256 --quiet); done
```

Scientific fidelity (does each finding state what its paper found) has not yet been human-checked; see the About page.

## Historical checkpoints (archive)

Before the packages existed the repository published an incremental record: `data/` (Tier 1, July 2026) and
`data/tier2/` (Tier 2 at 55%, August 2026), with docs under `docs/` and `docs/tier2/` and the site generator of that era in
`site_tools/site_generator.py`. They are kept unchanged for reproducibility of the earlier releases (tags `tier1-v1`,
`tier2-55pct-2026-08-03`); the packages supersede them. The package versions are tags `v1.1` and `v1.2.0`.

## Important distinctions

- Co-mention is not interaction or causation.
- Shared biology across literatures is not the same as patient comorbidity.
- A condition label is not the same as the source literature that supplied the paper.
- Entity-based views cover the <!--n:entity_string_pct-->60.3<!--/n-->% of findings that name an entity, not the whole dataset; the rest are symptom, phenotype and quality-of-life findings.
- A null result does not by itself establish ineffectiveness.

## Citation and license

Derived structured data is licensed under CC BY 4.0. Verbatim provenance text remains the copyright of its
respective authors and publishers and is not licensed by this project. See [`NOTICE.md`](NOTICE.md) and
[`CITATION.cff`](CITATION.cff).

Credit: Erin Magennis.
