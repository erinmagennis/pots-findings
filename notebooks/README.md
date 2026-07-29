# Notebooks

Four notebooks that reproduce everything in this repository from the published data files.
They run in Google Colab with **zero local setup** and no edits, and they also run
inside a local clone of this repo.

**Scope reminder:** Tier 1 covers **POTS / dysautonomia only** — chunks 0–75 of a
286-chunk corpus, 3,121 of ~14,263 corpus papers. ME/CFS, fibromyalgia, EDS, MCAS, IBS,
migraine and autism appear here **only as incidental mentions inside POTS/dysautonomia
papers**, not as those conditions' own literature. This is not a cross-condition resource.
Nothing here is medical advice.

| Notebook | What it does | Code cells |
|---|---|---|
| `01_load_and_explore.ipynb` | Load the data, apply the counting rules, recompute fill rates from scratch, first look at conditions / design tiers / entities, verify one finding against its source paper | 12 |
| `02_reproduce_figures.ipynb` | Reproduce all 10 figures, with the exact numbers printed above each chart so you can check them | 23 |
| `03_associations_and_contradictions.ipynb` | Cross-kind associations, under-studied replication targets, contradiction moderators, RCT/meta-tier treatment failures, convergence gating | 17 |
| `04_query_recipes.ipynb` | 12 practical queries with their caveats inline | 14 |

All four were executed top-to-bottom before release; see `_exec/_results.json` for the
execution receipt and `_exec/*.ipynb` for the executed copies with outputs.

## Loading the data

Every notebook begins with one constant you can repoint:

```python
RAW_BASE = "https://raw.githubusercontent.com/USER/REPO/main/data"
```

The loader prefers a local `../data/` directory when one exists (so the notebooks work in a
clone), and otherwise downloads from `RAW_BASE` into a local cache. Replace `USER/REPO`
with the actual repository path once published.

## Dependencies

`pandas`, `numpy`, `matplotlib`, `pyarrow` — all pre-installed in Colab. Nothing else.

## Counting rules the notebooks enforce

- **Papers are counted as `canonical_pmid.nunique()`**, never `pmid.nunique()` — 8 duplicate
  pmids were folded into their canonical records.
- **`papers_direct`** excludes `split_derived` rows and is reported separately wherever it
  could change a reading.
- **`canonical_entity` covers 29.8% of rows, not half** (10,858 of 36,459; 2,185 of 3,121 papers).
  The original `entity` string covers 53.0% — a different column with a different number. The gap
  is 17,152 rows naming no entity at all plus **8,449 rows whose entity string was never
  canonicalized** (head-only mapping; those stay findable by keyword on `entity_norm_original`).
  Every entity-keyed chart states its denominator.
