# POTS and dysautonomia findings browser

This is a static, no-backend browser over the current combined research checkpoint:

- 73,070 machine-extracted findings
- 6,244 canonical papers
- 2,803 canonical entities
- Tier 1 plus 81 of 146 Tier 2 chunks, or 55.5% of Tier 2

Every Tier 2 and combined number is a subset count. Absence of a finding is not evidence of absence.

## Run locally

From the repository root:

```bash
python -m http.server 8000 --directory site
```

Then open `http://localhost:8000/`.

The site uses framework-free ES modules and static JSON. It has no build step. Keyword search works without
an external model. Semantic search loads a browser model and falls back without breaking keyword search.

## Data contract

`site/data/` is generated output. Do not edit it by hand. The row order is Tier 1 first, followed by Tier 2,
and is shared by facets, text shards, detail shards, and embedding shards.

The main loaders are in `js/data.js`:

- `loadMeta()`
- `loadFacets()`
- `loadPapers()`
- `loadEntities()`
- `loadTextShard()` and `loadDetailShard()`

Run the checkpoint before a deployment:

```bash
python site_tools/verify_site.py --self-test
```

See `SITE_CONTRACT.md` and `INTEGRATION_SITE.md` in the repository root for the full boundaries and release flow.
