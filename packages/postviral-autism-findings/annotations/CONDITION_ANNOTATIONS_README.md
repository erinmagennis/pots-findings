# condition_annotations, additive, pmid-keyed, never a mutation of `condition`

Built 2026-09-16 from the MCAS bucket census (`mcas_census_per_paper.csv`, 200 papers classified against
freshly fetched abstracts) under **population-studied semantics**: `condition` is read as the patient
population the paper studied, per the researcher's decision of 2026-09-16 and
`CONDITION_BUCKET_DEFINITIONS.md` v1 (MCAS = the activation syndrome; mastocytosis excluded).

The shipped `condition` column is unchanged. Join this table on `pmid` to filter or stratify.

## Coverage

| verdict | papers | rows | meaning |
|---|---:|---:|---|
| `in_bucket` | 32 | 256 | an MCAS population is studied (incl. papers treating MCAS and mastocytosis as distinct) |
| `bucket_violation` | 148 | 1488 | no MCAS population: mastocytosis (49), mast-cell biology only (87), neither (12) |
| `NEEDS_HUMAN` | 903 | 7090 | not individually assessed (897 unsampled, 6 without a fetchable abstract) |
| total MCAS-labelled | 1083 | 8834 | every paper carrying `condition == 'MCAS'` in any package |

Only the MCAS bucket has been censused. Other buckets (`EDS_hypermobility`, `dysautonomia`, `general`,
`multiple`, …) have working definitions in `CONDITION_BUCKET_DEFINITIONS.md` but no rows here yet.

**Every verdict is classifier-derived and `human_confirmed == False`.** The stratified projection over the
903 unassessed papers (~750 mechanism-only, ~113 MCAS, ~52 mastocytosis, ~65 both, ~103 neither) is in
`mcas_bucket_census.csv` with 95% intervals; it is a projection, not a census, and it is not copied into
per-paper rows. The 66 papers whose title contains "mastocytos" are the bounded human-adjudication set
(title keyword caught 49/49 mastocytosis papers and 0/118 sampled other titles were mastocytosis).

## Columns

| column | type | meaning |
|---|---|---|
| `pmid` | str | join key; one row per paper |
| `condition_bucket` | str | the shipped bucket being annotated (`MCAS` only in this version) |
| `package` | str | which of the five packages holds the paper (zero overlap) |
| `tier_source`, `n_rows` | str, int | tier and number of findings rows carrying this bucket |
| `title`, `title_mastocytosis` | str, bool | title as shipped; title-keyword screen |
| `census_stratum`, `census_cat` | str | sampling stratum and raw classifier category (null when unassessed) |
| `condition_bucket_verdict` | enum | `in_bucket` / `bucket_violation` / `bucket_definition_disputed` / `NEEDS_HUMAN` |
| `condition_population_kind` | enum | `disorder_population` / `mechanism_only` / `not_applicable` / null |
| `condition_specific` | str | population as the paper states it, when assessed |
| `deciding_span`, `span_verified` | str, bool | verbatim span the classifier cited; whether it was found verbatim in the abstract |
| `condition_relabel_basis` | str | who decided, how, against which definitions version, confirmation status |
| `semantics` | str | `population_studied` |
| `definitions_version` | str | the definitions file and version the verdict is judged against |
| `human_confirmed` | bool | False everywhere in this version |
| `annotated_on` | str | ISO date |

## Use

```python
ann = pd.read_parquet('annotations/condition_annotations.parquet')
df = pd.read_parquet('data/tier2a_findings.parquet')
mcas_pop = df.merge(ann.loc[ann.condition_bucket_verdict == 'in_bucket', ['pmid']], on='pmid')   # pmid is str in both
```

When definitions change, this table is regenerated with a new `definitions_version`; verdicts are never
edited in place.
