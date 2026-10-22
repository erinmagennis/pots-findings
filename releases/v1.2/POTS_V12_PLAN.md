# POTS v1.2 — what is done, what remains (2026-10-21)

**Done (no model spend):**
- Benchmark of every model-emitted identifier in v1.1 (16,662 rows / 6,120 name × id pairs), two passes against the minting authorities: 65.3% denote the entity, 34.7% denote another entity, 0.02% not found. `benchmarks/POTS_MODEL_ID_BENCHMARK.md|json`, per-pair actions in `pots_model_id_benchmark.parquet`.
- v1.2 corpus table `findings_all_tiers_v1.2.parquet` (artifact store; 148,186 rows, same row set as v1.1): 10,879 rows re-tagged `authority_verified_retrospective` (match mode recorded: exact / synonym / exact_relaxed / compound_partial); 3,176 rows' ids REPLACED by the id their name resolves to (exact label/synonym), source noted; 2,607 rows' ids NULLED and tagged `id_withheld_unverified_v1.2`. The original model id is preserved in `ontology_id_v11_model_emitted` on every affected row. 125,797 `no_id` and 5,727 `authority_verified` rows untouched.

**Not done — the five-package rebuild.** The legacy builder (`build_packages.py`, legacy mode) renders README/LIMITATIONS prose that hard-codes the v1.1 situation: "there are NO authority-verified ids in this package", the `unverified_model_emitted` quickstart filter, the coverage-vs-correctness table, and the sampled `id_denotes_entity_rate` (0.578 on 276 rows for t1; the full-population benchmark gives 0.72 for t1-tagged pairs). A build with the v1.2 table fails at `docs.readme` on the missing `unverified_model_emitted` key. Required before v1.2 can ship:
1. `--docs-revision v1.2` in `build_packages.py`: rewrite the quickstart (lines ~487–499), the LIMITATIONS identifier passage (~708–720) and the coverage-vs-correctness section (~812–830) to describe the three verification states and cite the benchmark; replace the sampled rate with the measured full-population rate per package; add a CHANGES entry.
2. `verify_package.py`: accept the new `ontology_id_verification` categories; add a planted regression for them.
3. Rebuild five packages (inputs are staged: `pots_inputs/` 53 files from the artifact store, `annotations_v12/` from the v1.1 repo tarball); verifier + checksums; byte-identity check against a second build.
4. Update the `pots/` repository data and site, re-run the registry.
Estimated: ~2 h of careful editing and verification; zero model spend. Not attempted tonight because a hurried docs revision is exactly the class of error the auditor has been catching.

**Until then:** the STATE document and every v1.1 README say the model-emitted ids must not be used for joins; the benchmark parquet gives any reader the per-id verdict today.


## Build record — v1.2 packages (final build 2026-10-22T11:06:25Z)

Built with `build_packages.py --docs-revision v1.2` from `findings_all_tiers_v1.2.parquet` and the v1.1 annotation tables (the first build of the day shipped the annotation files under tier-prefixed names and was discarded; the final build is file-for-file a superset of v1.1 minus `REBUILD_REPORT.md`, plus `annotations/POTS_MODEL_ID_BENCHMARK.md/.json`). Built twice with `--build-utc` pinned, tarballs byte-identical; `verify_package.py --self-test` PASS and `shasum -c CHECKSUMS.sha256` clean for all five. Docs regenerated from per-package counts; v1.1 prose kept as history. Builder commit `0b5bdc4` (condition-findings-builder).

| package | findings | papers | authority_verified | authority_verified_retrospective | id_withheld_unverified_v1.2 | no_id | sha256 (tarball) |
|---|---|---|---|---|---|---|---|
| comorbid-conditions-findings-a-v1.2 | 36,611 | 3,123 | 0 | 5,721 | 995 | 29,895 | `0171f92b41bf3177…` |
| comorbid-conditions-findings-b-v1.2 | 33,830 | 2,589 | 0 | 4,788 | 785 | 28,257 | `12a49c8f18a371f6…` |
| dysautonomia-core-findings-v1.2 | 36,067 | 3,129 | 0 | 3,546 | 827 | 31,694 | `73fb1c1b56c47074…` |
| migraine-hypermobility-findings-v1.2 | 15,646 | 1,091 | 1,614 | 0 | 0 | 14,032 | `04029716a96f5151…` |
| postviral-autism-findings-v1.2 | 26,032 | 1,587 | 4,113 | 0 | 0 | 21,919 | `355e60be9fc96d31…` |
| **total** | **148,186** | — | **5,727** | **14,055** | **2,607** | **125,797** | |

Released into the user's `pots/` repo on branch `release/v1.2`: commit `e22d119` (packages v1.1, dated 2026-09-23 = bundle build date, tag `v1.1`) then `1df50c6` (packages v1.2, tag `v1.2`; README section, CHANGELOG.md, About-page verification note). Not pushed — the user pushes/merges.

Tier 3/4 packages are unchanged in data (their ids were resolver-derived from the start); rebuilt only so the five share one version and one `pots-findings` repo bundle.
