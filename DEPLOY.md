# How to publish this

Nothing here needs a server, a build step, or a paid service. Total repo 126 MB, largest file 22 MB —
under every GitHub limit, so no Git LFS required.

## 1. Look at it locally first (2 minutes)

    cd site && python -m http.server 8000
    # open http://localhost:8000

Click around before publishing. Try the search both ways: keyword mode works instantly; semantic mode
downloads a ~23 MB model on first use (a few seconds, then cached by the browser).

## 2. Push to GitHub

    git init && git add . && git commit -m "Tier 1 (v1): POTS/dysautonomia findings database + browser"
    git branch -M main
    git remote add origin https://github.com/erinmagennis/pots-findings.git
    git push -u origin main

## 3. The website

Published on Vercel, not GitHub Pages. `vercel.json` sets `outputDirectory: "site"`, so the
browser is served at the domain root:

    https://pots.erinmagennis.com

`.vercelignore` keeps `data/`, `figures/`, `notebooks/`, `validation/` and `docs/` off the CDN.
They stay in this repo. Redeploy after a data change with `vercel deploy --prod` from the repo root.

Everything works for visitors with no key and no install: search, browse, all charts, the chart
builder, every download. The chat panel is the only part needing an API key, and each visitor
supplies their own.

## 4. Notebooks in Colab (no install for anyone)

Colab opens any notebook straight from GitHub:

    https://colab.research.google.com/github/erinmagennis/pots-findings/blob/main/notebooks/01_load_and_explore.ipynb

Set `DATA_BASE` at the top of each notebook to your raw URL:

    https://raw.githubusercontent.com/erinmagennis/pots-findings/main/data/

Paste those four links into your README so a reader is one click from running the analysis.

## What to hand to whom

| Audience | Send them |
|---|---|
| A researcher in the field | the Pages URL, then `docs/LIMITATIONS.md` |
| A collaborator who codes | the repo + `notebooks/04_query_recipes.ipynb` |
| Someone asking "is this real?" | `docs/VERIFICATION_REPORT.md` |
| A patient / advocate | `docs/PLAIN_LANGUAGE_SUMMARY.md` |
| A funder or reviewer | `docs/CORE_FINDINGS.md` §3 (contradictions) + §5 (what failed) |

## Before you share it widely

Two things worth doing first, both because you know this literature better than the extraction does:

1. **Spot-check the 51 mappings flagged `map_confidence == "low"`** (plus 240 medium if you have
   time). That is 51 distinct entity mappings to eyeball — they affect 232 finding rows. Entity pages list every folded-in original string, so a wrong merge is
   visible in seconds.
2. **Read the two subtype contradictions in `docs/CORE_FINDINGS.md` §3** (midodrine, gAChR autoantibody). If
   they hold up against what you know, they are the most publishable thing in this release.

## Citation

Add a `CITATION.cff` naming yourself as author before publicising — it makes GitHub show a "Cite this
repository" button. The derived data is CC-BY-4.0; the short quoted excerpts are not yours or mine to
license, which is why they are capped at 200 characters and always shown next to their source link.

## Reproducing the validation

`validation/` carries the machinery that guards every number:

    cd validation && python -c "
    import pandas as pd, tier2_invariants as inv, tier2_facts as tf
    M = pd.read_parquet('../data/tier1_findings.parquet')
    V = pd.read_parquet('../data/entity_vocabulary.parquet')
    inv.report(inv.check(M, V))"

14 invariants; all must pass. `tier2_facts.py` enforces that any quoted number carries its counting
basis — see `docs/TIER2_HANDOFF.md` for why that matters.
