# REDESIGN_BRIEF.md - prompt for a coding assistant redesigning this site

Paste this whole file as your opening message to the assistant, then add your own design goals at
the end. It front-loads the constraints that are expensive to discover by reading the code.

---

## Task

Redesign the front end of a static research website: a browser for a literature-extraction dataset
about POTS, dysautonomia, and related conditions (ME/CFS, EDS, MCAS, fibromyalgia, IBS, small-fiber
neuropathy, migraine, autism). 73,070 findings extracted from 6,244 papers, with entity
canonicalization, cross-condition convergence, and adjudicated comorbidity claims.

I want the visual design and page structure improved. I do NOT want the data layer changed.

## Architecture - read this before writing code

- **Framework-free ES modules. No build step, no bundler, no npm install.** Everything is fetched as
  static JSON from `./data/`. Do not introduce React/Vue/Svelte, a bundler, or a package.json unless
  I explicitly ask - the zero-build property is deliberate so the site deploys as plain files.
- `site/js/data.js` is a shared loader with a cache. Pages call `loadMeta()`, `loadFacets()`,
  `loadPapers()`, `loadEntities()`, `loadTextShard(s)`, `loadDetailShard(s)`.
- One module per page: `site/js/page-*.js`, paired with `site/*.html`. 12 pages.
- `site/js/ui.js` has shared components: `header()`, `footer()`, `mount()`, `findingCard()`,
  `citeLine()`, `sortTable()`, `autocomplete()`, `framingBanner()`, `entityCoverageNote()`.
- `site/js/search.js` runs two independent modes: **keyword** (instant, zero dependency) and
  **semantic** (loads quantized embedding shards, embeds the query in-browser via
  `embed-worker.js`).
- `site/css/app.css` is all the styling.

## Hard rules

1. **Never edit anything under `site/data/`.** It is generated output - a projection of the dataset.
   Hand-editing it makes the site disagree with the published record. If a number looks wrong, the
   fix is upstream, not in the JSON.
2. **Never touch `data/`, `docs/`, `figures/`, `notebooks/`, or `validation/`.** That is the
   scientific record, published and citable.
3. **Keep the loader API in `data.js`.** You may restyle or restructure any page; if you rewrite
   `data.js` itself, preserve those function names and return shapes - every page depends on them.
4. **Never hardcode counts.** Read them from `meta.json` / `findings_facets.json`. Shard counts come
   from the data (`n`, `shard_rows`, `n_shards`); the site must keep working when the corpus grows.
5. **Preserve the keyword-search fallback.** Semantic search may fail (model CDN blocked, slow
   network). Keyword search must never depend on the model loading.
6. **Keep the coverage caveat visible.** See "Scope honesty" below. This is not decoration.
7. **After any change, run `python site_tools/verify_site.py`.** It must print PASS. It compares the
   site's numbers against a frozen fact registry and exits 1 if they drift.

## Scope honesty - a design requirement, not a disclaimer

This dataset is **partial and deliberately so**. Tier-2 covers 81 of 146 chunks (~55%). Every
tier-2 and combined figure is a subset figure, and **absence of a finding is not evidence of
absence**. Related traps the current UI is careful about, which a redesign must not undo:

- Only ~30–60% of findings carry a canonical entity, so entity-based views cover a *subset* of
  findings. `entityCoverageNote()` exists to say so wherever an entity view appears.
- Co-mention is not interaction. The associations view shows entities appearing in the same paper -
  that is not evidence they interact, and the current labels say so.
- A treatment "failing in this trial" is not "ineffective" - dose, comparator, and population
  matter. The null-results view says this.
- Convergence (shared biology across literatures) and comorbidity (explicitly claimed
  co-occurrence) are **different claims** and must stay visually separate.
- Some condition labels are incidental mentions inside another condition's literature, not that
  condition's own literature. The `evidence_scope` field distinguishes `within-literature` from
  `cross-mention`.

If a redesign makes the data look more complete or more certain than it is, that is a correctness
bug, not a style choice. Prefer a visible caveat over a clean-looking overstatement.

## Data shapes

`meta.json` - `{version, generated_utc, counts{...}, scope_caveat}`. All headline numbers.

`findings_facets.json` - dictionary-encoded columns for all 73,070 rows. `dicts` maps a facet key to
its value list; `cols` maps the same key to integer codes into that list. Filters and charts need
only this file. Facet keys include: `e` canonical_entity, `c` condition, `d` direction,
`ft` finding_type, `ek` entity_kind, `st` study_type, `nc` null_or_failed_result, `th` theme,
`rt` relation_type, `ti` **tier** (1 or 2), `sl` **source_literature**. Plus numeric columns
`y` year, `p` paper row index, `q` has-quantitative-detail, `has_can` has-canonical-entity.

`papers.json` - `{fields:[...], rows:[[...]]}`, column-oriented, 6,244 rows. Resolve by field index.

`entities.json` - `{n, entities:[{name, kind, mapc, oid, osrc, olabel, nf, np_, npd, origs, dirs,
tiers, conds}]}`, 2,803 entities.

`text_NN.json` / `detail_NN.json` - 13 shards of 6,000 rows, lazily loaded. Text is the finding
sentence; detail carries 12 parallel arrays (quote, quant, eff, path, lim, fut, npart, comp, symp,
treat, sec, ont).

Discovery tables: `associations.json`, `convergence.json`, `contradictions.json`,
`understudied.json`, `null_results.json`, `autocomplete.json`.

`emb/manifest.json` + `emb/*.bin` - uint8-quantized 384-dim embeddings, 13 shards. Shard filenames
come from the manifest; never hardcode them.

## Row-order contract

Row order is tier-1 rows first (0–36,458), then tier-2 (36,459–73,069). The facet columns, the
text/detail shards, and the embedding shards all share this one indexing. A view that mixes indices
from different builds shows the wrong findings **silently, with no error**.

## Two facets the current UI does not use

`ti` (tier) and `sl` (source_literature) are present in the data but no page surfaces them. Filtering
or grouping by which condition literature a finding came from is available if it helps your design.

## Chat page - already built, leave the key handling alone

`chat.html` is retrieval-augmented Q&A where **the visitor pastes their own API key**, kept in
`localStorage` on their device and sent only to the provider's endpoint. There is no server.

Do not add a server-side key, do not proxy the key, do not log or transmit it anywhere. If you keep
chat, keep the on-device explanation visible so visitors know where their key goes. The provider
model ids in `page-chat.js` are pinned strings and may be stale - updating those is fine.

## Suggested approach

Work one page at a time; each is an independent module, so nothing else breaks. Start with
`css/app.css` and `ui.js` for a global look, then individual pages. Run `verify_site.py` after each
change. Tell me before you alter `data.js` or the loader contract.

Read `SITE_CONTRACT.md` in the repo root - it is the authoritative version of these rules.

---

## My design goals

<add yours here - visual direction, which pages matter most, accessibility targets, mobile
behaviour, anything you want reworked first>
