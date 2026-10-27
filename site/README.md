# POTS and dysautonomia findings browser

This is a static, no-backend browser over findings package v1.2 (live at https://pots.erinmagennis.com):

- 148,186 machine-extracted findings
- 11,519 papers (one per PubMed record)
- five packages with Zenodo DOIs (see the repository README, "Download and cite")

Retracted papers and correction notices are flagged and left out of counts by default (`data/paper_flags.json`).
Absence of a finding is not evidence of absence.

## Run locally

From the repository root:

```bash
python site_tools/serve_local.py 8020
```

Then open `http://localhost:8020/`. This server handles the clean addresses (`/signals`, `/analyze`, `/chat`)
the way Vercel does; it does not run the redirects in `vercel.json` (`/discover`, `/builder`, `/charts`).

The site uses framework-free ES modules and static JSON. Keyword search works without an external model.
Semantic search loads a browser model and falls back without breaking keyword search.

## Pages and shared parts

- Nav order comes from `PAGES` in `js/ui.js`: Search, Signals, Connections, Analyze, Chat, About.
- One header and one footer for every page, written into each HTML file by `site_tools/apply_chrome.py`
  and styled by `css/chrome.css`. Do not edit a page's header or footer by hand.
- `start.html` is generated from the data by `site_tools/build_start_here.py`.

## Rebuild and check

`site/data/` is generated output. Do not edit it by hand. Rebuild in this order (see `site_tools/rebuild_site.py`):

```bash
python site_tools/build_v12_projection.py --root . --out site/data
python site_tools/build_home_data.py site
python site_tools/build_start_here.py site
python site_tools/build_connections_data.py --site site   # needs umap-learn + scikit-learn
python site_tools/apply_chrome.py site
python site_tools/apply_counts.py site README.md
python site_tools/verify_site_v12.py --self-test
```

The verifier checks every count against the packages, the home, Start and Connections numbers, the
header, footer and nav on every page, and `CHECKSUMS.txt`. Refresh `CHECKSUMS.txt` after any change.
